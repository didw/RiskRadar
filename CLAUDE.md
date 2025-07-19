# RiskRadar Development Guidelines

## 프로젝트 구조

이 프로젝트는 **Monorepo** 구조로, 모든 서비스가 하나의 저장소에서 관리됩니다.

```
RiskRadar/
├── services/           # 마이크로서비스
│   ├── data-service/   # Data Squad
│   ├── ml-service/     # ML/NLP Squad
│   ├── graph-service/  # Graph Squad
│   ├── api-gateway/    # Product Squad
│   └── web-ui/         # Product Squad
├── packages/shared/    # 공통 라이브러리
├── integration/        # 통합 테스트
├── tools/             # 개발 도구
├── scripts/           # 빌드/배포 스크립트
└── docs/              # 프로젝트 문서
```

## 핵심 기술 스택

| 영역 | 기술 | 버전 |
|------|------|------|
| Language | Python | 3.11+ |
| Language | TypeScript | 5.x |
| Database | Neo4j | 5.x |
| Streaming | Kafka | 3.x |
| Container | Docker | 24.x |
| Orchestration | Kubernetes | 1.28 |

## 개발 원칙

### 1. Monorepo 관리
- 각 서비스는 독립적으로 개발하되, 공통 인터페이스 준수
- `packages/shared`에 공통 타입/유틸리티 관리
- 서비스 간 의존성은 명시적으로 선언

### 2. 문서화
- 각 서비스는 자체 `CLAUDE.md`, `README.md`, `CHANGELOG.md` 보유
- 문서 간 상호 참조는 상대 경로 사용
- API 변경 시 관련 서비스 문서 동시 업데이트

#### 📝 문서 역할 구분
- **CLAUDE.md**: 개발 가이드라인만 간략히 작성
  - 개발 환경 설정, 코딩 규칙, 테스트 방법
  - 프로젝트 상세 정보나 변경사항은 포함하지 않음
- **README.md**: 프로젝트 관련 내용
  - 프로젝트 개요, 설치/실행 방법, 사용법
  - 현재 상태, 주요 기능, 아키텍처 설명
- **CHANGELOG.md**: 변경사항 기록
  - 버전별 추가/변경/수정 사항 상세 기록
  - [Keep a Changelog](https://keepachangelog.com/) 형식 준수
  - Sprint 완료 시 성과 지표 및 통합 테스트 결과 포함

### 3. 코드 스타일
- Python: PEP 8 + Black formatter
- TypeScript: ESLint + Prettier
- 커밋 메시지: Conventional Commits

### 4. 테스트
- Unit test coverage: 80% 이상
- Integration test: `integration/` 디렉토리에서 관리
- E2E test: Sprint 종료 시 필수

## 빠른 시작

```bash
# 환경 설정
make setup

# 전체 서비스 실행 (개발 모드)
make dev

# 특정 서비스만 실행
make dev-data-service

# 테스트 실행
make test
```

## 주요 문서 링크

### 프로젝트 개요
- [README.md](./README.md) - 프로젝트 전체 개요
- [Architecture](./docs/prd/PRD_Tech_Architecture.md) - 기술 아키텍처

### 개발 가이드
- [API Standards](./docs/trd/common/API_Standards.md) - API 표준
- [Data Models](./docs/trd/common/Data_Models.md) - 공통 데이터 모델
- [Integration Points](./docs/trd/common/Integration_Points.md) - 통합 지점

### Sprint 가이드
- [Sprint 0 Quick Start](./docs/trd/phase1/Sprint_0_Quick_Start.md) - 빠른 시작
- [Integration Strategy](./docs/trd/phase1/Integration_Strategy.md) - 통합 전략

## 개발 워크플로우

1. **Feature Branch**: `feature/{service-name}/{feature-description}`
2. **PR 생성**: 최소 1명 리뷰 필수
3. **CI 통과**: 모든 테스트 통과
4. **문서 업데이트**: API 변경 시 필수
5. **CHANGELOG 업데이트**: 기능 추가/변경 기록

📖 상세 가이드: [Git Workflow Guide](./docs/development/GIT_WORKFLOW_GUIDE.md)

## 디버깅 & 트러블슈팅

```bash
# 서비스 로그 확인
docker-compose logs -f {service-name}

# 서비스 상태 확인
curl http://localhost:{port}/health

# Kafka 메시지 확인
kafka-console-consumer --topic {topic-name}
```

## 팀 커뮤니케이션

- **Daily Standup**: 매일 09:00
- **Sprint Planning**: 매주 월요일
- **Integration Sync**: 매일 14:00
- **Slack**: #riskradar-dev

---
*최종 업데이트: 2024-07-19*