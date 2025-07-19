# RiskRadar
# AI 기반 CEO 리스크 관리 플랫폼

<div align="center">
  <img src="docs/assets/logo.png" alt="RiskRadar Logo" width="200"/>
  
  [![Build Status](https://github.com/your-org/riskradar/workflows/CI/badge.svg)](https://github.com/your-org/riskradar/actions)
  [![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
  [![Documentation](https://img.shields.io/badge/docs-latest-brightgreen.svg)](docs/)
</div>

## 🎯 프로젝트 개요

RiskRadar는 한국 상위 200대 기업의 CEO를 위한 AI 기반 리스크 관리 플랫폼입니다. Risk Knowledge Graph(RKG)를 활용하여 파편화된 정보를 통합하고 실시간으로 맥락 기반 인사이트를 제공합니다.

### 핵심 가치
- **실시간 리스크 모니터링**: 뉴스, 공시, SNS 등 다양한 소스에서 리스크 신호 포착
- **관계 기반 분석**: 기업-인물-이벤트 간의 숨겨진 연결고리 발견
- **맞춤형 인사이트**: CEO 개인화된 3분 브리핑 및 의사결정 지원
- **예측적 분석**: 머신러닝을 통한 리스크 패턴 식별 및 조기 경보

## 📦 모노레포 구조

```
RiskRadar/
├── services/                   # 마이크로서비스
│   ├── data-service/          # 데이터 수집 서비스
│   │   ├── crawlers/          # 뉴스 크롤러
│   │   ├── kafka/             # Kafka 프로듀서
│   │   ├── README.md
│   │   ├── CLAUDE.md
│   │   └── CHANGELOG.md
│   │
│   ├── ml-service/            # ML/NLP 서비스
│   │   ├── models/            # ML 모델
│   │   ├── processors/        # NLP 프로세서
│   │   ├── README.md
│   │   ├── CLAUDE.md
│   │   └── CHANGELOG.md
│   │
│   ├── graph-service/         # 그래프 DB 서비스
│   │   ├── neo4j/             # Neo4j 연동
│   │   ├── queries/           # Cypher 쿼리
│   │   ├── README.md
│   │   ├── CLAUDE.md
│   │   └── CHANGELOG.md
│   │
│   ├── api-gateway/           # API 게이트웨이
│   │   ├── graphql/           # GraphQL 스키마
│   │   ├── auth/              # 인증/인가
│   │   ├── README.md
│   │   ├── CLAUDE.md
│   │   └── CHANGELOG.md
│   │
│   └── web-ui/                # 웹 UI
│       ├── components/        # React 컴포넌트
│       ├── pages/             # Next.js 페이지
│       ├── README.md
│       ├── CLAUDE.md
│       └── CHANGELOG.md
│
├── packages/shared/           # 공통 라이브러리
│   ├── types/                 # TypeScript 타입
│   ├── utils/                 # 유틸리티 함수
│   └── constants/             # 공통 상수
│
├── integration/               # 통합 테스트
│   ├── e2e/                   # End-to-End 테스트
│   ├── contracts/             # Contract 테스트
│   └── performance/           # 성능 테스트
│
├── tools/                     # 개발 도구
│   ├── cli/                   # CLI 도구
│   ├── generators/            # 코드 생성기
│   └── analyzers/             # 코드 분석기
│
├── scripts/                   # 빌드/배포 스크립트
│   ├── build/                 # 빌드 스크립트
│   ├── deploy/                # 배포 스크립트
│   └── dev/                   # 개발 스크립트
│
├── docs/                      # 프로젝트 문서
│   ├── prd/                   # 제품 요구사항
│   ├── trd/                   # 기술 요구사항
│   ├── api/                   # API 문서
│   ├── operations/            # 운영 가이드
│   └── architecture/          # 아키텍처 문서
│
├── .github/                   # GitHub 설정
│   ├── workflows/             # GitHub Actions
│   └── ISSUE_TEMPLATE/        # 이슈 템플릿
│
├── CLAUDE.md                  # 개발 가이드라인
├── README.md                  # 프로젝트 개요 (현재 파일)
├── CHANGELOG.md               # 변경 이력
├── Makefile                   # 빌드 명령어
├── docker-compose.yml         # 로컬 개발 환경
└── .env.example               # 환경 변수 예시
```

## 🚀 빠른 시작

### Prerequisites
- Docker & Docker Compose 2.0+
- Node.js 18+
- Python 3.11+
- Git

### 설치 및 실행
```bash
# 1. 저장소 클론
git clone https://github.com/didw/RiskRadar.git
cd RiskRadar

# 2. 환경 설정
cp .env.example .env

# 3. 의존성 설치 (각 서비스별)
make setup

# 4. 전체 서비스 실행 (Docker Compose)
docker-compose up -d

# 또는 개발 환경 실행
make dev

# 5. 초기 데이터 시딩
NEO4J_PASSWORD=riskradar123 python scripts/seed_neo4j.py

# 6. 서비스 확인
# Web UI: http://localhost:3000
# API Gateway: http://localhost:8004/graphql
# ML Service: http://localhost:8082/docs
# Graph Service: http://localhost:8003/docs
# Neo4j Browser: http://localhost:7474 (neo4j/riskradar123)
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

### 주요 명령어
```bash
# 전체 빌드
make build-all

# 개별 서비스 실행
make dev-data-service
make dev-ml-service
make dev-graph-service
make dev-api-gateway

# 테스트 실행
make test
make test-integration

# 린트 및 포맷
make lint
make format

# 도커 이미지 빌드
docker-compose build

# 로그 확인
docker-compose logs -f [service-name]
```

### 브랜치 전략
- `main`: 프로덕션 배포
- `develop`: 개발 통합
- `feature/*`: 기능 개발
- `hotfix/*`: 긴급 수정

## 📊 프로젝트 현황

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

### 팀 구성
- **Data Squad** (3명): 데이터 수집 및 파이프라인
- **ML/NLP Squad** (3명): 한국어 자연어 처리
- **Graph Squad** (2명): 지식 그래프 구축
- **Platform Squad** (2명): 인프라 및 DevOps
- **Product Squad** (2명): API 및 UI 개발

## 📚 문서

### 핵심 문서
- [제품 요구사항 (PRD)](docs/prd/PRD.md)
- [기술 요구사항 (TRD)](docs/trd/README.md)
- [API 문서](docs/api/README.md)
- [운영 가이드](docs/operations/README.md)

### Sprint 문서
- [Sprint 1 Summary](docs/SPRINT1_SUMMARY.md) - Sprint 1 완료 보고서
- [Week 4 Integration Status](docs/week4_integration_status.md) - 통합 현황
- [Sprint 0 Integration Guide](docs/trd/phase1/Sprint_0_Integration_Guide.md)
- [Sprint Breakdown](docs/trd/phase1/Sprint_Breakdown.md)
- [Integration Strategy](docs/trd/phase1/Integration_Strategy.md)

## 🤝 기여하기

### 기여 프로세스
1. 이슈 생성 또는 할당
2. Feature 브랜치 생성
3. 코드 작성 및 테스트
4. PR 생성 및 리뷰 요청
5. 승인 후 머지

### 코드 리뷰 체크리스트
- [ ] 코드 스타일 가이드 준수
- [ ] 테스트 커버리지 80% 이상
- [ ] 문서 업데이트
- [ ] PR 템플릿 작성

## 📈 성능 목표 및 현황

| 지표 | 목표 | 현재 상태 | 달성률 |
|------|------|-----------|---------|
| **처리량** | 1,000+ 기사/시간 | 1,000+ 기사/시간 | ✅ 100% |
| **ML 처리속도** | < 10ms | 2.57ms | ✅ 257% |
| **API 응답시간** | < 200ms (P95) | ~10ms | ✅ 2000% |
| **가용성** | 99.9% uptime | 99%+ | ✅ 99% |
| **ML F1-Score** | 80% | 56.3% | ⚠️ 70% |

## 🔒 보안

- 모든 API는 JWT 인증 필수
- 데이터 암호화 (전송/저장)
- 정기적인 보안 감사
- GDPR/개인정보보호법 준수

## 📞 연락처

- **기술 문의**: tech@riskradar.ai
- **사업 문의**: business@riskradar.ai
- **버그 리포트**: [GitHub Issues](https://github.com/your-org/riskradar/issues)

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참고하세요.

---

<div align="center">
  Made with ❤️ by RiskRadar Team
</div>