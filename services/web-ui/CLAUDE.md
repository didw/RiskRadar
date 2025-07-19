# Web UI Development Guidelines
# 웹 UI 개발 가이드라인

## 📋 서비스 개요

Web UI는 RiskRadar의 프론트엔드 애플리케이션입니다. Next.js 14를 기반으로 하며, CEO들에게 직관적이고 강력한 리스크 관리 대시보드를 제공합니다.

## 🏗️ 프로젝트 구조

```
web-ui/
├── src/
│   ├── app/                    # Next.js 14 App Router
│   │   ├── (auth)/            # 인증 관련 페이지
│   │   │   ├── login/
│   │   │   └── register/
│   │   ├── (dashboard)/       # 대시보드 레이아웃
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   ├── companies/
│   │   │   ├── risks/
│   │   │   └── insights/
│   │   ├── api/              # API 라우트
│   │   ├── layout.tsx        # 루트 레이아웃
│   │   └── globals.css       # 전역 스타일
│   ├── components/           # React 컴포넌트
│   │   ├── ui/              # 기본 UI 컴포넌트
│   │   │   ├── Button/
│   │   │   ├── Card/
│   │   │   └── Modal/
│   │   ├── charts/          # 차트 컴포넌트
│   │   │   ├── RiskChart/
│   │   │   └── NetworkGraph/
│   │   ├── dashboard/       # 대시보드 컴포넌트
│   │   └── layout/          # 레이아웃 컴포넌트
│   ├── lib/                 # 라이브러리 코드
│   │   ├── api/             # API 클라이언트
│   │   ├── apollo/          # Apollo Client 설정
│   │   └── utils/           # 유틸리티 함수
│   ├── hooks/               # 커스텀 훅
│   │   ├── useAuth.ts
│   │   ├── useRiskData.ts
│   │   └── useWebSocket.ts
│   ├── services/            # API 서비스 레이어
│   │   └── auth.service.ts
│   ├── stores/              # 상태 관리 (Zustand)
│   │   └── auth-store.ts
│   ├── graphql/             # GraphQL 쿼리/뮤테이션
│   │   ├── queries/
│   │   │   ├── risk.ts      # 리스크 관련 쿼리
│   │   │   └── company.ts   # 기업 관련 쿼리
│   │   ├── mutations/
│   │   │   └── index.ts     # 뮤테이션 정의
│   │   └── types.ts         # GraphQL 타입 정의
│   ├── types/               # TypeScript 타입
│   │   └── auth.ts
│   └── styles/              # 스타일 관련
├── public/                  # 정적 파일
├── tests/                   # 테스트
├── middleware.ts            # Next.js 미들웨어 (인증 보호)
├── package.json
├── tsconfig.json
├── next.config.js
├── tailwind.config.ts
├── postcss.config.js
├── .env.example
├── .eslintrc.json
├── Dockerfile
├── README.md
├── CLAUDE.md               # 현재 파일
└── CHANGELOG.md
```

## 💻 개발 환경 설정

### Prerequisites
```bash
Node.js 18+
npm or yarn
Git
```

### 설치
```bash
# 의존성 설치
npm install

# 개발 서버 실행
npm run dev

# 프로덕션 빌드
npm run build
npm start
```

### 환경 설정
```bash
cp .env.example .env.local
```

## 🔧 주요 컴포넌트

### 1. App Router Structure
```typescript
// app/(dashboard)/layout.tsx
import { DashboardNav } from '@/components/layout/dashboard-nav';
import { DashboardHeader } from '@/components/layout/dashboard-header';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-screen overflow-hidden">
      <DashboardNav />
      <div className="flex-1 flex flex-col overflow-hidden">
        <DashboardHeader />
        <main className="flex-1 overflow-y-auto bg-gray-50 dark:bg-gray-900">
          <div className="container mx-auto p-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
```

