"""Dead Letter Queue 처리"""
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from kafka import KafkaProducer
from kafka.errors import KafkaError
import os

logger = logging.getLogger(__name__)

class DeadLetterQueue:
    """Failed 메시지 처리를 위한 DLQ"""
    
    def __init__(self, dlq_topic: str = "graph-service-dlq"):
        self.dlq_topic = dlq_topic
        self.producer = None
        self._init_producer()
    
    def _init_producer(self):
        """Kafka Producer 초기화"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=3
            )
            logger.info("DLQ Producer initialized")
        except KafkaError as e:
            logger.error(f"Failed to initialize DLQ producer: {e}")
    
    def send(self, original_message: Dict[str, Any], error: Exception, 
             retry_count: int = 0, metadata: Optional[Dict] = None):
        """실패한 메시지를 DLQ로 전송
        
        Args:
            original_message: 원본 메시지
            error: 발생한 에러
            retry_count: 재시도 횟수
            metadata: 추가 메타데이터
        """
        if not self.producer:
            logger.error("DLQ Producer not initialized")
            return
        
        dlq_message = {
            "original_message": original_message,
            "error": {
                "type": type(error).__name__,
                "message": str(error),
                "traceback": None  # 필요시 traceback 추가
            },
            "retry_count": retry_count,
            "failed_at": datetime.now().isoformat(),
            "service": "graph-service",
            "metadata": metadata or {}
        }
        
        try:
            future = self.producer.send(self.dlq_topic, dlq_message)
            future.get(timeout=10)  # 동기 전송
            logger.info(f"Message sent to DLQ: {original_message.get('id', 'unknown')}")
        except Exception as e:
            logger.error(f"Failed to send message to DLQ: {e}")
            # DLQ 실패 시 로컬 파일에 저장 (최후의 수단)
            self._save_to_file(dlq_message)
    
    def _save_to_file(self, message: Dict[str, Any]):
        """DLQ 전송 실패 시 파일로 저장"""
        try:
            filename = f"dlq_fallback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join("/tmp", filename)
            
            with open(filepath, 'w') as f:
                json.dump(message, f, indent=2)
            
            logger.warning(f"DLQ message saved to file: {filepath}")
        except Exception as e:
            logger.error(f"Failed to save DLQ message to file: {e}")
    
    def close(self):
        """Producer 종료"""
        if self.producer:
            self.producer.flush()
            self.producer.close()

# 싱글톤 인스턴스
dlq = DeadLetterQueue()