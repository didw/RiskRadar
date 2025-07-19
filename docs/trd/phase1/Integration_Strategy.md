# Phase 1 통합 전략
# Integration Strategy for Phase 1

## 1. 개요

Phase 1을 3개의 Sprint로 나누어 점진적 통합을 진행합니다. 첫 주에는 전체 시스템의 뼈대를 구축하고 Mock/Stub을 활용하여 End-to-End 플로우를 확인합니다.

## 2. Sprint 구성 (Phase 1: 4주)

### Sprint 개요
- **Sprint 0** (Week 1): End-to-End Skeleton with Mocks
- **Sprint 1** (Week 2): Core Features Integration
- **Sprint 2** (Week 3-4): Full Integration & Optimization

## 3. Sprint 0: Walking Skeleton (Week 1)

### 3.1 목표
"Hello World" 수준의 전체 시스템 플로우 구현 - Mock 데이터가 전체 파이프라인을 통과하여 UI에 표시되는 것을 확인

### 3.2 End-to-End 시나리오
```
[Mock News API] 
    → [Data Service (Stub)] 
    → [Kafka (Real)] 
    → [ML Service (Mock)] 
    → [Kafka (Real)]
    → [Graph Service (In-Memory)]
    → [GraphQL (Real)]
    → [UI (Basic)]
```

### 3.3 각 Squad 산출물

#### Data Squad
```python
# mock_crawler.py
class MockNewsCrawler:
    def get_news(self):
        return {
            "id": "mock-001",
            "title": "삼성전자 반도체 투자 확대",
            "content": "삼성전자가 반도체 생산시설에 10조원을 투자한다고 발표했다.",
            "source": "mock-news",
            "publishedAt": datetime.now().isoformat()
        }
    
    def publish_to_kafka(self):
        # 실제 Kafka에 발행
        producer.send('raw-news', self.get_news())
```

#### ML/NLP Squad
```python
# mock_nlp.py
class MockNLPProcessor:
    def process(self, news):
        # 하드코딩된 NLP 결과 반환
        return {
            "original": news,
            "nlp": {
                "entities": [
                    {"text": "삼성전자", "type": "COMPANY", "id": "mock-samsung"}
                ],
                "sentiment": {"score": 0.8, "label": "positive"},
                "keywords": ["반도체", "투자"]
            }
        }
```

#### Graph Squad
```python
# in_memory_graph.py
class InMemoryGraphDB:
    def __init__(self):
        self.nodes = {}
        self.edges = []
    
    def add_company(self, company_id, name):
        self.nodes[company_id] = {
            "type": "Company",
            "name": name,
            "riskScore": 5.0
        }
    
    def get_company(self, company_id):
        return self.nodes.get(company_id)
```

#### Platform Squad
```yaml
# docker-compose.yml for local development
version: '3.8'
services:
  kafka:
    image: confluentinc/cp-kafka:latest
    environment:
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
  
  zookeeper:
    image: confluentinc/cp-zookeeper:latest
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
```

#### Product Squad
```typescript
// pages/index.tsx
export default function MockDashboard() {
  const [mockData] = useState({
    company: "삼성전자",
    riskScore: 5.0,
    news: ["반도체 투자 확대"]
  });
  
  return (
    <div>
      <h1>RiskRadar Mock Dashboard</h1>
      <p>Company: {mockData.company}</p>
      <p>Risk Score: {mockData.riskScore}</p>
      <p>Latest News: {mockData.news[0]}</p>
    </div>
  );
}
```

### 3.4 통합 테스트 시나리오
```bash
# integration_test.sh
echo "1. Starting mock news generation..."
python mock_crawler.py --generate

echo "2. Checking Kafka message..."
kafka-console-consumer --topic raw-news --from-beginning --max-messages 1

echo "3. Processing through ML pipeline..."
python mock_nlp.py --process

echo "4. Updating graph..."
curl http://localhost:4000/graphql -d '{"query":"{ company(id:\"mock-samsung\") { name riskScore } }"}'

echo "5. Checking UI..."
curl http://localhost:3000 | grep "삼성전자"
```

## 4. Sprint 1: Core Features (Week 2)

### 4.1 목표
실제 기능 구현 시작 - Mock을 실제 구현으로 교체

### 4.2 구현 우선순위
1. **Real Data Flow**: 실제 뉴스 1개 소스
2. **Basic NLP**: 간단한 엔티티 추출
3. **Simple Graph**: 기본 노드/엣지 생성
4. **Real API**: GraphQL 기본 쿼리

### 4.3 각 Squad 목표

#### Data Squad
- 1개 언론사 실제 크롤러
- Kafka 메시지 포맷 확정
- 기본 중복 제거

#### ML/NLP Squad  
- 한국어 형태소 분석
- 회사명 추출 (정규식 기반)
- 감정 분석 (규칙 기반)

#### Graph Squad
- Neo4j 단일 인스턴스
- Company 노드 CRUD
- 기본 인덱스

#### Platform Squad
- Local K8s (Minikube)
- 기본 모니터링 (로그)
- Docker 이미지 빌드

#### Product Squad
- GraphQL 스키마 v0.1
- 기본 인증 (JWT Mock)
- 대시보드 레이아웃

## 5. Sprint 2: Full Integration (Week 3-4)

### 5.1 목표
전체 기능 통합 및 성능 목표 달성

