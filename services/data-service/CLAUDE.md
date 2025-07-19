# Data Service Development Guidelines
# 데이터 서비스 개발 가이드라인

## 📋 서비스 개요

Data Service는 RiskRadar의 데이터 수집 및 전처리를 담당하는 마이크로서비스입니다. 뉴스, 공시, SNS 등 다양한 소스에서 데이터를 수집하고 Kafka로 스트리밍합니다.

## 🏗️ 프로젝트 구조

```
data-service/
├── src/
│   ├── crawlers/                # 크롤러 구현
│   │   ├── base_crawler.py      # 베이스 크롤러 클래스
│   │   ├── news/                # 뉴스 크롤러
│   │   │   ├── chosun_crawler.py
│   │   │   ├── hankyung_crawler.py
│   │   │   ├── joongang_crawler.py
│   │   │   ├── yonhap_crawler.py
│   │   │   └── mk_crawler.py
│   │   └── disclosure/          # 공시 크롤러 (예정)
│   ├── kafka/                   # Kafka 관련
│   │   ├── producer.py          # (예정)
│   │   └── schemas.py           # 메시지 스키마
│   ├── processors/              # 데이터 전처리 (예정)
│   │   ├── cleaner.py
│   │   ├── validator.py
│   │   └── enricher.py
│   ├── api/                     # REST API (예정)
│   │   ├── routes.py
│   │   └── models.py
│   └── config.py                # 설정
├── tests/                       # 테스트
│   ├── unit/                    # 단위 테스트
│   └── integration/             # 통합 테스트
├── scripts/                     # 유틸리티 스크립트
├── requirements.txt
├── requirements-dev.txt
├── Dockerfile
├── README.md
├── CLAUDE.md                    # 현재 파일
└── CHANGELOG.md
```

## 💻 개발 환경 설정

### Prerequisites
```bash
Python 3.11+
Poetry 또는 pip
Docker
Redis (로컬 개발용)
```

### 설치
```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 환경 변수 설정
cp .env.example .env
```

### 로컬 실행
```bash
# Kafka 시작 (docker-compose 사용)
docker-compose up -d kafka zookeeper

# 서비스 실행
python -m src.main

# 또는 개발 모드
uvicorn src.main:app --reload --port 8001
```

## 🔧 주요 컴포넌트

### 1. Crawler Base Class
```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseCrawler(ABC):
    """모든 크롤러의 베이스 클래스"""
    
    def __init__(self, source_id: str, base_url: str, 
                 rate_limit: float = 1.0, timeout: int = 30,
                 max_retries: int = 3):
        self.source_id = source_id
        self.base_url = base_url
        self.rate_limiter = RateLimiter(requests_per_second=rate_limit)
        self.max_retries = max_retries
        # ... 기타 설정
    
    @abstractmethod
    async def fetch_article_list(self) -> List[str]:
        """기사 URL 목록 수집 - 구현 필요"""
        pass
    
    @abstractmethod
    async def parse_article(self, url: str, html: str) -> Dict[str, Any]:
        """기사 내용 파싱 - 구현 필요"""
        pass
    
    async def fetch_articles(self, max_articles: Optional[int] = None) -> List[Dict[str, Any]]:
        """메인 크롤링 메서드 - 공통 로직 구현"""
        # URL 수집 → 검증 → 개별 크롤링 → 정규화
```

### 2. Kafka Producer
```python
class NewsProducer:
    """뉴스 데이터를 Kafka로 전송"""
    
    def __init__(self):
        self.producer = KafkaProducer(
            bootstrap_servers=KAFKA_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
    
    async def send_news(self, news_data: NewsModel):
        """뉴스 데이터 전송"""
        try:
            future = self.producer.send('raw-news', news_data.dict())
            await future
        except Exception as e:
            logger.error(f"Failed to send news: {e}")
            raise
```

### 3. Data Models
```python
from pydantic import BaseModel, Field
from datetime import datetime

class NewsModel(BaseModel):
    """뉴스 데이터 모델"""
    id: str = Field(..., description="고유 ID")
    title: str = Field(..., description="제목")
    content: str = Field(..., description="본문")
    source: str = Field(..., description="출처")
    url: str = Field(..., description="원본 URL")
    published_at: datetime = Field(..., description="발행일시")
    crawled_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

## 📝 코딩 규칙

### 1. 크롤러 구현
- 모든 크롤러는 `BaseCrawler`를 상속
- 비동기 처리 사용 (`async/await`)
- Rate limiting 준수
- User-Agent 설정 필수
- 에러 처리 및 재시도 로직 구현

### 2. 데이터 검증
- Pydantic 모델 사용
- 필수 필드 검증
- URL 정규화
- 중복 제거 (URL 기반)

### 3. 에러 처리
```python
try:
    articles = await crawler.fetch_articles()
