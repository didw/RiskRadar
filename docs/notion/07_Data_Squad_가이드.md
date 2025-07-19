# 📊 Data Squad 가이드

## 팀 소개

> **Data Squad**: RiskRadar의 데이터 수집 및 스트리밍 파이프라인 전문팀
> 
> 실시간 뉴스 데이터 수집부터 Kafka 스트리밍까지, 모든 데이터의 시작점을 담당

---

## 👥 팀 구성 및 역할

### 현재 팀 구성 (Phase 1)
- **팀 리더**: Senior Data Engineer
- **팀 규모**: 2명
- **전문 영역**: 웹 크롤링, 데이터 파이프라인, 스트리밍

### Phase 2 확장 계획
- **신규 영입**: Data Engineer (멀티소스 전문)
- **목표 팀 규모**: 4명
- **확장 영역**: 18개 언론사, 공시정보, 소셜미디어

---

## 🎯 핵심 책임 영역

### 1. 웹 크롤링 시스템
```python
# BaseCrawler 아키텍처 확장
class BaseCrawler:
    """모든 크롤러의 기본 클래스"""
    def crawl(self) -> List[NewsItem]
    def process_rate_limit(self)
    def handle_errors(self)
    def validate_data(self)

# 현재 구현: 조선일보
class ChosunCrawler(BaseCrawler):
    rate_limit = "5 requests/second"
    success_rate = ">99%"
    
# Phase 2 확장: 17개 추가
class JoongangCrawler(BaseCrawler): pass
class DongaCrawler(BaseCrawler): pass
# ... 15개 더
```

### 2. Kafka 스트리밍 파이프라인
```yaml
토픽 아키텍처:
  raw-news:
    description: "원시 뉴스 데이터"
    producer: "Data Service"
    consumer: "ML Service"
    
  enriched-news:
    description: "NLP 처리된 뉴스"
    producer: "ML Service"  
    consumer: "Graph Service"
    
  error-news:
    description: "처리 실패 데이터"
    producer: "모든 서비스"
    consumer: "Data Service (재처리)"
```

### 3. 데이터 품질 관리
```python
# 데이터 검증 파이프라인
class DataQualityManager:
    def remove_duplicates(self)      # 중복 제거
    def normalize_text(self)         # 텍스트 정규화
    def validate_structure(self)     # 구조 검증
    def enrich_metadata(self)        # 메타데이터 추가
```

---

## 🏆 Phase 1 주요 성과

### ✅ 완료된 기능
```
크롤링 시스템:
├── ✅ 조선일보 실시간 크롤링 (>99% 성공률)
├── ✅ Rate limiting 및 에러 처리
├── ✅ 중복 제거 알고리즘 (100% 정확도)
├── ✅ 데이터 정규화 파이프라인
└── ✅ Health check 및 모니터링

Kafka 파이프라인:
├── ✅ 실시간 메시지 스트리밍
├── ✅ 메시지 유실 방지 (0% 손실률)
├── ✅ 자동 재처리 로직
├── ✅ 백프레셔 핸들링
└── ✅ 성능 모니터링 (지연시간 <50ms)
```

### 📊 달성 성과 지표
| 항목 | 목표 | 달성 | 상태 |
|------|------|------|------|
| **크롤링 성공률** | 95% | **>99%** | ✅ 4%↑ |
| **데이터 처리량** | 100/day | **1000+/day** | ✅ 10배↑ |
| **Kafka 가용성** | 99% | **100%** | ✅ 완벽 |
| **에러율** | <5% | **0%** | ✅ 무결함 |

---

## 🔧 기술 스택 및 도구

### 현재 기술 스택
```yaml
언어 및 프레임워크:
  - Python 3.11+
  - FastAPI (REST API)
  - Pydantic (데이터 검증)
  - asyncio (비동기 처리)

크롤링 도구:
  - requests (HTTP 클라이언트)
  - BeautifulSoup4 (HTML 파싱)
  - lxml (XML/HTML 파서)
  - fake-useragent (User-Agent 로테이션)

스트리밍:
  - Apache Kafka 3.x
  - kafka-python (Python 클라이언트)
  - avro-python3 (메시지 직렬화)

데이터베이스:
  - Redis (캐싱, 중복 체크)
  - PostgreSQL (메타데이터)

모니터링:
  - Prometheus (메트릭)
  - Grafana (대시보드)
  - 커스텀 Health Check
```

### Phase 2 도구 확장
```yaml
추가 예정:
  - Scrapy (고성능 크롤링)
  - Selenium (JavaScript 페이지)
  - Apache Airflow (워크플로우 관리)
  - Snowflake (데이터 웨어하우스)
  - dbt (데이터 변환)
```

---

## 🚀 개발 워크플로우

