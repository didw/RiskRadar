# ML Service Development Guidelines
# ML/NLP 서비스 개발 가이드라인

## 📋 서비스 개요

ML Service는 RiskRadar의 자연어 처리 및 머신러닝 추론을 담당하는 마이크로서비스입니다. 한국어 뉴스 텍스트에서 엔티티를 추출하고, 감정 분석을 수행하며, 리스크 관련 인사이트를 생성합니다.

## 🎯 현재 상태 (Sprint 1 Week 3 완료)

- ✅ **FastAPI 기반 ML 서비스 구축** - 고성능 비동기 처리
- ✅ **다중 NER 모델 지원** - Mock, KLUE-BERT, KoELECTRA 등
- ✅ **Kafka 통합** - 실시간 뉴스 데이터 처리 파이프라인
- ✅ **포괄적인 평가 시스템** - F1 Score 기반 모델 성능 측정
- ✅ **배치 처리 최적화** - 대용량 뉴스 데이터 효율적 처리
- ✅ **캐싱 시스템** - Redis 기반 성능 최적화
- ✅ **테스트 자동화** - 단위/통합 테스트 및 성능 검증
- ✅ **향상된 감정 분석** - 한국어 비즈니스 도메인 특화 분석기
- ✅ **고도화된 리스크 분석** - 다중 팩터 리스크 평가 모델
- ✅ **강화된 전처리 파이프라인** - 엔티티 컨텍스트 통합 분석

### 📡 접속 정보
- **API Endpoint**: http://localhost:8002
- **Health Check**: http://localhost:8002/health
- **API Docs**: http://localhost:8002/docs

## 🏗️ 프로젝트 구조

```
ml-service/
├── src/
│   ├── models/             # ML 모델
│   │   ├── ner/           # 개체명 인식 모델
│   │   │   ├── enhanced_rule_ner.py    # 향상된 규칙 기반 NER
│   │   │   ├── koelectra_ner.py        # KoELECTRA NER 모델
│   │   │   ├── postprocessor.py        # 후처리 모듈
│   │   │   ├── entity_linker.py        # 엔티티 연결
│   │   │   ├── company_matcher.py      # 회사명 매칭
│   │   │   ├── cache_manager.py        # 캐시 관리
│   │   │   └── knowledge_base.py       # 지식 베이스
│   │   ├── sentiment/     # 감정 분석 (Week 3 강화)
│   │   │   ├── enhanced_sentiment.py   # 새로 추가: 향상된 감정 분석기
│   │   │   └── mock_sentiment.py       # Mock 감정 분석
│   │   └── risk/          # 리스크 분류 (Week 3 강화)
│   │       ├── risk_analyzer.py        # 새로 추가: 종합 리스크 분석기
│   │       └── risk_classifier.py      # 기존 리스크 분류기
│   ├── processors/        # NLP 전처리
│   │   ├── tokenizer.py   # 한국어 토크나이저
│   │   ├── normalizer.py  # 텍스트 정규화
│   │   └── pipeline.py    # 처리 파이프라인
│   ├── kafka/             # Kafka 연동
│   │   ├── consumer.py    # 실시간 메시지 소비
│   │   ├── producer.py    # 처리 결과 발행
│   │   └── __init__.py
│   ├── api/              # REST API
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── models.py
│   ├── config.py         # 설정 관리
│   └── main.py           # 서비스 진입점
├── tests/                # 테스트
│   ├── unit/             # 단위 테스트
│   ├── integration/      # 통합 테스트
│   └── test_data/        # 테스트 데이터
├── mock-data/            # 개발용 Mock 데이터
├── requirements.txt      # Python 의존성
├── .env                  # 환경 변수
├── Dockerfile           # 컨테이너 이미지
├── README.md            # 프로젝트 정보
├── CLAUDE.md            # 현재 파일
└── CHANGELOG.md         # 변경 이력
```

## 💻 개발 환경 설정

### Prerequisites
```bash
Python 3.11+
CUDA 11.8+ (GPU 사용 시)
Poetry 또는 pip
Docker
```

### 설치
```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate

# 기본 의존성 설치 (빠른 시작)
pip install -r requirements.txt

# ML 프레임워크 설치 (전체 기능)
pip install -r requirements-ml.txt

# 또는 GPU 버전 설치
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
pip install transformers

# 한국어 NLP 도구 설치
python -m konlpy.downloader all
```

### Docker 빌드
```bash
# 개발/테스트용 (경량)
docker build -t ml-service .

# 프로덕션용 (ML 포함)
docker build -f Dockerfile.prod -t ml-service:prod .
```

