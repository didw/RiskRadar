"""그래프 관계 정의"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

class RelationshipType(Enum):
    """관계 타입"""
    # 기업 간 관계
    COMPETES_WITH = "COMPETES_WITH"
    PARTNERS_WITH = "PARTNERS_WITH"
    OWNS = "OWNS"
    SUBSIDIARY_OF = "SUBSIDIARY_OF"
    SUPPLIES_TO = "SUPPLIES_TO"
    
    # 인물-기업 관계
    WORKS_AT = "WORKS_AT"
    CEO_OF = "CEO_OF"
    BOARD_MEMBER_OF = "BOARD_MEMBER_OF"
    FOUNDED = "FOUNDED"
    
    # 이벤트 관계
    AFFECTS = "AFFECTS"
    CAUSED_BY = "CAUSED_BY"
    RELATED_TO = "RELATED_TO"
    
    # 뉴스 관계
    MENTIONED_IN = "MENTIONED_IN"
    REPORTED_BY = "REPORTED_BY"
    
    # 시계열 관계
    PRECEDED_BY = "PRECEDED_BY"
    FOLLOWED_BY = "FOLLOWED_BY"

@dataclass
class BaseRelationship:
    """기본 관계 클래스"""
    type: RelationshipType
    from_id: str
    to_id: str
    created_at: datetime = field(default_factory=datetime.now)
    confidence: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            'created_at': self.created_at.isoformat(),
            'confidence': self.confidence
        }
    
    def get_create_query(self) -> tuple:
        """CREATE 쿼리 생성"""
        raise NotImplementedError

@dataclass
class CompanyRelationship(BaseRelationship):
    """기업 간 관계"""
    strength: float = 0.5  # 관계 강도 0-1
    since: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            'strength': self.strength
        })
        if self.since:
            data['since'] = self.since.isoformat()
        return data
    
    def get_create_query(self) -> tuple:
        query = f"""
        MATCH (a {{id: $from_id}}), (b {{id: $to_id}})
        CREATE (a)-[r:{self.type.value} $properties]->(b)
        RETURN r
        """
        return query, {
            'from_id': self.from_id,
            'to_id': self.to_id,
            'properties': self.to_dict()
        }

@dataclass
class PersonCompanyRelationship(BaseRelationship):
    """인물-기업 관계"""
    role: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_current: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            'role': self.role,
            'is_current': self.is_current
        })
        if self.start_date:
            data['start_date'] = self.start_date.isoformat()
        if self.end_date:
            data['end_date'] = self.end_date.isoformat()
        return data
    
    def get_create_query(self) -> tuple:
        query = f"""
        MATCH (p:Person {{id: $from_id}}), (c:Company {{id: $to_id}})
        CREATE (p)-[r:{self.type.value} $properties]->(c)
        RETURN r
        """
        return query, {
            'from_id': self.from_id,
            'to_id': self.to_id,
            'properties': self.to_dict()
        }

@dataclass
class EventRelationship(BaseRelationship):
    """이벤트 관계"""
    impact_type: Optional[str] = None
    impact_severity: int = 5  # 1-10
    causation_confidence: float = 0.5  # 인과관계 신뢰도
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            'impact_type': self.impact_type,
            'impact_severity': self.impact_severity,
            'causation_confidence': self.causation_confidence
        })
        return data
    
    def get_create_query(self) -> tuple:
        query = f"""
        MATCH (a {{id: $from_id}}), (b {{id: $to_id}})
        CREATE (a)-[r:{self.type.value} $properties]->(b)
        RETURN r
        """
        return query, {
            'from_id': self.from_id,
            'to_id': self.to_id,
            'properties': self.to_dict()
        }

@dataclass
class MentionRelationship(BaseRelationship):
    """언급 관계 (뉴스-엔티티)"""
    sentiment: float = 0.0  # -1 to 1
    prominence: float = 0.5  # 0-1 (언급 중요도)
    context: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            'sentiment': self.sentiment,
            'prominence': self.prominence,
            'context': self.context
        })
        return data
    
    def get_create_query(self) -> tuple:
        query = f"""
        MATCH (e {{id: $from_id}}), (n:NewsArticle {{id: $to_id}})
        CREATE (e)-[r:{self.type.value} $properties]->(n)
        RETURN r
        """
        return query, {
            'from_id': self.from_id,
            'to_id': self.to_id,
            'properties': self.to_dict()
        }

@dataclass
class TimeSeriesRelationship(BaseRelationship):
    """시계열 관계 (이벤트 간)"""
    time_gap_hours: float = 0.0
    correlation_score: float = 0.0  # 상관관계 점수
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            'time_gap_hours': self.time_gap_hours,
            'correlation_score': self.correlation_score
        })
        return data
    
    def get_create_query(self) -> tuple:
        query = f"""
        MATCH (e1:Event {{id: $from_id}}), (e2:Event {{id: $to_id}})
        CREATE (e1)-[r:{self.type.value} $properties]->(e2)
        RETURN r
        """
        return query, {
            'from_id': self.from_id,
            'to_id': self.to_id,
            'properties': self.to_dict()
        }