except RateLimitError:
    await asyncio.sleep(60)
    # 재시도
except NetworkError as e:
    logger.error(f"Network error: {e}")
    # 알림 전송
except Exception as e:
    logger.exception("Unexpected error")
    # 모니터링 시스템에 알림
```

### 4. 로깅
```python
import structlog

logger = structlog.get_logger()

# 구조화된 로깅 사용
logger.info("article_crawled", 
    source=source_id,
    url=article_url,
    title=article_title,
    timestamp=datetime.now()
)
```

## 🧪 테스트

### 단위 테스트
```bash
pytest tests/unit/
```

### 통합 테스트
```bash
pytest tests/integration/
```

### 테스트 작성 규칙
```python
class TestChosunCrawler:
    @pytest.fixture
    def crawler(self):
        return ChosunCrawler()
    
    async def test_fetch_articles(self, crawler, mock_response):
        # Given
        mock_response.return_value = sample_html
        
        # When
        articles = await crawler.fetch_articles()
        
        # Then
        assert len(articles) > 0
        assert all('title' in a for a in articles)
```

## 🚀 배포

### Docker 빌드
```bash
docker build -t riskradar/data-service:latest .
```

### 환경 변수
```env
# Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_TOPIC_RAW_NEWS=raw-news

# Redis
REDIS_URL=redis://redis:6379

# Crawler 설정
CRAWLER_USER_AGENT="RiskRadar/1.0"
CRAWLER_TIMEOUT=30
CRAWLER_MAX_RETRIES=3

# API
API_PORT=8001
API_WORKERS=4
```

## 📊 모니터링

### Health Check
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "kafka": check_kafka_connection(),
        "redis": check_redis_connection()
    }
```

### Metrics
- 크롤링된 기사 수/시간
- 크롤링 실패율
- Kafka 전송 지연시간
- API 응답 시간

## 🔒 보안

### 크롤링 윤리
- robots.txt 준수
- 적절한 딜레이 설정
- 서버 부하 최소화
- 저작권 고려

### API 보안
- Rate limiting
- API key 인증
- Input validation
- SQL injection 방지

## 🤝 협업

### 다른 서비스와의 인터페이스
- **Output**: Kafka topic `raw-news`
- **Schema**: [NewsModel](#3-data-models)
- **Format**: JSON
- **Encoding**: UTF-8

### 의존성
- ML Service가 `raw-news` 토픽 구독
- Graph Service가 처리 결과 저장

## 🐛 트러블슈팅

### 일반적인 문제

#### 1. Kafka 연결 실패
```bash
# Kafka 상태 확인
docker-compose ps kafka

# 토픽 목록 확인
kafka-topics --list --bootstrap-server localhost:9092
```

#### 2. 크롤링 차단
- User-Agent 확인
- IP 차단 여부 확인
- Rate limit 조정

#### 3. 메모리 누수
- 크롤러 객체 재사용
- 연결 풀 관리
- 가비지 컬렉션 모니터링

## 📚 참고 자료

- [Apache Kafka Python Client](https://kafka-python.readthedocs.io/)
- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://pydantic-docs.helpmanual.io/)

## 🎯 Sprint 개발 가이드

현재 Sprint의 상세 요구사항은 다음 문서를 참고하세요:
- [Sprint 1 Requirements](./Sprint1_Requirements.md) - Week별 구현 목표
- [Sprint Breakdown](../../docs/trd/phase1/Sprint_Breakdown.md) - 전체 Sprint 계획

### 개발 우선순위
1. ~~베이스 크롤러 클래스 구현~~ ✅ 완료 (Week 1)
2. ~~5개 주요 언론사 크롤러 구현~~ ✅ 완료 (Week 2)
   - 조선일보 (ChosunCrawler)
   - 한국경제 (HankyungCrawler)
   - 중앙일보 (JoongangCrawler)
   - 연합뉴스 (YonhapCrawler)
   - 매일경제 (MKCrawler)
3. ~~통합 테스트 작성~~ ✅ 완료 (Week 2)
4. Kafka Producer 구현 (Week 3)
5. Bloom Filter 기반 중복 제거 (Week 3)
6. 배치 처리 및 스케줄러 구현 (Week 3)

## 📁 프로젝트 문서

### 핵심 문서
- [Data Squad TRD](../../docs/trd/phase1/TRD_Data_Squad_P1.md) - 기술 명세
- [API 표준](../../docs/trd/common/API_Standards.md) - API 설계
- [데이터 모델](../../docs/trd/common/Data_Models.md) - 공통 구조

### 연관 서비스
- [ML Service](../ml-service/CLAUDE.md) - Kafka 메시지 수신
- [Graph Service](../graph-service/CLAUDE.md) - 처리된 데이터 저장
- [통합 가이드](../../integration/README.md) - 시스템 통합