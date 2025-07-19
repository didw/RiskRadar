"""그래프 스키마 정의 및 검증"""
from typing import List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum

class EntityType(str, Enum):
    """엔티티 타입"""
    COMPANY = "COMPANY"
    PERSON = "PERSON"
    LOCATION = "LOCATION"
    ORGANIZATION = "ORGANIZATION"
    PRODUCT = "PRODUCT"

class EntitySchema(BaseModel):
    """ML 서비스에서 받는 엔티티 스키마"""
    text: str
    type: EntityType
    confidence: float = Field(ge=0.0, le=1.0)
    start_pos: int
    end_pos: int
    
    class Config:
        use_enum_values = True

class EnrichedNewsSchema(BaseModel):
    """Kafka에서 받는 enriched-news 메시지 스키마"""
    id: str
    title: str
    content: str
    url: str
    published_at: datetime
    source: str
    
    # ML 분석 결과
    entities: List[EntitySchema]
    sentiment: float = Field(ge=-1.0, le=1.0)
    risk_score: float = Field(ge=0.0, le=10.0)
    risk_indicators: List[str] = []
    topics: List[str] = []
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class GraphNodeCreate(BaseModel):
    """그래프 노드 생성 요청"""
    type: str
    properties: Dict[str, Any]

class GraphRelationshipCreate(BaseModel):
    """그래프 관계 생성 요청"""
    from_type: str
    from_id: str
    to_type: str
    to_id: str
    relationship_type: str
    properties: Dict[str, Any] = {}

class GraphQueryRequest(BaseModel):
    """그래프 쿼리 요청"""
    entity_id: str
    depth: int = Field(default=1, ge=1, le=3)
    relationship_types: List[str] = []
    
class NetworkRiskRequest(BaseModel):
    """네트워크 리스크 분석 요청"""
    company_id: str
    depth: int = Field(default=2, ge=1, le=3)
    min_risk_score: float = Field(default=7.0, ge=0.0, le=10.0)

class GraphStatsResponse(BaseModel):
    """그래프 통계 응답"""
    node_count: int
    relationship_count: int
    node_types: Dict[str, int]
    relationship_types: Dict[str, int]
    timestamp: datetime

class NetworkAnalysisResponse(BaseModel):
    """네트워크 분석 응답"""
    central_entity: str
    connected_entities: int
    average_risk_score: float
    high_risk_entities: List[Dict[str, Any]]
    risk_paths: List[List[str]]
    analysis_timestamp: datetime