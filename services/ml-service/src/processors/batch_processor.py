"""
배치 처리 최적화 모듈
Batch Processing Optimization Module
"""
import asyncio
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from ..kafka.schemas import NLPResult, Entity, Sentiment, Keyword

logger = logging.getLogger(__name__)


@dataclass
class BatchRequest:
    """배치 요청 데이터"""
    id: str
    text: str
    priority: int = 0  # 0: normal, 1: high, 2: urgent


@dataclass
class BatchResult:
    """배치 결과 데이터"""
    id: str
    result: Optional[NLPResult] = None
    error: Optional[str] = None
    processing_time_ms: float = 0


class BatchProcessor:
    """배치 처리 최적화기"""
    
    def __init__(self, max_workers: int = 4, batch_size: int = 10):
        """
        초기화
        
        Args:
            max_workers: 최대 워커 스레드 수
            batch_size: 배치 크기
        """
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # 성능 통계
        self.stats = {
            "total_batches": 0,
            "total_requests": 0,
            "total_processing_time_ms": 0,
            "avg_batch_time_ms": 0,
            "throughput_docs_per_sec": 0,
            "cache_hit_rate": 0.0
        }
        
        logger.info(f"Batch processor initialized (workers: {max_workers}, batch_size: {batch_size})")
    
    async def process_batch(self, requests: List[BatchRequest], 
                          nlp_pipeline) -> List[BatchResult]:
        """
        배치 요청 처리
        
        Args:
            requests: 배치 요청 리스트
            nlp_pipeline: NLP 파이프라인 인스턴스
            
        Returns:
            배치 결과 리스트
        """
        start_time = time.time()
        
        # 우선순위별 정렬
        sorted_requests = sorted(requests, key=lambda x: x.priority, reverse=True)
        
        # 배치 크기별로 분할
        batches = self._split_into_batches(sorted_requests)
        
        # 병렬 처리
        all_results = []
        
        for batch in batches:
            batch_results = await self._process_single_batch(batch, nlp_pipeline)
            all_results.extend(batch_results)
        
        # 원래 순서로 정렬
        request_id_to_result = {result.id: result for result in all_results}
        ordered_results = [request_id_to_result[req.id] for req in requests]
        
        # 통계 업데이트
        processing_time = (time.time() - start_time) * 1000
        self._update_stats(len(requests), processing_time)
        
        logger.info(f"Processed batch of {len(requests)} requests in {processing_time:.2f}ms")
        
        return ordered_results
    
    def _split_into_batches(self, requests: List[BatchRequest]) -> List[List[BatchRequest]]:
        """요청을 배치 크기별로 분할"""
        batches = []
        for i in range(0, len(requests), self.batch_size):
            batch = requests[i:i + self.batch_size]
            batches.append(batch)
        return batches
    
    async def _process_single_batch(self, batch: List[BatchRequest], 
                                   nlp_pipeline) -> List[BatchResult]:
        """단일 배치 처리"""
        loop = asyncio.get_event_loop()
        
        # 비동기 태스크 생성
        tasks = []
        for request in batch:
            task = loop.run_in_executor(
                self.executor,
                self._process_single_request,
                request,
                nlp_pipeline
            )
            tasks.append(task)
        
        # 모든 태스크 완료 대기
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 예외 처리
        batch_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                batch_results.append(BatchResult(
                    id=batch[i].id,
                    error=str(result)
                ))
            else:
                batch_results.append(result)
        
        return batch_results
    
    def _process_single_request(self, request: BatchRequest, 
                               nlp_pipeline) -> BatchResult:
        """단일 요청 처리 (동기)"""
        start_time = time.time()
        
        try:
            # NLP 파이프라인 처리 (동기식으로 호출)
            result = asyncio.run(nlp_pipeline.process(request.text))
            
            processing_time = (time.time() - start_time) * 1000
            
            return BatchResult(
                id=request.id,
                result=result,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"Failed to process request {request.id}: {e}")
            
            return BatchResult(
                id=request.id,
                error=str(e),
                processing_time_ms=processing_time
            )
    
    def _update_stats(self, request_count: int, processing_time_ms: float):
        """통계 업데이트"""
        self.stats["total_batches"] += 1
        self.stats["total_requests"] += request_count
        self.stats["total_processing_time_ms"] += processing_time_ms
        
        # 평균 배치 처리 시간
        self.stats["avg_batch_time_ms"] = (
            self.stats["total_processing_time_ms"] / self.stats["total_batches"]
        )
        
        # 처리량 (문서/초)
        if processing_time_ms > 0:
            self.stats["throughput_docs_per_sec"] = (request_count / processing_time_ms) * 1000
    
    def optimize_batch_size(self, test_sizes: List[int] = [5, 10, 20, 30]) -> int:
        """배치 크기 최적화"""
        # 실제 구현에서는 여러 배치 크기로 테스트하여 최적값 찾기
        # 여기서는 간단한 휴리스틱 사용
        
        if self.max_workers <= 2:
            return 5
        elif self.max_workers <= 4:
            return 10
        elif self.max_workers <= 8:
            return 20
        else:
            return 30
    
    def get_stats(self) -> Dict[str, Any]:
        """통계 조회"""
        return self.stats.copy()
    
    def reset_stats(self):
        """통계 초기화"""
        self.stats = {
            "total_batches": 0,
            "total_requests": 0,
            "total_processing_time_ms": 0,
            "avg_batch_time_ms": 0,
            "throughput_docs_per_sec": 0,
            "cache_hit_rate": 0.0
        }
    
    def shutdown(self):
        """리소스 정리"""
        self.executor.shutdown(wait=True)
        logger.info("Batch processor shutdown complete")


