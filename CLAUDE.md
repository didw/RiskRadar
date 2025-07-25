# RiskRadar Development Guidelines
# 통합 개발 가이드라인

## 📋 프로젝트 현황 (Phase 1 완료)

**RiskRadar**는 AI 기반 CEO 리스크 관리 플랫폼으로, **Phase 1 (2025-07-19 완료)** 기준 5개 마이크로서비스가 통합된 완전한 시스템입니다.

### 🏆 달성 성과
- ✅ **End-to-End 데이터 파이프라인** 완성
- ✅ **5개 마이크로서비스** 통합 완료
- ✅ **한국어 NLP 엔진** F1-Score 88.6% (목표 80% 초과)
- ✅ **실시간 처리** 49ms/article (목표 100ms 대비 51% 향상)
- ✅ **통합 테스트** 7/7 통과, API 테스트 38개 통과
- ✅ **Daily Report 시스템** 구현 완료 (실시간 모니터링)

## 🏗️ 시스템 아키텍처

### Monorepo 구조
```
RiskRadar/
├── services/                   # 5개 마이크로서비스 (완료)
│   ├── data-service/          # 📊 데이터 수집 & Kafka 프로듀서
│   ├── ml-service/            # 🤖 ML/NLP 추론 엔진
│   ├── graph-service/         # 🕸️ Neo4j 그래프 DB 관리
│   ├── api-gateway/           # 🌐 GraphQL 통합 API
│   └── web-ui/                # 🎨 Next.js 14 웹 대시보드
├── packages/shared/           # 공통 라이브러리
├── integration/               # 통합 테스트 자동화
├── tools/                     # 개발 도구
├── scripts/                   # 빌드/배포 스크립트
└── docs/                      # 완성된 문서 체계
```

### 실시간 데이터 플로우
```
🌐 뉴스 사이트 → 📊 Data Service → Kafka → 🤖 ML Service → Kafka → 🕸️ Graph Service
                                          ↓                    ↓
                                    📰 NLP 결과          📊 리스크 분석
                                          ↓                    ↓
                              🌐 API Gateway ←→ 🎨 Web Dashboard (실시간)
```

## 🔧 핵심 기술 스택

| 영역 | 기술 | 버전 | 상태 |
|------|------|------|------|
| **언어** | Python | 3.11+ | ✅ |
| **언어** | TypeScript | 5.x | ✅ |
| **프론트엔드** | Next.js | 14 (App Router) | ✅ |
| **백엔드** | FastAPI | 0.104+ | ✅ |
| **그래프 DB** | Neo4j | 5.x | ✅ |
| **스트리밍** | Apache Kafka | 3.x | ✅ |
| **컨테이너** | Docker | 24.x | ✅ |
| **API** | GraphQL | Apollo Server 4 | ✅ |
| **WebSocket** | GraphQL Subscriptions | - | ✅ |

## 💻 개발 환경 & 실행

<<<<<<< HEAD
### 개발 환경
=======
### 빠른 시작 (전체 시스템)
>>>>>>> c7c40f17da0b8537bdd8c967c64452a8affc0593
```bash
# 1. 저장소 클론
git clone https://github.com/didw/RiskRadar.git
cd RiskRadar

# 2. 환경 설정
cp .env.example .env

# 3. 전체 서비스 실행
docker-compose up -d

<<<<<<< HEAD
# 초기 데이터 시딩
NEO4J_PASSWORD=riskradar123 python scripts/seed_neo4j.py
=======
# 4. 상태 확인
make health-check

# 5. 초기 데이터 시딩
python scripts/seed_neo4j.py
>>>>>>> c7c40f17da0b8537bdd8c967c64452a8affc0593

# 6. 통합 테스트 실행
python scripts/test_e2e_flow.py

# 5. 접속
# Web UI:        http://localhost:3000
# API Gateway:   http://localhost:8004/graphql
# ML Service:    http://localhost:8002/docs
# Graph Service: http://localhost:8003/docs
# Neo4j:        http://localhost:7474
```

