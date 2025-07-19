"""
자주 사용되는 쿼리 최적화 모듈
Week 4 요구사항: 쿼리 성능 튜닝 및 최적화
"""
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum

from ..neo4j.driver import driver

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """쿼리 타입 분류"""
    SINGLE_HOP = "single_hop"  # 1-hop 쿼리 (< 50ms 목표)
    MULTI_HOP = "multi_hop"    # 3-hop 경로 (< 200ms 목표)
    AGGREGATION = "aggregation" # 집계 쿼리
    TRAVERSAL = "traversal"     # 그래프 순회


@dataclass
class QueryPerformance:
    """쿼리 성능 메트릭"""
    query_id: str
    execution_time_ms: float
    result_count: int
    cache_hit: bool
    timestamp: datetime


class OptimizedQueries:
    """최적화된 핵심 쿼리 모음"""
    
    def __init__(self):
        self.performance_log: List[QueryPerformance] = []
        self.query_cache: Dict[str, Tuple[Any, datetime]] = {}
        self.cache_ttl_seconds = 300  # 5분 캐시
    
    def _log_performance(self, query_id: str, execution_time: float, 
                        result_count: int, cache_hit: bool = False):
        """쿼리 성능 로깅"""
        perf = QueryPerformance(
            query_id=query_id,
            execution_time_ms=execution_time * 1000,  # 밀리초 변환
            result_count=result_count,
            cache_hit=cache_hit,
            timestamp=datetime.now()
        )
        self.performance_log.append(perf)
        
        # 성능 로그 크기 제한 (최근 1000개)
        if len(self.performance_log) > 1000:
            self.performance_log = self.performance_log[-1000:]
        
        # 성능 경고 (목표 시간 초과 시)
        if not cache_hit:
            if query_id.startswith("single_hop") and execution_time * 1000 > 50:
                logger.warning(f"1-hop query exceeded 50ms: {execution_time * 1000:.2f}ms")
            elif query_id.startswith("multi_hop") and execution_time * 1000 > 200:
                logger.warning(f"3-hop query exceeded 200ms: {execution_time * 1000:.2f}ms")
    
    def _get_cached_result(self, cache_key: str) -> Optional[Any]:
        """캐시에서 결과 조회"""
        if cache_key in self.query_cache:
            result, timestamp = self.query_cache[cache_key]
            if datetime.now() - timestamp < timedelta(seconds=self.cache_ttl_seconds):
                return result
            else:
                # 만료된 캐시 제거
                del self.query_cache[cache_key]
        return None
    
    def _cache_result(self, cache_key: str, result: Any):
        """결과 캐싱"""
        self.query_cache[cache_key] = (result, datetime.now())
        
        # 캐시 크기 제한 (최대 100개)
        if len(self.query_cache) > 100:
            # 가장 오래된 항목 제거
            oldest_key = min(self.query_cache.keys(), 
                           key=lambda k: self.query_cache[k][1])
            del self.query_cache[oldest_key]
    
    # 1. 기업 기본 정보 조회 (1-hop, 최적화됨)
    def get_company_basic_info(self, company_id: str) -> Optional[Dict[str, Any]]:
        """
        기업 기본 정보 조회 - 가장 자주 사용되는 쿼리
        목표: < 50ms
        """
        import time
        start_time = time.time()
        query_id = "single_hop_company_basic"
        cache_key = f"company_basic_{company_id}"
        
        # 캐시 확인
        cached_result = self._get_cached_result(cache_key)
        if cached_result is not None:
            self._log_performance(query_id, 0.001, 1, cache_hit=True)
            return cached_result
        
        query = """
        MATCH (c:Company {id: $company_id})
        RETURN {
            id: c.id,
            name: c.name,
            name_en: c.name_en,
            sector: c.sector,
            risk_score: c.risk_score,
            market_cap: c.market_cap,
            created_at: c.created_at,
            updated_at: c.updated_at
        } as company
        """
        
        try:
            results = driver.execute_read(query, company_id=company_id)
            result = results[0]["company"] if results else None
            
            # 캐싱
            if result:
                self._cache_result(cache_key, result)
            
            execution_time = time.time() - start_time
            self._log_performance(query_id, execution_time, len(results))
            
            return result
            
        except Exception as e:
            logger.error(f"Error in get_company_basic_info: {e}")
            execution_time = time.time() - start_time
            self._log_performance(query_id, execution_time, 0)
            return None
    
    # 2. 기업 연결 관계 조회 (1-hop, 최적화됨)
    def get_company_connections(self, company_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        기업의 직접 연결 관계 조회
        목표: < 50ms
        """
        import time
        start_time = time.time()
        query_id = "single_hop_connections"
        cache_key = f"connections_{company_id}_{limit}"
        
        # 캐시 확인
        cached_result = self._get_cached_result(cache_key)
        if cached_result is not None:
            self._log_performance(query_id, 0.001, len(cached_result), cache_hit=True)
            return cached_result
        
        query = """
        MATCH (c:Company {id: $company_id})-[r]-(connected)
        WHERE connected:Company OR connected:Person
        RETURN {
            entity: {
                id: connected.id,
                name: connected.name,
                type: labels(connected)[0]
            },
            relationship: {
                type: type(r),
                strength: coalesce(r.strength, 1.0),
                created_at: r.created_at
            }
        } as connection
        ORDER BY coalesce(r.strength, 1.0) DESC
        LIMIT $limit
        """
        
        try:
            results = driver.execute_read(query, company_id=company_id, limit=limit)
            connections = [row["connection"] for row in results]
            
            # 캐싱
            self._cache_result(cache_key, connections)
            
            execution_time = time.time() - start_time
            self._log_performance(query_id, execution_time, len(connections))
            
            return connections
            
        except Exception as e:
            logger.error(f"Error in get_company_connections: {e}")
            execution_time = time.time() - start_time
            self._log_performance(query_id, execution_time, 0)
            return []
    
    # 3. 리스크 전파 경로 분석 (3-hop, 최적화됨)
    def analyze_risk_propagation_paths(self, company_id: str, max_depth: int = 3) -> List[Dict[str, Any]]:
        """
        리스크 전파 경로 분석 - 3-hop 쿼리
        목표: < 200ms
        """
        import time
        start_time = time.time()
        query_id = "multi_hop_risk_paths"
        cache_key = f"risk_paths_{company_id}_{max_depth}"
        
        # 캐시 확인
        cached_result = self._get_cached_result(cache_key)
        if cached_result is not None:
            self._log_performance(query_id, 0.001, len(cached_result), cache_hit=True)
            return cached_result
        
        # 최적화된 쿼리: 인덱스 활용, 조기 필터링
        query = """
        MATCH (source:Company {id: $company_id})
        WHERE source.risk_score >= 5.0
        
        CALL apoc.path.expandConfig(source, {
            relationshipFilter: 'CONNECTED_TO|PARTNERS_WITH|SUBSIDIARY_OF',
            labelFilter: '+Company',
            maxLevel: $max_depth,
            uniqueness: 'NODE_GLOBAL',
            limit: 50
        }) YIELD path
        
        WITH path, 
             [node in nodes(path) | node.risk_score] as risk_scores,
             [rel in relationships(path) | coalesce(rel.strength, 1.0)] as strengths
        
        WHERE size(risk_scores) > 1 AND 
              all(score in risk_scores WHERE score >= 5.0)
        
        WITH path, risk_scores, strengths,
             reduce(propagation = 1.0, i in range(0, size(strengths)-1) | 
                propagation * strengths[i] * 0.8) as propagation_factor
        
        WHERE propagation_factor > 0.1
        
        RETURN {
            path: [node in nodes(path) | {
                id: node.id,
                name: node.name,
                risk_score: node.risk_score
            }],
            risk_scores: risk_scores,
            propagation_factor: propagation_factor,
            path_length: length(path)
        } as risk_path
        ORDER BY propagation_factor DESC
        LIMIT 20
        """
        
        try:
            results = driver.execute_read(
                query, 
                company_id=company_id, 
                max_depth=max_depth
            )
            paths = [row["risk_path"] for row in results]
            
            # 캐싱
            self._cache_result(cache_key, paths)
            
            execution_time = time.time() - start_time
            self._log_performance(query_id, execution_time, len(paths))
            
            return paths
            
        except Exception as e:
            logger.error(f"Error in analyze_risk_propagation_paths: {e}")
            execution_time = time.time() - start_time
            self._log_performance(query_id, execution_time, 0)
            return []
    
    # 4. 네트워크 리스크 집계 (최적화됨)
    def calculate_network_risk_summary(self, company_id: str) -> Dict[str, Any]:
        """
        네트워크 리스크 요약 통계
        목표: < 100ms
        """
        import time
        start_time = time.time()
        query_id = "aggregation_network_risk"
        cache_key = f"network_risk_{company_id}"
        
        # 캐시 확인
        cached_result = self._get_cached_result(cache_key)
        if cached_result is not None:
            self._log_performance(query_id, 0.001, 1, cache_hit=True)
            return cached_result
        
        query = """
        MATCH (c:Company {id: $company_id})
        
        // 직접 연결된 기업들
        OPTIONAL MATCH (c)-[:CONNECTED_TO|PARTNERS_WITH]-(direct:Company)
        WITH c, collect(direct) as direct_companies
        
        // 2-hop 연결된 기업들 (제한)
        OPTIONAL MATCH (c)-[:CONNECTED_TO|PARTNERS_WITH]-()-[:CONNECTED_TO|PARTNERS_WITH]-(indirect:Company)
        WHERE indirect <> c AND NOT indirect IN direct_companies
        WITH c, direct_companies, collect(DISTINCT indirect)[..50] as indirect_companies
        
        // 통계 계산
        WITH c, direct_companies, indirect_companies,
             direct_companies + indirect_companies as all_connected
        
        RETURN {
            company_id: c.id,
            company_name: c.name,
            own_risk_score: c.risk_score,
            direct_connections: size(direct_companies),
            indirect_connections: size(indirect_companies),
            total_network_size: size(all_connected),
            direct_avg_risk: 
                CASE 
                    WHEN size(direct_companies) > 0 
                    THEN reduce(sum = 0.0, comp in direct_companies | sum + comp.risk_score) / size(direct_companies)
                    ELSE 0.0 
                END,
            network_avg_risk: 
                CASE 
                    WHEN size(all_connected) > 0 
                    THEN reduce(sum = 0.0, comp in all_connected | sum + comp.risk_score) / size(all_connected)
                    ELSE 0.0 
                END,
            high_risk_neighbors: size([comp in direct_companies WHERE comp.risk_score >= 7.0]),
            systemic_risk_score: 
                CASE 
                    WHEN size(all_connected) > 0 
                    THEN c.risk_score * 0.6 + 
                         (reduce(sum = 0.0, comp in all_connected | sum + comp.risk_score) / size(all_connected)) * 0.4
                    ELSE c.risk_score 
                END
        } as summary
        """
        
        try:
            results = driver.execute_read(query, company_id=company_id)
            summary = results[0]["summary"] if results else {}
            
            # 캐싱
            if summary:
                self._cache_result(cache_key, summary)
            
            execution_time = time.time() - start_time
            self._log_performance(query_id, execution_time, 1 if summary else 0)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error in calculate_network_risk_summary: {e}")
            execution_time = time.time() - start_time
            self._log_performance(query_id, execution_time, 0)
            return {}
    
    # 5. 섹터별 리스크 분포 (최적화됨)
    def get_sector_risk_distribution(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        섹터별 리스크 분포 분석
        목표: < 150ms
        """
        import time
        start_time = time.time()
        query_id = "aggregation_sector_risk"
        cache_key = f"sector_risk_{limit}"
        
        # 캐시 확인 (더 긴 캐시 시간 - 10분)
        cached_result = self._get_cached_result(cache_key)
        if cached_result is not None:
            self._log_performance(query_id, 0.001, len(cached_result), cache_hit=True)
            return cached_result
        
        query = """
        MATCH (c:Company)
        WHERE c.sector IS NOT NULL AND c.risk_score IS NOT NULL
        
        WITH c.sector as sector, 
             collect(c.risk_score) as risk_scores,
             count(c) as company_count
        WHERE company_count >= 3  // 최소 3개 기업이 있는 섹터만
        
        RETURN {
            sector: sector,
            company_count: company_count,
            avg_risk_score: reduce(sum = 0.0, score in risk_scores | sum + score) / size(risk_scores),
            min_risk_score: reduce(min = 10.0, score in risk_scores | CASE WHEN score < min THEN score ELSE min END),
            max_risk_score: reduce(max = 0.0, score in risk_scores | CASE WHEN score > max THEN score ELSE max END),
            high_risk_count: size([score in risk_scores WHERE score >= 7.0]),
            low_risk_count: size([score in risk_scores WHERE score <= 3.0]),
            risk_volatility: 
                sqrt(reduce(sum = 0.0, score in risk_scores | 
                    sum + (score - reduce(avg = 0.0, s in risk_scores | avg + s) / size(risk_scores))^2
                ) / size(risk_scores))
        } as sector_stats
        ORDER BY sector_stats.avg_risk_score DESC
        LIMIT $limit
        """
        
        try:
            results = driver.execute_read(query, limit=limit)
            distribution = [row["sector_stats"] for row in results]
            
            # 캐싱 (10분)
            if distribution:
                self.query_cache[cache_key] = (distribution, datetime.now())
            
            execution_time = time.time() - start_time
            self._log_performance(query_id, execution_time, len(distribution))
            
            return distribution
            
        except Exception as e:
            logger.error(f"Error in get_sector_risk_distribution: {e}")
            execution_time = time.time() - start_time
            self._log_performance(query_id, execution_time, 0)
            return []
    
    # 6. 최근 리스크 이벤트 조회 (시계열 최적화)
    def get_recent_risk_events(self, company_id: Optional[str] = None, 
                             days: int = 30, limit: int = 50) -> List[Dict[str, Any]]:
        """
        최근 리스크 이벤트 조회 - 시계열 최적화
        목표: < 100ms
        """
        import time
        start_time = time.time()
        query_id = "traversal_recent_events"
        cache_key = f"recent_events_{company_id}_{days}_{limit}"
        
        # 캐시 확인
        cached_result = self._get_cached_result(cache_key)
        if cached_result is not None:
            self._log_performance(query_id, 0.001, len(cached_result), cache_hit=True)
            return cached_result
        
        # 날짜 필터링을 위한 timestamp 계산
        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_timestamp = int(cutoff_date.timestamp())
        
        if company_id:
            query = """
            MATCH (c:Company {id: $company_id})-[:AFFECTS|MENTIONED_IN]-(event)
            WHERE (event:RiskEvent OR event:NewsArticle) 
              AND event.created_at >= $cutoff_timestamp
            
            OPTIONAL MATCH (event)-[:AFFECTS]-(affected:Company)
            WHERE affected <> c
            
            RETURN {
                id: event.id,
                type: labels(event)[0],
                title: coalesce(event.title, event.description),
                severity: coalesce(event.severity, 5),
                created_at: event.created_at,
                source_company: c.name,
                affected_companies: collect(DISTINCT affected.name)[..5]
            } as event
            ORDER BY event.created_at DESC
            LIMIT $limit
            """
            params = {
                "company_id": company_id,
                "cutoff_timestamp": cutoff_timestamp,
                "limit": limit
            }
        else:
            query = """
            MATCH (event)
            WHERE (event:RiskEvent OR event:NewsArticle) 
              AND event.created_at >= $cutoff_timestamp
              AND event.severity >= 6
            
            OPTIONAL MATCH (event)-[:AFFECTS]-(company:Company)
            
            RETURN {
                id: event.id,
                type: labels(event)[0],
                title: coalesce(event.title, event.description),
                severity: coalesce(event.severity, 5),
                created_at: event.created_at,
                affected_companies: collect(DISTINCT company.name)[..5]
            } as event
            ORDER BY event.created_at DESC
            LIMIT $limit
            """
            params = {
                "cutoff_timestamp": cutoff_timestamp,
                "limit": limit
            }
        
        try:
            results = driver.execute_read(query, **params)
            events = [row["event"] for row in results]
            
            # 캐싱 (5분)
            if events:
                self._cache_result(cache_key, events)
            
            execution_time = time.time() - start_time
            self._log_performance(query_id, execution_time, len(events))
            
            return events
            
        except Exception as e:
            logger.error(f"Error in get_recent_risk_events: {e}")
            execution_time = time.time() - start_time
            self._log_performance(query_id, execution_time, 0)
            return []
    
    # 성능 모니터링 메소드들
    def get_performance_stats(self) -> Dict[str, Any]:
        """쿼리 성능 통계 반환"""
        if not self.performance_log:
            return {}
        
        # 최근 100개 쿼리 기준 통계
        recent_logs = self.performance_log[-100:]
        
        execution_times = [log.execution_time_ms for log in recent_logs if not log.cache_hit]
        cache_hits = sum(1 for log in recent_logs if log.cache_hit)
        total_queries = len(recent_logs)
        
        # 쿼리 타입별 통계
        type_stats = {}
        for log in recent_logs:
            query_type = log.query_id.split('_')[0]  # single, multi, aggregation, traversal
            if query_type not in type_stats:
                type_stats[query_type] = []
            if not log.cache_hit:
                type_stats[query_type].append(log.execution_time_ms)
        
        stats = {
            "total_queries": total_queries,
            "cache_hit_rate": cache_hits / total_queries if total_queries > 0 else 0,
            "cache_size": len(self.query_cache),
            "avg_execution_time_ms": sum(execution_times) / len(execution_times) if execution_times else 0,
            "p95_execution_time_ms": sorted(execution_times)[int(len(execution_times) * 0.95)] if execution_times else 0,
            "performance_goals": {
                "single_hop_under_50ms": sum(1 for t in execution_times if t < 50),
                "multi_hop_under_200ms": sum(1 for t in execution_times if t < 200)
            },
            "by_type": {}
        }
        
        # 타입별 통계 계산
        for qtype, times in type_stats.items():
            if times:
                stats["by_type"][qtype] = {
                    "count": len(times),
                    "avg_time_ms": sum(times) / len(times),
                    "max_time_ms": max(times),
                    "min_time_ms": min(times)
                }
        
        return stats
    
    def clear_cache(self):
        """캐시 초기화"""
        self.query_cache.clear()
        logger.info("Query cache cleared")
    
    def warm_up_cache(self, company_ids: List[str]):
        """캐시 워밍업 - 자주 사용되는 쿼리들을 미리 실행"""
        logger.info(f"Warming up cache for {len(company_ids)} companies")
        
        for company_id in company_ids:
            try:
                # 기본 정보 캐싱
                self.get_company_basic_info(company_id)
                # 연결 관계 캐싱
                self.get_company_connections(company_id)
                # 네트워크 리스크 캐싱
                self.calculate_network_risk_summary(company_id)
            except Exception as e:
                logger.warning(f"Cache warmup failed for {company_id}: {e}")
        
        logger.info("Cache warmup completed")


# 글로벌 인스턴스
_optimized_queries = OptimizedQueries()


def get_optimized_queries() -> OptimizedQueries:
    """최적화된 쿼리 인스턴스 반환"""
    return _optimized_queries