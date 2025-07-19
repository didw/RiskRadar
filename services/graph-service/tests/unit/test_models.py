"""모델 단위 테스트"""
import pytest
from datetime import datetime
from src.models.nodes import Company, Person, Event, RiskEvent, NewsArticle, RiskType
from src.models.relationships import (
    CompanyRelationship, PersonCompanyRelationship, 
    EventRelationship, MentionRelationship, RelationshipType
)

class TestNodeModels:
    """노드 모델 테스트"""
    
    def test_company_node(self):
        """Company 노드 테스트"""
        company = Company(
            id='company-test',
            name='Test Company',
            industry='Technology',
            market_cap=1000000.0,
            risk_score=7.5,
            country='USA',
            aliases=['Test Co', 'TC']
        )
        
        # to_dict 테스트
        data = company.to_dict()
        assert data['id'] == 'company-test'
        assert data['name'] == 'Test Company'
        assert data['industry'] == 'Technology'
        assert data['risk_score'] == 7.5
        assert len(data['aliases']) == 2
        
        # get_create_query 테스트
        query, params = company.get_create_query()
        assert 'MERGE (c:Company {id: $id})' in query
        assert params['id'] == 'company-test'
        assert 'properties' in params
    
    def test_person_node(self):
        """Person 노드 테스트"""
        person = Person(
            id='person-test',
            name='John Doe',
            title='CEO',
            organization='Test Company'
        )
        
        data = person.to_dict()
        assert data['name'] == 'John Doe'
        assert data['title'] == 'CEO'
        
        query, params = person.get_create_query()
        assert 'MERGE (p:Person {id: $id})' in query
    
    def test_risk_event_node(self):
        """RiskEvent 노드 테스트"""
        risk_event = RiskEvent(
            id='risk-test',
            type='Financial',
            title='Revenue Warning',
            risk_type=RiskType.FINANCIAL,
            severity=8,
            probability=0.7
        )
        
        data = risk_event.to_dict()
        assert data['risk_type'] == 'FINANCIAL'
        assert data['severity'] == 8
        assert data['probability'] == 0.7
        
        query, params = risk_event.get_create_query()
        assert 'CREATE (r:RiskEvent:Event {id: $id})' in query
    
    def test_news_article_node(self):
        """NewsArticle 노드 테스트"""
        now = datetime.now()
        news = NewsArticle(
            id='news-test',
            title='Test News',
            content='Test content',
            url='http://test.com',
            published_at=now,
            sentiment=0.5,
            risk_indicators=['financial', 'legal']
        )
        
        data = news.to_dict()
        assert data['title'] == 'Test News'
        assert data['sentiment'] == 0.5
        assert len(data['risk_indicators']) == 2

class TestRelationshipModels:
    """관계 모델 테스트"""
    
    def test_company_relationship(self):
        """기업 간 관계 테스트"""
        rel = CompanyRelationship(
            type=RelationshipType.COMPETES_WITH,
            from_id='company-1',
            to_id='company-2',
            strength=0.8
        )
        
        data = rel.to_dict()
        assert data['strength'] == 0.8
        assert 'created_at' in data
        
        query, params = rel.get_create_query()
        assert 'CREATE (a)-[r:COMPETES_WITH' in query
        assert params['from_id'] == 'company-1'
        assert params['to_id'] == 'company-2'
    
    def test_person_company_relationship(self):
        """인물-기업 관계 테스트"""
        rel = PersonCompanyRelationship(
            type=RelationshipType.CEO_OF,
            from_id='person-1',
            to_id='company-1',
            role='Chief Executive Officer',
            is_current=True
        )
        
        data = rel.to_dict()
        assert data['role'] == 'Chief Executive Officer'
        assert data['is_current'] is True
        
        query, params = rel.get_create_query()
        assert 'MATCH (p:Person {id: $from_id}), (c:Company {id: $to_id})' in query
    
    def test_mention_relationship(self):
        """언급 관계 테스트"""
        rel = MentionRelationship(
            type=RelationshipType.MENTIONED_IN,
            from_id='company-1',
            to_id='news-1',
            sentiment=-0.5,
            prominence=0.8,
            context='negative earnings report'
        )
        
        data = rel.to_dict()
        assert data['sentiment'] == -0.5
        assert data['prominence'] == 0.8
        assert data['context'] == 'negative earnings report'