### 로컬 실행
```bash
# 서비스 실행
python -m src.main

# 또는 개발 모드
uvicorn src.main:app --reload --port 8002
```

## 🔧 주요 컴포넌트

### 1. NLP Pipeline
```python
class NLPPipeline:
    """한국어 NLP 처리 파이프라인"""
    
    def __init__(self):
        self.tokenizer = SimpleTokenizer()  # Java 미설치 환경
        self.ner_model = KoElectraNaverNERModel()  # 최신 모델
        self.sentiment_analyzer = SentimentAnalyzer()
        self.keyword_extractor = KeywordExtractor()
        
    async def process(self, text: str) -> ProcessedResult:
        """텍스트 처리"""
        # 1. 전처리
        normalized = normalize_text(text)
        
        # 2. 토큰화
        tokens = self.tokenizer.tokenize(normalized)
        
        # 3. NER (캐싱 지원)
        entities = self.ner_model.extract_entities(text)
        
        # 4. 감정 분석
        sentiment = self.sentiment_analyzer.analyze(text)
        
        # 5. 키워드 추출
        keywords = self.keyword_extractor.extract(tokens)
        
        # 6. 리스크 점수
        risk_score = calculate_risk_score(sentiment, keywords)
        
        return ProcessedResult(
            entities=entities,
            sentiment=sentiment,
            keywords=keywords,
            risk_score=risk_score
        )
```

### 2. Enhanced Sentiment Analysis (Week 3 추가)
```python
class EnhancedSentimentAnalyzer:
    """향상된 한국어 비즈니스 도메인 감정 분석기"""
    
    def __init__(self):
        # 긍정적 지표들
        self.positive_indicators = {
            'growth': ['증가', '상승', '성장', '확대', '급증', '호조'],
            'success': ['성공', '달성', '기록', '성과', '수익', '이익'],
            'positive_business': ['투자', '확장', '진출', '출시', '런칭'],
        }
        
        # 부정적 지표들  
        self.negative_indicators = {
            'decline': ['감소', '하락', '급락', '폭락', '하향'],
            'problems': ['문제', '이슈', '우려', '위험', '리스크'],
            'financial_stress': ['연체', '부실', '파산', '회생', '부채'],
        }
        
        # 강화/약화 수식어
        self.intensifiers = {
            'strong_positive': ['대폭', '크게', '급격히', '현저히'],
            'strong_negative': ['대폭', '크게', '급격히', '심각하게'],
            'mild': ['소폭', '약간', '다소', '일부'],
        }
    
    def analyze_sentiment(self, text: str, entities: Optional[List] = None) -> Sentiment:
        """
        향상된 감정 분석
        - 다중 카테고리 지표 분석
        - 강화/약화 수식어 처리
        - 부정 표현 핸들링
        - 엔티티 컨텍스트 통합
        """
        sentiment_scores = self._calculate_sentiment_scores(text)
        
        # 엔티티 기반 조정
        if entities:
            sentiment_scores = self._adjust_with_entities(sentiment_scores, entities, text)
        
        return self._determine_final_sentiment(sentiment_scores)
```

### 3. Comprehensive Risk Analysis (Week 3 추가)
```python
class EnhancedRiskAnalyzer:
    """다중 팩터 리스크 분석기"""
    
    def __init__(self):
        # 금융 리스크 요소
        self.financial_risks = {
            'debt_default': ['연체', '부실', '채무불이행', '디폴트', '파산'],
            'liquidity_crisis': ['유동성', '자금부족', '현금흐름', '긴급자금'],
            'credit_rating': ['신용등급', '등급하향', '등급상향', '신용평가'],
        }
        
        # 운영 리스크 요소
        self.operational_risks = {
            'supply_chain': ['공급망', '원재료', '부품부족', '납기지연'],
            'production_issues': ['생산중단', '가동중단', '공장폐쇄', '품질문제'],
            'labor_issues': ['파업', '노사갈등', '임금협상', '정리해고'],
        }
        
        # ESG 리스크
        self.esg_risks = {
            'environmental': ['환경오염', '탄소배출', '폐수', '환경규제'],
            'social': ['사회적책임', '인권', '다양성', '지역사회'],
            'governance': ['지배구조', '투명성', '이사회', '내부거래'],
        }
    
    def analyze_risk(self, text: str, entities: Optional[List] = None, 
                    sentiment: Optional[Dict] = None) -> Dict[str, Any]:
        """
        종합적인 리스크 분석
        - 다중 카테고리 리스크 평가 (금융, 운영, 법적, 시장, ESG)
        - 이벤트 심각도 검출
        - 엔티티 및 감정 통합 분석
        - 리스크 트렌드 및 예측
        """
        # 1. 리스크 이벤트 감지
        risk_events = self._detect_risk_events(text)
        
        # 2. 카테고리별 리스크 점수 계산
        category_scores = self._calculate_category_scores(text, risk_events)
        
        # 3. 엔티티 기반 조정
        if entities:
            category_scores = self._adjust_with_entities(category_scores, entities, text)
        
        # 4. 감정 기반 조정
        if sentiment:
            category_scores = self._adjust_with_sentiment(category_scores, sentiment)
        
        # 5. 종합 리스크 점수 계산
        overall_risk_score = self._calculate_overall_risk(category_scores)
        
        return {
            'overall_risk_score': overall_risk_score,
            'risk_level': self._determine_risk_level(overall_risk_score),
            'category_scores': category_scores,
            'detected_events': risk_events,
            'risk_summary': self._generate_risk_summary(risk_events, category_scores)
        }
```

