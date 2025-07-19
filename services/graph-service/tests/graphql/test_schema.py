"""GraphQL 스키마 테스트"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.graphql.schema import Company, Person, Risk, Event
from src.graphql.resolvers import Query, Mutation


class TestGraphQLSchema:
    """GraphQL 스키마 테스트"""
    
    def test_company_type_creation(self):
        """Company 타입 생성 테스트"""
        company = Company(
            id="company-1",
            name="Apple Inc.",
            name_en="Apple Inc.",
            aliases=["Apple", "AAPL"],
            sector="Technology",
            risk_score=3.5,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        assert company.id == "company-1"
        assert company.name == "Apple Inc."
        assert company.sector == "Technology"
        assert company.risk_score == 3.5
        assert "Apple" in company.aliases
    
    def test_person_type_creation(self):
        """Person 타입 생성 테스트"""
        person = Person(
            id="person-1",
            name="Tim Cook",
            aliases=["Timothy Donald Cook"],
            company="Apple Inc.",
            role="CEO",
            influence_score=9.2,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        assert person.id == "person-1"
        assert person.name == "Tim Cook"
        assert person.role == "CEO"
        assert person.influence_score == 9.2
    
    def test_risk_type_creation(self):
        """Risk 타입 생성 테스트"""
        from src.graphql.schema import RiskType
        
        risk = Risk(
            id="risk-1",
            category=RiskType.FINANCIAL,
            level=8,
            trend="INCREASING",
            description="High financial risk",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        assert risk.id == "risk-1"
        assert risk.category == RiskType.FINANCIAL
        assert risk.level == 8
        assert risk.trend == "INCREASING"
    
    def test_event_type_creation(self):
        """Event 타입 생성 테스트"""
        from src.graphql.schema import EventType
        
        event = Event(
            id="event-1",
            type=EventType.MERGER,
            title="Apple acquires startup",
            description="Apple Inc. announces acquisition",
            date=datetime.now(),
            severity=6,
            impact=7.5,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        assert event.id == "event-1"
        assert event.type == EventType.MERGER
        assert event.title == "Apple acquires startup"
        assert event.severity == 6
        assert event.impact == 7.5
    
    @patch('src.neo4j.session.session')
    def test_query_resolver_mapping(self, mock_session):
        """Query 리졸버 매핑 테스트"""
        query = Query()
        
        # Mock 데이터 설정
        mock_session.run_query.return_value = [{
            'c': {
                'id': 'company-1',
                'name': 'Apple Inc.',
                'risk_score': 3.5,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
        }]
        
        # Company 매핑 테스트
        company_data = mock_session.run_query.return_value[0]['c']
        company = query._map_company(company_data)
        
        assert isinstance(company, Company)
        assert company.id == 'company-1'
        assert company.name == 'Apple Inc.'
        assert company.risk_score == 3.5
    
    def test_enum_values(self):
        """Enum 값 테스트"""
        from src.graphql.schema import RiskType, EventType, RelationshipType
        
        # RiskType enum
        assert RiskType.FINANCIAL.value == "FINANCIAL"
        assert RiskType.LEGAL.value == "LEGAL"
        assert RiskType.REPUTATION.value == "REPUTATION"
        assert RiskType.OPERATIONAL.value == "OPERATIONAL"
        assert RiskType.ESG.value == "ESG"
        
        # EventType enum
        assert EventType.MERGER.value == "MERGER"
        assert EventType.ACQUISITION.value == "ACQUISITION"
        assert EventType.LAWSUIT.value == "LAWSUIT"
        
        # RelationshipType enum
        assert RelationshipType.COMPETES_WITH.value == "COMPETES_WITH"
        assert RelationshipType.PARTNERS_WITH.value == "PARTNERS_WITH"
        assert RelationshipType.WORKS_AT.value == "WORKS_AT"
    
    def test_input_types(self):
        """Input 타입 테스트"""
        from src.graphql.schema import CompanyInput, PersonInput, RelationshipInput, RelationshipType
        
        # CompanyInput
        company_input = CompanyInput(
            name="Test Company",
            sector="Technology",
            country="USA"
        )
        assert company_input.name == "Test Company"
        assert company_input.sector == "Technology"
        
        # PersonInput
        person_input = PersonInput(
            name="Test Person",
            company="Test Company",
            role="CEO"
        )
        assert person_input.name == "Test Person"
        assert person_input.role == "CEO"
        
        # RelationshipInput
        rel_input = RelationshipInput(
            from_id="person-1",
            to_id="company-1",
            type=RelationshipType.WORKS_AT,
            strength=0.8
        )
        assert rel_input.from_id == "person-1"
        assert rel_input.type == RelationshipType.WORKS_AT
        assert rel_input.strength == 0.8