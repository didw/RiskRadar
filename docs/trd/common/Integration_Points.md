# Integration Points
# RiskRadar Squad 간 통합 지점

## 1. 개요

이 문서는 각 Squad 간의 의존성과 통합 지점을 정의합니다. 모든 Squad는 이 문서를 참조하여 다른 Squad와의 인터페이스를 구현해야 합니다.

## 2. Squad 간 의존성 매트릭스

| From \ To | Data | ML/NLP | Graph | Platform | Product |
|-----------|------|--------|-------|----------|---------|
| **Data** | - | Kafka Topic | - | Kafka Infra | Status API |
| **ML/NLP** | Data Format | - | Entity Format | GPU Nodes | - |
| **Graph** | - | Entity Data | - | Neo4j Infra | Query API |
| **Platform** | - | - | - | - | - |
| **Product** | Stats API | - | GraphQL | Auth Service | - |

## 3. 데이터 플로우

```
[Data Squad] 
    ↓ (raw-news)
[ML/NLP Squad]
    ↓ (enriched-news)
[Graph Squad]
    ↓ (GraphQL API)
[Product Squad]
    ↓ (REST/GraphQL)
[Frontend]
```

## 4. 상세 통합 지점

### 4.1 Data Squad → ML/NLP Squad

#### Kafka Topic: `raw-news`
```json
{
  "version": "1.0",
  "timestamp": "2024-07-19T10:00:00Z",
  "messageId": "msg-uuid",
  "type": "news.raw",
  "source": {
    "name": "조선일보",
    "tier": 1,
    "crawlerId": "crawler-1"
  },
  "payload": {
    "id": "news-uuid",
    "title": "string",
    "content": "string",
    "publishedAt": "2024-07-19T09:00:00Z",
    "url": "https://...",
    "author": "string",
    "category": "경제"
  },
  "metadata": {
    "crawledAt": "2024-07-19T10:00:00Z",
    "hash": "sha256",
    "contentLength": 1234
  }
}
```

**SLA**:
- 처리 지연: < 5분
- 메시지 크기: < 1MB
- 파티션 키: source.name

### 4.2 ML/NLP Squad → Graph Squad

#### Kafka Topic: `enriched-news`
```json
{
  "version": "1.0",
  "timestamp": "2024-07-19T10:01:00Z",
  "messageId": "msg-uuid",
  "type": "news.enriched",
  "original": {
    // 원본 raw-news 데이터
  },
  "nlp": {
    "entities": [
      {
        "text": "삼성전자",
        "type": "COMPANY",
        "kbId": "KR-1234567890",
        "confidence": 0.95,
        "position": [10, 14]
      }
    ],
    "sentiment": {
      "document": {"label": "negative", "score": 0.78},
      "entities": {
        "KR-1234567890": {"label": "negative", "score": 0.82}
      }
    },
    "keywords": [
      {"word": "반도체", "score": 0.85, "type": "TOPIC"}
    ],
    "processingTimeMs": 87
  }
}
```

**Entity ID 매핑 규칙**:
- ML/NLP는 임시 ID 생성
- Graph Squad가 KB ID로 매핑
- 매핑 실패 시 새 엔티티 생성

### 4.3 Graph Squad → Product Squad

#### GraphQL Endpoint
```graphql
# Endpoint: http://graph-service:4000/graphql

type Query {
  # 회사 조회
  company(companyId: ID!): Company
  
  # 리스크 전파 분석
  riskPropagation(
    sourceCompanyId: ID!
    maxDepth: Int = 3
  ): RiskPropagationResult
  
  # 관계 탐색
  shortestPath(
    from: ID!
    to: ID!
  ): PathResult
}

type Mutation {
  # 엔티티 업데이트 (내부용)
  updateCompanyRiskScore(
    companyId: ID!
    score: Float!
  ): Company
}
```

**인증**:
- 내부 서비스: mTLS
- 외부 요청: JWT 토큰

### 4.4 Platform Squad → All Squads

#### Kubernetes Resources
```yaml
# Namespace per Squad
apiVersion: v1
kind: Namespace
metadata:
  name: riskradar-{squad-name}
  labels:
    squad: {squad-name}
    environment: production

---
# Resource Quotas
apiVersion: v1
kind: ResourceQuota
metadata:
  name: {squad-name}-quota
spec:
  hard:
    requests.cpu: "10"
    requests.memory: 40Gi
    persistentvolumeclaims: "10"
```

