# Technical Requirements Documents (TRD)
# RiskRadar 기술 요구사항 문서

## 📋 개요

TRD는 PRD를 기반으로 각 개발팀이 구현해야 할 기술적 세부사항을 정의합니다. 
각 Squad별, Phase별로 독립적인 TRD를 제공하여 병렬 개발이 가능하도록 구성했습니다.

## 🗂️ TRD 구조

```
trd/
├── README.md           # TRD 인덱스 (현재 문서)
├── TRD_Template.md     # TRD 작성 템플릿
├── common/            # 공통 기술 사양
│   ├── API_Standards.md
│   ├── Data_Models.md
│   └── Integration_Points.md
├── phase1/            # Phase 1 (Week 1-4)
│   ├── TRD_Data_Squad_P1.md
│   ├── TRD_ML_NLP_Squad_P1.md
│   ├── TRD_Graph_Squad_P1.md
│   ├── TRD_Platform_Squad_P1.md
│   └── TRD_Product_Squad_P1.md
├── phase2/            # Phase 2 (Week 5-8)
│   └── ...
└── phase3/            # Phase 3 (Week 9-12)
    └── ...
```

## 🎯 Phase별 목표

### Phase 1: Foundation (Week 1-4) - Sprint 기반 개발
Phase 1을 3개의 Sprint로 나누어 빠른 통합과 피드백을 실현합니다.

#### Sprint 0: Walking Skeleton (Week 1)
- **목표**: Mock 데이터로 전체 시스템 연결 확인
- **검증**: E2E 데이터 플로우 동작
- **참고**: [Sprint 0 Integration Guide](phase1/Sprint_0_Integration_Guide.md)

#### Sprint 1: Core Features (Week 2)
- **목표**: 실제 데이터로 기본 기능 구현
- **검증**: 1개 뉴스 소스 처리, 기본 NLP 동작

#### Sprint 2: Full Integration (Week 3-4)
- **목표**: 전체 기능 통합 및 성능 최적화
- **검증**: 시간당 1,000개 뉴스 처리, 기본 엔티티 추출

**상세 계획**: [Sprint Breakdown](phase1/Sprint_Breakdown.md) | [Integration Strategy](phase1/Integration_Strategy.md)

### Phase 2: Core Engine (Week 5-8)
- **목표**: RKG 엔진 고도화 및 핵심 기능 구현
- **검증**: 일일 리포트 생성, API 응답 <200ms

### Phase 3: Product Polish (Week 9-12)
- **목표**: UI/UX 최적화 및 Beta 런칭
- **검증**: 고객 만족도 4.0/5.0, DAU/MAU 70%

## 👥 Squad별 책임

| Squad | 인원 | Phase 1 핵심 과제 | TRD 문서 |
|-------|------|-------------------|----------|
| Data | 3명 | Kafka 파이프라인, 크롤러 | [TRD_Data_Squad_P1.md](phase1/TRD_Data_Squad_P1.md) |
| ML/NLP | 3명 | 한국어 NLP 파이프라인 | [TRD_ML_NLP_Squad_P1.md](phase1/TRD_ML_NLP_Squad_P1.md) |
| Graph | 2명 | Neo4j 스키마, 기본 쿼리 | [TRD_Graph_Squad_P1.md](phase1/TRD_Graph_Squad_P1.md) |
| Platform | 2명 | K8s 인프라, CI/CD | [TRD_Platform_Squad_P1.md](phase1/TRD_Platform_Squad_P1.md) |
| Product | 2명 | API Gateway, 기본 UI | [TRD_Product_Squad_P1.md](phase1/TRD_Product_Squad_P1.md) |

## 🔗 통합 포인트

### API 통합
- [API Standards](common/API_Standards.md) - 모든 Squad 공통
- GraphQL 스키마는 Product Squad가 관리
- gRPC는 내부 서비스간 통신용

### 데이터 모델
- [Data Models](common/Data_Models.md) - 공통 데이터 구조
- Graph Squad가 RKG 스키마 주도
- Data Squad가 스트리밍 포맷 정의

### 의존성 관리
- [Integration Points](common/Integration_Points.md) - Squad간 인터페이스
- 각 TRD에 의존성 명시
- 주간 통합 테스트

## 📐 TRD 작성 원칙

1. **독립성**: 각 Squad가 독립적으로 개발 가능
2. **명확성**: 구현 가능한 수준의 상세 스펙
3. **검증성**: 측정 가능한 완료 기준
4. **추적성**: PRD 요구사항과 1:1 매핑

## 🚀 시작하기

1. 자신의 Squad TRD 확인
2. [공통 표준](common/) 숙지
3. Phase별 마일스톤 확인
4. 의존성 있는 다른 Squad와 조율

## 📅 일정 관리

- **주간 동기화**: 매주 금요일 Squad Lead 미팅
- **Phase 전환**: 4주 단위로 다음 Phase TRD 배포
- **변경 관리**: PR을 통한 TRD 업데이트