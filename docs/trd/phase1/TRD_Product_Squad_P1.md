# Technical Requirements Document
# Product Squad - Phase 1

## 1. 개요

### 1.1 문서 정보
- **Squad**: Product Squad
- **Phase**: 1 (Week 1-4)
- **작성일**: 2024-07-19
- **버전**: 1.0

### 1.2 범위
API Gateway 구축, GraphQL 스키마 설계, 기본 웹 대시보드 UI 구현

### 1.3 관련 문서
- PRD: [PRD.md](../../prd/PRD.md)
- Tech Architecture: [PRD_Tech_Architecture.md](../../prd/PRD_Tech_Architecture.md)
- 의존 TRD: 모든 Squad (API 통합)

## 2. 기술 요구사항

### 2.1 기능 요구사항
| ID | 기능명 | 설명 | 우선순위 | PRD 참조 |
|----|--------|------|----------|----------|
| F001 | API Gateway | Kong 기반 라우팅 및 인증 | P0 | FR-004 |
| F002 | GraphQL API | 통합 쿼리 인터페이스 | P0 | FR-004 |
| F003 | 인증/인가 | JWT 기반 사용자 인증 | P0 | FR-004 |
| F004 | 기본 대시보드 | 리스크 현황 UI | P0 | FR-004 |
| F005 | 반응형 디자인 | 모바일/태블릿 지원 | P1 | FR-004 |

### 2.2 비기능 요구사항
| 항목 | 요구사항 | 측정 방법 |
|------|----------|-----------|
| 응답시간 | API < 100ms, 페이지 < 3s | Performance 모니터링 |
| 동시사용자 | 100명 동시 접속 | 부하 테스트 |
| 브라우저 지원 | Chrome, Safari, Edge | Cross-browser 테스트 |
| 접근성 | WCAG 2.1 AA | Lighthouse 감사 |

## 3. 시스템 아키텍처

### 3.1 Frontend 아키텍처
```
┌─────────────────────────────────────────────────┐
│                   Client Layer                   │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────┐│
│  │   Desktop   │  │   Mobile    │  │  Tablet ││
│  │   Browser   │  │   Browser   │  │ Browser ││
│  └──────┬──────┘  └──────┬──────┘  └────┬────┘│
│         └─────────────────┼───────────────┘     │
└───────────────────────────┼─────────────────────┘
                           │
                    ┌──────▼──────┐
                    │    CDN      │
                    │(CloudFront) │
                    └──────┬──────┘
                           │
                ┌──────────▼───────────┐
                │   Next.js App        │
                │  (SSR/SSG/ISR)       │
                ├──────────────────────┤
                │ ┌──────────────────┐ │
                │ │     Pages        │ │
                │ │  ┌────┐  ┌────┐ │ │
                │ │  │Home│  │Risk│ │ │
                │ │  └────┘  └────┘ │ │
                │ └──────────────────┘ │
                │ ┌──────────────────┐ │
                │ │   Components     │ │
                │ │  ┌─────┐ ┌────┐ │ │
                │ │  │Chart│ │Map │ │ │
                │ │  └─────┘ └────┘ │ │
                │ └──────────────────┘ │
                │ ┌──────────────────┐ │
                │ │  State (Zustand) │ │
                │ └──────────────────┘ │
                └──────────┬───────────┘
                           │
                    ┌──────▼──────┐
                    │  API Gateway │
                    │    (Kong)    │
                    └──────┬──────┘
                           │
                ┌──────────▼───────────┐
                │    GraphQL Server    │
                │     (Strawberry)     │
                └──────────────────────┘
```

