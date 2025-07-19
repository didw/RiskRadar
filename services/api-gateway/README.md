# API Gateway
# GraphQL API 게이트웨이

## 🎯 서비스 개요

API Gateway는 RiskRadar 플랫폼의 통합 API 레이어입니다. GraphQL을 통해 클라이언트에게 단일 엔드포인트를 제공하고, 여러 마이크로서비스의 데이터를 통합합니다.

### 주요 기능
- 🔐 **인증/인가**: JWT 기반 사용자 인증
- 🔄 **데이터 통합**: 여러 서비스의 데이터 조합
- 📊 **GraphQL API**: 유연한 쿼리 인터페이스
- ⚡ **성능 최적화**: DataLoader, 배치 쿼리
- 🛡️ **에러 처리**: 표준화된 에러 관리
- 🔍 **서비스 통합**: Graph/ML 서비스 클라이언트
- 🔴 **실시간 업데이트**: WebSocket 기반 GraphQL Subscriptions (Week 3 추가)
- 📈 **고급 분석**: 복잡한 Analytics 쿼리 및 시계열 데이터 (Week 3 추가)

## 🚀 빠른 시작

### Prerequisites
- Node.js 18+
- npm or yarn
- Docker & Docker Compose

### 설치 및 실행
```bash
# 1. 의존성 설치
npm install

# 2. 환경 설정
cp .env.example .env

# 3. 개발 서버 실행
npm run dev

# 또는 프로덕션 실행
npm run build
npm start

# Docker 사용
docker-compose up api-gateway
```

## 📊 GraphQL API

### GraphQL Playground
```
http://localhost:4000/graphql
```

### 인증
```http
Authorization: Bearer <JWT_TOKEN>
```

### 주요 쿼리
```graphql
# 로그인
mutation Login {
  login(email: "user@example.com", password: "password") {
    token
    user {
      id
      email
      role
    }
  }
}

# 기업 리스크 조회
query GetCompanyRisk {
  company(id: "samsung-electronics") {
    name
    riskScore
    recentRisks {
      type
      severity
      occurredAt
    }
    insights {
      title
      description
      importance
    }
  }
}

# 대시보드
query Dashboard {
  dashboard {
    totalCompanies
    highRiskCompanies {
      id
      name
      riskScore
    }
    recentAlerts {
      id
      message
      severity
      timestamp
    }
  }
}
```

### 실시간 구독 (Week 3 추가)
```graphql
# 리스크 알림 구독
subscription RiskAlerts {
  riskAlert(companyIds: ["samsung", "lg", "sk"]) {
    companyId
    type
    severity
    message
    timestamp
  }
}

# 실시간 리스크 점수 업데이트 
subscription RiskScoreUpdates {
  riskScoreUpdates {
    company {
      id
      name
      riskScore
    }
    riskTrend {
      date
      averageRiskScore
      articleCount
    }
    sentimentAnalysis {
      overall {
        label
        score
        confidence
      }
    }
  }
}

# 시장 감정 업데이트
subscription MarketSentiment {
  marketSentimentUpdates {
    positive
    neutral
    negative
    total
  }
}
```

