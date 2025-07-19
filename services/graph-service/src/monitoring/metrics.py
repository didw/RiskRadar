"""모니터링 메트릭 수집기"""
import time
import logging
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, deque

from src.neo4j.session import session

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """메트릭 데이터 포인트"""
    timestamp: datetime
    value: float
    labels: Optional[Dict[str, str]] = None


@dataclass
class SystemMetrics:
    """시스템 메트릭"""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    neo4j_connections: int
    active_transactions: int
    query_cache_hit_rate: float


@dataclass
class GraphMetrics:
    """그래프 메트릭"""
    timestamp: datetime
    total_nodes: int
    total_relationships: int
    node_types: Dict[str, int]
    relationship_types: Dict[str, int]
    avg_node_degree: float
    graph_density: float


@dataclass
class PerformanceMetrics:
    """성능 메트릭"""
    timestamp: datetime
    avg_query_time: float
    p95_query_time: float
    p99_query_time: float
    queries_per_second: float
    failed_queries: int
    cache_hit_rate: float


@dataclass
class RiskMetrics:
    """리스크 메트릭"""
    timestamp: datetime
    avg_risk_score: float
    high_risk_entities: int
    risk_score_distribution: Dict[str, int]  # LOW, MEDIUM, HIGH
    risk_trends: List[float]  # Last 24 hours


