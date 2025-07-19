# Technical Requirements Document
# Graph Squad - Phase 1

## 1. 개요

### 1.1 문서 정보
- **Squad**: Graph Squad
- **Phase**: 1 (Week 1-4)
- **작성일**: 2024-07-19
- **버전**: 1.0

### 1.2 범위
Neo4j 클러스터 구축, RKG 기본 스키마 구현 및 초기 데이터 로딩

### 1.3 관련 문서
- PRD: [PRD_RKG_Design.md](../../prd/PRD_RKG_Design.md)
- Architecture: [PRD_Tech_Architecture.md](../../prd/PRD_Tech_Architecture.md)
- 의존 TRD: ML/NLP Squad (엔티티 데이터)

## 2. 기술 요구사항

### 2.1 기능 요구사항
| ID | 기능명 | 설명 | 우선순위 | PRD 참조 |
|----|--------|------|----------|----------|
| F001 | 그래프 스키마 구현 | 노드/관계 타입 정의 | P0 | FR-002 |
| F002 | 데이터 임포트 | 스트리밍 데이터 그래프 저장 | P0 | FR-002 |
| F003 | 기본 쿼리 API | CRUD 및 탐색 쿼리 | P0 | FR-002 |
| F004 | 인덱스 최적화 | 성능 인덱스 구축 | P0 | FR-002 |
| F005 | 엔티티 매칭 | 중복 엔티티 병합 | P1 | FR-002 |

### 2.2 비기능 요구사항
| 항목 | 요구사항 | 측정 방법 |
|------|----------|-----------|
| 쿼리 성능 | 1-hop 쿼리 < 50ms | 응답시간 모니터링 |
| 확장성 | 100만 노드, 500만 엣지 | 부하 테스트 |
| 동시성 | 100 동시 쿼리 | 성능 테스트 |
| 가용성 | 99.9% uptime | 모니터링 |

## 3. 시스템 아키텍처

### 3.1 Neo4j 클러스터 구성
```
┌─────────────────────────────────────────────────┐
│             Neo4j Cluster (3 nodes)             │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │   Core-1    │  │   Core-2    │  │  Core-3 │ │
│  │  (Leader)   │  │  (Follower) │  │(Follower│ │
│  └──────┬──────┘  └──────┬──────┘  └────┬────┘ │
│         │                 │              │      │
│         └────────────┬────┘              │      │
│                      │                   │      │
│  ┌───────────────────┴───────────────────┘      │
│  │          Causal Consistency                  │
│  └───────────────────┬──────────────────────────┤
└─────────────────────┼───────────────────────────┘
                      │
        ┌─────────────┴──────────────┐
        │      Load Balancer         │
        └─────────────┬──────────────┘
                      │
    ┌─────────────────┴──────────────────┐
    │          Graph Service             │
    ├────────────────────────────────────┤
    │  ┌──────────┐    ┌──────────────┐ │
    │  │ Importer │    │  Query API   │ │
    │  │ Service  │    │   Service    │ │
    │  └────┬─────┘    └──────┬───────┘ │
    └───────┼─────────────────┼──────────┘
            │                 │
    ┌───────▼─────┐   ┌───────▼────────┐
    │Kafka Topic: │   │  REST/GraphQL  │
    │enriched-news│   │   Endpoints    │
    └─────────────┘   └────────────────┘
```

### 3.2 데이터 플로우
1. **입력**: enriched-news에서 엔티티 정보 수신
2. **매칭**: 기존 노드와 매칭/병합
3. **저장**: 그래프에 노드/관계 생성
4. **인덱싱**: 실시간 인덱스 업데이트

## 4. 상세 설계

### 4.1 그래프 스키마

