# 2GB RAM 개발 워크플로우
# Low Memory Development Workflow

## 🎯 목표
2GB RAM 환경에서 Data Service, API Gateway, Web UI를 효율적으로 개발하는 방법

## ⚡ 핵심 전략: "한번에 하나씩"

### 1. **개발 순서**

#### Phase 1: API Gateway (가장 가벼움)
```bash
# 1. API Gateway만 개발
cd services/api-gateway
node mock-server.js  # 50-100MB만 사용

# 2. Postman/curl로 테스트
curl http://localhost:8004/health
```

#### Phase 2: Data Service
```bash
# 1. API Gateway 중지
pkill -f node

# 2. Data Service 개발
cd services/data-service
python main.py --mock  # Mock 모드로 실행

# 3. 단위 테스트만 실행
pytest tests/unit/ -v
```

#### Phase 3: Web UI
```bash
# 1. 모든 백엔드 중지
pkill -f python
pkill -f node

# 2. Web UI 개발 (Mock API 사용)
cd services/web-ui
NEXT_PUBLIC_USE_MOCK_API=true npm run dev
```

### 2. **메모리 절약 기법**

#### VS Code 대신 가벼운 에디터
```bash
# Nano (초경량)
nano services/data-service/main.py

# Vim (중간)
vim services/api-gateway/index.js

# VS Code (필요시만)
code --disable-extensions  # 확장 비활성화
```

#### 브라우저 최적화
```bash
# Chrome 대신 Firefox 사용 (메모리 효율적)
firefox --safe-mode

# 또는 터미널 기반 테스트
curl -X POST http://localhost:8004/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ companies { name } }"}'
```

### 3. **Mock 모드 활용**

#### Data Service Mock
```python
# services/data-service/main.py 수정
if os.getenv("MOCK_MODE"):
    # Kafka 없이 로컬 파일에 저장
    with open("mock_output.json", "w") as f:
        json.dump(news_data, f)
```

#### API Gateway Mock
```javascript
// 이미 생성된 mock-server.js 사용
// 실제 서비스 연결 없이 하드코딩된 응답
```

#### Web UI Mock
```javascript
// Mock API 응답 사용
const useMockApi = process.env.NEXT_PUBLIC_USE_MOCK_API === 'true';

if (useMockApi) {
  // 로컬 JSON 파일에서 데이터 로드
  return mockData;
}
```

### 4. **통합 테스트 전략**

#### Step 1: 각 서비스 개별 테스트
```bash
# 각 서비스 폴더에서
npm test  # 또는 pytest
```

#### Step 2: 순차적 통합 테스트
```bash
# 1. Data Service 실행 & 데이터 생성
./low-memory-dev.sh 1
curl -X POST http://localhost:8001/generate-mock-news

# 2. Data Service 중지, API Gateway 실행
./low-memory-dev.sh 2
curl http://localhost:8004/graphql

# 3. API Gateway 중지, Web UI 실행
./low-memory-dev.sh 3
# 브라우저에서 확인
```

#### Step 3: 통합 서버에서 전체 테스트
```bash
# 코드 푸시
git add .
git commit -m "feat: implement feature"
git push

# 통합 서버에서
ssh integration-server
cd RiskRadar
git pull
docker-compose up
```

## 🛠️ 개발 도구 설정

### 1. **Git 설정**
```bash
# 메모리 효율적인 Git 설정
git config --global core.preloadindex false
git config --global core.fscache false
git config --global gc.auto 0
```

### 2. **Node.js 메모리 제한**
```bash
# package.json scripts 수정
"scripts": {
  "dev": "NODE_OPTIONS='--max-old-space-size=512' next dev",
  "build": "NODE_OPTIONS='--max-old-space-size=512' next build"
}
```

### 3. **Python 메모리 최적화**
```python
# 가비지 컬렉션 강제
import gc
gc.collect()

# 대용량 데이터 처리 시 제너레이터 사용
def process_large_data():
    for item in data:
        yield process(item)  # 메모리 효율적
```

## 📊 메모리 모니터링

### 실시간 모니터링
```bash
# 메모리 사용량 확인
watch -n 1 free -h

# 프로세스별 메모리
top -o %MEM

# 특정 프로세스
ps aux | grep -E "(node|python|next)"
```

### 메모리 부족 시 대처
```bash
# 1. 스왑 메모리 추가 (임시)
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 2. 불필요한 프로세스 종료
pkill -f chrome
pkill -f firefox

# 3. 시스템 캐시 정리
sudo sync && echo 3 | sudo tee /proc/sys/vm/drop_caches
```

## 🚀 생산성 팁

### 1. **터미널 멀티플렉서 사용**
```bash
# tmux로 여러 세션 관리
tmux new -s dev
# Ctrl+B, C: 새 창
# Ctrl+B, N: 다음 창
# Ctrl+B, D: 세션 분리
```

### 2. **작업 자동화**
```bash
# Makefile에 추가
dev-data:
	@./scripts/dev/low-memory-dev.sh 1

dev-api:
	@./scripts/dev/low-memory-dev.sh 2

dev-ui:
	@./scripts/dev/low-memory-dev.sh 3
```

### 3. **코드 동기화**
```bash
# 자동 동기화 스크립트
while true; do
  git add .
  git commit -m "WIP: $(date +%Y%m%d-%H%M%S)"
  git push origin feature/current
  sleep 3600  # 1시간마다
done
```

## 🎯 결론

2GB RAM에서 3개 서비스를 **동시에** 개발하는 것은 불가능하지만, **순차적**으로 개발하면 가능합니다:

1. Mock 모드 활용
2. 한번에 하나의 서비스만 실행
3. 경량 도구 사용
4. 통합 테스트는 원격 서버에서

이 방법으로 메모리 제약을 극복하고 효율적으로 개발할 수 있습니다!