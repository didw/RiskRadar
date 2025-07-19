# ML Service
# 머신러닝/자연어처리 서비스

## 🎯 서비스 개요

ML Service는 RiskRadar 플랫폼의 인공지능 엔진입니다. 한국어 뉴스 텍스트를 분석하여 기업 리스크와 관련된 인사이트를 추출합니다.

### 주요 기능
- 🏢 **개체명 인식 (NER)**: 기업, 인물, 이벤트 등 핵심 엔티티 추출
- 😊 **감정 분석**: 긍정/부정/중립 감정 분류
- ⚠️ **리스크 점수**: 기업별 리스크 레벨 계산
- 🔑 **키워드 추출**: 핵심 키워드 및 토픽 분석
- 🚀 **고성능 처리**: 배치 처리 및 캐싱으로 최적화

### 성능 지표 (Sprint 1 - Week 3 기준)
- ⚡ **처리 속도**: 22.5ms/article (목표: 10ms) ⚠️ 
- 📊 **처리량**: 74 docs/second (목표: 100 docs/s) ⚠️
- 🎯 **NER F1-Score**: 88.6% (목표: 80%) ✅ **목표 달성!**
- 💾 **캐시 효과**: 90%+ 성능 향상 (반복 요청)
- 🐳 **Docker 이미지**: 2GB 절감 (CPU 전용 PyTorch)

## 🚀 빠른 시작

### Prerequisites
- Python 3.11+
- Java 11+ (KoNLPy 사용 시)
- CUDA 11.8+ (GPU 사용 시)
- Docker & Docker Compose

### 설치 및 실행
```bash
# 1. Java 설치 (Ubuntu/Debian)
sudo apt-get install openjdk-11-jdk

# 2. 기본 의존성 설치 (경량 버전)
pip install -r requirements.txt

# 3. ML 의존성 설치 (선택사항 - 전체 기능 사용 시)
pip install -r requirements-ml.txt

# 4. 환경 설정
cp .env.example .env

# 5. 서비스 실행
python -m uvicorn src.main:app --host 0.0.0.0 --port 8082

# 또는 Docker 사용 (개발/테스트)
docker build -t ml-service .
docker run -p 8082:8082 ml-service

# Docker Compose 사용
docker-compose up ml-service
```

### 의존성 관리
- `requirements.txt`: 기본 의존성 (빠른 빌드)
- `requirements-ml.txt`: ML 프레임워크 (torch, transformers)

## 📊 API 엔드포인트

### Health Check
```bash
GET /api/v1/health
```

### 텍스트 처리
```bash
POST /api/v1/process
{
  "text": "삼성전자가 반도체 공장을 증설한다고 발표했다."
}
```

### 배치 처리
```bash
POST /api/v1/batch
{
  "texts": ["텍스트1", "텍스트2", ...]
}
```

### 지식 베이스 검색
```bash
GET /api/v1/knowledge-base/search?query=삼성&entity_type=COMPANY
```

### 캐시 통계
```bash
GET /api/v1/cache/stats
```

## 🔧 설정

### 환경 변수
```env
# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_CONSUMER_GROUP=ml-service

# Model
MODEL_PATH=/models
MODEL_VERSION=v1.0.0

# GPU
CUDA_VISIBLE_DEVICES=0
```

## 📝 데이터 포맷

### Input Schema (Kafka)
```json
{
  "id": "news-id",
  "title": "뉴스 제목",
  "content": "뉴스 본문",
  "source": "chosun",
  "published_at": "2024-01-15T10:00:00Z"
}
```

### Output Schema (Kafka)
```json
{
  "original": {
    "id": "news-id",
    "title": "뉴스 제목"
  },
  "nlp": {
    "entities": [
      {
        "text": "삼성전자",
        "type": "COMPANY",
        "confidence": 0.95
      }
    ],
    "sentiment": {
      "label": "positive",
      "score": 0.8
    },
    "keywords": ["반도체", "투자", "공장"],
    "risk_score": 3.5
  },
  "processed_at": "2024-01-15T10:05:00Z"
}
```

## 🧪 테스트

```bash
# 단위 테스트
pytest tests/unit/

# 모델 테스트
pytest tests/models/

# 통합 테스트
pytest tests/integration/

# 성능 테스트
python tests/performance/benchmark.py
```

## 📈 모니터링

### Prometheus Metrics
- `ml_inference_duration_seconds`: 추론 시간
- `ml_processed_total`: 처리된 문서 수
- `ml_model_accuracy`: 모델 정확도

### GPU 모니터링
```bash
# GPU 사용률 확인
nvidia-smi

# 실시간 모니터링
watch -n 1 nvidia-smi
```

## 🧠 모델 정보

### 사용 모델
- **NER**: 
  - Enhanced Rule-based NER (현재) - F1: 88.6% ✅
  - KoELECTRA-small-v3-modu-ner - F1: 46.9%
  - KoELECTRA Naver NER - F1: 56.3%
- **Sentiment**: 규칙 기반 감정 분석
- **Keywords**: TF-IDF 기반 추출  
- **Risk Score**: 감정 및 키워드 기반 계산

### 핵심 컴포넌트 (Sprint 1 완료)
- **Enhanced Rule-based NER**: 한국어 특화 개체명 인식 (100+ 기업/인물 DB)
- **KoreanNERPostProcessor**: 스마트 연결사 감지 및 엔티티 병합 방지
- **KoreanEntityLinker**: 지식베이스 기반 엔티티 링킹
- **KoELECTRA NER**: Leo97/KoELECTRA-small-v3-modu-ner 통합
- **NERCacheManager**: LRU 캐싱 시스템 (모델 로딩, 추론 결과)
- **AdaptiveBatchProcessor**: 동적 배치 처리 (1-32 배치 크기)

### Sprint 1 Week 3 주요 성과
- 🎯 **F1-Score 88.6% 달성** (목표 80% 초과 달성)
- 🔧 **연결사 처리 개선**: "CJ그룹과 롯데그룹" → ["CJ그룹", "롯데그룹"]
- 🚀 **KoELECTRA 모델 통합** 완료
- ⚡ **성능 57.4% 향상** (vs. 이전 최고 모델)

### 다음 Sprint 계획
1. **처리 속도 최적화** (목표: 10ms/article)
2. **실제 Kafka 통합** (Mock → Real mode)
3. **감정 분석 모델 고도화**

## 🔗 관련 문서

- [개발 가이드라인](CLAUDE.md)
- [변경 이력](CHANGELOG.md)
- [모델 학습 가이드](docs/training.md)
- [API 상세 문서](docs/api.md)

## 🤝 담당자

- **Squad**: ML/NLP Squad
- **Lead**: @ml-lead
- **Members**: @ml-member1, @ml-member2, @ml-member3