#### 4.1.1 노드 타입
```cypher
// Company 노드
CREATE CONSTRAINT company_unique 
ON (c:Company) ASSERT c.companyId IS UNIQUE;

CREATE (c:Company {
    companyId: 'KR-{사업자번호}',
    name: '삼성전자',
    nameEn: 'Samsung Electronics',
    aliases: ['삼성', 'SEC', 'Samsung'],
    sector: 'IT/전자',
    subSector: '반도체',
    marketCap: 400000000000000,
    revenue: 279600000000000,
    employees: 267937,
    foundedYear: 1969,
    ceoName: '한종희',
    stockCode: '005930',
    description: '...',
    riskScore: 3.2,
    riskTrend: 'STABLE',
    lastUpdated: datetime(),
    metadata: {
        source: 'DART',
        confidence: 0.99
    }
})

// Person 노드
CREATE CONSTRAINT person_unique 
ON (p:Person) ASSERT p.personId IS UNIQUE;

CREATE (p:Person {
    personId: 'KR-P-{ID}',
    name: '이재용',
    nameEn: 'Lee Jae-yong',
    birthYear: 1968,
    role: '회장',
    company: '삼성전자',
    education: ['서울대학교', 'Harvard'],
    career: ['삼성전자 부회장', '삼성전자 회장'],
    influenceScore: 9.5,
    riskExposure: 4.2,
    connections: 150,
    lastUpdated: datetime()
})

// Event 노드
CREATE CONSTRAINT event_unique 
ON (e:Event) ASSERT e.eventId IS UNIQUE;

CREATE (e:Event {
    eventId: 'EVT-2024-{UUID}',
    type: 'LEGAL_RISK',
    subType: '특허분쟁',
    title: '반도체 특허 침해 소송',
    date: date('2024-07-19'),
    severity: 7,
    probability: 0.65,
    impact: 'HIGH',
    description: '...',
    source: ['Reuters', '연합뉴스'],
    relatedCountries: ['US', 'KR'],
    lastUpdated: datetime()
})

// Risk 노드
CREATE (r:Risk {
    riskId: 'RISK-{TYPE}-{ID}',
    category: 'MARKET',
    type: '환율변동',
    level: 4,
    probability: 0.7,
    potentialLoss: 1000000000,
    trend: 'INCREASING',
    mitigationCost: 50000000,
    description: '...'
})
```

#### 4.1.2 관계 타입
```cypher
// 비즈니스 관계
CREATE (c1:Company)-[:COMPETES_WITH {
    intensity: 0.8,
    market: '메모리반도체',
    marketShareOverlap: 0.65,
    since: date('2000-01-01')
}]->(c2:Company)

CREATE (c1:Company)-[:PARTNERS_WITH {
    type: 'SUPPLIER',
    contractValue: 5000000000,
    dependency: 0.3,
    since: date('2020-01-01'),
    validUntil: date('2025-12-31')
}]->(c2:Company)

CREATE (c1:Company)-[:SUBSIDIARY_OF {
    ownership: 0.51,
    since: date('2015-01-01')
}]->(c2:Company)

// 인물 관계
CREATE (p:Person)-[:LEADS {
    role: 'CEO',
    since: date('2023-01-01'),
    appointed: 'BOARD',
    salary: 1500000000
}]->(c:Company)

CREATE (p1:Person)-[:CONNECTED_TO {
    type: 'ALUMNI',
    institution: '서울대학교',
    strength: 0.6
}]->(p2:Person)

// 리스크 관계
CREATE (e:Event)-[:AFFECTS {
    impactScore: 7.5,
    impactType: 'FINANCIAL',
    estimatedLoss: 100000000000,
    duration: 180,
    confidence: 0.85
}]->(c:Company)

CREATE (c:Company)-[:EXPOSED_TO {
    exposureLevel: 0.7,
    trend: 'INCREASING',
    lastAssessed: datetime(),
    mitigationPlan: true
}]->(r:Risk)

// 뉴스 관계
CREATE (n:News)-[:MENTIONS {
    sentiment: -0.3,
    relevance: 0.9,
    context: 'MAIN_SUBJECT'
}]->(c:Company)
```

### 4.2 API 명세