class MetricsCollector:
    """메트릭 수집기"""
    
    def __init__(self, retention_hours: int = 24):
        self.retention_hours = retention_hours
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=retention_hours * 60))  # 1분 간격
        self.query_times: deque = deque(maxlen=1000)  # 최근 1000개 쿼리
        self.start_time = datetime.now()
        self.query_count = 0
        self.failed_query_count = 0
        self.cache_hits = 0
        self.cache_requests = 0
        self._lock = threading.RLock()
        
        # 자동 수집 시작
        self._collection_thread = threading.Thread(target=self._collect_metrics_loop, daemon=True)
        self._collection_thread.start()
        
        logger.info("MetricsCollector initialized")
    
    def record_query_time(self, query_time: float, success: bool = True):
        """쿼리 시간 기록"""
        with self._lock:
            self.query_times.append(query_time)
            self.query_count += 1
            
            if not success:
                self.failed_query_count += 1
    
    def record_cache_hit(self, hit: bool = True):
        """캐시 히트 기록"""
        with self._lock:
            self.cache_requests += 1
            if hit:
                self.cache_hits += 1
    
    def get_system_metrics(self) -> SystemMetrics:
        """시스템 메트릭 수집"""
        try:
            # Neo4j 연결 상태 확인
            neo4j_connections = self._get_neo4j_connections()
            active_transactions = self._get_active_transactions()
            query_cache_hit_rate = self._get_query_cache_hit_rate()
            
            # 시스템 리소스 (간단한 근사치)
            cpu_usage = self._get_cpu_usage()
            memory_usage = self._get_memory_usage()
            disk_usage = self._get_disk_usage()
            
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                neo4j_connections=neo4j_connections,
                active_transactions=active_transactions,
                query_cache_hit_rate=query_cache_hit_rate
            )
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_usage=0.0,
                memory_usage=0.0,
                disk_usage=0.0,
                neo4j_connections=0,
                active_transactions=0,
                query_cache_hit_rate=0.0
            )
    
    def get_graph_metrics(self) -> GraphMetrics:
        """그래프 메트릭 수집"""
        try:
            # 노드 통계
            node_query = """
            MATCH (n)
            RETURN labels(n)[0] as type, count(n) as count
            """
            node_results = session.run_query(node_query)
            
            # 관계 통계
            rel_query = """
            MATCH ()-[r]->()
            RETURN type(r) as type, count(r) as count
            """
            rel_results = session.run_query(rel_query)
            
            # 평균 연결도
            degree_query = """
            MATCH (n)
            OPTIONAL MATCH (n)-[r]-()
            WITH n, count(r) as degree
            RETURN avg(degree) as avg_degree
            """
            degree_result = session.run_query(degree_query)
            
            # 결과 처리
            node_types = {row['type']: row['count'] for row in node_results if row['type']}
            rel_types = {row['type']: row['count'] for row in rel_results}
            
            total_nodes = sum(node_types.values())
            total_rels = sum(rel_types.values())
            avg_degree = degree_result[0]['avg_degree'] if degree_result else 0.0
            
            # 그래프 밀도 계산
            graph_density = 0.0
            if total_nodes > 1:
                max_edges = total_nodes * (total_nodes - 1) / 2
                graph_density = total_rels / max_edges if max_edges > 0 else 0.0
            
            return GraphMetrics(
                timestamp=datetime.now(),
                total_nodes=total_nodes,
                total_relationships=total_rels,
                node_types=node_types,
                relationship_types=rel_types,
                avg_node_degree=avg_degree,
                graph_density=graph_density
            )
            
        except Exception as e:
            logger.error(f"Error collecting graph metrics: {e}")
            return GraphMetrics(
                timestamp=datetime.now(),
                total_nodes=0,
                total_relationships=0,
                node_types={},
                relationship_types={},
                avg_node_degree=0.0,
                graph_density=0.0
            )
    
    def get_performance_metrics(self) -> PerformanceMetrics:
        """성능 메트릭 수집"""
        try:
            with self._lock:
                query_times_list = list(self.query_times)
                
                if not query_times_list:
                    return PerformanceMetrics(
                        timestamp=datetime.now(),
                        avg_query_time=0.0,
                        p95_query_time=0.0,
                        p99_query_time=0.0,
                        queries_per_second=0.0,
                        failed_queries=self.failed_query_count,
                        cache_hit_rate=0.0
                    )
                
                # 쿼리 시간 통계
                avg_query_time = sum(query_times_list) / len(query_times_list)
                sorted_times = sorted(query_times_list)
                
                p95_idx = int(len(sorted_times) * 0.95)
                p99_idx = int(len(sorted_times) * 0.99)
                
                p95_query_time = sorted_times[p95_idx] if p95_idx < len(sorted_times) else sorted_times[-1]
                p99_query_time = sorted_times[p99_idx] if p99_idx < len(sorted_times) else sorted_times[-1]
                
                # QPS 계산
                time_elapsed = (datetime.now() - self.start_time).total_seconds()
                queries_per_second = self.query_count / time_elapsed if time_elapsed > 0 else 0.0
                
                # 캐시 히트율
                cache_hit_rate = (self.cache_hits / self.cache_requests * 100) if self.cache_requests > 0 else 0.0
                
                return PerformanceMetrics(
                    timestamp=datetime.now(),
                    avg_query_time=avg_query_time,
                    p95_query_time=p95_query_time,
                    p99_query_time=p99_query_time,
                    queries_per_second=queries_per_second,
                    failed_queries=self.failed_query_count,
                    cache_hit_rate=cache_hit_rate
                )
                
        except Exception as e:
            logger.error(f"Error collecting performance metrics: {e}")
            return PerformanceMetrics(
                timestamp=datetime.now(),
                avg_query_time=0.0,
                p95_query_time=0.0,
                p99_query_time=0.0,
                queries_per_second=0.0,
                failed_queries=self.failed_query_count,
                cache_hit_rate=0.0
            )
    
    def get_risk_metrics(self) -> RiskMetrics:
        """리스크 메트릭 수집"""
        try:
            # 리스크 점수 통계
            risk_query = """
            MATCH (n)
            WHERE n.risk_score IS NOT NULL
            WITH n.risk_score as risk_score
            RETURN 
                avg(risk_score) as avg_risk,
                count(CASE WHEN risk_score >= 7.0 THEN 1 END) as high_risk_count,
                count(CASE WHEN risk_score >= 5.0 AND risk_score < 7.0 THEN 1 END) as medium_risk_count,
                count(CASE WHEN risk_score < 5.0 THEN 1 END) as low_risk_count
            """
            
            result = session.run_query(risk_query)
            
            if result:
                data = result[0]
                avg_risk = data['avg_risk'] or 5.0
                high_risk_entities = data['high_risk_count'] or 0
                
                risk_distribution = {
                    'HIGH': data['high_risk_count'] or 0,
                    'MEDIUM': data['medium_risk_count'] or 0,
                    'LOW': data['low_risk_count'] or 0
                }
            else:
                avg_risk = 5.0
                high_risk_entities = 0
                risk_distribution = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
            
            # 리스크 트렌드 (최근 기록에서)
            risk_trends = self._get_risk_trends()
            
            return RiskMetrics(
                timestamp=datetime.now(),
                avg_risk_score=avg_risk,
                high_risk_entities=high_risk_entities,
                risk_score_distribution=risk_distribution,
                risk_trends=risk_trends
            )
            
        except Exception as e:
            logger.error(f"Error collecting risk metrics: {e}")
            return RiskMetrics(
                timestamp=datetime.now(),
                avg_risk_score=5.0,
                high_risk_entities=0,
                risk_score_distribution={'HIGH': 0, 'MEDIUM': 0, 'LOW': 0},
                risk_trends=[]
            )
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """전체 메트릭 요약"""
        system_metrics = self.get_system_metrics()
        graph_metrics = self.get_graph_metrics()
        performance_metrics = self.get_performance_metrics()
        risk_metrics = self.get_risk_metrics()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'system': asdict(system_metrics),
            'graph': asdict(graph_metrics),
            'performance': asdict(performance_metrics),
            'risk': asdict(risk_metrics),
            'uptime_seconds': (datetime.now() - self.start_time).total_seconds()
        }
    
    def get_historical_metrics(
        self,
        metric_type: str,
        hours: int = 1
    ) -> List[MetricPoint]:
        """과거 메트릭 조회"""
        try:
            history = self.metrics_history.get(metric_type, deque())
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            return [
                point for point in history
                if point.timestamp >= cutoff_time
            ]
            
        except Exception as e:
            logger.error(f"Error getting historical metrics: {e}")
            return []
    
    def _collect_metrics_loop(self):
        """메트릭 수집 루프 (백그라운드)"""
        while True:
            try:
                # 시스템 메트릭 저장
                system_metrics = self.get_system_metrics()
                self._store_metric('cpu_usage', system_metrics.cpu_usage, system_metrics.timestamp)
                self._store_metric('memory_usage', system_metrics.memory_usage, system_metrics.timestamp)
                self._store_metric('neo4j_connections', system_metrics.neo4j_connections, system_metrics.timestamp)
                
                # 그래프 메트릭 저장
                graph_metrics = self.get_graph_metrics()
                self._store_metric('total_nodes', graph_metrics.total_nodes, graph_metrics.timestamp)
                self._store_metric('total_relationships', graph_metrics.total_relationships, graph_metrics.timestamp)
                self._store_metric('graph_density', graph_metrics.graph_density, graph_metrics.timestamp)
                
                # 성능 메트릭 저장
                perf_metrics = self.get_performance_metrics()
                self._store_metric('avg_query_time', perf_metrics.avg_query_time, perf_metrics.timestamp)
                self._store_metric('queries_per_second', perf_metrics.queries_per_second, perf_metrics.timestamp)
                
                # 리스크 메트릭 저장
                risk_metrics = self.get_risk_metrics()
                self._store_metric('avg_risk_score', risk_metrics.avg_risk_score, risk_metrics.timestamp)
                self._store_metric('high_risk_entities', risk_metrics.high_risk_entities, risk_metrics.timestamp)
                
                time.sleep(60)  # 1분마다 수집
                
            except Exception as e:
                logger.error(f"Error in metrics collection loop: {e}")
                time.sleep(60)
    
    def _store_metric(self, metric_name: str, value: float, timestamp: datetime):
        """메트릭 저장"""
        metric_point = MetricPoint(timestamp=timestamp, value=value)
        self.metrics_history[metric_name].append(metric_point)
    
    def _get_neo4j_connections(self) -> int:
        """Neo4j 연결 수 조회"""
        try:
            query = "CALL dbms.listConnections() YIELD connectionId RETURN count(*) as connections"
            result = session.run_query(query)
            return result[0]['connections'] if result else 0
        except:
            return 1  # 기본값 (현재 연결)
    
    def _get_active_transactions(self) -> int:
        """활성 트랜잭션 수 조회"""
        try:
            query = "CALL dbms.listTransactions() YIELD transactionId RETURN count(*) as transactions"
            result = session.run_query(query)
            return result[0]['transactions'] if result else 0
        except:
            return 0
    
    def _get_query_cache_hit_rate(self) -> float:
        """쿼리 캐시 히트율 조회"""
        try:
            # 내부 캐시 히트율 사용
            with self._lock:
                if self.cache_requests > 0:
                    return (self.cache_hits / self.cache_requests) * 100
                return 0.0
        except:
            return 0.0
    
    def _get_cpu_usage(self) -> float:
        """CPU 사용률 (근사치)"""
        try:
            import psutil
            return psutil.cpu_percent(interval=1)
        except:
            return 0.0
    
    def _get_memory_usage(self) -> float:
        """메모리 사용률 (근사치)"""
        try:
            import psutil
            return psutil.virtual_memory().percent
        except:
            return 0.0
    
    def _get_disk_usage(self) -> float:
        """디스크 사용률 (근사치)"""
        try:
            import psutil
            return psutil.disk_usage('/').percent
        except:
            return 0.0
    
    def _get_risk_trends(self) -> List[float]:
        """리스크 트렌드 조회"""
        risk_history = self.metrics_history.get('avg_risk_score', deque())
        return [point.value for point in list(risk_history)[-24:]]  # 최근 24시간


# 싱글톤 인스턴스
metrics_collector = MetricsCollector()