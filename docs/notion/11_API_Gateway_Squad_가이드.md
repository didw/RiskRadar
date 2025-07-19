# 🌐 API Gateway Squad 개발 가이드

## 팀 개요 및 역할

> **미션**: 모든 클라이언트와 마이크로서비스 간의 통합 접점 제공
> 
> **비전**: 확장 가능하고 안전한 API 생태계 구축

---

## 🎯 핵심 책임 영역

### 1. GraphQL API 통합 레이어
```yaml
주요 업무:
  - GraphQL Federation 아키텍처 설계
  - 다중 서비스 스키마 통합
  - Type-safe API 스키마 관리
  - 실시간 쿼리 최적화

기술 스택:
  - Node.js + TypeScript
  - Apollo Server 4
  - GraphQL Code Generator
  - Apollo Federation (Phase 2)
```

### 2. 실시간 통신 관리
```yaml
WebSocket 관리:
  - GraphQL Subscriptions 구현
  - 실시간 리스크 알림 시스템
  - 연결 상태 관리 및 재연결 로직
  - 세션 기반 구독 관리

성능 목표:
  - WebSocket 지연시간: <50ms
  - 동시 연결: 1000+ users
  - 메시지 전달률: 99.9%
```

### 3. 서비스 간 통신 오케스트레이션
```yaml
통합 패턴:
  - RESTful API 통합 (Data, ML, Graph Services)
  - 에러 핸들링 및 재시도 로직
  - 응답 캐싱 전략
  - 로드 밸런싱 및 서킷 브레이커

모니터링:
  - API 응답시간 추적
  - 에러율 모니터링
  - 서비스 의존성 상태 체크
```

---

## 🏗️ 현재 구현 현황 (Phase 1 완료)

### ✅ 완료된 기능

#### 1. GraphQL Core API (100% 완료)
```typescript
// 구현된 주요 스키마
type Company {
  id: ID!
  name: String!
  riskScore: Float!
  industry: String!
  recentNews: [News!]!
  connectedCompanies: [Company!]!
}

type News {
  id: ID!
  title: String!
  content: String!
  publishedAt: DateTime!
  sentimentScore: Float!
  riskCategories: [String!]!
}

// 12개 고급 분석 쿼리 구현
Query {
  companyAnalytics(companyId: ID!): CompanyAnalytics
  industryAnalytics(industry: String!): IndustryAnalytics
  riskTrendAnalysis(timeRange: TimeRange!): [RiskTrend!]!
  networkAnalysis(centerNode: ID!): NetworkGraph
  # ... 8개 추가 쿼리
}
```

#### 2. WebSocket 실시간 업데이트 (100% 완료)
```typescript
// 실시간 구독 시스템
Subscription {
  riskScoreUpdated(companyId: ID!): RiskScoreUpdate!
  newNewsAlert(filter: NewsFilter): NewsAlert!
  systemHealthUpdate: SystemHealth!
}

// 구현된 실시간 기능
- 리스크 스코어 변경 알림
- 새로운 뉴스 실시간 푸시
- 시스템 상태 모니터링
- 사용자별 맞춤 알림
```

#### 3. 고급 분석 API (100% 완료)
```typescript
// Analytics 전용 리졸버
export const analyticsResolvers = {
  Query: {
    companyAnalytics: async (_, { companyId }) => {
      // 복합 데이터 수집 및 분석
      const [basicInfo, riskData, newsData, networkData] = 
        await Promise.all([
          getCompanyBasicInfo(companyId),
          getRiskAnalysis(companyId),
          getRecentNews(companyId),
          getNetworkConnections(companyId)
        ]);
      
      return {
        company: basicInfo,
        riskMetrics: riskData,
        newsSentiment: newsData,
        networkInfluence: networkData
      };
    }
  }
};
```

### 📊 달성 성과 지표
| 지표 | 목표 | 달성 | 달성률 |
|------|------|------|--------|
| API 테스트 통과 | 30+ | 38개 | 127% |
| 응답 시간 | <200ms | <100ms | 200% |
| WebSocket 지연 | <100ms | <50ms | 200% |
| 스키마 타입 | 50+ | 80+ | 160% |

---

## 🚀 Phase 2 개발 계획 (Week 5-8)