#### 4.2.1 엔티티 CRUD API
```yaml
# Create/Update Company
endpoint: /api/v1/graph/company
method: POST
request:
  type: object
  properties:
    companyId: string
    name: string
    properties: object
response:
  type: object
  properties:
    nodeId: string
    created: boolean
    
# Get Company with Relations
endpoint: /api/v1/graph/company/{companyId}
method: GET
parameters:
  - name: depth
    type: integer
    default: 1
    max: 3
  - name: relationTypes
    type: array
    items: string
response:
  type: object
  properties:
    node: object
    relationships: array
    connectedNodes: array
```

#### 4.2.2 그래프 탐색 API
```yaml
# Risk Propagation Query
endpoint: /api/v1/graph/risk-propagation
method: POST
request:
  type: object
  properties:
    sourceCompanyId: string
    riskType: string
    maxDepth: integer
    minImpact: float
response:
  type: object
  properties:
    paths: array
    affectedCompanies: array
    totalRiskScore: float
    
# Shortest Path
endpoint: /api/v1/graph/shortest-path
method: GET
parameters:
  - name: from
    type: string
  - name: to
    type: string
  - name: relationTypes
    type: array
response:
  type: object
  properties:
    path: array
    distance: integer
```

### 4.3 핵심 알고리즘

#### 4.3.1 엔티티 매칭 및 병합
```python
class EntityMatcher:
    def __init__(self, graph_db):
        self.db = graph_db
        self.similarity_threshold = 0.85
    
    def match_company(self, company_data):
        # 1. ID 기반 정확한 매칭
        if company_data.get('businessNumber'):
            query = """
            MATCH (c:Company {businessNumber: $bn})
            RETURN c
            """
            result = self.db.query(query, bn=company_data['businessNumber'])
            if result:
                return result[0]['c']
        
        # 2. 이름 기반 유사도 매칭
        candidates = self._find_similar_companies(company_data['name'])
        
        for candidate in candidates:
            similarity = self._calculate_similarity(company_data, candidate)
            if similarity > self.similarity_threshold:
                return self._merge_company(candidate, company_data)
        
        # 3. 새 노드 생성
        return self._create_company(company_data)
    
    def _calculate_similarity(self, data1, data2):
        scores = []
        
        # 이름 유사도 (한글/영문)
        name_sim = jellyfish.jaro_winkler(
            data1.get('name', ''), 
            data2.get('name', '')
        )
        scores.append(name_sim * 0.4)
        
        # 별칭 매칭
        aliases1 = set(data1.get('aliases', []))
        aliases2 = set(data2.get('aliases', []))
        alias_sim = len(aliases1 & aliases2) / max(len(aliases1 | aliases2), 1)
        scores.append(alias_sim * 0.2)
        
        # 섹터 매칭
        if data1.get('sector') == data2.get('sector'):
            scores.append(0.2)
        
        # CEO 이름 매칭
        if data1.get('ceoName') == data2.get('ceoName'):
            scores.append(0.2)
        
        return sum(scores)
```

#### 4.3.2 리스크 전파 알고리즘
```cypher
// 직접 리스크 전파 계산
CALL gds.graph.project(
    'riskNetwork',
    ['Company'],
    {
        PARTNERS_WITH: {
            properties: ['dependency']
        },
        SUBSIDIARY_OF: {
            properties: ['ownership']
        },
        COMPETES_WITH: {
            properties: ['intensity']
        }
    }
)

// PageRank 기반 시스템 리스크
CALL gds.pageRank.write('riskNetwork', {
    dampingFactor: 0.85,
    maxIterations: 20,
    writeProperty: 'systemicRisk'
})

// 커스텀 리스크 전파
MATCH (source:Company {companyId: $sourceId})
CALL apoc.path.expandConfig(source, {
    relationshipFilter: 'PARTNERS_WITH|SUBSIDIARY_OF',
    maxLevel: 3,
    uniqueness: 'NODE_GLOBAL'
}) YIELD path
WITH path, 
     reduce(risk = 1.0, r in relationships(path) | 
        risk * CASE type(r)
            WHEN 'PARTNERS_WITH' THEN r.dependency * 0.5
            WHEN 'SUBSIDIARY_OF' THEN r.ownership * 0.8
            ELSE 0.1
        END
     ) as propagatedRisk
WHERE propagatedRisk > 0.1
RETURN last(nodes(path)) as company, propagatedRisk
ORDER BY propagatedRisk DESC
```

