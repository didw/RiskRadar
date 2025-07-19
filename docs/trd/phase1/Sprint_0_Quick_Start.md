# Sprint 0 Quick Start Guide
# 빠른 시작 가이드

## 🚀 30분 안에 전체 시스템 실행하기

### 1. Prerequisites
```bash
# 필수 도구 확인
docker --version  # Docker 20.10+
docker-compose --version  # Docker Compose 2.0+
git --version
curl --version
```

### 2. Clone & Setup (5분)
```bash
# 프로젝트 클론
git clone https://github.com/didw/RiskRadar.git
cd RiskRadar

# 환경 변수 설정
cp .env.example .env

# Quick Start 스크립트 실행 권한
chmod +x quick-start.sh
```

### 3. 빠른 실행 (10분)
```bash
# 전체 시스템 자동 시작
./quick-start.sh
```

또는 수동 실행:

```bash
# Data Service
cat > services/data-service/requirements.txt << EOF
flask==2.3.0
kafka-python==2.0.2
EOF

cat > services/data-service/Dockerfile << EOF
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "mock_crawler.py"]
EOF

# 위 가이드의 mock_crawler.py 코드 복사

# ML Service, Graph Service, Web UI도 동일하게 설정
```

### 4. Docker Compose 실행 (5분)
```bash
# 전체 시스템 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

### 5. 동작 확인 (5분)
```bash
# 1. 서비스 상태 확인
curl http://localhost:8001/health
curl http://localhost:8002/health  
curl http://localhost:8003/health

# 2. Mock 뉴스 생성
curl -X POST http://localhost:8001/generate-mock-news

# 3. GraphQL 쿼리
curl http://localhost:4000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ companies { name riskScore } }"}'

# 4. UI 확인
open http://localhost:3000
```

### 6. E2E 테스트 (5분)
```bash
# 통합 테스트 실행
./scripts/test-e2e.sh
```

## 📋 체크리스트

### 시작 전
- [ ] Docker & Docker Compose 설치
- [ ] 8001, 8002, 8003, 3000, 4000, 9092 포트 사용 가능
- [ ] 최소 8GB RAM 여유 공간

### 실행 중
- [ ] 모든 컨테이너 Running 상태
- [ ] Kafka 토픽 생성 확인
- [ ] Health endpoint 응답 확인

### 완료 후
- [ ] Mock 뉴스 생성 → UI 표시 확인
- [ ] E2E 테스트 통과
- [ ] GraphQL Playground 접속 가능

## 🔧 자주 발생하는 문제

### 1. Kafka 연결 실패
```bash
# Kafka 재시작
docker-compose restart kafka

# 토픽 수동 생성
docker-compose exec kafka kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic raw-news
```

### 2. 포트 충돌
```bash
# 사용 중인 포트 확인
lsof -i :3000  # 또는 netstat -tulpn | grep 3000

# 포트 변경이 필요한 경우 .env 파일 수정
```

### 3. 메모리 부족
```bash
# Docker 리소스 확인
docker system df

# 불필요한 컨테이너/이미지 정리
docker system prune -a
```

## 🎯 Sprint 0 목표 달성 기준

✅ **필수 (Day 3까지)**
- Mock 뉴스가 생성되어 Kafka로 전송
- ML Service가 메시지를 처리하여 enriched 데이터 생성
- Graph Service가 회사 정보를 저장
- UI에서 회사 목록 표시
- E2E 테스트 1개 이상 통과

⭐ **추가 (시간이 남으면)**
- Prometheus 메트릭 수집
- 로그 중앙화 (ELK)
- API 문서 자동 생성

## 📞 지원

### Squad별 담당자
- **Data Squad**: @data-lead
- **ML/NLP Squad**: @ml-lead
- **Graph Squad**: @graph-lead
- **Platform Squad**: @platform-lead
- **Product Squad**: @product-lead

### 공통 이슈
- Slack: #riskradar-sprint0
- 통합 이슈: @integration-lead

## 🔄 다음 단계

Sprint 0 완료 후:
1. **회고 미팅** (Day 3, 17:00)
2. **Sprint 1 계획** (Day 4, 09:00)
3. **Mock → Real 전환 계획** 수립

---

**Remember**: Sprint 0의 목표는 완벽한 구현이 아닌 **전체 시스템의 연결 확인**입니다! 🎯