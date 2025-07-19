"""시계열 이벤트 연결 알고리즘"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from src.neo4j.session import session
from src.models.relationships import TimeSeriesRelationship, RelationshipType

logger = logging.getLogger(__name__)

@dataclass
class EventCorrelation:
    """이벤트 상관관계"""
    event1_id: str
    event2_id: str
    time_gap_hours: float
    correlation_score: float
    relationship_type: RelationshipType

class TimeSeriesAnalyzer:
    """시계열 이벤트 분석기"""
    
    def __init__(self, 
                 time_window_hours: int = 24,
                 correlation_threshold: float = 0.7):
        self.time_window_hours = time_window_hours
        self.correlation_threshold = correlation_threshold
        self.session = session
    
    def connect_temporal_events(self, event_id: str):
        """새 이벤트와 기존 이벤트의 시계열 연결"""
        # 1. 시간 윈도우 내 관련 이벤트 찾기
        related_events = self._find_temporal_neighbors(event_id)
        
        # 2. 각 이벤트와의 상관관계 계산
        correlations = []
        for related in related_events:
            correlation = self._calculate_event_correlation(event_id, related)
            if correlation and correlation.correlation_score >= self.correlation_threshold:
                correlations.append(correlation)
        
        # 3. 상관관계가 높은 이벤트들 연결
        for corr in correlations:
            self._create_temporal_relationship(corr)
        
        logger.info(f"Connected {len(correlations)} temporal events to {event_id}")
    
    def _find_temporal_neighbors(self, event_id: str) -> List[Dict]:
        """시간 윈도우 내 이벤트 찾기"""
        query = """
        MATCH (e1:Event {id: $event_id})
        MATCH (e2:Event)
        WHERE e2.id <> e1.id
          AND abs(duration.between(
                datetime(e1.occurred_at), 
                datetime(e2.occurred_at)
              ).hours) <= $window_hours
        RETURN e2.id as id, 
               e2.type as type,
               e2.occurred_at as occurred_at,
               duration.between(
                 datetime(e1.occurred_at), 
                 datetime(e2.occurred_at)
               ).hours as time_gap_hours
        ORDER BY abs(time_gap_hours)
        LIMIT 50
        """
        
        return self.session.run_query(
            query,
            event_id=event_id,
            window_hours=self.time_window_hours
        )
    
    def _calculate_event_correlation(self, 
                                   event1_id: str, 
                                   event2_data: Dict) -> Optional[EventCorrelation]:
        """두 이벤트 간 상관관계 계산"""
        # 영향을 받는 엔티티 확인
        shared_entities_query = """
        MATCH (e1:Event {id: $event1_id})-[:AFFECTS|MENTIONED_IN]-(entity)
        MATCH (e2:Event {id: $event2_id})-[:AFFECTS|MENTIONED_IN]-(entity)
        RETURN count(DISTINCT entity) as shared_count,
               collect(DISTINCT labels(entity)[0]) as entity_types
        """
        
        result = self.session.run_query(
            shared_entities_query,
            event1_id=event1_id,
            event2_id=event2_data['id']
        )
        
        if not result or result[0]['shared_count'] == 0:
            return None
        
        shared_count = result[0]['shared_count']
        time_gap = abs(event2_data['time_gap_hours'])
        
        # 상관관계 점수 계산
        # - 공유 엔티티가 많을수록 높은 점수
        # - 시간 간격이 짧을수록 높은 점수
        entity_score = min(shared_count / 5.0, 1.0)  # 최대 5개 공유 시 1.0
        time_score = 1.0 - (time_gap / self.time_window_hours)
        
        correlation_score = (entity_score * 0.7 + time_score * 0.3)
        
        # 관계 타입 결정
        if event2_data['time_gap_hours'] > 0:
            rel_type = RelationshipType.PRECEDED_BY
        else:
            rel_type = RelationshipType.FOLLOWED_BY
        
        return EventCorrelation(
            event1_id=event1_id,
            event2_id=event2_data['id'],
            time_gap_hours=time_gap,
            correlation_score=correlation_score,
            relationship_type=rel_type
        )
    
    def _create_temporal_relationship(self, correlation: EventCorrelation):
        """시계열 관계 생성"""
        relationship = TimeSeriesRelationship(
            type=correlation.relationship_type,
            from_id=correlation.event1_id,
            to_id=correlation.event2_id,
            time_gap_hours=correlation.time_gap_hours,
            correlation_score=correlation.correlation_score
        )
        
        query, params = relationship.get_create_query()
        self.session.run_query(query, **params)
    
    def find_event_chains(self, start_event_id: str, max_depth: int = 3) -> List[List[str]]:
        """이벤트 체인 찾기"""
        query = """
        MATCH path = (start:Event {id: $start_id})-[:PRECEDED_BY|FOLLOWED_BY*1..$depth]->(end:Event)
        WHERE ALL(r IN relationships(path) WHERE r.correlation_score >= $threshold)
        RETURN [n IN nodes(path) | n.id] as chain,
               reduce(score = 1.0, r IN relationships(path) | score * r.correlation_score) as chain_score
        ORDER BY chain_score DESC
        LIMIT 10
        """
        
        results = self.session.run_query(
            query,
            start_id=start_event_id,
            depth=max_depth,
            threshold=self.correlation_threshold
        )
        
        return [r['chain'] for r in results]
    
    def detect_cascading_risks(self, risk_event_id: str) -> List[Dict]:
        """연쇄 리스크 탐지"""
        query = """
        MATCH (start:RiskEvent {id: $risk_id})
        MATCH path = (start)-[:PRECEDED_BY|FOLLOWED_BY*1..3]->(risk:RiskEvent)
        WHERE ALL(r IN relationships(path) WHERE r.correlation_score >= 0.6)
        WITH risk, path,
             reduce(severity = start.severity, n IN nodes(path) | 
                    CASE WHEN n:RiskEvent THEN n.severity * 0.8 ELSE severity END
             ) as cascading_severity
        RETURN DISTINCT risk.id as risk_id,
               risk.title as title,
               risk.severity as original_severity,
               cascading_severity,
               length(path) as distance
        ORDER BY cascading_severity DESC
        """
        
        return self.session.run_query(query, risk_id=risk_event_id)

# 싱글톤 인스턴스
time_series_analyzer = TimeSeriesAnalyzer()