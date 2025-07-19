# Phase 1 Sprint 상세 계획
# Sprint Breakdown for Phase 1

## 1. Sprint 구성 개요

Phase 1 (4주)를 3개의 Sprint로 구성하여 빠른 통합 주기를 실현합니다.

```
Sprint 0 (Week 1): Walking Skeleton with Mocks
Sprint 1 (Week 2): Core Features Implementation  
Sprint 2 (Week 3-4): Full Integration & Optimization
```

## 2. Sprint 0: Walking Skeleton (Week 1)

### 2.1 전체 목표
**"Mock 데이터가 전 구간을 통과하는 것을 확인"**

### 2.2 Squad별 상세 태스크

#### Data Squad (3 days)
```yaml
Day 1-2: Mock 크롤러 및 Kafka Producer
  - [ ] Mock 뉴스 데이터 생성기 구현
  - [ ] Kafka Producer 설정 (실제 Kafka 사용)
  - [ ] 데이터 포맷 v0.1 정의
  - [ ] Health check endpoint 구현

Day 3: 통합 테스트
  - [ ] 다른 Squad와 연동 테스트
  - [ ] 메시지 발행 확인
  - [ ] 문서화

산출물:
  - mock_crawler.py
  - kafka_producer.py
  - data_format_v0.1.json
  - README.md
```

#### ML/NLP Squad (3 days)
```yaml
Day 1-2: Mock NLP Processor
  - [ ] Kafka Consumer 설정
  - [ ] Mock NLP 결과 생성기
  - [ ] Kafka Producer (enriched topic)
  - [ ] 기본 API endpoint

Day 3: 통합 테스트
  - [ ] Input/Output 검증
  - [ ] 처리 시간 측정
  - [ ] 에러 핸들링

산출물:
  - mock_nlp_processor.py
  - nlp_consumer.py
  - nlp_api.py
  - test_integration.py
```

#### Graph Squad (3 days)
```yaml
Day 1-2: In-Memory Graph Store
  - [ ] 간단한 메모리 기반 그래프 구조
  - [ ] Kafka Consumer 설정
  - [ ] 기본 CRUD API
  - [ ] GraphQL 스키마 v0.1

Day 3: 통합 테스트
  - [ ] 엔티티 저장 확인
  - [ ] 쿼리 동작 테스트
  - [ ] API 응답 검증

산출물:
  - in_memory_graph.py
  - graphql_schema_v0.1.graphql
  - graph_api.py
  - mock_data.json
```

#### Platform Squad (3 days)
```yaml
Day 1: Local 개발 환경
  - [ ] Docker Compose 설정
  - [ ] Kafka 단일 노드 구성
  - [ ] 네트워크 설정
  - [ ] 볼륨 마운트 구성

Day 2: 컨테이너화
  - [ ] 각 서비스 Dockerfile 작성 지원
  - [ ] 빌드 스크립트
  - [ ] 환경 변수 관리

Day 3: 통합 지원
  - [ ] 전체 서비스 구동 스크립트
  - [ ] 로그 수집 설정
  - [ ] 문제 해결 지원

산출물:
  - docker-compose.yml
  - Makefile
  - .env.example
  - setup.sh
```

#### Product Squad (3 days)
```yaml
Day 1-2: Mock UI 구현
  - [ ] Next.js 프로젝트 설정
  - [ ] 기본 레이아웃 구성
  - [ ] Mock 데이터 표시 컴포넌트
  - [ ] GraphQL 클라이언트 설정

Day 3: 통합 테스트
  - [ ] API 연결 테스트
  - [ ] 데이터 플로우 확인
  - [ ] UI 렌더링 검증

산출물:
  - pages/index.tsx
  - components/MockDashboard.tsx
  - lib/graphql-client.ts
  - __tests__/integration.test.ts
```

### 2.3 일일 통합 체크포인트

```yaml
Day 1 (월요일):
  09:00 - Kickoff: 전체 아키텍처 리뷰
  14:00 - Check: 개발 환경 설정 완료
  17:00 - Sync: 진행 상황 공유

Day 2 (화요일):
  09:00 - Standup: 블로킹 이슈 확인
  14:00 - Check: Mock 구현 진행도
  17:00 - Test: 개별 컴포넌트 테스트

Day 3 (수요일):
  09:00 - Standup: 통합 준비 상태
  11:00 - Integration: 전체 연동 시작
  14:00 - Debug: 통합 이슈 해결
  17:00 - Demo: Sprint 0 데모

Day 4-5 (목-금요일):
  - Sprint 1 준비
  - 문서 정리
  - 회고
```

## 3. Sprint 1: Core Features (Week 2)

### 3.1 전체 목표
**"실제 데이터로 기본 기능 구현"**

### 3.2 Squad별 상세 태스크

#### Data Squad (5 days)
```yaml
Day 1-2: 실제 크롤러 1개
  - [ ] 조선일보 크롤러 구현
  - [ ] HTML 파싱 로직
  - [ ] 에러 처리 및 재시도
  - [ ] 스케줄링 (5분 간격)

Day 3-4: 데이터 정규화
  - [ ] 데이터 정제 로직
  - [ ] 중복 제거 (URL 기반)
  - [ ] 메타데이터 추가
  - [ ] 신뢰도 점수 계산

Day 5: 모니터링
  - [ ] 크롤링 통계 API
  - [ ] 실패율 모니터링
  - [ ] Prometheus 메트릭

기능 목표:
  - 시간당 100개 기사 수집
  - 중복률 < 10%
  - 에러율 < 5%
```

