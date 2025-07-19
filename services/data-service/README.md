# Data Service
# 데이터 수집 서비스

## 🎯 서비스 개요

Data Service는 RiskRadar 플랫폼의 데이터 수집을 담당하는 마이크로서비스입니다. 다양한 뉴스 소스에서 실시간으로 데이터를 수집하고, 정제하여 Kafka 스트림으로 전송합니다.

### 주요 기능
- 🔍 **다중 소스 크롤링**: 5개 주요 언론사 뉴스 실시간 수집
- 🔄 **실시간 스트리밍**: Kafka를 통한 데이터 파이프라인
- 🧹 **데이터 정제**: 중복 제거 및 정규화
- ⚡ **고성능 처리**: 비동기 I/O 기반 동시 크롤링
- 🛡️ **안정성**: Rate limiting 및 재시도 메커니즘
- 📊 **모니터링**: 수집 상태 및 통계 제공

## 🚀 빠른 시작

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Redis (캐싱용)

### 설치 및 실행
```bash
# 1. 의존성 설치
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 개발용

# 2. 환경 설정
cp .env.example .env

# 3. 서비스 실행
python -m main

# 또는 개발 모드
uvicorn main:app --reload --port 8001

# Docker 사용
docker-compose up data-service
```

## 📊 API 엔드포인트

### Health Check
```bash
GET /health
```

### 크롤러 상태 관리
```bash
# 전체 크롤러 상태 조회
GET /api/v1/crawler/status

# 특정 크롤러 상태 조회
GET /api/v1/crawler/{source_id}/status

# 특정 크롤러 시작
POST /api/v1/crawler/{source_id}/start

# 특정 크롤러 중지
POST /api/v1/crawler/{source_id}/stop
```

### 수동 크롤링 트리거
```bash
# 전체 소스 크롤링
POST /api/v1/crawl
{
  "limit": 10
}

# 특정 소스 크롤링
POST /api/v1/crawl
{
  "source": "chosun",
  "limit": 5
}
```

### 수집 통계
```bash
# 최근 24시간 통계
GET /api/v1/stats/collection

# 특정 기간 통계
GET /api/v1/stats/collection?from_time=2024-07-19T00:00:00&to_time=2024-07-19T23:59:59
```

### Kafka Producer 모니터링
```bash
# Kafka Producer 통계
GET /kafka/stats

# Kafka 연결 상태
GET /kafka/health
```

### 중복 제거 모니터링
```bash
# 중복 제거 통계
GET /deduplication/stats

# 중복 제거 시스템 상태
GET /deduplication/health
```

### 배치 처리 모니터링
```bash
# 배치 처리 통계
GET /batch/stats

# 배치 큐 상태
GET /batch/queue

# 최근 배치 결과 (기본 10개)
GET /batch/recent?limit=20
```

### 에러 재시도 모니터링
```bash
# 재시도 통계
GET /retry/stats

# Circuit Breaker 상태
GET /retry/circuit-breaker/fetch_page_chosun

# 재시도 통계 초기화
POST /retry/reset-stats
```

## 🔧 설정

### 환경 변수
```env
# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_RAW_NEWS=raw-news

# Redis
REDIS_URL=redis://localhost:6379

# Crawler
CRAWLER_SCHEDULE_MINUTES=5
CRAWLER_TIMEOUT_SECONDS=30
```

### 지원 뉴스 소스
| 언론사 | Source ID | Rate Limit | 특징 |
|--------|-----------|------------|------|
| 조선일보 | `chosun` | 2초/요청 | 주요 종합 일간지 |
| 한국경제 | `hankyung` | 2초/요청 | 경제 전문지 |
| 중앙일보 | `joongang` | 2초/요청 | 주요 종합 일간지 |
| 연합뉴스 | `yonhap` | 3초/요청 | 국가 기간 통신사 |
| 매일경제 | `mk` | 2초/요청 | 경제 전문지 |

## 📝 데이터 포맷

### Output Schema (Kafka)
```json
{
  "id": "unique-news-id",
  "title": "뉴스 제목",
  "content": "뉴스 본문",
  "source": "chosun",
  "url": "https://...",
  "published_at": "2024-01-15T10:00:00Z",
  "crawled_at": "2024-01-15T10:05:00Z",
  "metadata": {
    "category": "경제",
    "reporter": "홍길동",
    "keywords": ["기업", "투자"]
  }
}
```

## 🧪 테스트

```bash
# 단위 테스트
pytest tests/unit/

# 통합 테스트
pytest tests/integration/

# 특정 크롤러 테스트
pytest tests/unit/test_chosun_crawler.py -v

# 커버리지 확인
pytest --cov=src tests/ --cov-report=html
```

### 테스트 현황
- 단위 테스트: 69개 (각 크롤러별 10+ 테스트)
- 통합 테스트: 9개 (전체 크롤러 일관성 검증)
- 커버리지: 80%+

## 📈 모니터링

### Prometheus Metrics
- `news_crawled_total`: 수집된 뉴스 총 개수
- `crawler_errors_total`: 크롤링 에러 수
- `kafka_send_duration_seconds`: Kafka 전송 시간

### 로그
```bash
# 로그 확인
docker-compose logs -f data-service

# 로그 레벨 조정
LOG_LEVEL=DEBUG python -m src.main
```

## 🔗 관련 문서

- [개발 가이드라인](CLAUDE.md)
- [변경 이력](CHANGELOG.md)
- [API 상세 문서](docs/api.md)

## 🤝 담당자

- **Squad**: Data Squad
- **Lead**: @data-lead
- **Members**: @member1, @member2, @member3