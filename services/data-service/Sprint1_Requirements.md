# Sprint 1 Requirements - Data Service

## 📋 개요
Data Service의 Sprint 1 목표는 5개 주요 언론사에서 실시간 뉴스를 수집하는 실제 크롤러를 구현하는 것입니다.

> 📚 **기술 명세**: [Data Squad TRD](../../docs/trd/phase1/TRD_Data_Squad_P1.md)를 참조하세요.

## 🎯 주차별 목표

### Week 1: 크롤러 프레임워크 구축 ✅
- [x] BaseCrawler 클래스 완성
- [x] Rate limiting 시스템 구현 (언론사별 요청 제한)
- [x] 조선일보 크롤러 구현 및 테스트
- [x] 데이터 정규화 모듈 구현

**구현할 메서드**: TRD의 [크롤러 아키텍처](../../docs/trd/phase1/TRD_Data_Squad_P1.md#crawler-architecture) 섹션 참조

### Week 2: 5개 언론사 크롤러 구현 ✅
- [x] 한국경제 크롤러 구현
- [x] 중앙일보 크롤러 구현  
- [x] 연합뉴스 크롤러 구현
- [x] 매일경제 크롤러 구현
- [x] API 엔드포인트 구현 (추가)

**언론사별 특징**: [크롤러 구현 가이드](../../docs/trd/phase1/TRD_Data_Squad_P1.md#crawler-implementation) 참조

### Week 3: Kafka 통합 및 중복 제거 ✅
- [x] Kafka Producer 최적화
- [x] Bloom Filter 기반 중복 제거
- [x] 배치 처리 구현 (100건 단위)
- [x] 에러 재시도 메커니즘

**성능 목표**: [성능 요구사항](../../docs/trd/phase1/TRD_Data_Squad_P1.md#performance-requirements) 참조

### Week 4: 최적화 및 모니터링 ✅
- [x] 처리량 1,000건/시간 달성
- [x] 발행 후 5분 내 수집
- [x] Prometheus 메트릭 추가
- [x] 통합 테스트 작성
- [x] 부하 테스트 프레임워크 구축 (추가)

## 📊 성능 요구사항
[TRD 성능 요구사항](../../docs/trd/phase1/TRD_Data_Squad_P1.md#performance-requirements) 참조

| 항목 | 목표값 | 측정 방법 |
|------|--------|-----------|
| 처리량 | 1,000 건/시간 | Prometheus 메트릭 |
| 지연시간 | < 5분 | 발행시간 vs 수집시간 |
| 중복률 | < 5% | 일일 중복 통계 |
| 가용성 | 99.9% | Uptime 모니터링 |

## 🧪 테스트 요구사항

### 단위 테스트
```bash
# 크롤러별 테스트
pytest tests/crawlers/test_chosun.py
pytest tests/crawlers/test_hankyung.py

# 커버리지 80% 이상
pytest --cov=src --cov-report=html
```

### 통합 테스트
```bash
# Kafka 연동 테스트
pytest tests/integration/test_kafka_producer.py

# End-to-End 테스트
pytest tests/e2e/test_crawl_to_kafka.py
```

## 🔗 의존성

### 외부 서비스
[통합 지점](../../docs/trd/common/Integration_Points.md#data-service) 참조

### 라이브러리
[기술 스택](../../docs/trd/phase1/TRD_Data_Squad_P1.md#tech-stack) 참조

## ✅ 완료 기준

1. **기능적 요구사항** ✅
   - [x] 5개 언론사 크롤러 모두 동작
   - [x] Kafka로 실시간 전송
   - [x] 중복 제거 시스템 구현

2. **비기능적 요구사항** ✅
   - [x] 성능 목표 달성 (1,000건/시간, 5분 이내 수집)
   - [x] 테스트 커버리지 85%
   - [x] 문서화 완료

3. **통합 요구사항** ✅
   - [x] ML Service가 데이터 수신 확인
   - [x] 일일 통합 테스트 통과
   - [x] 모니터링 대시보드 구성 (Prometheus 메트릭)

## 📌 참고사항

- 언론사 서버 부하를 고려한 크롤링
- robots.txt 준수 필수
- 저작권 관련 법규 확인
- 에러 발생 시 즉시 알림

## 🔍 관련 문서
- [Data Squad TRD](../../docs/trd/phase1/TRD_Data_Squad_P1.md)
- [Kafka 메시지 스키마](../../docs/trd/common/Data_Models.md#news-model)
- [통합 테스트 가이드](../../integration/README.md)