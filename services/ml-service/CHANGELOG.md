# ML Service Changelog
# ML/NLP 서비스 변경 이력

## [1.0.0] - 2024-07-19

### Week 1 Sprint 1: 기본 NLP 파이프라인 구축

#### 🚀 Added
- **Korean Text Processing Pipeline**
  - TextNormalizer: URL/이메일 제거, 텍스트 정규화
  - SimpleTokenizer: 기본 토큰화 (Java 미설치 환경용)
  - KoreanTokenizer: KoNLPy 래퍼 (Mecab, Komoran, Hannanum 지원)
- **NLP Processing Pipeline**
  - 비동기 텍스트 처리 파이프라인
  - Mock 엔티티 추출 (COMPANY, PERSON, EVENT)
  - 규칙 기반 감정 분석 (positive/neutral/negative)
  - TF-IDF 키워드 추출
  - 리스크 점수 계산
- **Mock Kafka Integration**
  - MockKafkaConsumer: 샘플 데이터 처리
  - MockKafkaProducer: 결과 저장
  - 실제 Kafka 준비 완료
- **REST API Endpoints**
  - `POST /api/v1/process`: 단일 텍스트 처리
  - `POST /api/v1/batch`: 배치 처리
  - `GET /api/v1/health`: 상태 확인
  - `GET /api/v1/model/info`: 모델 정보
- **Testing Infrastructure**
  - 단위 테스트 (tokenizer, normalizer, pipeline)
  - Pytest + pytest-asyncio
  - 테스트 커버리지 확보
- **Configuration Management**
  - pydantic-settings 기반 설정
  - 환경별 설정 지원 (.env)
  - Mock/Production 모드 전환

#### 🧪 Testing
- 19개 테스트 통과 (일부 KoNLPy 테스트는 Java 의존성으로 스킵)
- API 엔드포인트 정상 작동 확인
- Mock 데이터 처리 성공

#### 📚 Documentation
- CLAUDE.md 업데이트 (Week 1 완료 내용 반영)
- 상세한 설치/실행 가이드
- API 사용법 문서화

#### 🔧 Changed
- main.py를 src/main.py로 모듈화
- FastAPI lifespan 이벤트 활용
- 비동기 처리 구조로 전환

## [0.1.0] - 2024-01-15

### Sprint 0: Mock Implementation

#### 🚀 Added
- Mock NLP 프로세서 구현
  - 하드코딩된 엔티티 추출
  - 고정된 감정 분석 결과
  - 더미 키워드 추출
- Kafka Consumer/Producer 설정
  - `raw-news` 토픽 구독
  - `enriched-news` 토픽 발행
- 기본 API 엔드포인트
  - `/health` - 상태 확인
  - `/process` - 단일 텍스트 처리
- 백그라운드 처리 스레드
  - 비동기 메시지 처리
  - 에러 핸들링

#### 🧪 Testing
- Mock 프로세서 테스트
- Kafka 통합 테스트
- API 응답 검증

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

## [Unreleased]

## [1.1.4] - 2025-07-19

### 📚 문서 정리 및 프로젝트 구조화

#### 🔧 Changed
- **문서 역할 명확화**
  - CLAUDE.md: 개발 가이드라인 위주로 단순화
  - README.md: 프로젝트 현재 상태 및 성능 지표 업데이트
  - CHANGELOG.md: Sprint별 개발 성과 상세 기록
- **임시 파일 정리**
  - Sprint1_Requirements.md 제거
  - WEEK2_DEVELOPMENT_SUMMARY.md 제거
  - f1_score_analysis_report.md 제거
  - performance_benchmark.md 제거
  - server.log 제거

#### 📝 Documentation
- 성능 지표 업데이트 (Sprint 1 - Week 2 기준)
- 핵심 컴포넌트 현황 반영
- 다음 Sprint 계획 명시

## [1.1.3] - 2025-07-19

### 🔧 의존성 최적화

#### 🚀 Added
- **CPU 전용 PyTorch 설치**
  - Docker 이미지 크기 최적화를 위한 CPU 버전 PyTorch 사용
  - `torch==2.1.0+cpu` 및 `torchvision==0.16.0+cpu`
  - GPU 버전 대비 약 2GB 이미지 크기 감소

#### 🔧 Changed
- **requirements.txt 통합**
  - ML 라이브러리를 기본 requirements.txt에 포함
  - 별도의 requirements-ml.txt 제거
  - Mock 모드에서도 동일한 의존성 사용

#### 🐛 Fixed
- 통합 테스트 시 ML 라이브러리 누락 문제 해결
- 개발/프로덕션 환경 간 의존성 일관성 확보

### 🚀 Planned
- KLUE-BERT NER 모델 통합
- KoBERT 감정분석 모델 통합  
- 실시간 처리 성능 최적화
- 배치 처리 파이프라인 구현

---

## [1.1.2] - 2025-07-19

### 통합 테스트 수정

#### 🐛 Fixed
- **의존성 오류 해결**
  - `pydantic-settings` 패키지 추가 (v2.1.0)
  - `requests` 라이브러리 추가 (Hugging Face API 사용)
  - config.py에 pydantic import fallback 로직 구현