### 3.2 API Gateway 구조
```
┌────────────────────────────────────────────────┐
│                Kong API Gateway                 │
├────────────────────────────────────────────────┤
│                                                │
│  ┌──────────────┐  ┌──────────────┐          │
│  │   Plugins    │  │   Routes     │          │
│  ├──────────────┤  ├──────────────┤          │
│  │ • JWT Auth   │  │ /api/v1/*    │          │
│  │ • Rate Limit │  │ /graphql     │          │
│  │ • CORS       │  │ /health      │          │
│  │ • Logging    │  │ /metrics     │          │
│  │ • Transform  │  └──────┬───────┘          │
│  └──────────────┘         │                  │
│                           │                  │
│  ┌────────────────────────▼─────────────────┐ │
│  │            Upstream Services             │ │
│  ├──────────────────────────────────────────┤ │
│  │                                          │ │
│  │  ┌──────────┐  ┌──────────┐  ┌────────┐│ │
│  │  │  Graph   │  │   Data   │  │  ML    ││ │
│  │  │  Service │  │  Service │  │Service ││ │
│  │  └──────────┘  └──────────┘  └────────┘│ │
│  └──────────────────────────────────────────┘ │
└────────────────────────────────────────────────┘
```

## 4. 상세 설계

### 4.1 GraphQL 스키마

#### 4.1.1 주요 타입 정의
```graphql
type Company {
  companyId: ID!
  name: String!
  nameEn: String
  sector: String!
  marketCap: Float
  riskScore: Float!
  riskTrend: RiskTrend!
  ceo: Person
  competitors(limit: Int = 5): [Company!]!
  risks(
    category: RiskCategory
    minLevel: Int
  ): [Risk!]!
  events(
    dateFrom: DateTime
    dateTo: DateTime
    limit: Int = 10
  ): [Event!]!
  news(limit: Int = 5): [News!]!
}

type Person {
  personId: ID!
  name: String!
  role: String!
  company: Company
  influenceScore: Float!
  connections(limit: Int = 10): [Person!]!
}

type Event {
  eventId: ID!
  type: EventType!
  title: String!
  date: DateTime!
  severity: Int!
  affectedCompanies: [Company!]!
  relatedRisks: [Risk!]!
}

type Risk {
  riskId: ID!
  category: RiskCategory!
  level: Int!
  probability: Float!
  trend: RiskTrend!
  exposedCompanies(limit: Int = 10): [Company!]!
}

enum RiskCategory {
  MARKET
  CREDIT
  OPERATIONAL
  REGULATORY
  REPUTATIONAL
}

enum RiskTrend {
  INCREASING
  STABLE
  DECREASING
}

# 쿼리 정의
type Query {
  # 회사 조회
  company(companyId: ID!): Company
  companies(
    sector: String
    minMarketCap: Float
    limit: Int = 20
    offset: Int = 0
  ): [Company!]!
  
  # 리스크 분석
  riskPropagation(
    sourceCompanyId: ID!
    maxDepth: Int = 3
    minImpact: Float = 0.1
  ): RiskPropagationResult!
  
  # 대시보드 데이터
  dashboardSummary(userId: ID!): DashboardSummary!
  
  # 검색
  search(
    query: String!
    types: [SearchType!]
    limit: Int = 20
  ): SearchResult!
}

# 뮤테이션 정의
type Mutation {
  # 사용자 설정
  updateUserPreferences(
    input: UserPreferencesInput!
  ): User!
  
  # 관심 기업 관리
  addWatchlistCompany(
    companyId: ID!
  ): Watchlist!
  
  removeWatchlistCompany(
    companyId: ID!
  ): Watchlist!
}

# 구독 정의
type Subscription {
  # 실시간 리스크 알림
  riskAlerts(
    userId: ID!
    minSeverity: Int = 5
  ): RiskAlert!
  
  # 뉴스 피드
  newsFeed(
    companyIds: [ID!]!
  ): News!
}
```

