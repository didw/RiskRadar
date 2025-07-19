# MIQ RiskRadar - Head of Engineering 분석 보고서

## 개요: MIQ가 직면한 문제와 기회

MIQ는 프로그래매틱 미디어 파트너로서 성공적인 사업을 운영하고 있으나, 서비스 중심 모델의 한계에 직면해 있습니다. 본 보고서는 이러한 한계를 극복하고 새로운 성장 동력을 확보하기 위한 **RiskRadar** (기존 문서에서는 여러 이름으로 언급됨) 플랫폼 개발 계획을 제시합니다.

### 핵심 문제 진단

1. **사업 모델의 구조적 한계**
   - 현재 MIQ는 인력 기반의 서비스 모델로 운영되어 확장성(Scalability)이 제한적
   - 전문가의 시간과 노력에 의존하여 성장이 선형적으로 제약됨
   - 독점적 기술 자산(IP) 부재로 방어력(Defensibility) 취약

2. **시장 환경의 변화**
   - 프로그래매틱 광고 시장이 플랫폼 중심으로 재편
   - The Trade Desk 등 경쟁사는 SaaS 플랫폼으로 확장 가능한 수익 창출
   - 쿠키리스 시대 도래로 새로운 형태의 데이터 인텔리전스 솔루션 필요

3. **타겟 고객의 Pain Points** (한국 200대 기업 CEO)
   - 하루 15시간 이상 업무에 시달리며 정보 과부하 상태
   - 파편화된 정보로 인한 의사결정의 어려움
   - 리스크 조기 감지와 기회 포착의 한계
   - 맥락 기반의 통합적 인사이트 부재

## 요구사항 정리

### 제품 비전
단편화된 고객 데이터와 외부 정보를 통합하여 **Risk Knowledge Graph (RKG)** 기반의 지능형 리스크 관리 플랫폼을 구축합니다.

### 핵심 요구사항

#### 1. 기능적 요구사항

**Phase 1: Passive Risk Management (수동적 RM)**
- 실시간 데이터 수집 파이프라인 구축
  - Tier 1 언론사 중심 뉴스 크롤링
  - 공시 시스템(DART, EDGAR) 연동
  - SNS 및 커뮤니티 weak signal 수집
- Risk Knowledge Graph 구축
  - 기업, 인물, 사건, 규제 등 핵심 엔티티 모델링
  - 관계(Relationship) 자동 추출 및 저장
- 데일리 리스크 브리핑 생성
  - CEO 맞춤형 3분 요약 리포트
  - 중요도 기반 우선순위 정렬

**Phase 2: Active Risk Management (능동적 RM)**
- 맥락 인지 기능
  - 캘린더/이메일 연동을 통한 사용자 컨텍스트 파악
  - 미팅 어시스턴트 (상대방 분석, 리스크 사전 브리핑)
- 대화형 인터페이스
  - "B사와 파트너십을 맺을 때 주의점은?" 같은 자연어 질의 처리
  - RKG 기반 심층 분석 및 인사이트 제공
- 리스크 시뮬레이션
  - What-if 시나리오 분석
  - 의사결정에 따른 잠재 리스크/기회 예측

#### 2. 비기능적 요구사항

- **보안**: 최고 수준의 데이터 암호화, RBAC, 독립망 옵션
- **성능**: 실시간 처리 (5분 이내 데이터 반영), 100ms 이내 쿼리 응답
- **확장성**: 일 1000만+ 이벤트 처리, 수평적 확장 가능
- **사용성**: C-level 친화적 UI/UX, 직관적 시각화

## 개발 프로세스 도출

### 개발 방법론: Agile + Lean Startup

**핵심 원칙**
1. MVP First - 핵심 가설을 빠르게 검증
2. Data-Driven - 실제 CEO 피드백 기반 개선
3. Scalable Architecture - 향후 확장 고려한 설계

