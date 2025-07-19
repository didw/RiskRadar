# API Gateway Development Guidelines
# API 게이트웨이 개발 가이드라인

## 📋 서비스 개요

API Gateway는 RiskRadar의 통합 API 엔드포인트를 제공하는 서비스입니다. GraphQL을 통해 클라이언트에게 통합된 데이터 접근을 제공하고, 인증/인가를 처리합니다.

### 🎯 현재 상태 (Sprint 1 Week 2 완료)
- ✅ Apollo Server 4 기반 GraphQL API 구현
- ✅ TypeScript 환경 및 빌드 시스템 구성
- ✅ 포괄적인 GraphQL 스키마 정의 (Company, Risk, User, News)
- ✅ Mock Resolver로 전체 API 구조 구현
- ✅ JWT 인증 미들웨어 기반 구조 준비
- ✅ Health check 엔드포인트
- ✅ Security 헤더 및 CORS 설정
- ✅ Graph Service 클라이언트 구현 및 통합
- ✅ ML Service 상태 조회 구현
- ✅ DataLoader 패턴으로 N+1 쿼리 문제 해결
- ✅ 포괄적인 테스트 코드 작성 (38개 테스트)
- ✅ Multi-stage Docker 빌드 최적화

### 📡 접속 정보
- **GraphQL Playground**: http://localhost:8004/graphql
- **Health Check**: http://localhost:8004/health

## 🏗️ 프로젝트 구조

```
api-gateway/
├── src/
│   ├── graphql/            # GraphQL 설정
│   │   ├── schema/         # 스키마 정의
│   │   │   ├── company.graphql
│   │   │   ├── risk.graphql
│   │   │   └── user.graphql
│   │   ├── resolvers/      # 리졸버
│   │   │   ├── company.ts
│   │   │   ├── risk.ts
│   │   │   └── user.ts
│   │   ├── directives/     # 커스텀 디렉티브
│   │   └── dataloaders/    # DataLoader
│   ├── auth/              # 인증/인가
│   │   ├── jwt.ts         # JWT 처리
│   │   ├── middleware.ts   # 인증 미들웨어
│   │   └── permissions.ts  # 권한 관리
│   ├── services/          # 서비스 클라이언트
│   │   ├── graph.client.ts
│   │   ├── ml.client.ts
│   │   └── data.client.ts
│   ├── middleware/        # 미들웨어
│   │   ├── rateLimit.ts
│   │   ├── logging.ts
│   │   └── error.ts
│   ├── utils/            # 유틸리티
│   └── index.ts          # 진입점
├── tests/                # 테스트
├── package.json
├── tsconfig.json
├── Dockerfile
├── README.md
├── CLAUDE.md            # 현재 파일
└── CHANGELOG.md
```

## 💻 개발 환경 설정

### Prerequisites
```bash
Node.js 18+
npm or yarn
Docker
```

### 🚀 빠른 시작
```bash
# 1. 의존성 설치
npm install

# 2. 환경 설정
cp .env.example .env

# 3. 빌드
npm run build

# 4. 개발 서버 실행
npm run dev

# 또는 프로덕션 모드
npm start
```

### ✅ 동작 확인
```bash
# Health check
curl http://localhost:4000/health

# GraphQL 쿼리 테스트
curl -X POST http://localhost:4000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ company(id: \"1\") { id name industry riskScore } }"}'
```

### 환경 변수
주요 환경 변수는 `.env.example` 참조

## 📈 개발 현황

### Week 1 완료 ✅
- [x] Apollo Server 4 설정
- [x] GraphQL 스키마 정의 (Company, Risk, User, News)
- [x] Mock Resolver 구현
- [x] JWT 인증 미들웨어
- [x] Health Check 엔드포인트

### Week 2 완료 ✅
- [x] Graph Service 클라이언트 구현
- [x] ML Service 상태 조회 구현
- [x] DataLoader 패턴 적용
- [x] 에러 처리 표준화
- [x] 단위/통합 테스트 구현 (38개 테스트 통과)

### Week 3 예정 🚧
- [ ] WebSocket 실시간 업데이트
- [ ] Rate Limiting 고도화
- [ ] 성능 모니터링
- [ ] API 문서 자동 생성

## 🔧 주요 컴포넌트

### 1. GraphQL Schema
```graphql
# 통합 스키마
type Query {
  # 기업 정보
  company(id: ID!): Company
  companies(
    limit: Int = 10
    offset: Int = 0
    filter: CompanyFilter
  ): CompanyConnection!
  
  # 리스크 분석
  riskAnalysis(companyId: ID!): RiskAnalysis!
  riskEvents(
    filter: RiskEventFilter
    sort: RiskEventSort
  ): [RiskEvent!]!
  
  # 사용자 대시보드
  dashboard: Dashboard!
  insights(companyId: ID!): [Insight!]!
}

type Mutation {
  # 사용자 관리
  login(email: String!, password: String!): AuthPayload!
  refreshToken(token: String!): AuthPayload!
  
  # 설정
  updatePreferences(input: PreferencesInput!): User!
  subscribeToAlerts(companyIds: [ID!]!): Subscription!
}

type Subscription {
  # 실시간 업데이트
  riskAlert(companyIds: [ID!]!): RiskAlert!
  newsUpdate(filters: NewsFilter): NewsUpdate!
}
```

