# Technical Requirements Document
# Data Squad - Phase 1

## 1. 개요

### 1.1 문서 정보
- **Squad**: Data Squad
- **Phase**: 1 (Week 1-4)
- **작성일**: 2024-07-19
- **버전**: 1.0

### 1.2 범위
실시간 데이터 수집 파이프라인 구축 및 기본 ETL 프로세스 구현

### 1.3 관련 문서
- PRD: [PRD.md](../../prd/PRD.md)
- Architecture: [PRD_Tech_Architecture.md](../../prd/PRD_Tech_Architecture.md)
- 의존 TRD: Platform Squad (Kafka 인프라)

## 2. 기술 요구사항

### 2.1 기능 요구사항
| ID | 기능명 | 설명 | 우선순위 | PRD 참조 |
|----|--------|------|----------|----------|
| F001 | 뉴스 크롤러 | Tier 1 언론사 5개 실시간 크롤링 | P0 | FR-001 |
| F002 | Kafka Producer | 수집 데이터 스트리밍 | P0 | FR-001 |
| F003 | 데이터 정규화 | 통일된 JSON 포맷 변환 | P0 | FR-001 |
| F004 | 중복 제거 | URL/제목 기반 중복 필터링 | P0 | FR-001 |
| F005 | 신뢰도 평가 | 소스별 신뢰도 점수 부여 | P1 | FR-001 |

### 2.2 비기능 요구사항
| 항목 | 요구사항 | 측정 방법 |
|------|----------|-----------|
| 성능 | 시간당 1,000건 이상 처리 | 처리량 모니터링 |
| 확장성 | 언론사별 독립 스케일링 | 크롤러 인스턴스 수 |
| 신뢰성 | 실패 시 자동 재시도 (3회) | 에러 로그 분석 |
| 지연시간 | 발행 후 5분 내 수집 | 타임스탬프 비교 |

## 3. 시스템 아키텍처

### 3.1 컴포넌트 다이어그램
```
┌─────────────────────────────────────────────────────┐
│                   News Sources                       │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │
│  │조선일보 │ │한국경제 │ │ 중앙일보│ │연합뉴스 │  │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘  │
└───────┼───────────┼───────────┼───────────┼────────┘
        │           │           │           │
        ▼           ▼           ▼           ▼
┌─────────────────────────────────────────────────────┐
│                 Crawler Service                      │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │
│  │Crawler-1│ │Crawler-2│ │Crawler-3│ │Crawler-4│  │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘  │
└───────┼───────────┼───────────┼───────────┼────────┘
        └───────────┴───────────┴───────────┘
                        │
                        ▼
                ┌──────────────┐
                │ Normalizer   │
                │ & Deduper    │
                └──────┬───────┘
                       │
                       ▼
                ┌──────────────┐
                │Kafka Producer│
                └──────┬───────┘
                       │
                       ▼
                ┌──────────────┐
                │ Kafka Topic: │
                │ raw-news     │
                └──────────────┘
```

### 3.2 데이터 플로우
1. **수집**: 각 크롤러가 RSS/API를 통해 뉴스 수집
2. **정규화**: 통일된 형식으로 변환
3. **중복 제거**: Redis 기반 Bloom Filter 적용
4. **스트리밍**: Kafka로 실시간 전송

## 4. 상세 설계

### 4.1 API 명세

#### 4.1.1 크롤러 상태 API
```yaml
endpoint: /api/v1/crawler/status
method: GET
response:
  type: object
  properties:
    crawlers:
      type: array
      items:
        type: object
        properties:
          id: string
          source: string
          status: enum [running, stopped, error]
          lastCrawl: datetime
          itemsCollected: integer
          errorCount: integer
```

#### 4.1.2 수집 통계 API
```yaml
endpoint: /api/v1/stats/collection
method: GET
parameters:
  - name: from
    type: datetime
    required: false
  - name: to
    type: datetime
    required: false
response:
  type: object
  properties:
    totalItems: integer
    bySource: object
    byHour: array
    duplicateRate: float
```

### 4.2 데이터 모델

#### 4.2.1 Raw News Format
```json
{
  "id": "uuid",
  "source": {
    "name": "조선일보",
    "tier": 1,
    "url": "https://..."
  },
  "article": {
    "title": "string",
    "content": "string",
    "summary": "string",
    "publishedAt": "2024-07-19T10:00:00Z",
    "author": "string",
    "category": "경제",
    "tags": ["array"],
    "url": "string"
  },
  "metadata": {
    "crawledAt": "2024-07-19T10:05:00Z",
    "crawlerId": "crawler-1",
    "reliability": 0.95,
    "hash": "sha256"
  }
}
```

#### 4.2.2 Kafka Message Format
```json
{
  "version": "1.0",
  "timestamp": "2024-07-19T10:05:00Z",
  "type": "news.raw",
  "payload": {
    // Raw News Format
  },
  "headers": {
    "source": "chosun",
    "contentType": "application/json",
    "messageId": "uuid"
  }
}
```

### 4.3 핵심 알고리즘

