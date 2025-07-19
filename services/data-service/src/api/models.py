from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class CrawlerStatus(str, Enum):
    """크롤러 상태"""
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


class CrawlerInfo(BaseModel):
    """크롤러 정보"""
    id: str = Field(..., description="크롤러 ID")
    source: str = Field(..., description="뉴스 소스")
    status: CrawlerStatus = Field(..., description="크롤러 상태")
    last_crawl: Optional[datetime] = Field(None, description="마지막 크롤링 시간")
    items_collected: int = Field(0, description="수집된 기사 수")
    error_count: int = Field(0, description="에러 발생 수")


class CrawlerStatusResponse(BaseModel):
    """크롤러 상태 응답"""
    crawlers: List[CrawlerInfo] = Field(..., description="크롤러 목록")


class CrawlRequest(BaseModel):
    """크롤링 요청"""
    source: Optional[str] = Field(None, description="특정 소스만 크롤링 (선택사항)")
    limit: Optional[int] = Field(10, description="수집할 기사 수 제한")


class CrawlResponse(BaseModel):
    """크롤링 응답"""
    status: str = Field(..., description="처리 상태")
    message: str = Field(..., description="처리 메시지")
    crawled_count: int = Field(0, description="크롤링된 기사 수")
    errors: List[str] = Field(default_factory=list, description="에러 목록")
    data: List[Dict[str, Any]] = Field(default_factory=list, description="크롤링된 데이터")


class CollectionStatsRequest(BaseModel):
    """수집 통계 요청"""
    from_time: Optional[datetime] = Field(None, description="시작 시간")
    to_time: Optional[datetime] = Field(None, description="종료 시간")


class CollectionStatsResponse(BaseModel):
    """수집 통계 응답"""
    total_items: int = Field(0, description="총 수집 건수")
    by_source: Dict[str, int] = Field(default_factory=dict, description="소스별 통계")
    by_hour: List[Dict[str, Any]] = Field(default_factory=list, description="시간별 통계")
    duplicate_rate: float = Field(0.0, description="중복률")
    time_range: Dict[str, datetime] = Field(default_factory=dict, description="조회 기간")