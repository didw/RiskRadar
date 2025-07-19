# Low Resource Development Guide
# 저사양 시스템 개발 가이드

## 🎯 개요

이 가이드는 2 Core, 2GB RAM 환경에서 RiskRadar를 개발하는 방법을 설명합니다.

## 🚨 리소스 제약사항

### 현재 시스템
- **CPU**: 2 cores
- **RAM**: 1.9GB (실제 가용: ~250MB)
- **Disk**: 1.6GB available

### 전체 스택 요구사항
- Kafka + Zookeeper: 1GB+
- Neo4j: 1GB+
- 5개 서비스: 1.5GB+
- **총합**: 3.5GB+ 필요

**결론**: 전체 스택을 동시에 실행할 수 없음

## 💡 개발 전략

### 1. **분할 정복 접근법**
한번에 하나의 서비스만 개발하고 테스트

### 2. **Mock 우선 개발**
실제 인프라 대신 가벼운 Mock 사용

### 3. **로컬 개발 + 최소 Docker**
가능한 로컬에서 개발, 필수 서비스만 Docker

## 🛠️ 실제 개발 방법

### Step 1: 최소 인프라만 실행
```bash
# Redis만 실행 (Kafka 대체)
make -f Makefile.light redis
```

### Step 2: 개발할 서비스 선택
```bash
# 예: Data Service 개발
make -f Makefile.light local-data

# 별도 터미널에서 로그 확인
docker logs -f riskradar-redis-light
```

### Step 3: 통합 테스트
```bash
# 두 서비스 연동 테스트
# Terminal 1: Data Service
make -f Makefile.light data

# Terminal 2: ML Service  
make -f Makefile.light ml
```

## 📋 서비스별 개발 가이드

### Data Service 개발
```bash
# 1. 가상환경 설정
cd services/data-service
python3 -m venv venv
source venv/bin/activate

# 2. 의존성 설치
pip install flask redis

# 3. 로컬 실행
REDIS_URL=redis://localhost:6379 \
USE_MOCK_KAFKA=true \
python -m src.main
```

### Web UI 개발
```bash
# 1. 의존성 설치
cd services/web-ui
npm install

# 2. Mock API 모드로 실행
NEXT_PUBLIC_USE_MOCK_API=true \
npm run dev
```

## 🔄 대체 솔루션

### Kafka → Redis Pub/Sub
```python
# Kafka 대신 Redis 사용
import redis

r = redis.Redis()

# Publisher
r.publish('raw-news', json.dumps(news_data))

# Subscriber
pubsub = r.pubsub()
pubsub.subscribe('raw-news')
for message in pubsub.listen():
    process_message(message['data'])
```

### Neo4j → In-Memory Graph
```python
# 간단한 메모리 그래프
class InMemoryGraph:
    def __init__(self):
        self.nodes = {}
        self.edges = []
    
    def add_company(self, id, data):
        self.nodes[id] = {'type': 'Company', **data}
    
    def get_company(self, id):
        return self.nodes.get(id)
```

## 🚀 점진적 통합

### Phase 1: Mock Everything
- Redis Pub/Sub
- In-Memory DB
- Mock API responses

### Phase 2: Selective Real Services
- 실제 Kafka (별도 서버)
- 실제 Neo4j (클라우드)
- 로컬은 여전히 경량 유지

### Phase 3: Full Integration
- CI/CD 환경에서 전체 테스트
- 로컬은 개발만

## 📊 성능 최적화 팁

### 1. **Docker 메모리 제한**
```yaml
services:
  my-service:
    mem_limit: 256m
    memswap_limit: 256m
```

### 2. **불필요한 프로세스 종료**
```bash
# 메모리 확인
free -h

# 큰 프로세스 찾기
ps aux | sort -nrk 3,3 | head -10
```

### 3. **스왑 파일 추가 (임시)**
```bash
# 1GB 스왑 추가
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

## 🌩️ 클라우드 대안

### 1. **GitHub Codespaces**
- 무료 티어: 월 60시간
- 4 cores, 8GB RAM
- 전체 스택 실행 가능

### 2. **Gitpod**
- 무료 티어: 월 50시간
- 전체 개발 환경 제공

### 3. **개발 서버 공유**
- 팀에서 개발 서버 구축
- SSH/VS Code Remote 사용

## 📝 체크리스트

### 로컬 개발 시작 전
- [ ] Redis 설치 또는 Docker로 실행
- [ ] Python 3.11+ 설치
- [ ] Node.js 18+ 설치
- [ ] 1GB+ 여유 디스크 공간

### 일일 개발 플로우
1. [ ] `make -f Makefile.light clean` (이전 컨테이너 정리)
2. [ ] `make -f Makefile.light redis` (Redis 시작)
3. [ ] 개발할 서비스 로컬 실행
4. [ ] 테스트 완료 후 정리

### 통합 테스트 전
- [ ] 모든 Mock 구현 완료
- [ ] 로컬 테스트 통과
- [ ] CI 환경에서 전체 테스트 실행

## 🆘 문제 해결

### "Cannot allocate memory"
```bash
# 1. 메모리 정리
docker system prune -a
sync && echo 3 | sudo tee /proc/sys/vm/drop_caches

# 2. 컨테이너 제한
docker update --memory="128m" container_name
```

### 느린 빌드
```bash
# .dockerignore 확인
echo "node_modules" >> .dockerignore
echo "__pycache__" >> .dockerignore
echo ".git" >> .dockerignore
```

### 디스크 공간 부족
```bash
# Docker 이미지 정리
docker image prune -a

# 로그 정리
docker container prune
docker volume prune
```

## 🎯 결론

저사양 환경에서도 효율적인 개발이 가능합니다:
1. 한번에 하나씩 집중
2. Mock과 경량 도구 활용
3. 필요시 클라우드 활용

"제약은 창의성을 낳는다" - 현명하게 리소스를 활용하세요! 🚀