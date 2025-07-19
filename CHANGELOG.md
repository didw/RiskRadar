# Changelog
# 변경 이력

이 프로젝트의 모든 주요 변경사항이 이 파일에 기록됩니다.

포맷은 [Keep a Changelog](https://keepachangelog.com/ko/1.0.0/)를 기반으로 하며,
이 프로젝트는 [Semantic Versioning](https://semver.org/spec/v2.0.0.html)을 따릅니다.

## [Unreleased]

## [0.2.2] - 2025-07-19

### 🔧 ML Service 개선

#### 🚀 Added
- **CPU 전용 PyTorch 설치**
  - `--extra-index-url https://download.pytorch.org/whl/cpu` 추가
  - `torch==2.1.0+cpu` 및 `torchvision==0.16.0+cpu` 사용
  - Docker 이미지 크기 최적화 (GPU 버전 대비 약 2GB 감소)

#### 🔧 Changed
- **의존성 관리 개선**
  - ML 라이브러리를 기본 requirements.txt에 포함
  - 개발 환경과 프로덕션 환경 일관성 확보
  - Mock 모드에서도 ML 라이브러리 사용 가능

#### 📝 Documentation
- ML Service의 CPU 전용 설치 가이드 추가
- Docker 빌드 최적화 문서 업데이트

## [0.2.1] - 2025-07-19

### 🐛 통합 테스트 수정

#### 🔧 Fixed
- **ML Service**
  - `pydantic-settings` 패키지 누락 문제 해결
  - `requests` 라이브러리 추가 (Hugging Face API 사용)
  - config.py에 pydantic import fallback 로직 구현
  
- **Graph Service**
  - Neo4j 연결 재시도 로직 추가 (최대 30회, 2초 간격)
  - Docker 환경에서 서비스 시작 순서 문제 해결
  - Health check degraded 상태 추가
  
- **API Gateway**
  - TypeScript 빌드 프로세스 개선 (Multi-stage Dockerfile)
  - GraphQL 스키마 파일 복사 문제 해결
  - 포트 설정 일관성 확보 (4000 → 8004)
  - .dockerignore 파일 추가로 빌드 최적화

#### 📝 Documentation
- 각 서비스 CLAUDE.md 업데이트
- README.md 설치 및 실행 가이드 개선
- 서비스별 CHANGELOG.md 업데이트

### 🎯 **Sprint 1 Week 1 완료 (2024-07-19)**

#### 🚀 Added
- **Data Service**
  - ✅ BaseCrawler 추상 클래스 구현 (base_crawler.py)
  - ✅ 조선일보 크롤러 (ChosunCrawler) 완전 구현
  - ✅ Rate limiting 및 에러 처리 시스템
  - ✅ Kafka Producer 통합 및 메시지 발송 성공
  - ✅ 포괄적인 단위 테스트 (test_base_crawler.py)

- **ML Service**
  - ✅ 한국어 NLP 파이프라인 구축
  - ✅ Mock Kafka Consumer/Producer 구현
  - ✅ 텍스트 전처리 모듈 (normalizer.py)
  - ✅ SimpleTokenizer 통합 (KoNLPy 준비)
  - ✅ REST API 엔드포인트 (/api/v1/process, /health)

- **Graph Service**
  - ✅ Neo4j 연동 및 노드 생성 시스템
  - ✅ Kafka Consumer 구현
  - ✅ Company 및 Risk 노드 생성 로직
  - ✅ GraphQL 스키마 정의

- **API Gateway**
  - ✅ Apollo Server 4 기반 GraphQL API 구현
  - ✅ TypeScript + Jest 개발 환경 구축
  - ✅ 포괄적인 GraphQL 스키마 및 Mock Resolver
  - ✅ JWT 인증 미들웨어 기반 구조
  - ✅ Health check 및 보안 설정

- **Web UI**
  - ✅ Next.js 14 + TypeScript 환경 구축
  - ✅ Apollo Client GraphQL 통합
  - ✅ Dashboard 컴포넌트 구현
  - ✅ Tailwind CSS 스타일링

#### 🧪 Testing
- **통합 테스트 성공**
  - ✅ 전체 데이터 플로우 검증: Data Service → Kafka → ML Service → Graph Service
  - ✅ 6개 뉴스 노드 성공적으로 Neo4j에 저장
  - ✅ 모든 서비스 Health Check 통과
  - ✅ 에러율 0% 달성

#### 📝 Documentation
- Git Workflow Guide 작성
- 각 서비스별 Sprint 1 Requirements 정의
- 신규 개발자 온보딩 가이드 작성

### 🔧 Changed
- Neo4j Docker 이미지: `neo4j:5.0` → `neo4j:5-community`
- Redis 포트: 6379 → 6380 (충돌 해결)
- Kafka 설정: Confluent 메트릭 제거

### 🐛 Fixed
- Docker Compose 인프라 구성 이슈 해결
- 서비스 간 포트 충돌 해결
- SSH 원격 개발 환경 설정 가이드 추가

---

## [0.2.0] - Sprint 1 Week 1 (2024-07-19)

### Sprint 1: 실제 데이터 처리 구현

#### 🚀 Added
- 모노레포 구조 설정
- 기본 프로젝트 구조 생성
- Sprint 0 Mock 구현 준비
- 개발 가이드라인 (CLAUDE.md) 작성
- 프로젝트 개요 문서 (README.md) 작성
- **Thin Vertical Slice 구현**
  - 각 서비스의 최소 실행 가능한 버전 생성
  - Data Service: FastAPI + Kafka Producer
  - ML Service: Kafka Consumer/Producer + 간단한 처리
  - Graph Service: Kafka Consumer + Neo4j 저장
  - API Gateway: Express + GraphQL
  - Web UI: Next.js + 기본 대시보드
  - Quick Start 스크립트 (`quick-start.sh`)

#### 📝 Documentation
- PRD 문서 모듈화 및 개선
- TRD 문서 Squad별/Phase별 작성
- Sprint 기반 개발 계획 수립
- 통합 가이드 및 Quick Start 문서 작성
- **개발 가이드 문서 추가**
  - Thin Vertical Slice Guide 작성
  - 각 서비스 CLAUDE.md에 프로젝트 문서 링크 추가
  - Sprint 0 Quick Start Guide 업데이트

#### 🔧 Changed
- docker-compose.yml API Gateway 포트 변경 (4000 → 8004)

## [0.1.0] - 2024-01-15

### Sprint 0: Walking Skeleton

#### 🚀 Added
- **Data Service**
  - Mock 뉴스 생성기 구현
  - Kafka Producer 설정
  - Health check endpoint
  - 기본 API 구조

- **ML Service**
  - Mock NLP 프로세서 구현
  - Kafka Consumer/Producer 설정
  - 하드코딩된 엔티티 추출
  - 감정 분석 Mock

- **Graph Service**
  - In-memory 그래프 저장소
  - GraphQL 스키마 v0.1
  - 기본 CRUD 작업
  - Mock 데이터 관리

- **Platform**
  - Docker Compose 설정
  - 로컬 Kafka 클러스터
  - 개발 환경 스크립트
  - 기본 네트워킹

- **Web UI**
  - Next.js 프로젝트 설정
  - Mock 대시보드 구현
  - GraphQL 클라이언트
  - 기본 레이아웃

#### 🧪 Testing
- E2E 통합 테스트 스크립트
- Health check 모니터링
- Mock 데이터 플로우 검증

#### 📚 Documentation
- Sprint 0 Quick Start Guide
- Integration Guide
- 각 서비스별 README

## [0.0.1] - 2024-01-01

### 프로젝트 초기화

#### 🚀 Added
- 초기 저장소 생성
- 기본 디렉토리 구조
- 프로젝트 비전 문서
- 경쟁사 분석 문서
- PRD 초안 작성

#### 📝 Documentation
- Risk Management 전략 문서
- Risk Knowledge Graph 연구
- 고객 페르소나 정의
- 기술 스택 선정

---

## 버전 관리 정책

### 버전 번호 체계
- `MAJOR.MINOR.PATCH`
- MAJOR: 호환되지 않는 API 변경
- MINOR: 하위 호환성 있는 기능 추가
- PATCH: 하위 호환성 있는 버그 수정

### 릴리스 주기
- **Sprint Release**: 각 Sprint 완료 시 (2주)
- **Phase Release**: 각 Phase 완료 시 (4주)
- **Production Release**: Beta 테스트 후

### 태그 규칙
- Sprint: `sprint-0`, `sprint-1`, ...
- Phase: `phase-1`, `phase-2`, ...
- Release: `v0.1.0`, `v0.2.0`, ...

## 주요 마일스톤

### 🎯 Upcoming
- [ ] v0.2.0 - Sprint 1 (실제 데이터 처리)
- [ ] v0.3.0 - Sprint 2 (전체 통합)
- [ ] v1.0.0 - Phase 1 완료 (MVP)

### ✅ Completed
- [x] v0.1.0 - Sprint 0 (Walking Skeleton)
- [x] v0.0.1 - 프로젝트 초기화

---

더 자세한 변경사항은 각 서비스별 CHANGELOG.md를 참고하세요:
- [Data Service](services/data-service/CHANGELOG.md)
- [ML Service](services/ml-service/CHANGELOG.md)
- [Graph Service](services/graph-service/CHANGELOG.md)
- [API Gateway](services/api-gateway/CHANGELOG.md)
- [Web UI](services/web-ui/CHANGELOG.md)