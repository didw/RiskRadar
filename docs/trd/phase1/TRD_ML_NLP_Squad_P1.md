# Technical Requirements Document
# ML/NLP Squad - Phase 1

## 1. 개요

### 1.1 문서 정보
- **Squad**: ML/NLP Squad
- **Phase**: 1 (Week 1-4)
- **작성일**: 2024-07-19
- **버전**: 1.0

### 1.2 범위
한국어 NLP 파이프라인 구축 및 기본 엔티티 추출 시스템 구현

### 1.3 관련 문서
- PRD: [PRD.md](../../prd/PRD.md)
- RKG Design: [PRD_RKG_Design.md](../../prd/PRD_RKG_Design.md)
- 의존 TRD: Data Squad (입력 데이터 포맷)

## 2. 기술 요구사항

### 2.1 기능 요구사항
| ID | 기능명 | 설명 | 우선순위 | PRD 참조 |
|----|--------|------|----------|----------|
| F001 | 한국어 전처리 | 형태소 분석, 정규화 | P0 | FR-002 |
| F002 | 개체명 인식 (NER) | Company, Person, Event 추출 | P0 | FR-002 |
| F003 | 감정 분석 | 긍정/부정/중립 분류 | P1 | FR-002 |
| F004 | 키워드 추출 | 주요 키워드 및 토픽 추출 | P1 | FR-002 |
| F005 | 스트리밍 처리 | Kafka 실시간 처리 | P0 | FR-002 |

### 2.2 비기능 요구사항
| 항목 | 요구사항 | 측정 방법 |
|------|----------|-----------|
| 정확도 | NER F1-Score 80% 이상 | 테스트셋 평가 |
| 처리 속도 | 기사당 100ms 이내 | 평균 처리 시간 |
| 처리량 | 초당 10개 문서 | 스트리밍 메트릭 |
| 메모리 | 모델당 2GB 이내 | 리소스 모니터링 |

## 3. 시스템 아키텍처

### 3.1 컴포넌트 다이어그램
```
┌─────────────────────┐
│   Kafka Topic:      │
│   raw-news         │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────────────────────────────┐
│           NLP Pipeline Service               │
│                                             │
│  ┌─────────────┐    ┌──────────────┐       │
│  │   Consumer   │───▶│ Preprocessor │       │
│  └─────────────┘    └──────┬───────┘       │
│                            │               │
│                            ▼               │
│  ┌──────────────────────────────────┐      │
│  │        Model Pipeline            │      │
│  │  ┌─────────┐     ┌─────────┐   │      │
│  │  │   NER   │     │Sentiment│   │      │
│  │  │  Model  │     │Analysis │   │      │
│  │  └────┬────┘     └────┬────┘   │      │
│  │       │               │         │      │
│  │       └───────┬───────┘         │      │
│  │               ▼                 │      │
│  │        ┌─────────────┐          │      │
│  │        │  Keyword    │          │      │
│  │        │ Extraction  │          │      │
│  │        └─────┬───────┘          │      │
│  └──────────────┼──────────────────┘      │
│                 │                          │
│                 ▼                          │
│          ┌──────────────┐                  │
│          │   Producer   │                  │
│          └──────┬───────┘                  │
└─────────────────┼───────────────────────────┘
                  │
                  ▼
         ┌────────────────┐
         │  Kafka Topic:  │
         │ enriched-news  │
         └────────────────┘
```

### 3.2 데이터 플로우
1. **입력**: Kafka에서 원시 뉴스 데이터 수신
2. **전처리**: 한국어 형태소 분석 및 정규화
3. **분석**: NER, 감정분석, 키워드 추출 병렬 처리
4. **출력**: 분석 결과를 enriched-news 토픽으로 전송

## 4. 상세 설계

### 4.1 API 명세

