# Graph Service 성능 테스트

## 개요

Graph Service의 성능을 측정하고 벤치마킹하기 위한 테스트 모음입니다.

## 테스트 구성

### 1. 쿼리 성능 테스트 (`test_query_performance.py`)

- **단순 노드 조회**: ID 인덱스를 사용한 조회 성능
- **패턴 매칭**: 1-hop 관계 탐색 성능
- **집계 쿼리**: 대량 노드에 대한 집계 연산
- **다중 홉 탐색**: 2-hop 네트워크 분석
- **동시 쿼리**: 여러 쿼리 동시 처리
- **쓰기 성능**: 단일 및 배치 쓰기
- **인덱스 효과성**: 인덱스 유무에 따른 성능 차이

### 2. 로드 성능 테스트 (`test_load_performance.py`)

- **메시지 처리량**: Kafka 메시지 처리 속도
- **동시 처리**: 병렬 메시지 처리
- **대량 노드 생성**: 배치 크기별 성능
- **관계 생성**: 대량 관계 생성 성능
- **메모리 사용**: 대용량 결과 처리
- **트랜잭션 격리**: 동시 트랜잭션 처리

## 실행 방법

### 전체 성능 테스트 실행

```bash
pytest tests/performance/ -v -m performance
```

### 특정 테스트만 실행

```bash
# 쿼리 성능만
pytest tests/performance/test_query_performance.py -v

# 로드 성능만
pytest tests/performance/test_load_performance.py -v
```

### 상세 출력과 함께 실행

```bash
pytest tests/performance/ -v -s -m performance
```

## 성능 기준

### 쿼리 성능 기준

| 테스트 | 기준 | 설명 |
|--------|------|------|
| 인덱스 조회 | < 10ms | ID로 단일 노드 조회 |
| 1-hop 탐색 | < 50ms | 직접 연결된 노드 탐색 |
| 집계 쿼리 (5K) | < 100ms | 5000개 노드 집계 |
| 2-hop 탐색 | < 200ms | 2단계 네트워크 분석 |
| 동시 쿼리 (20) | < 1s | 20개 쿼리 동시 처리 |

### 로드 성능 기준

| 테스트 | 기준 | 설명 |
|--------|------|------|
| 메시지 처리 | > 3 msg/sec | Kafka 메시지 처리량 |
| 노드 생성 | > 200 nodes/sec | 배치 노드 생성 속도 |
| 관계 생성 | > 250 rels/sec | 관계 생성 속도 |

## 성능 최적화 팁

### 1. 인덱스 활용

```cypher
// 자주 검색되는 필드에 인덱스 생성
CREATE INDEX company_name IF NOT EXISTS FOR (c:Company) ON (c.name)
CREATE INDEX company_risk IF NOT EXISTS FOR (c:Company) ON (c.risk_score)
```

### 2. 배치 처리

```python
# 개별 처리 대신 배치 사용
operations = [(query1, params1), (query2, params2), ...]
tm.batch_write(operations, batch_size=100)
```

### 3. 쿼리 최적화

```cypher
// Bad: 전체 스캔
MATCH (n) WHERE n.name = 'Samsung' RETURN n

// Good: 레이블과 인덱스 사용
MATCH (n:Company {name: 'Samsung'}) RETURN n
```

### 4. 연결 풀 설정

```python
driver = Neo4jDriver(
    max_connection_pool_size=50,
    connection_acquisition_timeout=30
)
```

## 모니터링

### Neo4j 쿼리 로그 확인

```cypher
// 느린 쿼리 확인
CALL dbms.listQueries() 
YIELD query, elapsedTimeMillis 
WHERE elapsedTimeMillis > 1000
RETURN query, elapsedTimeMillis
```

### 메모리 사용량 확인

```cypher
CALL dbms.components() 
YIELD name, versions, edition
RETURN name, versions, edition
```

## 결과 분석

성능 테스트 실행 후 다음 항목을 확인하세요:

1. **평균 응답 시간**: 각 작업의 평균 소요 시간
2. **처리량**: 초당 처리 가능한 작업 수
3. **리소스 사용률**: CPU, 메모리 사용량
4. **병목 지점**: 가장 느린 작업 식별

## 주의사항

- 성능 테스트는 격리된 환경에서 실행하세요
- 테스트 전 충분한 워밍업을 수행하세요
- 테스트 데이터는 실제 환경과 유사하게 구성하세요
- 여러 번 실행하여 일관된 결과를 확인하세요