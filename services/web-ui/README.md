# Web UI - RiskRadar 웹 프론트엔드

## 🎯 서비스 개요

Web UI는 RiskRadar의 사용자 인터페이스입니다. CEO와 임원진을 위한 직관적이고 강력한 리스크 관리 대시보드를 제공합니다.

### 주요 기능
- 📊 **실시간 대시보드**: 리스크 현황 한눈에 파악
- 🏢 **기업 분석**: 개별 기업 상세 리스크 분석
- 🔔 **알림 시스템**: 중요 리스크 실시간 알림
- 📈 **인사이트**: AI 기반 맞춤형 인사이트

## 🚀 빠른 시작

### Prerequisites
- Node.js 18+
- npm or yarn

### 설치 및 실행
```bash
# 1. 의존성 설치
npm install

# 2. 환경 설정
cp .env.example .env.local

# 3. 개발 서버 실행
npm run dev

# 브라우저에서 열기
open http://localhost:3000
```

### 테스트 계정
```
이메일: admin@riskradar.ai
비밀번호: password
```

## 🎨 기술 스택

### Core
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: Zustand

### API & Data
- **GraphQL Client**: Apollo Client (HTTP + WebSocket)
- **Real-time**: GraphQL Subscriptions
- **Authentication**: JWT + Next.js Middleware

### UI & Visualization
- **Component Library**: shadcn/ui + Radix UI
- **Charts**: Recharts (Line, Area, Pie, Bar)
- **Icons**: Lucide React
- **Mobile**: Responsive Design + Sheet Components

### Performance & PWA
- **Code Splitting**: Dynamic Imports
- **Image Optimization**: Next.js Image
- **Caching**: Apollo Client + Service Worker
- **Offline Support**: PWA with Manifest

### Testing & Tools
- **Testing**: Jest + React Testing Library
- **Bundle Analysis**: Webpack Bundle Analyzer
- **Linting**: ESLint + Prettier
- **Type Checking**: TypeScript

## 📅 Sprint 1 진행 상황

### ✅ Week 1: 프로젝트 설정 (완료)
- Next.js 14 App Router 마이그레이션
- TypeScript 및 Tailwind CSS 설정
- 기본 대시보드 레이아웃
- Mock 데이터 기반 UI

### ✅ Week 2: 인증 시스템 (완료)
- 로그인/회원가입 페이지
- Zustand 기반 상태 관리
- Protected routes 미들웨어
- JWT 토큰 관리
- 사용자 프로필 페이지

### ✅ Week 3: 대시보드 구현 (완료)
- 리스크 요약 카드 강화 (다양한 변형 지원)
- 기업 목록 테이블 개선 (정렬, 필터, 검색)
- 리스크 차트 구현 (Line/Area/Pie/Bar 차트)
- 고급 필터 및 검색 기능
- GraphQL 쿼리/뮤테이션 정의

### ✅ Week 4: 최적화 및 통합 (완료)
- GraphQL 완전 통합 (Apollo Client, WebSocket)
- 실시간 뉴스 타임라인
- 모바일 반응형 레이아웃 (햄버거 메뉴, Sheet)
- 코드 스플리팅 (동적 임포트)
- 이미지 최적화 설정
- PWA 지원 (오프라인 페이지, Service Worker)
- 번들 최적화 설정

## 📱 주요 화면

### 대시보드
- **리스크 요약 카드**: 전체 모니터링 기업, 고위험 기업, 신규 리스크, 평균 리스크 점수
- **리스크 차트**: Line/Area 차트로 30일간 리스크 추이 시각화
- **리스크 분포**: Pie/Bar 차트로 리스크 레벨 및 산업별 분포
- **기업 목록**: 정렬, 필터, 검색이 가능한 실시간 기업 리스트
- **뉴스 타임라인**: 실시간 뉴스 업데이트 및 감성 분석

### 반응형 디자인
- **데스크톱**: 사이드바 네비게이션 + 멀티 컬럼 레이아웃
- **태블릿**: 최적화된 그리드 레이아웃
- **모바일**: 햄버거 메뉴 + 스택형 레이아웃

### PWA 기능
- **오프라인 지원**: Service Worker로 캐싱
- **홈 스크린 추가**: 네이티브 앱처럼 설치 가능
- **푸시 알림**: 중요 리스크 업데이트 (예정)

## 🧪 테스트

```bash
# 단위 테스트
npm test

# 테스트 감시 모드
npm run test:watch

# E2E 테스트
npm run test:e2e

# 테스트 커버리지
npm run test:coverage
```

## 📦 빌드 및 배포

```bash
# 프로덕션 빌드
npm run build

# 빌드 결과 실행
npm start

# Docker 빌드
docker build -t riskradar/web-ui:latest .

# 번들 분석
npm run analyze
```

## 🔧 환경 설정

### 환경 변수
```env
# API 엔드포인트
NEXT_PUBLIC_GRAPHQL_URL=http://localhost:4000/graphql
NEXT_PUBLIC_WS_URL=ws://localhost:4000/graphql

# 인증
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-secret-key

# 외부 서비스
NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX
NEXT_PUBLIC_SENTRY_DSN=https://...
```

## 📊 성능 최적화

### Core Web Vitals 목표
- **LCP**: < 2.5s
- **FID**: < 100ms
- **CLS**: < 0.1

### 최적화 전략
- 이미지 최적화 (Next.js Image)
- 코드 스플리팅
- 폰트 최적화
- 캐싱 전략

## 🎨 디자인 시스템

### 컴포넌트
```bash
# Storybook 실행
npm run storybook
```

### 색상 체계
- Primary: Blue (#3B82F6)
- Risk Low: Green (#10B981)
- Risk Medium: Yellow (#F59E0B)
- Risk High: Red (#EF4444)

## 🔗 관련 문서

- [개발 가이드라인](CLAUDE.md)
- [변경 이력](CHANGELOG.md)
- [컴포넌트 문서](docs/components.md)
- [디자인 시스템](docs/design-system.md)

## 🤝 담당자

- **Squad**: Product Squad
- **Lead**: @product-lead
- **Members**: @frontend-dev1, @frontend-dev2