### Sprint 3: GraphQL Federation 도입 (Week 5)
```yaml
목표: 마이크로서비스별 스키마 분산 관리

주요 작업:
  Day 1-2: Federation Gateway 설정
    - Apollo Gateway 구성
    - 서비스별 서브그래프 정의
    - 스키마 합성 테스트
  
  Day 3-4: 서비스별 스키마 분리
    - Data Service: News, Source 스키마
    - ML Service: Analysis, Sentiment 스키마  
    - Graph Service: Company, Relationship 스키마
  
  Day 5-7: 통합 테스트 및 최적화
    - Cross-service 쿼리 테스트
    - 성능 벤치마크
    - 에러 핸들링 강화

성공 기준:
  - Federation 응답시간 <150ms
  - 서비스별 독립 배포 가능
  - 스키마 충돌 0건
```

### Sprint 4: 고급 인증/권한 시스템 (Week 6)
```yaml
목표: Enterprise 수준 보안 구현

주요 작업:
  Day 1-2: JWT 기반 인증
    - Auth0/Cognito 통합
    - 토큰 검증 미들웨어
    - 세션 관리 로직
  
  Day 3-4: RBAC 권한 시스템
    - Role: CEO, CFO, Analyst, Viewer
    - 리소스별 접근 제어
    - GraphQL 디렉티브 보안
  
  Day 5-7: API Rate Limiting
    - 사용자별 요청 제한
    - 프리미엄/엔터프라이즈 티어
    - 모니터링 및 알림

성공 기준:
  - 인증 응답시간 <50ms
  - 권한 체크 정확도 100%
  - Rate limiting 정밀도 99%+
```

### Sprint 5: 고급 캐싱 전략 (Week 7)
```yaml
목표: 성능 최적화 및 확장성 확보

주요 작업:
  Day 1-2: Redis 다계층 캐싱
    - 쿼리 결과 캐싱
    - 분산 캐시 동기화
    - TTL 전략 최적화
  
  Day 3-4: GraphQL 쿼리 캐싱
    - 자동 캐시 키 생성
    - 복잡 쿼리 최적화
    - 캐시 무효화 로직
  
  Day 5-7: CDN 통합
    - 정적 리소스 CDN 배포
    - 지역별 캐시 전략
    - 성능 모니터링

성능 목표:
  - 캐시 히트율 90%+
  - 응답시간 50% 향상
  - 처리량 5배 증가
```

### Sprint 6: API Analytics & Monitoring (Week 8)
```yaml
목표: 종합 모니터링 및 인사이트 시스템

주요 작업:
  Day 1-2: OpenTelemetry 통합
    - 분산 트레이싱 구현
    - 메트릭 수집 자동화
    - 로그 상관관계 분석
  
  Day 3-4: 비즈니스 메트릭 추적
    - API 사용 패턴 분석
    - 고객별 사용량 통계
    - 인기 쿼리 순위
  
  Day 5-7: 자동화된 알림 시스템
    - SLA 위반 감지
    - 이상 패턴 알림
    - 성능 리포트 자동 생성

대시보드 구축:
  - Grafana 대시보드 (기술 메트릭)
  - 비즈니스 인텔리전스 대시보드
  - 실시간 상태 모니터링
```

---

## 🔧 개발 환경 & 도구

### 로컬 개발 설정
```bash
# API Gateway 개발 환경 실행
cd services/api-gateway
npm install
npm run dev

# GraphQL Playground 접속
# http://localhost:8004/graphql

# 코드 생성 (스키마 변경 시)
npm run codegen

# 테스트 실행
npm run test
npm run test:integration
```

### 필수 개발 도구
```yaml
IDE 설정:
  - VSCode + GraphQL 확장
  - Apollo GraphQL 확장
  - TypeScript 4.8+
  - Prettier + ESLint

디버깅 도구:
  - Apollo Studio (GraphQL 모니터링)
  - GraphQL Playground
  - Postman (REST API 테스트)
  - WebSocket King (WS 테스트)

성능 도구:
  - Artillery (로드 테스트)
  - k6 (성능 테스트)
  - Apollo Studio Metrics
```

### 스키마 관리 워크플로우
```bash
# 1. 스키마 변경
vim src/graphql/schema/analytics.graphql

# 2. 코드 생성
npm run codegen

# 3. 리졸버 구현
vim src/graphql/resolvers/analytics.ts

# 4. 테스트 작성
vim tests/analytics.test.ts

# 5. 통합 테스트
npm run test:integration
```

---

## 📋 코딩 표준 & 베스트 프랙티스

### GraphQL 스키마 설계 원칙
```graphql
# ✅ 좋은 예시
type Company {
  id: ID!
  name: String!
  riskScore: Float!
  
  # 연관 데이터는 별도 필드로
  recentNews(limit: Int = 10): [News!]!
  connectedCompanies(maxDistance: Int = 2): [Company!]!
}

# ❌ 피해야 할 패턴
type Company {
  id: ID!
  name: String!
  
  # 너무 많은 중첩은 N+1 문제 야기
  news: [News!]!
  newsWithSentiment: [NewsWithSentiment!]!
  newsWithRisk: [NewsWithRisk!]!
}
```

