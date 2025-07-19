# Data Service Changelog
# 데이터 서비스 변경 이력

## [Unreleased]

### 🚀 Planned
- 실시간 크롤링 스케줄러
- Prometheus 메트릭 추가
- 성능 최적화 (1,000건/시간)

## [0.4.0] - 2025-07-19

### Sprint 1 Week 3: Kafka 통합 및 중복 제거

#### 🚀 Added
- **최적화된 Kafka Producer** (`src/kafka/producer.py`)
  - 배치 처리 (100건 단위)
  - gzip 압축으로 네트워크 효율성 향상
  - 비동기 전송 및 백그라운드 배치 처리
  - 성능 모니터링 및 통계 수집
  - Circuit breaker 패턴 적용

- **Bloom Filter 기반 중복 제거** (`src/processors/deduplicator.py`)
  - URL 기반 중복 탐지 (SHA256 해시)
  - 제목 유사도 기반 중복 탐지 (Jaccard similarity)
  - Redis 영구 저장 (선택사항)
  - 메모리 전용 모드 지원
  - 80% 이상 유사도 시 중복 판정

- **배치 처리 시스템** (`src/processors/batch_processor.py`)
  - 100건 단위 배치 처리
  - 우선순위 큐 (연합뉴스 최우선)
  - 동시성 제어 (최대 3개 배치)
  - 처리 상태 추적 및 통계
  - 타임아웃 및 에러 처리

- **고급 에러 재시도 메커니즘** (`src/processors/retry_manager.py`)
  - 지수 백오프 + Jitter
  - 에러 타입별 재시도 정책
  - Circuit Breaker 패턴
  - 자동 에러 분류 시스템
  - Rate limit 특별 처리

#### 🔧 Enhanced
- **크롤링 파이프라인 개선**
  - 중복 제거 통합으로 데이터 품질 향상
  - 배치 처리로 처리량 대폭 증가
  - Kafka 배치 전송으로 네트워크 효율성 개선
  - 소스별 우선순위 적용

- **BaseCrawler 기능 강화**
  - `to_kafka_message()` 메서드 추가
  - 데이터 정규화 개선
  - 재시도 메커니즘 통합

#### 📊 API Endpoints
- **Kafka 모니터링**
  - `GET /kafka/stats` - Producer 통계
  - `GET /kafka/health` - 연결 상태

- **중복 제거 모니터링**
  - `GET /deduplication/stats` - 중복 제거 통계
  - `GET /deduplication/health` - 시스템 상태

- **배치 처리 모니터링**
  - `GET /batch/stats` - 배치 처리 통계
  - `GET /batch/queue` - 큐 상태
  - `GET /batch/recent` - 최근 배치 결과

- **재시도 메커니즘 모니터링**
  - `GET /retry/stats` - 재시도 통계
  - `GET /retry/circuit-breaker/{operation}` - Circuit breaker 상태
  - `POST /retry/reset-stats` - 통계 초기화

#### 🧪 Testing
- **Kafka Producer 테스트**
  - 37개 단위 테스트 (모킹 기반)
  - 배치 처리 플로우 검증
  - 설정 및 메시지 변환 테스트

#### ⚡ Performance
- **처리량 개선**
  - 개별 처리 → 100건 배치 처리
  - 압축으로 네트워크 사용량 감소
  - 동시성 제어로 안정성 확보

- **중복 제거 효율성**
  - Bloom Filter로 O(1) URL 중복 검사
  - 제목 유사도로 정교한 중복 탐지
  - 최대 5% 중복률 목표

#### 🔧 Changed
- `execute_crawling()` 배치 처리 적용
- API 응답에 더 많은 통계 정보 포함
- 에러 처리 로직 표준화

#### 📝 Documentation
- 각 시스템별 상세 주석 추가
- API 엔드포인트 문서화
- 설정 파라미터 설명

## [0.3.1] - 2025-07-19

### Sprint 1 Week 2: API 엔드포인트 구현

