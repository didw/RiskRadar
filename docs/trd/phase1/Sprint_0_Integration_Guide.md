# Sprint 0 통합 가이드
# Walking Skeleton Integration Guide

## 1. 목표

Sprint 0의 핵심은 **"모든 컴포넌트가 연결되어 데이터가 흐르는 것을 확인"**하는 것입니다.

## 2. 시스템 플로우

```
[Mock News Generator]
    ↓ (HTTP POST)
[Data Service :8001]
    ↓ (Kafka: raw-news)
[ML Service :8002]
    ↓ (Kafka: enriched-news)  
[Graph Service :8003]
    ↓ (GraphQL)
[API Gateway :4000]
    ↓ (HTTP/GraphQL)
[Web UI :3000]
```

## 3. 환경 설정

### 3.1 디렉토리 구조
```
riskradar-sprint0/
├── docker-compose.yml
├── services/
│   ├── data-service/
│   │   ├── Dockerfile
│   │   ├── mock_crawler.py
│   │   └── requirements.txt
│   ├── ml-service/
│   │   ├── Dockerfile
│   │   ├── mock_nlp.py
│   │   └── requirements.txt
│   ├── graph-service/
│   │   ├── Dockerfile
│   │   ├── in_memory_graph.py
│   │   └── requirements.txt
│   └── web-ui/
│       ├── Dockerfile
│       ├── package.json
│       └── pages/index.tsx
├── scripts/
│   ├── setup.sh
│   ├── test-e2e.sh
│   └── cleanup.sh
└── tests/
    └── integration_test.py
```

### 3.2 Docker Compose 설정
```yaml
version: '3.8'

services:
  # Infrastructure
  zookeeper:
    image: confluentinc/cp-zookeeper:7.4.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000

  kafka:
    image: confluentinc/cp-kafka:7.4.0
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"

  # Services
  data-service:
    build: ./services/data-service
    ports:
      - "8001:8001"
    environment:
      KAFKA_BOOTSTRAP_SERVERS: kafka:29092
      SERVICE_PORT: 8001
    depends_on:
      - kafka
    volumes:
      - ./services/data-service:/app

  ml-service:
    build: ./services/ml-service
    ports:
      - "8002:8002"
    environment:
      KAFKA_BOOTSTRAP_SERVERS: kafka:29092
      SERVICE_PORT: 8002
    depends_on:
      - kafka
    volumes:
      - ./services/ml-service:/app

  graph-service:
    build: ./services/graph-service
    ports:
      - "8003:8003"
      - "4000:4000"  # GraphQL
    environment:
      KAFKA_BOOTSTRAP_SERVERS: kafka:29092
      SERVICE_PORT: 8003
      GRAPHQL_PORT: 4000
    depends_on:
      - kafka
    volumes:
      - ./services/graph-service:/app

  web-ui:
    build: ./services/web-ui
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_GRAPHQL_URL: http://localhost:4000/graphql
    depends_on:
      - graph-service
    volumes:
      - ./services/web-ui:/app
```

## 4. 서비스별 Mock 구현

### 4.1 Data Service
```python
# services/data-service/mock_crawler.py
from flask import Flask, jsonify
from kafka import KafkaProducer
import json
import uuid
from datetime import datetime

app = Flask(__name__)
producer = KafkaProducer(
    bootstrap_servers=['kafka:29092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "data-service"})

@app.route('/generate-mock-news', methods=['POST'])
def generate_mock_news():
    mock_news = {
        "id": f"mock-{uuid.uuid4()}",
        "title": "삼성전자 반도체 공장 증설 발표",
        "content": "삼성전자가 평택에 새로운 반도체 공장을 건설한다고 발표했습니다.",
        "source": "mock-news",
        "publishedAt": datetime.now().isoformat(),
        "url": "http://mock-news.com/1"
    }
    
    # Kafka로 전송
    producer.send('raw-news', mock_news)
    producer.flush()
    
    return jsonify({
        "success": True,
        "newsId": mock_news["id"],
        "message": "Mock news generated and sent to Kafka"
    })

@app.route('/stats', methods=['GET'])
def stats():
    return jsonify({
        "generated": 1,
        "source": "mock",
        "status": "active"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001)
```

### 4.2 ML Service
```python
# services/ml-service/mock_nlp.py
from flask import Flask, jsonify
from kafka import KafkaConsumer, KafkaProducer
import json
import threading

app = Flask(__name__)

# Kafka setup
consumer = KafkaConsumer(
    'raw-news',
    bootstrap_servers=['kafka:29092'],
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    group_id='ml-service-group'
)

producer = KafkaProducer(
    bootstrap_servers=['kafka:29092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

processed_count = 0

def process_news():
    global processed_count
    for message in consumer:
        news = message.value
        
        # Mock NLP 처리
        enriched = {
            "original": news,
            "nlp": {
                "entities": [
                    {
                        "text": "삼성전자",
                        "type": "COMPANY",
                        "id": "mock-samsung",
                        "confidence": 0.95
                    }
                ],
                "sentiment": {
                    "score": 0.8,
                    "label": "positive"
                },
                "keywords": ["반도체", "공장", "증설"]
            },
            "processedAt": datetime.now().isoformat()
        }
        
        # Enriched 데이터 전송
        producer.send('enriched-news', enriched)
        producer.flush()
        processed_count += 1

# 백그라운드 스레드에서 Kafka 처리
thread = threading.Thread(target=process_news)
thread.daemon = True
thread.start()

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "service": "ml-service",
        "processed": processed_count
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8002)
```