### TypeScript 코딩 가이드
```typescript
// ✅ 강타입 리졸버 정의
interface CompanyResolvers {
  recentNews: (
    parent: Company,
    args: { limit?: number },
    context: GraphQLContext
  ) => Promise<News[]>;
}

// ✅ 에러 핸들링
export const companyResolvers: CompanyResolvers = {
  recentNews: async (parent, { limit = 10 }, { dataSources }) => {
    try {
      const news = await dataSources.newsAPI.getByCompany(
        parent.id, 
        limit
      );
      return news.map(transformNewsItem);
    } catch (error) {
      logger.error('Failed to fetch company news', { 
        companyId: parent.id, 
        error: error.message 
      });
      throw new GraphQLError('뉴스 조회에 실패했습니다');
    }
  }
};
```

### 성능 최적화 패턴
```typescript
// ✅ DataLoader를 활용한 N+1 해결
const companyLoader = new DataLoader(async (ids: string[]) => {
  const companies = await dataSources.graphAPI.getCompaniesByIds(ids);
  return ids.map(id => companies.find(c => c.id === id));
});

// ✅ 쿼리 복잡도 제한
const depthLimit = require('graphql-depth-limit')(7);
const server = new ApolloServer({
  typeDefs,
  resolvers,
  validationRules: [depthLimit]
});
```

---

## 🧪 테스트 전략

### 단위 테스트
```typescript
// 리졸버 테스트 예시
describe('Company Resolvers', () => {
  test('recentNews returns limited news items', async () => {
    const mockDataSources = {
      newsAPI: {
        getByCompany: jest.fn().mockResolvedValue(mockNewsData)
      }
    };
    
    const result = await companyResolvers.recentNews(
      { id: 'company-1' },
      { limit: 5 },
      { dataSources: mockDataSources }
    );
    
    expect(result).toHaveLength(5);
    expect(mockDataSources.newsAPI.getByCompany)
      .toHaveBeenCalledWith('company-1', 5);
  });
});
```

### 통합 테스트
```typescript
// GraphQL 쿼리 테스트
describe('GraphQL Integration', () => {
  test('company analytics query returns complete data', async () => {
    const query = `
      query GetCompanyAnalytics($id: ID!) {
        companyAnalytics(companyId: $id) {
          company { name riskScore }
          riskMetrics { financial operational }
          newsSentiment { positive negative neutral }
        }
      }
    `;
    
    const result = await client.query({
      query,
      variables: { id: 'samsung-electronics' }
    });
    
    expect(result.data.companyAnalytics).toMatchObject({
      company: expect.objectContaining({
        name: expect.any(String),
        riskScore: expect.any(Number)
      })
    });
  });
});
```

### 성능 테스트
```javascript
// Artillery 설정 (artillery.yml)
config:
  target: 'http://localhost:8004'
  phases:
    - duration: 60
      arrivalRate: 10
scenarios:
  - name: 'GraphQL Complex Query'
    requests:
      - post:
          url: '/graphql'
          json:
            query: |
              query ComplexAnalytics($id: ID!) {
                companyAnalytics(companyId: $id) {
                  company { name riskScore recentNews { title sentimentScore } }
                  networkInfluence { centrality connections }
                }
              }
            variables:
              id: 'samsung-electronics'
```

---

## 🔍 모니터링 & 디버깅

### 핵심 메트릭 추적
```yaml
응답시간 메트릭:
  - P50, P95, P99 응답시간
  - 쿼리별 실행 시간
  - 외부 API 호출 지연시간

에러 메트릭:
  - GraphQL 에러율
  - HTTP 상태코드 분포
  - 타임아웃 발생률

비즈니스 메트릭:
  - 가장 많이 사용되는 쿼리
  - 사용자별 API 사용량
  - 리얼타임 구독자 수
```

### 로깅 표준
```typescript
// 구조화된 로깅
logger.info('GraphQL query executed', {
  operation: info.operation.operation,
  operationName: info.operation.name?.value,
  variables: args,
  executionTime: Date.now() - startTime,
  userId: context.user?.id,
  complexity: getQueryComplexity(info)
});

// 에러 로깅
logger.error('External API call failed', {
  service: 'ml-service',
  endpoint: '/api/v1/analyze',
  statusCode: error.response?.status,
  responseTime: duration,
  retryCount: attempt
});
```

