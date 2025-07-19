# 📅 일일 통합 가이드 (14:00)

## 🎯 통합 테스트 목적
개별적으로 개발한 모듈들이 함께 잘 동작하는지 매일 확인하고, 문제를 조기에 발견/해결

## 🕐 14:00 통합 프로세스

### 1️⃣ 사전 준비 (13:50)
```bash
# 각자의 Feature 브랜치에서
git add .
git commit -m "feat: 오전 작업 내용"
git push origin feature/[service]/[feature]
```

### 2️⃣ 통합 환경 시작 (14:00)
**한 명이 화면 공유하며 진행**
```bash
# 최신 develop 브랜치로
git checkout develop
git pull origin develop

# 전체 시스템 실행
./quick-start.sh

# 시스템 상태 확인
docker-compose ps
```

### 3️⃣ 통합 테스트 실행 (14:10)
```bash
# 단계별 통합 테스트
make test-integration-step1  # Data → ML
make test-integration-step2  # ML → Graph  
make test-integration-step3  # Graph → API → UI
```

### 4️⃣ 문제 발생 시 대응
```bash
# 실시간 로그 확인
docker-compose logs -f [문제 서비스]

# Kafka 메시지 확인
docker exec -it riskradar-kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic raw-news \
  --from-beginning

# 즉시 수정 & 재배포
cd services/[문제 서비스]
# 수정 후
docker-compose up -d --build [서비스명]
```

## 🧪 통합 테스트 시나리오

### Scenario 1: 뉴스 수집 → AI 분석
```bash
# 1. Data Service에서 테스트 뉴스 발행
curl -X POST http://localhost:8001/simulate-news

# 2. ML Service 로그 확인 (처리 확인)
docker-compose logs ml-service | grep "Processed news"

# 3. 처리 결과 확인
curl http://localhost:8002/health
```

### Scenario 2: AI 분석 → 그래프 저장
```bash
# 1. ML Service에서 분석 결과 발행
curl -X POST http://localhost:8002/test-enrichment

# 2. Neo4j에서 저장 확인
# http://localhost:7474 접속
# MATCH (n:Entity) RETURN n LIMIT 10
```

### Scenario 3: 전체 플로우
```bash
# 1. Web UI 접속
open http://localhost:3000

# 2. 대시보드에서 실시간 데이터 확인
# 3. GraphQL Playground 테스트
open http://localhost:4000/graphql
```

## 📊 체크포인트

### ✅ Data → ML
- [ ] Kafka raw-news 토픽에 메시지 발행
- [ ] ML Service가 메시지 수신 및 처리
- [ ] 처리 시간 < 5초

### ✅ ML → Graph
- [ ] Kafka enriched-news 토픽에 메시지 발행
- [ ] Graph Service가 엔티티 저장
- [ ] Neo4j에서 노드/관계 확인

### ✅ Graph → API → UI
- [ ] GraphQL 쿼리 정상 동작
- [ ] Web UI에서 데이터 표시
- [ ] 실시간 업데이트 확인

## 🔧 자주 발생하는 문제

### 1. Kafka 연결 실패
```bash
# Kafka 재시작
docker-compose restart kafka

# 토픽 재생성
docker exec -it riskradar-kafka kafka-topics.sh \
  --create --topic raw-news \
  --bootstrap-server localhost:9092 \
  --partitions 3 --replication-factor 1
```

### 2. Neo4j 메모리 부족
```bash
# docker-compose.yml 수정
# NEO4J_dbms_memory_heap_max__size: 2G
docker-compose up -d neo4j
```

### 3. 서비스 간 타이밍 이슈
```bash
# 의존성 순서대로 재시작
docker-compose restart kafka
sleep 10
docker-compose restart data-service ml-service
sleep 5
docker-compose restart graph-service
```

## 💬 커뮤니케이션

### Slack/Teams 채널
```
#riskradar-integration
- 14:00 "통합 테스트 시작합니다"
- 14:10 "Step 1 통과 ✅"
- 14:20 "ML → Graph 이슈 발생, 디버깅 중"
- 14:30 "이슈 해결, PR #123 참조"
```

### 이슈 기록
```markdown
## 2024-01-15 통합 이슈
- 문제: ML Service 메모리 누수
- 원인: 배치 처리 시 GC 미실행
- 해결: batch_size 100 → 50으로 조정
- PR: #124
```

## 📝 통합 후 작업

### 1. Feature 브랜치 업데이트
```bash
git checkout feature/my-service/my-feature
git merge develop
git push origin feature/my-service/my-feature
```

### 2. 내일 작업 조율
- 인터페이스 변경 예정 공유
- 의존성 있는 작업 확인
- Mock 데이터 업데이트 필요사항

### 3. 문서 업데이트
- 변경된 API 스펙
- 새로운 환경 변수
- 성능 측정 결과

---
**Remember**: 통합은 우리 모두의 책임입니다! 🤝