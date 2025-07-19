# Web UI Changelog
# 웹 UI 변경 이력

## [Unreleased]

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

### v0.2.0 (Sprint 1)
- [ ] 로그인/로그아웃 기능
- [ ] 기본 대시보드 레이아웃
- [ ] 회사 상세 페이지
- [ ] 기본 차트 구현
- [ ] 반응형 디자인

### v0.3.0 (Sprint 2)
- [ ] 실시간 업데이트 (WebSocket)
- [ ] 고급 차트 및 시각화
- [ ] 알림 시스템
- [ ] 사용자 설정
- [ ] 성능 최적화