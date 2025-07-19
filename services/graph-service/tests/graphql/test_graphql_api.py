"""GraphQL API 테스트"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime
import json

from fastapi.testclient import TestClient
from src.main import app
from src.graphql.schema import Company, Person, Risk, Event


class TestGraphQLAPI:
    """GraphQL API 테스트"""
    
    @pytest.fixture
    def client(self):
        """테스트 클라이언트"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_session(self):
        """Mock Neo4j 세션"""
        with patch('src.neo4j.session.session') as mock:
            yield mock
    
    @pytest.fixture
    def sample_company_data(self):
        """샘플 기업 데이터"""
        return {
            'id': 'company-1',
            'name': 'Apple Inc.',
            'name_en': 'Apple Inc.',
            'aliases': ['Apple', 'AAPL'],
            'sector': 'Technology',
            'sub_sector': 'Consumer Electronics',
            'country': 'United States',
            'stock_code': 'AAPL',
            'market_cap': 2800000000000.0,
            'employee_count': 164000,
            'founded_year': 1976,
            'risk_score': 3.5,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
    
    @pytest.fixture
    def sample_person_data(self):
        """샘플 인물 데이터"""
        return {
            'id': 'person-1',
            'name': 'Tim Cook',
            'aliases': ['Timothy Donald Cook'],
            'company': 'Apple Inc.',
            'role': 'CEO',
            'nationality': 'American',
            'birth_year': 1960,
            'influence_score': 9.2,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
    
    def test_company_query(self, client, mock_session, sample_company_data):
        """기업 단일 조회 테스트"""
        # Mock 데이터 설정
        mock_session.run_query.return_value = [{'c': sample_company_data}]
        
        # GraphQL 쿼리
        query = """
        query GetCompany($id: ID!) {
            company(id: $id) {
                id
                name
                nameEn
                sector
                riskScore
            }
        }
        """
        
        response = client.post(
            "/graphql",
            json={
                "query": query,
                "variables": {"id": "company-1"}
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "errors" not in data
        assert data["data"]["company"]["id"] == "company-1"
        assert data["data"]["company"]["name"] == "Apple Inc."
        assert data["data"]["company"]["riskScore"] == 3.5
    
    def test_companies_list_query(self, client, mock_session, sample_company_data):
        """기업 목록 조회 테스트"""
        # Mock 데이터 설정
        mock_session.run_query.return_value = [
            {'c': sample_company_data},
            {'c': {**sample_company_data, 'id': 'company-2', 'name': 'Microsoft'}}
        ]
        
        # GraphQL 쿼리
        query = """
        query GetCompanies($filter: CompanyFilter) {
            companies(filter: $filter) {
                id
                name
                sector
                riskScore
            }
        }
        """
        
        response = client.post(
            "/graphql",
            json={
                "query": query,
                "variables": {
                    "filter": {
                        "sector": "Technology",
                        "minRiskScore": 3.0
                    }
                }
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "errors" not in data
        assert len(data["data"]["companies"]) == 2
        assert data["data"]["companies"][0]["sector"] == "Technology"
    
    def test_person_query(self, client, mock_session, sample_person_data):
        """인물 조회 테스트"""
        # Mock 데이터 설정
        mock_session.run_query.return_value = [{'p': sample_person_data}]
        
        # GraphQL 쿼리
        query = """
        query GetPerson($id: ID!) {
            person(id: $id) {
                id
                name
                company
                role
                influenceScore
            }
        }
        """
        
        response = client.post(
            "/graphql",
            json={
                "query": query,
                "variables": {"id": "person-1"}
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "errors" not in data
        assert data["data"]["person"]["name"] == "Tim Cook"
        assert data["data"]["person"]["role"] == "CEO"
        assert data["data"]["person"]["influenceScore"] == 9.2
    
    def test_network_analysis_query(self, client, mock_session):
        """네트워크 분석 쿼리 테스트"""
        # Mock 데이터 설정
        mock_session.run_query.return_value = [{
            'central': {
                'id': 'company-1',
                'name': 'Apple Inc.',
                'risk_score': 3.5
            },
            'connected_count': 25,
            'avg_risk': 4.2
        }]
        
        # GraphQL 쿼리
        query = """
        query NetworkAnalysis($entityId: ID!, $depth: Int!, $minRiskScore: Float!) {
            networkAnalysis(entityId: $entityId, depth: $depth, minRiskScore: $minRiskScore) {
                centralEntity {
                    ... on Company {
                        id
                        name
                        riskScore
                    }
                }
                connectedEntities
                averageRiskScore
                networkDensity
            }
        }
        """
        
        response = client.post(
            "/graphql",
            json={
                "query": query,
                "variables": {
                    "entityId": "company-1",
                    "depth": 2,
                    "minRiskScore": 5.0
                }
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "errors" not in data
        analysis = data["data"]["networkAnalysis"]
        assert analysis["connectedEntities"] == 25
        assert analysis["averageRiskScore"] == 4.2
        assert analysis["centralEntity"]["name"] == "Apple Inc."
    
    def test_search_query(self, client, mock_session, sample_company_data):
        """통합 검색 테스트"""
        # Mock 데이터 설정
        mock_session.run_query.return_value = [
            {'node': {**sample_company_data, 'labels': ['Company']}}
        ]
        
        # GraphQL 쿼리
        query = """
        query Search($query: String!, $nodeTypes: [String!], $limit: Int!) {
            search(query: $query, nodeTypes: $nodeTypes, limit: $limit) {
                ... on Company {
                    id
                    name
                    sector
                }
                ... on Person {
                    id
                    name
                    role
                }
            }
        }
        """
        
        response = client.post(
            "/graphql",
            json={
                "query": query,
                "variables": {
                    "query": "Apple",
                    "nodeTypes": ["Company"],
                    "limit": 10
                }
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "errors" not in data
        assert len(data["data"]["search"]) == 1
        assert data["data"]["search"][0]["name"] == "Apple Inc."
    
    def test_create_company_mutation(self, client, mock_session, sample_company_data):
        """기업 생성 뮤테이션 테스트"""
        # Mock 데이터 설정
        mock_session.run_query.return_value = [{'c': sample_company_data}]
        
        # GraphQL 뮤테이션
        mutation = """
        mutation CreateCompany($input: CompanyInput!) {
            createCompany(input: $input) {
                id
                name
                sector
                riskScore
            }
        }
        """
        
        response = client.post(
            "/graphql",
            json={
                "query": mutation,
                "variables": {
                    "input": {
                        "name": "Apple Inc.",
                        "nameEn": "Apple Inc.",
                        "sector": "Technology",
                        "country": "United States",
                        "stockCode": "AAPL"
                    }
                }
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "errors" not in data
        company = data["data"]["createCompany"]
        assert company["name"] == "Apple Inc."
        assert company["sector"] == "Technology"
    
    def test_create_person_mutation(self, client, mock_session, sample_person_data):
        """인물 생성 뮤테이션 테스트"""
        # Mock 데이터 설정
        mock_session.run_query.return_value = [{'p': sample_person_data}]
        
        # GraphQL 뮤테이션
        mutation = """
        mutation CreatePerson($input: PersonInput!) {
            createPerson(input: $input) {
                id
                name
                company
                role
            }
        }
        """
        
        response = client.post(
            "/graphql",
            json={
                "query": mutation,
                "variables": {
                    "input": {
                        "name": "Tim Cook",
                        "company": "Apple Inc.",
                        "role": "CEO",
                        "nationality": "American"
                    }
                }
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "errors" not in data
        person = data["data"]["createPerson"]
        assert person["name"] == "Tim Cook"
        assert person["role"] == "CEO"
    
    def test_create_relationship_mutation(self, client, mock_session):
        """관계 생성 뮤테이션 테스트"""
        # Mock 데이터 설정
        mock_session.run_query.return_value = [{
            'r': {
                'id': 'rel-1',
                'properties': '{}',
                'strength': 0.8,
                'confidence': 0.9,
                'created_at': datetime.now()
            },
            'from': {
                'id': 'person-1',
                'name': 'Tim Cook',
                'labels': ['Person']
            },
            'to': {
                'id': 'company-1',
                'name': 'Apple Inc.',
                'labels': ['Company']
            }
        }]
        
        # GraphQL 뮤테이션
        mutation = """
        mutation CreateRelationship($input: RelationshipInput!) {
            createRelationship(input: $input) {
                id
                type
                strength
                confidence
                fromNode {
                    ... on Person {
                        id
                        name
                    }
                }
                toNode {
                    ... on Company {
                        id
                        name
                    }
                }
            }
        }
        """
        
        response = client.post(
            "/graphql",
            json={
                "query": mutation,
                "variables": {
                    "input": {
                        "fromId": "person-1",
                        "toId": "company-1",
                        "type": "WORKS_AT",
                        "strength": 0.8,
                        "confidence": 0.9
                    }
                }
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "errors" not in data
        relationship = data["data"]["createRelationship"]
        assert relationship["type"] == "WORKS_AT"
        assert relationship["strength"] == 0.8
    
    def test_update_company_risk_score_mutation(self, client, mock_session, sample_company_data):
        """기업 리스크 점수 업데이트 뮤테이션 테스트"""
        # Mock 데이터 설정
        updated_data = {**sample_company_data, 'risk_score': 7.5}
        mock_session.run_query.return_value = [{'c': updated_data}]
        
        # GraphQL 뮤테이션
        mutation = """
        mutation UpdateCompanyRiskScore($id: ID!, $riskScore: Float!) {
            updateCompanyRiskScore(id: $id, riskScore: $riskScore) {
                id
                name
                riskScore
            }
        }
        """
        
        response = client.post(
            "/graphql",
            json={
                "query": mutation,
                "variables": {
                    "id": "company-1",
                    "riskScore": 7.5
                }
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "errors" not in data
        company = data["data"]["updateCompanyRiskScore"]
        assert company["riskScore"] == 7.5
    
    def test_invalid_query_error(self, client):
        """잘못된 쿼리 에러 처리 테스트"""
        # 잘못된 GraphQL 구문
        query = """
        query InvalidQuery {
            invalidField {
                nonExistentField
            }
        }
        """
        
        response = client.post(
            "/graphql",
            json={"query": query}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # GraphQL 에러가 반환되어야 함
        assert "errors" in data
        assert len(data["errors"]) > 0
    
    def test_graphql_playground_endpoint(self, client):
        """GraphQL Playground 엔드포인트 테스트"""
        response = client.get("/playground")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        assert "GraphQL Playground" in response.text
        assert "/graphql" in response.text  # 엔드포인트 설정 확인
    
    def test_graphql_introspection(self, client):
        """GraphQL 스키마 인트로스펙션 테스트"""
        query = """
        query IntrospectionQuery {
            __schema {
                types {
                    name
                    kind
                }
            }
        }
        """
        
        response = client.post(
            "/graphql",
            json={"query": query}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "errors" not in data
        types = data["data"]["__schema"]["types"]
        type_names = [t["name"] for t in types]
        
        # 정의한 타입들이 스키마에 포함되어 있는지 확인
        assert "Company" in type_names
        assert "Person" in type_names
        assert "Risk" in type_names
        assert "Event" in type_names
        assert "NetworkAnalysis" in type_names
    
    @pytest.mark.asyncio
    async def test_dataloader_batching(self, mock_session):
        """DataLoader 배치 처리 테스트"""
        from src.graphql.dataloaders import company_loader
        
        # Mock 데이터 설정
        mock_session.run_query.return_value = [
            {'id': 'company-1', 'c': {'id': 'company-1', 'name': 'Apple'}},
            {'id': 'company-2', 'c': {'id': 'company-2', 'name': 'Microsoft'}}
        ]
        
        # 여러 회사를 동시에 로드
        companies = await company_loader.load_many(['company-1', 'company-2'])
        
        # 배치 로딩이 작동했는지 확인
        assert len(companies) == 2
        assert companies[0]['name'] == 'Apple'
        assert companies[1]['name'] == 'Microsoft'
        
        # 한 번의 데이터베이스 호출만 발생했는지 확인
        assert mock_session.run_query.call_count == 1