### Daily 작업 흐름
```
09:00 - 시스템 상태 확인
├── Kafka 클러스터 헬스체크
├── 크롤링 성공률 확인
├── 에러 로그 리뷰
└── 성능 지표 모니터링

10:00 - 개발 작업
├── 신규 크롤러 개발
├── 데이터 품질 개선
├── 성능 최적화
└── 테스트 코드 작성

14:00 - Integration Sync
├── ML Squad와 데이터 스키마 협의
├── Graph Squad와 메시지 포맷 논의
├── Platform Squad와 인프라 이슈 공유
└── Product Squad와 요구사항 확인

16:00 - 품질 보증
├── 단위 테스트 실행
├── 통합 테스트 검증
├── 성능 벤치마크
└── 데이터 품질 검사
```

### 코드 리뷰 체크리스트
```python
# 크롤러 코드 리뷰 기준
class CrawlerReviewChecklist:
    ✅ Rate limiting 구현 여부
    ✅ 에러 핸들링 (네트워크, 파싱)
    ✅ 로깅 및 모니터링
    ✅ 테스트 코드 작성
    ✅ 성능 최적화 (메모리, 속도)
    ✅ 보안 고려사항 (User-Agent, 프록시)
    ✅ 데이터 검증 로직
    ✅ 문서화 (README, 주석)
```

---

## 📋 현재 작업 및 우선순위

### 진행 중인 작업
```
Sprint 진행 상황:
├── 🔄 크롤링 성능 최적화 (진행중 - 80%)
├── 🔄 Kafka 파티셔닝 전략 개선 (진행중 - 60%)
├── 🔄 데이터 품질 자동화 (진행중 - 70%)
└── 🔄 모니터링 대시보드 구축 (진행중 - 90%)
```

### Phase 2 준비 작업
```
준비 중인 작업:
├── 📋 17개 언론사 크롤러 설계
├── 📋 공시정보 API 연동 방안
├── 📋 소셜미디어 데이터 수집 전략
├── 📋 대용량 처리 아키텍처 설계
└── 📋 Kubernetes 배포 준비
```

---

## 🧪 테스트 전략

### 테스트 피라미드
```
Data Squad 테스트 구조:
├── E2E 테스트 (10%)
│   ├── 전체 데이터 파이프라인 검증
│   └── 다운스트림 서비스 통합 테스트
├── 통합 테스트 (20%)
│   ├── Kafka 메시지 플로우 테스트
│   ├── 데이터베이스 연동 테스트
│   └── 외부 API 연동 테스트
└── 단위 테스트 (70%)
    ├── 크롤러 로직 테스트
    ├── 데이터 변환 테스트
    └── 에러 핸들링 테스트
```

### 자동화된 테스트
```python
# 크롤링 테스트 자동화
@pytest.mark.integration
def test_chosun_crawler():
    crawler = ChosunCrawler()
    articles = crawler.crawl()
    
    assert len(articles) > 0
    assert all(article.title for article in articles)
    assert all(article.content for article in articles)
    assert all(article.published_at for article in articles)

# Kafka 메시지 테스트
@pytest.mark.kafka
def test_kafka_message_flow():
    producer.send('raw-news', test_news_data)
    messages = consumer.poll(timeout_ms=5000)
    
    assert len(messages) == 1
    assert messages[0].value == test_news_data
```

---

## 📊 성능 모니터링

### 핵심 지표 추적
```yaml
크롤링 지표:
  - 성공률: >99% (목표: >95%)
  - 응답시간: <2초 (목표: <5초)
  - 시간당 기사 수: 100+ (목표: 50+)
  - 에러율: 0% (목표: <5%)

Kafka 지표:
  - 메시지 처리량: 1000+ msg/s
  - 지연시간: <50ms (P95)
  - 파티션 밸런스: ±5%
  - 재처리율: <1%

데이터 품질:
  - 중복률: 0% (완벽한 중복 제거)
  - 누락 필드: 0%
  - 스키마 준수율: 100%
  - 정규화 정확도: 100%
```

### 알림 및 대응
```yaml
알림 설정:
  크리티컬:
    - 크롤링 실패율 >5%
    - Kafka 메시지 유실
    - 시스템 다운
    대응: 즉시 알림 + 자동 복구 시도

경고:
    - 응답시간 >5초
    - 메모리 사용률 >80%
    - 디스크 사용률 >85%
    대응: 슬랙 알림 + 모니터링 강화
```

---

## 🛠️ 트러블슈팅 가이드

### 자주 발생하는 이슈

#### 1. 크롤링 실패
```python
문제: HTTP 403/429 에러
원인: Rate limiting 또는 IP 차단
해결:
  1. User-Agent 로테이션 확인
  2. 요청 간격 증가
  3. 프록시 서버 사용
  4. 크롤링 시간 분산

# 구현 예시
class RateLimiter:
    def __init__(self, requests_per_second=2):
        self.min_interval = 1.0 / requests_per_second
        self.last_request = 0
    
    def wait_if_needed(self):
        elapsed = time.time() - self.last_request
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request = time.time()
```