### 4. Entity Extraction
```python
class EntityExtractor:
    """개체명 인식"""
    
    def __init__(self, model_path: str):
        self.model = KoBERTForNER.from_pretrained(model_path)
        self.label_map = {
            0: "O",
            1: "B-COMPANY",
            2: "I-COMPANY",
            3: "B-PERSON",
            4: "I-PERSON",
            # ...
        }
    
    async def extract(self, tokens: List[str]) -> List[Entity]:
        """엔티티 추출"""
        # 인코딩
        inputs = self.tokenizer.encode_plus(tokens, return_tensors="pt")
        
        # 추론
        with torch.no_grad():
            outputs = self.model(**inputs)
            predictions = torch.argmax(outputs.logits, dim=-1)
        
        # 디코딩
        entities = self.decode_predictions(tokens, predictions)
        return entities
```

### 3. Kafka Integration
```python
class MLConsumer:
    """Kafka 컨슈머"""
    
    def __init__(self):
        self.consumer = KafkaConsumer(
            'raw-news',
            bootstrap_servers=KAFKA_SERVERS,
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        self.producer = MLProducer()
        self.pipeline = NLPPipeline()
    
    async def process_messages(self):
        """메시지 처리 루프"""
        for message in self.consumer:
            try:
                # 원본 뉴스
                news = message.value
                
                # NLP 처리
                result = await self.pipeline.process(news['content'])
                
                # 결과 발행
                enriched = {
                    "original": news,
                    "nlp": result.dict(),
                    "processed_at": datetime.now().isoformat()
                }
                
                await self.producer.send_enriched(enriched)
                
            except Exception as e:
                logger.error(f"Processing failed: {e}")
                # DLQ로 전송
```

## 📝 코딩 규칙

### 1. 모델 관리
- 모델 버전 관리 (DVC 사용)
- 모델 메타데이터 기록
- A/B 테스트 지원
- 롤백 가능한 배포

### 2. 성능 최적화
```python
# 배치 처리
@batch_processor(batch_size=32)
async def process_batch(texts: List[str]):
    # 배치 단위로 처리
    pass

# 모델 캐싱
@lru_cache(maxsize=1)
def load_model():
    return torch.load("model.pt")

# GPU 메모리 관리
torch.cuda.empty_cache()
```

### 3. 에러 처리
```python
try:
    result = await model.predict(text)
except torch.cuda.OutOfMemoryError:
    # GPU 메모리 정리 후 재시도
    torch.cuda.empty_cache()
    result = await model.predict(text)
except ModelError as e:
    # 폴백 모델 사용
    result = await fallback_model.predict(text)
```

### 4. 모니터링
```python
# 추론 시간 측정
@measure_inference_time
async def predict(self, text: str):
    # 모델 추론
    pass

# 정확도 추적
metrics.record_accuracy(predicted, actual)
```

## 🧪 테스트

### 단위 테스트
```bash
pytest tests/unit/
```

### 모델 테스트
```bash
pytest tests/models/ -v
```

### 통합 테스트
```bash
pytest tests/integration/
```

### 테스트 작성 예시
```python
class TestNERModel:
    def test_company_extraction(self):
        # Given
        text = "삼성전자가 새로운 반도체 공장을 건설합니다."
        
        # When
        entities = extractor.extract(text)
        
        # Then
        assert any(e.text == "삼성전자" and e.type == "COMPANY" for e in entities)
    
    @pytest.mark.parametrize("text,expected", [
        ("긍정적인 실적 발표", "positive"),
        ("손실이 크게 증가했다", "negative"),
    ])
    def test_sentiment_analysis(self, text, expected):
        result = analyzer.analyze(text)
        assert result.label == expected
```

## 🚀 배포