### 2. Apollo Server Setup
```typescript
import { ApolloServer } from '@apollo/server';
import { expressMiddleware } from '@apollo/server/express4';
import { buildSubgraphSchema } from '@apollo/federation';

const server = new ApolloServer({
  schema: buildSubgraphSchema({
    typeDefs,
    resolvers,
  }),
  plugins: [
    ApolloServerPluginDrainHttpServer({ httpServer }),
    ApolloServerPluginLandingPageLocalDefault(),
  ],
  context: async ({ req }) => {
    // 인증 정보 추출
    const token = req.headers.authorization?.replace('Bearer ', '');
    const user = token ? await verifyToken(token) : null;
    
    // DataLoader 생성
    const loaders = {
      company: createCompanyLoader(),
      risk: createRiskLoader(),
    };
    
    return { user, loaders, services };
  },
});
```

### 3. Service Clients
```typescript
// Graph Service 클라이언트 (src/services/graph.client.ts)
export class GraphServiceClient {
  private client: GraphQLClient;
  
  async getCompany(id: string): Promise<Company | null>
  async getCompanies(filter?, limit?, offset?): Promise<Company[]>
  async getCompaniesByIds(ids: string[]): Promise<Company[]>
  async getNetworkRisk(companyId: string): Promise<NetworkRisk | null>
  async getConnectedCompanies(companyId: string, depth?): Promise<Company[]>
  async searchCompanies(query: string, limit?): Promise<Company[]>
  async addCompany(companyData): Promise<Company | null>
  async updateCompany(id: string, updates): Promise<Company | null>
}

// ML Service 클라이언트 (src/services/ml.client.ts)
export class MLServiceClient {
  async getStatus(): Promise<MLServiceStatus | null>
  async analyzeNews(newsData): Promise<NewsAnalysisResult | null>
  async batchAnalyzeNews(newsItems): Promise<NewsAnalysisResult[]>
  async predictRisk(companyId: string): Promise<RiskPrediction[]>
  async getSentimentTrends(companyId: string): Promise<any[]>
  async getRiskInsights(companyId: string): Promise<any[]>
  async getModelMetrics(): Promise<any>
}
```

### 4. Authentication
```typescript
// JWT 미들웨어
export const authMiddleware = async (
  req: Request,
  res: Response,
  next: NextFunction
) => {
  try {
    const token = req.headers.authorization?.replace('Bearer ', '');
    
    if (!token) {
      return next();
    }
    
    const payload = await verifyJWT(token);
    req.user = await getUserById(payload.userId);
    
    next();
  } catch (error) {
    next(error);
  }
};

// GraphQL 디렉티브
@Directive('@auth(requires: Role = USER)')
class AuthDirective extends SchemaDirectiveVisitor {
  visitFieldDefinition(field: GraphQLField<any, any>) {
    const { resolve = defaultFieldResolver } = field;
    
    field.resolve = async function (...args) {
      const [, , context] = args;
      
      if (!context.user) {
        throw new ForbiddenError('Authentication required');
      }
      
      const requiredRole = this.args.requires;
      if (!hasRole(context.user, requiredRole)) {
        throw new ForbiddenError('Insufficient permissions');
      }
      
      return resolve.apply(this, args);
    };
  }
}
```

### 5. DataLoader 패턴 (src/graphql/dataloaders/index.ts)
```typescript
// N+1 쿼리 문제 해결을 위한 배치 로딩
export const createCompanyLoader = () => {
  return new DataLoader<string, any>(async (ids) => {
    const companies = await graphServiceClient.getCompaniesByIds([...ids]);
    const companyMap = new Map(companies.map(c => [c.id, c]));
    return ids.map(id => companyMap.get(id) || null);
  }, { cache: true, maxBatchSize: 100 });
};

// 사용 가능한 모든 DataLoader
export const createLoaders = () => ({
  company: createCompanyLoader(),
  connectedCompanies: createConnectedCompaniesLoader(),
  networkRisk: createNetworkRiskLoader(),
  riskPredictions: createRiskPredictionsLoader(),
  sentimentTrends: createSentimentTrendsLoader(),
  riskInsights: createRiskInsightsLoader(),
});

// Context에서 활용
context: {
  user: req.user,
  loaders: createLoaders(), // 매 요청마다 새 인스턴스
  services: { graph: graphServiceClient, ml: mlServiceClient }
}
```

