"""
Kafka Consumer for ML Service
Consumes raw news from 'raw-news' topic and processes them through NLP pipeline
"""
import json
import logging
from typing import Dict, Any, Optional
from kafka import KafkaConsumer
from kafka.errors import KafkaError
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


class MLConsumer:
    """Kafka consumer for processing raw news articles"""
    
    def __init__(self, bootstrap_servers: str = 'localhost:9092', 
                 group_id: str = 'ml-service',
                 topic: str = 'raw-news'):
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.topic = topic
        self.consumer = None
        self.pipeline = None  # Will be set when NLP pipeline is ready
        self.producer = None  # Will be set when producer is ready
        
    def connect(self):
        """Initialize Kafka consumer connection"""
        try:
            logger.info(f"Attempting to connect to Kafka at {self.bootstrap_servers}")
            self.consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                session_timeout_ms=30000,
                heartbeat_interval_ms=10000,
                request_timeout_ms=40000,
                connections_max_idle_ms=540000
            )
            logger.info(f"Connected to Kafka broker at {self.bootstrap_servers}")
            logger.info(f"Subscribed to topic: {self.topic}")
        except KafkaError as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            raise
            
    def set_pipeline(self, pipeline):
        """Set NLP pipeline for processing messages"""
        self.pipeline = pipeline
        
    def set_producer(self, producer):
        """Set producer for sending enriched messages"""
        self.producer = producer
        
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single news article through NLP pipeline"""
        try:
            # Extract content
            news_id = message.get('id', 'unknown')
            content = message.get('content', '')
            
            logger.info(f"Processing news article: {news_id}")
            
            # Process through NLP pipeline if available
            if self.pipeline:
                nlp_result = await self.pipeline.process(content)
                # Convert NLPResult object to dictionary for JSON serialization
                nlp_dict = {
                    "entities": [
                        {
                            "text": entity.text,
                            "type": entity.type,
                            "start": entity.start,
                            "end": entity.end,
                            "confidence": entity.confidence
                        } for entity in nlp_result.entities
                    ],
                    "sentiment": {
                        "label": nlp_result.sentiment.label,
                        "score": nlp_result.sentiment.score
                    },
                    "keywords": [
                        {
                            "text": keyword.text,
                            "score": keyword.score
                        } for keyword in nlp_result.keywords
                    ],
                    "risk_score": nlp_result.risk_score,
                    "processing_time_ms": nlp_result.processing_time_ms
                }
            else:
                # Mock processing for now
                nlp_dict = {
                    "entities": [],
                    "sentiment": {"label": "neutral", "score": 0.0},
                    "keywords": [],
                    "risk_score": 0.0
                }
            
            # Create enriched news object
            enriched = {
                "original": message,
                "nlp": nlp_dict,
                "processed_at": datetime.now().isoformat(),
                "ml_service_version": "1.0.0"
            }
            
            return enriched
            
        except Exception as e:
            logger.error(f"Error processing message {message.get('id')}: {e}")
            raise
            
    async def consume_messages(self):
        """Main consumption loop - non-blocking version"""
        if not self.consumer:
            raise RuntimeError("Consumer not connected. Call connect() first.")
            
        logger.info("Starting message consumption...")
        
        try:
            while True:
                # Poll for messages with a timeout (non-blocking)
                messages = self.consumer.poll(timeout_ms=1000)
                if not messages:
                    # No messages, yield control
                    await asyncio.sleep(0.1)
                    continue
                    
                for topic_partition, records in messages.items():
                    for message in records:
                        try:
                            # Process message
                            enriched = await self.process_message(message.value)
                            
                            # Send to enriched-news topic via producer  
                            logger.info(f"Producer status: {self.producer is not None}")
                            if self.producer:
                                try:
                                    logger.info(f"Attempting to send enriched message for: {message.value.get('id')}")
                                    await self.producer.send_enriched(enriched)
                                    logger.info(f"Successfully processed and sent message: {message.value.get('id')}")
                                except Exception as e:
                                    logger.error(f"Failed to send enriched message: {e}")
                                    logger.info(f"Successfully processed message (send failed): {message.value.get('id')}")
                            else:
                                logger.warning(f"No producer available, processed message: {message.value.get('id')}")
                            
                        except Exception as e:
                            logger.error(f"Failed to process message: {e}")
                            # TODO: Send to DLQ (Dead Letter Queue)
                    
        except asyncio.CancelledError:
            logger.info("Consumer task cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in consumer loop: {e}")
            raise
        finally:
            self.close()
            
    def close(self):
        """Close consumer connection"""
        if self.consumer:
            self.consumer.close()
            logger.info("Consumer connection closed")
            
    def consume_messages_sync(self):
        """Synchronous consumption loop for threading"""
        if not self.consumer:
            raise RuntimeError("Consumer not connected. Call connect() first.")
            
        logger.info("Starting synchronous message consumption...")
        
        try:
            for message in self.consumer:
                try:
                    # Create event loop for async processing
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    # Process message
                    enriched = loop.run_until_complete(self.process_message(message.value))
                    
                    # Send to enriched-news topic via producer
                    if self.producer:
                        try:
                            logger.info(f"Attempting to send enriched message for: {message.value.get('id')}")
                            loop.run_until_complete(self.producer.send_enriched(enriched))
                            logger.info(f"Successfully processed and sent message: {message.value.get('id')}")
                        except Exception as e:
                            logger.error(f"Failed to send enriched message: {e}")
                    else:
                        logger.warning(f"No producer available, processed message: {message.value.get('id')}")
                    
                except Exception as e:
                    logger.error(f"Failed to process message: {e}")
                    # TODO: Send to DLQ (Dead Letter Queue)
                    
        except KeyboardInterrupt:
            logger.info("Shutting down consumer...")
        finally:
            self.close()


class MockKafkaConsumer(MLConsumer):
    """Mock Kafka consumer for development/testing"""
    
    def __init__(self, mock_data_path: str = 'mock-data/raw-news.json'):
        super().__init__()
        self.mock_data_path = mock_data_path
        self.mock_messages = []
        
    def connect(self):
        """Load mock data instead of connecting to Kafka"""
        try:
            with open(self.mock_data_path, 'r', encoding='utf-8') as f:
                self.mock_messages = json.load(f)
            logger.info(f"Loaded {len(self.mock_messages)} mock messages")
        except Exception as e:
            logger.error(f"Failed to load mock data: {e}")
            raise
            
    async def consume_messages(self):
        """Process mock messages"""
        logger.info("Starting mock message consumption...")
        
        for message in self.mock_messages:
            try:
                enriched = await self.process_message(message)
                logger.info(f"Processed mock message: {message.get('id')}")
                
                # Simulate processing delay
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Failed to process mock message: {e}")
                
        logger.info("Finished processing all mock messages")
        
    def close(self):
        """No-op for mock consumer"""
        logger.info("Mock consumer closed")