#### Service Discovery
```yaml
# Service naming convention
{service-name}.{namespace}.svc.cluster.local

# Examples:
graph-service.riskradar-graph.svc.cluster.local
api-service.riskradar-product.svc.cluster.local
```

### 4.5 Product Squad → All Squads

#### 통합 API Gateway Routes
```yaml
# Kong Routes
/api/v1/companies/* → graph-service
/api/v1/news/* → data-service
/api/v1/analysis/* → ml-service
/graphql → graphql-service
```

#### 공통 인증 헤더
```http
Authorization: Bearer {JWT_TOKEN}
X-User-ID: {userId}
X-Company-ID: {companyId}
X-Request-ID: {requestId}
```

## 5. 서비스 간 통신

### 5.1 동기 통신 (gRPC)

#### Proto 정의
```protobuf
syntax = "proto3";

package riskradar.v1;

// Entity Service (Graph Squad)
service EntityService {
  rpc GetCompany(GetCompanyRequest) returns (Company);
  rpc SearchCompanies(SearchRequest) returns (SearchResponse);
}

message GetCompanyRequest {
  string company_id = 1;
}

message Company {
  string company_id = 1;
  string name = 2;
  float risk_score = 3;
  // ...
}
```

### 5.2 비동기 통신 (Kafka)

#### Topic 명명 규칙
```
{domain}.{entity}.{event}

예시:
- news.raw.created
- risk.company.updated
- analysis.nlp.completed
```

#### 메시지 헤더
```json
{
  "version": "1.0",
  "timestamp": "ISO8601",
  "messageId": "UUID",
  "correlationId": "UUID",
  "source": "service-name"
}
```

## 6. 에러 처리

### 6.1 에러 전파
```json
{
  "error": {
    "code": "ENTITY_NOT_FOUND",
    "message": "Company not found",
    "service": "graph-service",
    "traceId": "span-id",
    "details": {}
  }
}
```

### 6.2 재시도 정책
| 통신 유형 | 재시도 횟수 | 백오프 | 타임아웃 |
|----------|------------|--------|----------|
| gRPC | 3 | Exponential | 5s |
| Kafka | 5 | Fixed 1s | - |
| HTTP | 3 | Exponential | 30s |

## 7. 모니터링 및 추적

### 7.1 분산 추적
- Trace ID는 모든 서비스 간 전파
- Jaeger/Zipkin 통합
- 주요 스팬:
  - `data.crawl`
  - `nlp.process`
  - `graph.update`
  - `api.request`

### 7.2 메트릭
각 통합 지점에서 수집할 메트릭:
- Request rate
- Error rate
- Latency (P50, P95, P99)
- Message lag (Kafka)

## 8. 버전 관리

### 8.1 API 버전
- 하위 호환성 유지
- Breaking change 시 새 버전
- Deprecation 기간: 3개월

### 8.2 메시지 버전
- 메시지에 version 필드 포함
- 다중 버전 처리 지원

## 9. 보안

### 9.1 서비스 간 인증
- **내부**: mTLS (Istio 자동 관리)
- **외부**: JWT 토큰

### 9.2 암호화
- **전송 중**: TLS 1.3
- **저장 시**: 민감 데이터 암호화

## 10. 장애 시나리오

### 10.1 Kafka 장애
- 로컬 큐 사용 (최대 1시간)
- 중요 데이터는 DB 백업

### 10.2 Graph DB 장애
- 읽기 전용 리플리카 사용
- 캐시된 데이터 제공

### 10.3 ML 서비스 장애
- 기본 규칙 기반 처리
- 나중에 재처리

## 11. 테스트

### 11.1 통합 테스트
```bash
# 전체 파이프라인 테스트
1. Data Squad: 테스트 뉴스 생성
2. ML/NLP: 엔티티 추출 확인
3. Graph: 그래프 업데이트 확인
4. Product: API 응답 확인
```

### 11.2 계약 테스트
- Pact 또는 Spring Cloud Contract 사용
- 각 Squad가 제공자/소비자 테스트 작성

## 12. 체크리스트

### Squad Lead 체크리스트
- [ ] 의존 서비스 확인
- [ ] API 계약 정의
- [ ] 에러 처리 구현
- [ ] 모니터링 설정
- [ ] 통합 테스트 작성

### 일일 체크
- [ ] 서비스 간 지연시간
- [ ] 에러율
- [ ] 메시지 큐 지연