### 트러블슈팅 가이드
```yaml
일반적인 문제 해결:

1. "Schema merge conflict" 에러:
   원인: 타입명 중복 또는 필드 타입 불일치
   해결: npm run codegen 실행 후 스키마 검증

2. "N+1 query detected" 경고:
   원인: DataLoader 미사용
   해결: 관련 리졸버에 DataLoader 패턴 적용

3. "WebSocket connection failed":
   원인: 네트워크 또는 인증 문제
   해결: 연결 상태 로그 확인, 재연결 로직 점검

4. "Query timeout":
   원인: 복잡한 쿼리 또는 외부 API 지연
   해결: 쿼리 복잡도 분석, 캐싱 전략 검토
```

---

## 🎯 성능 목표 & KPI

### Sprint별 목표 달성 지표

#### Sprint 3 (Federation) 목표
```yaml
기술 지표:
  - Federation 응답시간: <150ms (목표)
  - 스키마 합성 시간: <5초
  - 서비스별 독립 배포: 100% 가능

비즈니스 지표:
  - API 다운타임: 0분
  - 개발자 생산성: 30% 향상
  - 스키마 관리 효율성: 50% 향상
```

#### Sprint 4 (인증/권한) 목표
```yaml
보안 지표:
  - 인증 성공률: 99.9%+
  - 권한 체크 정확도: 100%
  - 보안 스캔 통과율: 100%

성능 지표:
  - 인증 오버헤드: <10ms
  - Rate limiting 정확도: 99%+
  - 토큰 검증 시간: <5ms
```

#### Sprint 5 (캐싱) 목표
```yaml
성능 지표:
  - 캐시 히트율: 90%+
  - 응답시간 단축: 50%+
  - 처리량 증가: 5배

비용 효율성:
  - 외부 API 호출: 70% 감소
  - 서버 리소스 사용량: 40% 감소
  - 응답 데이터 크기: 30% 감소
```

### 최종 Phase 2 목표
```yaml
종합 성능 목표:
  - API 응답시간: P95 <100ms
  - WebSocket 지연: <30ms
  - 동시 연결 지원: 5000+ users
  - API 가용성: 99.9%

확장성 목표:
  - 일일 API 요청: 1M+
  - 피크 시간 처리량: 1000 req/s
  - 자동 스케일링: 응답시간 기반

개발자 경험:
  - API 문서화: 100% 자동화
  - 스키마 검증: CI/CD 통합
  - 에러 응답: 명확한 메시지 제공
```

---

## 🚀 팀 협업 프로세스

### 일일 개발 워크플로우
```yaml
Daily Standup (09:00):
  - 전날 GraphQL 스키마 변경사항 공유
  - 외부 서비스 API 상태 점검
  - 성능 지표 리뷰 (응답시간, 에러율)

개발 작업:
  - 스키마 변경 → 코드 생성 → 리졸버 구현
  - 단위 테스트 → 통합 테스트 → 성능 테스트
  - PR 생성 → 코드 리뷰 → 배포

End-of-Day (18:00):
  - 일일 성능 메트릭 리포트 확인
  - 다음날 우선순위 작업 계획
  - 블로커 이슈 에스컬레이션
```

### 다른 Squad와의 협업
```yaml
Data Squad와의 협업:
  - 새로운 데이터 소스 API 스펙 협의
  - 응답 데이터 형식 표준화
  - 에러 코드 및 메시지 통일

ML Squad와의 협업:
  - 분석 결과 API 형식 정의
  - 실시간 분석 요청 프로토콜
  - 성능 요구사항 협의

Graph Squad와의 협업:
  - 그래프 쿼리 최적화 방안
  - 복잡한 관계 분석 API 설계
  - 실시간 그래프 업데이트 알림

Product Squad와의 협업:
  - 프론트엔드 요구사항 반영
  - 사용자 경험 개선을 위한 API 조정
  - 실시간 기능 요구사항 분석
```

### 코드 리뷰 체크리스트
```yaml
필수 체크 항목:
  ✓ GraphQL 스키마 검증 통과
  ✓ TypeScript 컴파일 에러 없음
  ✓ 단위 테스트 80% 이상 커버리지
  ✓ 통합 테스트 통과
  ✓ 성능 테스트 기준 충족

보안 체크:
  ✓ 인증/권한 검증 로직 포함
  ✓ 입력 데이터 검증 및 제한
  ✓ 민감 정보 로깅 제외
  ✓ Rate limiting 적용

성능 체크:
  ✓ N+1 쿼리 문제 없음
  ✓ 적절한 캐싱 전략 적용
  ✓ 메모리 누수 가능성 없음
  ✓ 복잡도 제한 설정
```

---

*최종 업데이트: 2025-07-19*