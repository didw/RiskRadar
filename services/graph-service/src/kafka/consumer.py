"""Kafka Consumer 구현"""
import os
import json
import logging
import asyncio
from typing import Optional
from kafka import KafkaConsumer
from kafka.errors import KafkaError
import threading

from src.kafka.handlers import GraphMessageHandler

logger = logging.getLogger(__name__)

class GraphKafkaConsumer:
    """Graph Service Kafka Consumer"""
    
    def __init__(self):
        self.consumer: Optional[KafkaConsumer] = None
        self.handler = GraphMessageHandler()
        self.running = False
        self.consumer_thread: Optional[threading.Thread] = None
        
        # Kafka 설정
        # Docker Compose 환경에서는 서비스명 사용
        is_docker = os.getenv("DOCKER_ENV", "false").lower() == "true"
        default_kafka = "kafka:9092" if is_docker else "localhost:9092"
        
        self.bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", default_kafka)
        self.group_id = os.getenv("KAFKA_GROUP_ID", "graph-service-group")
        self.topic = "enriched-news"
        
    def start(self):
        """Consumer 시작"""
        if self.running:
            logger.warning("Consumer already running")
            return
            
        self.running = True
        self.consumer_thread = threading.Thread(target=self._consume_messages)
        self.consumer_thread.daemon = True
        self.consumer_thread.start()
        logger.info("Kafka consumer started")
        
    def stop(self):
        """Consumer 중지"""
        self.running = False
        if self.consumer:
            self.consumer.close()
        if self.consumer_thread:
            self.consumer_thread.join(timeout=5)
        logger.info("Kafka consumer stopped")
        
    def _consume_messages(self):
        """메시지 소비 루프"""
        try:
            self.consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='latest',
                enable_auto_commit=True,
                max_poll_records=10
            )
            
            logger.info(f"Connected to Kafka topic: {self.topic}")
            
            while self.running:
                try:
                    # 메시지 폴링
                    messages = self.consumer.poll(timeout_ms=1000)
                    
                    for topic_partition, records in messages.items():
                        for record in records:
                            asyncio.run(self._process_message(record.value))
                            
                except Exception as e:
                    logger.error(f"Error processing messages: {e}")
                    
        except KafkaError as e:
            logger.error(f"Kafka consumer error: {e}")
        finally:
            if self.consumer:
                self.consumer.close()
                
    async def _process_message(self, message: dict):
        """개별 메시지 처리"""
        try:
            logger.debug(f"Processing message: {message.get('id', 'unknown')}")
            await self.handler.handle_enriched_news(message)
            logger.info(f"Successfully processed message: {message.get('id', 'unknown')}")
        except Exception as e:
            logger.error(f"Failed to process message: {e}", exc_info=True)
            # 실패한 메시지는 DLQ로 보내거나 재시도 로직 추가 가능

# 싱글톤 인스턴스
consumer = GraphKafkaConsumer()