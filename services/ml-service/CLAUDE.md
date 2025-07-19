# ML Service Development Guidelines
# ML/NLP 서비스 개발 가이드라인

## 📋 서비스 개요

ML Service는 RiskRadar의 자연어 처리 및 머신러닝 추론을 담당하는 마이크로서비스입니다. 한국어 뉴스 텍스트에서 엔티티를 추출하고, 감정 분석을 수행하며, 리스크 관련 인사이트를 생성합니다.

## 🏗️ 프로젝트 구조

```
ml-service/
├── src/
│   ├── models/             # ML 모델
│   │   ├── ner/           # 개체명 인식
│   │   │   ├── kobert_ner.py
│   │   │   └── configs/
│   │   ├── sentiment/     # 감정 분석
│   │   │   └── sentiment_analyzer.py
│   │   └── risk/          # 리스크 분류
│   │       └── risk_classifier.py
│   ├── processors/        # NLP 전처리
│   │   ├── tokenizer.py   # 한국어 토크나이저
│   │   ├── normalizer.py  # 텍스트 정규화
│   │   └── pipeline.py    # 처리 파이프라인
│   ├── kafka/             # Kafka 연동
│   │   ├── consumer.py
│   │   ├── producer.py
│   │   └── schemas.py
│   ├── api/              # REST API
│   │   ├── routes.py
│   │   └── models.py
│   └── config.py         # 설정
├── models/               # 학습된 모델 파일
│   ├── kobert-ner/
│   └── sentiment/
├── tests/                # 테스트
├── notebooks/            # 실험 노트북
├── requirements.txt
├── Dockerfile
├── README.md
├── CLAUDE.md            # 현재 파일
└── CHANGELOG.md
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

### 2. Entity Extraction
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
# Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_CONSUMER_GROUP=ml-service

# Model
MODEL_PATH=/app/models
MODEL_VERSION=v1.0.0

# GPU
CUDA_VISIBLE_DEVICES=0

# API
API_PORT=8002
API_WORKERS=4
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