**팀 구성 (5개 스쿼드, 총 25명)**
- Data Pipeline Squad: 크롤링, ETL, 실시간 처리
- RKG Core Squad: 그래프 모델링, NLP/ML
- Frontend Squad: UI/UX, 시각화
- Platform Squad: 인프라, DevOps, 보안
- Product Squad: PM, 도메인 전문가

**Sprint 구성**
- 2주 스프린트 × 6회 = 12주 (3개월)
- Daily Standup, Sprint Review, Retrospective

## 3개월 마일스톤 설계

### Month 1: Foundation & PoC (Sprint 1-2)

**목표**: 기술적 타당성 검증 및 데이터 파이프라인 구축

**Week 1-2 (Sprint 1)**
- 아키텍처 설계 및 기술 스택 확정
- Neo4j 클러스터 구성 및 RKG 스키마 설계
- Kafka 기반 스트리밍 인프라 구축
- Tier 1 언론사 대상 크롤러 PoC

**Week 3-4 (Sprint 2)**  
- NLP 파이프라인 구축
  - 한국어 NER (spaCy + KoNLPy)
  - Risk Signal Detection 룰 엔진
- 기초 GraphDB 데이터 적재 시작
- 첫 번째 엔드투엔드 데이터 흐름 검증

**Deliverable**: 일 1만건 뉴스 처리 가능한 파이프라인

### Month 2: Passive RM MVP (Sprint 3-4)

**목표**: 첫 파일럿 고객에게 수동적 리스크 관리 MVP 제공

**Week 5-6 (Sprint 3)**
- RKG 관계 추론 엔진 개발
  - Graph Algorithm 구현 (PageRank, Community Detection)
  - Risk Propagation 모델
- LLM 기반 Report Generator
  - GPT-4/Claude API 통합
  - 리스크 요약 및 인사이트 생성

**Week 7-8 (Sprint 4)**
- 웹 대시보드 MVP
  - React 기반 SPA
  - Risk Map 시각화 (D3.js)
  - 데일리 브리핑 이메일 시스템
- 3개 파일럿 고객 온보딩

**Deliverable**: CEO Daily Report MVP 1.0

### Month 3: RKG 고도화 & Active RM 프로토타입 (Sprint 5-6)

**목표**: Active RM 핵심 기능 구현 및 상용화 준비

**Week 9-10 (Sprint 5)**
- 캘린더 연동 및 컨텍스트 파악
  - Google/MS Calendar OAuth 연동
  - 미팅 정보 자동 추출
- 대화형 인터페이스 프로토타입
  - GraphQL 기반 질의 API
  - 자연어 처리 (Intent Classification)

**Week 11-12 (Sprint 6)**
- 시스템 안정화 및 성능 최적화
- 운영 모니터링 시스템 구축
  - Prometheus + Grafana
  - 로그 수집 및 분석 (ELK Stack)
- 정식 런칭 준비

**Deliverable**: Active RM 프로토타입 포함 통합 플랫폼

## 기술 스택 선정

### 핵심 기술 스택

**Data Layer**
- **수집**: Python (Scrapy), Apache Airflow
- **스트리밍**: Apache Kafka (AWS MSK)
- **저장**: 
  - Raw Data: AWS S3
  - Structured: PostgreSQL
  - **Graph: Neo4j Enterprise** (핵심)

**ML/AI Layer**
- **NLP**: spaCy, KoNLPy, Hugging Face
- **LLM**: OpenAI GPT-4, Claude API
- **GraphRAG**: LangChain + Neo4j Vector Index
- **MLOps**: MLflow, Weights & Biases

**Application Layer**
- **Backend**: FastAPI (Python), GraphQL
- **Frontend**: Next.js 14, TypeScript, TailwindCSS
- **Visualization**: D3.js, Cytoscape.js
- **Real-time**: WebSocket (Socket.io)

**Infrastructure**
- **Cloud**: AWS (Primary)
- **Container**: Docker, Kubernetes (EKS)
- **CI/CD**: GitHub Actions, ArgoCD
- **Monitoring**: Prometheus, Grafana, Sentry