- **Docker 빌드 개선**
  - requirements.txt 정리 및 최적화
  - 개발 환경 빌드 시간 단축

#### 📝 Documentation
- CLAUDE.md 업데이트
- 의존성 관리 문서화

## [1.1.1] - 2025-07-19

### 통합 테스트 이슈 수정

#### 🐛 Fixed
- **빌드 최적화**
  - ML 의존성 분리 (requirements.txt / requirements-ml.txt)
  - Docker 빌드 시간 단축 (torch, transformers 제외)
  - pydantic_settings import 오류 해결 (fallback 로직 추가)
- **서비스 시작 오류**
  - ML Service: Dockerfile CMD 경로 수정 (main:app → src.main:app)
  - Graph Service: Neo4j 연결 지연 초기화 구현
  - API Gateway: PORT 환경변수 설정 (8004)

#### 🔧 Changed
- requirements.txt를 경량화하여 개발/테스트 환경 빌드 속도 개선
- config.py에 pydantic import 호환성 개선

#### 📚 Documentation
- INTEGRATION_TEST_FIXES.md 추가 (통합 테스트 문제 해결 가이드)

---

## [1.1.0] - 2025-07-19

### Week 2 Sprint 1: NER 모델 통합 및 성능 최적화

#### 🚀 Added
- **Korean NER Model Integration**
  - Hugging Face Inference API 통합
  - Multilingual NER 모델 적용 (Babelscape/wikineural-multilingual-ner)
  - KoCharELECTRA 로컬 모델 지원
  - KoELECTRA Naver NER 모델 통합 (monologg/koelectra-base-v3-naver-ner)
- **Korean NLP Post-processing**
  - KoreanNERPostProcessor: 한국어 특화 후처리
  - 조사 제거, 숫자 정규화, 특수문자 처리
  - 신뢰도 필터링 및 인접 엔티티 병합
- **Entity Processing Components**
  - KoreanEntityLinker: 지식 베이스 기반 엔티티 링킹
  - KoreanCompanyMatcher: 한국 기업명 정규화 및 매칭
  - KoreanEntitySplitter: 연결사로 이어진 엔티티 분리
  - 주요 한국 기업/인물 정보 (40+ 엔티티)
  - 별칭 및 그룹사 관계 매핑
- **Performance Optimization**
  - LRU 캐싱 시스템 (NERCacheManager)
  - AdaptiveBatchProcessor: 동적 배치 처리
  - 병렬 처리 지원 (ThreadPoolExecutor)
  - **목표 초과 달성**:
    - 처리 속도: 2.57ms/article (목표: 10ms)
    - 처리량: 389 docs/second (목표: 100 docs/s)
- **Evaluation Framework**
  - F1-Score 평가 도구
  - 20개 한국어 테스트 케이스
  - 정확도/재현율/F1 메트릭 계산

#### 📊 Performance Metrics
- **처리 성능**
  - 순차 처리 대비 배치 처리: 86.7% 성능 개선 (30문서)
  - 최적 배치 크기: 5
  - 캐시 효과: 90%+ 성능 향상 (반복 요청)
- **NER 정확도**
  - Mock Model F1: 32.3%
  - Multilingual Model F1: 37.8%
  - KoELECTRA Naver F1: 56.3%
  - 목표 F1: 80% (미달성, 23.7% 부족)

#### 🔧 Changed
- Pipeline 구조를 캐싱 지원하도록 리팩토링
- API 엔드포인트 확장 (캐시/배치/지식베이스 관리)
- 모델 추상화 계층 추가
- 평가 스크립트 개선

#### 📚 Documentation
- 성능 벤치마크 보고서
- F1-Score 분석 보고서
- Week 2 Sprint 1 개발 요약
- 모든 문서 업데이트 (CLAUDE.md, README.md)

## 다음 릴리스 계획

### v1.2.0 (Sprint 2)
- [ ] 한국어 전용 NER 모델 적용 (KLUE-BERT)
- [ ] 도메인 특화 파인튜닝
- [ ] F1-Score 80% 달성
- [ ] 실제 Kafka 통합
- [ ] GPU 가속 지원

### v1.2.0 (Sprint 2)
- [ ] 리스크 분류기 모델 구현
- [ ] 배치 처리 최적화
- [ ] A/B 테스트 프레임워크
- [ ] 모델 성능 모니터링
- [ ] 자동 재학습 파이프라인

---

## 성과 지표

### Sprint 1 달성도
#### Week 1: 100%
- ✅ 한국어 NLP 파이프라인 구축 완료
- ✅ Mock 시스템으로 전체 워크플로우 검증
- ✅ 단위 테스트 및 API 테스트 통과
- ✅ Data Service와 연동 성공 (통합 테스트)
- ✅ 에러율 0% 달성

#### Week 2: 90%
- ✅ NER 모델 통합 (3개 모델 테스트)
- ✅ 한국어 후처리 로직 구현
- ✅ 성능 최적화 (목표 초과 달성)
- ✅ 배치 처리 및 캐싱 시스템
- ⚠️ F1-Score 56.3% (목표 80% 미달)