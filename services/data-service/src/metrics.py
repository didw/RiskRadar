"""
Prometheus 메트릭 정의 및 수집
Week 4 요구사항 구현
"""
import time
from functools import wraps
from typing import Callable, Any, Dict, Optional
from datetime import datetime
import logging

from prometheus_client import (
    Counter, Histogram, Gauge, Summary,
    generate_latest, CONTENT_TYPE_LATEST,
    CollectorRegistry, REGISTRY
)

logger = logging.getLogger(__name__)


# 메트릭 정의
# 1. 총 크롤링 요청 수 (source별)
crawl_requests_total = Counter(
    'data_service_crawl_requests_total',
    'Total number of crawl requests',
    ['source', 'status']  # labels: source=뉴스소스, status=success/failure
)

# 2. 크롤링 소요 시간
crawl_duration_seconds = Histogram(
    'data_service_crawl_duration_seconds',
    'Time spent crawling in seconds',
    ['source'],
    buckets=(0.1, 0.5, 1, 2, 5, 10, 30, 60, 120, 300)  # 0.1초 ~ 5분
)

# 3. 처리된 기사 수 (source별)
articles_processed_total = Counter(
    'data_service_articles_processed_total',
    'Total number of articles processed',
    ['source', 'status']  # status: processed/duplicate/error
)

# 4. Kafka로 전송된 메시지 수
kafka_messages_sent_total = Counter(
    'data_service_kafka_messages_sent_total',
    'Total number of messages sent to Kafka',
    ['topic', 'status']  # status: success/failure
)

# 5. 중복 제거율 (Gauge로 현재 비율 표시)
deduplication_rate = Gauge(
    'data_service_deduplication_rate',
    'Current deduplication rate (0-1)',
    ['time_window']  # time_window: 1h/24h/7d
)

# 6. 크롤링 에러 수 (error_type별)
crawl_errors_total = Counter(
    'data_service_crawl_errors_total',
    'Total number of crawl errors',
    ['source', 'error_type']  # error_type: network/parse/timeout/rate_limit/unknown
)

# 7. 현재 처리량 (시간당 기사 수)
current_throughput_articles_per_hour = Gauge(
    'data_service_current_throughput_articles_per_hour',
    'Current throughput in articles per hour'
)

# 8. 평균 지연시간
average_latency_seconds = Gauge(
    'data_service_average_latency_seconds',
    'Average latency from article publication to processing in seconds'
)

# 추가 메트릭
# 9. 동시 실행 중인 크롤러 수
active_crawlers = Gauge(
    'data_service_active_crawlers',
    'Number of currently active crawlers'
)

# 10. 크롤러별 연속 실패 횟수
consecutive_failures = Gauge(
    'data_service_consecutive_failures',
    'Number of consecutive failures per crawler',
    ['source']
)

# 11. 배치 처리 큐 크기
batch_queue_size = Gauge(
    'data_service_batch_queue_size',
    'Current size of batch processing queue'
)

# 12. 재시도 큐 크기
retry_queue_size = Gauge(
    'data_service_retry_queue_size',
    'Current size of retry queue'
)


