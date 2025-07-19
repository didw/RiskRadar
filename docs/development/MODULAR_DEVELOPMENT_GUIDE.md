# 🧩 모듈별 독립 개발 가이드

## 📋 개발 전략
각 모듈은 독립적으로 개발하고, 매일 14:00에 통합 테스트를 함께 수행합니다.

## 🎯 모듈별 최소 실행 환경

### 1️⃣ Data Service (뉴스 크롤러)
```bash
cd services/data-service

# 최소 필요 서비스: Kafka, Redis
docker-compose -f ../../docker-compose.minimal.yml up kafka redis -d

# 단위 테스트
pytest tests/unit/

# 크롤러 실행 (파일 출력 모드)
python main.py --output-mode file --output-dir ./test_output
```

### 2️⃣ ML Service (AI 분석)
```bash
cd services/ml-service

# 최소 필요 서비스: Kafka만
docker-compose -f ../../docker-compose.minimal.yml up kafka -d

# 샘플 데이터로 테스트
python -m src.processors.ner_processor --input ../data-service/test_output/sample.json

# 단위 테스트
pytest tests/unit/
```

### 3️⃣ Graph Service (지식 그래프)
```bash
cd services/graph-service

# 최소 필요 서비스: Neo4j, Kafka
docker-compose -f ../../docker-compose.minimal.yml up neo4j kafka -d

# 스키마 초기화
python scripts/init_schema.py

# 단위 테스트
pytest tests/unit/
```

### 4️⃣ API Gateway
```bash
cd services/api-gateway

# 최소 필요 서비스: Redis (세션용)
docker-compose -f ../../docker-compose.minimal.yml up redis -d

# Mock 모드로 실행
export USE_MOCK_SERVICES=true
npm run dev

# 단위 테스트
npm test
```

### 5️⃣ Web UI
```bash
cd services/web-ui

# 독립 실행 (Mock API 사용)
export NEXT_PUBLIC_API_URL=http://localhost:3000/api/mock
npm run dev

# 단위 테스트
npm test
```

## 🔄 일일 개발 플로우

### 🌅 오전 (09:00-13:50)
**개별 모듈 개발**
```bash
# 1. Feature 브랜치에서 작업
git checkout feature/my-service/my-feature

# 2. 최소 서비스만 실행
docker-compose -f docker-compose.minimal.yml up [필요한 서비스] -d

# 3. 개발 및 단위 테스트
make test-unit

# 4. 커밋
git commit -m "feat(service): 기능 구현"
```

### 🤝 통합 시간 (14:00-15:00)
**모든 개발자 함께**
```bash
# 1. 전체 시스템 실행
./quick-start.sh

# 2. 통합 테스트 실행
make test-integration

# 3. 문제 발생 시 함께 디버깅
# - Slack/Teams로 화면 공유
# - 실시간으로 로그 확인
# - 즉시 수정 및 재테스트
```

### 🌆 오후 (15:00-18:00)
**통합 이슈 해결 & 개발 계속**
```bash
# 통합 이슈 수정 후 개별 개발 계속
```

## 📊 모듈별 Mock 데이터

### Data Service → ML Service
```json
// mock-data/raw-news.json
{
  "id": "mock-001",
  "title": "테스트 뉴스",
  "content": "삼성전자가 영업이익 10조원을 기록했다.",
  "source": "mock",
  "published_at": "2024-01-15T10:00:00Z"
}
```

### ML Service → Graph Service
```json
// mock-data/enriched-news.json
{
  "id": "mock-001",
  "entities": [
    {"text": "삼성전자", "type": "ORG", "confidence": 0.95}
  ],
  "sentiment": {"score": 0.8, "label": "positive"}
}
```

## 🧪 통합 테스트 전략

### 1. 단계별 통합
```bash
# Step 1: Data → ML
docker-compose up kafka data-service ml-service -d
./tests/integration/test_data_to_ml.sh

# Step 2: ML → Graph
docker-compose up kafka ml-service graph-service neo4j -d
./tests/integration/test_ml_to_graph.sh

# Step 3: Graph → API → UI
docker-compose up graph-service api-gateway web-ui neo4j redis -d
./tests/integration/test_full_stack.sh
```

### 2. 디버깅 도구
```bash
# Kafka 메시지 확인
kafka-console-consumer --topic raw-news --from-beginning

# 서비스 로그 실시간 확인
docker-compose logs -f [service-name]

# Neo4j 브라우저
http://localhost:7474
```

## 📝 일일 체크리스트

### 개발자 개인 (오전)
- [ ] Feature 브랜치 최신화
- [ ] 최소 서비스로 개발 환경 구성
- [ ] 단위 테스트 통과
- [ ] Mock 데이터로 기능 검증

### 팀 전체 (14:00)
- [ ] 전체 시스템 실행
- [ ] 통합 테스트 실행
- [ ] 이슈 공유 및 해결
- [ ] 내일 작업 조율

## 🚀 빠른 시작 스크립트

### minimal-start.sh
```bash
#!/bin/bash
# 모듈별 최소 환경 실행 스크립트

SERVICE=$1

case $SERVICE in
  "data")
    docker-compose -f docker-compose.minimal.yml up kafka redis -d
    echo "✅ Data Service 환경 준비 완료"
    ;;
  "ml")
    docker-compose -f docker-compose.minimal.yml up kafka -d
    echo "✅ ML Service 환경 준비 완료"
    ;;
  "graph")
    docker-compose -f docker-compose.minimal.yml up kafka neo4j -d
    echo "✅ Graph Service 환경 준비 완료"
    ;;
  "api")
    docker-compose -f docker-compose.minimal.yml up redis -d
    echo "✅ API Gateway 환경 준비 완료"
    ;;
  "web")
    echo "✅ Web UI는 독립 실행 가능"
    ;;
  *)
    echo "Usage: $0 [data|ml|graph|api|web]"
    exit 1
    ;;
esac
```

## 💡 팁

1. **Mock 우선 개발**: 실제 연동 전에 Mock으로 검증
2. **Contract Test**: 인터페이스 변경 시 즉시 문서화
3. **로그 레벨**: 개발 중에는 DEBUG, 통합 시 INFO
4. **데이터 샘플**: 각자 10개 정도의 테스트 데이터 준비

## 🔗 관련 문서
- [Docker Compose Minimal](../../docker-compose.minimal.yml)
- [Mock Data Samples](../../mock-data/)
- [Integration Test Guide](./INTEGRATION_TEST_GUIDE.md)