### 기술 선정 근거

1. **Neo4j 선택 이유**
   - 복잡한 관계 질의에 최적화 (수십 hop traversal)
   - Cypher 쿼리 언어의 직관성
   - Graph Data Science 라이브러리 제공
   - 기업용 기능 (HA, 백업, 보안) 완비

2. **Kafka 선택 이유**
   - 대용량 실시간 스트림 처리 검증
   - 내결함성 및 확장성
   - 정확히 한 번(Exactly-once) 전달 보장

3. **FastAPI + GraphQL 조합**
   - 높은 성능과 자동 문서화
   - 복잡한 그래프 데이터 질의에 최적
   - 타입 안정성 보장

## Risk Knowledge Graph (RKG) 설계

### Core Node Types

```cypher
// 핵심 엔티티
(:Company {
  companyId: string (LEI/사업자번호),
  name: string,
  aliases: string[],
  sector: string,
  marketCapKRW: float,
  riskScore: float,
  updatedAt: datetime
})

(:Person {
  personId: string,
  fullName: string,
  roles: string[],
  primaryCompanyId: string,
  riskScore: float
})

(:Event {
  eventId: UUID,
  eventType: enum (Merger, Lawsuit, Regulation, Scandal...),
  title: string,
  severity: int (1-5),
  eventDate: datetime,
  sourceUri: string
})

(:Risk {
  riskId: UUID,
  category: enum (Financial, Regulatory, Reputational...),
  impact: float,
  probability: float,
  description: string
})
```

### Key Relationships

```cypher
// 관계 정의
(:Person)-[:LEADS {role, sinceDate}]->(:Company)
(:Company)-[:COMPETES_WITH {similarity}]->(:Company)
(:Company)-[:PARTNERS_WITH {since}]->(:Company)
(:Company)-[:INVOLVED_IN {role}]->(:Event)
(:Event)-[:CREATES]->(:Risk)
(:Risk)-[:AFFECTS {impact}]->(:Company)
(:Event)-[:MENTIONED_IN {confidence}]->(:Source)
```

### 인덱스 및 제약조건

```cypher
CREATE CONSTRAINT company_id_unique ON (c:Company) ASSERT c.companyId IS UNIQUE;
CREATE INDEX company_name_idx FOR (c:Company) ON (c.name);
CREATE INDEX event_date_idx FOR (e:Event) ON (e.eventDate);
CREATE FULLTEXT INDEX company_search FOR (c:Company) ON (c.name, c.aliases);
```

### Graph Algorithms 활용

1. **Risk Propagation**: 리스크가 네트워크를 통해 전파되는 경로 분석
2. **Community Detection**: 밀접하게 연결된 기업 그룹 식별
3. **Link Prediction**: 미래에 발생 가능한 관계 예측
4. **Centrality Analysis**: 네트워크에서 중요한 노드 식별

## 시스템 아키텍처

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                    │
│         Risk Dashboard │ Reports │ Chat Interface       │
└────────────────────┬───────────────────────────────────┘
                     │ GraphQL/WebSocket
┌────────────────────┴───────────────────────────────────┐
│                  API Gateway (Kong)                     │
└────────────────────┬───────────────────────────────────┘
                     │
┌────────────────────┴───────────────────────────────────┐
│              Application Services (MSA)                 │
│  ┌─────────────┐ ┌──────────────┐ ┌─────────────┐    │
│  │Report Engine│ │Risk Analyzer │ │Chat Service │    │
│  └─────────────┘ └──────────────┘ └─────────────┘    │
└────────────────────┬───────────────────────────────────┘
                     │
┌────────────────────┴───────────────────────────────────┐
│                    ML/AI Layer                          │
│  ┌──────────┐ ┌───────────┐ ┌──────────────────┐     │
│  │   NLP    │ │    LLM    │ │   GraphRAG       │     │
│  └──────────┘ └───────────┘ └──────────────────┘     │
└────────────────────┬───────────────────────────────────┘
                     │
