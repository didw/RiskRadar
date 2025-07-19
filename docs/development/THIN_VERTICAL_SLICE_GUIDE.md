# Thin Vertical Slice 구현 가이드

## 개요

이 문서는 RiskRadar 프로젝트의 "얇은 수직 슬라이스(Thin Vertical Slice)" 구현을 설명합니다. 이 접근법은 최소한의 기능으로 전체 시스템의 End-to-End 흐름을 구축하여 빠른 통합과 검증을 가능하게 합니다.

## 구현 내용

### 1. 서비스별 최소 구현

#### Data Service (Python/FastAPI)
- **포트**: 8001
- **주요 기능**:
  - Health check endpoint (`/health`)
  - 시뮬레이션 뉴스 생성 (`/simulate-news`)
  - Kafka producer로 `raw-news` 토픽에 메시지 전송
- **파일 구조**:
  ```
  services/data-service/
  ├── main.py            # FastAPI 애플리케이션
  ├── requirements.txt   # Python 의존성
  └── Dockerfile        # Docker 이미지 정의
  ```

#### ML Service (Python/FastAPI)
- **포트**: 8002
- **주요 기능**:
  - Kafka consumer로 `raw-news` 토픽 구독
  - 간단한 데이터 처리 (sentiment, keywords, risk_score 추가)
  - Kafka producer로 `enriched-news` 토픽에 전송
- **특징**: 백그라운드 스레드로 Kafka 메시지 처리

#### Graph Service (Python/FastAPI + Neo4j)
- **포트**: 8003
- **주요 기능**:
  - Kafka consumer로 `enriched-news` 토픽 구독
  - Neo4j에 뉴스 노드 저장
  - 그래프 통계 API (`/api/graph/stats`)
- **연결**: Neo4j 데이터베이스 (bolt://neo4j:7687)

#### API Gateway (Node.js/Express + GraphQL)
- **포트**: 8004
- **주요 기능**:
  - GraphQL 엔드포인트 (`/graphql`)
  - Health check 쿼리
  - Graph 서비스 통계 쿼리
- **GraphQL Schema**:
  ```graphql
  type Query {
    health: HealthStatus!
    graphStats: GraphStats!
  }
  ```

#### Web UI (Next.js)
- **포트**: 3000
- **주요 기능**:
  - 시스템 상태 대시보드
  - "Simulate News" 버튼으로 데이터 플로우 트리거
  - 실시간 health check 표시

### 2. 데이터 플로우

```
Web UI (3000) 
  → API Gateway (8004) 
  → Data Service (8001) 
  → Kafka (raw-news) 
  → ML Service (8002) 
  → Kafka (enriched-news) 
  → Graph Service (8003) 
  → Neo4j
```

### 3. Quick Start 스크립트

`quick-start.sh` 스크립트는 다음을 자동화합니다:
1. 인프라 서비스 시작 (Kafka, Neo4j, Redis)
2. Kafka 토픽 생성 (`raw-news`, `enriched-news`)
3. 애플리케이션 서비스 시작
4. Health check 수행

## 실행 방법

### 빠른 시작
```bash
./quick-start.sh
```

### Docker Compose 직접 실행
```bash
# 전체 스택 시작
docker-compose up -d

# 특정 서비스만 시작
docker-compose up -d data-service ml-service

# 로그 확인
docker-compose logs -f [service-name]
```

### 개별 서비스 로컬 실행
```bash
# Data Service
cd services/data-service
pip install -r requirements.txt
uvicorn main:app --reload --port 8001

# Web UI
cd services/web-ui
npm install
npm run dev
```

## 테스트 방법

### 1. Health Check
```bash
# 각 서비스 health check
curl http://localhost:8001/health  # Data Service
curl http://localhost:8002/health  # ML Service
curl http://localhost:8003/health  # Graph Service
curl http://localhost:8004/health  # API Gateway
curl http://localhost:3000/api/health  # Web UI
```

### 2. 데이터 플로우 테스트
```bash
# 뉴스 시뮬레이션
curl -X POST http://localhost:8001/simulate-news

# GraphQL 쿼리
curl -X POST http://localhost:8004/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ graphStats { nodeCount timestamp } }"}'
```

### 3. Web UI 테스트
1. 브라우저에서 http://localhost:3000 접속
2. "Simulate News" 버튼 클릭
3. 시스템 상태 확인

## 환경 변수

각 서비스는 다음 환경 변수를 사용합니다:

### 공통
- `KAFKA_BOOTSTRAP_SERVERS`: Kafka 브로커 주소
- `LOG_LEVEL`: 로그 레벨 (기본: INFO)

### Graph Service
- `NEO4J_URI`: Neo4j 연결 URI
- `NEO4J_USER`: Neo4j 사용자명
- `NEO4J_PASSWORD`: Neo4j 비밀번호

### API Gateway
- `PORT`: 서버 포트
- `GRAPH_SERVICE_URL`: Graph 서비스 URL
- `ML_SERVICE_URL`: ML 서비스 URL
- `DATA_SERVICE_URL`: Data 서비스 URL

## 통합 가이드라인과의 호환성

이 구현은 다음 개발 가이드라인과 완전히 호환됩니다:

### [Distributed Development Guide](./DISTRIBUTED_DEV_GUIDE.md)
- Mock 우선 개발 지원
- 서비스별 독립 실행 가능
- 원격 통합 테스트 준비

### [Low Resource Guide](./LOW_RESOURCE_GUIDE.md)
- 각 서비스 메모리 제한 준수
- Docker 프로파일 지원
- 경량화된 의존성

## 다음 단계

1. **Mock 모드 추가**: 환경 변수로 mock/real 모드 전환
2. **메모리 최적화**: 각 서비스의 메모리 사용량 프로파일링
3. **통합 테스트**: E2E 테스트 케이스 작성
4. **모니터링**: Prometheus/Grafana 통합

## 트러블슈팅

### Kafka 연결 실패
```bash
# Kafka 상태 확인
docker-compose ps kafka

# Kafka 토픽 목록
docker exec riskradar-kafka kafka-topics --list --bootstrap-server localhost:9092
```

### Neo4j 연결 실패
```bash
# Neo4j 상태 확인
docker-compose ps neo4j

# Neo4j 브라우저 접속
http://localhost:7474
```

### 서비스 재시작
```bash
# 특정 서비스만 재시작
docker-compose restart [service-name]

# 전체 재시작
docker-compose down && docker-compose up -d
```