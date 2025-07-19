# Neo4j Enterprise Cluster
# RiskRadar Graph Service

## 개요

이 디렉토리는 RiskRadar Graph Service를 위한 Neo4j Enterprise 클러스터 설정을 포함합니다.

### 클러스터 구성

- **Core Servers**: 3개 (neo4j-core-1, neo4j-core-2, neo4j-core-3)
- **Read Replicas**: 1개 (neo4j-replica-1)
- **Load Balancer**: HAProxy
- **고가용성**: 99.9% 가용성 목표

## 빠른 시작

### 1. 클러스터 시작
```bash
# 클러스터 시작 (자동 설정)
./scripts/cluster-setup.sh start

# 또는 Docker Compose 직접 사용
docker-compose -f docker-compose.cluster.yml up -d
```

### 2. 클러스터 상태 확인
```bash
# 클러스터 상태 확인
./scripts/cluster-setup.sh status

# 개별 서버 상태 확인
docker exec neo4j-core-1 cypher-shell -u neo4j -p riskradar2024 "SHOW SERVERS"
```

### 3. 클러스터 접속
```bash
# Primary (읽기/쓰기)
bolt://localhost:7687

# Read-only
bolt://localhost:7688

# HTTP Browser
http://localhost:7474
```

## 네트워크 구성

### 포트 매핑

| 서비스 | HTTP | Bolt | 백업 | 메트릭 |
|--------|------|------|------|--------|
| Core-1 | 7474 | 7687 | 6362 | 2004 |
| Core-2 | 7475 | 7688 | 6362 | 2004 |
| Core-3 | 7476 | 7689 | 6362 | 2004 |
| Replica-1 | 7477 | 7690 | - | 2004 |
| HAProxy | 7474 | 7687/7688 | - | 8404 |

### 로드 밸런싱

**HAProxy 구성:**
- **쓰기 작업**: Core 서버로 라운드 로빈
- **읽기 작업**: Read Replica 우선, Core 서버 백업
- **헬스 체크**: 자동 장애 감지 및 복구

## 성능 설정

### 메모리 구성
- **Heap Size**: 2G ~ 4G per server
- **Page Cache**: 2G per server
- **Transaction Memory**: 1G max

### 클러스터 설정
- **최소 Core 서버**: 3개
- **리더 선출 타임아웃**: 7초
- **조인 타임아웃**: 10분

## 모니터링

### 메트릭 엔드포인트
```bash
# Prometheus 메트릭
curl http://localhost:2004/metrics

# HAProxy 통계
curl http://localhost:8404/stats

# 클러스터 헬스 체크
curl http://localhost:8080/health
```

### 주요 메트릭
- 클러스터 상태 (Leader/Follower)
- 트랜잭션 처리량
- 쿼리 응답 시간
- 메모리 사용률

## 백업 및 복구

### 자동 백업
```bash
# 백업 생성
./scripts/cluster-setup.sh backup

# 백업 위치
./backups/YYYYMMDD_HHMMSS/
```

### 수동 백업
```bash
# 데이터베이스 덤프
docker exec neo4j-core-1 neo4j-admin dump --database=graph --to=/var/lib/neo4j/backup/graph.dump

# 백업 파일 복사
docker cp neo4j-core-1:/var/lib/neo4j/backup/graph.dump ./backups/
```

### 복구
```bash
# 데이터베이스 복구
docker exec neo4j-core-1 neo4j-admin load --from=/var/lib/neo4j/backup/graph.dump --database=graph --force
```

## 보안 설정

### 인증
- **사용자명**: neo4j
- **비밀번호**: riskradar2024
- **최소 비밀번호 길이**: 8자

### 네트워크 보안
- 클러스터 간 통신 암호화
- TLS 설정 (선택적)
- 방화벽 규칙 적용

## 문제 해결

### 일반적인 문제

#### 1. 클러스터 형성 실패
```bash
# 로그 확인
docker logs neo4j-core-1

# 네트워크 확인
docker network ls | grep neo4j

# 포트 확인
netstat -tulpn | grep 7687
```

#### 2. 메모리 부족
```bash
# 메모리 사용량 확인
docker stats

# Heap 크기 조정 (neo4j.conf)
dbms.memory.heap.max_size=6g
```

#### 3. 디스크 공간 부족
```bash
# 디스크 사용량 확인
docker exec neo4j-core-1 df -h

# 로그 정리
docker exec neo4j-core-1 find /logs -name "*.log" -mtime +7 -delete
```

### 클러스터 재시작
```bash
# 전체 클러스터 재시작
./scripts/cluster-setup.sh restart

# 개별 서버 재시작
docker restart neo4j-core-1
```

### 로그 확인
```bash
# 모든 서비스 로그
docker-compose -f docker-compose.cluster.yml logs -f

# 특정 서비스 로그
docker logs -f neo4j-core-1
```

## 개발 환경

### 로컬 개발
```bash
# 단일 노드로 시작 (개발용)
docker run -d \
  --name neo4j-dev \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5.0
```

### 클러스터 개발
```bash
# 최소 클러스터 (2 core + 1 replica)
docker-compose -f docker-compose.cluster.yml up -d neo4j-core-1 neo4j-core-2 neo4j-replica-1
```

## 프로덕션 고려사항

### 하드웨어 요구사항
- **CPU**: 8+ cores per server
- **RAM**: 16GB+ per server
- **Storage**: SSD, 500GB+ per server
- **Network**: 1Gbps+ 대역폭

### 운영 체크리스트
- [ ] 정기 백업 설정
- [ ] 모니터링 알림 설정
- [ ] 로그 로테이션 설정
- [ ] 보안 감사 설정
- [ ] 성능 튜닝 적용

## 참고 자료

- [Neo4j Clustering Guide](https://neo4j.com/docs/operations-manual/current/clustering/)
- [Neo4j Performance Tuning](https://neo4j.com/docs/operations-manual/current/performance/)
- [HAProxy Configuration](https://www.haproxy.org/download/2.8/doc/configuration.txt)