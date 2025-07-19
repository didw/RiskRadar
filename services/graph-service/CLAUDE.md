# Graph Service Development Guidelines
# 그래프 서비스 개발 가이드라인

## 📋 서비스 개요

Graph Service는 RiskRadar의 Risk Knowledge Graph(RKG)를 관리하는 핵심 서비스입니다. Neo4j를 기반으로 기업, 인물, 이벤트 간의 복잡한 관계를 저장하고 쿼리합니다.

## 🏗️ 프로젝트 구조

```
graph-service/
├── src/
│   ├── neo4j/              # Neo4j 연동
│   │   ├── driver.py       # 드라이버 관리
│   │   ├── session.py      # 세션 관리
│   │   └── config.py       # 연결 설정
│   ├── models/             # 그래프 모델
│   │   ├── nodes.py        # 노드 정의
│   │   ├── relationships.py # 관계 정의
│   │   └── schemas.py      # 스키마 검증
│   ├── queries/            # Cypher 쿼리
│   │   ├── company.py      # 기업 관련 쿼리
│   │   ├── risk.py         # 리스크 분석 쿼리
│   │   ├── network.py      # 네트워크 분석
│   │   └── templates/      # 쿼리 템플릿
│   ├── kafka/              # Kafka 연동
│   │   ├── consumer.py
│   │   └── handlers.py
│   ├── graphql/            # GraphQL API
│   │   ├── schema.py       # GraphQL 스키마
│   │   ├── resolvers.py    # 리졸버
│   │   └── types.py        # 타입 정의
│   └── algorithms/         # 그래프 알고리즘
│       ├── centrality.py   # 중심성 분석
│       ├── community.py    # 커뮤니티 탐지
│       └── pathfinding.py  # 경로 탐색
├── scripts/                # 유틸리티 스크립트
│   ├── init_db.py         # DB 초기화
│   └── migrations/        # 스키마 마이그레이션
├── tests/                 # 테스트
├── requirements.txt
├── Dockerfile
├── README.md
├── CLAUDE.md             # 현재 파일
└── CHANGELOG.md
```

## 💻 개발 환경 설정

### Prerequisites
```bash
Python 3.11+
Neo4j 5.0+
Docker & Docker Compose
```

### 설치
```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# Neo4j 로컬 실행
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5.0

# 환경 변수 설정
cp .env.example .env
```

### 데이터베이스 초기화
```bash
# 스키마 생성
python scripts/init_db.py

# 제약조건 및 인덱스
python scripts/create_constraints.py
```

## 🔧 주요 컴포넌트

### 1. Graph Models
```python
# 노드 정의
class Company(StructuredNode):
    """기업 노드"""
    company_id = StringProperty(unique_index=True, required=True)
    name = StringProperty(required=True)
    industry = StringProperty()
    market_cap = FloatProperty()
    risk_score = FloatProperty(default=5.0)
    last_updated = DateTimeProperty(default_now=True)
    
    # 관계
    mentioned_in = RelationshipTo('NewsArticle', 'MENTIONED_IN')
    connected_to = RelationshipTo('Company', 'CONNECTED_TO')
    has_ceo = RelationshipTo('Person', 'HAS_CEO')

class RiskEvent(StructuredNode):
    """리스크 이벤트 노드"""
    event_id = StringProperty(unique_index=True, required=True)
    type = StringProperty(required=True)  # FINANCIAL, LEGAL, REPUTATION
    severity = IntegerProperty(min_value=1, max_value=10)
    description = StringProperty()
    occurred_at = DateTimeProperty(required=True)
    
    # 관계
    affects = RelationshipTo('Company', 'AFFECTS')
    caused_by = RelationshipTo('Person', 'CAUSED_BY')
```

### 2. Cypher Query Templates
```python
class CompanyQueries:
    """기업 관련 쿼리"""
    
    @staticmethod
    def find_connected_risks(company_id: str, depth: int = 2):
        """연결된 리스크 찾기"""
        query = """
        MATCH (c:Company {company_id: $company_id})
        MATCH path = (c)-[*1..$depth]-(risk:RiskEvent)
        WHERE risk.severity >= 7
        RETURN c, path, risk
        ORDER BY risk.occurred_at DESC
        LIMIT 50
        """
        return query
    
    @staticmethod
    def calculate_network_risk(company_id: str):
        """네트워크 리스크 계산"""
        query = """
        MATCH (c:Company {company_id: $company_id})
        MATCH (c)-[:CONNECTED_TO*1..2]-(connected:Company)
        WITH c, connected, connected.risk_score as risk
        RETURN c.name as company,
               avg(risk) as network_risk,
               count(connected) as connected_companies
        """
        return query
```

