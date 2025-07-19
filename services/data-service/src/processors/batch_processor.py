"""
배치 처리 시스템
- 100건 단위 배치 처리
- 동시성 제어
- 처리 상태 추적
- 에러 처리 및 재시도
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import time
from enum import Enum
import uuid
from concurrent.futures import ThreadPoolExecutor
import threading

logger = logging.getLogger(__name__)


class BatchStatus(str, Enum):
    """배치 처리 상태"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"  # 일부 실패


@dataclass
class BatchItem:
    """배치 처리 항목"""
    id: str
    data: Dict[str, Any]
    priority: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None
    error: Optional[str] = None
    retry_count: int = 0


@dataclass
class BatchResult:
    """배치 처리 결과"""
    batch_id: str
    status: BatchStatus
    items: List[BatchItem]
    successful_count: int = 0
    failed_count: int = 0
    processing_time: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_summary: List[str] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """성공률 계산"""
        total = self.successful_count + self.failed_count
        return self.successful_count / total if total > 0 else 0.0


@dataclass
class BatchProcessorConfig:
    """배치 처리 설정"""
    batch_size: int = 100
    max_concurrent_batches: int = 3
    max_retries: int = 3
    retry_delay: float = 1.0  # seconds
    timeout: float = 300.0  # 5 minutes
    enable_priority: bool = True
    queue_size_limit: int = 10000