class AdaptiveBatchProcessor(BatchProcessor):
    """적응형 배치 처리기"""
    
    def __init__(self, max_workers: int = 4, initial_batch_size: int = 10):
        super().__init__(max_workers, initial_batch_size)
        
        # 적응형 매개변수
        self.performance_history = []
        self.adaptation_threshold = 5  # 성능 측정 횟수
        self.current_optimal_size = initial_batch_size
        
    async def process_batch(self, requests: List[BatchRequest], 
                          nlp_pipeline) -> List[BatchResult]:
        """적응형 배치 처리"""
        start_time = time.time()
        
        # 기본 배치 처리
        results = await super().process_batch(requests, nlp_pipeline)
        
        # 성능 기록
        processing_time = (time.time() - start_time) * 1000
        throughput = len(requests) / (processing_time / 1000)
        
        self.performance_history.append({
            "batch_size": self.batch_size,
            "request_count": len(requests),
            "processing_time_ms": processing_time,
            "throughput": throughput
        })
        
        # 적응형 조정
        if len(self.performance_history) >= self.adaptation_threshold:
            self._adapt_batch_size()
        
        return results
    
    def _adapt_batch_size(self):
        """배치 크기 적응형 조정"""
        if len(self.performance_history) < 3:
            return
        
        # 최근 성능 분석
        recent_performance = self.performance_history[-3:]
        avg_throughput = sum(p["throughput"] for p in recent_performance) / len(recent_performance)
        
        # 성능이 떨어지면 배치 크기 조정
        if len(self.performance_history) >= 6:
            prev_performance = self.performance_history[-6:-3]
            prev_avg_throughput = sum(p["throughput"] for p in prev_performance) / len(prev_performance)
            
            if avg_throughput < prev_avg_throughput * 0.9:  # 10% 성능 저하
                if self.batch_size > 5:
                    self.batch_size = max(5, self.batch_size - 2)
                    logger.info(f"Decreased batch size to {self.batch_size} due to performance drop")
            elif avg_throughput > prev_avg_throughput * 1.1:  # 10% 성능 향상
                if self.batch_size < 50:
                    self.batch_size = min(50, self.batch_size + 2)
                    logger.info(f"Increased batch size to {self.batch_size} due to performance gain")
        
        # 히스토리 크기 제한
        if len(self.performance_history) > 20:
            self.performance_history = self.performance_history[-10:]
    
    def get_adaptation_stats(self) -> Dict[str, Any]:
        """적응형 통계 조회"""
        base_stats = self.get_stats()
        
        adaptation_stats = {
            "current_batch_size": self.batch_size,
            "performance_history_length": len(self.performance_history),
            "recent_throughput": (
                self.performance_history[-1]["throughput"] 
                if self.performance_history else 0
            )
        }
        
        return {**base_stats, **adaptation_stats}


# 전역 배치 프로세서 인스턴스
_global_batch_processor: Optional[AdaptiveBatchProcessor] = None


def get_batch_processor() -> AdaptiveBatchProcessor:
    """전역 배치 프로세서 반환"""
    global _global_batch_processor
    
    if _global_batch_processor is None:
        _global_batch_processor = AdaptiveBatchProcessor()
    
    return _global_batch_processor


def configure_batch_processor(max_workers: int = 4, batch_size: int = 10):
    """배치 프로세서 설정"""
    global _global_batch_processor
    
    if _global_batch_processor:
        _global_batch_processor.shutdown()
    
    _global_batch_processor = AdaptiveBatchProcessor(max_workers, batch_size)