## 📝 코딩 규칙

### 1. GraphQL Best Practices
- Schema-first 개발
- 명확한 타입 정의
- Nullable vs Non-nullable 신중히 결정
- Pagination 표준 준수 (Relay Connection)

### 2. Error Handling (src/utils/errors.ts)
```typescript
// 표준화된 에러 처리
export enum ErrorCode {
  UNAUTHENTICATED = 'UNAUTHENTICATED',
  FORBIDDEN = 'FORBIDDEN',
  INVALID_INPUT = 'INVALID_INPUT',
  NOT_FOUND = 'NOT_FOUND',
  SERVICE_UNAVAILABLE = 'SERVICE_UNAVAILABLE',
  RATE_LIMIT_EXCEEDED = 'RATE_LIMIT_EXCEEDED',
  INTERNAL_ERROR = 'INTERNAL_ERROR',
}

export class CustomError extends GraphQLError {
  constructor(message: string, code: ErrorCode, extensions?: Record<string, any>) {
    super(message, {
      extensions: { code, timestamp: new Date().toISOString(), ...extensions }
    });
  }
}

// 특화된 에러 클래스들
export class AuthenticationError extends CustomError
export class ForbiddenError extends CustomError
export class ValidationError extends CustomError
export class NotFoundError extends CustomError
export class ServiceUnavailableError extends CustomError

// 유틸리티 함수들
export const throwIfNotFound = <T>(item: T | null, resource: string): T
export const throwIfNotAuthenticated = (user: any): void
export const withRetry = async <T>(operation: () => Promise<T>): Promise<T>
```

### 3. Rate Limiting
```typescript
import rateLimit from 'express-rate-limit';
import RedisStore from 'rate-limit-redis';

const limiter = rateLimit({
  store: new RedisStore({
    client: redis,
    prefix: 'rl:',
  }),
  windowMs: 15 * 60 * 1000, // 15분
  max: 100, // 최대 요청 수
  message: 'Too many requests',
});

// GraphQL 복잡도 제한
const depthLimit = require('graphql-depth-limit');
const costAnalysis = require('graphql-cost-analysis');

const server = new ApolloServer({
  validationRules: [
    depthLimit(5),
    costAnalysis({
      maximumCost: 1000,
      defaultCost: 1,
      scalarCost: 1,
      objectCost: 2,
      listFactor: 10,
    }),
  ],
});
```

### 4. Logging
```typescript
import winston from 'winston';

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.Console({
      format: winston.format.simple(),
    }),
  ],
});

// GraphQL 플러그인
const loggingPlugin = {
  async requestDidStart() {
    return {
      async willSendResponse(requestContext) {
        logger.info('GraphQL Response', {
          query: requestContext.request.query,
          variables: requestContext.request.variables,
          duration: Date.now() - requestContext.startTime,
        });
      },
    };
  },
};
```

## 🧪 테스트

### 현재 테스트 현황
- **총 38개 테스트 ✅ 모두 통과**
- **단위 테스트**: 13개 (Company Resolver)
- **통합 테스트**: 25개 (Graph Service Client)

### 테스트 실행
```bash
# 전체 테스트 실행
npm test

# 단위 테스트만
npm run test:unit

# 통합 테스트만  
npm run test:integration

# 커버리지 포함
npm run test:coverage
```

### 테스트 구조
```
tests/
├── unit/
│   └── resolvers/
│       └── company.test.ts     # GraphQL 리졸버 테스트
└── integration/
    └── services/
        └── graph.client.test.ts # 서비스 클라이언트 테스트
```

### 주요 테스트 케이스
- DataLoader 기반 배치 쿼리
- 필터링/정렬/페이지네이션
- 에러 처리 및 복구
- 서비스 가용성 확인
- GraphQL 스키마 검증

## 🚀 배포

### Docker 빌드
```bash
docker build -t riskradar/api-gateway:latest .
```

### Multi-stage Dockerfile
프로덕션용 Docker 이미지는 multi-stage 빌드를 사용하여 최적화되어 있습니다:
- **빌드 스테이지**: TypeScript 컴파일 및 GraphQL 스키마 복사
- **프로덕션 스테이지**: 최소 런타임 환경 (node:18-alpine)
- **빌드 최적화**: .dockerignore를 통한 불필요한 파일 제외

### 환경 변수
```env
# Server
PORT=8004
NODE_ENV=production

# Services
GRAPH_SERVICE_URL=http://graph-service:8003
ML_SERVICE_URL=http://ml-service:8002
DATA_SERVICE_URL=http://data-service:8001

# Auth
JWT_SECRET=your-secret-key
JWT_EXPIRES_IN=7d

# Redis
REDIS_URL=redis://redis:6379

# Monitoring
APOLLO_KEY=service:api-gateway:xxxxx
```