## 5. 기술 스택

### 5.1 사용 기술
- **데이터베이스**: Neo4j Enterprise 5.x
- **언어**: 
  - Java 17 (메인 서비스)
  - Python 3.11 (데이터 처리)
- **프레임워크**:
  - Spring Boot 3.x
  - Neo4j Java Driver
- **라이브러리**:
  - APOC (Neo4j 확장)
  - GDS (Graph Data Science)
- **모니터링**:
  - Neo4j Metrics
  - Micrometer

### 5.2 인프라 요구사항
- **Neo4j 클러스터**:
  - Core 서버: 3대 (8 vCPU, 32GB RAM, 500GB SSD)
  - Heap: 16GB
  - Page Cache: 12GB
- **애플리케이션 서버**:
  - 인스턴스: 2대 (4 vCPU, 16GB RAM)
- **네트워크**:
  - 클러스터 내부: 10Gbps
  - 낮은 지연시간 요구

## 6. 구현 계획

### 6.1 마일스톤
| 주차 | 목표 | 산출물 |
|------|------|--------|
| Week 1 | Neo4j 클러스터 구축 | 3-node 클러스터 |
| Week 2 | 스키마 구현 & 인덱스 | 전체 스키마 완성 |
| Week 3 | Import 서비스 구현 | 실시간 데이터 로딩 |
| Week 4 | Query API & 최적화 | API 엔드포인트 |

### 6.2 리스크 및 대응
| 리스크 | 영향도 | 대응 방안 |
|--------|--------|-----------|
| 대용량 데이터 성능 | High | 샤딩 전략, 읽기 전용 복제본 |
| 복잡한 쿼리 지연 | Medium | 쿼리 최적화, 결과 캐싱 |
| 노드 장애 | Medium | 자동 페일오버, 백업 |

## 7. 테스트 계획

### 7.1 단위 테스트
- **커버리지**: 80%
- **테스트 항목**:
  - 스키마 제약조건
  - 엔티티 매칭 로직
  - Cypher 쿼리 정확성

### 7.2 성능 테스트
- **데이터셋**: 10만 노드, 50만 관계
- **시나리오**:
  - 1-hop 쿼리: < 50ms
  - 3-hop 경로 탐색: < 200ms
  - 동시 100 쿼리: 평균 < 100ms

## 8. 완료 기준

### 8.1 기능 완료
- [x] Neo4j 클러스터 구축 완료
- [x] 전체 스키마 구현
- [x] 실시간 데이터 임포트
- [x] 기본 CRUD API

### 8.2 성능 완료
- [x] 쿼리 응답시간 목표 달성
- [x] 10만 노드 처리 가능
- [x] 시스템 가용성 99.9%

## 9. 의존성

### 9.1 외부 의존성
- **ML/NLP Squad**: 엔티티 데이터 포맷
- **Platform Squad**: 쿠버네티스 환경

### 9.2 데이터 의존성
- 초기 마스터 데이터 (기업 정보)
- 엔티티 ID 체계 정의

## 10. 부록

### 10.1 Cypher 쿼리 예제
```cypher
// 회사의 1차 리스크 네트워크
MATCH (c:Company {companyId: $id})-[r:EXPOSED_TO|AFFECTS*1]-(risk)
RETURN c, r, risk

// 경쟁사 분석
MATCH (c:Company {companyId: $id})-[:COMPETES_WITH]-(competitor)
OPTIONAL MATCH (competitor)-[:EXPOSED_TO]->(risk:Risk)
RETURN competitor, collect(risk) as risks
ORDER BY competitor.marketCap DESC
```

### 10.2 참고 자료
- [Neo4j Best Practices](https://neo4j.com/docs/operations-manual/current/performance/)
- [Graph Data Modeling](https://neo4j.com/developer/data-modeling/)