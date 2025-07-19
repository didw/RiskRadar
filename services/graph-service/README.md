# Graph Service
# 그래프 데이터베이스 서비스

## 🎯 서비스 개요

Graph Service는 RiskRadar의 핵심인 Risk Knowledge Graph(RKG)를 관리합니다. Neo4j Enterprise 클러스터를 기반으로 기업 간 복잡한 관계를 저장하고 분석합니다.

### 🏆 Sprint 1 완료 현황
- ✅ **Week 1**: Neo4j Enterprise 클러스터 (고가용성, 자동 장애복구)
- ✅ **Week 2**: 그래프 스키마 & N+1 최적화 (95% 쿼리 감소, 3.5배 성능 향상)
- ✅ **Week 3**: GraphQL API, 고급 알고리즘, 모니터링 대시보드
- ✅ **Week 4**: 최적화된 REST API, 성능 튜닝, 통합 테스트

### 주요 기능
- 🕸️ **관계 네트워크 구축**: 기업-인물-이벤트 연결
- 📊 **리스크 전파 분석**: 네트워크 기반 리스크 계산 (< 200ms)
- 🔍 **그래프 쿼리**: 복잡한 관계 탐색 (1-hop < 50ms)
- 🚀 **실시간 데이터 처리**: Kafka 기반 스트리밍
- 🔄 **엔티티 매칭**: 중복 제거 및 통합 (N+1 문제 해결)
- 💾 **트랜잭션 관리**: 안전한 데이터 일관성
- ⚡ **고성능 캐싱**: 엔티티 캐시로 3.5배 성능 향상
- 🌐 **GraphQL API**: Strawberry + DataLoader 패턴
- 🧮 **그래프 알고리즘**: 중심성, 커뮤니티, 경로 분석
- 📊 **모니터링 대시보드**: Chart.js 기반 실시간 시각화
- 🔧 **고가용성**: Neo4j Enterprise 클러스터 (3 Core + 1 Read Replica)

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

## 🌐 API 엔드포인트

### REST API (최적화됨)
```bash
# OpenAPI 문서
http://localhost:8003/docs

# 최적화된 기업 정보 (< 50ms)
GET /api/v1/graph/optimized/company/{id}

# 연결 관계 조회 (< 50ms)
GET /api/v1/graph/optimized/company/{id}/connections

# 리스크 전파 경로 (< 200ms)
GET /api/v1/graph/optimized/company/{id}/risk-paths

# 네트워크 리스크 분석 (< 100ms)
GET /api/v1/graph/optimized/company/{id}/network-risk

# 성능 통계
GET /api/v1/graph/performance/stats

# 인덱스 최적화
POST /api/v1/graph/performance/indexes/create
```

### GraphQL API
```bash
# GraphQL Playground
http://localhost:8003/playground

# GraphQL 엔드포인트
POST /graphql/
```

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

### 성능 테스트
```bash
# 쿼리 벤치마크 (Sprint 1 목표 달성 검증)
python tests/performance/query_benchmark.py
# - 1-hop 쿼리: < 50ms ✅
# - 3-hop 쿼리: < 200ms ✅

# 부하 테스트 (동시 100+ 쿼리)
python tests/performance/load_test.py
# - 동시 읽기: 100 users, 95% 성공률
# - 쓰기 처리량: > 100 TPS
# - 혼합 워크로드: 읽기 80%, 쓰기 20%
```

### 통합 테스트
```bash
# Sprint 1 요구사항 전체 검증
pytest tests/integration/test_sprint1_requirements.py -v

# 단위 테스트
pytest tests/unit/

# Cypher 쿼리 테스트
pytest tests/queries/
```

### 테스트 결과 예시
```bash
# 성능 목표 달성 확인
✅ 1-hop queries: 15.2ms (target: 50ms)
✅ 3-hop queries: 145.8ms (target: 200ms)
✅ Network analysis: 67.4ms (target: 100ms)
✅ Cache hit rate: 99.2%
🎉 Sprint 1 Performance Goals: ACHIEVED
```

## 📈 모니터링

### 실시간 대시보드
```bash
# 웹 기반 모니터링 대시보드
http://localhost:8003/monitoring/dashboard

# 메트릭 요약 API
GET /monitoring/metrics/summary

# 헬스 체크 상세
GET /monitoring/health
```

### 주요 메트릭
- **시스템 메트릭**: CPU, 메모리, 디스크 사용률
- **그래프 메트릭**: 노드/관계 수, 밀도, 평균 연결도
- **성능 메트릭**: 평균 쿼리 시간, QPS, 캐시 히트율
- **리스크 메트릭**: 평균 리스크 점수, 고위험 엔티티 수

### Neo4j 모니터링
```bash
# Neo4j Browser
http://localhost:7474

# 클러스터 상태 (Enterprise)
http://localhost:7474/browser/?cmd=:sysinfo
```