### 2. Authentication System
```typescript
// stores/auth-store.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthStore {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      
      login: async (credentials) => {
        const { user, token } = await authService.login(credentials);
        set({ user, token, isAuthenticated: true });
      },
      
      logout: () => {
        set({ user: null, token: null, isAuthenticated: false });
      },
    }),
    { name: 'auth-storage' }
  )
);
```

### 3. Protected Routes Middleware
```typescript
// middleware.ts
export function middleware(request: NextRequest) {
  const token = request.cookies.get('auth-token')?.value;
  
  if (!token && !publicPaths.includes(request.nextUrl.pathname)) {
    return NextResponse.redirect(new URL('/login', request.url));
  }
  
  return NextResponse.next();
}
```

### 4. GraphQL Client Setup
```typescript
// lib/apollo/client.ts
import { ApolloClient, InMemoryCache, createHttpLink } from '@apollo/client';
import { setContext } from '@apollo/client/link/context';

const httpLink = createHttpLink({
  uri: process.env.NEXT_PUBLIC_GRAPHQL_URL,
});

const authLink = setContext((_, { headers }) => {
  const token = localStorage.getItem('token');
  
  return {
    headers: {
      ...headers,
      authorization: token ? `Bearer ${token}` : '',
    },
  };
});

export const apolloClient = new ApolloClient({
  link: authLink.concat(httpLink),
  cache: new InMemoryCache({
    typePolicies: {
      Company: {
        keyFields: ['id'],
      },
    },
  }),
});
```

### 5. Component Architecture
```typescript
// components/dashboard/RiskOverview.tsx
'use client';

import { useQuery } from '@apollo/client';
import { Card, CardHeader, CardContent } from '@/components/ui/Card';
import { RiskChart } from '@/components/charts/RiskChart';
import { GET_RISK_OVERVIEW } from '@/graphql/queries/risk';
import { Skeleton } from '@/components/ui/Skeleton';

export function RiskOverview({ companyId }: { companyId: string }) {
  const { data, loading, error } = useQuery(GET_RISK_OVERVIEW, {
    variables: { companyId },
    pollInterval: 60000, // 1분마다 갱신
  });
  
  if (loading) return <RiskOverviewSkeleton />;
  if (error) return <ErrorMessage error={error} />;
  
  return (
    <Card>
      <CardHeader>
        <h2 className="text-xl font-semibold">리스크 개요</h2>
      </CardHeader>
      <CardContent>
        <RiskChart data={data.riskOverview} />
        <div className="mt-4 grid grid-cols-3 gap-4">
          <RiskMetric
            label="전체 리스크 점수"
            value={data.riskOverview.totalScore}
            trend={data.riskOverview.trend}
          />
          {/* 추가 메트릭 */}
        </div>
      </CardContent>
    </Card>
  );
}
```

### 6. Custom Hooks
```typescript
// hooks/useRiskData.ts
import { useQuery, useSubscription } from '@apollo/client';
import { GET_RISK_DATA, RISK_UPDATE_SUBSCRIPTION } from '@/graphql';
import { useEffect } from 'react';

export function useRiskData(companyId: string) {
  const { data, loading, error, refetch } = useQuery(GET_RISK_DATA, {
    variables: { companyId },
  });
  
  // 실시간 업데이트 구독
  const { data: updateData } = useSubscription(RISK_UPDATE_SUBSCRIPTION, {
    variables: { companyId },
  });
  
  useEffect(() => {
    if (updateData) {
      // 캐시 업데이트 또는 refetch
      refetch();
    }
  }, [updateData, refetch]);
  
  return {
    riskData: data?.riskData,
    loading,
    error,
    refetch,
  };
}
```

