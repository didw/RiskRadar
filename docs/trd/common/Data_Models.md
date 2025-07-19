# Data Models
# RiskRadar 공통 데이터 모델

## 1. 핵심 엔티티

### 1.1 Company (기업)
```typescript
interface Company {
  // 식별자
  companyId: string;          // "KR-{사업자번호}"
  businessNumber?: string;    // 사업자등록번호
  
  // 기본 정보
  name: string;               // 한글명
  nameEn?: string;            // 영문명
  aliases: string[];          // 별칭/약칭
  
  // 분류
  sector: string;             // 대분류 (IT/전자, 금융 등)
  subSector?: string;         // 소분류
  industry?: string;          // 산업 코드
  
  // 재무 정보
  marketCap?: number;         // 시가총액
  revenue?: number;           // 매출액
  profit?: number;            // 영업이익
  employees?: number;         // 직원수
  
  // 리스크 정보
  riskScore: number;          // 0-10
  riskTrend: RiskTrend;       // INCREASING | STABLE | DECREASING
  riskFactors: RiskFactor[];  // 리스크 요인들
  
  // 관계 정보
  ceoId?: string;             // Person ID
  parentCompanyId?: string;   // 모회사 ID
  
  // 메타데이터
  foundedYear?: number;       // 설립연도
  stockCode?: string;         // 종목코드
  website?: string;           // 웹사이트
  description?: string;       // 회사 설명
  
  // 시스템 정보
  createdAt: Date;
  updatedAt: Date;
  lastCrawledAt?: Date;
  dataSource: string;         // DART | MANUAL | CRAWLED
  confidence: number;         // 0-1
}
```

### 1.2 Person (인물)
```typescript
interface Person {
  // 식별자
  personId: string;           // "KR-P-{UUID}"
  
  // 기본 정보
  name: string;               // 한글명
  nameEn?: string;            // 영문명
  birthYear?: number;         // 출생연도
  nationality?: string;       // 국적
  
  // 직책 정보
  currentRole?: string;       // 현재 직책
  currentCompanyId?: string;  // 현재 회사
  previousRoles: Role[];      // 이전 경력
  
  // 학력
  education: Education[];
  
  // 영향력
  influenceScore: number;     // 0-10
  connections: number;        // 연결 수
  publicProfile: boolean;     // 공인 여부
  
  // 리스크
  riskExposure: number;       // 0-10
  sanctions?: Sanction[];     // 제재 정보
  
  // 시스템 정보
  createdAt: Date;
  updatedAt: Date;
  verified: boolean;
}

interface Role {
  companyId: string;
  companyName: string;
  position: string;
  startDate?: Date;
  endDate?: Date;
  isCurrent: boolean;
}
```

### 1.3 Event (이벤트)
```typescript
interface Event {
  // 식별자
  eventId: string;            // "EVT-{YYYY}-{UUID}"
  
  // 분류
  type: EventType;            // LEGAL | FINANCIAL | OPERATIONAL | REGULATORY
  subType?: string;           // 세부 유형
  category?: string;          // 카테고리
  
  // 내용
  title: string;              // 제목
  description: string;        // 설명
  summary?: string;           // 요약
  
  // 시간 정보
  eventDate: Date;            // 발생일
  reportedDate: Date;         // 보도일
  endDate?: Date;             // 종료일 (지속적 이벤트)
  
  // 영향도
  severity: number;           // 1-10
  probability?: number;       // 0-1 (예측 이벤트)
  impact: ImpactLevel;        // LOW | MEDIUM | HIGH | CRITICAL
  urgency: UrgencyLevel;      // LOW | MEDIUM | HIGH | IMMEDIATE
  
  // 관련 정보
  affectedCompanyIds: string[];
  relatedPersonIds: string[];
  relatedCountries: string[];
  relatedRiskIds: string[];
  
  // 출처
  sources: Source[];
  
  // 시스템 정보
  createdAt: Date;
  updatedAt: Date;
  verificationStatus: VerificationStatus;
}
```

