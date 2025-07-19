from fastapi import FastAPI
from contextlib import asynccontextmanager
import os
import json
from kafka import KafkaProducer
from datetime import datetime
import logging

from src.api.routes import router as api_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Data Service", version="0.3.0")

# Kafka producer (initialized on startup)
producer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global producer
    kafka_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    try:
        producer = KafkaProducer(
            bootstrap_servers=kafka_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        logger.info(f"Connected to Kafka at {kafka_servers}")
    except Exception as e:
        logger.error(f"Failed to connect to Kafka: {e}")
        producer = None
    
    yield
    
    # Shutdown
    if producer:
        producer.close()

app = FastAPI(title="Data Service", version="0.3.0", lifespan=lifespan)

# API 라우터 등록
app.include_router(api_router)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "data-service",
        "timestamp": datetime.now().isoformat(),
        "kafka": "connected" if producer else "disconnected"
    }

@app.post("/simulate-news")
async def simulate_news():
    """임시 뉴스 데이터 생성 및 Kafka 전송"""
    if not producer:
        return {"error": "Kafka not connected"}
    
    test_news = {
        "id": f"test-{datetime.now().timestamp()}",
        "title": "테스트 뉴스 제목",
        "content": "테스트 뉴스 내용입니다.",
        "source": "test-source",
        "url": "https://example.com/test",
        "published_at": datetime.now().isoformat(),
        "crawled_at": datetime.now().isoformat()
    }
    
    try:
        future = producer.send('raw-news', test_news)
        producer.flush()
        return {"status": "sent", "data": test_news}
    except Exception as e:
        logger.error(f"Failed to send to Kafka: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)