"""
쿼리 성능 튜닝 모듈
Week 4 요구사항: 인덱스 최적화, 쿼리 플랜 분석, 성능 모니터링
"""
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from ..neo4j.driver import driver

logger = logging.getLogger(__name__)


class IndexType(Enum):
    """인덱스 타입"""
    BTREE = "BTREE"
    TEXT = "TEXT"
    POINT = "POINT"
    LOOKUP = "LOOKUP"
    FULLTEXT = "FULLTEXT"


@dataclass
class IndexInfo:
    """인덱스 정보"""
    name: str
    labels: List[str]
    properties: List[str]
    type: str
    state: str
    population_percent: float
    provider: str


@dataclass
class QueryPlan:
    """쿼리 실행 계획"""
    query: str
    plan: Dict[str, Any]
    execution_time_ms: float
    db_hits: int
    estimated_rows: int
    actual_rows: int
    index_usage: List[str]


class PerformanceTuner:
    """성능 튜닝 관리자"""
    
    def __init__(self):
        self.query_plans: List[QueryPlan] = []
        self.slow_queries: List[Dict[str, Any]] = []
        self.slow_query_threshold_ms = 100  # 100ms 이상 느린 쿼리
    
    # 1. 인덱스 관리
    def create_performance_indexes(self) -> Dict[str, bool]:
        """성능 최적화를 위한 인덱스 생성"""
        indexes_to_create = [
            # Company 노드 인덱스 (가장 중요)
            {
                "name": "company_id_index",
                "query": "CREATE INDEX company_id_index IF NOT EXISTS FOR (c:Company) ON (c.id)"
            },
            {
                "name": "company_name_index", 
                "query": "CREATE INDEX company_name_index IF NOT EXISTS FOR (c:Company) ON (c.name)"
            },
            {
                "name": "company_risk_score_index",
                "query": "CREATE INDEX company_risk_score_index IF NOT EXISTS FOR (c:Company) ON (c.risk_score)"
            },
            {
                "name": "company_sector_index",
                "query": "CREATE INDEX company_sector_index IF NOT EXISTS FOR (c:Company) ON (c.sector)"
            },
            {
                "name": "company_created_at_index",
                "query": "CREATE INDEX company_created_at_index IF NOT EXISTS FOR (c:Company) ON (c.created_at)"
            },
            
            # Person 노드 인덱스
            {
                "name": "person_id_index",
                "query": "CREATE INDEX person_id_index IF NOT EXISTS FOR (p:Person) ON (p.id)"
            },
            {
                "name": "person_name_index",
                "query": "CREATE INDEX person_name_index IF NOT EXISTS FOR (p:Person) ON (p.name)"
            },
            
            # RiskEvent 노드 인덱스
            {
                "name": "risk_event_id_index",
                "query": "CREATE INDEX risk_event_id_index IF NOT EXISTS FOR (r:RiskEvent) ON (r.id)"
            },
            {
                "name": "risk_event_severity_index",
                "query": "CREATE INDEX risk_event_severity_index IF NOT EXISTS FOR (r:RiskEvent) ON (r.severity)"
            },
            {
                "name": "risk_event_created_at_index",
                "query": "CREATE INDEX risk_event_created_at_index IF NOT EXISTS FOR (r:RiskEvent) ON (r.created_at)"
            },
            
            # NewsArticle 노드 인덱스
            {
                "name": "news_id_index",
                "query": "CREATE INDEX news_id_index IF NOT EXISTS FOR (n:NewsArticle) ON (n.id)"
            },
            {
                "name": "news_created_at_index",
                "query": "CREATE INDEX news_created_at_index IF NOT EXISTS FOR (n:NewsArticle) ON (n.created_at)"
            },
            
            # 관계 인덱스 (중요한 관계들)
            {
                "name": "connected_to_strength_index",
                "query": "CREATE INDEX connected_to_strength_index IF NOT EXISTS FOR ()-[r:CONNECTED_TO]-() ON (r.strength)"
            },
            {
                "name": "affects_created_at_index",
                "query": "CREATE INDEX affects_created_at_index IF NOT EXISTS FOR ()-[r:AFFECTS]-() ON (r.created_at)"
            },
            
            # 복합 인덱스 (자주 사용되는 조합)
            {
                "name": "company_sector_risk_index",
                "query": "CREATE INDEX company_sector_risk_index IF NOT EXISTS FOR (c:Company) ON (c.sector, c.risk_score)"
            },
            {
                "name": "company_name_sector_index",
                "query": "CREATE INDEX company_name_sector_index IF NOT EXISTS FOR (c:Company) ON (c.name, c.sector)"
            }
        ]
        
        # 전문 검색 인덱스
        fulltext_indexes = [
            {
                "name": "company_fulltext_index",
                "query": """
                CREATE FULLTEXT INDEX company_fulltext_index IF NOT EXISTS
                FOR (c:Company) ON EACH [c.name, c.name_en, c.aliases]
                """
            },
            {
                "name": "news_fulltext_index", 
                "query": """
                CREATE FULLTEXT INDEX news_fulltext_index IF NOT EXISTS
                FOR (n:NewsArticle) ON EACH [n.title, n.content]
                """
            }
        ]
        
        results = {}
        
        # 기본 인덱스 생성
        for index_def in indexes_to_create:
            try:
                driver.execute_write(index_def["query"])
                results[index_def["name"]] = True
                logger.info(f"Created index: {index_def['name']}")
            except Exception as e:
                results[index_def["name"]] = False
                logger.error(f"Failed to create index {index_def['name']}: {e}")
        
        # 전문 검색 인덱스 생성
        for index_def in fulltext_indexes:
            try:
                driver.execute_write(index_def["query"])
                results[index_def["name"]] = True
                logger.info(f"Created fulltext index: {index_def['name']}")
            except Exception as e:
                results[index_def["name"]] = False
                logger.error(f"Failed to create fulltext index {index_def['name']}: {e}")
        
        return results
    
    def get_index_status(self) -> List[IndexInfo]:
        """인덱스 상태 조회"""
        query = "SHOW INDEXES"
        
        try:
            results = driver.execute_read(query)
            indexes = []
            
            for row in results:
                index_info = IndexInfo(
                    name=row.get("name", ""),
                    labels=row.get("labelsOrTypes", []),
                    properties=row.get("properties", []),
                    type=row.get("type", ""),
                    state=row.get("state", ""),
                    population_percent=row.get("populationPercent", 0.0),
                    provider=row.get("provider", {}).get("key", "")
                )
                indexes.append(index_info)
            
            return indexes
            
        except Exception as e:
            logger.error(f"Error getting index status: {e}")
            return []
    
    def analyze_index_usage(self) -> Dict[str, Any]:
        """인덱스 사용률 분석"""
        # 인덱스 상태 확인
        indexes = self.get_index_status()
        
        # 인덱스별 통계
        index_stats = {}
        for index in indexes:
            if index.state == "ONLINE":
                index_stats[index.name] = {
                    "labels": index.labels,
                    "properties": index.properties,
                    "type": index.type,
                    "population_percent": index.population_percent,
                    "provider": index.provider
                }
        
        # 느린 쿼리에서 인덱스 미사용 분석
        missing_indexes = self._analyze_missing_indexes()
        
        return {
            "total_indexes": len(indexes),
            "online_indexes": len([i for i in indexes if i.state == "ONLINE"]),
            "failed_indexes": len([i for i in indexes if i.state == "FAILED"]),
            "index_details": index_stats,
            "missing_indexes": missing_indexes,
            "recommendations": self._get_index_recommendations()
        }
    
    def _analyze_missing_indexes(self) -> List[str]:
        """누락된 인덱스 분석"""
        recommendations = []
        
        # 자주 사용되는 패턴 중 인덱스가 없는 것들 찾기
        common_patterns = [
            ("Company", "market_cap"),
            ("Company", "updated_at"),
            ("Person", "role"),
            ("RiskEvent", "event_type"),
            ("NewsArticle", "source"),
            ("NewsArticle", "sentiment")
        ]
        
        existing_indexes = self.get_index_status()
        existing_patterns = set()
        
        for index in existing_indexes:
            if index.labels and index.properties:
                for label in index.labels:
                    for prop in index.properties:
                        existing_patterns.add((label, prop))
        
        for label, prop in common_patterns:
            if (label, prop) not in existing_patterns:
                recommendations.append(f"CREATE INDEX FOR (n:{label}) ON (n.{prop})")
        
        return recommendations
    
    def _get_index_recommendations(self) -> List[str]:
        """인덱스 최적화 권장사항"""
        recommendations = []
        
        # 느린 쿼리 분석 기반 권장사항
        if len(self.slow_queries) > 0:
            recommendations.append("Consider creating composite indexes for frequent multi-property queries")
        
        # 인덱스 상태 기반 권장사항
        indexes = self.get_index_status()
        for index in indexes:
            if index.population_percent < 100:
                recommendations.append(f"Index {index.name} is not fully populated ({index.population_percent:.1f}%)")
        
        return recommendations
    
    # 2. 쿼리 플랜 분석
    def analyze_query_plan(self, query: str, parameters: Dict[str, Any] = None) -> QueryPlan:
        """쿼리 실행 계획 분석"""
        if parameters is None:
            parameters = {}
        
        # PROFILE을 사용하여 실제 실행 통계 수집
        profile_query = f"PROFILE {query}"
        
        start_time = time.time()
        
        try:
            # 쿼리 실행 및 프로파일링
            results = driver.execute_read(profile_query, **parameters)
            execution_time = (time.time() - start_time) * 1000  # ms 변환
            
            # 실행 계획 정보 추출 (Neo4j 5.x 방식)
            plan_info = {
                "operatorType": "ProfiledQuery",
                "dbHits": 0,
                "rows": len(results),
                "time": execution_time
            }
            
            query_plan = QueryPlan(
                query=query,
                plan=plan_info,
                execution_time_ms=execution_time,
                db_hits=plan_info.get("dbHits", 0),
                estimated_rows=0,
                actual_rows=plan_info.get("rows", 0),
                index_usage=[]  # 실제 환경에서는 plan에서 추출
            )
            
            # 느린 쿼리 기록
            if execution_time > self.slow_query_threshold_ms:
                self.slow_queries.append({
                    "query": query,
                    "execution_time_ms": execution_time,
                    "timestamp": datetime.now(),
                    "parameters": parameters
                })
                
                # 느린 쿼리 로그 크기 제한
                if len(self.slow_queries) > 100:
                    self.slow_queries = self.slow_queries[-100:]
            
            self.query_plans.append(query_plan)
            
            # 쿼리 플랜 로그 크기 제한
            if len(self.query_plans) > 50:
                self.query_plans = self.query_plans[-50:]
            
            return query_plan
            
        except Exception as e:
            logger.error(f"Error analyzing query plan: {e}")
            return QueryPlan(
                query=query,
                plan={"error": str(e)},
                execution_time_ms=0,
                db_hits=0,
                estimated_rows=0,
                actual_rows=0,
                index_usage=[]
            )
    
    def get_slow_queries(self, limit: int = 20) -> List[Dict[str, Any]]:
        """느린 쿼리 목록 반환"""
        return sorted(
            self.slow_queries[-limit:],
            key=lambda q: q["execution_time_ms"],
            reverse=True
        )
    
    def get_query_performance_summary(self) -> Dict[str, Any]:
        """쿼리 성능 요약"""
        if not self.query_plans:
            return {"message": "No query plans available"}
        
        execution_times = [plan.execution_time_ms for plan in self.query_plans]
        db_hits = [plan.db_hits for plan in self.query_plans]
        
        return {
            "total_queries_analyzed": len(self.query_plans),
            "slow_queries_count": len(self.slow_queries),
            "performance_metrics": {
                "avg_execution_time_ms": sum(execution_times) / len(execution_times),
                "p95_execution_time_ms": sorted(execution_times)[int(len(execution_times) * 0.95)] if execution_times else 0,
                "max_execution_time_ms": max(execution_times) if execution_times else 0,
                "avg_db_hits": sum(db_hits) / len(db_hits) if db_hits else 0
            },
            "performance_goals": {
                "queries_under_50ms": sum(1 for t in execution_times if t < 50),
                "queries_under_200ms": sum(1 for t in execution_times if t < 200),
                "goal_achievement_rate": sum(1 for t in execution_times if t < 50) / len(execution_times) if execution_times else 0
            }
        }
    
    # 3. 자동 최적화
    def optimize_query(self, query: str) -> str:
        """쿼리 자동 최적화 제안"""
        optimized = query
        suggestions = []
        
        # 1. LIMIT 추가 권장
        if "LIMIT" not in query.upper() and "MATCH" in query.upper():
            suggestions.append("Consider adding LIMIT clause to prevent large result sets")
        
        # 2. 인덱스 힌트 추가
        if "MATCH (c:Company)" in query and "c.id" in query:
            if "USING INDEX" not in query.upper():
                suggestions.append("Consider using index hint: USING INDEX c:Company(id)")
        
        # 3. WHERE 절 최적화
        if "WHERE" in query.upper():
            # 조기 필터링 권장
            if query.count("WHERE") > 1:
                suggestions.append("Consider moving WHERE clauses closer to MATCH for early filtering")
        
        # 4. 불필요한 연산 제거
        if "count(*)" in query.lower() and "RETURN" in query:
            suggestions.append("Consider using exists() instead of count(*) for existence checks")
        
        return {
            "original_query": query,
            "optimized_query": optimized,
            "suggestions": suggestions
        }
    
    def run_performance_diagnostics(self) -> Dict[str, Any]:
        """성능 진단 실행"""
        diagnostics = {}
        
        # 1. 데이터베이스 통계
        try:
            stats_query = """
            CALL db.stats.retrieve("GRAPH COUNTS") YIELD section, data
            RETURN section, data
            """
            stats_results = driver.execute_read(stats_query)
            diagnostics["db_stats"] = {row["section"]: row["data"] for row in stats_results}
        except Exception as e:
            diagnostics["db_stats"] = {"error": str(e)}
        
        # 2. 인덱스 분석
        diagnostics["index_analysis"] = self.analyze_index_usage()
        
        # 3. 쿼리 성능 분석
        diagnostics["query_performance"] = self.get_query_performance_summary()
        
        # 4. 메모리 사용량 (Neo4j 스토어 정보)
        try:
            store_query = "CALL db.info() YIELD *"
            store_results = driver.execute_read(store_query)
            diagnostics["store_info"] = store_results[0] if store_results else {}
        except Exception as e:
            diagnostics["store_info"] = {"error": str(e)}
        
        # 5. 성능 권장사항
        diagnostics["recommendations"] = self._generate_performance_recommendations()
        
        return diagnostics
    
    def _generate_performance_recommendations(self) -> List[str]:
        """성능 최적화 권장사항 생성"""
        recommendations = []
        
        # 느린 쿼리 기반 권장사항
        slow_queries_count = len(self.slow_queries)
        if slow_queries_count > 10:
            recommendations.append(f"High number of slow queries detected ({slow_queries_count}). Consider query optimization.")
        
        # 인덱스 기반 권장사항
        indexes = self.get_index_status()
        online_indexes = [i for i in indexes if i.state == "ONLINE"]
        if len(online_indexes) < 10:
            recommendations.append("Consider creating more indexes for frequently queried properties.")
        
        # 쿼리 패턴 기반 권장사항
        if self.query_plans:
            avg_execution_time = sum(p.execution_time_ms for p in self.query_plans) / len(self.query_plans)
            if avg_execution_time > 100:
                recommendations.append("Average query execution time is high. Consider query optimization and index tuning.")
        
        return recommendations
    
    # 4. 캐시 워밍업
    def warm_up_database(self, sample_queries: List[Tuple[str, Dict[str, Any]]] = None):
        """데이터베이스 캐시 워밍업"""
        if sample_queries is None:
            # 기본 워밍업 쿼리들
            sample_queries = [
                ("MATCH (c:Company) RETURN count(c)", {}),
                ("MATCH (p:Person) RETURN count(p)", {}),
                ("MATCH (r:RiskEvent) RETURN count(r)", {}),
                ("MATCH ()-[rel]->() RETURN type(rel), count(rel)", {}),
                ("MATCH (c:Company) WHERE c.risk_score >= 7.0 RETURN c.id, c.name LIMIT 10", {})
            ]
        
        logger.info("Starting database warmup...")
        
        for query, params in sample_queries:
            try:
                start_time = time.time()
                driver.execute_read(query, **params)
                execution_time = (time.time() - start_time) * 1000
                logger.debug(f"Warmup query executed in {execution_time:.2f}ms: {query[:50]}...")
            except Exception as e:
                logger.warning(f"Warmup query failed: {e}")
        
        logger.info("Database warmup completed")


# 글로벌 인스턴스
_performance_tuner = PerformanceTuner()


def get_performance_tuner() -> PerformanceTuner:
    """성능 튜너 인스턴스 반환"""
    return _performance_tuner