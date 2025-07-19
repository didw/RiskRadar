# Risk Knowledge Graph (RKG) 설계
# RiskRadar Graph Database Design

## 1. 개념 모델

### 1.1 RKG 정의
Risk Knowledge Graph는 기업, 인물, 이벤트, 리스크 간의 복잡한 관계를 표현하는 지식 그래프입니다.

### 1.2 핵심 가치
- **관계 발견**: 숨겨진 리스크 연결고리 파악
- **전파 분석**: 리스크의 간접 영향 추적
- **예측 가능**: 패턴 기반 미래 리스크 예측

## 2. 노드(Node) 설계

### 2.1 Company (기업)
```cypher
(:Company {
  companyId: String,      // "KR-삼성전자"
  name: String,           // "삼성전자"
  aliases: [String],      // ["Samsung", "SEC"]
  sector: String,         // "IT/전자"
  marketCap: Float,       // 400조원
  revenue: Float,         // 연매출
  employees: Integer,     // 직원수
  ceoName: String,        // 대표이사
  riskScore: Float,       // 0-10
  lastUpdated: DateTime
})
```

### 2.2 Person (인물)
```cypher
(:Person {
  personId: String,       // "KR-이재용"
  name: String,           // "이재용"
  role: String,           // "회장"
  company: String,        // "삼성전자"
  influenceScore: Float,  // 영향력 점수
  riskExposure: Float,    // 리스크 노출도
  connections: Integer,   // 관계 수
  lastUpdated: DateTime
})
```

### 2.3 Event (이벤트)
```cypher
(:Event {
  eventId: String,        // "EVT-2024-001"
  type: String,           // "법적분쟁"
  title: String,          // 사건명
  date: DateTime,         // 발생일
  severity: Integer,      // 1-10
  category: String,       // 분류
  impact: Float,          // 영향도
  confidence: Float,      // AI 신뢰도
  source: String,         // 출처
  description: Text
})
```

### 2.4 Risk (리스크)
```cypher
(:Risk {
  riskId: String,         // "RISK-001"
  type: String,           // "시장|신용|운영|규제"
  level: Integer,         // 1-5
  probability: Float,     // 0-1
  impact: Float,          // 예상 손실
  trend: String,          // "상승|유지|하락"
  mitigationCost: Float   // 완화 비용
})
```

### 2.5 News (뉴스)
```cypher
(:News {
  newsId: String,
  title: String,
  content: Text,
  publishedAt: DateTime,
  source: String,
  sentiment: Float,       // -1 to 1
  reliability: Float      // 0-1
})
```

## 3. 관계(Relationship) 설계

### 3.1 비즈니스 관계
```cypher
// 경쟁 관계
(c1:Company)-[:COMPETES_WITH {
  intensity: Float,           // 경쟁 강도
  marketOverlap: Float,       // 시장 중복도
  since: Date
}]->(c2:Company)

// 파트너십
(c1:Company)-[:PARTNERS_WITH {
  type: String,               // "공급|유통|기술"
  value: Float,               // 거래 규모
  dependency: Float,          // 의존도
  since: Date
}]->(c2:Company)

// 투자 관계
(c1:Company)-[:INVESTS_IN {
  amount: Float,              // 투자 금액
  stake: Float,               // 지분율
  date: Date
}]->(c2:Company)
```

### 3.2 인물 관계
```cypher
// 경영진
(p:Person)-[:LEADS {
  role: String,               // "CEO|CFO|CTO"
  since: Date,
  authority: Float            // 권한 수준
}]->(c:Company)

// 인맥
(p1:Person)-[:KNOWS {
  strength: Float,            // 관계 강도
  context: String             // "학연|지연|업무"
}]->(p2:Person)
```

### 3.3 리스크 관계
```cypher
// 리스크 노출
(c:Company)-[:EXPOSED_TO {
  level: Float,               // 노출 수준
  trend: String,              // 추세
  lastAssessed: DateTime
}]->(r:Risk)

// 이벤트 영향
(e:Event)-[:AFFECTS {
  impactScore: Float,         // 영향 점수
  duration: Integer,          // 지속 기간
  financialImpact: Float      // 재무 영향
}]->(c:Company)

// 뉴스 언급
(n:News)-[:MENTIONS {
  sentiment: Float,           // 감정 점수
  relevance: Float            // 관련성
}]->(c:Company)
```

## 4. 그래프 알고리즘

