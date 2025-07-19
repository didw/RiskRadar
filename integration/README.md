# Integration Tests & Documentation
# 통합 테스트 및 문서

## 🎯 개요

이 디렉토리는 RiskRadar의 모든 서비스 간 통합 테스트와 관련 문서를 포함합니다. End-to-End 테스트, Contract 테스트, 성능 테스트 등을 관리합니다.

## 📁 디렉토리 구조

```
integration/
├── e2e/                    # End-to-End 테스트
│   ├── scenarios/          # 테스트 시나리오
│   │   ├── news-flow.test.ts
│   │   ├── risk-analysis.test.ts
│   │   └── user-journey.test.ts
│   ├── fixtures/           # 테스트 데이터
│   └── utils/             # 테스트 유틸리티
├── contracts/             # Contract 테스트
│   ├── data-ml.contract.ts
│   ├── ml-graph.contract.ts
│   └── graph-api.contract.ts
├── performance/           # 성능 테스트
│   ├── load-tests/
│   ├── stress-tests/
│   └── benchmarks/
├── docker-compose.test.yml # 테스트 환경 설정
├── Makefile               # 테스트 실행 명령어
└── README.md             # 현재 파일
```

## 🧪 테스트 종류

### 1. End-to-End 테스트
전체 시스템 플로우를 검증하는 테스트

#### ✅ Sprint 1 Week 1 통합 테스트 결과 (2024-07-19)
**완전한 데이터 플로우 검증 성공**
- **뉴스 처리 플로우**: Data Service → Kafka → ML Service → Graph Service ✅
- **처리량**: 6개 뉴스 노드 성공적으로 Neo4j에 저장
- **에러율**: 0% (모든 서비스 정상 동작)
- **응답 시간**: 모든 서비스 2초 이내 응답
- **Health Check**: 전체 서비스 정상 상태 확인

#### 주요 시나리오
- **뉴스 처리 플로우**: 크롤링 → NLP → 그래프 저장 → UI 표시 ✅ **검증 완료**
- **리스크 분석**: 데이터 수집 → 분석 → 알림
- **사용자 여정**: 로그인 → 대시보드 → 상세 분석

### 2. Contract 테스트
서비스 간 인터페이스 계약을 검증

#### 테스트 대상
- Kafka 메시지 스키마
- GraphQL API 스키마
- REST API 응답 형식

### 3. 성능 테스트
시스템 성능 목표 달성 여부 검증

#### 측정 지표
- 처리량 (TPS)
- 응답 시간 (P50, P95, P99)
- 리소스 사용률
- 확장성

## 🚀 테스트 실행

### Prerequisites
```bash
# 필요한 도구 설치
npm install -g @playwright/test
npm install -g k6
docker-compose --version
```

### 전체 테스트 실행
```bash
# 테스트 환경 시작
make test-env-up

# 모든 테스트 실행
make test-all

# 테스트 환경 정리
make test-env-down
```

### 개별 테스트 실행
```bash
# E2E 테스트만
make test-e2e

# Contract 테스트만
make test-contracts

# 성능 테스트만
make test-performance
```

## 📊 E2E 테스트 예시

### 뉴스 처리 플로우
```typescript
// e2e/scenarios/news-flow.test.ts
import { test, expect } from '@playwright/test';
import { generateMockNews, waitForProcessing } from '../utils';

test.describe('News Processing Flow', () => {
  test('should process news from crawling to UI display', async ({ page }) => {
    // 1. Generate mock news
    const newsId = await generateMockNews();
    
    // 2. Wait for ML processing
    await waitForProcessing('ml-service', newsId);
    
    // 3. Wait for graph storage
    await waitForProcessing('graph-service', newsId);
    
    // 4. Check UI display
    await page.goto('http://localhost:3000');
    await expect(page.locator(`[data-news-id="${newsId}"]`)).toBeVisible();
    
    // 5. Verify risk score update
    const riskScore = await page.locator('.risk-score').textContent();
    expect(parseFloat(riskScore)).toBeGreaterThan(0);
  });
});
```

