#!/usr/bin/env python3
"""001: Initial schema with TRD specifications"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.migrations.migration import Migration

class InitialSchema(Migration):
    """초기 스키마 생성 - TRD 스펙 준수"""
    
    def __init__(self):
        super().__init__(
            version="001",
            description="Initial schema with TRD specifications"
        )
    
    def up(self):
        """스키마 생성"""
        # 1. 기존 제약조건 제거 (업데이트를 위해)
        self._drop_existing_constraints()
        
        # 2. 노드 제약조건 생성
        self._create_node_constraints()
        
        # 3. 인덱스 생성
        self._create_indexes()
    
    def down(self):
        """스키마 롤백"""
        # 인덱스와 제약조건 제거
        self._drop_indexes()
        self._drop_constraints()
    
    def _drop_existing_constraints(self):
        """기존 제약조건 제거"""
        from src.neo4j.session import session
        
        constraints_to_drop = [
            "DROP CONSTRAINT company_id_unique IF EXISTS",
            "DROP CONSTRAINT person_id_unique IF EXISTS",
            "DROP CONSTRAINT event_id_unique IF EXISTS",
            "DROP CONSTRAINT news_id_unique IF EXISTS"
        ]
        
        for constraint in constraints_to_drop:
            try:
                session.run_query(constraint)
            except:
                pass  # 제약조건이 없으면 무시
    
    def _create_node_constraints(self):
        """노드 제약조건 생성"""
        from src.neo4j.session import session
        
        constraints = [
            # Company 제약조건
            "CREATE CONSTRAINT company_id_unique IF NOT EXISTS FOR (c:Company) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT company_name_exists IF NOT EXISTS FOR (c:Company) REQUIRE c.name IS NOT NULL",
            
            # Person 제약조건
            "CREATE CONSTRAINT person_id_unique IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT person_name_exists IF NOT EXISTS FOR (p:Person) REQUIRE p.name IS NOT NULL",
            
            # Event 제약조건
            "CREATE CONSTRAINT event_id_unique IF NOT EXISTS FOR (e:Event) REQUIRE e.id IS UNIQUE",
            "CREATE CONSTRAINT event_type_exists IF NOT EXISTS FOR (e:Event) REQUIRE e.type IS NOT NULL",
            
            # Risk 제약조건
            "CREATE CONSTRAINT risk_id_unique IF NOT EXISTS FOR (r:Risk) REQUIRE r.id IS UNIQUE",
            "CREATE CONSTRAINT risk_category_exists IF NOT EXISTS FOR (r:Risk) REQUIRE r.category IS NOT NULL",
            
            # NewsArticle 제약조건
            "CREATE CONSTRAINT news_id_unique IF NOT EXISTS FOR (n:NewsArticle) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT news_title_exists IF NOT EXISTS FOR (n:NewsArticle) REQUIRE n.title IS NOT NULL"
        ]
        
        for constraint in constraints:
            session.run_query(constraint)
    
    def _create_indexes(self):
        """인덱스 생성"""
        from src.neo4j.session import session
        
        indexes = [
            # Company 인덱스
            "CREATE INDEX company_name IF NOT EXISTS FOR (c:Company) ON (c.name)",
            "CREATE INDEX company_risk_score IF NOT EXISTS FOR (c:Company) ON (c.risk_score)",
            "CREATE INDEX company_stock_code IF NOT EXISTS FOR (c:Company) ON (c.stock_code)",
            "CREATE INDEX company_sector IF NOT EXISTS FOR (c:Company) ON (c.sector)",
            
            # Person 인덱스
            "CREATE INDEX person_name IF NOT EXISTS FOR (p:Person) ON (p.name)",
            "CREATE INDEX person_company IF NOT EXISTS FOR (p:Person) ON (p.company)",
            "CREATE INDEX person_influence IF NOT EXISTS FOR (p:Person) ON (p.influence_score)",
            
            # Event 인덱스
            "CREATE INDEX event_date IF NOT EXISTS FOR (e:Event) ON (e.date)",
            "CREATE INDEX event_type IF NOT EXISTS FOR (e:Event) ON (e.type)",
            "CREATE INDEX event_severity IF NOT EXISTS FOR (e:Event) ON (e.severity)",
            
            # Risk 인덱스
            "CREATE INDEX risk_category IF NOT EXISTS FOR (r:Risk) ON (r.category)",
            "CREATE INDEX risk_level IF NOT EXISTS FOR (r:Risk) ON (r.level)",
            "CREATE INDEX risk_trend IF NOT EXISTS FOR (r:Risk) ON (r.trend)",
            
            # NewsArticle 인덱스
            "CREATE INDEX news_published_at IF NOT EXISTS FOR (n:NewsArticle) ON (n.published_at)",
            "CREATE INDEX news_sentiment IF NOT EXISTS FOR (n:NewsArticle) ON (n.sentiment)",
            
            # 복합 인덱스
            "CREATE INDEX company_sector_country IF NOT EXISTS FOR (c:Company) ON (c.sector, c.country)",
            "CREATE INDEX event_type_impact IF NOT EXISTS FOR (e:Event) ON (e.type, e.impact)"
        ]
        
        for index in indexes:
            session.run_query(index)
    
    def _drop_indexes(self):
        """인덱스 제거"""
        from src.neo4j.session import session
        
        # 롤백 시 인덱스 제거
        indexes = [
            "DROP INDEX company_name IF EXISTS",
            "DROP INDEX company_risk_score IF EXISTS",
            "DROP INDEX company_stock_code IF EXISTS",
            "DROP INDEX company_sector IF EXISTS",
            "DROP INDEX person_name IF EXISTS",
            "DROP INDEX person_company IF EXISTS",
            "DROP INDEX person_influence IF EXISTS",
            "DROP INDEX event_date IF EXISTS",
            "DROP INDEX event_type IF EXISTS",
            "DROP INDEX event_severity IF EXISTS",
            "DROP INDEX risk_category IF EXISTS",
            "DROP INDEX risk_level IF EXISTS",
            "DROP INDEX risk_trend IF EXISTS",
            "DROP INDEX news_published_at IF EXISTS",
            "DROP INDEX news_sentiment IF EXISTS",
            "DROP INDEX company_sector_country IF EXISTS",
            "DROP INDEX event_type_impact IF EXISTS"
        ]
        
        for index in indexes:
            try:
                session.run_query(index)
            except:
                pass
    
    def _drop_constraints(self):
        """제약조건 제거"""
        from src.neo4j.session import session
        
        constraints = [
            "DROP CONSTRAINT company_id_unique IF EXISTS",
            "DROP CONSTRAINT company_name_exists IF EXISTS",
            "DROP CONSTRAINT person_id_unique IF EXISTS",
            "DROP CONSTRAINT person_name_exists IF EXISTS",
            "DROP CONSTRAINT event_id_unique IF EXISTS",
            "DROP CONSTRAINT event_type_exists IF EXISTS",
            "DROP CONSTRAINT risk_id_unique IF EXISTS",
            "DROP CONSTRAINT risk_category_exists IF EXISTS",
            "DROP CONSTRAINT news_id_unique IF EXISTS",
            "DROP CONSTRAINT news_title_exists IF EXISTS"
        ]
        
        for constraint in constraints:
            try:
                session.run_query(constraint)
            except:
                pass

# 마이그레이션 등록
if __name__ == "__main__":
    from src.migrations.migration import runner
    migration = InitialSchema()
    runner.register(migration)
    runner.run_all()