### 7. Server Components
```typescript
// app/(dashboard)/companies/[id]/page.tsx
import { notFound } from 'next/navigation';
import { getClient } from '@/lib/apollo/server';
import { GET_COMPANY } from '@/graphql/queries/company';
import { CompanyDetail } from '@/components/dashboard/CompanyDetail';

export default async function CompanyPage({
  params,
}: {
  params: { id: string };
}) {
  const client = getClient();
  
  try {
    const { data } = await client.query({
      query: GET_COMPANY,
      variables: { id: params.id },
    });
    
    if (!data.company) {
      notFound();
    }
    
    return <CompanyDetail company={data.company} />;
  } catch (error) {
    throw error;
  }
}

// 정적 생성을 위한 params
export async function generateStaticParams() {
  const client = getClient();
  const { data } = await client.query({ query: GET_TOP_COMPANIES });
  
  return data.companies.map((company) => ({
    id: company.id,
  }));
}
```

## 📝 코딩 규칙

### 1. 컴포넌트 구조
```typescript
// ✅ Good: 명확한 Props 타입과 구조
interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  onClick?: () => void;
  children: React.ReactNode;
}

export function Button({
  variant = 'primary',
  size = 'md',
  disabled = false,
  onClick,
  children,
}: ButtonProps) {
  return (
    <button
      className={cn(
        'rounded-lg font-medium transition-colors',
        variants[variant],
        sizes[size],
        disabled && 'opacity-50 cursor-not-allowed'
      )}
      disabled={disabled}
      onClick={onClick}
    >
      {children}
    </button>
  );
}
```

### 2. 상태 관리
```typescript
// Zustand store for global state
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

interface UserStore {
  user: User | null;
  setUser: (user: User | null) => void;
  preferences: UserPreferences;
  updatePreferences: (preferences: Partial<UserPreferences>) => void;
}

export const useUserStore = create<UserStore>()(
  devtools(
    persist(
      (set) => ({
        user: null,
        setUser: (user) => set({ user }),
        preferences: defaultPreferences,
        updatePreferences: (prefs) =>
          set((state) => ({
            preferences: { ...state.preferences, ...prefs },
          })),
      }),
      {
        name: 'user-storage',
      }
    )
  )
);
```

### 3. 에러 처리
```typescript
// Error Boundary
'use client';

import { useEffect } from 'react';
import { captureException } from '@sentry/nextjs';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    captureException(error);
  }, [error]);
  
  return (
    <div className="flex flex-col items-center justify-center min-h-screen">
      <h2 className="text-2xl font-bold mb-4">문제가 발생했습니다</h2>
      <button
        onClick={reset}
        className="px-4 py-2 bg-blue-500 text-white rounded"
      >
        다시 시도
      </button>
    </div>
  );
}
```

### 4. 성능 최적화
```typescript
// 이미지 최적화
import Image from 'next/image';

export function CompanyLogo({ company }: { company: Company }) {
  return (
    <Image
      src={company.logo}
      alt={`${company.name} logo`}
      width={64}
      height={64}
      className="rounded-lg"
      placeholder="blur"
      blurDataURL={company.logoBlur}
    />
  );
}

// 동적 임포트
const RiskChart = dynamic(
  () => import('@/components/charts/RiskChart').then((mod) => mod.RiskChart),
  {
    loading: () => <ChartSkeleton />,
    ssr: false,
  }
);
```

## 🧪 테스트

### 단위 테스트
```bash
npm test
```

### 통합 테스트
```bash
npm run test:integration
```

### E2E 테스트
```bash
npm run test:e2e
```

### 테스트 예시
```typescript
// components/ui/Button/Button.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from './Button';

describe('Button', () => {
  it('renders with children', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });
  
  it('calls onClick when clicked', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    
    fireEvent.click(screen.getByText('Click me'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
  
  it('is disabled when disabled prop is true', () => {
    render(<Button disabled>Click me</Button>);
    expect(screen.getByText('Click me')).toBeDisabled();
  });
});
```

## 🚀 배포

### Docker 빌드
```bash
docker build -t riskradar/web-ui:latest .
```