#### 4.3.1 중복 제거 알고리즘
```python
class DuplicateDetector:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.bloom_filter = BloomFilter(
            capacity=1000000,
            error_rate=0.001
        )
    
    def is_duplicate(self, article):
        # URL 기반 체크
        url_hash = hashlib.sha256(article.url.encode()).hexdigest()
        if self.bloom_filter.contains(url_hash):
            return True
        
        # 제목 유사도 체크 (Jaccard similarity)
        title_hash = self._generate_shingle_hash(article.title)
        similar = self.redis.smembers(f"shingle:{title_hash[:8]}")
        
        for existing in similar:
            if self._jaccard_similarity(title_hash, existing) > 0.8:
                return True
        
        # 새 아티클로 등록
        self.bloom_filter.add(url_hash)
        self.redis.sadd(f"shingle:{title_hash[:8]}", title_hash)
        return False
```

#### 4.3.2 크롤링 스케줄러
```python
class CrawlerScheduler:
    def __init__(self):
        self.sources = {
            "chosun": {"interval": 300, "priority": 1},
            "hankyung": {"interval": 300, "priority": 1},
            "joongang": {"interval": 600, "priority": 2},
            "yonhap": {"interval": 180, "priority": 1},
            "maeil": {"interval": 600, "priority": 2}
        }
    
    async def schedule(self):
        tasks = []
        for source, config in self.sources.items():
            task = asyncio.create_task(
                self._crawl_periodically(source, config)
            )
            tasks.append(task)
        await asyncio.gather(*tasks)
```

## 5. 기술 스택

### 5.1 사용 기술
- **언어**: Python 3.11+
- **프레임워크**: 
  - Scrapy 2.11 (크롤링)
  - FastAPI (API 서버)
  - aiokafka (Kafka 클라이언트)
- **라이브러리**:
  - BeautifulSoup4 (HTML 파싱)
  - newspaper3k (기사 추출)
  - redis-py (캐싱)
  - prometheus-client (메트릭)
- **도구**:
  - Docker (컨테이너화)
  - Poetry (의존성 관리)

### 5.2 인프라 요구사항
- **컴퓨팅**: 
  - 크롤러: 2 vCPU, 4GB RAM × 5 인스턴스
  - API 서버: 2 vCPU, 4GB RAM × 2 인스턴스
- **스토리지**: 
  - Redis: 2GB (중복 제거용)
  - 로그: 100GB/월
- **네트워크**: 
  - Outbound: 10Mbps (크롤링)
  - Kafka 연결: 내부 네트워크

## 6. 구현 계획

### 6.1 마일스톤
| 주차 | 목표 | 산출물 |
|------|------|--------|
| Week 1 | 크롤러 프레임워크 구축 | 기본 크롤러 1개 동작 |
| Week 2 | 5개 언론사 크롤러 구현 | 모든 크롤러 완성 |
| Week 3 | Kafka 연동 및 중복 제거 | 파이프라인 통합 |
| Week 4 | 모니터링 및 최적화 | 성능 목표 달성 |

### 6.2 리스크 및 대응
| 리스크 | 영향도 | 대응 방안 |
|--------|--------|-----------|
| 언론사 크롤링 차단 | High | User-Agent 로테이션, IP 프록시 |
| 데이터 포맷 변경 | Medium | 파서 버전 관리, 알림 시스템 |
| Kafka 처리 지연 | Medium | 배치 크기 조정, 파티션 증가 |

## 7. 테스트 계획

### 7.1 단위 테스트
- **커버리지 목표**: 80%
- **주요 테스트 케이스**:
  - 각 언론사별 파서 정확도
  - 중복 감지 알고리즘
  - 데이터 정규화 로직
  - Kafka 메시지 직렬화

### 7.2 통합 테스트
- **크롤러 → Kafka**: 메시지 전달 확인
- **부하 테스트**: 시간당 2,000건 처리
- **장애 복구**: 크롤러 재시작 시나리오

## 8. 완료 기준

### 8.1 기능 완료 기준
- [x] 5개 언론사 크롤러 구현
- [x] 시간당 1,000건 이상 수집
- [x] 중복률 5% 미만
- [x] Kafka 전송 성공률 99%

### 8.2 성능 완료 기준
- [x] 발행 후 5분 내 수집
- [x] 크롤러 가용성 95% 이상
- [x] 메모리 사용량 4GB 이내

## 9. 의존성

### 9.1 외부 의존성
- **Platform Squad**: Kafka 클러스터 구축 완료
- **ML/NLP Squad**: 데이터 포맷 합의

### 9.2 내부 의존성
- Redis 설치 및 설정
- 네트워크 프록시 구성

## 10. 부록

### 10.1 용어 정의
| 용어 | 설명 |
|------|------|
| Tier 1 언론사 | 주요 전국 일간지 (조선, 중앙, 한경 등) |
| Bloom Filter | 확률적 자료구조, 중복 체크용 |
| Shingle | 텍스트 유사도 비교를 위한 n-gram |

### 10.2 참고 자료
- [Scrapy Documentation](https://docs.scrapy.org/)
- [Kafka Best Practices](https://kafka.apache.org/documentation/)
- [뉴스 크롤링 법적 가이드라인]()