#### 4.1.2 GraphQL Resolver 구현
```python
import strawberry
from typing import List, Optional
from datetime import datetime

@strawberry.type
class Company:
    company_id: str
    name: str
    risk_score: float
    
    @strawberry.field
    async def competitors(self, limit: int = 5) -> List["Company"]:
        # Neo4j 쿼리
        query = """
        MATCH (c:Company {companyId: $id})-[:COMPETES_WITH]-(comp:Company)
        RETURN comp
        ORDER BY comp.marketCap DESC
        LIMIT $limit
        """
        return await graph_service.query(query, id=self.company_id, limit=limit)
    
    @strawberry.field
    async def risks(
        self, 
        category: Optional[str] = None,
        min_level: Optional[int] = None
    ) -> List["Risk"]:
        filters = []
        if category:
            filters.append(f"r.category = '{category}'")
        if min_level:
            filters.append(f"r.level >= {min_level}")
        
        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
        
        query = f"""
        MATCH (c:Company {{companyId: $id}})-[:EXPOSED_TO]->(r:Risk)
        {where_clause}
        RETURN r
        ORDER BY r.level DESC
        """
        return await graph_service.query(query, id=self.company_id)

@strawberry.type
class Query:
    @strawberry.field
    async def company(self, company_id: str) -> Optional[Company]:
        return await company_service.get_by_id(company_id)
    
    @strawberry.field
    async def risk_propagation(
        self,
        source_company_id: str,
        max_depth: int = 3,
        min_impact: float = 0.1
    ) -> "RiskPropagationResult":
        return await risk_analysis_service.calculate_propagation(
            source_company_id,
            max_depth,
            min_impact
        )

schema = strawberry.Schema(query=Query, mutation=Mutation, subscription=Subscription)
```

### 4.2 Frontend 컴포넌트

#### 4.2.1 대시보드 레이아웃
```tsx
// app/dashboard/page.tsx
import { Suspense } from 'react';
import { DashboardLayout } from '@/components/layouts/DashboardLayout';
import { RiskSummaryCard } from '@/components/cards/RiskSummaryCard';
import { RiskMapViewer } from '@/components/visualization/RiskMapViewer';
import { NewsTimeline } from '@/components/timeline/NewsTimeline';
import { CompanyWatchlist } from '@/components/watchlist/CompanyWatchlist';

export default async function DashboardPage() {
  return (
    <DashboardLayout>
      <div className="grid grid-cols-12 gap-6">
        {/* 리스크 요약 카드 */}
        <div className="col-span-12 md:col-span-4">
          <Suspense fallback={<RiskSummaryCard.Skeleton />}>
            <RiskSummaryCard />
          </Suspense>
        </div>
        
        {/* 3D 리스크 맵 */}
        <div className="col-span-12 md:col-span-8">
          <Suspense fallback={<RiskMapViewer.Skeleton />}>
            <RiskMapViewer />
          </Suspense>
        </div>
        
        {/* 뉴스 타임라인 */}
        <div className="col-span-12 lg:col-span-8">
          <Suspense fallback={<NewsTimeline.Skeleton />}>
            <NewsTimeline />
          </Suspense>
        </div>
        
        {/* 관심 기업 목록 */}
        <div className="col-span-12 lg:col-span-4">
          <Suspense fallback={<CompanyWatchlist.Skeleton />}>
            <CompanyWatchlist />
          </Suspense>
        </div>
      </div>
    </DashboardLayout>
  );
}
```