### 환경 변수
```env
# API
NEXT_PUBLIC_GRAPHQL_URL=http://localhost:4000/graphql
NEXT_PUBLIC_WS_URL=ws://localhost:4000/graphql

# Auth
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-secret-key

# Analytics
NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX

# Sentry
NEXT_PUBLIC_SENTRY_DSN=https://...
```

### 빌드 최적화
```javascript
// next.config.js
module.exports = {
  images: {
    domains: ['cdn.riskradar.ai'],
    formats: ['image/avif', 'image/webp'],
  },
  experimental: {
    optimizeCss: true,
  },
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },
};
```

## 📊 모니터링

### 성능 메트릭
- Core Web Vitals (LCP, FID, CLS)
- Bundle size
- API response time
- Client-side errors

### Analytics
```typescript
// Google Analytics
import { sendGAEvent } from '@next/third-parties/google';

export function trackEvent(action: string, params?: any) {
  if (process.env.NODE_ENV === 'production') {
    sendGAEvent('event', action, params);
  }
}
```

## 🎨 디자인 시스템

### 색상 팔레트
```css
/* tailwind.config.ts */
colors: {
  primary: {
    50: '#eff6ff',
    500: '#3b82f6',
    900: '#1e3a8a',
  },
  risk: {
    low: '#10b981',
    medium: '#f59e0b',
    high: '#ef4444',
  },
}
```

### 컴포넌트 라이브러리
- shadcn/ui 기반
- Tailwind CSS
- Framer Motion (애니메이션)
- Recharts (차트)

## 🔒 보안

### CSP 설정
```typescript
// middleware.ts
export function middleware(request: NextRequest) {
  const nonce = Buffer.from(crypto.randomUUID()).toString('base64');
  const cspHeader = `
    default-src 'self';
    script-src 'self' 'nonce-${nonce}' 'strict-dynamic';
    style-src 'self' 'nonce-${nonce}';
    img-src 'self' blob: data:;
    font-src 'self';
    object-src 'none';
    base-uri 'self';
    form-action 'self';
    frame-ancestors 'none';
    block-all-mixed-content;
    upgrade-insecure-requests;
  `;
  
  const response = NextResponse.next();
  response.headers.set('Content-Security-Policy', cspHeader);
  return response;
}
```

## 🤝 협업

### 개발 서버
- Local: http://localhost:3000
- Staging: https://staging.riskradar.ai
- Production: https://app.riskradar.ai

### 스타일 가이드
- Prettier 설정 준수
- ESLint 규칙 준수
- 컴포넌트 스토리북

## 🐛 트러블슈팅

### 일반적인 문제

#### 1. Hydration Error
```typescript
// 클라이언트 전용 컴포넌트 분리
const ClientOnlyChart = dynamic(
  () => import('./Chart'),
  { ssr: false }
);
```

#### 2. 메모리 누수
- useEffect cleanup
- Event listener 제거
- Subscription 해제

#### 3. 번들 크기
```bash
# 번들 분석
npm run analyze

# 동적 임포트 활용
const HeavyComponent = lazy(() => import('./HeavyComponent'));
```

## 📚 참고 자료