### 4.1 리스크 전파 분석
```cypher
// 1차 리스크 전파
MATCH (source:Company {name: $company})
      -[r:PARTNERS_WITH|COMPETES_WITH]-
      (target:Company)
WITH target, 
     type(r) as relType,
     CASE type(r)
       WHEN 'PARTNERS_WITH' THEN r.dependency * 0.3
       WHEN 'COMPETES_WITH' THEN r.intensity * 0.2
     END as riskTransfer
RETURN target.name, sum(riskTransfer) as totalRisk
ORDER BY totalRisk DESC
```

### 4.2 영향력 분석 (PageRank)
```cypher
CALL gds.pageRank.stream('businessNetwork', {
  relationshipWeightProperty: 'dependency',
  dampingFactor: 0.85
})
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).name AS company,
       score AS influenceScore
ORDER BY score DESC
LIMIT 20
```

### 4.3 커뮤니티 탐지
```cypher
CALL gds.louvain.stream('businessNetwork')
YIELD nodeId, communityId
WITH communityId, 
     collect(gds.util.asNode(nodeId)) AS members
WHERE size(members) >= 3
RETURN communityId,
       [m IN members | m.name] AS companies,
       avg([m IN members | m.riskScore]) AS avgRisk
```

### 4.4 최단 경로 분석
```cypher
// 두 기업 간 리스크 경로
MATCH path = shortestPath(
  (c1:Company {name: $company1})-[*..5]-
  (c2:Company {name: $company2})
)
RETURN path,
       length(path) as distance,
       [n IN nodes(path) | n.name] as companies
```

## 5. 인덱스 및 제약조건

### 5.1 유니크 제약조건
```cypher
CREATE CONSTRAINT company_id 
  FOR (c:Company) REQUIRE c.companyId IS UNIQUE;
  
CREATE CONSTRAINT person_id 
  FOR (p:Person) REQUIRE p.personId IS UNIQUE;
  
CREATE CONSTRAINT event_id 
  FOR (e:Event) REQUIRE e.eventId IS UNIQUE;
```

### 5.2 성능 인덱스
```cypher
// 복합 인덱스
CREATE INDEX company_sector_risk 
  FOR (c:Company) ON (c.sector, c.riskScore);
  
CREATE INDEX event_date_severity 
  FOR (e:Event) ON (e.date, e.severity);

// 전문 검색 인덱스
CREATE FULLTEXT INDEX company_search 
  FOR (c:Company) ON EACH [c.name, c.aliases];
  
CREATE FULLTEXT INDEX news_content 
  FOR (n:News) ON EACH [n.title, n.content];
```

## 6. 데이터 수집 및 업데이트

### 6.1 실시간 업데이트
```cypher
// 뉴스 기반 이벤트 생성
MERGE (e:Event {eventId: $eventId})
SET e.title = $title,
    e.date = datetime(),
    e.severity = $severity,
    e.lastUpdated = timestamp()
    
// 관계 생성
MERGE (e)-[:MENTIONED_IN]->(n:News {newsId: $newsId})
MERGE (e)-[:AFFECTS {impactScore: $impact}]->(c:Company {companyId: $companyId})
```

### 6.2 배치 업데이트
```cypher
// 일일 리스크 점수 재계산
MATCH (c:Company)
OPTIONAL MATCH (c)<-[:AFFECTS]-(e:Event)
WHERE e.date > datetime() - duration('P7D')
WITH c, avg(e.severity) as recentRisk
SET c.riskScore = CASE 
  WHEN recentRisk IS NULL THEN c.riskScore * 0.95
  ELSE (c.riskScore * 0.7) + (recentRisk * 0.3)
END
```

## 7. 쿼리 최적화

### 7.1 쿼리 패턴
```cypher
// GOOD: 인덱스 활용
MATCH (c:Company {companyId: $id})
RETURN c

// BAD: 전체 스캔
MATCH (c:Company)
WHERE c.name CONTAINS $keyword
RETURN c
```

### 7.2 성능 모니터링
```cypher
// 쿼리 프로파일링
PROFILE
MATCH (c:Company)-[:PARTNERS_WITH*1..2]-(related)
WHERE c.riskScore > 7
RETURN c, collect(related) as partners
```

## 8. 확장성 전략

### 8.1 샤딩
- 산업별 서브그래프 분리
- 지역별 데이터 파티셔닝

### 8.2 읽기 확장
- Read Replica 구성
- 캐싱 레이어 (Redis)

### 8.3 쓰기 최적화
- 배치 임포트 활용
- 비동기 업데이트 큐