#### 4.1.1 NLP 분석 API (테스트용)
```yaml
endpoint: /api/v1/nlp/analyze
method: POST
request:
  type: object
  properties:
    text: string
    options:
      type: object
      properties:
        ner: boolean
        sentiment: boolean
        keywords: boolean
response:
  type: object
  properties:
    entities:
      type: array
      items:
        type: object
        properties:
          text: string
          type: enum [COMPANY, PERSON, EVENT, LOCATION]
          position: [start, end]
          confidence: float
    sentiment:
      type: object
      properties:
        label: enum [positive, negative, neutral]
        score: float
    keywords:
      type: array
      items:
        type: object
        properties:
          word: string
          score: float
```

### 4.2 데이터 모델

#### 4.2.1 Enriched News Format
```json
{
  "original": {
    // 원본 뉴스 데이터
  },
  "nlp": {
    "preprocessed": {
      "tokens": ["형태소", "배열"],
      "normalized_text": "정규화된 텍스트"
    },
    "entities": [
      {
        "text": "삼성전자",
        "type": "COMPANY",
        "position": [10, 14],
        "confidence": 0.95,
        "kb_id": "KR-삼성전자"  // Knowledge Base ID
      },
      {
        "text": "이재용",
        "type": "PERSON",
        "position": [20, 23],
        "confidence": 0.92,
        "kb_id": "KR-이재용"
      }
    ],
    "sentiment": {
      "document": {
        "label": "negative",
        "score": 0.78
      },
      "entities": {
        "삼성전자": {"label": "negative", "score": 0.82},
        "이재용": {"label": "neutral", "score": 0.51}
      }
    },
    "keywords": [
      {"word": "반도체", "score": 0.85, "type": "TOPIC"},
      {"word": "수출규제", "score": 0.79, "type": "RISK"}
    ],
    "processing_time_ms": 87
  }
}
```

### 4.3 핵심 알고리즘

#### 4.3.1 NER 파이프라인
```python
class KoreanNERPipeline:
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained("klue/bert-base")
        self.model = AutoModelForTokenClassification.from_pretrained(
            "klue/bert-base-ner"
        )
        self.entity_linker = EntityLinker()  # KB 연결
        
    def extract_entities(self, text: str) -> List[Entity]:
        # 토크나이징
        inputs = self.tokenizer(
            text, 
            return_tensors="pt",
            max_length=512,
            truncation=True
        )
        
        # 모델 추론
        with torch.no_grad():
            outputs = self.model(**inputs)
            predictions = torch.argmax(outputs.logits, dim=2)
        
        # BIO 태깅 디코딩
        entities = self._decode_bio_tags(
            inputs.input_ids[0], 
            predictions[0]
        )
        
        # Entity Linking (KB 연결)
        for entity in entities:
            entity.kb_id = self.entity_linker.link(
                entity.text, 
                entity.type,
                context=text
            )
        
        return entities
```

#### 4.3.2 감정 분석 앙상블
```python
class SentimentAnalyzer:
    def __init__(self):
        self.models = [
            KoBERTSentiment(),
            KoELECTRASentiment(),
            RuleBased()  # 금융 도메인 특화 규칙
        ]
        self.weights = [0.4, 0.4, 0.2]
    
    def analyze(self, text: str) -> SentimentResult:
        # 각 모델 예측
        predictions = []
        for model in self.models:
            pred = model.predict(text)
            predictions.append(pred)
        
        # 가중 평균 앙상블
        final_scores = np.average(
            [p.scores for p in predictions],
            weights=self.weights,
            axis=0
        )
        
        # Aspect-based sentiment (엔티티별)
        entities = self.extract_entity_mentions(text)
        entity_sentiments = {}
        
        for entity in entities:
            context = self.extract_context(text, entity)
            entity_sentiments[entity] = self.analyze_context(context)
        
        return SentimentResult(
            document_sentiment=final_scores,
            entity_sentiments=entity_sentiments
        )
```