#### ML/NLP Squad (5 days)
```yaml
Day 1-2: 기본 NLP 파이프라인
  - [ ] KoNLPy 통합
  - [ ] 형태소 분석
  - [ ] 문장 분리
  - [ ] 전처리 로직

Day 3-4: 엔티티 추출
  - [ ] 정규식 기반 회사명 추출
  - [ ] 사전 기반 매칭
  - [ ] 신뢰도 점수
  - [ ] 결과 포맷팅

Day 5: 감정 분석
  - [ ] 규칙 기반 감정 분석
  - [ ] 키워드 추출
  - [ ] 성능 최적화

기능 목표:
  - 기사당 처리 시간 < 200ms
  - 회사명 추출 정확도 > 70%
  - 처리량: 초당 5개
```

#### Graph Squad (5 days)
```yaml
Day 1-2: Neo4j 기본 구성
  - [ ] Neo4j 단일 인스턴스 설정
  - [ ] 기본 스키마 구현
  - [ ] 제약조건 및 인덱스
  - [ ] 연결 풀 설정

Day 3-4: 엔티티 관리
  - [ ] Company 노드 CRUD
  - [ ] 엔티티 매칭 로직
  - [ ] 관계 생성 (MENTIONED_IN)
  - [ ] 트랜잭션 관리

Day 5: 쿼리 API
  - [ ] 기본 GraphQL resolver
  - [ ] 회사 조회 쿼리
  - [ ] 최근 뉴스 쿼리
  - [ ] 성능 측정

기능 목표:
  - 노드 생성: 초당 100개
  - 쿼리 응답: < 100ms
  - 동시 연결: 50개
```

#### Platform Squad (5 days)
```yaml
Day 1-2: Minikube 환경
  - [ ] Local K8s 클러스터
  - [ ] 네임스페이스 구성
  - [ ] ConfigMap/Secret
  - [ ] Service 정의

Day 3-4: 기본 배포
  - [ ] Deployment YAML
  - [ ] 롤링 업데이트 설정
  - [ ] 리소스 제한
  - [ ] Health probe

Day 5: 모니터링 기초
  - [ ] kubectl 대시보드
  - [ ] 로그 수집 (Fluentd)
  - [ ] 기본 알림
  - [ ] 트러블슈팅 가이드

기능 목표:
  - 모든 서비스 K8s 배포
  - 자동 재시작 설정
  - 로그 중앙화
```

#### Product Squad (5 days)
```yaml
Day 1-2: GraphQL Gateway
  - [ ] Apollo Server 설정
  - [ ] 스키마 통합
  - [ ] Resolver 구현
  - [ ] DataLoader 설정

Day 3-4: 기본 대시보드
  - [ ] 메인 레이아웃
  - [ ] 회사 목록 컴포넌트
  - [ ] 리스크 점수 표시
  - [ ] 뉴스 타임라인

Day 5: 인증 기초
  - [ ] JWT 토큰 생성
  - [ ] 로그인 페이지
  - [ ] 인증 미들웨어
  - [ ] 세션 관리

기능 목표:
  - GraphQL 쿼리 5개
  - 페이지 로드 < 3초
  - 모바일 반응형
```

## 4. Sprint 2: Full Integration (Week 3-4)

### 4.1 전체 목표
**"프로덕션 준비 완료"**

### 4.2 Week 3: 기능 확장

#### 모든 Squad 공통
- 5개 뉴스 소스 확장
- ML 모델 통합
- 복잡한 쿼리 구현
- 성능 최적화
- 에러 처리 고도화

### 4.3 Week 4: 통합 및 최적화

#### 주요 활동
- 전체 시스템 성능 테스트
- 보안 점검
- 문서화 완성
- 배포 준비
- 최종 데모

## 5. 검증 방법

### 5.1 Sprint 0 검증 (Mock)
```bash
# 전체 플로우 테스트
curl -X POST http://localhost:8001/generate-mock-news
sleep 5
curl http://localhost:3000/api/companies/mock-samsung | jq .
```

### 5.2 Sprint 1 검증 (Basic)
```bash
# 실제 뉴스 처리 확인
curl http://localhost:8001/stats | jq .crawled_count
curl http://localhost:8002/health | jq .processed_count
curl http://localhost:4000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ companies { name riskScore } }"}'
```

### 5.3 Sprint 2 검증 (Full)
```bash
# 성능 테스트
k6 run performance-test.js
# 목표: 100 concurrent users, <200ms response time
```

## 6. 리스크 관리

### 6.1 Sprint별 리스크
| Sprint | Risk | Impact | Mitigation |
|--------|------|--------|------------|
| Sprint 0 | 통합 실패 | High | Mock 우선, 단순화 |
| Sprint 1 | 실제 데이터 처리 어려움 | Medium | 데이터 양 제한 |
| Sprint 2 | 성능 미달 | Medium | 점진적 최적화 |

### 6.2 빠른 피드백 루프
- 일일 통합 테스트
- 즉각적인 이슈 해결
- Pair programming
- Code review 필수

## 7. Definition of Done

### Sprint 0
- [ ] Mock 데이터 E2E 플로우 성공
- [ ] 모든 서비스 Health Check 통과
- [ ] Integration test 1개 이상 통과
- [ ] README 문서 작성

### Sprint 1  
- [ ] 실제 데이터 처리 확인
- [ ] 기본 기능 동작
- [ ] Unit test coverage > 50%
- [ ] API 문서 생성

### Sprint 2
- [ ] 모든 기능 요구사항 충족
- [ ] 성능 목표 달성
- [ ] 보안 체크리스트 통과
- [ ] 운영 문서 완성