### 3. GraphQL Schema
```graphql
type Company {
  id: ID!
  name: String!
  riskScore: Float!
  industry: String
  connectedCompanies: [Company!]
  recentRisks: [RiskEvent!]
  networkRisk: NetworkRisk!
}

type RiskEvent {
  id: ID!
  type: RiskType!
  severity: Int!
  description: String
  occurredAt: DateTime!
  affectedCompanies: [Company!]
}

type Query {
  company(id: ID!): Company
  companies(limit: Int = 10): [Company!]
  riskEvents(
    companyId: ID
    type: RiskType
    minSeverity: Int
  ): [RiskEvent!]
  networkAnalysis(companyId: ID!): NetworkAnalysis!
}

type Mutation {
  updateCompanyRisk(id: ID!, riskScore: Float!): Company!
  createRiskEvent(input: RiskEventInput!): RiskEvent!
}
```

### 4. Kafka Message Handler
```python
class GraphMessageHandler:
    """Kafka 메시지 처리"""
    
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    
    async def handle_enriched_news(self, message: dict):
        """ML 서비스에서 온 뉴스 처리"""
        with self.driver.session() as session:
            # 트랜잭션으로 처리
            session.execute_write(self._create_news_graph, message)
    
    @staticmethod
    def _create_news_graph(tx, message):
        """뉴스 그래프 생성"""
        # 1. 뉴스 노드 생성
        news_query = """
        CREATE (n:NewsArticle {
            id: $id,
            title: $title,
            published_at: datetime($published_at),
            sentiment: $sentiment
        })
        """
        tx.run(news_query, **message['original'])
        
        # 2. 엔티티 연결
        for entity in message['nlp']['entities']:
            if entity['type'] == 'COMPANY':
                company_query = """
                MERGE (c:Company {name: $name})
                WITH c
                MATCH (n:NewsArticle {id: $news_id})
                CREATE (c)-[:MENTIONED_IN {
                    confidence: $confidence,
                    sentiment: $sentiment
                }]->(n)
                """
                tx.run(company_query, 
                    name=entity['text'],
                    news_id=message['original']['id'],
                    confidence=entity['confidence'],
                    sentiment=message['nlp']['sentiment']['score']
                )
```

## 📝 코딩 규칙

### 1. Cypher 쿼리 작성
- 파라미터 바인딩 사용 (인젝션 방지)
- 인덱스 활용 최적화
- EXPLAIN/PROFILE로 성능 확인
- 트랜잭션 적절히 활용

### 2. 그래프 모델링
```cypher
// Good: 명확한 관계 방향
(Company)-[:OWNS]->(Subsidiary)
(Person)-[:WORKS_AT]->(Company)

// Bad: 양방향 관계
(Company)-[:RELATED]-(Company)
```

### 3. 성능 최적화
```python
# 배치 처리
def batch_create_nodes(nodes: List[dict], batch_size: int = 1000):
    """대량 노드 생성"""
    with driver.session() as session:
        for i in range(0, len(nodes), batch_size):
            batch = nodes[i:i+batch_size]
            session.execute_write(lambda tx: tx.run(
                "UNWIND $nodes as node CREATE (n:Company) SET n = node",
                nodes=batch
            ))

# 연결 풀 설정
driver = GraphDatabase.driver(
    uri,
    auth=auth,
    max_connection_pool_size=50,
    connection_acquisition_timeout=30
)
```

### 4. 에러 처리
```python
from neo4j.exceptions import ServiceUnavailable, TransientError

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def execute_query(query: str, **params):
    try:
        with driver.session() as session:
            return session.run(query, **params).data()
    except ServiceUnavailable:
        logger.error("Neo4j service unavailable")
        raise
    except TransientError as e:
        logger.warning(f"Transient error, retrying: {e}")
        raise
```

## 🧪 테스트

### 단위 테스트
```bash
pytest tests/unit/
```

### 통합 테스트
```bash
# Neo4j 테스트 인스턴스 실행
docker-compose -f docker-compose.test.yml up -d

# 테스트 실행
pytest tests/integration/
```

### 그래프 쿼리 테스트
```python
def test_risk_propagation():
    """리스크 전파 테스트"""
    # Given: 연결된 기업 네트워크
    create_test_network()
    
    # When: 한 기업에 리스크 이벤트 발생
    create_risk_event("company-1", severity=8)
    
    # Then: 연결된 기업들의 네트워크 리스크 증가
    network_risk = calculate_network_risk("company-2")
    assert network_risk > baseline_risk
```

## 🚀 배포

### Docker 빌드
```bash
docker build -t riskradar/graph-service:latest .
```

### 환경 변수
```env
# Neo4j
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:9092

# GraphQL
GRAPHQL_PORT=4000

# Service
SERVICE_PORT=8003
```

