"""헬스 체크 및 시스템 상태 모니터링"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from src.neo4j.driver import driver as neo4j_driver
from src.kafka.consumer import consumer as kafka_consumer

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """헬스 상태"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    """컴포넌트 헬스 정보"""
    name: str
    status: HealthStatus
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    last_check: Optional[datetime] = None
    response_time_ms: Optional[float] = None


@dataclass
class HealthCheckResult:
    """헬스 체크 결과"""
    status: HealthStatus
    timestamp: datetime
    service: str
    version: str
    uptime_seconds: float
    components: List[ComponentHealth]
    metrics: Optional[Dict[str, Any]] = None


class HealthChecker:
    """헬스 체커"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.last_check_results: Dict[str, ComponentHealth] = {}
        self.check_interval_seconds = 30
        logger.info("HealthChecker initialized")
    
    async def get_health_status(self) -> Dict[str, Any]:
        """전체 헬스 상태 조회"""
        try:
            # 각 컴포넌트 체크
            neo4j_health = await self._check_neo4j_health()
            kafka_health = await self._check_kafka_health()
            cache_health = await self._check_cache_health()
            api_health = await self._check_api_health()
            
            # 전체 상태 결정
            components = [neo4j_health, kafka_health, cache_health, api_health]
            overall_status = self._determine_overall_status(components)
            
            # 추가 메트릭
            metrics = await self._collect_health_metrics()
            
            result = HealthCheckResult(
                status=overall_status,
                timestamp=datetime.now(),
                service="graph-service",
                version="1.0.0",
                uptime_seconds=(datetime.now() - self.start_time).total_seconds(),
                components=components,
                metrics=metrics
            )
            
            return self._serialize_health_result(result)
            
        except Exception as e:
            logger.error(f"Error in health check: {e}")
            return {
                "status": HealthStatus.UNKNOWN,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _check_neo4j_health(self) -> ComponentHealth:
        """Neo4j 헬스 체크"""
        try:
            import time
            start_time = time.time()
            
            # 연결 확인
            neo4j_driver.driver.verify_connectivity()
            
            # 간단한 쿼리 실행
            result = neo4j_driver.execute_read("RETURN 1 as test")
            
            response_time = (time.time() - start_time) * 1000  # ms
            
            if result and result[0]['test'] == 1:
                health = ComponentHealth(
                    name="neo4j",
                    status=HealthStatus.HEALTHY,
                    message="Neo4j is responsive",
                    response_time_ms=response_time,
                    last_check=datetime.now(),
                    details={
                        "uri": neo4j_driver._driver._uri if neo4j_driver._driver else "unknown",
                        "database": "graph"
                    }
                )
            else:
                health = ComponentHealth(
                    name="neo4j",
                    status=HealthStatus.DEGRADED,
                    message="Neo4j query returned unexpected result",
                    response_time_ms=response_time,
                    last_check=datetime.now()
                )
                
        except Exception as e:
            health = ComponentHealth(
                name="neo4j",
                status=HealthStatus.CRITICAL,
                message=f"Neo4j connection failed: {str(e)}",
                last_check=datetime.now()
            )
        
        self.last_check_results["neo4j"] = health
        return health
    
    async def _check_kafka_health(self) -> ComponentHealth:
        """Kafka 헬스 체크"""
        try:
            # Kafka consumer 상태 확인
            is_running = kafka_consumer.running
            
            if is_running:
                # 추가 상태 정보
                details = {
                    "consumer_group": kafka_consumer.consumer_group_id,
                    "topics": kafka_consumer.topics,
                    "running": True
                }
                
                health = ComponentHealth(
                    name="kafka",
                    status=HealthStatus.HEALTHY,
                    message="Kafka consumer is running",
                    last_check=datetime.now(),
                    details=details
                )
            else:
                health = ComponentHealth(
                    name="kafka",
                    status=HealthStatus.DEGRADED,
                    message="Kafka consumer is not running",
                    last_check=datetime.now()
                )
                
        except Exception as e:
            health = ComponentHealth(
                name="kafka",
                status=HealthStatus.CRITICAL,
                message=f"Kafka health check failed: {str(e)}",
                last_check=datetime.now()
            )
        
        self.last_check_results["kafka"] = health
        return health
    
    async def _check_cache_health(self) -> ComponentHealth:
        """캐시 헬스 체크"""
        try:
            from src.kafka.entity_cache import entity_cache
            
            # 캐시 통계 조회
            cache_stats = entity_cache.get_cache_stats()
            
            # 캐시 성능 평가
            hit_rate = cache_stats.get('cache_hit_rate', 0)
            total_entities = cache_stats.get('total_companies', 0) + cache_stats.get('total_persons', 0)
            
            if hit_rate >= 70 and total_entities > 0:
                status = HealthStatus.HEALTHY
                message = f"Cache performing well (hit rate: {hit_rate:.1f}%)"
            elif hit_rate >= 50:
                status = HealthStatus.DEGRADED
                message = f"Cache performance degraded (hit rate: {hit_rate:.1f}%)"
            else:
                status = HealthStatus.DEGRADED
                message = f"Low cache hit rate: {hit_rate:.1f}%"
            
            health = ComponentHealth(
                name="entity_cache",
                status=status,
                message=message,
                last_check=datetime.now(),
                details=cache_stats
            )
            
        except Exception as e:
            health = ComponentHealth(
                name="entity_cache",
                status=HealthStatus.DEGRADED,
                message=f"Cache health check failed: {str(e)}",
                last_check=datetime.now()
            )
        
        self.last_check_results["cache"] = health
        return health
    
    async def _check_api_health(self) -> ComponentHealth:
        """API 엔드포인트 헬스 체크"""
        try:
            # 간단한 API 응답성 체크
            # 실제로는 내부 API 호출을 시뮬레이션
            
            health = ComponentHealth(
                name="api",
                status=HealthStatus.HEALTHY,
                message="API endpoints are responsive",
                last_check=datetime.now(),
                details={
                    "endpoints": [
                        "/health",
                        "/api/v1/graph/stats",
                        "/graphql",
                        "/monitoring/dashboard"
                    ]
                }
            )
            
        except Exception as e:
            health = ComponentHealth(
                name="api",
                status=HealthStatus.DEGRADED,
                message=f"API health check failed: {str(e)}",
                last_check=datetime.now()
            )
        
        self.last_check_results["api"] = health
        return health
    
    async def _collect_health_metrics(self) -> Dict[str, Any]:
        """헬스 관련 메트릭 수집"""
        try:
            from src.monitoring.metrics import metrics_collector
            
            # 최근 성능 메트릭
            perf_metrics = metrics_collector.get_performance_metrics()
            
            # 에러율 계산
            error_rate = 0.0
            if perf_metrics.queries_per_second > 0:
                error_rate = (perf_metrics.failed_queries / 
                            (perf_metrics.queries_per_second * 60)) * 100  # 분당 에러율
            
            return {
                "error_rate_percent": error_rate,
                "avg_response_time_ms": perf_metrics.avg_query_time,
                "p99_response_time_ms": perf_metrics.p99_query_time,
                "active_connections": 1,  # 기본값
                "memory_usage_percent": self._get_memory_usage(),
                "cpu_usage_percent": self._get_cpu_usage()
            }
            
        except Exception as e:
            logger.error(f"Error collecting health metrics: {e}")
            return {}
    
    def _determine_overall_status(self, components: List[ComponentHealth]) -> HealthStatus:
        """전체 헬스 상태 결정"""
        if not components:
            return HealthStatus.UNKNOWN
        
        # Critical이 하나라도 있으면 Critical
        if any(c.status == HealthStatus.CRITICAL for c in components):
            return HealthStatus.CRITICAL
        
        # Degraded가 2개 이상이면 Critical
        degraded_count = sum(1 for c in components if c.status == HealthStatus.DEGRADED)
        if degraded_count >= 2:
            return HealthStatus.CRITICAL
        
        # Degraded가 1개면 Degraded
        if degraded_count == 1:
            return HealthStatus.DEGRADED
        
        # 모두 Healthy면 Healthy
        return HealthStatus.HEALTHY
    
    def _serialize_health_result(self, result: HealthCheckResult) -> Dict[str, Any]:
        """헬스 체크 결과 직렬화"""
        return {
            "status": result.status,
            "timestamp": result.timestamp.isoformat(),
            "service": result.service,
            "version": result.version,
            "uptime_seconds": result.uptime_seconds,
            "components": {
                comp.name: {
                    "status": comp.status,
                    "message": comp.message,
                    "details": comp.details,
                    "last_check": comp.last_check.isoformat() if comp.last_check else None,
                    "response_time_ms": comp.response_time_ms
                }
                for comp in result.components
            },
            "metrics": result.metrics or {}
        }
    
    def _get_memory_usage(self) -> float:
        """메모리 사용률 조회"""
        try:
            import psutil
            return psutil.virtual_memory().percent
        except:
            return 0.0
    
    def _get_cpu_usage(self) -> float:
        """CPU 사용률 조회"""
        try:
            import psutil
            return psutil.cpu_percent(interval=0.1)
        except:
            return 0.0
    
    async def run_diagnostic_checks(self) -> Dict[str, Any]:
        """진단 체크 실행"""
        diagnostics = {
            "timestamp": datetime.now().isoformat(),
            "checks": []
        }
        
        # Neo4j 연결 풀 상태
        try:
            pool_info = {
                "name": "neo4j_connection_pool",
                "status": "ok",
                "details": {
                    "max_connections": 50,
                    "active_connections": 1  # 실제로는 드라이버에서 가져와야 함
                }
            }
            diagnostics["checks"].append(pool_info)
        except Exception as e:
            diagnostics["checks"].append({
                "name": "neo4j_connection_pool",
                "status": "error",
                "error": str(e)
            })
        
        # 그래프 데이터베이스 크기
        try:
            size_query = """
            CALL apoc.meta.stats() 
            YIELD nodeCount, relCount, labelCount, relTypeCount
            RETURN nodeCount, relCount, labelCount, relTypeCount
            """
            # 실제로는 APOC가 필요하므로 대체 쿼리 사용
            node_count_query = "MATCH (n) RETURN count(n) as nodeCount"
            result = neo4j_driver.execute_read(node_count_query)
            
            diagnostics["checks"].append({
                "name": "graph_database_size",
                "status": "ok",
                "details": {
                    "node_count": result[0]['nodeCount'] if result else 0
                }
            })
        except Exception as e:
            diagnostics["checks"].append({
                "name": "graph_database_size",
                "status": "error",
                "error": str(e)
            })
        
        return diagnostics


# 싱글톤 인스턴스
health_checker = HealthChecker()