┌────────────────────┴───────────────────────────────────┐
│                  Data Layer                             │
│  ┌──────────┐ ┌───────────┐ ┌──────────────────┐     │
│  │PostgreSQL│ │   Neo4j   │ │   Kafka/S3       │     │
│  └──────────┘ └───────────┘ └──────────────────┘     │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Ingestion**: 크롤러 → Kafka → Stream Processor
2. **Enrichment**: NLP Service → Entity/Relation Extraction
3. **Storage**: Neo4j (Graph) + PostgreSQL (Meta) + S3 (Raw)
4. **Query**: GraphQL → Neo4j Cypher → Response
5. **Real-time**: WebSocket → Event Stream → Client Update

### 주요 설계 원칙

1. **Microservices Architecture**: 각 서비스 독립 배포/확장
2. **Event-Driven**: Kafka 중심의 비동기 처리
3. **API-First**: GraphQL 통한 일관된 인터페이스
4. **Cloud-Native**: 컨테이너 기반, 자동 확장
5. **Security by Design**: Zero-trust, 암호화, RBAC

## 예상 도전 과제 및 대응 방안

### 기술적 도전 과제

1. **대용량 그래프 성능**
   - 문제: 수백만 노드/엣지 처리 시 쿼리 성능 저하
   - 해결: 샤딩, 캐싱, 그래프 요약 기법 적용

2. **한국어 NLP 정확도**
   - 문제: 도메인 특화 용어, 신조어 처리
   - 해결: Custom NER 모델 학습, 지속적 사전 업데이트

3. **실시간 처리 지연**
   - 문제: 뉴스 발생 → 알림까지 지연
   - 해결: 스트림 처리 최적화, 우선순위 큐 도입

### 비즈니스 도전 과제

1. **CEO 사용성**
   - 문제: 복잡한 데이터에 대한 거부감
   - 해결: 극도로 단순화된 UI, 3분 요약 원칙

2. **데이터 신뢰성**
   - 문제: 잘못된 정보로 인한 신뢰 상실
   - 해결: 멀티소스 검증, 신뢰도 스코어링

3. **가격 정당화**
   - 문제: ROI 증명의 어려움
   - 해결: 리스크 회피 사례 정량화, Success Story 축적

## 향후 발전 방향

### Phase 3: Intelligence Platform (6개월 후)

1. **예측 분석 고도화**
   - Graph Neural Network 기반 리스크 예측
   - 시계열 분석 통합

2. **산업별 특화 모델**
   - 금융, 제조, IT 등 섹터별 커스터마이징
   - 도메인 전문가 협업

3. **글로벌 확장**
   - 다국어 지원 (영어, 중국어, 일본어)
   - 해외 데이터 소스 통합

### Long-term Vision

**"프로그래매틱 미디어 파트너"에서 "인텔리전스 플랫폼 기업"으로**

- 기존 서비스 수익 + SaaS 구독 수익의 이중 구조
- 데이터 네트워크 효과를 통한 진입 장벽 구축
- M&A나 IPO를 위한 기업 가치 극대화

## 결론

RiskRadar 프로젝트는 MIQ의 미래를 위한 필수적인 전략적 투자입니다. 단순히 새로운 제품을 만드는 것이 아니라, 회사의 비즈니스 모델을 근본적으로 혁신하는 변곡점이 될 것입니다.

**핵심 성공 요인**
1. 그래프 기반 기술의 차별화된 가치
2. 한국 200대 기업 CEO라는 명확한 타겟
3. MIQ의 기존 전문성과 신기술의 융합
4. 단계적 접근을 통한 리스크 관리

3개월 내 MVP 출시를 시작으로, MIQ는 기술 기반의 확장 가능한 비즈니스 모델을 확보하고, 프로그래매틱 광고를 넘어 기업 인텔리전스 시장의 리더로 도약할 수 있을 것입니다.

---

*작성일: 2025-07-18*  
*작성자: Head of Engineering Candidate*