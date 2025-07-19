# RiskRadar 개발 진행 상황

## 현재 역할
ML/NLP Squad 개발자로서 RiskRadar의 자연어 처리 및 머신러닝 서비스(ML Service) 개발을 담당하고 있습니다.

## 프로젝트 개요
- **프로젝트명**: RiskRadar - 한국 금융 리스크 모니터링 플랫폼
- **구조**: Monorepo 기반 마이크로서비스 아키텍처
- **주요 서비스**:
  - Data Service: 뉴스 크롤링 및 수집
  - ML Service: NLP 처리 및 엔티티 추출
  - Graph Service: 지식 그래프 구축
  - API Gateway: GraphQL API 제공
  - Web UI: 대시보드 프론트엔드

## 현재 진행 상황

### Sprint 1 - Week 1 (완료) ✅
1. **한국어 NLP 파이프라인 구축**
   - TextNormalizer: 텍스트 정규화
   - KoreanTokenizer: KoNLPy 기반 토크나이저
   - Mock NER 모델 구현
   - 규칙 기반 감정 분석

2. **Kafka 통합**
   - Mock Consumer/Producer 구현
   - 메시지 스키마 정의
   - 비동기 처리 구조

3. **REST API 구현**
   - `/api/v1/process`: 단일 텍스트 처리
   - `/api/v1/batch`: 배치 처리
   - `/health`: 상태 확인

4. **통합 테스트 성공**
   - 전체 데이터 플로우 검증
   - 모든 서비스 연동 확인

### Sprint 1 - Week 2 (진행 중) 🔄
1. **NER 모델 통합** ✅
   - Hugging Face API 연동 시도
   - KoCharELECTRA 로컬 모델 테스트
   - KoELECTRA Naver NER 모델 구현
   - **현재 F1-Score: 56.3% (목표: 80%)**

2. **한국어 후처리 구현** ✅
   - 조사 제거 및 정규화
   - 엔티티 링킹 (40+ 한국 기업/인물)
   - 연결 엔티티 분리

3. **성능 최적화** ✅
   - LRU 캐싱 시스템
   - 동적 배치 처리
   - **달성 성능**:
     - 처리 속도: 2.57ms/article (목표: 10ms) ✅
     - 처리량: 389 docs/second (목표: 100 docs/s) ✅

4. **의존성 최적화** ✅
   - CPU 전용 PyTorch 설치
   - Docker 이미지 크기 감소 (2GB 절감)
   - requirements.txt 통합

## 현재 이슈

### 1. F1-Score 목표 미달성
- **현재**: 56.3%
- **목표**: 80%
- **원인**: 
  - 한국어 특화 모델 부족
  - 도메인 특화 학습 데이터 부재
  - 모델 파인튜닝 필요

### 2. Git Push 차단
- **문제**: 이전 커밋에 Hugging Face API 토큰이 포함됨
- **상태**: 로컬 커밋은 완료, 원격 저장소 푸시 불가
- **해결 방법**: 
  - git history 수정 필요
  - 또는 GitHub에서 시크릿 허용

## 다음 단계

### 단기 (이번 주)
1. F1-Score 개선
   - KLUE-BERT 모델 테스트
   - 도메인 특화 데이터셋 구축
   - 모델 파인튜닝

2. 실제 Kafka 통합
   - Mock 모드에서 실제 모드로 전환
   - 메시지 처리 안정성 확보

### 중기 (Sprint 2)
1. 감정 분석 모델 구현
2. 리스크 분류기 개발
3. GPU 가속 지원
4. A/B 테스트 프레임워크

### 장기 (Phase 2)
1. 실시간 학습 파이프라인
2. 모델 버전 관리 시스템
3. 성능 모니터링 대시보드
4. 자동 재학습 시스템

## 기술 스택
- **언어**: Python 3.11+
- **프레임워크**: FastAPI, PyTorch, Transformers
- **NLP**: KoNLPy, KoELECTRA, KLUE-BERT
- **메시징**: Kafka
- **컨테이너**: Docker
- **테스트**: pytest, pytest-asyncio

## 참고 문서
- [Sprint 1 Requirements](services/ml-service/Sprint1_Requirements.md)
- [Week 2 Development Summary](services/ml-service/WEEK2_DEVELOPMENT_SUMMARY.md)
- [F1-Score Analysis Report](services/ml-service/f1_score_analysis_report.md)
- [Performance Benchmark](services/ml-service/performance_benchmark.md)

---
*최종 업데이트: 2025-07-19*