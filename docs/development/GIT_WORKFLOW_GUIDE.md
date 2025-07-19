# Git Workflow Guide - Feature Branch 전략

## 🌳 브랜치 전략

### 브랜치 구조
```
master (main)
├── develop
│   ├── feature/data-service/chosun-crawler
│   ├── feature/ml-service/ner-integration
│   ├── feature/graph-service/schema-v1
│   ├── feature/api-gateway/jwt-auth
│   └── feature/web-ui/dashboard
└── hotfix/critical-bug-fix
```

## 📋 개발 플로우

### 1. Feature Branch 생성
```bash
# develop 브랜치에서 시작
git checkout develop
git pull origin develop

# 서비스명/기능명으로 브랜치 생성
git checkout -b feature/data-service/chosun-crawler
```

### 2. 개발 진행
```bash
# 작업 진행
cd services/data-service
# ... 코드 작성 ...

# 로컬 테스트
pytest tests/
make lint

# 커밋 (작은 단위로 자주)
git add .
git commit -m "feat(data-service): 조선일보 기사 목록 파싱 구현"
```

### 3. 일일 통합 (14:00)
```bash
# 최신 develop 머지
git fetch origin
git merge origin/develop

# 충돌 해결 후 푸시
git push origin feature/data-service/chosun-crawler

# CI/CD에서 자동 통합 테스트 실행
```

### 4. PR(Pull Request) 생성
```bash
# 기능 완료 후 PR 생성
gh pr create --base develop --title "feat(data-service): 조선일보 크롤러 구현"
```

## 🔄 일일 통합 프로세스

### 오전 작업 (09:00-14:00)
```bash
# 각자 Feature Branch에서 개발
git checkout feature/my-service/my-feature
# 코드 작성...
```

### 통합 시간 (14:00)
```bash
# 1. 모든 개발자가 develop 최신 변경사항 머지
git fetch origin
git merge origin/develop

# 2. 충돌 해결
# 3. 로컬 테스트 통과 확인
make test

# 4. Feature Branch 푸시
git push origin feature/my-service/my-feature
```

### 통합 테스트 (14:00-15:00)
```yaml
# .github/workflows/integration-test.yml
on:
  schedule:
    - cron: '0 5 * * *'  # 14:00 KST
  workflow_dispatch:

jobs:
  integration-test:
    runs-on: self-hosted
    steps:
      - name: Checkout develop
        uses: actions/checkout@v3
        with:
          ref: develop
      
      - name: Run E2E Tests
        run: |
          docker-compose -f docker-compose.test.yml up -d
          make test-e2e
```

## 🚦 머지 규칙

### Feature → Develop 머지 조건
1. ✅ 모든 테스트 통과
2. ✅ 코드 리뷰 승인 (최소 1명)
3. ✅ 통합 테스트 통과
4. ✅ 문서 업데이트 완료

### Develop → Master 머지 (주간 릴리즈)
1. ✅ 모든 Feature 브랜치 머지 완료
2. ✅ 전체 통합 테스트 통과
3. ✅ 성능 테스트 통과
4. ✅ 보안 스캔 통과

## 💡 베스트 프랙티스

### 1. 브랜치 명명 규칙
```
feature/{service-name}/{feature-description}
├── feature/data-service/naver-crawler
├── feature/ml-service/sentiment-analysis
└── feature/web-ui/mobile-responsive
```

### 2. 커밋 메시지 규칙
```
type(scope): subject

- feat: 새로운 기능
- fix: 버그 수정
- docs: 문서 수정
- style: 코드 포맷팅
- refactor: 코드 리팩토링
- test: 테스트 추가
- chore: 빌드 업무 수정

예시:
feat(data-service): 네이버 뉴스 크롤러 추가
fix(ml-service): NER 모델 메모리 누수 해결
```

### 3. PR 템플릿
```markdown
## 변경 사항
- 조선일보 크롤러 구현
- Rate limiting 추가
- 에러 처리 개선

## 테스트
- [x] 단위 테스트 통과
- [x] 통합 테스트 통과
- [x] 로컬 환경 테스트

## 체크리스트
- [x] 문서 업데이트
- [x] CHANGELOG.md 업데이트
- [x] 코드 리뷰 요청
```

## 🛡️ 보호 규칙

### Develop Branch 보호
```yaml
# GitHub Branch Protection Rules
- Require pull request reviews: 1
- Require status checks to pass
  - ci/test
  - ci/lint
  - ci/integration
- Require branches to be up to date
- Include administrators
```

### Master Branch 보호
```yaml
- Require pull request reviews: 2
- Require status checks to pass
- Restrict who can push
- Require signed commits
```

## 🔧 충돌 해결

### 일반적인 충돌 상황
1. **Kafka 토픽 스키마 변경**
   - Data Service와 ML Service 간 조율 필요
   - Schema Registry 사용 권장

2. **API 인터페이스 변경**
   - API Gateway와 Web UI 간 조율
   - API 버저닝 활용

3. **데이터 모델 변경**
   - 모든 서비스 영향
   - 단계적 마이그레이션

### 충돌 해결 프로세스
```bash
# 1. 충돌 발생 시
git status  # 충돌 파일 확인

# 2. 충돌 해결
# 파일 편집하여 충돌 마커 제거

# 3. 해결 완료
git add .
git commit -m "resolve: develop 브랜치와 충돌 해결"

# 4. 재테스트
make test
```

## 📅 주간 플로우

### 월요일
- Sprint 계획 회의
- Feature Branch 생성

### 화-목요일
- 기능 개발
- 일일 통합 (14:00)

### 금요일
- 주간 통합 리뷰
- Develop → Master 머지 준비
- 다음 주 계획

## 🚀 CI/CD 통합

### Feature Branch 푸시 시
1. 자동 린트 검사
2. 단위 테스트 실행
3. Docker 이미지 빌드

### PR 생성 시
1. 통합 테스트 실행
2. 코드 커버리지 체크
3. 보안 스캔

### Develop 머지 시
1. 전체 E2E 테스트
2. 성능 테스트
3. 스테이징 배포

이 워크플로우를 따르면 **안정적인 통합**과 **빠른 개발**을 동시에 달성할 수 있습니다!