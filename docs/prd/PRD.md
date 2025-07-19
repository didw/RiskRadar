# Product Requirements Document (PRD)
# RiskRadar - AI 기반 CEO 리스크 관리 플랫폼

## 1. 제품 개요

### 1.1 핵심 정보
- **제품명**: RiskRadar
- **타겟**: 한국 200대 기업 CEO
- **목표**: Risk Knowledge Graph 기반 실시간 의사결정 지원
- **MVP 일정**: 3개월

### 1.2 핵심 가치
"파편화된 정보를 통합하여 CEO에게 맥락 기반 인사이트 제공"

## 2. 문제 정의

### 2.1 고객 Pain Points
1. **정보 과부하**: 일일 500+ 뉴스, 100+ 보고서 처리
2. **맥락 부재**: 숨겨진 리스크 연결고리 파악 어려움
3. **수동적 대응**: 리스크 현실화 후 대응
4. **도구 부재**: CEO 맞춤 의사결정 지원 시스템 부족

### 2.2 시장 기회
- **TAM**: 연 3,000억원 (한국 200대 기업)
- **초기 목표**: 3년 내 20% 점유율 (연 150억원)

## 3. 솔루션

### 3.1 제품 전략
| Phase | 유형 | 핵심 가치 |
|-------|------|-----------|
| Phase 1 | Passive RM | 리스크 조기 경보 (FOMO 해소) |
| Phase 2 | Active RM | 실시간 의사결정 지원 |
| Phase 3 | Predictive RM | 미래 시나리오 예측 |

### 3.2 차별화 요소
- **Risk Knowledge Graph**: 기업-인물-이벤트 관계 분석
- **3D Risk Map**: 직관적 리스크 시각화
- **한국 특화**: 재벌 구조, 규제 환경 깊은 이해

## 4. MVP 핵심 기능 (3개월)

### 4.1 필수 기능 (P0)
1. **데이터 수집**: Tier 1 언론사 18개 실시간 크롤링
2. **RKG 구축**: 핵심 엔티티 추출 및 관계 분석
3. **일일 리포트**: CEO 맞춤 3분 브리핑
4. **웹 대시보드**: 리스크 현황 시각화

### 4.2 추가 기능 (P1-P2)
- Real-time Risk Map (3D)
- 캘린더 연동 미팅 브리핑
- 대화형 인터페이스

## 5. 비기능적 요구사항

| 항목 | 요구사항 | 목표 |
|------|----------|------|
| 성능 | 응답시간 | < 3초 |
| 처리량 | 일일 이벤트 | 1천만건 |
| 실시간성 | 반영시간 | < 5분 |
| 가용성 | Uptime | 99.9% |
| 보안 | 암호화 | AES-256 |

## 6. 기술 스택 개요

- **Core**: Neo4j + Kafka + Flink
- **Backend**: FastAPI + GraphQL
- **Frontend**: Next.js + D3.js
- **AI/ML**: KoBERT + GPT-4
- **Infra**: AWS EKS + Docker

> 상세 기술 아키텍처: [PRD_Tech_Architecture.md](./PRD_Tech_Architecture.md)

## 7. 개발 계획

### 7.1 팀 구성 (11명)
- Data Squad (3명)
- ML/NLP Squad (3명)
- Graph Squad (2명)
- Platform Squad (2명)
- Product Squad (2명)

### 7.2 주요 마일스톤
- **Week 1-4**: 인프라 구축 & 데이터 파이프라인
- **Week 5-8**: RKG 엔진 & 핵심 기능
- **Week 9-12**: UI/UX & Beta 테스트

> 상세 개발 계획: [PRD_Development_Plan.md](./PRD_Development_Plan.md)

## 8. 성공 지표

### 8.1 비즈니스 KPI
- 파일럿 고객: 10개사
- DAU/MAU: 70%
- 리포트 열람률: 90%

### 8.2 기술 KPI
- NLP 정확도: 95%
- API 응답시간: <100ms (P95)
- 시스템 가용성: 99.9%

> 상세 측정 지표: [PRD_Metrics_Risk.md](./PRD_Metrics_Risk.md)

## 9. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|-----------|
| 한국어 NLP | 높음 | KoBERT + 도메인 데이터셋 |
| CEO 채택률 | 높음 | 무료 POC 3개월 |
| 확장성 | 중간 | Neo4j 클러스터링 |

## 10. 관련 문서

- [기술 아키텍처 상세](./PRD_Tech_Architecture.md)
- [개발 계획 및 마일스톤](./PRD_Development_Plan.md)
- [Risk Knowledge Graph 설계](./PRD_RKG_Design.md)
- [성공 지표 및 리스크 관리](./PRD_Metrics_Risk.md)