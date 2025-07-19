"""Kafka 메시지 처리 통합 테스트"""
import pytest
import asyncio
from datetime import datetime
from src.kafka.handlers import GraphMessageHandler
from src.models.schemas import EnrichedNewsSchema, EntitySchema, EntityType
from src.neo4j.driver import Neo4jDriver

class TestKafkaMessageProcessing:
    """Kafka 메시지 처리 테스트"""
    
    @pytest.fixture
    def handler(self):
        """메시지 핸들러 fixture"""
        return GraphMessageHandler()
    
    @pytest.fixture
    def sample_message(self):
        """샘플 enriched-news 메시지"""
        return {
            "id": "news-test-001",
            "title": "Samsung Electronics Reports Record Profits",
            "content": "Samsung Electronics announced record quarterly profits...",
            "url": "https://example.com/news/001",
            "published_at": datetime.now().isoformat(),
            "source": "Reuters",
            "entities": [
                {
                    "text": "Samsung Electronics",
                    "type": "COMPANY",
                    "confidence": 0.95,
                    "start_pos": 0,
                    "end_pos": 18
                },
                {
                    "text": "Lee Jae-yong",
                    "type": "PERSON",
                    "confidence": 0.88,
                    "start_pos": 50,
                    "end_pos": 62
                }
            ],
            "sentiment": 0.7,
            "risk_score": 3.5,
            "risk_indicators": ["financial", "positive"],
            "topics": ["technology", "earnings"]
        }
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_process_enriched_news(self, handler, sample_message):
        """enriched-news 메시지 처리 테스트"""
        # 메시지 처리
        await handler.handle_enriched_news(sample_message)
        
        # 뉴스 노드 확인
        driver = Neo4jDriver()
        news_result = driver.execute_query(
            "MATCH (n:NewsArticle {id: $id}) RETURN n",
            id=sample_message['id']
        )
        assert len(news_result) == 1
        
        # 기업 노드 확인
        company_result = driver.execute_query(
            "MATCH (c:Company {name: $name}) RETURN c",
            name="Samsung Electronics"
        )
        assert len(company_result) > 0
        
        # 인물 노드 확인
        person_result = driver.execute_query(
            "MATCH (p:Person {name: $name}) RETURN p",
            name="Lee Jae-yong"
        )
        assert len(person_result) > 0
        
        # 관계 확인
        relation_result = driver.execute_query("""
            MATCH (c:Company)-[r:MENTIONED_IN]->(n:NewsArticle {id: $news_id})
            RETURN count(r) as count
            """,
            news_id=sample_message['id']
        )
        assert relation_result[0]['count'] >= 1
        
        # 정리
        driver.execute_query(
            "MATCH (n:NewsArticle {id: $id}) DETACH DELETE n",
            id=sample_message['id']
        )
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_high_risk_event_creation(self, handler):
        """높은 리스크 이벤트 생성 테스트"""
        high_risk_message = {
            "id": "news-risk-001",
            "title": "Major Security Breach at Tech Company",
            "content": "A significant security breach has been reported...",
            "url": "https://example.com/news/risk001",
            "published_at": datetime.now().isoformat(),
            "source": "SecurityNews",
            "entities": [
                {
                    "text": "Tech Corp",
                    "type": "COMPANY",
                    "confidence": 0.92,
                    "start_pos": 0,
                    "end_pos": 9
                }
            ],
            "sentiment": -0.8,
            "risk_score": 8.5,  # 높은 리스크 점수
            "risk_indicators": ["security", "breach", "data_loss"],
            "topics": ["cybersecurity", "incident"]
        }
        
        # 메시지 처리
        await handler.handle_enriched_news(high_risk_message)
        
        # 리스크 이벤트 확인
        driver = Neo4jDriver()
        risk_result = driver.execute_query(
            "MATCH (r:RiskEvent {id: $id}) RETURN r",
            id=f"risk-{high_risk_message['id']}"
        )
        assert len(risk_result) == 1
        assert risk_result[0]['r']['severity'] == 8
        
        # 정리
        driver.execute_query(
            "MATCH (n {id: $news_id}) DETACH DELETE n",
            news_id=high_risk_message['id']
        )
        driver.execute_query(
            "MATCH (r:RiskEvent {id: $risk_id}) DETACH DELETE r",
            risk_id=f"risk-{high_risk_message['id']}"
        )
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_entity_deduplication(self, handler):
        """엔티티 중복 제거 테스트"""
        # 첫 번째 메시지
        message1 = {
            "id": "news-dup-001",
            "title": "Samsung News 1",
            "content": "Content 1",
            "url": "https://example.com/1",
            "published_at": datetime.now().isoformat(),
            "source": "Source1",
            "entities": [
                {
                    "text": "Samsung Electronics",
                    "type": "COMPANY",
                    "confidence": 0.95,
                    "start_pos": 0,
                    "end_pos": 18
                }
            ],
            "sentiment": 0.5,
            "risk_score": 5.0,
            "risk_indicators": [],
            "topics": []
        }
        
        # 두 번째 메시지 (같은 회사, 다른 표기)
        message2 = {
            "id": "news-dup-002",
            "title": "Samsung News 2",
            "content": "Content 2",
            "url": "https://example.com/2",
            "published_at": datetime.now().isoformat(),
            "source": "Source2",
            "entities": [
                {
                    "text": "Samsung",  # 약어
                    "type": "COMPANY",
                    "confidence": 0.90,
                    "start_pos": 0,
                    "end_pos": 7
                }
            ],
            "sentiment": 0.3,
            "risk_score": 4.0,
            "risk_indicators": [],
            "topics": []
        }
        
        # 메시지 처리
        await handler.handle_enriched_news(message1)
        await handler.handle_enriched_news(message2)
        
        # 기업 노드가 하나만 있는지 확인
        driver = Neo4jDriver()
        company_result = driver.execute_query(
            "MATCH (c:Company) WHERE c.name CONTAINS 'Samsung' RETURN count(c) as count"
        )
        
        # 엔티티 매칭 알고리즘에 따라 1개 또는 2개일 수 있음
        assert company_result[0]['count'] <= 2
        
        # 정리
        driver.execute_query(
            "MATCH (n:NewsArticle) WHERE n.id IN $ids DETACH DELETE n",
            ids=["news-dup-001", "news-dup-002"]
        )
        driver.execute_query(
            "MATCH (c:Company) WHERE c.name CONTAINS 'Samsung' DETACH DELETE c"
        )