#### 4.2.2 3D Risk Map 컴포넌트
```tsx
// components/visualization/RiskMapViewer.tsx
'use client';

import { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';
import { useRiskMapData } from '@/hooks/useRiskMapData';

export function RiskMapViewer() {
  const containerRef = useRef<HTMLDivElement>(null);
  const { data, loading } = useRiskMapData();
  
  useEffect(() => {
    if (!containerRef.current || loading || !data) return;
    
    // Three.js 씬 설정
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(
      75,
      containerRef.current.clientWidth / containerRef.current.clientHeight,
      0.1,
      1000
    );
    
    const renderer = new THREE.WebGLRenderer({ 
      antialias: true,
      alpha: true 
    });
    renderer.setSize(
      containerRef.current.clientWidth,
      containerRef.current.clientHeight
    );
    containerRef.current.appendChild(renderer.domElement);
    
    // 컨트롤 추가
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    
    // 회사 노드 생성
    data.companies.forEach((company) => {
      const geometry = new THREE.SphereGeometry(
        Math.log(company.marketCap) / 10,
        32,
        32
      );
      
      const material = new THREE.MeshPhongMaterial({
        color: getRiskColor(company.riskScore),
        emissive: getRiskColor(company.riskScore),
        emissiveIntensity: 0.2
      });
      
      const sphere = new THREE.Mesh(geometry, material);
      sphere.position.set(
        company.position.x,
        company.position.y,
        company.position.z
      );
      
      sphere.userData = { company };
      scene.add(sphere);
    });
    
    // 관계 라인 생성
    data.relationships.forEach((rel) => {
      const points = [
        new THREE.Vector3(rel.from.x, rel.from.y, rel.from.z),
        new THREE.Vector3(rel.to.x, rel.to.y, rel.to.z)
      ];
      
      const geometry = new THREE.BufferGeometry().setFromPoints(points);
      const material = new THREE.LineBasicMaterial({
        color: 0x666666,
        opacity: rel.strength,
        transparent: true
      });
      
      const line = new THREE.Line(geometry, material);
      scene.add(line);
    });
    
    // 조명 추가
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);
    
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.4);
    directionalLight.position.set(10, 10, 10);
    scene.add(directionalLight);
    
    // 카메라 위치
    camera.position.z = 50;
    
    // 애니메이션 루프
    function animate() {
      requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    }
    animate();
    
    // 리사이즈 핸들러
    const handleResize = () => {
      if (!containerRef.current) return;
      
      camera.aspect = containerRef.current.clientWidth / containerRef.current.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(
        containerRef.current.clientWidth,
        containerRef.current.clientHeight
      );
    };
    
    window.addEventListener('resize', handleResize);
    
    return () => {
      window.removeEventListener('resize', handleResize);
      renderer.dispose();
    };
  }, [data, loading]);
  
  return (
    <div className="relative w-full h-[600px] bg-gray-900 rounded-lg">
      <div ref={containerRef} className="w-full h-full" />
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-white">Loading risk map...</div>
        </div>
      )}
    </div>
  );
}

function getRiskColor(riskScore: number): number {
  // 리스크 점수에 따른 색상 반환
  if (riskScore < 3) return 0x00ff00; // 녹색
  if (riskScore < 6) return 0xffff00; // 노란색
  if (riskScore < 8) return 0xff8800; // 주황색
  return 0xff0000; // 빨간색
}
```

### 4.3 API Gateway 설정

#### 4.3.1 Kong 구성
```yaml
_format_version: "3.0"

services:
  - name: graphql-service
    url: http://graphql-service.riskradar-prod.svc.cluster.local:4000
    routes:
      - name: graphql-route
        paths:
          - /graphql
        methods:
          - POST
          - GET
    plugins:
      - name: jwt
        config:
          key_claim_name: iss
          claims_to_verify:
            - exp
      - name: rate-limiting
        config:
          minute: 100
          policy: local
      - name: cors
        config:
          origins:
            - https://app.riskradar.io
            - http://localhost:3000
          credentials: true
          exposed_headers:
            - X-Request-Id
      - name: request-transformer
        config:
          add:
            headers:
              - X-Service-Name:graphql

  - name: rest-api-service
    url: http://api-service.riskradar-prod.svc.cluster.local:8080
    routes:
      - name: api-route
        paths:
          - /api/v1
        strip_path: false
    plugins:
      - name: jwt
      - name: rate-limiting
        config:
          second: 10
          minute: 100
      - name: response-transformer
        config:
          add:
            headers:
              - X-API-Version:v1
              - Cache-Control:no-cache

consumers:
  - username: admin@riskradar.io
    jwt_secrets:
      - key: ${JWT_SECRET}
        algorithm: HS256

plugins:
  - name: prometheus
  - name: zipkin
    config:
      http_endpoint: http://jaeger-collector:9411/api/v2/spans
      sample_ratio: 0.01
```

### 4.4 인증/인가 시스템

#### 4.4.1 JWT 토큰 구조
```typescript
interface JWTPayload {
  sub: string;          // User ID
  email: string;        // User email
  name: string;         // User name
  company: string;      // Company ID
  role: UserRole;       // ADMIN | USER | VIEWER
  permissions: string[]; // Fine-grained permissions
  iat: number;          // Issued at
  exp: number;          // Expiration
  iss: string;          // Issuer
}

enum UserRole {
  ADMIN = 'ADMIN',
  USER = 'USER',
  VIEWER = 'VIEWER'
}
```

