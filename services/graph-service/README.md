# Graph Service
# 그래프 데이터베이스 서비스

## 🎯 서비스 개요

Graph Service는 RiskRadar의 핵심인 Risk Knowledge Graph(RKG)를 관리합니다. Neo4j를 기반으로 기업 간 복잡한 관계를 저장하고 분석합니다.

### 주요 기능
- 🕸️ **관계 네트워크 구축**: 기업-인물-이벤트 연결
- 📊 **리스크 전파 분석**: 네트워크 기반 리스크 계산
- 🔍 **그래프 쿼리**: 복잡한 관계 탐색
- 🚀 **실시간 데이터 처리**: Kafka 기반 스트리밍
- 🔄 **엔티티 매칭**: 중복 제거 및 통합 (N+1 문제 해결)
- 💾 **트랜잭션 관리**: 안전한 데이터 일관성
- ⚡ **고성능 캐싱**: 엔티티 캐시로 3.5배 성능 향상

## 🚀 빠른 시작

### Prerequisites
- Python 3.11+
- Neo4j 5.0+
- Docker & Docker Compose

### 설치 및 실행
```bash
# 1. Neo4j 실행
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5.0

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 데이터베이스 초기화
python scripts/init_db.py

# 4. 서비스 실행
python -m src.main

# 또는 Docker 사용
docker-compose up graph-service
```

## 📊 GraphQL API

### GraphQL Playground
```
http://localhost:4000/graphql
```

### 주요 쿼리
```graphql
# 기업 정보 조회
query GetCompany {
  company(id: "samsung-electronics") {
    name
    riskScore
    connectedCompanies {
      name
      riskScore
    }
    recentRisks {
      type
      severity
      description
    }
  }
}

# 네트워크 분석
query NetworkAnalysis {
  networkAnalysis(companyId: "samsung-electronics") {
    centralityScore
    clusterCoefficient
    connectedComponents
  }
}
```

## 🔧 설정

### 환경 변수
```env
# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Service
GRAPHQL_PORT=4000
SERVICE_PORT=8003
```

## 📝 데이터 모델

### 노드 타입
- **Company**: 기업 정보
- **Person**: 인물 (CEO, 임원 등)
- **RiskEvent**: 리스크 이벤트
- **NewsArticle**: 뉴스 기사

### 관계 타입
- `MENTIONED_IN`: 뉴스에 언급됨
- `CONNECTED_TO`: 기업 간 연결
- `HAS_CEO`: CEO 관계
- `AFFECTS`: 리스크 영향

## 🧪 테스트

```bash
# 단위 테스트
pytest tests/unit/

# 통합 테스트
pytest tests/integration/

# Cypher 쿼리 테스트
pytest tests/queries/
```

## 📈 모니터링

### Prometheus Metrics
- `graph_nodes_total`: 총 노드 수
- `graph_relationships_total`: 총 관계 수
- `query_duration_seconds`: 쿼리 실행 시간

### Neo4j Browser
```
http://localhost:7474
```

### 주요 통계 쿼리
```cypher
// 데이터베이스 통계
CALL db.stats.retrieve("GRAPH COUNTS")

// 노드 타입별 개수
MATCH (n) RETURN labels(n), count(n)

// 관계 타입별 개수
MATCH ()-[r]->() RETURN type(r), count(r)
```

## ⚡ 성능 최적화

### N+1 문제 해결
Graph Service는 엔티티 매칭에서 발생하는 N+1 쿼리 문제를 해결했습니다:

```bash
# 🚨 기존: 엔티티마다 전체 DB 조회
for entity in entities:  # 35개 엔티티
    MATCH (c:Company) RETURN c  # 35번의 전체 테이블 스캔

# ✅ 개선: 배치 캐싱으로 O(1) 처리
entity_cache.get_companies()  # 1번의 캐시 조회
batch_matcher.match_entities_batch(entities)  # 메모리에서 매칭
```

### 성능 개선 결과
- **쿼리 수 95% 감소**: 35번 → 2번
- **처리 속도 3.5배 향상**: 70ms → 20ms
- **캐시 히트율 99%**: 두 번째 조회부터 즉시 응답

### 캐시 API
```bash
# 캐시 통계 조회
GET /api/v1/graph/cache/stats

# 캐시 수동 새로고침
POST /api/v1/graph/cache/refresh
```

## 🔗 관련 문서

- [개발 가이드라인](CLAUDE.md)
- [변경 이력](CHANGELOG.md)
- [Sprint 1 요구사항](Sprint1_Requirements.md)
- [성능 테스트 가이드](tests/performance/README.md)
- [TRD 문서](../../docs/trd/phase1/TRD_Graph_Squad_P1.md)

## 🤝 담당자

- **Squad**: Graph Squad
- **Lead**: @graph-lead
- **Members**: @graph-member1, @graph-member2