"""
Kafka Producer for ML Service
Publishes enriched news to 'enriched-news' topic
"""
import json
import logging
from typing import Dict, Any
from kafka import KafkaProducer
from kafka.errors import KafkaError

logger = logging.getLogger(__name__)


class MLProducer:
    """Kafka producer for publishing enriched news"""
    
    def __init__(self, bootstrap_servers: str = 'localhost:9092',
                 topic: str = 'enriched-news'):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.producer = None
        
    def connect(self):
        """Initialize Kafka producer connection"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8'),
                acks='all',  # Wait for all replicas
                retries=3,
                max_in_flight_requests_per_connection=1
            )
            logger.info(f"Connected to Kafka broker at {self.bootstrap_servers}")
        except KafkaError as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            raise
            
    async def send_enriched(self, enriched_news: Dict[str, Any]):
        """Send enriched news to Kafka topic"""
        if not self.producer:
            raise RuntimeError("Producer not connected. Call connect() first.")
            
        try:
            # Send message
            future = self.producer.send(self.topic, enriched_news)
            
            # Wait for send to complete
            record_metadata = future.get(timeout=10)
            
            logger.info(
                f"Sent enriched news {enriched_news['original']['id']} "
                f"to topic {record_metadata.topic} "
                f"partition {record_metadata.partition} "
                f"offset {record_metadata.offset}"
            )
            
        except KafkaError as e:
            logger.error(f"Failed to send message: {e}")
            raise
            
    def flush(self):
        """Flush any pending messages"""
        if self.producer:
            self.producer.flush()
            
    def close(self):
        """Close producer connection"""
        if self.producer:
            self.producer.close()
            logger.info("Producer connection closed")


class MockKafkaProducer(MLProducer):
    """Mock Kafka producer for development/testing"""
    
    def __init__(self, output_file: str = 'mock-data/enriched-news.json'):
        super().__init__()
        self.output_file = output_file
        self.messages = []
        
    def connect(self):
        """Initialize mock producer"""
        logger.info("Mock producer initialized")
        
    async def send_enriched(self, enriched_news: Dict[str, Any]):
        """Store message in memory and write to file"""
        self.messages.append(enriched_news)
        logger.info(f"Mock: Sent enriched news {enriched_news['original']['id']}")
        
        # Write to file for inspection
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(self.messages, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to write mock output: {e}")
            
    def flush(self):
        """No-op for mock producer"""
        pass
        
    def close(self):
        """Save final state"""
        if self.messages:
            try:
                with open(self.output_file, 'w', encoding='utf-8') as f:
                    json.dump(self.messages, f, ensure_ascii=False, indent=2)
                logger.info(f"Saved {len(self.messages)} messages to {self.output_file}")
            except Exception as e:
                logger.error(f"Failed to save mock messages: {e}")