#### 4.3.3 도메인 특화 키워드 추출
```python
class DomainKeywordExtractor:
    def __init__(self):
        self.risk_keywords = load_risk_dictionary()
        self.finance_terms = load_finance_terms()
        self.tfidf = TfidfVectorizer(
            tokenizer=korean_tokenizer,
            max_features=1000
        )
        
    def extract_keywords(self, text: str) -> List[Keyword]:
        keywords = []
        
        # 1. TF-IDF 기반 추출
        tfidf_keywords = self.extract_tfidf(text)
        
        # 2. 도메인 사전 매칭
        risk_matches = self.match_risk_keywords(text)
        finance_matches = self.match_finance_terms(text)
        
        # 3. BERT 기반 키워드 추출
        bert_keywords = self.extract_bert_keywords(text)
        
        # 4. 통합 및 랭킹
        all_keywords = tfidf_keywords + risk_matches + finance_matches + bert_keywords
        ranked = self.rank_keywords(all_keywords, text)
        
        return ranked[:10]  # Top 10
```

## 5. 기술 스택

### 5.1 사용 기술
- **언어**: Python 3.11+
- **ML 프레임워크**: 
  - PyTorch 2.0
  - Transformers 4.35
- **한국어 NLP**:
  - KoNLPy (형태소 분석)
  - kiwipiepy (고속 형태소 분석)
- **모델**:
  - KLUE-BERT (NER)
  - KoBERT (감정분석)
  - KoGPT2 (생성 태스크)
- **스트리밍**:
  - aiokafka
  - ray (분산 처리)

### 5.2 인프라 요구사항
- **컴퓨팅**:
  - GPU: T4 × 2 (모델 서빙)
  - CPU: 8 vCPU, 32GB RAM × 3
- **스토리지**:
  - 모델 저장: 20GB
  - 캐시: 10GB
- **모델 서빙**:
  - TorchServe 또는 Triton

## 6. 구현 계획

### 6.1 마일스톤
| 주차 | 목표 | 산출물 |
|------|------|--------|
| Week 1 | 기본 NLP 파이프라인 | 형태소 분석 완료 |
| Week 2 | NER 모델 통합 | 3가지 엔티티 추출 |
| Week 3 | 감정분석 & 키워드 | 전체 파이프라인 |
| Week 4 | 최적화 & 통합 테스트 | 성능 목표 달성 |

### 6.2 리스크 및 대응
| 리스크 | 영향도 | 대응 방안 |
|--------|--------|-----------|
| 한국어 모델 성능 부족 | High | 도메인 데이터 추가 학습 |
| GPU 메모리 부족 | Medium | 모델 양자화, 배치 크기 조정 |
| 처리 속도 미달 | Medium | 모델 경량화, 캐싱 전략 |

## 7. 테스트 계획

### 7.1 단위 테스트
- **커버리지 목표**: 85%
- **주요 테스트**:
  - 형태소 분석 정확도
  - NER 경계 검출
  - 감정 분류 일관성
  - 엣지 케이스 (긴 문장, 특수문자)

### 7.2 성능 테스트
- **데이터셋**: 자체 구축 1만건
- **메트릭**:
  - NER: F1-Score > 80%
  - Sentiment: Accuracy > 85%
  - Latency: P95 < 100ms

## 8. 완료 기준

### 8.1 기능 완료 기준
- [x] 한국어 전처리 파이프라인 구축
- [x] 3가지 엔티티 타입 추출 (회사, 인물, 이벤트)
- [x] 문서 레벨 감정 분석
- [x] 상위 10개 키워드 추출

### 8.2 성능 완료 기준
- [x] NER F1-Score 80% 이상
- [x] 처리 속도: 기사당 100ms 이내
- [x] 메모리 사용량: 2GB 이내

## 9. 의존성

### 9.1 외부 의존성
- **Data Squad**: 입력 데이터 포맷 정의
- **Graph Squad**: 엔티티 KB ID 체계

### 9.2 모델 의존성
- KLUE 사전학습 모델
- 도메인 특화 사전 구축

## 10. 부록

### 10.1 용어 정의
| 용어 | 설명 |
|------|------|
| NER | Named Entity Recognition (개체명 인식) |
| BIO | Begin-Inside-Outside 태깅 방식 |
| KB | Knowledge Base (지식 베이스) |
| F1-Score | Precision과 Recall의 조화평균 |

### 10.2 참고 자료
- [KLUE Benchmark](https://klue-benchmark.com/)
- [KoNLPy Documentation](https://konlpy.org/)
- [한국어 NLP 모범 사례]()