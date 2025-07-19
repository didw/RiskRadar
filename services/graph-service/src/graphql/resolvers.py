"""GraphQL 리졸버"""
import strawberry
from typing import List, Optional
from datetime import datetime
import logging

from src.neo4j.session import session
from src.graphql.schema import (
    Company, Person, Risk, Event, NewsArticle,
    NetworkAnalysis, RiskAssessment, Relationship,
    CompanyFilter, PersonFilter, EventFilter, RiskFilter,
    PaginationInput, CompanyInput, PersonInput, RelationshipInput,
    NodeUnion, CentralityScore, RiskPath
)
from src.graphql.dataloaders import (
    CompanyDataLoader, PersonDataLoader, EventDataLoader,
    RelationshipDataLoader
)

logger = logging.getLogger(__name__)

@strawberry.type
class Query:
    """GraphQL 쿼리 루트"""
    
    @strawberry.field
    async def company(self, id: strawberry.ID) -> Optional[Company]:
        """단일 기업 조회"""
        try:
            query = """
            MATCH (c:Company {id: $id})
            RETURN c
            """
            result = session.run_query(query, id=id)
            
            if result:
                company_data = result[0]['c']
                return self._map_company(company_data)
            return None
            
        except Exception as e:
            logger.error(f"Error fetching company {id}: {e}")
            return None
    
    @strawberry.field
    async def companies(
        self, 
        filter: Optional[CompanyFilter] = None,
        pagination: Optional[PaginationInput] = None
    ) -> List[Company]:
        """기업 목록 조회"""
        try:
            # 기본 쿼리
            query = "MATCH (c:Company)"
            params = {}
            conditions = []
            
            # 필터 적용
            if filter:
                if filter.name:
                    conditions.append("c.name CONTAINS $name")
                    params['name'] = filter.name
                
                if filter.sector:
                    conditions.append("c.sector = $sector")
                    params['sector'] = filter.sector
                
                if filter.country:
                    conditions.append("c.country = $country")
                    params['country'] = filter.country
                
                if filter.min_risk_score is not None:
                    conditions.append("c.risk_score >= $min_risk_score")
                    params['min_risk_score'] = filter.min_risk_score
                
                if filter.max_risk_score is not None:
                    conditions.append("c.risk_score <= $max_risk_score")
                    params['max_risk_score'] = filter.max_risk_score
            
            # WHERE 절 추가
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            # 정렬 및 페이지네이션
            query += " RETURN c ORDER BY c.name"
            
            if pagination and pagination.first:
                query += f" LIMIT {pagination.first}"
            else:
                query += " LIMIT 50"  # 기본 제한
            
            result = session.run_query(query, **params)
            
            return [self._map_company(row['c']) for row in result]
            
        except Exception as e:
            logger.error(f"Error fetching companies: {e}")
            return []
    
    @strawberry.field
    async def person(self, id: strawberry.ID) -> Optional[Person]:
        """단일 인물 조회"""
        try:
            query = """
            MATCH (p:Person {id: $id})
            RETURN p
            """
            result = session.run_query(query, id=id)
            
            if result:
                person_data = result[0]['p']
                return self._map_person(person_data)
            return None
            
        except Exception as e:
            logger.error(f"Error fetching person {id}: {e}")
            return None
    
    @strawberry.field
    async def people(
        self,
        filter: Optional[PersonFilter] = None,
        pagination: Optional[PaginationInput] = None
    ) -> List[Person]:
        """인물 목록 조회"""
        try:
            query = "MATCH (p:Person)"
            params = {}
            conditions = []
            
            if filter:
                if filter.name:
                    conditions.append("p.name CONTAINS $name")
                    params['name'] = filter.name
                
                if filter.company:
                    conditions.append("p.company = $company")
                    params['company'] = filter.company
                
                if filter.role:
                    conditions.append("p.role = $role")
                    params['role'] = filter.role
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " RETURN p ORDER BY p.name LIMIT 50"
            result = session.run_query(query, **params)
            
            return [self._map_person(row['p']) for row in result]
            
        except Exception as e:
            logger.error(f"Error fetching people: {e}")
            return []
    
    @strawberry.field
    async def events(
        self,
        filter: Optional[EventFilter] = None,
        pagination: Optional[PaginationInput] = None
    ) -> List[Event]:
        """이벤트 목록 조회"""
        try:
            query = "MATCH (e:Event)"
            params = {}
            conditions = []
            
            if filter:
                if filter.type:
                    conditions.append("e.type = $type")
                    params['type'] = filter.type.value
                
                if filter.start_date:
                    conditions.append("e.date >= datetime($start_date)")
                    params['start_date'] = filter.start_date.isoformat()
                
                if filter.end_date:
                    conditions.append("e.date <= datetime($end_date)")
                    params['end_date'] = filter.end_date.isoformat()
                
                if filter.min_severity:
                    conditions.append("e.severity >= $min_severity")
                    params['min_severity'] = filter.min_severity
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " RETURN e ORDER BY e.date DESC LIMIT 50"
            result = session.run_query(query, **params)
            
            return [self._map_event(row['e']) for row in result]
            
        except Exception as e:
            logger.error(f"Error fetching events: {e}")
            return []
    
    @strawberry.field
    async def risks(
        self,
        filter: Optional[RiskFilter] = None,
        pagination: Optional[PaginationInput] = None
    ) -> List[Risk]:
        """리스크 목록 조회"""
        try:
            query = "MATCH (r:Risk)"
            params = {}
            conditions = []
            
            if filter:
                if filter.category:
                    conditions.append("r.category = $category")
                    params['category'] = filter.category.value
                
                if filter.min_level:
                    conditions.append("r.level >= $min_level")
                    params['min_level'] = filter.min_level
                
                if filter.max_level:
                    conditions.append("r.level <= $max_level")
                    params['max_level'] = filter.max_level
                
                if filter.trend:
                    conditions.append("r.trend = $trend")
                    params['trend'] = filter.trend
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " RETURN r ORDER BY r.level DESC LIMIT 50"
            result = session.run_query(query, **params)
            
            return [self._map_risk(row['r']) for row in result]
            
        except Exception as e:
            logger.error(f"Error fetching risks: {e}")
            return []
    
    @strawberry.field
    async def network_analysis(
        self,
        entity_id: strawberry.ID,
        depth: int = 2,
        min_risk_score: float = 5.0
    ) -> Optional[NetworkAnalysis]:
        """네트워크 분석"""
        try:
            # 중심 엔티티와 연결된 노드 찾기
            query = """
            MATCH (central {id: $entity_id})
            MATCH path = (central)-[*1..$depth]-(connected)
            WHERE connected.risk_score >= $min_risk_score
            WITH central, connected, path
            RETURN 
                central,
                count(DISTINCT connected) as connected_count,
                avg(connected.risk_score) as avg_risk,
                collect(DISTINCT {
                    node: connected,
                    path_length: length(path)
                }) as connections
            """
            
            result = session.run_query(
                query,
                entity_id=entity_id,
                depth=depth,
                min_risk_score=min_risk_score
            )
            
            if not result:
                return None
            
            data = result[0]
            central_node = self._map_node(data['central'])
            
            return NetworkAnalysis(
                central_entity=central_node,
                connected_entities=data['connected_count'],
                average_risk_score=data['avg_risk'] or 0.0,
                network_density=0.5,  # TODO: 실제 계산
                clustering_coefficient=0.3,  # TODO: 실제 계산
                centrality_scores=[],  # TODO: 구현
                risk_paths=[]  # TODO: 구현
            )
            
        except Exception as e:
            logger.error(f"Error in network analysis: {e}")
            return None
    
    @strawberry.field
    async def search(
        self,
        query: str,
        node_types: Optional[List[str]] = None,
        limit: int = 20
    ) -> List[NodeUnion]:
        """통합 검색"""
        try:
            # 전체 텍스트 검색 쿼리
            cypher_query = """
            CALL db.index.fulltext.queryNodes('entity_search', $search_term)
            YIELD node, score
            WHERE score > 0.5
            """
            
            if node_types:
                labels_condition = " OR ".join([f"'{nt}' IN labels(node)" for nt in node_types])
                cypher_query += f" AND ({labels_condition})"
            
            cypher_query += f" RETURN node ORDER BY score DESC LIMIT {limit}"
            
            result = session.run_query(cypher_query, search_term=query)
            
            nodes = []
            for row in result:
                node = self._map_node(row['node'])
                if node:
                    nodes.append(node)
            
            return nodes
            
        except Exception as e:
            logger.error(f"Error in search: {e}")
            return []
    
    # Helper methods
    def _map_company(self, data) -> Company:
        """Neo4j 데이터를 Company 객체로 변환"""
        return Company(
            id=data.get('id', ''),
            name=data.get('name', ''),
            name_en=data.get('name_en'),
            aliases=data.get('aliases', []),
            sector=data.get('sector'),
            sub_sector=data.get('sub_sector'),
            country=data.get('country'),
            stock_code=data.get('stock_code'),
            market_cap=data.get('market_cap'),
            employee_count=data.get('employee_count'),
            founded_year=data.get('founded_year'),
            risk_score=data.get('risk_score', 5.0),
            created_at=data.get('created_at', datetime.now()),
            updated_at=data.get('updated_at', datetime.now())
        )
    
    def _map_person(self, data) -> Person:
        """Neo4j 데이터를 Person 객체로 변환"""
        return Person(
            id=data.get('id', ''),
            name=data.get('name', ''),
            aliases=data.get('aliases', []),
            company=data.get('company'),
            role=data.get('role'),
            nationality=data.get('nationality'),
            birth_year=data.get('birth_year'),
            influence_score=data.get('influence_score', 5.0),
            created_at=data.get('created_at', datetime.now()),
            updated_at=data.get('updated_at', datetime.now())
        )
    
    def _map_event(self, data) -> Event:
        """Neo4j 데이터를 Event 객체로 변환"""
        from src.graphql.schema import EventType
        
        return Event(
            id=data.get('id', ''),
            type=EventType(data.get('type', 'MERGER')),
            title=data.get('title', ''),
            description=data.get('description'),
            date=data.get('date', datetime.now()),
            severity=data.get('severity', 5),
            impact=data.get('impact', 5.0),
            source=data.get('source'),
            created_at=data.get('created_at', datetime.now()),
            updated_at=data.get('updated_at', datetime.now())
        )
    
    def _map_risk(self, data) -> Risk:
        """Neo4j 데이터를 Risk 객체로 변환"""
        from src.graphql.schema import RiskType
        
        return Risk(
            id=data.get('id', ''),
            category=RiskType(data.get('category', 'OPERATIONAL')),
            level=data.get('level', 5),
            trend=data.get('trend', 'STABLE'),
            description=data.get('description', ''),
            mitigation=data.get('mitigation'),
            probability=data.get('probability'),
            impact=data.get('impact'),
            created_at=data.get('created_at', datetime.now()),
            updated_at=data.get('updated_at', datetime.now())
        )
    
    def _map_node(self, data) -> Optional[NodeUnion]:
        """Neo4j 노드를 적절한 타입으로 변환"""
        labels = data.labels if hasattr(data, 'labels') else []
        
        if 'Company' in labels:
            return self._map_company(dict(data))
        elif 'Person' in labels:
            return self._map_person(dict(data))
        elif 'Event' in labels:
            return self._map_event(dict(data))
        elif 'Risk' in labels:
            return self._map_risk(dict(data))
        # NewsArticle 등 추가 타입 매핑
        
        return None

