"""
Configuration for ML Service
"""
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # Service info
    service_name: str = "ml-service"
    service_version: str = "1.0.0"
    
    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8002
    api_workers: int = 1
    
    # Kafka settings
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_consumer_group: str = "ml-service"
    kafka_input_topic: str = "raw-news"
    kafka_output_topic: str = "enriched-news"
    
    # Model settings
    model_path: str = "/app/models"
    model_version: str = "v1.0.0"
    tokenizer_backend: str = "komoran"  # mecab, komoran, hannanum
    
    # Processing settings
    batch_size: int = 32
    max_processing_time_ms: int = 100
    enable_gpu: bool = False
    
    # Development settings
    use_mock_kafka: bool = True
    use_simple_tokenizer: bool = False
    use_mock_ner: bool = True  # Use mock NER model by default
    mock_data_path: str = "mock-data/raw-news.json"
    
    # NER model settings
    ner_model_name: str = "Babelscape/wikineural-multilingual-ner"
    huggingface_api_token: Optional[str] = None  # Set via environment variable
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    """Get application settings"""
    return Settings()