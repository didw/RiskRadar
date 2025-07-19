#!/usr/bin/env python3
"""Neo4j 스키마 초기화 스크립트"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from typing import List
from src.neo4j.session import session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 제약조건 정의
CONSTRAINTS = [
    # 유니크 제약조건
    "CREATE CONSTRAINT company_id_unique IF NOT EXISTS FOR (c:Company) REQUIRE c.id IS UNIQUE",
    "CREATE CONSTRAINT person_id_unique IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE",
    "CREATE CONSTRAINT event_id_unique IF NOT EXISTS FOR (e:Event) REQUIRE e.id IS UNIQUE",
    "CREATE CONSTRAINT news_id_unique IF NOT EXISTS FOR (n:NewsArticle) REQUIRE n.id IS UNIQUE",
    
    # 필수 속성 제약조건
    "CREATE CONSTRAINT company_name_exists IF NOT EXISTS FOR (c:Company) REQUIRE c.name IS NOT NULL",
    "CREATE CONSTRAINT person_name_exists IF NOT EXISTS FOR (p:Person) REQUIRE p.name IS NOT NULL",
    "CREATE CONSTRAINT event_type_exists IF NOT EXISTS FOR (e:Event) REQUIRE e.type IS NOT NULL",
    "CREATE CONSTRAINT news_title_exists IF NOT EXISTS FOR (n:NewsArticle) REQUIRE n.title IS NOT NULL",
]

# 인덱스 정의
INDEXES = [
    # 검색용 인덱스
    "CREATE INDEX company_name IF NOT EXISTS FOR (c:Company) ON (c.name)",
    "CREATE INDEX company_risk_score IF NOT EXISTS FOR (c:Company) ON (c.risk_score)",
    "CREATE INDEX person_name IF NOT EXISTS FOR (p:Person) ON (p.name)",
    "CREATE INDEX event_occurred_at IF NOT EXISTS FOR (e:Event) ON (e.occurred_at)",
    "CREATE INDEX risk_event_severity IF NOT EXISTS FOR (r:RiskEvent) ON (r.severity)",
    "CREATE INDEX news_published_at IF NOT EXISTS FOR (n:NewsArticle) ON (n.published_at)",
    
    # 복합 인덱스
    "CREATE INDEX company_industry_country IF NOT EXISTS FOR (c:Company) ON (c.industry, c.country)",
    "CREATE INDEX event_type_impact IF NOT EXISTS FOR (e:Event) ON (e.type, e.impact_score)",
]

def create_constraints():
    """제약조건 생성"""
    logger.info("Creating constraints...")
    session.create_constraints(CONSTRAINTS)
    logger.info(f"Created {len(CONSTRAINTS)} constraints")

def create_indexes():
    """인덱스 생성"""
    logger.info("Creating indexes...")
    session.create_indexes(INDEXES)
    logger.info(f"Created {len(INDEXES)} indexes")

def verify_schema():
    """스키마 검증"""
    logger.info("Verifying schema...")
    
    # 제약조건 확인
    constraints_query = "SHOW CONSTRAINTS"
    constraints = session.run_query(constraints_query)
    logger.info(f"Found {len(constraints)} constraints")
    
    # 인덱스 확인
    indexes_query = "SHOW INDEXES"
    indexes = session.run_query(indexes_query)
    logger.info(f"Found {len(indexes)} indexes")
    
    return len(constraints), len(indexes)

def create_sample_data():
    """샘플 데이터 생성 (개발용)"""
    logger.info("Creating sample data...")
    
    sample_queries = [
        # 샘플 기업
        ("""
        CREATE (c1:Company {
            id: 'company-1',
            name: 'Acme Corporation',
            industry: 'Technology',
            risk_score: 7.5,
            country: 'USA'
        })
        """, {}),
        
        ("""
        CREATE (c2:Company {
            id: 'company-2',
            name: 'Global Industries',
            industry: 'Manufacturing',
            risk_score: 6.0,
            country: 'UK'
        })
        """, {}),
        
        # 샘플 인물
        ("""
        CREATE (p1:Person {
            id: 'person-1',
            name: 'John Doe',
            title: 'CEO',
            organization: 'Acme Corporation'
        })
        """, {}),
        
        # 샘플 이벤트
        ("""
        CREATE (e1:RiskEvent:Event {
            id: 'event-1',
            type: 'Financial',
            title: 'Revenue Warning',
            risk_type: 'FINANCIAL',
            severity: 8,
            occurred_at: datetime()
        })
        """, {}),
        
        # 샘플 관계
        ("""
        MATCH (c1:Company {id: 'company-1'}), (c2:Company {id: 'company-2'})
        CREATE (c1)-[:COMPETES_WITH {strength: 0.8}]->(c2)
        """, {}),
        
        ("""
        MATCH (p:Person {id: 'person-1'}), (c:Company {id: 'company-1'})
        CREATE (p)-[:CEO_OF {since: datetime()}]->(c)
        """, {}),
        
        ("""
        MATCH (e:Event {id: 'event-1'}), (c:Company {id: 'company-1'})
        CREATE (e)-[:AFFECTS {impact_severity: 8}]->(c)
        """, {}),
    ]
    
    for query, params in sample_queries:
        try:
            session.run_query(query, **params)
        except Exception as e:
            logger.warning(f"Sample data might already exist: {e}")
    
    logger.info("Sample data created")

def main():
    """메인 함수"""
    logger.info("Initializing Neo4j schema...")
    
    try:
        # 1. 제약조건 생성
        create_constraints()
        
        # 2. 인덱스 생성
        create_indexes()
        
        # 3. 스키마 검증
        constraint_count, index_count = verify_schema()
        
        # 4. 샘플 데이터 생성 (옵션)
        if "--sample-data" in sys.argv:
            create_sample_data()
        
        logger.info(f"""
Schema initialization completed successfully!
- Constraints: {constraint_count}
- Indexes: {index_count}

To verify in Neo4j Browser:
- SHOW CONSTRAINTS
- SHOW INDEXES
- MATCH (n) RETURN n LIMIT 25
        """)
        
    except Exception as e:
        logger.error(f"Schema initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()