class MetricsCollector:
    """메트릭 수집 및 관리 클래스"""
    
    def __init__(self):
        self._start_time = time.time()
        self._article_counts = {}  # source별 기사 수 추적
        self._duplicate_counts = {}  # source별 중복 수 추적
        
    def record_crawl_request(self, source: str, success: bool):
        """크롤링 요청 기록"""
        status = 'success' if success else 'failure'
        crawl_requests_total.labels(source=source, status=status).inc()
        
    def record_crawl_duration(self, source: str, duration: float):
        """크롤링 소요 시간 기록"""
        crawl_duration_seconds.labels(source=source).observe(duration)
        
    def record_article_processed(self, source: str, status: str = 'processed'):
        """처리된 기사 기록"""
        articles_processed_total.labels(source=source, status=status).inc()
        
        # 중복 제거율 계산을 위한 카운팅
        if source not in self._article_counts:
            self._article_counts[source] = 0
            self._duplicate_counts[source] = 0
            
        if status == 'processed':
            self._article_counts[source] += 1
        elif status == 'duplicate':
            self._duplicate_counts[source] += 1
            
    def record_kafka_message(self, topic: str, success: bool):
        """Kafka 메시지 전송 기록"""
        status = 'success' if success else 'failure'
        kafka_messages_sent_total.labels(topic=topic, status=status).inc()
        
    def record_crawl_error(self, source: str, error_type: str):
        """크롤링 에러 기록"""
        crawl_errors_total.labels(source=source, error_type=error_type).inc()
        
    def update_deduplication_rate(self, time_window: str = '1h'):
        """중복 제거율 업데이트"""
        total = sum(self._article_counts.values())
        duplicates = sum(self._duplicate_counts.values())
        
        if total > 0:
            rate = duplicates / (total + duplicates)
            deduplication_rate.labels(time_window=time_window).set(rate)
            
    def update_throughput(self, articles_per_hour: float):
        """처리량 업데이트"""
        current_throughput_articles_per_hour.set(articles_per_hour)
        
    def update_latency(self, avg_latency: float):
        """평균 지연시간 업데이트"""
        average_latency_seconds.set(avg_latency)
        
    def update_active_crawlers(self, count: int):
        """활성 크롤러 수 업데이트"""
        active_crawlers.set(count)
        
    def update_consecutive_failures(self, source: str, count: int):
        """연속 실패 횟수 업데이트"""
        consecutive_failures.labels(source=source).set(count)
        
    def update_batch_queue_size(self, size: int):
        """배치 큐 크기 업데이트"""
        batch_queue_size.set(size)
        
    def update_retry_queue_size(self, size: int):
        """재시도 큐 크기 업데이트"""
        retry_queue_size.set(size)
        
    def get_error_type_from_exception(self, e: Exception) -> str:
        """예외로부터 에러 타입 추출"""
        error_str = str(e).lower()
        
        if 'timeout' in error_str:
            return 'timeout'
        elif 'connection' in error_str or 'network' in error_str:
            return 'network'
        elif 'parse' in error_str or 'parsing' in error_str:
            return 'parse'
        elif 'rate' in error_str and 'limit' in error_str:
            return 'rate_limit'
        else:
            return 'unknown'


# 전역 메트릭 수집기 인스턴스
_metrics_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """메트릭 수집기 인스턴스 반환"""
    return _metrics_collector


# 데코레이터 패턴 구현
def track_crawl_metrics(source: str):
    """크롤링 메트릭 추적 데코레이터"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            success = False
            
            try:
                # 함수 실행
                result = await func(*args, **kwargs)
                success = True
                return result
                
            except Exception as e:
                # 에러 메트릭 기록
                error_type = _metrics_collector.get_error_type_from_exception(e)
                _metrics_collector.record_crawl_error(source, error_type)
                raise
                
            finally:
                # 크롤링 요청 및 소요 시간 기록
                duration = time.time() - start_time
                _metrics_collector.record_crawl_request(source, success)
                _metrics_collector.record_crawl_duration(source, duration)
                
        return wrapper
    return decorator


def track_kafka_metrics(topic: str):
    """Kafka 전송 메트릭 추적 데코레이터"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            success = False
            
            try:
                result = func(*args, **kwargs)
                success = True
                return result
                
            except Exception as e:
                logger.error(f"Kafka send failed: {e}")
                raise
                
            finally:
                _metrics_collector.record_kafka_message(topic, success)
                
        return wrapper
    return decorator


def track_processing_time(operation: str):
    """처리 시간 추적 데코레이터 (범용)"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                return result
                
            finally:
                duration = time.time() - start_time
                logger.debug(f"{operation} took {duration:.2f}s")
                
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                return result
                
            finally:
                duration = time.time() - start_time
                logger.debug(f"{operation} took {duration:.2f}s")
                
        # 비동기 함수인지 확인
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
            
    return decorator


def generate_metrics() -> bytes:
    """Prometheus 포맷으로 메트릭 생성"""
    # 중복 제거율 업데이트
    _metrics_collector.update_deduplication_rate('1h')
    
    return generate_latest()


def get_metrics_stats() -> Dict[str, Any]:
    """메트릭 통계 반환 (디버깅용)"""
    return {
        "uptime_seconds": time.time() - _metrics_collector._start_time,
        "article_counts": _metrics_collector._article_counts.copy(),
        "duplicate_counts": _metrics_collector._duplicate_counts.copy(),
        "deduplication_rates": {
            source: (
                _metrics_collector._duplicate_counts.get(source, 0) / 
                (_metrics_collector._article_counts.get(source, 0) + 
                 _metrics_collector._duplicate_counts.get(source, 0))
                if (_metrics_collector._article_counts.get(source, 0) + 
                    _metrics_collector._duplicate_counts.get(source, 0)) > 0
                else 0
            )
            for source in set(
                list(_metrics_collector._article_counts.keys()) + 
                list(_metrics_collector._duplicate_counts.keys())
            )
        }
    }