#### 4.4.2 인증 미들웨어
```typescript
// middleware/auth.ts
import { NextRequest, NextResponse } from 'next/server';
import { verifyJWT } from '@/lib/auth';

export async function authMiddleware(request: NextRequest) {
  const token = request.headers.get('authorization')?.replace('Bearer ', '');
  
  if (!token) {
    return NextResponse.json(
      { error: 'Authentication required' },
      { status: 401 }
    );
  }
  
  try {
    const payload = await verifyJWT(token);
    
    // 권한 검증
    const requiredPermission = getRequiredPermission(request);
    if (requiredPermission && !payload.permissions.includes(requiredPermission)) {
      return NextResponse.json(
        { error: 'Insufficient permissions' },
        { status: 403 }
      );
    }
    
    // 사용자 정보를 헤더에 추가
    const response = NextResponse.next();
    response.headers.set('X-User-Id', payload.sub);
    response.headers.set('X-User-Role', payload.role);
    
    return response;
  } catch (error) {
    return NextResponse.json(
      { error: 'Invalid token' },
      { status: 401 }
    );
  }
}
```

## 5. 기술 스택

### 5.1 Frontend
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript 5.x
- **Styling**: Tailwind CSS 3.x
- **State Management**: Zustand
- **Data Fetching**: TanStack Query + GraphQL
- **Visualization**: D3.js, Three.js
- **Testing**: Jest, React Testing Library

### 5.2 Backend (API Layer)
- **API Gateway**: Kong 3.x
- **GraphQL**: Strawberry (Python)
- **Authentication**: JWT (PyJWT)
- **Validation**: Pydantic
- **Documentation**: GraphQL Playground

### 5.3 개발 도구
- **Bundler**: Turbo
- **Linting**: ESLint, Prettier
- **Git Hooks**: Husky
- **CI/CD**: GitLab CI

## 6. 구현 계획

### 6.1 마일스톤
| 주차 | 목표 | 산출물 |
|------|------|--------|
| Week 1 | API Gateway 설정 | Kong 구성 완료 |
| Week 2 | GraphQL 스키마 | 기본 쿼리 동작 |
| Week 3 | 인증 시스템 | JWT 로그인 구현 |
| Week 4 | 대시보드 UI | 기본 화면 완성 |

### 6.2 리스크 및 대응
| 리스크 | 영향도 | 대응 방안 |
|--------|--------|-----------|
| GraphQL 복잡도 | Medium | DataLoader로 N+1 해결 |
| 3D 렌더링 성능 | High | WebGL 최적화, LOD 적용 |
| 모바일 대응 | Medium | Progressive Enhancement |

## 7. 테스트 계획

### 7.1 단위 테스트
- **Frontend**: 컴포넌트 테스트 80% 커버리지
- **GraphQL**: Resolver 테스트
- **인증**: JWT 생성/검증 테스트

### 7.2 통합 테스트
- **E2E**: Playwright로 주요 시나리오
- **API**: Postman Collection
- **성능**: Lighthouse CI

## 8. 완료 기준

### 8.1 기능 완료
- [x] Kong API Gateway 구동
- [x] GraphQL 엔드포인트 동작
- [x] JWT 기반 로그인
- [x] 대시보드 첫 화면

### 8.2 품질 기준
- [x] Lighthouse 점수 90+
- [x] 모바일 반응형 디자인
- [x] 3초 이내 페이지 로드

## 9. 의존성

### 9.1 외부 의존성
- 모든 백엔드 서비스 API
- Neo4j GraphQL 라이브러리
- CDN 설정

### 9.2 디자인 시스템
- Figma 디자인 파일
- 브랜드 가이드라인

## 10. 부록

### 10.1 UI 컴포넌트 라이브러리
```tsx
// Design System 구조
components/
├── primitives/      # 기본 요소
│   ├── Button/
│   ├── Input/
│   └── Card/
├── composites/      # 조합 컴포넌트
│   ├── Form/
│   ├── Table/
│   └── Modal/
└── patterns/        # 비즈니스 컴포넌트
    ├── RiskCard/
    ├── CompanyProfile/
    └── NewsItem/
```

### 10.2 참고 자료
- [Next.js Documentation](https://nextjs.org/docs)
- [GraphQL Best Practices](https://graphql.org/learn/best-practices/)
- [Kong Gateway Guide](https://docs.konghq.com/)