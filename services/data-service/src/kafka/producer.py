"""
최적화된 Kafka Producer 구현
- 배치 처리
- 압축
- 비동기 전송
- 에러 처리 및 재시도
"""
import logging
import json
import asyncio
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from kafka import KafkaProducer
from kafka.errors import KafkaError
import threading
from queue import Queue, Empty
import os

logger = logging.getLogger(__name__)


@dataclass
class ProducerConfig:
    """Kafka Producer 설정"""
    bootstrap_servers: str = "localhost:9092"
    topic: str = "raw-news"
    batch_size: int = 16384  # 16KB
    linger_ms: int = 100  # 100ms 대기
    compression_type: str = "gzip"  # 압축
    max_request_size: int = 1048576  # 1MB
    acks: str = "1"  # 리더만 응답 대기
    retries: int = 3
    retry_backoff_ms: int = 100
    max_in_flight_requests_per_connection: int = 5
    enable_idempotence: bool = True
    
    @classmethod
    def from_env(cls) -> 'ProducerConfig':
        """환경변수에서 설정 로드"""
        return cls(
            bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
            topic=os.getenv("KAFKA_TOPIC_RAW_NEWS", "raw-news"),
            batch_size=int(os.getenv("KAFKA_BATCH_SIZE", "16384")),
            linger_ms=int(os.getenv("KAFKA_LINGER_MS", "100")),
            compression_type=os.getenv("KAFKA_COMPRESSION", "gzip"),
            acks=os.getenv("KAFKA_ACKS", "1"),
            retries=int(os.getenv("KAFKA_RETRIES", "3"))
        )


@dataclass
class NewsMessage:
    """뉴스 메시지 데이터 클래스"""
    id: str
    title: str
    content: str
    source: str
    url: str
    published_at: str
    crawled_at: str
    summary: Optional[str] = None
    author: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    images: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        data = asdict(self)
        # None 값 제거
        return {k: v for k, v in data.items() if v is not None}
    
    def to_json(self) -> str:
        """JSON 문자열로 변환"""
        return json.dumps(self.to_dict(), ensure_ascii=False, separators=(',', ':'))