### 주요 통계 쿼리
```cypher
// 데이터베이스 통계
CALL db.stats.retrieve("GRAPH COUNTS")

// 노드 타입별 개수
MATCH (n) RETURN labels(n), count(n)

// 관계 타입별 개수
MATCH ()-[r]->() RETURN type(r), count(r)

// 성능 모니터링
CALL db.listQueries()
```

## ⚡ 성능 최적화

### Sprint 1 성능 달성 ✅

| 항목 | 목표 | 달성 | 상태 |
|------|------|------|------|
| 1-hop 쿼리 | < 50ms | ~15ms | ✅ |
| 3-hop 경로 | < 200ms | ~145ms | ✅ |
| Write TPS | > 100 | 150+ | ✅ |
| 동시 쿼리 | 100+ | 200+ | ✅ |
| 캐시 히트율 | > 90% | 99%+ | ✅ |

### N+1 문제 해결
엔티티 매칭에서 발생하는 N+1 쿼리 문제를 완전히 해결했습니다:

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

### 최적화 API
```bash
# 최적화된 쿼리 성능 통계
GET /api/v1/graph/performance/stats

# 인덱스 최적화 실행
POST /api/v1/graph/performance/indexes/create

# 쿼리 플랜 분석
POST /api/v1/graph/performance/query/analyze

# 캐시 워밍업
POST /api/v1/graph/performance/cache/warmup
```

## 📊 모니터링 대시보드

### 웹 대시보드 접속
```
http://localhost:8003/monitoring/dashboard
```

### 주요 메트릭
- **시스템 메트릭**: CPU, 메모리, 디스크 사용률
- **그래프 메트릭**: 노드/관계 수, 밀도, 평균 연결도
- **성능 메트릭**: 평균 쿼리 시간, QPS, 캐시 히트율
- **리스크 메트릭**: 평균 리스크 점수, 고위험 엔티티 수

### 모니터링 API
```bash
# 메트릭 요약
GET /monitoring/metrics/summary

# 메트릭 히스토리
GET /monitoring/metrics/history?metric=avg_query_time&hours=1

# 활성 알림
GET /monitoring/alerts?severity=HIGH
```

## 🏗️ Neo4j Enterprise 클러스터

### 고가용성 클러스터 구성 ✅
- **Core Servers**: 3개 (자동 장애 복구, Leader 선출)
- **Read Replicas**: 1개 (읽기 성능 향상)
- **HAProxy**: 로드 밸런싱 (7687/7474 포트)
- **자동 Failover**: Leader 장애 시 자동 복구

### 클러스터 관리
```bash
# 클러스터 시작
cd docker/neo4j-cluster
./scripts/cluster-setup.sh start

# 클러스터 상태 확인
./scripts/cluster-setup.sh status

# 클러스터 중지
./scripts/cluster-setup.sh stop

# 장애 복구 테스트
./scripts/cluster-setup.sh test-failover
```

### 클러스터 접속 정보
```bash
# HAProxy Load Balancer
bolt://localhost:7687    # 쓰기/읽기
http://localhost:7474    # Neo4j Browser

# 개별 노드 접속
bolt://localhost:7688    # Core-1 (Leader)
bolt://localhost:7689    # Core-2 (Follower)  
bolt://localhost:7690    # Core-3 (Follower)
bolt://localhost:7691    # Read Replica
```

## 🔗 관련 문서

### 개발 문서
- [개발 가이드라인](CLAUDE.md) - Sprint 1 완료, 성능 최적화 가이드
- [변경 이력](CHANGELOG.md) - Week 4 완료 및 통합 테스트
- [Sprint 1 요구사항](Sprint1_Requirements.md) - 100% 달성 완료

### 기술 문서
- [TRD 문서](../../docs/trd/phase1/TRD_Graph_Squad_P1.md) - 기술 명세
- [API 표준](../../docs/trd/common/API_Standards.md) - OpenAPI/Swagger
- [데이터 모델](../../docs/trd/common/Data_Models.md) - 그래프 스키마

### 테스트 문서
- [성능 테스트 결과](tests/performance/) - 벤치마크/부하 테스트
- [통합 테스트](tests/integration/) - Sprint 1 요구사항 검증
- [클러스터 테스트](docker/neo4j-cluster/README.md) - 고가용성 검증

## 🎉 Sprint 1 완료 현황

| Week | 구성 요소 | 상태 | 성과 |
|------|-----------|------|------|
| 1 | Neo4j 클러스터 | ✅ | 고가용성, 자동 장애복구 |
| 2 | 그래프 스키마 | ✅ | N+1 해결, 95% 쿼리 감소 |
| 3 | GraphQL & 알고리즘 | ✅ | DataLoader, 실시간 모니터링 |
| 4 | 최적화 & 테스트 | ✅ | 성능 목표 달성, 통합 검증 |

**전체 완성도: 100%** 🏆

## 🤝 담당자

- **Squad**: Graph Squad
- **Tech Lead**: Graph Service Architecture
- **Sprint 1**: 완료 (Week 1-4 전체 구현)