"""Kafka 메시지 핸들러"""
import logging
import json
from datetime import datetime
from typing import Dict, Any, List
import uuid

from src.neo4j.session import session
from src.models.nodes import Company, Person, NewsArticle, Event
from src.models.relationships import MentionRelationship, RelationshipType
from src.models.schemas import EnrichedNewsSchema, EntityType
from src.algorithms.entity_matching import matcher
from src.algorithms.time_series import time_series_analyzer
from src.algorithms.batch_entity_matching import batch_matcher
from src.kafka.entity_cache import entity_cache

logger = logging.getLogger(__name__)

class GraphMessageHandler:
    """Kafka 메시지 처리 핸들러"""
    
    def __init__(self):
        self.session = session
        
    async def handle_enriched_news(self, message: Dict[str, Any]):
        """ML 서비스에서 온 enriched-news 메시지 처리"""
        try:
            # 메시지 파싱 및 검증
            enriched_news = EnrichedNewsSchema(**message)
            logger.info(f"Processing enriched news: {enriched_news.id}")
            
            # 1. 뉴스 기사 노드 생성
            news_node = self._create_news_node(enriched_news)
            
            # 2. 엔티티 처리 및 관계 생성
            self._process_entities(enriched_news)
            
            # 3. 리스크 이벤트 생성 (높은 리스크 점수인 경우)
            if enriched_news.risk_score >= 7.0:
                risk_event_id = self._create_risk_event(enriched_news)
                # 시계열 이벤트 연결
                if risk_event_id:
                    time_series_analyzer.connect_temporal_events(risk_event_id)
            
            logger.info(f"Successfully processed news: {enriched_news.id}")
            
        except Exception as e:
            logger.error(f"Error processing enriched news: {e}")
            raise
    
    def _create_news_node(self, news: EnrichedNewsSchema) -> str:
        """뉴스 기사 노드 생성"""
        news_node = NewsArticle(
            id=news.id,
            title=news.title,
            content=news.content[:500] if news.content else None,  # 내용 제한
            url=news.url,
            published_at=news.published_at,
            source=news.source,
            sentiment=news.sentiment,
            risk_indicators=news.risk_indicators
        )
        
        query, params = news_node.get_create_query()
        self.session.run_query(query, **params)
        return news.id
    
    def _process_entities(self, news: EnrichedNewsSchema):
        """엔티티 처리 및 관계 생성 - N+1 문제 해결"""
        # 신뢰도 필터링
        valid_entities = [
            entity for entity in news.entities 
            if entity.confidence >= 0.7
        ]
        
        if not valid_entities:
            return
        
        # 🚀 배치 매칭으로 N+1 문제 해결
        entity_matches = batch_matcher.match_entities_batch(valid_entities)
        
        # 매칭된 엔티티와 새 엔티티 처리
        for entity in valid_entities:
            entity_key = f"{entity.type}:{entity.text}"
            entity_id = entity_matches.get(entity_key)
            
            # 매칭되지 않은 엔티티는 새로 생성
            if not entity_id:
                entity_id = self._create_new_entity(entity)
            
            if entity_id:
                self._create_mention_relationship(entity_id, news.id, entity, news.sentiment)
    
    def _create_new_entity(self, entity: Dict[str, Any]) -> str:
        """새 엔티티 생성 및 캐시 업데이트"""
        entity_type = entity['type']
        entity_text = entity['text']
        
        # 엔티티 타입별 생성
        if entity_type == EntityType.COMPANY:
            return self._create_company_entity(entity_text)
        elif entity_type == EntityType.PERSON:
            return self._create_person_entity(entity_text)
        else:
            # 기타 엔티티는 일반 Event로 처리
            return self._create_generic_entity(entity_text, entity_type)
    
    def _create_company_entity(self, company_name: str) -> str:
        """기업 엔티티 생성"""
        company_id = f"company-{uuid.uuid4()}"
        company = Company(
            id=company_id,
            name=company_name,
            aliases=[company_name]
        )
        
        query, params = company.get_create_query()
        self.session.run_query(query, **params)
        
        # 캐시에 추가
        entity_cache.add_company({
            'id': company_id,
            'name': company_name,
            'aliases': [company_name],
            'sector': None,
            'country': None,
            'risk_score': None
        })
        
        logger.info(f"Created new company: {company_name}")
        return company_id
    
    def _create_person_entity(self, person_name: str) -> str:
        """인물 엔티티 생성"""
        person_id = f"person-{uuid.uuid4()}"
        person = Person(
            id=person_id,
            name=person_name,
            aliases=[person_name]
        )
        
        query, params = person.get_create_query()
        self.session.run_query(query, **params)
        
        # 캐시에 추가
        entity_cache.add_person({
            'id': person_id,
            'name': person_name,
            'aliases': [person_name],
            'company': None,
            'role': None,
            'influence_score': None
        })
        
        logger.info(f"Created new person: {person_name}")
        return person_id
    
    def _create_generic_entity(self, entity_text: str, entity_type: str) -> str:
        """기타 엔티티 생성"""
        event_id = f"event-{uuid.uuid4()}"
        event = Event(
            id=event_id,
            type=entity_type,
            title=entity_text,
            occurred_at=datetime.now()
        )
        
        query, params = event.get_create_query()
        self.session.run_query(query, **params)
        logger.info(f"Created new event: {entity_text}")
        return event_id
    
    def _create_mention_relationship(self, entity_id: str, news_id: str, 
                                   entity: Dict[str, Any], sentiment: float):
        """언급 관계 생성"""
        mention = MentionRelationship(
            type=RelationshipType.MENTIONED_IN,
            from_id=entity_id,
            to_id=news_id,
            sentiment=sentiment,
            confidence=entity['confidence'],
            prominence=0.5  # 추후 계산 로직 추가
        )
        
        query, params = mention.get_create_query()
        self.session.run_query(query, **params)
    
    def _create_risk_event(self, news: EnrichedNewsSchema) -> str:
        """리스크 이벤트 생성"""
        # 리스크 타입 결정 (리스크 지표 기반)
        risk_type = self._determine_risk_type(news.risk_indicators)
        risk_event_id = f"risk-{news.id}"
        
        event_query = """
        CREATE (r:RiskEvent:Event {
            id: $id,
            type: 'Risk',
            title: $title,
            risk_type: $risk_type,
            severity: $severity,
            occurred_at: datetime($occurred_at),
            description: $description
        })
        """
        
        params = {
            'id': risk_event_id,
            'title': f"Risk Event: {news.title[:100]}",
            'risk_type': risk_type,
            'severity': int(news.risk_score),
            'occurred_at': news.published_at.isoformat(),
            'description': f"Generated from news article: {news.url}"
        }
        
        self.session.run_query(event_query, **params)
        
        # 뉴스와 리스크 이벤트 연결
        link_query = """
        MATCH (r:RiskEvent {id: $risk_id}), (n:NewsArticle {id: $news_id})
        CREATE (r)-[:DERIVED_FROM]->(n)
        """
        
        self.session.run_query(
            link_query,
            risk_id=risk_event_id,
            news_id=news.id
        )
        
        return risk_event_id
    
    def _determine_risk_type(self, risk_indicators: List[str]) -> str:
        """리스크 지표에서 리스크 타입 결정"""
        # 간단한 키워드 매칭 (추후 개선)
        if any('financial' in ind.lower() for ind in risk_indicators):
            return 'FINANCIAL'
        elif any('legal' in ind.lower() for ind in risk_indicators):
            return 'LEGAL'
        elif any('reputation' in ind.lower() for ind in risk_indicators):
            return 'REPUTATION'
        else:
            return 'OPERATIONAL'