#### 🚀 Added
- **REST API 엔드포인트 구현** (`src/api/`)
  - `/api/v1/crawl` - 수동 크롤링 트리거 (통합 테스트 리뷰 반영)
  - `/api/v1/crawler/status` - 크롤러 상태 조회
  - `/api/v1/crawler/{source_id}/start` - 특정 크롤러 시작
  - `/api/v1/crawler/{source_id}/stop` - 특정 크롤러 중지
  - `/api/v1/stats/collection` - 수집 통계 조회

- **API 데이터 모델** (`src/api/models.py`)
  - `CrawlerStatusResponse` - 크롤러 상태 응답
  - `CrawlRequest/Response` - 크롤링 요청/응답
  - `CollectionStatsResponse` - 수집 통계 응답
  - Pydantic 기반 타입 안전성 보장

- **백그라운드 태스크 처리**
  - FastAPI BackgroundTasks 활용
  - 비동기 크롤링 실행
  - 실시간 상태 업데이트

#### 🧪 Testing
- **API 테스트 추가** (`tests/unit/test_api_routes.py`)
  - 17개 API 엔드포인트 테스트
  - FastAPI TestClient 기반
  - Mock을 활용한 격리된 테스트

#### 🔧 Changed
- FastAPI 버전 업데이트 (0.1.0 → 0.3.1)
- API 라우터 통합
- python-dateutil 의존성 추가

#### 📝 Documentation
- TRD 요구사항 대비 100% 구현 완료
- 통합 테스트 리뷰 이슈 해결

## [0.3.0] - 2025-07-19

### Sprint 1 Week 2: 5개 언론사 크롤러 구현

#### 🚀 Added
- **4개 추가 언론사 크롤러 구현**
  - 한국경제 크롤러 (hankyung_crawler.py)
  - 중앙일보 크롤러 (joongang_crawler.py)
  - 연합뉴스 크롤러 (yonhap_crawler.py)
  - 매일경제 크롤러 (mk_crawler.py)

- **크롤러별 특화 기능**
  - 언론사별 URL 패턴 대응
  - 다양한 날짜 형식 파싱 (dateutil 활용)
  - 언론사별 선택자 패턴 중앙화
  - 연합뉴스 AKR ID 체계 지원

- **공통 개선사항**
  - Exponential backoff 재시도 로직
  - HTTP 429 (Rate Limited) 대응
  - 데이터 검증 강화 (제목 길이, 컨텐츠 길이)
  - URL 유효성 검증 메서드
  - 50% 실패시 크롤링 중단 로직

#### 🧪 Testing
- **단위 테스트 추가**
  - 각 크롤러별 10+ 단위 테스트
  - 날짜 파싱 테스트
  - 컨텐츠 정제 테스트
  - 에러 처리 테스트

- **통합 테스트 작성**
  - 9개 통합 테스트로 전체 크롤러 일관성 검증
  - 동시 크롤링 시뮬레이션
  - Rate limiting 설정 검증
  - 데이터 정규화 일관성 확인

#### 📝 Documentation
- CLAUDE.md 프로젝트 구조 업데이트
- README.md 크롤러 정보 추가
- 각 크롤러별 상세 주석

#### 🔧 Changed
- BaseCrawler에 max_retries 파라미터 추가
- User-Agent에 봇 정보 URL 추가
- 이미지 크기 필터링 로직 개선
- 연합뉴스 더 엄격한 rate limit (3초)

#### 🐛 Fixed
- 날짜 파싱 타임존 처리
- 중복 컨텐츠 제거 로직
- 작은 이미지 스킵 기능

## [0.2.0] - 2024-01-17

### Sprint 1 Week 1: 실제 크롤러 구현

#### 🚀 Added
- **BaseCrawler 추상 클래스** (base_crawler.py)
  - 비동기 HTTP 클라이언트 (aiohttp)
  - Rate limiting 시스템 (RateLimiter)
  - 에러 처리 및 재시도 로직
  - URL 정규화 및 검증
  - 기사 데이터 표준화