- [Next.js Documentation](https://nextjs.org/docs)
- [React Documentation](https://react.dev)
- [Tailwind CSS](https://tailwindcss.com)
- [Apollo Client](https://www.apollographql.com/docs/react/)

## 🎯 Sprint 개발 가이드

현재 Sprint의 상세 요구사항은 다음 문서를 참고하세요:
- [Sprint 1 Requirements](./Sprint1_Requirements.md) - Week별 구현 목표
- [Sprint Breakdown](../../docs/trd/phase1/Sprint_Breakdown.md) - 전체 Sprint 계획

### 개발 우선순위
1. 기본 대시보드 UI ✅
2. 반응형 레이아웃 ✅
3. 실시간 데이터 업데이트 ✅
4. GraphQL 통합 ✅
5. 성능 최적화 ✅

## 📋 개발 가이드라인

### 아키텍처 원칙

#### 1. 컴포넌트 구조
- **UI 컴포넌트**: `components/ui/` - 재사용 가능한 기본 컴포넌트
- **도메인 컴포넌트**: `components/dashboard/`, `components/charts/` - 비즈니스 로직이 포함된 컴포넌트
- **레이아웃 컴포넌트**: `components/layout/` - 페이지 레이아웃

#### 2. 데이터 흐름
```typescript
// GraphQL 쿼리 우선, 에러 시 Mock 데이터 fallback
const { data, loading, error } = useQuery(GET_RISK_DATA);

if (error) {
  // Mock 데이터로 fallback
  return <ComponentWithMockData />;
}
```

#### 3. 성능 최적화
- 동적 임포트로 코드 스플리팅
- React.memo()로 불필요한 리렌더링 방지
- Apollo Client 캐싱 활용

### 코딩 규칙

#### 1. GraphQL 통합
```typescript
// Apollo Client 설정
const apolloClient = new ApolloClient({
  link: splitLink, // HTTP + WebSocket
  cache: new InMemoryCache({
    typePolicies: {
      Company: { keyFields: ['id'] },
    },
  }),
});

// 실시간 구독 사용
const { data } = useSubscription(RISK_UPDATE_SUBSCRIPTION);
```

#### 2. 모바일 우선 반응형 디자인
```typescript
// Tailwind CSS 반응형 클래스 사용
<div className="grid gap-4 sm:gap-6 md:grid-cols-2 lg:grid-cols-4">
  {/* 모바일: 1열, 태블릿: 2열, 데스크톱: 4열 */}
</div>

// 모바일 전용 컴포넌트
<div className="md:hidden">
  <MobileSidebar />
</div>
```

#### 3. 에러 처리 및 로딩 상태
```typescript
if (loading) return <Skeleton className="w-full h-[300px]" />;
if (error) {
  console.error("GraphQL Error:", error);
  return <FallbackComponent />;
}
```

#### 4. 타입 안전성
```typescript
// GraphQL 타입 정의
interface CompanyRiskFilter {
  industries?: string[];
  riskLevels?: string[];
  searchTerm?: string;
}

// 컴포넌트 Props 타입
interface RiskSummaryCardProps {
  title: string;
  value: string | number;
  variant?: "default" | "danger" | "warning" | "success";
}
```

### 테스트 전략

#### 1. 컴포넌트 테스트
```typescript
// Jest + React Testing Library
describe('RiskSummaryCard', () => {
  it('renders with required props', () => {
    render(<RiskSummaryCard title="Test" value="100" />);
    expect(screen.getByText('Test')).toBeInTheDocument();
  });
});
```

#### 2. GraphQL 테스트
```typescript
// Apollo Client MockedProvider 사용
const mocks = [
  {
    request: { query: GET_RISK_DATA },
    result: { data: { riskData: mockData } },
  },
];
```

### PWA 최적화

#### 1. Service Worker
```javascript
// 캐시 전략
const CACHE_NAME = 'riskradar-v1';
const urlsToCache = ['/', '/offline'];

// 오프라인 지원
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then(response => response || fetch(event.request))
      .catch(() => caches.match('/offline'))
  );
});
```

#### 2. 매니페스트 설정
```json
{
  "name": "RiskRadar",
  "display": "standalone",
  "start_url": "/",
  "theme_color": "#3B82F6"
}
```

## 📁 프로젝트 문서

### 핵심 문서
- [Product Squad TRD](../../docs/trd/phase1/TRD_Product_Squad_P1.md) - 기술 명세
- [API 표준](../../docs/trd/common/API_Standards.md) - API 설계
- [통합 포인트](../../docs/trd/common/Integration_Points.md) - 서비스 연동

### 연관 서비스
- [API Gateway](../api-gateway/CLAUDE.md) - GraphQL API 제공
- [통합 가이드](../../integration/README.md) - 시스템 통합