### 4.3 Graph Service
```python
# services/graph-service/in_memory_graph.py
from flask import Flask
from flask_graphql import GraphQLView
import graphene
from kafka import KafkaConsumer
import json
import threading

app = Flask(__name__)

# In-memory storage
companies = {}
news_items = []

# Kafka consumer
consumer = KafkaConsumer(
    'enriched-news',
    bootstrap_servers=['kafka:29092'],
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    group_id='graph-service-group'
)

def consume_enriched_news():
    for message in consumer:
        enriched = message.value
        
        # Extract companies and update
        for entity in enriched['nlp']['entities']:
            if entity['type'] == 'COMPANY':
                company_id = entity['id']
                if company_id not in companies:
                    companies[company_id] = {
                        'id': company_id,
                        'name': entity['text'],
                        'riskScore': 5.0,
                        'newsCount': 0
                    }
                companies[company_id]['newsCount'] += 1
                
        # Store news
        news_items.append({
            'id': enriched['original']['id'],
            'title': enriched['original']['title'],
            'sentiment': enriched['nlp']['sentiment']['score']
        })

# Start consumer thread
thread = threading.Thread(target=consume_enriched_news)
thread.daemon = True
thread.start()

# GraphQL Schema
class Company(graphene.ObjectType):
    id = graphene.String()
    name = graphene.String()
    riskScore = graphene.Float()
    newsCount = graphene.Int()

class News(graphene.ObjectType):
    id = graphene.String()
    title = graphene.String()
    sentiment = graphene.Float()

class Query(graphene.ObjectType):
    company = graphene.Field(Company, id=graphene.String())
    companies = graphene.List(Company)
    recent_news = graphene.List(News, limit=graphene.Int(default_value=10))
    
    def resolve_company(self, info, id):
        return companies.get(id)
    
    def resolve_companies(self, info):
        return list(companies.values())
    
    def resolve_recent_news(self, info, limit):
        return news_items[-limit:]

schema = graphene.Schema(query=Query)

# Routes
@app.route('/health')
def health():
    return {
        "status": "healthy",
        "service": "graph-service",
        "companies": len(companies),
        "news": len(news_items)
    }

# GraphQL endpoint
app.add_url_rule(
    '/graphql',
    view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True)
)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000)
```

### 4.4 Web UI
```typescript
// services/web-ui/pages/index.tsx
import { useState, useEffect } from 'react';

interface Company {
  id: string;
  name: string;
  riskScore: number;
  newsCount: number;
}

export default function MockDashboard() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    // Fetch data from GraphQL
    fetch('http://localhost:4000/graphql', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: `
          query {
            companies {
              id
              name
              riskScore
              newsCount
            }
          }
        `
      })
    })
    .then(res => res.json())
    .then(data => {
      setCompanies(data.data?.companies || []);
      setLoading(false);
    })
    .catch(err => {
      console.error('Failed to fetch:', err);
      setLoading(false);
    });
  }, []);
  
  const generateNews = async () => {
    try {
      const response = await fetch('http://localhost:8001/generate-mock-news', {
        method: 'POST'
      });
      const data = await response.json();
      alert(`News generated: ${data.newsId}`);
      
      // Refresh after 2 seconds
      setTimeout(() => window.location.reload(), 2000);
    } catch (err) {
      alert('Failed to generate news');
    }
  };
  
  return (
    <div style={{ padding: '20px', fontFamily: 'Arial' }}>
      <h1>RiskRadar Sprint 0 - Mock Dashboard</h1>
      
      <button 
        onClick={generateNews}
        style={{
          padding: '10px 20px',
          fontSize: '16px',
          backgroundColor: '#007bff',
          color: 'white',
          border: 'none',
          borderRadius: '5px',
          cursor: 'pointer',
          marginBottom: '20px'
        }}
      >
        Generate Mock News
      </button>
      
      <h2>Companies</h2>
      {loading ? (
        <p>Loading...</p>
      ) : companies.length === 0 ? (
        <p>No companies yet. Click "Generate Mock News" to start!</p>
      ) : (
        <table style={{ borderCollapse: 'collapse', width: '100%' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid #ddd' }}>
              <th style={{ padding: '10px', textAlign: 'left' }}>Company</th>
              <th style={{ padding: '10px', textAlign: 'left' }}>Risk Score</th>
              <th style={{ padding: '10px', textAlign: 'left' }}>News Count</th>
            </tr>
          </thead>
          <tbody>
            {companies.map(company => (
              <tr key={company.id} style={{ borderBottom: '1px solid #ddd' }}>
                <td style={{ padding: '10px' }}>{company.name}</td>
                <td style={{ padding: '10px' }}>{company.riskScore.toFixed(1)}</td>
                <td style={{ padding: '10px' }}>{company.newsCount}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      
      <div style={{ marginTop: '40px', fontSize: '12px', color: '#666' }}>
        <h3>System Status</h3>
        <p>Data Service: http://localhost:8001/health</p>
        <p>ML Service: http://localhost:8002/health</p>
        <p>Graph Service: http://localhost:8003/health</p>
        <p>GraphQL Playground: http://localhost:4000/graphql</p>
      </div>
    </div>
  );
}
```

