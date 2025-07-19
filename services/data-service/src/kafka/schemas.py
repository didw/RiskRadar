"""
Kafka message schemas for Data Service
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl


class NewsArticle(BaseModel):
    """News article data model matching TRD specifications"""
    
    # Required fields
    id: str = Field(..., description="Unique article identifier")
    title: str = Field(..., description="Article title")
    content: str = Field(..., description="Full article content")
    source: str = Field(..., description="News source identifier (e.g., 'chosun')")
    url: HttpUrl = Field(..., description="Original article URL")
    published_at: str = Field(..., description="Article publication time (ISO format)")
    crawled_at: str = Field(..., description="Time when article was crawled (ISO format)")
    
    # Optional fields
    summary: str = Field(default="", description="Article summary or description")
    author: str = Field(default="", description="Article author/reporter")
    category: str = Field(default="", description="News category")
    tags: List[str] = Field(default_factory=list, description="Article tags/keywords")
    image_url: Optional[str] = Field(default="", description="Main article image URL")
    
    # Metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (source_name, language, etc.)"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "id": "a1b2c3d4e5f6",
                "title": "경제 성장률 3.5% 전망",
                "content": "올해 경제 성장률이 3.5%를 기록할 것으로...",
                "summary": "경제 전문가들은 올해 성장률을...",
                "source": "chosun",
                "url": "https://www.chosun.com/economy/2024/01/15/example",
                "published_at": "2024-01-15T10:30:00+09:00",
                "crawled_at": "2024-01-15T10:35:00+09:00",
                "author": "김경제 기자",
                "category": "경제",
                "tags": ["경제", "성장률", "GDP"],
                "image_url": "https://image.chosun.com/example.jpg",
                "metadata": {
                    "source_name": "조선일보",
                    "language": "ko",
                    "word_count": 850
                }
            }
        }


class KafkaMessage(BaseModel):
    """Wrapper for Kafka messages"""
    
    key: str = Field(..., description="Message key (usually article ID)")
    value: NewsArticle = Field(..., description="Message payload")
    topic: str = Field(default="raw-news", description="Kafka topic")
    partition: Optional[int] = Field(default=None, description="Target partition")
    timestamp: Optional[str] = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Message timestamp"
    )
    headers: Optional[Dict[str, str]] = Field(
        default_factory=dict,
        description="Message headers"
    )


class CrawlerStatus(BaseModel):
    """Crawler status for monitoring"""
    
    crawler_id: str = Field(..., description="Crawler identifier")
    status: str = Field(..., description="Current status (running/idle/error)")
    last_run: Optional[str] = Field(default=None, description="Last run timestamp")
    articles_crawled: int = Field(default=0, description="Articles crawled in last run")
    errors: int = Field(default=0, description="Errors in last run")
    next_run: Optional[str] = Field(default=None, description="Next scheduled run")
    message: str = Field(default="", description="Status message")


class CrawlerMetrics(BaseModel):
    """Metrics for monitoring dashboard"""
    
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    total_articles: int = Field(..., description="Total articles crawled")
    articles_per_hour: float = Field(..., description="Articles crawled per hour")
    success_rate: float = Field(..., description="Success rate percentage")
    avg_crawl_time: float = Field(..., description="Average crawl time in seconds")
    kafka_lag: int = Field(default=0, description="Kafka producer lag")
    active_crawlers: List[str] = Field(default_factory=list, description="Active crawlers")