### Docker 빌드
```bash
# CPU 버전
docker build -t riskradar/ml-service:latest .

# GPU 버전
docker build -f Dockerfile.gpu -t riskradar/ml-service:latest-gpu .
```

### 환경 변수
```env
# Development mode
USE_MOCK_KAFKA=false
USE_SIMPLE_TOKENIZER=true

# API settings
API_HOST=0.0.0.0
API_PORT=8082

# Kafka settings (local development)
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_CONSUMER_GROUP=ml-service
KAFKA_INPUT_TOPIC=raw-news
KAFKA_OUTPUT_TOPIC=enriched-news

# Model settings
MODEL_PATH=/app/models
MODEL_VERSION=v1.0.0
TOKENIZER_BACKEND=komoran

# Processing settings
BATCH_SIZE=32
MAX_PROCESSING_TIME_MS=100
ENABLE_GPU=false

# Logging
LOG_LEVEL=INFO
```

### 실제 Kafka 통합 (Production Mode)
```bash
# Kafka 서비스 연결 확인
docker exec riskradar-kafka kafka-topics --bootstrap-server localhost:9092 --list

# 메시지 생산 테스트
echo '{"id": "test-001", "title": "테스트 뉴스", "content": "삼성전자가 새로운 투자를 발표했습니다."}' | \
  docker exec -i riskradar-kafka kafka-console-producer \
  --bootstrap-server localhost:9092 --topic raw-news

# 처리된 메시지 확인
docker exec riskradar-kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 --topic enriched-news \
  --from-beginning --max-messages 1 | jq '.nlp.entities'
```

## 📊 모니터링

### Health Check
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model_loaded": model_manager.is_loaded(),
        "gpu_available": torch.cuda.is_available(),
        "kafka_connected": check_kafka_connection()
    }
```

### Metrics
- 추론 시간 (P50, P95, P99)
- 처리량 (요청/초)
- 모델 정확도
- GPU 사용률
- 메모리 사용량

## 🔒 보안

### 모델 보안
- 모델 파일 암호화
- 접근 권한 관리
- 모델 무결성 검증

### 데이터 보안
- PII 마스킹
- 로그 필터링
- 민감 정보 제거

## 🤝 협업

### Input/Output
- **Input**: Kafka topic `raw-news`
- **Output**: Kafka topic `enriched-news`
- **Schema**: [EnrichedNewsModel](schemas.py)

### API 엔드포인트
- `POST /process`: 단일 텍스트 처리
- `POST /batch`: 배치 처리
- `GET /model/info`: 모델 정보

## 🐛 트러블슈팅

### 일반적인 문제

#### 0. 빌드 타임아웃
```bash
# 경량 버전으로 빌드
docker build -t ml-service .

# ML 의존성은 런타임에 설치
docker exec ml-service pip install -r requirements-ml.txt
```

#### 1. GPU 메모리 부족
```python
# 배치 크기 줄이기
BATCH_SIZE = 16  # 32에서 감소

# 그래디언트 체크포인팅
model.gradient_checkpointing_enable()
```

#### 2. 모델 로딩 실패
```bash
# 모델 파일 확인
ls -la /app/models/

# 권한 확인
chmod -R 755 /app/models/
```

#### 3. 느린 추론 속도
- 배치 처리 활용
- 모델 경량화 (양자화)
- TorchScript 변환

## 📚 참고 자료

- [KoBERT Documentation](https://github.com/SKTBrain/KoBERT)
- [KoNLPy Documentation](https://konlpy.org/)
- [PyTorch Documentation](https://pytorch.org/docs/)

## 📝 문서 관리 가이드라인

### 문서 역할 구분
- **CLAUDE.md**: 개발 가이드라인만 작성 (환경 설정, 코딩 규칙, 테스트 방법)
- **README.md**: 프로젝트 관련 내용 (개요, 현재 상태, 아키텍처, 사용법)
- **CHANGELOG.md**: 개발 수행 내용 기록 (Sprint별 성과, 변경사항 상세)

## 📁 프로젝트 문서

### 핵심 문서
- [ML/NLP Squad TRD](../../docs/trd/phase1/TRD_ML_NLP_Squad_P1.md) - 기술 명세
- [API 표준](../../docs/trd/common/API_Standards.md) - API 설계
- [데이터 모델](../../docs/trd/common/Data_Models.md) - 공통 구조

### 연관 서비스
- [Data Service](../data-service/CLAUDE.md) - Kafka 메시지 송신
- [Graph Service](../graph-service/CLAUDE.md) - 처리 결과 전달
- [통합 가이드](../../integration/README.md) - 시스템 통합