## 📊 모니터링

### Health Check
```typescript
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    services: {
      graph: checkGraphService(),
      ml: checkMLService(),
      redis: checkRedis(),
    },
  });
});
```

### Metrics
- Request rate
- Response time (P50, P95, P99)
- Error rate
- Active connections

### Apollo Studio
- Schema 변경 추적
- 성능 모니터링
- 사용 패턴 분석

## 🔒 보안

### Authentication
- JWT 기반 인증
- Refresh token rotation
- Session management

### Authorization
- Role-based access control
- Field-level permissions
- Resource-based authorization

### Security Headers
```typescript
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
    },
  },
}));
```

## 🤝 협업

### API 문서
- GraphQL Playground: `/graphql`
- Schema 파일: `schema.graphql`
- Postman Collection: `docs/postman.json`

### 버전 관리
- Semantic versioning
- Breaking change policy
- Deprecation warnings

## 🐛 트러블슈팅

### 일반적인 문제

#### 1. N+1 쿼리 문제
```typescript
// DataLoader 사용
const resolver = {
  Company: {
    // Bad
    risks: (company) => getRisksByCompanyId(company.id),
    
    // Good
    risks: (company, _, { loaders }) => 
      loaders.risks.load(company.id),
  },
};
```

#### 2. 메모리 누수
- DataLoader 인스턴스 재사용 금지
- Context별로 새 인스턴스 생성
- Subscription 정리

#### 3. 타임아웃
```typescript
// 타임아웃 설정
const server = new ApolloServer({
  stopGracePeriodMillis: 60000,
  apollo: {
    requestTimeout: 30000,
  },
});
```

#### 4. Docker 빌드 문제
- **`index.js` 파일 없음**: TypeScript 빌드 확인 (`npm run build`)
- **GraphQL 스키마 없음**: Dockerfile에서 스키마 복사 확인
- **포트 불일치**: 환경 변수 PORT와 설정 일치 확인 (기본값: 8004)

## 📚 참고 자료

- [Apollo Server Documentation](https://www.apollographql.com/docs/apollo-server/)
- [GraphQL Best Practices](https://graphql.org/learn/best-practices/)
- [DataLoader Pattern](https://github.com/graphql/dataloader)
- [GraphQL Security](https://www.howtographql.com/advanced/4-security/)

## 🎯 Sprint 개발 가이드

현재 Sprint의 상세 요구사항은 다음 문서를 참고하세요:
- [Sprint 1 Requirements](./Sprint1_Requirements.md) - Week별 구현 목표
- [Sprint Breakdown](../../docs/trd/phase1/Sprint_Breakdown.md) - 전체 Sprint 계획

### 개발 우선순위
1. GraphQL 스키마 정의
2. JWT 인증 구현
3. 서비스 통합 레이어

## 📁 프로젝트 문서

### 핵심 문서
- [Platform Squad TRD](../../docs/trd/phase1/TRD_Platform_Squad_P1.md) - 기술 명세
- [API 표준](../../docs/trd/common/API_Standards.md) - API 설계
- [통합 포인트](../../docs/trd/common/Integration_Points.md) - 서비스 연동

### 연관 서비스
- [Graph Service](../graph-service/CLAUDE.md) - GraphQL 리졸버 데이터
- [Web UI](../web-ui/CLAUDE.md) - GraphQL 클라이언트
- [통합 가이드](../../integration/README.md) - 시스템 통합

---

## 📝 최근 업데이트

### 2025-07-19 - 통합 테스트 수정
- ✅ Multi-stage Docker 빌드 구현
- ✅ TypeScript 빌드 프로세스 개선
- ✅ 포트 설정 일관성 확보 (4000 → 8004)
- ✅ .dockerignore 파일 추가로 빌드 최적화

### 2024-07-19 - Sprint 1 Week 2 완료 🎉
- ✅ Graph Service 클라이언트 구현 완료
- ✅ ML Service 상태 조회 통합 완료
- ✅ DataLoader 패턴 적용 완료
- ✅ 에러 처리 표준화 완료
- ✅ 단위/통합 테스트 코드 작성 완료 (38개 테스트)

### 2024-07-19 - Sprint 1 Week 1 완료
- ✅ Apollo Server 4 기반 GraphQL API Gateway 구현 완료
- ✅ TypeScript + Jest 개발 환경 구축
- ✅ 포괄적인 GraphQL 스키마 및 Mock Resolver 구현
- ✅ JWT 인증 미들웨어 기반 구조 준비
- ✅ Health check 및 보안 설정 완료

### Next Steps (Week 3)
- [ ] WebSocket 실시간 업데이트
- [ ] Rate Limiting 고도화
- [ ] 성능 모니터링
- [ ] API 문서 자동 생성

*최종 업데이트: 2025-07-19*