class BatchProcessor:
    """배치 처리기"""
    
    def __init__(self, config: BatchProcessorConfig):
        self.config = config
        
        # 큐 및 상태 관리
        self._pending_items: List[BatchItem] = []
        self._processing_batches: Dict[str, BatchResult] = {}
        self._completed_batches: List[BatchResult] = []
        self._lock = threading.Lock()
        
        # 처리 상태
        self._running = False
        self._processor_task = None
        
        # 통계
        self._stats = {
            "total_items_processed": 0,
            "total_batches_processed": 0,
            "total_failed_items": 0,
            "total_processing_time": 0.0,
            "average_batch_size": 0.0,
            "average_processing_time": 0.0,
            "current_queue_size": 0,
            "current_processing_batches": 0,
            "start_time": datetime.now()
        }
        
        # 스레드 풀
        self._thread_pool = ThreadPoolExecutor(
            max_workers=self.config.max_concurrent_batches,
            thread_name_prefix="batch-processor"
        )
    
    def add_item(self, data: Dict[str, Any], priority: int = 0) -> str:
        """배치 처리 항목 추가"""
        with self._lock:
            if len(self._pending_items) >= self.config.queue_size_limit:
                raise Exception(f"Queue size limit exceeded: {self.config.queue_size_limit}")
            
            item = BatchItem(
                id=str(uuid.uuid4()),
                data=data,
                priority=priority
            )
            
            self._pending_items.append(item)
            
            # 우선순위 정렬 (높은 우선순위가 먼저)
            if self.config.enable_priority:
                self._pending_items.sort(key=lambda x: x.priority, reverse=True)
            
            self._stats["current_queue_size"] = len(self._pending_items)
            
            return item.id
    
    def add_items(self, items_data: List[Dict[str, Any]], priority: int = 0) -> List[str]:
        """다중 항목 추가"""
        item_ids = []
        for data in items_data:
            item_id = self.add_item(data, priority)
            item_ids.append(item_id)
        return item_ids
    
    def _create_batch(self) -> Optional[List[BatchItem]]:
        """배치 생성"""
        with self._lock:
            if len(self._pending_items) == 0:
                return None
            
            # 배치 크기만큼 항목 추출
            batch_size = min(self.config.batch_size, len(self._pending_items))
            batch_items = self._pending_items[:batch_size]
            self._pending_items = self._pending_items[batch_size:]
            
            self._stats["current_queue_size"] = len(self._pending_items)
            
            return batch_items
    
    async def _process_batch_async(
        self, 
        batch_items: List[BatchItem], 
        processor_func: Callable
    ) -> BatchResult:
        """배치 비동기 처리"""
        batch_id = str(uuid.uuid4())
        batch_result = BatchResult(
            batch_id=batch_id,
            status=BatchStatus.PROCESSING,
            items=batch_items,
            started_at=datetime.now()
        )
        
        # 처리 중 배치 등록
        with self._lock:
            self._processing_batches[batch_id] = batch_result
            self._stats["current_processing_batches"] = len(self._processing_batches)
        
        start_time = time.time()
        
        try:
            successful_count = 0
            failed_count = 0
            error_summary = []
            
            # 각 항목 처리
            for item in batch_items:
                try:
                    # 타임아웃 설정
                    result = await asyncio.wait_for(
                        processor_func(item.data),
                        timeout=self.config.timeout / len(batch_items)
                    )
                    
                    item.processed_at = datetime.now()
                    successful_count += 1
                    
                except Exception as e:
                    item.error = str(e)
                    failed_count += 1
                    error_summary.append(f"Item {item.id}: {str(e)}")
                    
                    logger.error(f"Error processing item {item.id}: {e}")
            
            # 결과 업데이트
            processing_time = time.time() - start_time
            
            batch_result.successful_count = successful_count
            batch_result.failed_count = failed_count
            batch_result.processing_time = processing_time
            batch_result.completed_at = datetime.now()
            batch_result.error_summary = error_summary
            
            # 상태 결정
            if failed_count == 0:
                batch_result.status = BatchStatus.COMPLETED
            elif successful_count == 0:
                batch_result.status = BatchStatus.FAILED
            else:
                batch_result.status = BatchStatus.PARTIAL
            
            logger.info(
                f"Batch {batch_id} completed: "
                f"{successful_count} success, {failed_count} failed, "
                f"{processing_time:.3f}s"
            )
            
        except Exception as e:
            # 배치 전체 실패
            batch_result.status = BatchStatus.FAILED
            batch_result.completed_at = datetime.now()
            batch_result.processing_time = time.time() - start_time
            batch_result.failed_count = len(batch_items)
            batch_result.error_summary = [f"Batch processing failed: {str(e)}"]
            
            logger.error(f"Batch {batch_id} failed: {e}")
        
        finally:
            # 처리 완료 배치 이동
            with self._lock:
                if batch_id in self._processing_batches:
                    del self._processing_batches[batch_id]
                
                self._completed_batches.append(batch_result)
                
                # 완료된 배치 히스토리 제한 (최근 100개만 유지)
                if len(self._completed_batches) > 100:
                    self._completed_batches = self._completed_batches[-100:]
                
                # 통계 업데이트
                self._stats["total_items_processed"] += successful_count
                self._stats["total_failed_items"] += failed_count
                self._stats["total_batches_processed"] += 1
                self._stats["total_processing_time"] += processing_time
                self._stats["current_processing_batches"] = len(self._processing_batches)
                
                # 평균 계산
                if self._stats["total_batches_processed"] > 0:
                    self._stats["average_batch_size"] = (
                        self._stats["total_items_processed"] / 
                        self._stats["total_batches_processed"]
                    )
                    self._stats["average_processing_time"] = (
                        self._stats["total_processing_time"] / 
                        self._stats["total_batches_processed"]
                    )
        
        return batch_result
    
    async def process_batches(self, processor_func: Callable) -> None:
        """배치들을 지속적으로 처리"""
        self._running = True
        
        try:
            while self._running:
                # 동시 처리 제한 확인
                if len(self._processing_batches) >= self.config.max_concurrent_batches:
                    await asyncio.sleep(0.1)
                    continue
                
                # 새 배치 생성
                batch_items = self._create_batch()
                if not batch_items:
                    await asyncio.sleep(0.5)  # 처리할 항목이 없으면 대기
                    continue
                
                # 배치 처리 시작 (비동기)
                asyncio.create_task(
                    self._process_batch_async(batch_items, processor_func)
                )
                
        except Exception as e:
            logger.error(f"Error in batch processor main loop: {e}")
        finally:
            self._running = False
    
    def start(self, processor_func: Callable):
        """배치 처리 시작"""
        if self._processor_task and not self._processor_task.done():
            logger.warning("Batch processor already running")
            return
        
        logger.info("Starting batch processor")
        self._processor_task = asyncio.create_task(
            self.process_batches(processor_func)
        )
    
    def stop(self):
        """배치 처리 중지"""
        logger.info("Stopping batch processor")
        self._running = False
        
        if self._processor_task:
            self._processor_task.cancel()
    
    def get_stats(self) -> Dict[str, Any]:
        """통계 정보 반환"""
        with self._lock:
            stats = self._stats.copy()
        
        # 추가 계산
        uptime = datetime.now() - stats["start_time"]
        stats["uptime_seconds"] = uptime.total_seconds()
        
        if stats["uptime_seconds"] > 0:
            stats["items_per_second"] = (
                stats["total_items_processed"] / stats["uptime_seconds"]
            )
        else:
            stats["items_per_second"] = 0.0
        
        # 성공률
        total_processed = stats["total_items_processed"] + stats["total_failed_items"]
        if total_processed > 0:
            stats["success_rate"] = stats["total_items_processed"] / total_processed
        else:
            stats["success_rate"] = 0.0
        
        return stats
    
    def get_queue_status(self) -> Dict[str, Any]:
        """큐 상태 반환"""
        with self._lock:
            return {
                "pending_items": len(self._pending_items),
                "processing_batches": len(self._processing_batches),
                "completed_batches": len(self._completed_batches),
                "queue_limit": self.config.queue_size_limit,
                "is_running": self._running
            }
    
    def get_recent_batches(self, limit: int = 10) -> List[Dict[str, Any]]:
        """최근 배치 결과 반환"""
        with self._lock:
            recent_batches = self._completed_batches[-limit:]
        
        return [
            {
                "batch_id": batch.batch_id,
                "status": batch.status.value,
                "successful_count": batch.successful_count,
                "failed_count": batch.failed_count,
                "success_rate": batch.success_rate,
                "processing_time": batch.processing_time,
                "started_at": batch.started_at.isoformat() if batch.started_at else None,
                "completed_at": batch.completed_at.isoformat() if batch.completed_at else None
            }
            for batch in recent_batches
        ]
    
    def clear_completed_batches(self):
        """완료된 배치 히스토리 삭제"""
        with self._lock:
            self._completed_batches.clear()
        logger.info("Cleared completed batch history")
    
    def close(self):
        """배치 처리기 종료"""
        self.stop()
        
        # 스레드 풀 종료
        self._thread_pool.shutdown(wait=True)
        
        logger.info("Batch processor closed")


# 글로벌 인스턴스
_batch_processor: Optional[BatchProcessor] = None


def get_batch_processor() -> BatchProcessor:
    """글로벌 배치 처리기 인스턴스 반환"""
    global _batch_processor
    
    if _batch_processor is None:
        config = BatchProcessorConfig()
        _batch_processor = BatchProcessor(config)
    
    return _batch_processor


def close_batch_processor():
    """글로벌 배치 처리기 종료"""
    global _batch_processor
    
    if _batch_processor:
        _batch_processor.close()
        _batch_processor = None