### Neo4j 프로덕션 설정
```yaml
# neo4j.conf
dbms.memory.heap.initial_size=2g
dbms.memory.heap.max_size=4g
dbms.memory.pagecache.size=2g

# 쿼리 캐시
dbms.query_cache_size=100
cypher.query_cache_size=1000
```

## 📊 모니터링

### Health Check
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "neo4j": check_neo4j_connection(),
        "kafka": check_kafka_connection(),
        "node_count": get_total_nodes(),
        "relationship_count": get_total_relationships()
    }
```

### Metrics
- 노드/관계 생성 속도
- 쿼리 응답 시간
- 트랜잭션 처리량
- 캐시 히트율

### Neo4j 모니터링
```cypher
// 데이터베이스 통계
CALL db.stats.retrieve("GRAPH COUNTS")

// 쿼리 성능
CALL db.listQueries()

// 인덱스 사용률
SHOW INDEXES
```

## 🔒 보안

### 접근 제어
- Role-based access control
- 쿼리 권한 제한
- SSL/TLS 암호화

### 쿼리 보안
```python
# Good: 파라미터 바인딩
session.run("MATCH (n:Company {name: $name})", name=user_input)

# Bad: 문자열 연결
session.run(f"MATCH (n:Company {name: '{user_input}'})")  # 위험!
```

## 🤝 협업

### Input/Output
- **Input**: Kafka topic `enriched-news`
- **Output**: GraphQL API
- **Schema**: [GraphQL Schema](#3-graphql-schema)

### API 엔드포인트
- GraphQL: `http://localhost:4000/graphql`
- REST: `http://localhost:8003/api/v1/`

## 🐛 트러블슈팅

### 일반적인 문제

#### 1. 메모리 부족
```bash
# heap 크기 증가
NEO4J_dbms_memory_heap_max__size=8g

# 페이지 캐시 조정
NEO4J_dbms_memory_pagecache_size=4g
```

#### 2. 느린 쿼리
```cypher
// 쿼리 프로파일링
PROFILE MATCH (n:Company)-[*1..3]-(m) RETURN n, m

// 인덱스 생성
CREATE INDEX company_name FOR (c:Company) ON (c.name)
```

#### 3. 데드락
- 트랜잭션 크기 줄이기
- 락 순서 일관성 유지
- 재시도 로직 구현

## 📚 참고 자료

- [Neo4j Documentation](https://neo4j.com/docs/)
- [Cypher Query Language](https://neo4j.com/docs/cypher-manual/)
- [Graph Data Science Library](https://neo4j.com/docs/graph-data-science/)

## 🎯 Sprint 개발 가이드

현재 Sprint의 상세 요구사항은 다음 문서를 참고하세요:
- [Sprint 1 Requirements](./Sprint1_Requirements.md) - Week별 구현 목표
- [Sprint Breakdown](../../docs/trd/phase1/Sprint_Breakdown.md) - 전체 Sprint 계획

### Sprint 1 Week 2 완료 사항 ✅
1. **TRD 기반 스키마 강화**
   - Risk 노드 타입 추가
   - Company 노드 확장 (aliases, sector 등)
   - Event 타입 열거형 정의
   - 관계 속성 강화

2. **인프라 개선**
   - 데이터베이스 마이그레이션 시스템
   - 트랜잭션 관리 (TransactionManager)
   - Dead Letter Queue (DLQ)
   - 재시도 로직 구현

3. **API 확장**
   - 7개 신규 REST 엔드포인트
   - 기업 CRUD 및 관계 조회
   - 리스크 분석 API
   - 마이그레이션 API
   - 캐시 관리 API

4. **테스트 강화**
   - 통합 테스트 스위트
   - 성능 테스트 프레임워크
   - 자동화된 테스트 스크립트

### 🚨 긴급 수정 완료 ✅
5. **N+1 쿼리 문제 해결**
   - 엔티티 캐시 시스템 구현
   - 배치 엔티티 매칭 도입
   - 쿼리 수 95% 감소 (35번 → 2번)
   - 처리 속도 3.5배 향상

### 다음 단계 (Week 3)
1. Neo4j Enterprise 클러스터 구성
2. GraphQL API 구현
3. 모니터링 대시보드 설정

## 📁 프로젝트 문서

### 핵심 문서
- [Graph Squad TRD](../../docs/trd/phase1/TRD_Graph_Squad_P1.md) - 기술 명세
- [API 표준](../../docs/trd/common/API_Standards.md) - API 설계
- [데이터 모델](../../docs/trd/common/Data_Models.md) - 공통 구조

### 연관 서비스
- [ML Service](../ml-service/CLAUDE.md) - Kafka 메시지 송신
- [API Gateway](../api-gateway/CLAUDE.md) - GraphQL 쿼리 수신
- [통합 가이드](../../integration/README.md) - 시스템 통합