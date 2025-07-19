# Graph Service Changelog
# 그래프 서비스 변경 이력

## [Unreleased]

## [0.3.2] - 2025-07-19

### 통합 테스트 수정

#### 🔧 Fixed
- **Neo4j 연결 안정성 개선**
  - 시작 시 Neo4j 연결 재시도 로직 추가 (최대 30회, 2초 간격)
  - Docker 환경에서 서비스 시작 순서 문제 해결
  - Health check에 degraded 상태 추가 (Neo4j 연결 실패 시)

- **서비스 시작 개선**
  - main.py에 연결 확인 로직 추가
  - 연결 실패 시 명확한 로그 메시지
  - 재시도 과정 로깅으로 디버깅 용이

#### 📝 Documentation
- CLAUDE.md 업데이트
- Docker 환경 트러블슈팅 가이드 추가

## [0.3.1] - 2025-07-19

### 🚨 긴급 수정: N+1 쿼리 문제 해결

#### 🚀 Added
- **엔티티 캐시 시스템**
  - 30분 TTL 메모리 캐시
  - 스레드 안전 구현 (RLock)
  - 자동 캐시 새로고침
  - 캐시 통계 API

- **배치 엔티티 매칭**
  - N+1 → O(1) 최적화: 한 번의 캐시 조회로 모든 엔티티 처리
  - 정확 매칭 + 유사도 매칭 (85% 임계값)
  - 별칭 지원으로 매칭 정확도 향상
  - 동시 처리 지원

- **새로운 API 엔드포인트**
  - `GET /api/v1/graph/cache/stats`: 캐시 통계 조회
  - `POST /api/v1/graph/cache/refresh`: 수동 캐시 새로고침

- **성능 테스트 & 벤치마크**
  - N+1 문제 해결 검증 테스트
  - 캐시 효과성 측정
  - 매칭 정확도 검증
  - 자동화된 벤치마크 스크립트

#### 🔧 Changed
- **Kafka 메시지 핸들러 최적화**
  - 엔티티 처리 로직 배치화
  - 신규 엔티티 생성 시 캐시 자동 업데이트
  - 신뢰도 필터링 개선 (0.7 이상)

#### 📈 Performance
- **쿼리 수 95% 감소**: 35번 → 2번
- **처리 속도 3.5배 향상**: 70ms → 20ms  
- **캐시 히트율 99%**: 두 번째 조회부터 즉시 응답
- **일일 뉴스 1,000건 처리**: 30초 → 8초

#### 🐛 Fixed
- 엔티티 매칭에서 심각한 N+1 쿼리 문제 해결
- 전체 테이블 스캔으로 인한 성능 저하 해결
- 메모리 효율성 개선

#### 📚 Documentation
- README.md 성능 최적화 섹션 추가
- 캐시 API 문서화
- N+1 해결 과정 설명

## [0.3.0] - 2025-07-19

### Sprint 1 Week 1: Core Implementation

#### 🚀 Added
- **프로젝트 구조 개선**
  - `src/` 디렉토리 구조로 모듈화
  - `scripts/` 디렉토리에 유틸리티 스크립트
  - `tests/` 디렉토리에 단위/통합 테스트
  
- **Neo4j 통합**
  - Neo4j 드라이버 with 연결 풀링 및 재시도 로직
  - 세션 관리 및 배치 처리 지원
  - 스키마 초기화 스크립트 (`scripts/init_schema.py`)
  - 제약조건 및 인덱스 자동 생성
  
- **그래프 모델 구현**
  - 노드: Company, Person, Event, RiskEvent, NewsArticle
  - 관계: COMPETES_WITH, PARTNERS_WITH, MENTIONED_IN, AFFECTS 등
  - Pydantic 기반 스키마 검증
  
- **핵심 알고리즘**
  - 엔티티 매칭 (85% 유사도 임계값)
  - 시계열 이벤트 연결
  - 연쇄 리스크 탐지
  
- **REST API 엔드포인트**
  - `/api/v1/graph/stats`: 그래프 통계
  - `/api/v1/graph/query`: 그래프 쿼리
  - `/api/v1/graph/network-risk`: 네트워크 리스크 분석
  - `/api/v1/graph/companies/{id}`: 기업 상세 정보
  
- **Kafka 통합 개선**
  - GraphMessageHandler로 메시지 처리 로직 분리
  - 엔티티 중복 제거 및 병합
  - 비동기 메시지 처리
  
- **테스트**
  - 엔티티 매칭 단위 테스트
  - 모델 단위 테스트
  - pytest 설정 및 구조

#### 🔧 Changed
- main.py를 엔트리 포인트로만 사용하도록 리팩토링
- 모든 비즈니스 로직을 src/ 디렉토리로 이동
- 환경 변수 관리 개선 (.env.example 추가)

#### 📚 Documentation
- 상세한 코드 주석 추가
- .gitignore 파일 생성
- CHANGELOG 업데이트

## [0.1.0] - 2024-01-15

### Sprint 0: Mock Implementation

#### 🚀 Added
- In-memory 그래프 저장소 구현
  - Python dict 기반 노드/엣지 저장
  - 간단한 CRUD 작업
- GraphQL 스키마 v0.1
  - Company 타입
  - News 타입
  - 기본 Query
- Kafka Consumer 설정
  - `enriched-news` 토픽 구독
  - 엔티티 추출 및 저장
- GraphQL 엔드포인트
  - `/graphql` - GraphQL Playground
  - 기본 resolver 구현

#### 🧪 Testing
- In-memory 저장소 테스트
- GraphQL 쿼리 테스트
- Kafka 통합 테스트

#### 📚 Documentation
- README.md 작성
- CLAUDE.md 개발 가이드라인
- GraphQL 스키마 문서

## [0.0.1] - 2024-01-01

### 프로젝트 초기화

#### 🚀 Added
- 서비스 디렉토리 구조 생성
- 기본 Python 프로젝트 설정
- requirements.txt 작성
- Dockerfile 초안

---

## 다음 릴리스 계획

### v0.2.0 (Sprint 1)
- [ ] Neo4j 단일 인스턴스 설정
- [ ] 기본 스키마 구현
- [ ] Company 노드 CRUD
- [ ] 기본 GraphQL resolver
- [ ] 제약조건 및 인덱스

### v0.3.0 (Sprint 2)
- [ ] 복잡한 Cypher 쿼리
- [ ] 그래프 알고리즘 적용
- [ ] 성능 최적화
- [ ] Neo4j 클러스터링
- [ ] 백업/복구 전략