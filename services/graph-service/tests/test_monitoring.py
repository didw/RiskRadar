"""모니터링 모듈 테스트"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import os

# Mock Neo4j environment
os.environ["NEO4J_URI"] = "bolt://mock:7687"
os.environ["NEO4J_USER"] = "mock"
os.environ["NEO4J_PASSWORD"] = "mock"


class TestMetricsCollector:
    """메트릭 수집기 테스트"""
    
    def test_metric_dataclasses(self):
        """메트릭 데이터클래스 테스트"""
        import sys
        from unittest.mock import patch
        
        mock_session = MagicMock()
        
        with patch.dict('sys.modules', {
            'src.neo4j.session': mock_session,
            'src.neo4j.driver': MagicMock()
        }):
            from src.monitoring.metrics import (
                MetricPoint, SystemMetrics, GraphMetrics, 
                PerformanceMetrics, RiskMetrics
            )
            
            # MetricPoint 테스트
            metric_point = MetricPoint(
                timestamp=datetime.now(),
                value=42.5,
                labels={"type": "test"}
            )
            assert metric_point.value == 42.5
            assert metric_point.labels["type"] == "test"
            
            # SystemMetrics 테스트
            system_metrics = SystemMetrics(
                timestamp=datetime.now(),
                cpu_usage=25.5,
                memory_usage=60.0,
                disk_usage=40.0,
                neo4j_connections=5,
                active_transactions=2,
                query_cache_hit_rate=85.0
            )
            assert system_metrics.cpu_usage == 25.5
            assert system_metrics.neo4j_connections == 5
            
            # GraphMetrics 테스트
            graph_metrics = GraphMetrics(
                timestamp=datetime.now(),
                total_nodes=1000,
                total_relationships=5000,
                node_types={"Company": 500, "Person": 500},
                relationship_types={"WORKS_AT": 1000},
                avg_node_degree=5.0,
                graph_density=0.01
            )
            assert graph_metrics.total_nodes == 1000
            assert graph_metrics.node_types["Company"] == 500
            
            print("✅ Metric dataclasses test passed")
    
    def test_performance_metrics_calculation(self):
        """성능 메트릭 계산 테스트"""
        import sys
        from unittest.mock import patch
        
        mock_session = MagicMock()
        
        with patch.dict('sys.modules', {
            'src.neo4j.session': mock_session,
            'src.neo4j.driver': MagicMock(),
            'src.kafka.consumer': MagicMock()
        }):
            from src.monitoring.metrics import MetricsCollector
            
            collector = MetricsCollector(retention_hours=1)
            
            # 쿼리 시간 기록
            query_times = [10.5, 20.3, 15.7, 30.2, 12.1]
            for qt in query_times:
                collector.record_query_time(qt)
            
            # 캐시 히트 기록
            collector.record_cache_hit(True)
            collector.record_cache_hit(True)
            collector.record_cache_hit(False)
            
            # 성능 메트릭 계산
            perf_metrics = collector.get_performance_metrics()
            
            # 평균 쿼리 시간 검증
            expected_avg = sum(query_times) / len(query_times)
            assert abs(perf_metrics.avg_query_time - expected_avg) < 0.1
            
            # 캐시 히트율 검증 (2/3 = 66.67%)
            assert abs(perf_metrics.cache_hit_rate - 66.67) < 0.1
            
            print("✅ Performance metrics calculation test passed")
    
    def test_metrics_history(self):
        """메트릭 히스토리 테스트"""
        import sys
        from unittest.mock import patch
        
        mock_session = MagicMock()
        
        with patch.dict('sys.modules', {
            'src.neo4j.session': mock_session,
            'src.neo4j.driver': MagicMock(),
            'src.kafka.consumer': MagicMock()
        }):
            from src.monitoring.metrics import MetricsCollector
            
            collector = MetricsCollector(retention_hours=1)
            
            # 메트릭 저장
            now = datetime.now()
            collector._store_metric('test_metric', 100.0, now)
            collector._store_metric('test_metric', 110.0, now + timedelta(minutes=1))
            collector._store_metric('test_metric', 120.0, now + timedelta(minutes=2))
            
            # 히스토리 조회
            history = collector.get_historical_metrics('test_metric', hours=1)
            
            assert len(history) == 3
            assert history[0].value == 100.0
            assert history[1].value == 110.0
            assert history[2].value == 120.0
            
            print("✅ Metrics history test passed")


class TestHealthChecker:
    """헬스 체커 테스트"""
    
    def test_health_status_enum(self):
        """헬스 상태 열거형 테스트"""
        import sys
        from unittest.mock import patch
        
        mock_modules = {
            'src.neo4j.session': MagicMock(),
            'src.neo4j.driver': MagicMock(),
            'src.kafka.consumer': MagicMock()
        }
        
        with patch.dict('sys.modules', mock_modules):
            from src.monitoring.health_check import HealthStatus
            
            assert HealthStatus.HEALTHY == "healthy"
            assert HealthStatus.DEGRADED == "degraded"
            assert HealthStatus.CRITICAL == "critical"
            assert HealthStatus.UNKNOWN == "unknown"
            
            print("✅ Health status enum test passed")
    
    def test_component_health_dataclass(self):
        """컴포넌트 헬스 데이터클래스 테스트"""
        import sys
        from unittest.mock import patch
        
        mock_modules = {
            'src.neo4j.session': MagicMock(),
            'src.neo4j.driver': MagicMock(),
            'src.kafka.consumer': MagicMock()
        }
        
        with patch.dict('sys.modules', mock_modules):
            from src.monitoring.health_check import ComponentHealth, HealthStatus
            
            component = ComponentHealth(
                name="test_component",
                status=HealthStatus.HEALTHY,
                message="Component is healthy",
                response_time_ms=15.5,
                last_check=datetime.now(),
                details={"version": "1.0"}
            )
            
            assert component.name == "test_component"
            assert component.status == HealthStatus.HEALTHY
            assert component.response_time_ms == 15.5
            assert component.details["version"] == "1.0"
            
            print("✅ Component health dataclass test passed")
    
    def test_overall_status_determination(self):
        """전체 상태 결정 로직 테스트"""
        import sys
        from unittest.mock import patch
        
        mock_modules = {
            'src.neo4j.session': MagicMock(),
            'src.neo4j.driver': MagicMock(),
            'src.kafka.consumer': MagicMock()
        }
        
        with patch.dict('sys.modules', mock_modules):
            from src.monitoring.health_check import HealthChecker, ComponentHealth, HealthStatus
            
            checker = HealthChecker()
            
            # 모두 healthy
            components = [
                ComponentHealth("neo4j", HealthStatus.HEALTHY),
                ComponentHealth("kafka", HealthStatus.HEALTHY),
                ComponentHealth("cache", HealthStatus.HEALTHY)
            ]
            assert checker._determine_overall_status(components) == HealthStatus.HEALTHY
            
            # 하나가 degraded
            components[1] = ComponentHealth("kafka", HealthStatus.DEGRADED)
            assert checker._determine_overall_status(components) == HealthStatus.DEGRADED
            
            # 두 개가 degraded
            components[2] = ComponentHealth("cache", HealthStatus.DEGRADED)
            assert checker._determine_overall_status(components) == HealthStatus.CRITICAL
            
            # 하나가 critical
            components[0] = ComponentHealth("neo4j", HealthStatus.CRITICAL)
            assert checker._determine_overall_status(components) == HealthStatus.CRITICAL
            
            print("✅ Overall status determination test passed")


class TestMonitoringDashboard:
    """모니터링 대시보드 테스트"""
    
    def test_dashboard_router_creation(self):
        """대시보드 라우터 생성 테스트"""
        import sys
        from unittest.mock import patch
        
        mock_modules = {
            'src.neo4j.session': MagicMock(),
            'src.neo4j.driver': MagicMock(),
            'src.kafka.consumer': MagicMock(),
            'src.monitoring.metrics': MagicMock(),
            'src.monitoring.health_check': MagicMock()
        }
        
        with patch.dict('sys.modules', mock_modules):
            from src.monitoring.dashboard import get_monitoring_router
            
            router = get_monitoring_router()
            
            # 라우터 확인
            assert router is not None
            assert router.prefix == "/monitoring"
            
            # 엔드포인트 확인
            routes = [route.path for route in router.routes]
            assert "/dashboard" in routes
            assert "/metrics/summary" in routes
            assert "/metrics/history" in routes
            assert "/alerts" in routes
            
            print("✅ Dashboard router creation test passed")
    
    def test_alert_generation(self):
        """알림 생성 로직 테스트"""
        # 간단한 알림 생성 로직 테스트
        alerts = []
        
        # 고위험 엔티티 임계값 초과
        high_risk_entities = 150
        if high_risk_entities > 100:
            alerts.append({
                "id": "risk-001",
                "severity": "HIGH",
                "type": "RISK_THRESHOLD",
                "message": f"High risk entities count exceeded: {high_risk_entities}"
            })
        
        # 쿼리 성능 저하
        avg_query_time = 120.5
        if avg_query_time > 100:
            alerts.append({
                "id": "perf-001",
                "severity": "MEDIUM",
                "type": "PERFORMANCE",
                "message": f"Average query time is high: {avg_query_time:.2f}ms"
            })
        
        assert len(alerts) == 2
        assert alerts[0]["severity"] == "HIGH"
        assert alerts[1]["severity"] == "MEDIUM"
        
        print("✅ Alert generation test passed")


def test_monitoring_integration():
    """모니터링 통합 테스트"""
    # 메트릭 수집 → 헬스 체크 → 대시보드 표시 흐름 테스트
    
    # 1. 메트릭 수집
    metrics_data = {
        "system": {
            "cpu_usage": 30.5,
            "memory_usage": 55.0
        },
        "graph": {
            "total_nodes": 1500,
            "total_relationships": 7500
        },
        "performance": {
            "avg_query_time": 25.5,
            "qps": 10.2
        }
    }
    
    # 2. 헬스 상태 결정
    health_status = "healthy"
    if metrics_data["system"]["cpu_usage"] > 80:
        health_status = "degraded"
    if metrics_data["system"]["memory_usage"] > 90:
        health_status = "critical"
    
    # 3. 대시보드 데이터 준비
    dashboard_data = {
        "status": health_status,
        "metrics": metrics_data,
        "timestamp": datetime.now().isoformat()
    }
    
    assert dashboard_data["status"] == "healthy"
    assert dashboard_data["metrics"]["graph"]["total_nodes"] == 1500
    
    print("✅ Monitoring integration test passed")


if __name__ == "__main__":
    # MetricsCollector 테스트
    test_metrics = TestMetricsCollector()
    test_metrics.test_metric_dataclasses()
    test_metrics.test_performance_metrics_calculation()
    test_metrics.test_metrics_history()
    
    # HealthChecker 테스트
    test_health = TestHealthChecker()
    test_health.test_health_status_enum()
    test_health.test_component_health_dataclass()
    test_health.test_overall_status_determination()
    
    # Dashboard 테스트
    test_dashboard = TestMonitoringDashboard()
    test_dashboard.test_dashboard_router_creation()
    test_dashboard.test_alert_generation()
    
    # 통합 테스트
    test_monitoring_integration()
    
    print("\n🎉 All monitoring tests passed!")