### 1.4 Risk (리스크)
```typescript
interface Risk {
  // 식별자
  riskId: string;             // "RISK-{TYPE}-{UUID}"
  
  // 분류
  category: RiskCategory;     // MARKET | CREDIT | OPERATIONAL | REGULATORY
  type: string;               // 세부 유형
  
  // 평가
  level: number;              // 1-5
  probability: number;        // 0-1
  impact: number;             // 예상 영향 (금액)
  trend: RiskTrend;           // INCREASING | STABLE | DECREASING
  
  // 설명
  description: string;
  indicators: string[];       // 리스크 지표들
  
  // 대응
  mitigationCost?: number;    // 완화 비용
  mitigationStrategies: string[];
  
  // 관련 정보
  affectedSectors: string[];
  affectedRegions: string[];
  
  // 시스템 정보
  createdAt: Date;
  updatedAt: Date;
  lastAssessedAt: Date;
}
```

### 1.5 News (뉴스)
```typescript
interface News {
  // 식별자
  newsId: string;             // "NEWS-{SOURCE}-{UUID}"
  
  // 내용
  title: string;              // 제목
  content: string;            // 본문
  summary?: string;           // AI 요약
  
  // 출처
  source: NewsSource;         // 언론사 정보
  author?: string;            // 기자
  url: string;                // 원문 링크
  
  // 시간
  publishedAt: Date;          // 발행일
  crawledAt: Date;            // 수집일
  
  // 분석 결과
  sentiment: number;          // -1 to 1
  relevance: number;          // 0-1
  reliability: number;        // 0-1
  
  // 추출 정보
  mentionedCompanies: EntityMention[];
  mentionedPeople: EntityMention[];
  identifiedRisks: string[];
  keywords: Keyword[];
  
  // 분류
  category: string;           // 경제, 정치, 사회 등
  tags: string[];
  
  // 시스템 정보
  createdAt: Date;
  processedAt?: Date;
  language: string;           // ko | en
}

interface EntityMention {
  entityId: string;
  entityName: string;
  sentiment: number;          // -1 to 1
  relevance: number;          // 0-1
  context: string;            // 주변 문맥
}
```

## 2. 관계 모델

### 2.1 Company Relations
```typescript
interface CompanyRelation {
  fromCompanyId: string;
  toCompanyId: string;
  relationType: CompanyRelationType;
  properties: Record<string, any>;
  since?: Date;
  until?: Date;
  isActive: boolean;
}

enum CompanyRelationType {
  COMPETES_WITH = "COMPETES_WITH",
  PARTNERS_WITH = "PARTNERS_WITH",
  SUBSIDIARY_OF = "SUBSIDIARY_OF",
  SUPPLIES_TO = "SUPPLIES_TO",
  CUSTOMER_OF = "CUSTOMER_OF",
  INVESTS_IN = "INVESTS_IN"
}

// 관계별 속성
interface CompetesWithProps {
  intensity: number;          // 0-1
  market: string;            // 경쟁 시장
  marketShareOverlap: number; // 0-1
}

interface PartnersWithProps {
  type: PartnershipType;     // SUPPLIER | DISTRIBUTOR | TECHNOLOGY
  contractValue?: number;
  dependency: number;        // 0-1
}
```

### 2.2 Person Relations
```typescript
interface PersonRelation {
  fromPersonId: string;
  toPersonId: string;
  relationType: PersonRelationType;
  properties: Record<string, any>;
  since?: Date;
}

enum PersonRelationType {
  KNOWS = "KNOWS",
  WORKED_WITH = "WORKED_WITH",
  STUDIED_WITH = "STUDIED_WITH",
  RELATED_TO = "RELATED_TO"
}
```

## 3. 시계열 데이터

