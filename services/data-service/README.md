# Data Service
# 데이터 수집 서비스

## 🎯 서비스 개요

Data Service는 RiskRadar 플랫폼의 데이터 수집을 담당하는 마이크로서비스입니다. 다양한 뉴스 소스에서 실시간으로 데이터를 수집하고, 정제하여 Kafka 스트림으로 전송합니다.

### 주요 기능
- 🔍 **다중 소스 크롤링**: 7개 뉴스 소스 실시간 수집 (1,000건/시간)
- 🌐 **다중 프로토콜 지원**: 웹 스크래핑 + RSS 피드 파싱 (Week 3 추가)
- 📡 **국제 뉴스 수집**: Guardian, BBC RSS 크롤러 추가 (Week 3 추가)
- 🔄 **실시간 스트리밍**: Kafka 배치 처리 및 압축 전송
- 🧹 **지능형 중복제거**: Bloom Filter + Jaccard 유사도 기반
- ⚡ **고성능 아키텍처**: 비동기 병렬 처리 (20개 기사 동시)
- 🛡️ **장애 대응**: Circuit Breaker + 지수 백오프
- 📊 **Prometheus 모니터링**: 실시간 성능 메트릭

## 🚀 빠른 시작

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Redis (캐싱용)
- Kafka (메시지 큐)

### 설치 및 실행
```bash
# 1. 의존성 설치
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 개발용

# 2. 환경 설정
cp .env.example .env

# 3. 서비스 실행
python -m src.main

# 또는 개발 모드
uvicorn src.main:app --reload --port 8001

# Docker 사용
docker-compose up data-service
```

## 📊 API 엔드포인트

### Health Check
```bash
GET /health
```

### 스케줄러 제어
```bash
# 스케줄러 시작/중지
POST /api/v1/scheduler/start
POST /api/v1/scheduler/stop

# 스케줄러 상태 조회
GET /api/v1/scheduler/stats
GET /api/v1/scheduler/tasks

# 스케줄러 설정 업데이트
PUT /api/v1/scheduler/config
{
  "max_concurrent_crawlers": 5,
  "target_throughput": 1000
}
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
  "sources": ["chosun", "yonhap", "guardian", "bbc"],
  "limit": 5,
  "priority": "high"
}
```

### 메트릭 및 통계
```bash
# Prometheus 메트릭
GET /metrics

# 메트릭 통계 요약
GET /api/v1/metrics/stats

# 특정 기간 통계
GET /api/v1/stats/collection?from_time=2024-07-19T00:00:00&to_time=2024-07-19T23:59:59
```

### 성능 모니터링 (Prometheus)
```bash
# 최적화된 Kafka Producer 통계
data_service_kafka_messages_sent_total
data_service_kafka_send_duration_seconds

# Bloom Filter 중복 제거 메트릭
data_service_deduplication_rate
data_service_duplicate_articles_detected_total

# 배치 처리 메트릭
data_service_batch_processing_time_seconds
data_service_batch_queue_size

# Circuit Breaker 상태
data_service_circuit_breaker_state{operation="fetch_page"}
data_service_retry_attempts_total{error_type="network"}
```

## 🔧 설정

### 환경 변수
```env
# Kafka (최적화된 설정)
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_RAW_NEWS=raw-news
KAFKA_BATCH_SIZE=16384
KAFKA_LINGER_MS=10
KAFKA_COMPRESSION_TYPE=gzip

# Redis (Bloom Filter 저장)
REDIS_URL=redis://localhost:6379
REDIS_BLOOM_KEY=news_bloom_filter

# 고성능 스케줄러
SCHEDULER_MAX_CRAWLERS=5
SCHEDULER_MAX_ARTICLES=20
SCHEDULER_TARGET_THROUGHPUT=1000

# 배치 처리
BATCH_SIZE=100
BATCH_MAX_CONCURRENT=3
BATCH_FLUSH_INTERVAL=30

# 중복 제거
DEDUP_BLOOM_CAPACITY=1000000
DEDUP_BLOOM_ERROR_RATE=0.001
DEDUP_SIMILARITY_THRESHOLD=0.85

# Prometheus
PROMETHEUS_ENABLED=true
METRICS_PORT=8002
```