<<<<<<< HEAD
### 프로덕션 배포
```bash
# 프로덕션 배포 스크립트 실행
chmod +x ./scripts/deploy_production.sh
./scripts/deploy_production.sh

# 또는 Docker Compose로 직접 배포
docker-compose -f docker-compose.prod.yml up -d

# 초기 데이터 시딩
NEO4J_PASSWORD=riskradar123 python scripts/seed_neo4j.py
```

## 주요 문서 링크
=======
### 개발 환경 실행
```bash
# 전체 개발 환경
make dev
>>>>>>> c7c40f17da0b8537bdd8c967c64452a8affc0593

# 개별 서비스 실행
make dev-data-service    # 데이터 수집
make dev-ml-service      # ML/NLP 처리
make dev-graph-service   # 그래프 DB
make dev-api-gateway     # API 게이트웨이
make dev-web-ui          # 웹 대시보드

# 테스트 실행
make test                # 전체 테스트
make test-integration    # 통합 테스트
make test-performance    # 성능 테스트
```

### 필수 사전 조건
- **Docker & Docker Compose** 2.0+
- **Node.js** 18+
- **Python** 3.11+
- **Git**

## 📝 개발 원칙 & 워크플로우

### 1. Monorepo 관리 원칙
- **독립성**: 각 서비스는 독립적으로 개발
- **공통성**: `packages/shared`에서 공통 타입/유틸리티 관리
- **명시성**: 서비스 간 의존성은 명시적으로 선언
- **일관성**: 모든 서비스는 동일한 패턴과 표준 준수

### Sprint 가이드
- [Sprint 0 Quick Start](./docs/trd/phase1/Sprint_0_Quick_Start.md) - 빠른 시작
- [Integration Strategy](./docs/trd/phase1/Integration_Strategy.md) - 통합 전략
- [Sprint 1 Summary](./docs/SPRINT1_SUMMARY.md) - Sprint 1 완료 보고서

## 📊 Daily Report 시스템

### 개요
Phase 1에서 구현된 Daily Report는 CEO를 위한 실시간 시스템 모니터링 대시보드입니다.

### 접속 방법
```bash
# 실시간 데이터 기반 Daily Report
http://localhost:8080/daily-report-real-data.html

# Mock 데이터 기반 Demo Report  
http://localhost:8080/daily-report-standalone.html
```

### 구현 구조
```
Daily Report System/
├── Scripts/
│   ├── generate_daily_report.py    # Python 스크립트 버전
│   ├── setup_daily_report_cron.sh  # Cron 자동화
│   └── run_daily_report.sh         # 실행 스크립트
├── API Gateway/
│   ├── src/graphql/schema/dailyReport.graphql
│   └── src/graphql/resolvers/dailyReport.ts
└── Web UI/
    ├── daily-report-real-data.html      # 실시간 데이터
    └── daily-report-standalone.html     # Mock 데이터
```

### 개발 가이드라인

#### 1. 데이터 소스 우선순위
```javascript
// 1순위: 실제 서비스 API 호출
const healthCheck = await fetch(`${serviceUrl}/health`);

// 2순위: GraphQL API 쿼리
const { data } = await apolloClient.query({ query: GET_DAILY_REPORT });

// 3순위: Mock 데이터 fallback
const report = data?.dailyReport || mockReport;
```

#### 2. 실시간 업데이트 패턴
```javascript
// 30초마다 자동 새로고침
setInterval(loadRealData, 30000);

// 사용자 트리거 새로고침
<button onclick="loadRealData()">🔄 Refresh</button>
```

#### 3. 에러 처리 표준
```javascript
try {
  const response = await fetch(url, { 
    signal: AbortSignal.timeout(5000) 
  });
  return { status: 'healthy', data: await response.json() };
} catch (error) {
  return { status: 'critical', error: error.message };
}
```

#### 4. 상태 표시 가이드라인
- **healthy**: 녹색 (정상 동작)
- **degraded**: 노란색 (부분적 문제)  
- **critical**: 빨간색 (심각한 문제)
- **loading**: 회색 (로딩 중)

