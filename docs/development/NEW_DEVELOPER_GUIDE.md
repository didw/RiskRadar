# 🚀 신규 개발자 온보딩 가이드

## 📋 프로젝트 개요
RiskRadar - 금융 리스크 모니터링 시스템 (5개 마이크로서비스)

## 🎯 즉시 해야 할 일

### 1. 개발 환경 설정 (30분)
```bash
# 프로젝트 클론
git clone [repository-url]
cd RiskRadar

# 담당 모듈의 최소 환경만 실행
./scripts/minimal-start.sh [service-name]

# 예시
./scripts/minimal-start.sh data    # Data Service 개발자
./scripts/minimal-start.sh ml      # ML Service 개발자
```

> 💡 **개발 전략**: 오전에는 최소 환경으로 단위 테스트, 14:00에 통합 테스트

### 2. 담당 서비스 확인
본인이 담당할 서비스 디렉토리로 이동:
- `services/data-service` - 뉴스 크롤링
- `services/ml-service` - AI 분석
- `services/graph-service` - 지식 그래프
- `services/api-gateway` - API 서버
- `services/web-ui` - 웹 인터페이스

### 3. 필수 문서 읽기 (1시간)
```bash
# 담당 서비스의 CLAUDE.md 확인
cat services/[your-service]/CLAUDE.md

# Sprint 1 체크리스트 확인
cat services/[your-service]/Sprint1_Requirements.md

# 기술 명세서 확인
cat docs/trd/phase1/TRD_[Your_Squad]_P1.md
```

## 💻 개발 시작하기

### 1. Feature 브랜치 생성
```bash
# 스크립트 사용
./scripts/create-feature-branch.sh [service-name] [feature-name]

# 예시
./scripts/create-feature-branch.sh data-service chosun-crawler
```

### 2. 개발 규칙
- **커밋 메시지**: `feat(service): 기능 설명`
- **일일 통합**: 매일 14:00에 develop 브랜치와 동기화
- **테스트 필수**: 커밋 전 테스트 실행

### 3. 일일 작업 흐름
```bash
# 오전 (09:00-14:00)
git checkout feature/your-branch
# 코드 작성...

# 통합 시간 (14:00)
git fetch origin
git merge origin/develop
# 충돌 해결 후
git push origin feature/your-branch

# 오후 (14:00-18:00)
# 개발 계속...
```

## 📊 주요 명령어

### 서비스별 테스트
```bash
# Python 서비스 (data, ml, graph)
cd services/[service-name]
pytest
make lint

# Node.js 서비스 (api-gateway, web-ui)
cd services/[service-name]
npm test
npm run lint
```

### 통합 테스트
```bash
# 전체 시스템 테스트
docker-compose up -d
make test-e2e
```

## 🆘 도움이 필요할 때

1. **기술 문제**: TRD 문서 참조
2. **Git 충돌**: [Git Workflow Guide](./GIT_WORKFLOW_GUIDE.md) 참조
3. **통합 문제**: [Integration Points](../trd/common/Integration_Points.md) 참조
4. **성능 최적화**: [2GB RAM Workflow](./2GB_RAM_WORKFLOW.md) 참조

## ⚡ 빠른 시작 체크리스트

- [ ] quick-start.sh 실행 성공
- [ ] 담당 서비스 CLAUDE.md 읽기 완료
- [ ] Sprint1_Requirements.md 확인
- [ ] Feature 브랜치 생성
- [ ] 첫 번째 테스트 실행
- [ ] 14:00 통합 프로세스 이해

## 📅 첫 주 목표

1. **Day 1-2**: 환경 설정 및 문서 숙지
2. **Day 3-4**: 첫 번째 기능 구현 시작
3. **Day 5**: 코드 리뷰 및 PR 생성

---

💡 **Tip**: 매일 14:00 통합을 잊지 마세요! 충돌을 최소화하는 핵심입니다.