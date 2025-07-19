"""그래프 노드 정의"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

class NodeType(Enum):
    """노드 타입"""
    COMPANY = "Company"
    PERSON = "Person"
    EVENT = "Event"
    RISK_EVENT = "RiskEvent"
    NEWS_ARTICLE = "NewsArticle"

class RiskType(Enum):
    """리스크 타입"""
    FINANCIAL = "FINANCIAL"
    LEGAL = "LEGAL"
    REPUTATION = "REPUTATION"
    OPERATIONAL = "OPERATIONAL"
    STRATEGIC = "STRATEGIC"
    COMPLIANCE = "COMPLIANCE"

class BaseNode:
    """기본 노드 클래스"""
    def __init__(self, id: str):
        self.id = id
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def get_create_query(self) -> tuple:
        """CREATE 쿼리 생성"""
        raise NotImplementedError

@dataclass
class Company:
    """기업 노드"""
    id: str
    name: str
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    risk_score: float = 5.0
    country: Optional[str] = None
    aliases: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'industry': self.industry,
            'market_cap': self.market_cap,
            'risk_score': self.risk_score,
            'country': self.country,
            'aliases': self.aliases,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def get_create_query(self) -> tuple:
        query = """
        MERGE (c:Company {id: $id})
        SET c += $properties
        RETURN c
        """
        return query, {'id': self.id, 'properties': self.to_dict()}

@dataclass
class Person:
    """인물 노드"""
    id: str
    name: str
    title: Optional[str] = None
    organization: Optional[str] = None
    nationality: Optional[str] = None
    aliases: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'title': self.title,
            'organization': self.organization,
            'nationality': self.nationality,
            'aliases': self.aliases,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def get_create_query(self) -> tuple:
        query = """
        MERGE (p:Person {id: $id})
        SET p += $properties
        RETURN p
        """
        return query, {'id': self.id, 'properties': self.to_dict()}

@dataclass
class Event:
    """이벤트 노드"""
    id: str
    type: str
    title: str
    description: Optional[str] = None
    occurred_at: datetime = field(default_factory=datetime.now)
    location: Optional[str] = None
    impact_score: float = 5.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'type': self.type,
            'title': self.title,
            'description': self.description,
            'occurred_at': self.occurred_at.isoformat(),
            'location': self.location,
            'impact_score': self.impact_score,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def get_create_query(self) -> tuple:
        query = """
        CREATE (e:Event {id: $id})
        SET e += $properties
        RETURN e
        """
        return query, {'id': self.id, 'properties': self.to_dict()}

@dataclass
class RiskEvent:
    """리스크 이벤트 노드"""
    id: str
    type: str
    title: str
    risk_type: RiskType
    severity: int  # 1-10
    description: Optional[str] = None
    occurred_at: datetime = field(default_factory=datetime.now)
    location: Optional[str] = None
    impact_score: float = 5.0
    probability: float = 0.5  # 0-1
    mitigation_status: str = "OPEN"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'type': self.type,
            'title': self.title,
            'description': self.description,
            'occurred_at': self.occurred_at.isoformat(),
            'location': self.location,
            'impact_score': self.impact_score,
            'risk_type': self.risk_type.value,
            'severity': self.severity,
            'probability': self.probability,
            'mitigation_status': self.mitigation_status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def get_create_query(self) -> tuple:
        query = """
        CREATE (r:RiskEvent:Event {id: $id})
        SET r += $properties
        RETURN r
        """
        return query, {'id': self.id, 'properties': self.to_dict()}

@dataclass
class NewsArticle:
    """뉴스 기사 노드"""
    id: str
    title: str
    content: Optional[str] = None
    url: Optional[str] = None
    published_at: datetime = field(default_factory=datetime.now)
    source: Optional[str] = None
    sentiment: float = 0.0  # -1 to 1
    risk_indicators: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'url': self.url,
            'published_at': self.published_at.isoformat(),
            'source': self.source,
            'sentiment': self.sentiment,
            'risk_indicators': self.risk_indicators,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def get_create_query(self) -> tuple:
        query = """
        CREATE (n:NewsArticle {id: $id})
        SET n += $properties
        RETURN n
        """
        return query, {'id': self.id, 'properties': self.to_dict()}