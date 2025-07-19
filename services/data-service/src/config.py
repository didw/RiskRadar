"""
Configuration settings for Data Service
"""
import os
from pathlib import Path
from typing import Optional
from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Service info
    SERVICE_NAME: str = "data-service"
    SERVICE_VERSION: str = "0.1.0"
    
    # API settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8001
    API_WORKERS: int = 4
    
    # Kafka settings
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
    KAFKA_TOPIC_RAW_NEWS: str = "raw-news"
    KAFKA_PRODUCER_TIMEOUT: int = 10
    KAFKA_MAX_BATCH_SIZE: int = 100
    
    # Redis settings (for caching/deduplication)
    REDIS_URL: str = "redis://redis:6379"
    REDIS_TTL: int = 86400  # 24 hours
    
    # Crawler settings
    CRAWLER_USER_AGENT: str = "RiskRadar/1.0 (News Monitoring System)"
    CRAWLER_TIMEOUT: int = 30
    CRAWLER_MAX_RETRIES: int = 3
    CRAWLER_RATE_LIMIT: float = 0.5  # requests per second
    
    # Crawler targets
    CRAWLER_MAX_ARTICLES_PER_SOURCE: int = 50
    CRAWLER_SCHEDULE_MINUTES: int = 15  # Run every 15 minutes
    
    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json or text
    
    # Development
    DEBUG: bool = False
    MOCK_KAFKA: bool = False  # Use JSON files instead of Kafka in dev
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()


# Crawler configurations
CRAWLER_CONFIGS = {
    "chosun": {
        "name": "조선일보",
        "base_url": "https://www.chosun.com",
        "rate_limit": 0.5,
        "sections": ["/economy/", "/national/", "/international/", "/politics/"]
    },
    "hankyung": {
        "name": "한국경제",
        "base_url": "https://www.hankyung.com",
        "rate_limit": 0.5,
        "sections": ["/economy/", "/society/", "/international/", "/politics/"]
    },
    "joongang": {
        "name": "중앙일보", 
        "base_url": "https://www.joongang.co.kr",
        "rate_limit": 0.5,
        "sections": ["/economy/", "/society/", "/international/", "/politics/"]
    },
    "yonhap": {
        "name": "연합뉴스",
        "base_url": "https://www.yna.co.kr",
        "rate_limit": 0.3,  # More strict for Yonhap
        "sections": ["/economy/", "/society/", "/international/", "/politics/"]
    },
    "mk": {
        "name": "매일경제",
        "base_url": "https://www.mk.co.kr",
        "rate_limit": 0.5,
        "sections": ["/economy/", "/stock/", "/realestate/", "/it/"]
    }
}