### 확장 방법

#### 새로운 메트릭 추가
1. **Python 스크립트 업데이트**
   ```python
   def get_new_metric(self):
       # 새로운 메트릭 수집 로직
       return {"metric_name": "value"}
   ```

2. **GraphQL 스키마 확장**
   ```graphql
   type DailyReport {
     # 기존 필드들...
     newMetric: NewMetricType!
   }
   ```

3. **HTML 템플릿 업데이트**
   ```html
   <div id="new-metric">
     <!-- 새로운 메트릭 표시 -->
   </div>
   ```

### 자동화 설정
```bash
# Daily Report 자동 생성 (매일 오전 9시)
chmod +x ./scripts/setup_daily_report_cron.sh
./scripts/setup_daily_report_cron.sh
```

<<<<<<< HEAD
### Phase 2 & 3 계획
- [Phase 2 Overview](./docs/prd/PRD_Phase2_Overview.md) - Phase 2 제품 요구사항
- [Phase 3 Overview](./docs/prd/PRD_Phase3_Overview.md) - Phase 3 제품 요구사항
- [Sprint Plan](./docs/trd/SPRINT_PLAN_PHASE2_3.md) - Phase 2-3 Sprint 계획

## 개발 워크플로우
=======
### 2. 문서화 표준
>>>>>>> c7c40f17da0b8537bdd8c967c64452a8affc0593

#### 📚 문서 역할 구분
- **CLAUDE.md**: 개발 가이드라인 (환경 설정, 코딩 규칙, 테스트)
- **README.md**: 프로젝트 정보 (개요, 현재 상태, 아키텍처, 사용법)
- **CHANGELOG.md**: 변경사항 기록 (Sprint별 성과, 지표, 기능 변경)

