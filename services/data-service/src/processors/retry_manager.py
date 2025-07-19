"""
고급 에러 처리 및 재시도 메커니즘
- 지수 백오프
- 에러 타입별 재시도 정책
- Circuit Breaker 패턴
- 데드 레터 큐
"""
import asyncio
import logging
import time
from typing import Dict, Any, Optional, Callable, List, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import random
import json

logger = logging.getLogger(__name__)


class RetryPolicy(str, Enum):
    """재시도 정책"""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    FIXED_DELAY = "fixed_delay"
    LINEAR_BACKOFF = "linear_backoff"
    NO_RETRY = "no_retry"


class ErrorType(str, Enum):
    """에러 타입 분류"""
    NETWORK_ERROR = "network_error"
    TIMEOUT_ERROR = "timeout_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    PARSE_ERROR = "parse_error"
    VALIDATION_ERROR = "validation_error"
    TEMPORARY_ERROR = "temporary_error"
    PERMANENT_ERROR = "permanent_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class RetryConfig:
    """재시도 설정"""
    max_retries: int = 3
    base_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    backoff_multiplier: float = 2.0
    jitter: bool = True  # 랜덤 지연 추가
    retry_policy: RetryPolicy = RetryPolicy.EXPONENTIAL_BACKOFF
    
    # 에러 타입별 재시도 여부
    retryable_errors: List[ErrorType] = field(default_factory=lambda: [
        ErrorType.NETWORK_ERROR,
        ErrorType.TIMEOUT_ERROR,
        ErrorType.RATE_LIMIT_ERROR,
        ErrorType.TEMPORARY_ERROR
    ])
    
    # 특별 처리
    rate_limit_delay: float = 60.0  # Rate limit 시 대기 시간
    circuit_breaker_threshold: int = 5  # 연속 실패 임계값
    circuit_breaker_timeout: float = 300.0  # 5분


@dataclass
class RetryAttempt:
    """재시도 시도 정보"""
    attempt_number: int
    timestamp: datetime
    error_type: ErrorType
    error_message: str
    delay_used: float
    success: bool = False


@dataclass
class RetryResult:
    """재시도 결과"""
    success: bool
    result: Any = None
    error: Optional[Exception] = None
    attempts: List[RetryAttempt] = field(default_factory=list)
    total_time: float = 0.0
    final_error_type: Optional[ErrorType] = None


