# Distributed Development Guide
# 분산 개발 환경 가이드

## 🎯 개요

이 가이드는 로컬 개발과 원격 통합 테스트를 분리하여 효율적으로 개발하는 방법을 설명합니다.

## 🏗️ 환경 구성

### 1. **로컬 환경 (개발용)**
- **용도**: 코드 작성, 단위 테스트, 코드 리뷰
- **필요 사양**: 2GB RAM, 2 Core
- **도구**: VS Code, Git, Python/Node.js

### 2. **통합 환경 (테스트용)**
- **용도**: 전체 스택 실행, 통합 테스트, 성능 테스트
- **필요 사양**: 8GB+ RAM, 4+ Core
- **위치**: 고사양 서버, 클라우드, 또는 팀 공용 서버

## 📋 개발 워크플로우

### Step 1: 로컬 개발 환경 설정
```bash
# 로컬 개발 도구 설정
./scripts/dev/setup-local-dev.sh

# 특정 서비스 개발 준비
cd services/data-service
source venv/bin/activate
pip install -r requirements.txt
```

### Step 2: 코드 작성 및 단위 테스트
```bash
# 코드 작성
vim src/main.py

# 단위 테스트 실행
pytest tests/unit/

# 린트 및 포맷
black .
flake8 .
```

### Step 3: 원격 통합 테스트
```bash
# 코드 푸시
git add .
git commit -m "feat: implement news crawler"
git push origin feature/news-crawler

# SSH로 통합 서버 접속
ssh user@integration-server

# 통합 서버에서
cd /path/to/RiskRadar
git pull origin feature/news-crawler
make dev-run
make test-integration
```

## 🔄 개발 시나리오

### 시나리오 1: Data Service 개발
```bash
# 로컬 (개발자 PC)
cd services/data-service
# Mock Kafka 사용하여 개발
python src/main.py --mock-kafka

# 원격 (통합 서버)
# 실제 Kafka와 함께 테스트
docker-compose up -d kafka
docker-compose up data-service
```

### 시나리오 2: Web UI 개발
```bash
# 로컬 (개발자 PC)
cd services/web-ui
# Mock API로 UI 개발
NEXT_PUBLIC_USE_MOCK_API=true npm run dev

# 원격 (통합 서버)
# 실제 API와 연동 테스트
docker-compose up
```

## 🛠️ 도구 및 설정

### 1. **VS Code Remote Development**
```json
// .vscode/settings.json
{
  "remote.SSH.remotePlatform": {
    "integration-server": "linux"
  },
  "remote.SSH.configFile": "~/.ssh/config"
}
```

SSH 설정:
```bash
# ~/.ssh/config
Host integration-server
    HostName your-server-ip
    User ubuntu
    IdentityFile ~/.ssh/id_rsa
    ForwardAgent yes
```

### 2. **Git 워크플로우**
```bash
# Feature 브랜치 생성
git checkout -b feature/my-feature

# 로컬에서 작업
git add .
git commit -m "feat: add new feature"

# 통합 테스트 전 푸시
git push origin feature/my-feature

# 통합 서버에서 테스트
ssh integration-server
cd RiskRadar
git fetch origin
git checkout feature/my-feature
make test-integration
```

### 3. **환경 변수 관리**
```bash
# 로컬 개발용 (.env.local)
USE_MOCK_SERVICES=true
LOG_LEVEL=debug

# 통합 테스트용 (.env.integration)
USE_MOCK_SERVICES=false
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
NEO4J_URI=bolt://localhost:7687
```

## 📊 모니터링 및 디버깅

### 로컬 디버깅
```bash
# Python 디버깅
python -m pdb src/main.py

# Node.js 디버깅
node --inspect services/api-gateway/src/index.js
```

### 원격 로그 확인
```bash
# SSH 터널을 통한 로그 스트리밍
ssh integration-server 'docker-compose logs -f' | grep ERROR

# 특정 서비스 로그
ssh integration-server 'docker-compose logs -f data-service'
```

## 🚀 CI/CD 통합

### GitHub Actions 활용
```yaml
# .github/workflows/test.yml
name: Integration Test

on:
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: self-hosted  # 고사양 러너
    steps:
      - uses: actions/checkout@v3
      - name: Run Integration Tests
        run: |
          make dev-run
          make test-integration
```

## 📝 팀 협업 가이드

### 1. **일일 스탠드업**
```
- 로컬에서 작업한 내용
- 통합 테스트가 필요한 부분
- 블로킹 이슈
```

### 2. **코드 리뷰**
```
- 로컬에서 단위 테스트 통과 확인
- PR 생성 시 통합 테스트 결과 첨부
- 리뷰어는 로컬에서 코드만 확인
```

### 3. **통합 서버 사용 규칙**
```
- 사용 전 Slack에 알림
- 테스트 완료 후 리소스 정리
- 장시간 독점 금지
```

## 🔧 문제 해결

### 로컬 개발 이슈
```bash
# Python 가상환경 문제
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Node.js 의존성 문제
rm -rf node_modules package-lock.json
npm install
```

### 통합 환경 이슈
```bash
# 전체 리셋
ssh integration-server
cd RiskRadar
make dev-clean
make dev-setup
make dev-run
```

## 📋 체크리스트

### 로컬 개발 시작 전
- [ ] 최신 코드 pull
- [ ] 가상환경 활성화
- [ ] 환경 변수 설정
- [ ] Mock 서비스 준비

### 통합 테스트 전
- [ ] 단위 테스트 통과
- [ ] 코드 스타일 검사
- [ ] 커밋 및 푸시
- [ ] 통합 서버 가용성 확인

### 코드 리뷰 요청 전
- [ ] 로컬 테스트 완료
- [ ] 통합 테스트 완료
- [ ] 문서 업데이트
- [ ] PR 설명 작성

## 🎯 장점

1. **리소스 효율성**: 개발자 PC 사양 제약 극복
2. **빠른 개발**: 로컬에서 빠른 반복 개발
3. **안정적 테스트**: 통합 환경에서 실제 테스트
4. **팀 협업**: 공용 통합 환경 공유

이 방식으로 효율적인 개발이 가능합니다! 🚀