@strawberry.type
class Mutation:
    """GraphQL 뮤테이션 루트"""
    
    @strawberry.mutation
    async def create_company(self, input: CompanyInput) -> Company:
        """기업 생성"""
        try:
            import uuid
            company_id = f"company-{uuid.uuid4()}"
            
            query = """
            CREATE (c:Company {
                id: $id,
                name: $name,
                name_en: $name_en,
                aliases: $aliases,
                sector: $sector,
                sub_sector: $sub_sector,
                country: $country,
                stock_code: $stock_code,
                market_cap: $market_cap,
                employee_count: $employee_count,
                founded_year: $founded_year,
                risk_score: 5.0,
                created_at: datetime(),
                updated_at: datetime()
            })
            RETURN c
            """
            
            params = {
                'id': company_id,
                'name': input.name,
                'name_en': input.name_en,
                'aliases': input.aliases or [],
                'sector': input.sector,
                'sub_sector': input.sub_sector,
                'country': input.country,
                'stock_code': input.stock_code,
                'market_cap': input.market_cap,
                'employee_count': input.employee_count,
                'founded_year': input.founded_year
            }
            
            result = session.run_query(query, **params)
            
            if result:
                company_data = result[0]['c']
                return Query()._map_company(company_data)
            
            raise Exception("Failed to create company")
            
        except Exception as e:
            logger.error(f"Error creating company: {e}")
            raise
    
    @strawberry.mutation
    async def create_person(self, input: PersonInput) -> Person:
        """인물 생성"""
        try:
            import uuid
            person_id = f"person-{uuid.uuid4()}"
            
            query = """
            CREATE (p:Person {
                id: $id,
                name: $name,
                aliases: $aliases,
                company: $company,
                role: $role,
                nationality: $nationality,
                birth_year: $birth_year,
                influence_score: 5.0,
                created_at: datetime(),
                updated_at: datetime()
            })
            RETURN p
            """
            
            params = {
                'id': person_id,
                'name': input.name,
                'aliases': input.aliases or [],
                'company': input.company,
                'role': input.role,
                'nationality': input.nationality,
                'birth_year': input.birth_year
            }
            
            result = session.run_query(query, **params)
            
            if result:
                person_data = result[0]['p']
                return Query()._map_person(person_data)
            
            raise Exception("Failed to create person")
            
        except Exception as e:
            logger.error(f"Error creating person: {e}")
            raise
    
    @strawberry.mutation
    async def create_relationship(self, input: RelationshipInput) -> Relationship:
        """관계 생성"""
        try:
            import uuid
            rel_id = f"rel-{uuid.uuid4()}"
            
            query = """
            MATCH (from {id: $from_id}), (to {id: $to_id})
            CREATE (from)-[r:%s {
                id: $rel_id,
                properties: $properties,
                strength: $strength,
                confidence: $confidence,
                created_at: datetime()
            }]->(to)
            RETURN r, from, to
            """ % input.type.value
            
            params = {
                'from_id': input.from_id,
                'to_id': input.to_id,
                'rel_id': rel_id,
                'properties': input.properties,
                'strength': input.strength,
                'confidence': input.confidence
            }
            
            result = session.run_query(query, **params)
            
            if result:
                rel_data = result[0]['r']
                from_node = Query()._map_node(result[0]['from'])
                to_node = Query()._map_node(result[0]['to'])
                
                return Relationship(
                    id=rel_data.get('id'),
                    type=input.type,
                    from_node=from_node,
                    to_node=to_node,
                    properties=rel_data.get('properties'),
                    strength=rel_data.get('strength'),
                    confidence=rel_data.get('confidence'),
                    created_at=rel_data.get('created_at', datetime.now())
                )
            
            raise Exception("Failed to create relationship")
            
        except Exception as e:
            logger.error(f"Error creating relationship: {e}")
            raise
    
    @strawberry.mutation
    async def update_company_risk_score(
        self,
        id: strawberry.ID,
        risk_score: float
    ) -> Optional[Company]:
        """기업 리스크 점수 업데이트"""
        try:
            query = """
            MATCH (c:Company {id: $id})
            SET c.risk_score = $risk_score, c.updated_at = datetime()
            RETURN c
            """
            
            result = session.run_query(query, id=id, risk_score=risk_score)
            
            if result:
                company_data = result[0]['c']
                return Query()._map_company(company_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error updating company risk score: {e}")
            raise