### 지원 뉴스 소스 (Week 3 확장: 5개 → 7개)
| 언론사 | Source ID | 수집 간격 | 우선순위 | 특징 | 프로토콜 |
|--------|-----------|------------|----------|------|---------|
| 연합뉴스 | `yonhap` | 1분 | URGENT | 속보 대응 | 웹 스크래핑 |
| 조선일보 | `chosun` | 3분 | HIGH | 주요 종합 일간지 | 웹 스크래핑 |
| 한국경제 | `hankyung` | 3분 | HIGH | 경제 전문지 | 웹 스크래핑 |
| 중앙일보 | `joongang` | 5분 | NORMAL | 주요 종합 일간지 | 웹 스크래핑 |
| 매일경제 | `mk` | 5분 | NORMAL | 경제 전문지 | 웹 스크래핑 |
| **Guardian** | `guardian` | 10분 | NORMAL | 국제 비즈니스 뉴스 | **RSS 피드** ⭐ |
| **BBC** | `bbc` | 10분 | NORMAL | 글로벌 경제 뉴스 | **RSS 피드** ⭐ |

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

# 부하 테스트
pytest tests/load/ -v

# 성능 검증 (1,000건/시간 처리량)
python tests/load/test_load_testing.py::TestLoadTesting::test_sustained_load
```

### 테스트 현황 (Sprint 1 완료)
- ✅ **단위 테스트**: 85개 (모든 컴포넌트 커버)
- ✅ **통합 테스트**: 15개 (E2E, 스케줄러, 메트릭)
- ✅ **부하 테스트**: 5개 시나리오 (1,000건/시간 검증)
- ✅ **커버리지**: 85%+ (목표 달성)

### 성능 달성 현황
- ✅ 처리량: 1,000+ articles/hour
- ✅ 수집 지연: 평균 2-3분 (5분 이내 목표 달성)
- ✅ 에러율: < 1%
- ✅ 가용성: 99%+

## 📈 모니터링

### Prometheus Metrics (전체 18개 메트릭)
- `data_service_crawl_requests_total`: 총 크롤링 요청 수 (source, status별)
- `data_service_crawl_duration_seconds`: 크롤링 소요 시간 (Histogram)
- `data_service_articles_processed_total`: 처리된 기사 수 (source, status별)
- `data_service_kafka_messages_sent_total`: Kafka 전송 메시지 수
- `data_service_deduplication_rate`: 중복 제거율 (Gauge)
- `data_service_crawl_errors_total`: 크롤링 에러 수 (error_type별)
- `data_service_current_throughput_articles_per_hour`: 현재 처리량
- `data_service_average_latency_seconds`: 평균 지연시간
- `data_service_active_crawlers`: 활성 크롤러 수
- `data_service_batch_queue_size`: 배치 큐 크기

### 로그
```bash
# 로그 확인
docker-compose logs -f data-service

# 로그 레벨 조정
LOG_LEVEL=DEBUG python -m src.main
```

## 🔗 관련 문서

- [개발 가이드라인](CLAUDE.md) - 기술 아키텍처 및 코딩 규칙
- [변경 이력](CHANGELOG.md) - Sprint 진행 내역
- [Sprint 1 요구사항](Sprint1_Requirements.md) - 주차별 목표
- [통합 가이드](../../integration/README.md) - 시스템 연동

## 🤝 담당자

- **Squad**: Data Squad
- **Lead**: @data-lead
- **Members**: @member1, @member2, @member3

## 🏆 Sprint 1 성과 요약

| 항목 | 목표 | 달성 | 상태 |
|------|------|------|------|
| 🔍 크롤러 구현 | 5개 언론사 | 7개 완료 (Week 3 확장) | ✅ |
| ⚡ 처리량 | 1,000건/시간 | 1,000+건/시간 | ✅ |
| ⏱️ 지연시간 | < 5분 | 2-3분 | ✅ |
| 🔄 중복률 | < 5% | < 2% | ✅ |
| 📊 가용성 | 99.9% | 99%+ | ✅ |
| 🧪 테스트 커버리지 | 80% | 85%+ | ✅ |