- **조선일보 크롤러** (chosun_crawler.py)
  - 6개 섹션 크롤링 (경제, 사회, 국제, 정치, IT, 문화)
  - 기사 URL 추출 및 필터링
  - 제목, 본문, 저자, 카테고리, 이미지 추출
  - 한국어 날짜 파싱
  - 메타데이터 추출

- **Kafka Producer 통합**
  - 실제 뉴스 데이터 발송 성공
  - 표준화된 뉴스 스키마
  - 에러 처리 및 로깅

#### 🧪 Testing
- **단위 테스트** (test_base_crawler.py)
  - BaseCrawler 모든 메서드 테스트
  - RateLimiter 동작 검증
  - URL 정규화 테스트
  - 기사 ID 생성 테스트
  - 에러 처리 시나리오 테스트

- **통합 테스트 성공**
  - 실제 조선일보 사이트 크롤링
  - Kafka 메시지 발송 검증
  - ML Service와 데이터 플로우 확인

#### 📝 Documentation
- CLAUDE.md 업데이트 (개발 가이드라인)
- Sprint1_Requirements.md 작성
- 코드 주석 및 docstring 추가

#### 🔧 Changed
- Mock 구현을 실제 크롤러로 완전 교체
- 에러 처리 로직 강화
- 로깅 시스템 개선

## [0.1.0] - 2024-01-15

### Sprint 0: Mock Implementation

#### 🚀 Added
- Mock 뉴스 생성기 구현
  - 하드코딩된 샘플 뉴스 데이터
  - `/generate-mock-news` 엔드포인트
- Kafka Producer 설정
  - `raw-news` 토픽으로 메시지 발행
  - JSON 직렬화
- Health Check 엔드포인트
  - 서비스 상태 확인
  - Kafka 연결 상태
- 기본 통계 API
  - `/stats` 엔드포인트
  - Mock 데이터 생성 횟수

#### 🧪 Testing
- Mock 데이터 생성 테스트
- Kafka 메시지 발행 검증

#### 📚 Documentation
- README.md 작성
- CLAUDE.md 개발 가이드라인
- API 문서 초안

## [0.0.1] - 2024-01-01

### 프로젝트 초기화

#### 🚀 Added
- 서비스 디렉토리 구조 생성
- 기본 Python 프로젝트 설정
- requirements.txt 작성
- Dockerfile 초안

---

## 다음 릴리스 계획

### v0.3.0 (Sprint 1 Week 2) - ✅ Completed
- ✅ 한국경제 크롤러 구현
- ✅ 중앙일보 크롤러 구현
- ✅ 연합뉴스 크롤러 구현
- ✅ 매일경제 크롤러 구현
- ✅ 통합 테스트 작성

### v0.4.0 (Sprint 1 Week 3)
- [ ] Kafka Producer 최적화
- [ ] Bloom Filter 기반 중복 제거
- [ ] 배치 처리 구현 (100건 단위)
- [ ] 에러 재시도 메커니즘
- [ ] 처리량 1,000건/시간 달성

### v0.5.0 (Sprint 1 Week 4)
- [ ] 발행 후 5분 내 수집 달성
- [ ] Prometheus 메트릭 추가
- [ ] 통합 테스트 강화
- [ ] 성능 최적화
- [ ] 모니터링 대시보드

---

## 성과 지표

### Sprint 1 Week 1 달성도: 100%
- ✅ 조선일보 크롤러 완전 구현
- ✅ 실제 데이터 크롤링 및 Kafka 발송 성공
- ✅ 단위 테스트 및 통합 테스트 통과
- ✅ 에러율 0% 달성

### Sprint 1 Week 2 달성도: 100%
- ✅ 5개 언론사 크롤러 모두 구현
- ✅ 각 크롤러별 10+ 단위 테스트 작성
- ✅ 통합 테스트로 일관성 검증
- ✅ 테스트 커버리지 80%+ 달성
- ✅ 문서화 완료