## 🔄 Contract 테스트 예시

### Kafka 메시지 Contract
```typescript
// contracts/data-ml.contract.ts
import { validateSchema } from '@contract-testing/validator';
import { RawNewsSchema, EnrichedNewsSchema } from '@shared/schemas';

describe('Data Service → ML Service Contract', () => {
  test('raw-news message schema', async () => {
    const message = await consumeKafkaMessage('raw-news');
    
    const validation = validateSchema(message, RawNewsSchema);
    expect(validation.valid).toBe(true);
    
    // 필수 필드 확인
    expect(message).toHaveProperty('id');
    expect(message).toHaveProperty('title');
    expect(message).toHaveProperty('content');
    expect(message).toHaveProperty('publishedAt');
  });
});
```

## 📈 성능 테스트 예시

### Load Test
```javascript
// performance/load-tests/api-load.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 100 }, // Ramp up
    { duration: '5m', target: 100 }, // Stay at 100 users
    { duration: '2m', target: 0 },   // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<200'], // 95% of requests under 200ms
    http_req_failed: ['rate<0.1'],    // Error rate under 10%
  },
};

export default function () {
  const query = `
    query GetCompanies {
      companies(limit: 10) {
        id
        name
        riskScore
      }
    }
  `;
  
  const res = http.post('http://localhost:4000/graphql', JSON.stringify({
    query: query,
  }), {
    headers: { 'Content-Type': 'application/json' },
  });
  
  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 200ms': (r) => r.timings.duration < 200,
  });
  
  sleep(1);
}
```

## 🔧 테스트 환경 설정

### docker-compose.test.yml
```yaml
version: '3.8'

services:
  # Test Database
  test-neo4j:
    image: neo4j:5.0
    environment:
      NEO4J_AUTH: neo4j/test
    ports:
      - "7475:7474"
      - "7688:7687"
  
  # Test Kafka
  test-kafka:
    image: confluentinc/cp-kafka:latest
    environment:
      KAFKA_ZOOKEEPER_CONNECT: test-zookeeper:2181
    depends_on:
      - test-zookeeper
  
  # All services with test configuration
  # ...
```

## 📝 CI/CD 통합

### GitHub Actions
```yaml
# .github/workflows/integration-tests.yml
name: Integration Tests

on:
  pull_request:
    branches: [main, develop]

jobs:
  integration-tests:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Start test environment
        run: make test-env-up
        
      - name: Run E2E tests
        run: make test-e2e
        
      - name: Run contract tests
        run: make test-contracts
        
      - name: Upload test results
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: integration/test-results/
```

## 📊 테스트 리포트

### 리포트 생성
```bash
# HTML 리포트 생성
make test-report

# 리포트 확인
open integration/test-results/report.html
```

### 메트릭 수집
- 테스트 실행 시간
- 성공/실패 비율
- 코드 커버리지
- 성능 메트릭

## 🚨 테스트 실패 시

### 디버깅 단계
1. 로그 확인: `docker-compose logs <service-name>`
2. 서비스 상태 확인: `make health-check`
3. 네트워크 연결 확인
4. 테스트 데이터 검증

### 일반적인 문제
- Kafka 연결 실패 → 토픽 생성 확인
- 타임아웃 → 대기 시간 증가
- 스키마 불일치 → Contract 테스트 업데이트

## 🤝 기여 가이드

### 새로운 테스트 추가
1. 적절한 디렉토리에 테스트 파일 생성
2. 테스트 시나리오 문서화
3. CI 파이프라인에 포함
4. README 업데이트

### 테스트 명명 규칙
- E2E: `<feature>-flow.test.ts`
- Contract: `<service1>-<service2>.contract.ts`
- Performance: `<scenario>-load.js`

## 📞 담당자

- **Integration Lead**: @integration-lead
- **E2E Tests**: @e2e-owner
- **Performance Tests**: @perf-owner