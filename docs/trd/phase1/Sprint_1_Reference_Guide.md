# Sprint 1 Reference Guide
# Sprint 1 참조 가이드

## 🎯 목적
이 문서는 Sprint 1 개발에 필요한 모든 문서와 리소스에 대한 통합 네비게이션을 제공합니다.

## 📚 문서 구조

### 1. 기술 명세 (Technical Specifications)
각 Squad의 상세 기술 명세는 TRD 문서에서 확인하세요:

| Squad | TRD 문서 | 주요 내용 |
|-------|----------|-----------|
| Data Squad | [TRD_Data_Squad_P1.md](TRD_Data_Squad_P1.md) | 크롤러 아키텍처, Kafka 설정, 데이터 포맷 |
| ML/NLP Squad | [TRD_ML_Squad_P1.md](TRD_ML_Squad_P1.md) | 모델 명세, NLP 파이프라인, 성능 목표 |
| Graph Squad | [TRD_Graph_Squad_P1.md](TRD_Graph_Squad_P1.md) | Neo4j 스키마, 그래프 모델, Cypher 쿼리 |
| Product Squad | [TRD_Product_Squad_P1.md](TRD_Product_Squad_P1.md) | API Gateway, Web UI, GraphQL 스키마 |

### 2. Sprint 1 태스크 체크리스트
각 서비스별 주간 태스크는 다음 문서에서 확인하세요:

| 서비스 | Sprint 1 Requirements | 담당 Squad |
|--------|----------------------|------------|
| Data Service | [📋 Sprint1_Requirements.md](../../../services/data-service/Sprint1_Requirements.md) | Data Squad |
| ML Service | [📋 Sprint1_Requirements.md](../../../services/ml-service/Sprint1_Requirements.md) | ML/NLP Squad |
| Graph Service | [📋 Sprint1_Requirements.md](../../../services/graph-service/Sprint1_Requirements.md) | Graph Squad |
| API Gateway | [📋 Sprint1_Requirements.md](../../../services/api-gateway/Sprint1_Requirements.md) | Product Squad |
| Web UI | [📋 Sprint1_Requirements.md](../../../services/web-ui/Sprint1_Requirements.md) | Product Squad |

### 3. 공통 표준 및 가이드
모든 Squad가 준수해야 할 공통 표준:

| 문서 | 내용 | 필수 여부 |
|------|------|-----------|
| [API_Standards.md](../../common/API_Standards.md) | REST/GraphQL API 표준, 에러 처리 | ✅ 필수 |
| [Data_Models.md](../../common/Data_Models.md) | 공통 데이터 모델, 엔티티 정의 | ✅ 필수 |
| [Integration_Points.md](../../common/Integration_Points.md) | 서비스 간 통합 지점, Kafka 토픽 | ✅ 필수 |
| [Security_Guidelines.md](../../common/Security_Guidelines.md) | 보안 가이드라인, 인증/인가 | ✅ 필수 |

### 4. Sprint 1 전체 일정
[Sprint_1_Detailed_Tasks.md](Sprint_1_Detailed_Tasks.md) - 전체 Sprint 1 마일스톤 및 통합 일정

## 🔍 빠른 참조

### 기술 스택 정보를 찾고 있나요?
→ 각 Squad의 TRD 문서 참조

### 이번 주 할 일을 확인하고 싶나요?
→ 해당 서비스의 Sprint1_Requirements.md 참조

### API 설계 가이드가 필요하나요?
→ [API_Standards.md](../../common/API_Standards.md) 참조

### 데이터 모델 정의가 필요하나요?
→ [Data_Models.md](../../common/Data_Models.md) 참조

### 다른 서비스와 어떻게 통합하나요?
→ [Integration_Points.md](../../common/Integration_Points.md) 참조

## 📋 주요 결정 사항 추적

### 변경된 기술 결정
| 날짜 | 결정 사항 | 영향받는 Squad | 문서 업데이트 |
|------|-----------|----------------|---------------|
| 2024-01-15 | Kafka 대신 Redis Streams 사용 (개발 환경) | 전체 | ✅ |
| - | - | - | - |

## 🚀 Sprint 1 주요 목표

### Week 1-2: 기반 구축
- 각 서비스 기본 구조 설정
- CI/CD 파이프라인 구축
- 개발 환경 표준화

### Week 3-4: 핵심 기능 구현
- Data Service: 2개 뉴스 소스 크롤러
- ML Service: NER 기본 구현
- Graph Service: 기본 스키마 및 CRUD
- API Gateway: 인증 및 기본 쿼리
- Web UI: 로그인 및 대시보드 레이아웃

### Week 5-6: 통합 및 테스트
- 서비스 간 통합 테스트
- 성능 벤치마크
- 문서화 완성

## 🔗 외부 리소스

- [프로젝트 전체 README](../../../README.md)
- [프로젝트 CHANGELOG](../../../CHANGELOG.md)
- [개발 가이드라인 (CLAUDE.md)](../../../CLAUDE.md)

---
*이 문서는 Sprint 1 진행 중 지속적으로 업데이트됩니다.*
*최종 업데이트: 2025-07-19*