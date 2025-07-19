"""
Main entry point for ML Service
"""
import asyncio
import logging
import signal
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .config import get_settings
from .api import router, set_pipeline
from .processors import NLPPipeline, ProcessingConfig
from .kafka import MockKafkaConsumer, MockKafkaProducer, MLConsumer, MLProducer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
consumer = None
producer = None
pipeline = None
consumer_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global consumer, producer, pipeline, consumer_task
    
    settings = get_settings()
    logger.info(f"Starting {settings.service_name} v{settings.service_version}")
    
    try:
        # Initialize NLP pipeline
        config = ProcessingConfig(
            tokenizer_backend=settings.tokenizer_backend,
            use_simple_tokenizer=settings.use_simple_tokenizer
        )
        pipeline = NLPPipeline(config)
        set_pipeline(pipeline)
        logger.info("NLP pipeline initialized")
        
        # Initialize Kafka components
        if settings.use_mock_kafka:
            logger.info("Using mock Kafka components")
            consumer = MockKafkaConsumer(settings.mock_data_path)
            producer = MockKafkaProducer()
        else:
            logger.info("Using real Kafka components")
            consumer = MLConsumer(
                bootstrap_servers=settings.kafka_bootstrap_servers,
                group_id=settings.kafka_consumer_group,
                topic=settings.kafka_input_topic
            )
            producer = MLProducer(
                bootstrap_servers=settings.kafka_bootstrap_servers,
                topic=settings.kafka_output_topic
            )
            
        # Connect Kafka components
        consumer.connect()
        producer.connect()
        
        # Set pipeline in consumer
        consumer.set_pipeline(pipeline)
        
        # Start consumer task
        consumer_task = asyncio.create_task(consumer.consume_messages())
        logger.info("Kafka consumer started")
        
    except Exception as e:
        logger.error(f"Failed to initialize service: {e}")
        raise
        
    yield
    
    # Cleanup
    logger.info("Shutting down service...")
    
    if consumer_task:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
            
    if consumer:
        consumer.close()
    if producer:
        producer.close()
        
    logger.info("Service shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="RiskRadar ML Service",
    description="NLP processing service for Korean financial news",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "ML Service",
        "version": "1.0.0",
        "status": "running"
    }


def handle_shutdown(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}")
    sys.exit(0)


def main():
    """Main function"""
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    
    # Get settings
    settings = get_settings()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, settings.log_level))
    
    # Run the application
    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        workers=settings.api_workers,
        reload=False
    )


if __name__ == "__main__":
    main()