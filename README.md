# RiskRadar
# AI 기반 CEO 리스크 관리 플랫폼

<div align="center">
  <img src="docs/assets/logo.png" alt="RiskRadar Logo" width="200"/>
  
  [![Build Status](https://github.com/your-org/riskradar/workflows/CI/badge.svg)](https://github.com/your-org/riskradar/actions)
  [![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
  [![Documentation](https://img.shields.io/badge/docs-latest-brightgreen.svg)](docs/)
  [![Phase](https://img.shields.io/badge/Phase-1%20Completed-green.svg)](docs/prd/PRD.md)
</div>

## 🎯 프로젝트 개요

RiskRadar는 한국 상위 200대 기업의 CEO를 위한 AI 기반 리스크 관리 플랫폼입니다. Risk Knowledge Graph(RKG)를 활용하여 파편화된 정보를 통합하고 실시간으로 맥락 기반 인사이트를 제공합니다.

### 🏆 Phase 1 달성 성과 (2025-07-19 완료)
- ✅ **완전한 End-to-End 데이터 파이프라인** 구축
- ✅ **5개 마이크로서비스** 통합 완료
- ✅ **한국어 NLP 엔진** F1-Score 88.6% 달성
- ✅ **실시간 리스크 모니터링** 시스템 가동
- ✅ **GraphQL 통합 API** 및 WebSocket 실시간 업데이트

### 핵심 가치
- **실시간 리스크 모니터링**: 뉴스, 공시, SNS 등 다양한 소스에서 리스크 신호 포착
- **관계 기반 분석**: 기업-인물-이벤트 간의 숨겨진 연결고리 발견  
- **맞춤형 인사이트**: CEO 개인화된 3분 브리핑 및 의사결정 지원
- **예측적 분석**: 머신러닝을 통한 리스크 패턴 식별 및 조기 경보

## 📦 시스템 아키텍처

### 현재 구현된 마이크로서비스 (Phase 1)
```
RiskRadar/
├── services/                   # 5개 마이크로서비스 (완료)
│   ├── data-service/          # 📊 데이터 수집 & Kafka 프로듀서
│   │   ├── src/crawlers/      # 뉴스 크롤러 (조선일보 등)
│   │   ├── src/kafka/         # Kafka 통합
│   │   ├── tests/             # 테스트 자동화
│   │   └── Dockerfile         # 컨테이너화 완료
│   │
│   ├── ml-service/            # 🤖 ML/NLP 추론 엔진
│   │   ├── src/models/ner/    # Enhanced Rule-based NER
│   │   ├── src/models/sentiment/ # 한국어 감정 분석
│   │   ├── src/kafka/         # 실시간 처리 파이프라인
│   │   └── tests/             # ML 모델 테스트
│   │
│   ├── graph-service/         # 🕸️ Neo4j 그래프 DB 관리
│   │   ├── src/neo4j/         # 그래프 스키마 & 쿼리
│   │   ├── src/api/           # GraphQL API
│   │   └── cypher/            # Cypher 쿼리 라이브러리
│   │
│   ├── api-gateway/           # 🌐 GraphQL 통합 API
│   │   ├── src/graphql/       # 통합 스키마 & 리졸버
│   │   ├── src/auth/          # JWT 인증/인가
│   │   ├── src/services/      # 서비스 클라이언트
│   │   └── tests/             # 38개 테스트 통과
│   │
│   └── web-ui/                # 🎨 Next.js 14 웹 대시보드
│       ├── src/app/           # App Router
│       ├── src/components/    # React 컴포넌트 시스템
│       ├── src/graphql/       # Apollo Client
│       └── src/hooks/         # 커스텀 훅
│
├── integration/               # 통합 테스트 & 검증
│   ├── test_week2_integration.py # E2E 테스트
│   └── performance/           # 성능 테스트
│
├── docs/                      # 완성된 문서 체계
│   ├── prd/                   # 제품 요구사항
│   ├── trd/phase1/            # Phase 1 기술 명세
│   └── development/           # 개발 가이드
│
├── scripts/dev/               # 개발 자동화 도구
└── docker-compose.yml         # 통합 개발 환경
```

### 실시간 데이터 플로우
```
🌐 뉴스 사이트
    ↓ (크롤링)
📊 Data Service → Kafka → 🤖 ML Service → Kafka → 🕸️ Graph Service
                              ↓ (NLP 처리)        ↓ (관계 분석)
                              📰 실시간 뉴스      📊 리스크 스코어
                                     ↓                  ↓
                              🌐 API Gateway ← → 🎨 Web Dashboard
                                     ↓ (GraphQL + WebSocket)
                              👥 CEO 대시보드 (실시간 업데이트)
```

## 🚀 빠른 시작

### Prerequisites
- Docker & Docker Compose 2.0+
- Node.js 18+
- Python 3.11+
- Git

### 전체 시스템 실행 (권장)
```bash
# 1. 저장소 클론
git clone https://github.com/didw/RiskRadar.git
cd RiskRadar

# 2. 환경 설정
cp .env.example .env

# 3. 전체 서비스 실행 (Docker Compose)
docker-compose up -d

# 4. 서비스 상태 확인
make health-check

# 5. 초기 데이터 시딩
NEO4J_PASSWORD=riskradar123 python scripts/seed_neo4j.py

<<<<<<< HEAD
# 6. 서비스 확인
# Web UI: http://localhost:3000
# API Gateway: http://localhost:8004/graphql
# ML Service: http://localhost:8082/docs
# Graph Service: http://localhost:8003/docs
# Neo4j Browser: http://localhost:7474 (neo4j/riskradar123)
=======
# 6. 접속 확인
# 🎨 Web UI:        http://localhost:3000
# 🌐 API Gateway:   http://localhost:8004/graphql  
# 🤖 ML Service:    http://localhost:8002/docs
# 🕸️ Graph Service: http://localhost:8003/docs
# 📊 Neo4j Browser: http://localhost:7474
# 📋 Kafka UI:      http://localhost:8080
>>>>>>> c7c40f17da0b8537bdd8c967c64452a8affc0593
```

### 통합 테스트
```bash
# End-to-End 테스트 실행
python scripts/test_e2e_flow.py

# 개별 서비스 테스트
curl http://localhost:8001/health  # Data Service
curl http://localhost:8082/api/v1/health  # ML Service
curl http://localhost:8003/health  # Graph Service
curl http://localhost:8004/health  # API Gateway
```

### 프로덕션 배포
```bash
# 프로덕션 배포 스크립트 실행
./scripts/deploy_production.sh

# 또는 Docker Compose로 직접 배포
docker-compose -f docker-compose.prod.yml up -d

# 프로덕션 서비스 확인
# Web UI: http://localhost
# API Gateway: http://localhost:8004/graphql
# Monitoring: http://localhost:3001 (Grafana)
```

### 개발 가이드
- 🚀 [Quick Start Guide](docs/trd/phase1/Sprint_0_Quick_Start.md) - 30분 안에 시작하기
- 🔧 [Thin Vertical Slice Guide](docs/development/THIN_VERTICAL_SLICE_GUIDE.md) - 최소 구현 가이드
- 💻 [Low Resource Development](docs/development/LOW_RESOURCE_GUIDE.md) - 저사양 환경 개발
- 🌐 [Distributed Development](docs/development/DISTRIBUTED_DEV_GUIDE.md) - 분산 개발 전략

## 🏗️ 아키텍처

### 시스템 구성도
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Web UI    │────▶│ API Gateway │────▶│   GraphQL   │
└─────────────┘     └─────────────┘     └─────────────┘
                            │
                    ┌───────┴────────┐
                    ▼                ▼
            ┌─────────────┐  ┌─────────────┐
            │ ML Service  │  │Graph Service│
            └─────────────┘  └─────────────┘
                    │                │
                    └───────┬────────┘
                            ▼
                    ┌─────────────┐
                    │    Kafka    │
                    └─────────────┘
                            ▲
                    ┌─────────────┐
                    │Data Service │
                    └─────────────┘
```

### 기술 스택
- **Frontend**: Next.js 14, TypeScript, TailwindCSS
- **Backend**: Python (FastAPI), Node.js (GraphQL)
- **ML/NLP**: PyTorch, KoBERT, KoNLPy
- **Database**: Neo4j, PostgreSQL, Redis
- **Infrastructure**: Kubernetes (EKS), Docker
- **Streaming**: Apache Kafka
- **Monitoring**: Prometheus, Grafana, ELK

## 🛠️ 개발

### 개발 가이드라인
개발 시 [CLAUDE.md](CLAUDE.md)의 가이드라인을 따라주세요.

### 개발 환경 실행
```bash
# 개별 서비스 실행
make dev-data-service    # 데이터 수집
make dev-ml-service      # ML/NLP 처리  
make dev-graph-service   # 그래프 DB
make dev-api-gateway     # API 게이트웨이
make dev-web-ui          # 웹 대시보드

# 통합 테스트 실행
make test-integration

# 성능 테스트
make test-performance
```

### 🔧 개발 가이드
- 🚀 [Sprint 0 Quick Start](docs/trd/phase1/Sprint_0_Quick_Start.md) - 30분 안에 시작하기
- 📖 [Thin Vertical Slice](docs/development/THIN_VERTICAL_SLICE_GUIDE.md) - 최소 구현 가이드
- 💻 [저사양 환경 개발](docs/development/2GB_RAM_WORKFLOW.md) - 메모리 제한 환경
- 🌐 [분산 개발 전략](docs/development/DISTRIBUTED_DEV_GUIDE.md) - 팀 협업

## 🏗️ 기술 스택 & 성능

### Phase 1 달성 지표
| 항목 | 목표 | 달성 | 상태 |
|------|------|------|------|
| NLP F1-Score | 80% | **88.6%** | ✅ 초과 달성 |
| 처리 속도 | 100ms/article | **49ms/article** | ✅ 2배 향상 |
| 처리량 | 10 docs/s | **20+ docs/s** | ✅ 2배 향상 |
| API 테스트 | 30개 | **38개** | ✅ 모든 테스트 통과 |
| 통합 테스트 | 5개 | **7개** | ✅ E2E 검증 완료 |

### 기술 스택
- **Frontend**: Next.js 14 (App Router), TypeScript, TailwindCSS, Apollo Client
- **Backend**: Python FastAPI, Node.js GraphQL, JWT 인증
- **ML/NLP**: Enhanced Rule-based NER, 한국어 특화 감정 분석, KoNLPy
- **Database**: Neo4j (그래프), Redis (캐싱), PostgreSQL (메타데이터)
- **Streaming**: Apache Kafka (실시간 데이터 파이프라인)
- **Infrastructure**: Docker Compose, Kubernetes ready
- **Monitoring**: Health checks, Performance metrics, Integration tests

## 📊 현재 상태 및 로드맵

### ✅ Phase 1 완료 (Week 1-4): Foundation
```
Sprint 0 (Week 1): Walking Skeleton ✅
├── 5개 마이크로서비스 Mock 구현
├── Docker Compose 통합 환경  
└── E2E 데이터 플로우 검증

Sprint 1 (Week 2-3): Core Features ✅  
├── 실제 뉴스 크롤링 (조선일보)
├── Enhanced NER 모델 (88.6% F1-Score)
├── Neo4j 그래프 DB 구축
├── GraphQL 통합 API (38개 테스트)
├── WebSocket 실시간 업데이트
└── React 대시보드 (반응형)

Sprint 2 (Week 4): Integration & Optimization ✅
├── 성능 최적화 (49ms/article)
├── 통합 테스트 자동화 (7개)  
├── 문서화 완성
└── 배포 준비 완료
```

### 🚧 Phase 2 예정 (Week 5-8): RKG Engine
- **고급 Risk Knowledge Graph**: 복합 관계 분석, 리스크 전파 모델
- **예측 모델링**: 시계열 분석, 리스크 패턴 학습
- **다중 데이터 소스**: 18개 언론사, 공시정보, 소셜미디어  
- **실시간 대시보드**: CEO 맞춤형 3분 브리핑

### 📅 Phase 3 예정 (Week 9-12): Product Polish  
- **고급 UI/UX**: 3D Risk Map, 인터랙티브 시각화
- **모바일 앱**: PWA, 푸시 알림, 오프라인 지원
- **AI 인사이트**: GPT 기반 자연어 요약, 의사결정 지원
- **Enterprise 기능**: 멀티테넌트, RBAC, 감사 로그

## 🛠️ 개발 워크플로우

### 코딩 가이드라인
개발 시 [CLAUDE.md](CLAUDE.md)의 가이드라인을 준수해주세요.

### 주요 명령어  
```bash
# 전체 시스템 관리
make setup          # 의존성 설치
make dev             # 개발 환경 실행  
make build-all       # 전체 빌드
make test            # 모든 테스트 실행
make health-check    # 서비스 상태 확인

# 개별 서비스 제어
make dev-{service}   # 특정 서비스 실행
make test-{service}  # 특정 서비스 테스트
make logs-{service}  # 서비스 로그 확인

# 품질 관리
make lint            # 코드 스타일 검사
make format          # 코드 포맷팅
make security-scan   # 보안 검사
make performance     # 성능 테스트
```

### Git 워크플로우
- `main`: 프로덕션 안정 버전 (Phase 1 완료)
- `develop`: 개발 통합 브랜치
- `feature/*`: 새 기능 개발
- `hotfix/*`: 긴급 수정
- `release/*`: 릴리스 준비

## 📚 문서 체계

### 개발 일정

#### Phase 1: Foundation (Week 1-4) ✅ COMPLETE
- **Sprint 0**: Walking Skeleton ✅
- **Sprint 1**: Core Features ✅
  - Week 1: 기본 구조 및 Mock 구현 ✅
  - Week 2: 서비스 통합 및 테스트 ✅
  - Week 3: 실시간 기능 및 고급 기능 ✅
  - Week 4: 통합 테스트 및 프로덕션 배포 ✅

**Phase 1 성과**:
- 7개 뉴스 소스 통합 (목표 5개 초과 달성)
- End-to-End 파이프라인 구축 완료
- ML 처리 속도 2.57ms (목표 10ms 대비 74% 향상)
- GraphQL API 및 WebSocket 실시간 업데이트 구현
- 프로덕션 배포 완료 (2025-07-19)

#### Phase 2: Enhanced Intelligence (Week 5-8) 🚀 NEXT
- **Sprint 2**: ML 성능 개선 (목표: F1-Score 80%+)
- **Sprint 3**: 엔터프라이즈 기능 구현
- 상세 계획: [Phase 2 Overview](docs/prd/PRD_Phase2_Overview.md)

#### Phase 3: AI Automation (Week 9-12) 📅
- **Sprint 4**: 글로벌 확장 및 AI 자동화
- **Sprint 5**: 최적화 및 출시 준비
- 상세 계획: [Phase 3 Overview](docs/prd/PRD_Phase3_Overview.md)

### 🎯 핵심 문서  
- [📋 제품 요구사항 (PRD)](docs/prd/PRD.md) - 비즈니스 목표 및 요구사항
- [⚙️ 기술 요구사항 (TRD)](docs/trd/README.md) - 아키텍처 및 구현 명세  
- [🔗 API 문서](docs/api/README.md) - GraphQL 스키마 및 사용법
- [🚀 배포 가이드](docs/operations/README.md) - 운영 및 모니터링

### 📖 Phase별 문서
- **Phase 1**: [Sprint 문서](docs/trd/phase1/) - 완료된 구현 내용
- **Phase 2**: RKG Engine 설계 문서 (작성 예정)
- **Phase 3**: Product Polish 사양서 (작성 예정)

### Sprint 문서
- [Sprint 1 Summary](docs/SPRINT1_SUMMARY.md) - Sprint 1 완료 보고서
- [Week 4 Integration Status](docs/week4_integration_status.md) - 통합 현황
- [Sprint 0 Integration Guide](docs/trd/phase1/Sprint_0_Integration_Guide.md)
- [Sprint Breakdown](docs/trd/phase1/Sprint_Breakdown.md)
- [Integration Strategy](docs/trd/phase1/Integration_Strategy.md)

### 🔧 개발 문서
- [통합 테스트 가이드](integration/README.md) - E2E 테스트 실행법
- [성능 최적화](docs/development/PERFORMANCE.md) - 성능 튜닝 가이드
- [트러블슈팅](docs/development/TROUBLESHOOTING.md) - 문제 해결법

## 🤝 기여하기

### 기여 프로세스
1. 이슈 생성 또는 할당받기
2. Feature 브랜치 생성 (`feature/squad-feature-name`)
3. 코드 작성 및 테스트 (커버리지 80% 이상)
4. PR 생성 및 리뷰 요청 (최소 1명 승인)
5. CI/CD 통과 후 머지

### 품질 기준
- [ ] 코드 스타일 가이드 준수 (Prettier, ESLint, Black)
- [ ] 테스트 커버리지 80% 이상
- [ ] 문서 업데이트 (CHANGELOG.md 포함)
- [ ] 통합 테스트 통과
- [ ] 성능 기준 충족

<<<<<<< HEAD
## 📈 성능 목표 및 현황

| 지표 | 목표 | 현재 상태 | 달성률 |
|------|------|-----------|---------|
| **처리량** | 1,000+ 기사/시간 | 1,000+ 기사/시간 | ✅ 100% |
| **ML 처리속도** | < 10ms | 2.57ms | ✅ 257% |
| **API 응답시간** | < 200ms (P95) | ~10ms | ✅ 2000% |
| **가용성** | 99.9% uptime | 99%+ | ✅ 99% |
| **ML F1-Score** | 80% | 56.3% | ⚠️ 70% |
=======
## 📈 성능 & 모니터링

### 현재 달성 지표 (Phase 1)
- **처리량**: 20+ 기사/초 (목표 10 docs/s 대비 2배)
- **지연시간**: 49ms/article (목표 100ms 대비 51% 향상)  
- **정확도**: F1-Score 88.6% (목표 80% 대비 8.6% 향상)
- **가용성**: 통합 테스트 7/7 통과
- **API 성능**: 38개 테스트 모두 통과
>>>>>>> c7c40f17da0b8537bdd8c967c64452a8affc0593

### 모니터링 대시보드
- **Health Checks**: 각 서비스 생존 확인
- **Performance Metrics**: 응답시간, 처리량, 에러율
- **Business Metrics**: 리스크 점수 분포, 뉴스 처리량
- **Integration Tests**: 자동화된 E2E 검증

## 🔒 보안 & 컴플라이언스

- **인증/인가**: JWT 기반 세션 관리
- **데이터 보호**: 전송/저장 시 암호화 (AES-256)
- **API 보안**: Rate limiting, CORS, CSP 헤더
- **개인정보보호**: GDPR/개인정보보호법 준수 설계
- **감사 로그**: 모든 API 호출 로깅

## 🎯 다음 마일스톤

### Phase 2 목표 (Week 5-8)
- [ ] **고급 RKG 엔진**: 다층 관계 분석, 리스크 전파 시뮬레이션
- [ ] **예측 모델**: 시계열 분석 기반 리스크 예측  
- [ ] **멀티 소스**: 18개 언론사 + 공시정보 통합
- [ ] **실시간 인사이트**: CEO 3분 브리핑 자동 생성

### Phase 3 목표 (Week 9-12)  
- [ ] **3D 시각화**: Three.js 기반 리스크 맵
- [ ] **모바일 최적화**: PWA, 푸시 알림
- [ ] **AI 코파일럿**: GPT 기반 의사결정 지원
- [ ] **Enterprise Ready**: 멀티테넌트, RBAC

## 📞 연락처 & 지원

- **기술 문의**: tech@riskradar.ai  
- **사업 문의**: business@riskradar.ai
- **버그 리포트**: [GitHub Issues](https://github.com/your-org/riskradar/issues)
- **개발 문서**: [Technical Documentation](docs/)

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참고하세요.

---

<div align="center">
  <strong>🏆 Phase 1 완료 (2025-07-19)</strong><br>
  Made with ❤️ by RiskRadar Team
</div>