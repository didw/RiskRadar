# Web UI Changelog
# 웹 UI 변경 이력

## [Unreleased]

## [0.3.0] - 2025-07-19

### Sprint 1 - Week 3: 대시보드 구현

#### 🚀 Added
- **리스크 요약 카드 강화**
  - 재사용 가능한 RiskSummaryCard 컴포넌트
  - 다양한 변형 지원 (default, danger, warning, success)
  - 트렌드 아이콘 및 변화율 표시
  - 반응형 그리드 레이아웃
- **기업 목록 테이블 개선**
  - EnhancedCompanyList 컴포넌트
  - 정렬 기능 (이름, 리스크 점수, 변화)
  - 고급 필터링 (산업별, 리스크 레벨별)
  - 실시간 검색 기능
  - 드롭다운 액션 메뉴
  - 페이지네이션 지원
- **리스크 차트 구현**
  - RiskOverviewChart (Line/Area 차트 변형)
  - RiskDistributionChart (Pie/Bar 차트 변형)
  - 커스텀 툴팁 구현
  - 반응형 차트 디자인
  - Recharts 라이브러리 통합
- **필터 및 검색 기능**
  - CompanyFilters 컴포넌트
  - 다중 필터 선택
  - 필터 초기화 기능
  - 활성 필터 표시
  - EmptyState 컴포넌트
- **GraphQL 통합**
  - 쿼리 정의 (GET_RISK_OVERVIEW, GET_COMPANY_RISKS 등)
  - 뮤테이션 정의 (UPDATE_COMPANY_ALERT, CREATE_RISK_REPORT 등)
  - TypeScript 타입 정의
  - GraphQL 버전 컴포넌트 생성
  - 실시간 업데이트 구독 준비

#### 🔧 Changed
- 컴포넌트 구조 개선 (더 모듈화된 설계)
- 타입 안정성 향상
- UI 일관성 개선

#### 📦 Dependencies
- recharts (차트 라이브러리)
- @radix-ui/react-popover
- react-day-picker
- date-fns

#### 🧪 Testing
- 테스트 구조 설정
- RiskSummaryCard 단위 테스트 작성

## [0.2.0] - 2025-07-19

### Sprint 1 - Week 2: 인증 시스템 구현

#### 🚀 Added
- **인증 시스템 구축**
  - 로그인/회원가입 페이지 UI
  - 비밀번호 강도 검증
  - 회원가입 성공 메시지
- **상태 관리**
  - Zustand 기반 인증 상태 관리
  - 토큰 저장 및 자동 갱신
  - 로그인 상태 유지
- **보안 기능**
  - Protected routes 미들웨어
  - JWT 토큰 관리
  - 자동 로그아웃
- **사용자 프로필**
  - 프로필 페이지
  - 드롭다운 메뉴
  - 사용자 정보 표시
- **API 통합**
  - API 클라이언트 구현
  - 인증 서비스 레이어
  - 에러 핸들링

#### 🔧 Changed
- 대시보드 헤더에 사용자 메뉴 추가
- 환경 변수 구조 개선

#### 📦 Dependencies
- @radix-ui/react-label
- @radix-ui/react-dropdown-menu

## [0.1.0] - 2024-01-15

### Sprint 0: Mock Implementation

#### 🚀 Added
- Next.js 14 프로젝트 설정
  - App Router 구조
  - TypeScript 설정
  - Tailwind CSS 설정
- Mock 대시보드 구현
  - 기본 레이아웃
  - 회사 목록 테이블
  - Mock 데이터 표시
- GraphQL 클라이언트 설정
  - Apollo Client 설정
  - 기본 쿼리 작성
- Mock 뉴스 생성 버튼
  - API 호출 기능
  - 새로고침 기능

#### 🎨 UI/UX
- 기본 디자인 시스템
- 반응형 레이아웃
- 로딩 상태 표시
- 에러 처리

#### 🧪 Testing
- 컴포넌트 테스트 설정
- Mock 데이터 테스트

#### 📚 Documentation
- README.md 작성
- CLAUDE.md 개발 가이드라인
- 컴포넌트 문서화

## [0.0.1] - 2024-01-01

### 프로젝트 초기화

#### 🚀 Added
- 서비스 디렉토리 구조 생성
- Next.js 프로젝트 생성
- 기본 설정 파일
- Dockerfile 초안

---

## 다음 릴리스 계획

### v0.4.0 (Sprint 1 - Week 4)
- [ ] 모바일 반응형 레이아웃 최적화
- [ ] 이미지 최적화 (Next.js Image)
- [ ] 코드 스플리팅
- [ ] PWA 설정
- [ ] 성능 최적화

### v1.0.0 (Sprint 2)
- [ ] 실시간 업데이트 (WebSocket)
- [ ] 고급 차트 및 시각화
- [ ] 알림 시스템
- [ ] 사용자 설정
- [ ] 성능 최적화