### 5.2 구현 범위
- 5개 언론사 크롤링
- ML 모델 기반 NLP
- 복잡한 그래프 쿼리
- 프로덕션 준비

## 6. 일일 통합 전략

### 6.1 Daily Integration Points
```yaml
09:00 - Daily Standup
  - 통합 이슈 공유
  - 블로킹 포인트 확인

14:00 - Integration Test
  - 자동화된 E2E 테스트 실행
  - 실패 시 즉시 수정

17:00 - Daily Build
  - 모든 서비스 도커 이미지 빌드
  - 통합 환경 배포
```

### 6.2 통합 환경
```
dev-integration/
├── docker-compose.yml    # 로컬 통합 환경
├── k8s/                 # Minikube 환경
│   ├── data-service.yaml
│   ├── ml-service.yaml
│   ├── graph-service.yaml
│   └── product-service.yaml
└── scripts/
    ├── setup.sh         # 환경 설정
    ├── test-e2e.sh      # E2E 테스트
    └── cleanup.sh       # 정리
```

## 7. Mock에서 실제로 전환 계획

### 7.1 점진적 교체
| Component | Sprint 0 (Mock) | Sprint 1 (Partial) | Sprint 2 (Full) |
|-----------|----------------|-------------------|-----------------|
| News Source | Hardcoded JSON | 1 Real Source | 5 Sources |
| NLP | Fixed Results | Regex Based | ML Model |
| Graph DB | In-Memory Map | Neo4j Single | Neo4j Cluster |
| API | Static Response | Basic GraphQL | Full GraphQL |
| UI | Static HTML | React Basic | Full Dashboard |

### 7.2 Feature Flags
```typescript
const features = {
  USE_REAL_NEWS_SOURCE: process.env.SPRINT >= 1,
  USE_ML_NLP: process.env.SPRINT >= 2,
  USE_NEO4J_CLUSTER: process.env.SPRINT >= 2,
  ENABLE_AUTH: process.env.SPRINT >= 1
};
```

## 8. 통합 테스트 자동화

### 8.1 E2E Test Suite
```typescript
describe('RiskRadar E2E Tests', () => {
  it('Sprint 0: Mock data flows through system', async () => {
    // 1. Generate mock news
    await dataService.generateMockNews();
    
    // 2. Wait for processing
    await waitFor(() => mlService.hasProcessed('mock-001'));
    
    // 3. Check graph update
    const company = await graphService.getCompany('mock-samsung');
    expect(company).toBeDefined();
    
    // 4. Verify UI display
    const response = await fetch('http://localhost:3000');
    expect(response.text()).toContain('삼성전자');
  });
  
  it('Sprint 1: Real news processing', async () => {
    // Real crawler test
    await dataService.crawlNews('chosun');
    // ... more assertions
  });
});
```

### 8.2 Health Check Endpoints
각 서비스는 통합 상태를 확인할 수 있는 health check 제공:

```yaml
GET /health
{
  "status": "healthy",
  "version": "sprint-0",
  "dependencies": {
    "kafka": "connected",
    "database": "connected"
  },
  "features": {
    "realData": false,
    "mlEnabled": false
  }
}
```

## 9. 위험 관리

### 9.1 통합 리스크
| Risk | Impact | Mitigation |
|------|--------|------------|
| Kafka 연결 실패 | High | Local Kafka 사용, Fallback 큐 |
| 서비스 간 API 불일치 | Medium | Contract Test, Mock 우선 |
| 성능 저하 | Low | Sprint 2에서 최적화 |

### 9.2 Rollback 전략
- 각 Sprint는 독립적으로 동작 가능
- Feature Flag로 이전 버전 전환
- Git Tag로 Sprint별 버전 관리

## 10. 성공 기준

### Sprint 0 (Week 1)
- [ ] Mock 데이터가 전체 파이프라인 통과
- [ ] 모든 서비스 간 연결 확인
- [ ] 기본 UI에 데이터 표시
- [ ] E2E 테스트 1개 통과

### Sprint 1 (Week 2)
- [ ] 실제 뉴스 1개 소스 처리
- [ ] 기본 NLP 처리 동작
- [ ] Neo4j에 데이터 저장
- [ ] GraphQL 쿼리 동작

### Sprint 2 (Week 3-4)
- [ ] 5개 뉴스 소스 크롤링
- [ ] ML 기반 NLP 처리
- [ ] 복잡한 그래프 쿼리
- [ ] 성능 목표 달성

## 11. 커뮤니케이션

### 11.1 통합 미팅
- **Sprint Planning**: 매주 월요일 오전
- **Daily Sync**: 매일 오후 2시 (15분)
- **Sprint Review**: 매주 금요일 오후

### 11.2 통합 채널
```
#riskradar-integration (Slack)
- 통합 이슈 실시간 공유
- 빌드 상태 알림
- 테스트 결과 공유
```

## 12. 도구 및 환경

### 12.1 개발 환경
```bash
# 로컬 통합 환경 설정
./scripts/setup-integration-env.sh

# 서비스 시작
docker-compose up -d

# 통합 테스트 실행
./scripts/run-integration-tests.sh

# 로그 확인
docker-compose logs -f
```

### 12.2 CI/CD Pipeline
```yaml
stages:
  - build
  - test
  - integrate
  - deploy

integration-test:
  stage: integrate
  script:
    - docker-compose up -d
    - npm run test:e2e
    - docker-compose down
  only:
    - develop
```