#### 2. Kafka 메시지 유실
```python
문제: 메시지가 Consumer에 도달하지 않음
원인: Producer 설정 문제 또는 네트워크 이슈
해결:
  1. acks='all' 설정 확인
  2. retries 설정 증가
  3. 네트워크 연결 상태 점검
  4. Consumer group 상태 확인

# 안전한 Producer 설정
producer_config = {
    'acks': 'all',
    'retries': 3,
    'retry_backoff_ms': 1000,
    'request_timeout_ms': 30000
}
```

#### 3. 메모리 부족
```python
문제: 크롤링 중 메모리 사용량 급증
원인: 대용량 페이지 또는 메모리 누수
해결:
  1. 스트리밍 파싱 사용
  2. 정기적인 가비지 컬렉션
  3. 배치 크기 조정
  4. 메모리 프로파일링

# 메모리 효율적인 파싱
def parse_large_page(content):
    # 한 번에 모든 내용을 메모리에 로드하지 않음
    soup = BeautifulSoup(content, 'lxml')
    for article in soup.find_all('article'):
        yield parse_article(article)
        article.decompose()  # 메모리 해제
```

---

## 📚 학습 리소스

### 필수 학습 자료
```
웹 크롤링:
├── "Web Scraping with Python" (O'Reilly)
├── Scrapy 공식 문서
├── HTTP 프로토콜 완벽 가이드
└── robots.txt 및 크롤링 윤리

Apache Kafka:
├── "Kafka: The Definitive Guide" (O'Reilly)
├── Confluent Kafka 튜토리얼
├── 실시간 스트리밍 아키텍처 패턴
└── Kafka 성능 튜닝 가이드

데이터 엔지니어링:
├── "Designing Data-Intensive Applications"
├── Apache Airflow 마스터 클래스
├── 데이터 품질 관리 베스트 프랙티스
└── 실시간 데이터 파이프라인 설계
```

### 인증 및 교육
```
추천 인증:
├── AWS Certified Data Engineer
├── Apache Kafka 개발자 인증
├── Python 고급 데이터 처리
└── Kubernetes 애플리케이션 개발자
```

---

## 🎯 커리어 개발 경로

### 스킬 개발 로드맵
```
Junior Data Engineer → Senior Data Engineer:
├── Month 1-3: Python 마스터리
├── Month 4-6: Kafka 전문가
├── Month 7-9: 클라우드 플랫폼 (AWS/GCP)
├── Month 10-12: 분산 시스템 설계
└── Year 2: 팀 리더십 및 아키텍트

전문 분야 선택:
├── 🚀 실시간 스트리밍 전문가
├── 🌐 웹 크롤링 및 API 전문가
├── 🏗️ 데이터 아키텍트
└── 📊 데이터 플랫폼 엔지니어
```

### 성과 평가 기준
```
기술 역량 (50%):
├── 코드 품질 및 테스트 커버리지
├── 시스템 성능 최적화 기여도
├── 새로운 기술 도입 및 적용
└── 문제 해결 능력

협업 및 커뮤니케이션 (30%):
├── 다른 Squad와의 협업 품질
├── 기술 지식 공유 및 문서화
├── 코드 리뷰 참여도
└── 멘토링 및 지식 전파

비즈니스 임팩트 (20%):
├── 데이터 품질 개선 기여도
├── 시스템 안정성 향상
├── 개발 생산성 증대
└── 고객 만족도 개선
```

---

## 🔮 Phase 2 준비사항

### 기술적 준비
```
멀티소스 크롤링:
├── 17개 언론사 API 조사 완료
├── 공시정보 API 연동 방안 설계
├── 소셜미디어 데이터 수집 전략
└── 대용량 처리 아키텍처 설계

인프라 확장:
├── Kubernetes 마이그레이션 계획
├── Kafka 클러스터 스케일링
├── 스토리지 확장 (Data Lake)
└── 모니터링 시스템 고도화
```

### 팀 확장 준비
```
신규 팀원 온보딩:
├── 온보딩 가이드 문서 작성
├── 개발 환경 자동화 스크립트
├── 멘토링 프로그램 설계
└── 코드 리뷰 프로세스 정립
```

---

## 📞 도움이 필요할 때

### 팀 내 연락처
```
팀 리더: @data-lead (Slack)
시니어 엔지니어: @senior-data-eng
DevOps 지원: @platform-squad
긴급 상황: #riskradar-alerts
```

### 외부 리소스
```
기술 지원:
├── Kafka 커뮤니티 포럼
├── Python 데이터 엔지니어링 그룹
├── AWS/GCP 기술 지원
└── Stack Overflow (riskradar 태그)
```

---

*최종 업데이트: 2025-07-19*