### 3.1 Risk Score History
```typescript
interface RiskScoreHistory {
  entityId: string;           // Company or Person ID
  entityType: EntityType;
  timestamp: Date;
  riskScore: number;
  factors: RiskFactor[];
  calculationMethod: string;
}

interface RiskFactor {
  factorType: string;
  weight: number;
  value: number;
  description: string;
}
```

### 3.2 Market Data
```typescript
interface MarketData {
  companyId: string;
  date: Date;
  openPrice: number;
  closePrice: number;
  highPrice: number;
  lowPrice: number;
  volume: number;
  marketCap: number;
}
```

## 4. 사용자 데이터

### 4.1 User
```typescript
interface User {
  userId: string;
  email: string;
  name: string;
  companyId: string;          // 소속 회사
  role: UserRole;
  permissions: Permission[];
  preferences: UserPreferences;
  createdAt: Date;
  lastLoginAt: Date;
}

interface UserPreferences {
  language: string;           // ko | en
  timezone: string;
  dashboardLayout: any;       // 커스텀 레이아웃
  emailNotifications: boolean;
  pushNotifications: boolean;
  riskThresholds: {
    high: number;
    medium: number;
    low: number;
  };
}
```

### 4.2 Watchlist
```typescript
interface Watchlist {
  watchlistId: string;
  userId: string;
  name: string;
  companies: WatchlistItem[];
  createdAt: Date;
  updatedAt: Date;
}

interface WatchlistItem {
  companyId: string;
  addedAt: Date;
  notes?: string;
  alertSettings: AlertSettings;
}
```

## 5. 공통 타입

### 5.1 Enums
```typescript
enum RiskTrend {
  INCREASING = "INCREASING",
  STABLE = "STABLE",
  DECREASING = "DECREASING"
}

enum ImpactLevel {
  LOW = "LOW",
  MEDIUM = "MEDIUM",
  HIGH = "HIGH",
  CRITICAL = "CRITICAL"
}

enum EntityType {
  COMPANY = "COMPANY",
  PERSON = "PERSON",
  EVENT = "EVENT",
  RISK = "RISK"
}

enum DataSource {
  DART = "DART",
  NEWS = "NEWS",
  MANUAL = "MANUAL",
  API = "API",
  CRAWLED = "CRAWLED"
}
```

### 5.2 Value Objects
```typescript
interface Address {
  street?: string;
  city?: string;
  state?: string;
  country: string;
  postalCode?: string;
}

interface ContactInfo {
  phone?: string;
  email?: string;
  fax?: string;
}

interface Source {
  name: string;
  url?: string;
  credibility: number;        // 0-1
  type: SourceType;
}

interface Keyword {
  word: string;
  score: number;              // 0-1
  type?: KeywordType;         // TOPIC | RISK | ENTITY
}
```

## 6. 데이터 검증 규칙

### 6.1 ID 형식
- Company: `KR-{10자리 사업자번호}`
- Person: `KR-P-{UUID}`
- Event: `EVT-{YYYY}-{UUID}`
- Risk: `RISK-{CATEGORY}-{UUID}`

### 6.2 필수 필드
- 모든 엔티티: `id`, `createdAt`, `updatedAt`
- Company: `name`, `sector`, `riskScore`
- Person: `name`, `influenceScore`
- Event: `title`, `type`, `eventDate`, `severity`

### 6.3 값 범위
- Score 필드: 0-10
- Probability 필드: 0-1
- Sentiment: -1 to 1
- Severity: 1-10

## 7. 데이터 라이프사이클

### 7.1 생성
1. 데이터 수집/입력
2. 검증 및 정규화
3. 중복 체크
4. ID 생성
5. 저장

### 7.2 업데이트
1. 변경 감지
2. 검증
3. 버전 관리
4. 이력 저장
5. 캐시 무효화

### 7.3 삭제
- Soft delete 정책
- `deletedAt` 필드 사용
- 관련 데이터 처리
- 감사 로그 유지