### 고급 분석 쿼리 (Week 3 추가)
```graphql
# 기업별 종합 분석
query CompanyAnalytics {
  companyAnalytics(
    companyId: "samsung-electronics"
    timeRange: { from: "2024-01-01", to: "2024-07-19" }
    includeCompetitors: true
  ) {
    company {
      id
      name
      riskScore
    }
    riskTrend {
      date
      averageRiskScore
      articleCount
      topRiskCategories {
        category
        score
        count
        trend
      }
    }
    newsVolume {
      date
      count
      sources {
        source
        count
        averageSentiment
      }
    }
    competitorComparison {
      competitor {
        id
        name
      }
      riskScoreComparison
      marketPosition
    }
  }
}

# 산업별 분석
query IndustryAnalytics {
  industryAnalytics(
    industry: "반도체"
    timeRange: { from: "2024-01-01", to: "2024-07-19" }
    limit: 50
  ) {
    industry
    averageRiskScore
    totalCompanies
    newsVolume
    topCompanies {
      id
      name
      riskScore
    }
    riskDistribution {
      range
      count
      percentage
    }
    emergingRisks {
      risk
      description
      severity
      frequency
    }
  }
}

# 네트워크 분석
query NetworkAnalysis {
  networkAnalysis(
    companies: ["samsung", "lg", "sk"]
    maxDegrees: 2
  ) {
    centralCompanies {
      company {
        id
        name
      }
      influenceScore
      connections
      riskPropagation
    }
    riskClusters {
      id
      companies {
        id
        name
      }
      sharedRisks
      clusterRiskScore
    }
  }
}

# 고급 검색
query AdvancedSearch {
  advancedSearch(
    query: "반도체 공급망"
    filters: {
      industry: ["반도체", "전자"]
      riskLevel: ["HIGH", "CRITICAL"]
    }
    timeRange: { from: "2024-07-01", to: "2024-07-19" }
    limit: 20
    includeNews: true
    includeInsights: true
  ) {
    companies {
      id
      name
      riskScore
    }
    news {
      id
      title
      source
      publishedAt
    }
    insights {
      insight
      type
      confidence
      significance
    }
    totalResults
    searchTime
    suggestions
  }
}
```

## 🔧 설정

### 환경 변수
```env
# Server
PORT=4000
NODE_ENV=development

# Services
GRAPH_SERVICE_URL=http://localhost:8003
ML_SERVICE_URL=http://localhost:8002
DATA_SERVICE_URL=http://localhost:8001

# Auth
JWT_SECRET=your-secret-key
JWT_EXPIRES_IN=7d

# Redis
REDIS_URL=redis://localhost:6379
```

## 📝 API 스키마

### 주요 타입
```graphql
type Company {
  id: ID!
  name: String!
  riskScore: Float!
  industry: String
  marketCap: Float
  recentRisks: [RiskEvent!]!
  insights: [Insight!]!
}

type RiskEvent {
  id: ID!
  type: RiskType!
  severity: Int!
  description: String!
  occurredAt: DateTime!
}

type User {
  id: ID!
  email: String!
  name: String!
  role: Role!
  preferences: UserPreferences!
}
```

## 🧪 테스트

### 현재 상황 ✅
- **총 38개 테스트 모두 통과**
- **단위 테스트**: 13개 (Company Resolver)
- **통합 테스트**: 25개 (Service Clients)

```bash
# 전체 테스트 실행
npm test

# 단위 테스트만
npm run test:unit

# 통합 테스트만
npm run test:integration

# 테스트 커버리지
npm run test:coverage
```

### 테스트 커버리지
- **Resolvers**: GraphQL 리졸버 로직 검증
- **Service Clients**: 외부 서비스 통신 테스트
- **DataLoader**: 배치 쿼리 최적화 확인
- **Error Handling**: 에러 시나리오 처리

## 📈 모니터링

### Prometheus Metrics
- `graphql_request_duration`: 요청 처리 시간
- `graphql_request_total`: 총 요청 수
- `graphql_error_total`: 에러 수

### Health Check
```bash
GET /health
```

### Apollo Studio
프로덕션 환경에서 Apollo Studio를 통한 모니터링 지원

## 🔒 보안

### 인증 방식
- JWT Bearer Token
- Refresh Token Rotation
- Session Management

### Rate Limiting
- 일반 사용자: 100 requests / 15분
- Premium 사용자: 1000 requests / 15분

### 권한 관리
- `USER`: 기본 조회 권한
- `PREMIUM`: 고급 분석 기능
- `ADMIN`: 전체 관리 권한

## 🔗 관련 문서

- [개발 가이드라인](CLAUDE.md)
- [변경 이력](CHANGELOG.md)
- [GraphQL 스키마](schema.graphql)
- [API 문서](docs/api.md)

## 🤝 담당자

- **Squad**: Product Squad
- **Lead**: @product-lead
- **Members**: @api-developer1, @api-developer2