## 5. 통합 테스트 스크립트

### 5.1 E2E 테스트
```bash
#!/bin/bash
# scripts/test-e2e.sh

echo "=== RiskRadar Sprint 0 E2E Test ==="

# 1. Check all services are healthy
echo "1. Checking service health..."
curl -s http://localhost:8001/health | jq .
curl -s http://localhost:8002/health | jq .
curl -s http://localhost:8003/health | jq .

# 2. Generate mock news
echo -e "\n2. Generating mock news..."
NEWS_RESPONSE=$(curl -s -X POST http://localhost:8001/generate-mock-news)
echo $NEWS_RESPONSE | jq .

# 3. Wait for processing
echo -e "\n3. Waiting for processing..."
sleep 3

# 4. Check ML service processed the news
echo -e "\n4. Checking ML service..."
curl -s http://localhost:8002/health | jq .

# 5. Query GraphQL for companies
echo -e "\n5. Querying companies via GraphQL..."
curl -s http://localhost:4000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ companies { id name riskScore newsCount } }"}' | jq .

# 6. Check if UI is accessible
echo -e "\n6. Checking UI..."
UI_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000)
if [ $UI_STATUS -eq 200 ]; then
    echo "✓ UI is accessible"
else
    echo "✗ UI is not accessible (status: $UI_STATUS)"
fi

echo -e "\n=== Test Complete ==="
```

### 5.2 개발 환경 설정 스크립트
```bash
#!/bin/bash
# scripts/setup.sh

echo "Setting up RiskRadar Sprint 0 environment..."

# 1. Create necessary directories
mkdir -p services/{data-service,ml-service,graph-service,web-ui}

# 2. Create Kafka topics
docker-compose exec kafka kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic raw-news \
  --partitions 3 \
  --replication-factor 1

docker-compose exec kafka kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic enriched-news \
  --partitions 3 \
  --replication-factor 1

# 3. Install dependencies (example for each service)
echo "Installing dependencies..."
# Add pip install, npm install commands as needed

echo "Setup complete!"
```

## 6. 트러블슈팅

### 6.1 일반적인 문제

#### Kafka 연결 실패
```bash
# Kafka 상태 확인
docker-compose logs kafka | tail -20

# Topic 목록 확인
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092
```

#### 서비스 시작 실패
```bash
# 개별 서비스 로그 확인
docker-compose logs data-service
docker-compose logs ml-service
docker-compose logs graph-service

# 포트 충돌 확인
netstat -tulpn | grep -E '(8001|8002|8003|3000|4000)'
```

### 6.2 디버깅 팁

1. **로그 실시간 확인**
```bash
docker-compose logs -f
```

2. **Kafka 메시지 확인**
```bash
# raw-news 토픽 메시지 확인
docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic raw-news \
  --from-beginning

# enriched-news 토픽 메시지 확인
docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic enriched-news \
  --from-beginning
```

3. **GraphQL 쿼리 테스트**
```bash
# GraphQL Playground 접속
open http://localhost:4000/graphql

# 또는 curl로 테스트
curl http://localhost:4000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ companies { name } }"}'
```

## 7. Sprint 0 체크리스트

### 개발 완료
- [ ] Mock 뉴스 생성기 구현
- [ ] Kafka 메시지 발행/구독 동작
- [ ] Mock NLP 처리 완료
- [ ] In-memory 그래프 저장
- [ ] GraphQL 쿼리 동작
- [ ] UI에서 데이터 표시

### 통합 완료
- [ ] 전체 서비스 Docker Compose로 실행
- [ ] E2E 테스트 통과
- [ ] 각 서비스 Health Check 정상
- [ ] 데이터 플로우 확인

### 문서화
- [ ] README 작성
- [ ] API 엔드포인트 문서화
- [ ] 설정 방법 문서화
- [ ] 트러블슈팅 가이드

## 8. 다음 단계 (Sprint 1 준비)

1. **실제 구현 계획**
   - Mock 코드를 실제 구현으로 교체할 부분 식별
   - 필요한 라이브러리 및 의존성 조사

2. **성능 목표 설정**
   - 각 컴포넌트별 처리 시간 목표
   - 시스템 전체 처리량 목표

3. **팀 동기화**
   - Sprint 0 회고
   - Sprint 1 계획 수립
   - 블로킹 이슈 해결