class OptimizedKafkaProducer:
    """최적화된 Kafka Producer"""
    
    def __init__(self, config: ProducerConfig):
        self.config = config
        self.producer = None
        self._stats = {
            "total_sent": 0,
            "total_failed": 0,
            "total_bytes": 0,
            "avg_batch_size": 0,
            "last_error": None,
            "start_time": time.time()
        }
        self._lock = threading.Lock()
        self._message_queue = Queue()
        self._batch_thread = None
        self._running = False
        self._initialize_producer()
    
    def _initialize_producer(self):
        """Producer 초기화"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.config.bootstrap_servers.split(','),
                batch_size=self.config.batch_size,
                linger_ms=self.config.linger_ms,
                compression_type=self.config.compression_type,
                max_request_size=self.config.max_request_size,
                acks=self.config.acks,
                retries=self.config.retries,
                retry_backoff_ms=self.config.retry_backoff_ms,
                max_in_flight_requests_per_connection=self.config.max_in_flight_requests_per_connection,
                enable_idempotence=self.config.enable_idempotence,
                value_serializer=lambda v: v.encode('utf-8') if isinstance(v, str) else v,
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                # 성능 최적화
                buffer_memory=33554432,  # 32MB
                request_timeout_ms=30000,
                # 에러 처리
                api_version=(0, 10, 1)
            )
            logger.info(f"Kafka Producer initialized: {self.config.bootstrap_servers}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Kafka Producer: {e}")
            self.producer = None
            raise
    
    def start_batch_processing(self):
        """배치 처리 스레드 시작"""
        if self._batch_thread and self._batch_thread.is_alive():
            return
        
        self._running = True
        self._batch_thread = threading.Thread(target=self._batch_processor, daemon=True)
        self._batch_thread.start()
        logger.info("Batch processing thread started")
    
    def stop_batch_processing(self):
        """배치 처리 스레드 중지"""
        self._running = False
        if self._batch_thread:
            self._batch_thread.join(timeout=5)
        logger.info("Batch processing thread stopped")
    
    def _batch_processor(self):
        """배치 처리 스레드 함수"""
        batch = []
        last_send_time = time.time()
        
        while self._running:
            try:
                # 큐에서 메시지 가져오기 (100ms 대기)
                try:
                    message = self._message_queue.get(timeout=0.1)
                    batch.append(message)
                except Empty:
                    pass
                
                # 배치 전송 조건 확인
                current_time = time.time()
                should_send = (
                    len(batch) >= 100 or  # 배치 크기
                    (batch and current_time - last_send_time >= 1.0)  # 시간 제한
                )
                
                if should_send and batch:
                    self._send_batch(batch)
                    batch = []
                    last_send_time = current_time
                    
            except Exception as e:
                logger.error(f"Error in batch processor: {e}")
                time.sleep(1)
        
        # 종료 시 남은 배치 전송
        if batch:
            self._send_batch(batch)
    
    def _send_batch(self, batch: List[NewsMessage]):
        """배치 메시지 전송"""
        if not self.producer:
            logger.error("Producer not available")
            return
        
        try:
            start_time = time.time()
            
            for message in batch:
                # 키는 source로 설정 (파티셔닝)
                key = message.source
                value = message.to_json()
                
                future = self.producer.send(
                    self.config.topic,
                    key=key,
                    value=value,
                    headers=[
                        ('message_id', message.id.encode()),
                        ('source', message.source.encode()),
                        ('crawled_at', message.crawled_at.encode())
                    ]
                )
                
                # 콜백 등록
                future.add_callback(self._on_send_success, message)
                future.add_errback(self._on_send_error, message)
            
            # 배치 플러시
            self.producer.flush(timeout=10)
            
            # 통계 업데이트
            with self._lock:
                self._stats["total_sent"] += len(batch)
                self._stats["avg_batch_size"] = (
                    (self._stats["avg_batch_size"] * (self._stats["total_sent"] - len(batch)) + len(batch)) /
                    self._stats["total_sent"]
                )
            
            processing_time = time.time() - start_time
            logger.info(f"Sent batch of {len(batch)} messages in {processing_time:.3f}s")
            
        except Exception as e:
            logger.error(f"Failed to send batch: {e}")
            with self._lock:
                self._stats["total_failed"] += len(batch)
                self._stats["last_error"] = str(e)
    
    def _on_send_success(self, message: NewsMessage, record_metadata):
        """전송 성공 콜백"""
        with self._lock:
            self._stats["total_bytes"] += record_metadata.serialized_value_size
        
        logger.debug(
            f"Message sent successfully: {message.id} "
            f"to partition {record_metadata.partition} "
            f"at offset {record_metadata.offset}"
        )
    
    def _on_send_error(self, message: NewsMessage, exception):
        """전송 실패 콜백"""
        with self._lock:
            self._stats["total_failed"] += 1
            self._stats["last_error"] = str(exception)
        
        logger.error(f"Failed to send message {message.id}: {exception}")
    
    def send_message(self, message: NewsMessage) -> bool:
        """단일 메시지 전송 (큐에 추가)"""
        try:
            self._message_queue.put(message, timeout=1.0)
            return True
        except Exception as e:
            logger.error(f"Failed to queue message {message.id}: {e}")
            return False
    
    def send_messages(self, messages: List[NewsMessage]) -> int:
        """다중 메시지 전송"""
        sent_count = 0
        for message in messages:
            if self.send_message(message):
                sent_count += 1
        return sent_count
    
    def get_stats(self) -> Dict[str, Any]:
        """통계 정보 반환"""
        with self._lock:
            stats = self._stats.copy()
        
        # 추가 계산
        uptime = time.time() - stats["start_time"]
        stats["uptime_seconds"] = uptime
        stats["messages_per_second"] = stats["total_sent"] / uptime if uptime > 0 else 0
        stats["queue_size"] = self._message_queue.qsize()
        stats["is_connected"] = self.producer is not None
        
        return stats
    
    def health_check(self) -> Dict[str, Any]:
        """헬스 체크"""
        try:
            if not self.producer:
                return {"status": "unhealthy", "reason": "Producer not initialized"}
            
            # 메타데이터 요청으로 연결 확인
            metadata = self.producer.bootstrap_connected()
            
            return {
                "status": "healthy" if metadata else "degraded",
                "connected": metadata,
                "topic": self.config.topic,
                "bootstrap_servers": self.config.bootstrap_servers
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "reason": str(e),
                "topic": self.config.topic
            }
    
    def close(self):
        """Producer 종료"""
        logger.info("Closing Kafka Producer...")
        
        self.stop_batch_processing()
        
        if self.producer:
            try:
                self.producer.flush(timeout=10)
                self.producer.close(timeout=10)
            except Exception as e:
                logger.error(f"Error closing producer: {e}")
        
        logger.info("Kafka Producer closed")


# 글로벌 인스턴스
_producer_instance: Optional[OptimizedKafkaProducer] = None


def get_producer() -> OptimizedKafkaProducer:
    """글로벌 Producer 인스턴스 반환"""
    global _producer_instance
    
    if _producer_instance is None:
        config = ProducerConfig.from_env()
        _producer_instance = OptimizedKafkaProducer(config)
        _producer_instance.start_batch_processing()
    
    return _producer_instance


def close_producer():
    """글로벌 Producer 종료"""
    global _producer_instance
    
    if _producer_instance:
        _producer_instance.close()
        _producer_instance = None