#### 📖 문서 관리 규칙
- 문서 간 상호 참조는 **상대 경로** 사용
- API 변경 시 **관련 서비스 문서** 동시 업데이트
- Sprint 완료 시 **성과 지표** 및 **통합 테스트 결과** 기록
- [Keep a Changelog](https://keepachangelog.com/) 형식 준수

### 3. 코드 스타일 & 품질
- **Python**: PEP 8 + Black formatter + isort
- **TypeScript**: ESLint + Prettier + strict mode
- **커밋**: Conventional Commits 형식
- **테스트**: Unit test coverage 80% 이상 필수
- **리뷰**: 모든 PR은 최소 1명 승인 필수

### 4. Git 워크플로우
```bash
# 브랜치 명명 규칙
feature/{service-name}/{feature-description}
hotfix/{service-name}/{issue-description}
release/{version}

# 예시
feature/ml-service/enhanced-ner-model
feature/api-gateway/websocket-subscriptions
```

#### 개발 프로세스
1. **이슈 생성** → 작업 할당
2. **Feature 브랜치** 생성
3. **코드 작성** + 테스트 (커버리지 80%)
4. **PR 생성** + 리뷰 요청
5. **CI/CD 통과** + 문서 업데이트
6. **승인 후 머지** + CHANGELOG 업데이트

## 🧪 테스트 전략

### 테스트 레벨
- **Unit Tests**: 각 서비스별 80% 커버리지
- **Integration Tests**: `integration/` 디렉토리에서 E2E 테스트
- **Performance Tests**: 성능 기준 달성 검증
- **Contract Tests**: API 간 계약 테스트

### 테스트 실행
```bash
# 전체 테스트 스위트
make test

# 서비스별 테스트
make test-data-service
make test-ml-service
make test-graph-service
make test-api-gateway
make test-web-ui

# 특수 테스트
make test-integration    # E2E 통합 테스트
make test-performance    # 성능 테스트
make test-security       # 보안 테스트
```

### 품질 게이트
- ✅ 모든 Unit Test 통과
- ✅ Integration Test 7/7 통과
- ✅ 코드 커버리지 80% 이상
- ✅ 린팅 규칙 통과
- ✅ 보안 스캔 통과
- ✅ 성능 기준 달성

## 🔍 디버깅 & 트러블슈팅

### 서비스 상태 확인
```bash
# Health Check (모든 서비스)
make health-check

# 개별 서비스 상태
curl http://localhost:8001/health  # Data Service
curl http://localhost:8002/health  # ML Service
curl http://localhost:8003/health  # Graph Service
curl http://localhost:8004/health  # API Gateway
curl http://localhost:3000/api/health  # Web UI
```

### 로그 확인
```bash
# 전체 로그
docker-compose logs -f

# 서비스별 로그
docker-compose logs -f data-service
docker-compose logs -f ml-service
docker-compose logs -f graph-service
docker-compose logs -f api-gateway
docker-compose logs -f web-ui

# Kafka 로그
docker-compose logs -f kafka
```

### 실시간 데이터 플로우 디버깅
```bash
# Kafka 토픽 목록
docker exec riskradar-kafka kafka-topics --bootstrap-server localhost:9092 --list

# 메시지 확인
docker exec riskradar-kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic raw-news --from-beginning

# Neo4j 쿼리 테스트
# http://localhost:7474 → Cypher 쿼리 실행

# GraphQL Playground
# http://localhost:8004/graphql → Query/Mutation 테스트
```

### 일반적인 문제 해결
- **포트 충돌**: `docker-compose down` 후 재시작
- **메모리 부족**: 저사양 환경은 [2GB RAM 가이드](docs/development/2GB_RAM_WORKFLOW.md) 참조
- **의존성 오류**: `make clean && make setup` 재설치
- **Kafka 연결 실패**: `docker-compose restart kafka` 후 5분 대기

## 📊 성능 모니터링

### Phase 1 달성 지표
| 메트릭 | 목표 | 달성 | 상태 |
|--------|------|------|------|
| NLP F1-Score | 80% | **88.6%** | ✅ 초과 달성 |
| 처리 속도 | 100ms/article | **49ms** | ✅ 2배 향상 |
| 처리량 | 10 docs/s | **20+** | ✅ 2배 향상 |
| API 테스트 | 30개 | **38개** | ✅ 완료 |
| 통합 테스트 | 5개 | **7개** | ✅ 완료 |

### 실시간 모니터링
```bash
# 서비스 메트릭
make metrics

# 성능 벤치마크
make benchmark

# 리소스 사용량
docker stats
```

## 🔒 보안 & 컴플라이언스

### 보안 기준
- **인증**: JWT 기반 토큰 인증 (모든 API)
- **암호화**: AES-256 (저장), TLS 1.3 (전송)
- **인가**: RBAC 기반 역할 관리
- **감사**: 모든 API 호출 로깅
- **스캔**: 정기적 보안 취약점 검사

### 개인정보보호
- GDPR/개인정보보호법 준수 설계
- 개인정보 익명화/가명처리
- 데이터 최소 수집 원칙
- 보관 기간 제한

## 📚 주요 문서 링크

### 📖 프로젝트 문서
- [📋 프로젝트 개요](./README.md) - 시스템 현황 및 사용법
- [🎯 제품 요구사항](./docs/prd/PRD.md) - 비즈니스 목표
- [⚙️ 기술 아키텍처](./docs/prd/PRD_Tech_Architecture.md) - 시스템 설계

### 🔧 개발 가이드
- [🚀 빠른 시작](./docs/trd/phase1/Sprint_0_Quick_Start.md) - 30분 시작 가이드
- [📖 Thin Vertical Slice](./docs/development/THIN_VERTICAL_SLICE_GUIDE.md) - 최소 구현
- [💻 저사양 환경](./docs/development/2GB_RAM_WORKFLOW.md) - 메모리 제한 개발
- [🌐 분산 개발](./docs/development/DISTRIBUTED_DEV_GUIDE.md) - 팀 협업

### 🎯 기술 명세
- [📡 API 표준](./docs/trd/common/API_Standards.md) - API 설계 원칙
- [📊 데이터 모델](./docs/trd/common/Data_Models.md) - 공통 구조
- [🔗 통합 지점](./docs/trd/common/Integration_Points.md) - 서비스 연동

### 📋 Sprint 문서 (Phase 1 완료)
- [Sprint 0](./docs/trd/phase1/Sprint_0_Quick_Start.md) - Walking Skeleton
- [Sprint 분해](./docs/trd/phase1/Sprint_Breakdown.md) - 단계별 계획
- [통합 전략](./docs/trd/phase1/Integration_Strategy.md) - E2E 검증

## 🤝 팀 커뮤니케이션

### 개발 리듬
- **Daily Standup**: 매일 09:00 (15분)
- **Sprint Planning**: 격주 월요일 (2시간)
- **Sprint Review**: 격주 금요일 (1시간)
- **Integration Sync**: 매일 14:00 (30분)
- **Retrospective**: Sprint 종료 시 (1시간)

### 커뮤니케이션 채널
- **Slack**: #riskradar-dev (일반), #riskradar-alerts (알림)
- **GitHub**: Issues, Pull Requests, Discussions
- **문서**: 이 가이드 및 각 서비스 문서
- **회의**: Zoom/Google Meet

### 에스컬레이션 경로
1. **기술 이슈**: Squad Lead → Tech Lead
2. **일정 이슈**: Squad Lead → Project Manager
3. **아키텍처 결정**: Tech Lead → Architecture Committee
4. **긴급 이슈**: 즉시 Slack #riskradar-alerts

## 🎯 Phase 2 & 3 준비

### Phase 2 목표 (Week 5-8): RKG Engine
- 고급 Risk Knowledge Graph 엔진
- 예측 모델링 및 시계열 분석
- 18개 언론사 다중 소스 통합
- CEO 맞춤형 3분 브리핑

### Phase 3 목표 (Week 9-12): Product Polish
- 3D Risk Map 시각화
- 모바일 PWA 앱
- GPT 기반 AI 인사이트
- Enterprise 기능 (멀티테넌트, RBAC)

## 환경별 설정

### 개발 환경
- Docker Compose: `docker-compose.yml`
- 포트: 각 서비스별 기본 포트 사용
- 데이터베이스: 로컬 컨테이너

### 프로덕션 환경
- Docker Compose: `docker-compose.prod.yml`
- 포트: Nginx를 통한 통합 접근 (80/443)
- 모니터링: Prometheus + Grafana
- 로깅: ELK Stack (선택사항)

## 서비스별 포트

| 서비스 | 개발 포트 | 프로덕션 포트 | 헬스체크 |
|--------|-----------|---------------|----------|
| Web UI | 3000 | 80 (Nginx) | /api/health |
| API Gateway | 8004 | 8004 | /health |
| Data Service | 8001 | 8001 | /health |
| ML Service | 8082 | 8082 | /api/v1/health |
| Graph Service | 8003 | 8003 | /health |
| Neo4j | 7474/7687 | 7474/7687 | - |
| Kafka | 9092 | 9092 | - |

## 개발 팁

### 서비스 디버깅
```bash
# 서비스 연동 테스트
python scripts/test_e2e_flow.py

# Kafka 메시지 확인
docker exec riskradar-kafka kafka-console-consumer --topic enriched-news --from-beginning

# Neo4j 데이터 확인
# http://localhost:7474 (neo4j/riskradar123)

# 로그 실시간 확인
docker-compose logs -f [service-name]
```

### 트러블슈팅
1. **포트 충돌**: 기존 서비스 중지 후 재시작
2. **Neo4j 인증 실패**: `NEO4J_PASSWORD=riskradar123` 환경 변수 설정
3. **ML Service 포트**: 8082 사용 (8002 아님)
4. **GraphQL 스키마 충돌**: 타입명 중복 확인

---

## 📞 지원 & 연락처

- **기술 지원**: [GitHub Issues](https://github.com/your-org/riskradar/issues)
- **문서 개선**: PR을 통한 기여
- **긴급 문의**: tech@riskradar.ai

---

*최종 업데이트: 2025-07-19 (Phase 1 완료)*