class CircuitBreaker:
    """Circuit Breaker 패턴 구현"""
    
    def __init__(self, failure_threshold: int = 5, timeout: float = 300.0):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open
    
    def can_execute(self) -> bool:
        """실행 가능 여부 확인"""
        if self.state == "closed":
            return True
        elif self.state == "open":
            if time.time() - self.last_failure_time >= self.timeout:
                self.state = "half_open"
                return True
            return False
        else:  # half_open
            return True
    
    def on_success(self):
        """성공 시 호출"""
        self.failure_count = 0
        self.state = "closed"
    
    def on_failure(self):
        """실패 시 호출"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
    
    def get_status(self) -> Dict[str, Any]:
        """상태 정보 반환"""
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "last_failure_time": self.last_failure_time,
            "timeout": self.timeout
        }


class ErrorClassifier:
    """에러 분류기"""
    
    @staticmethod
    def classify_error(error: Exception) -> ErrorType:
        """에러를 타입별로 분류"""
        error_str = str(error).lower()
        error_type_name = type(error).__name__.lower()
        
        # 네트워크 에러
        if any(keyword in error_str for keyword in [
            "connection", "timeout", "network", "unreachable", 
            "dns", "socket", "ssl", "certificate"
        ]):
            return ErrorType.NETWORK_ERROR
        
        # 타임아웃 에러
        if any(keyword in error_str for keyword in [
            "timeout", "timed out", "time out"
        ]) or "timeout" in error_type_name:
            return ErrorType.TIMEOUT_ERROR
        
        # Rate Limit 에러
        if any(keyword in error_str for keyword in [
            "rate limit", "too many requests", "429", "throttle"
        ]):
            return ErrorType.RATE_LIMIT_ERROR
        
        # 파싱 에러
        if any(keyword in error_str for keyword in [
            "parse", "parsing", "json", "xml", "html", "decode"
        ]) or any(keyword in error_type_name for keyword in [
            "parse", "json", "decode"
        ]):
            return ErrorType.PARSE_ERROR
        
        # 검증 에러
        if any(keyword in error_str for keyword in [
            "validation", "invalid", "required", "missing"
        ]) or "validation" in error_type_name:
            return ErrorType.VALIDATION_ERROR
        
        # 영구적 에러 (재시도 불필요)
        if any(keyword in error_str for keyword in [
            "not found", "404", "unauthorized", "forbidden", 
            "403", "401", "bad request", "400"
        ]):
            return ErrorType.PERMANENT_ERROR
        
        # 일시적 에러
        if any(keyword in error_str for keyword in [
            "temporary", "503", "502", "500", "server error"
        ]):
            return ErrorType.TEMPORARY_ERROR
        
        return ErrorType.UNKNOWN_ERROR


class RetryManager:
    """재시도 관리자"""
    
    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
        self.error_classifier = ErrorClassifier()
        
        # Circuit breakers (작업별로 관리)
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        # 통계
        self._stats = {
            "total_executions": 0,
            "total_retries": 0,
            "total_successes": 0,
            "total_failures": 0,
            "error_type_counts": {error_type.value: 0 for error_type in ErrorType},
            "circuit_breaker_trips": 0,
            "start_time": datetime.now()
        }
    
    def _get_circuit_breaker(self, operation_key: str) -> CircuitBreaker:
        """작업별 Circuit Breaker 가져오기"""
        if operation_key not in self.circuit_breakers:
            self.circuit_breakers[operation_key] = CircuitBreaker(
                self.config.circuit_breaker_threshold,
                self.config.circuit_breaker_timeout
            )
        return self.circuit_breakers[operation_key]
    
    def _calculate_delay(self, attempt: int, error_type: ErrorType) -> float:
        """재시도 지연 시간 계산"""
        if error_type == ErrorType.RATE_LIMIT_ERROR:
            return self.config.rate_limit_delay
        
        if self.config.retry_policy == RetryPolicy.NO_RETRY:
            return 0.0
        elif self.config.retry_policy == RetryPolicy.FIXED_DELAY:
            delay = self.config.base_delay
        elif self.config.retry_policy == RetryPolicy.LINEAR_BACKOFF:
            delay = self.config.base_delay * attempt
        else:  # EXPONENTIAL_BACKOFF
            delay = self.config.base_delay * (self.config.backoff_multiplier ** (attempt - 1))
        
        # 최대 지연 시간 제한
        delay = min(delay, self.config.max_delay)
        
        # Jitter 추가 (랜덤성)
        if self.config.jitter:
            jitter_range = delay * 0.1  # ±10%
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0.0, delay)
    
    def _is_retryable(self, error_type: ErrorType) -> bool:
        """재시도 가능 여부 확인"""
        return error_type in self.config.retryable_errors
    
    async def execute_with_retry(
        self,
        operation: Callable,
        operation_key: str = "default",
        *args,
        **kwargs
    ) -> RetryResult:
        """재시도 기능이 있는 작업 실행"""
        start_time = time.time()
        attempts = []
        
        # Circuit breaker 확인
        circuit_breaker = self._get_circuit_breaker(operation_key)
        if not circuit_breaker.can_execute():
            self._stats["circuit_breaker_trips"] += 1
            return RetryResult(
                success=False,
                error=Exception("Circuit breaker is OPEN"),
                attempts=attempts,
                total_time=0.0,
                final_error_type=ErrorType.PERMANENT_ERROR
            )
        
        self._stats["total_executions"] += 1
        
        for attempt in range(1, self.config.max_retries + 2):  # +2 because range is exclusive and we want initial + retries
            try:
                # 작업 실행
                if asyncio.iscoroutinefunction(operation):
                    result = await operation(*args, **kwargs)
                else:
                    result = operation(*args, **kwargs)
                
                # 성공
                attempt_info = RetryAttempt(
                    attempt_number=attempt,
                    timestamp=datetime.now(),
                    error_type=ErrorType.UNKNOWN_ERROR,  # No error
                    error_message="",
                    delay_used=0.0,
                    success=True
                )
                attempts.append(attempt_info)
                
                circuit_breaker.on_success()
                self._stats["total_successes"] += 1
                
                return RetryResult(
                    success=True,
                    result=result,
                    attempts=attempts,
                    total_time=time.time() - start_time
                )
                
            except Exception as error:
                # 에러 분류
                error_type = self.error_classifier.classify_error(error)
                self._stats["error_type_counts"][error_type.value] += 1
                
                # 시도 정보 기록
                delay_used = 0.0
                if attempt <= self.config.max_retries and self._is_retryable(error_type):
                    delay_used = self._calculate_delay(attempt, error_type)
                
                attempt_info = RetryAttempt(
                    attempt_number=attempt,
                    timestamp=datetime.now(),
                    error_type=error_type,
                    error_message=str(error),
                    delay_used=delay_used,
                    success=False
                )
                attempts.append(attempt_info)
                
                # 재시도 가능성 확인
                if (attempt > self.config.max_retries or 
                    not self._is_retryable(error_type)):
                    # 최종 실패
                    circuit_breaker.on_failure()
                    self._stats["total_failures"] += 1
                    
                    return RetryResult(
                        success=False,
                        error=error,
                        attempts=attempts,
                        total_time=time.time() - start_time,
                        final_error_type=error_type
                    )
                
                # 재시도 준비
                self._stats["total_retries"] += 1
                
                if delay_used > 0:
                    logger.info(
                        f"Retrying {operation_key} (attempt {attempt + 1}) "
                        f"after {delay_used:.2f}s due to {error_type.value}: {str(error)}"
                    )
                    await asyncio.sleep(delay_used)
        
        # 이 지점에 도달하면 안됨 (위에서 처리되어야 함)
        circuit_breaker.on_failure()
        return RetryResult(
            success=False,
            error=Exception("Unexpected end of retry loop"),
            attempts=attempts,
            total_time=time.time() - start_time,
            final_error_type=ErrorType.UNKNOWN_ERROR
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """통계 정보 반환"""
        stats = self._stats.copy()
        
        # 시간 정보
        uptime = datetime.now() - stats["start_time"]
        stats["uptime_seconds"] = uptime.total_seconds()
        
        # 비율 계산
        total_ops = stats["total_executions"]
        if total_ops > 0:
            stats["success_rate"] = stats["total_successes"] / total_ops
            stats["failure_rate"] = stats["total_failures"] / total_ops
            stats["retry_rate"] = stats["total_retries"] / total_ops
        else:
            stats["success_rate"] = 0.0
            stats["failure_rate"] = 0.0
            stats["retry_rate"] = 0.0
        
        # Circuit breaker 상태
        stats["circuit_breakers"] = {
            key: breaker.get_status() 
            for key, breaker in self.circuit_breakers.items()
        }
        
        return stats
    
    def reset_stats(self):
        """통계 초기화"""
        self._stats = {
            "total_executions": 0,
            "total_retries": 0,
            "total_successes": 0,
            "total_failures": 0,
            "error_type_counts": {error_type.value: 0 for error_type in ErrorType},
            "circuit_breaker_trips": 0,
            "start_time": datetime.now()
        }
        
        # Circuit breaker도 초기화
        for breaker in self.circuit_breakers.values():
            breaker.failure_count = 0
            breaker.state = "closed"
            breaker.last_failure_time = None
    
    def get_circuit_breaker_status(self, operation_key: str) -> Optional[Dict[str, Any]]:
        """특정 작업의 Circuit breaker 상태 반환"""
        if operation_key in self.circuit_breakers:
            return self.circuit_breakers[operation_key].get_status()
        return None


# 글로벌 인스턴스
_retry_manager: Optional[RetryManager] = None


def get_retry_manager() -> RetryManager:
    """글로벌 재시도 관리자 인스턴스 반환"""
    global _retry_manager
    
    if _retry_manager is None:
        config = RetryConfig()
        _retry_manager = RetryManager(config)
    
    return _retry_manager


# 편의 함수들
async def retry_on_error(
    operation: Callable,
    operation_key: str = "default",
    max_retries: int = 3,
    *args,
    **kwargs
) -> Any:
    """간단한 재시도 실행 (결과만 반환)"""
    retry_manager = get_retry_manager()
    
    # 임시 config 생성
    original_config = retry_manager.config
    retry_manager.config = RetryConfig(max_retries=max_retries)
    
    try:
        result = await retry_manager.execute_with_retry(
            operation, operation_key, *args, **kwargs
        )
        
        if result.success:
            return result.result
        else:
            raise result.error
    finally:
        retry_manager.config = original_config


def with_circuit_breaker(operation_key: str):
    """Circuit breaker 데코레이터"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            retry_manager = get_retry_manager()
            result = await retry_manager.execute_with_retry(
                func, operation_key, *args, **kwargs
            )
            
            if result.success:
                return result.result
            else:
                raise result.error
        
        return wrapper
    return decorator