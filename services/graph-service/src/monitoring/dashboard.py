"""모니터링 대시보드 API"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse

from src.monitoring.metrics import metrics_collector
from src.monitoring.health_check import health_checker

logger = logging.getLogger(__name__)

# API 라우터 생성
router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/dashboard", response_class=HTMLResponse)
async def monitoring_dashboard():
    """모니터링 대시보드 HTML 페이지"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>RiskRadar Graph Service - Monitoring Dashboard</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                max-width: 1400px;
                margin: 0 auto;
            }
            h1 {
                color: #333;
                border-bottom: 2px solid #007bff;
                padding-bottom: 10px;
            }
            .metrics-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }
            .metric-card {
                background: white;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .metric-title {
                font-size: 18px;
                font-weight: bold;
                color: #555;
                margin-bottom: 10px;
            }
            .metric-value {
                font-size: 36px;
                font-weight: bold;
                color: #007bff;
            }
            .metric-unit {
                font-size: 14px;
                color: #999;
            }
            .metric-trend {
                font-size: 14px;
                margin-top: 5px;
            }
            .trend-up {
                color: #28a745;
            }
            .trend-down {
                color: #dc3545;
            }
            .chart-container {
                width: 100%;
                height: 300px;
                margin-top: 20px;
            }
            .status-indicator {
                display: inline-block;
                width: 10px;
                height: 10px;
                border-radius: 50%;
                margin-right: 5px;
            }
            .status-healthy {
                background-color: #28a745;
            }
            .status-warning {
                background-color: #ffc107;
            }
            .status-critical {
                background-color: #dc3545;
            }
            .refresh-button {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
            }
            .refresh-button:hover {
                background-color: #0056b3;
            }
            .last-updated {
                color: #666;
                font-size: 14px;
                margin-top: 10px;
            }
        </style>
        <script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
    </head>
    <body>
        <div class="container">
            <h1>RiskRadar Graph Service Monitoring Dashboard</h1>
            
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div class="last-updated">Last updated: <span id="lastUpdated">-</span></div>
                <button class="refresh-button" onclick="refreshMetrics()">Refresh</button>
            </div>
            
            <div class="metrics-grid" id="metricsGrid">
                <!-- System Metrics -->
                <div class="metric-card">
                    <div class="metric-title">System Status</div>
                    <div id="systemStatus">
                        <span class="status-indicator status-healthy"></span>
                        <span>Loading...</span>
                    </div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-title">Total Nodes</div>
                    <div class="metric-value" id="totalNodes">-</div>
                    <div class="metric-unit">nodes in graph</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-title">Total Relationships</div>
                    <div class="metric-value" id="totalRelationships">-</div>
                    <div class="metric-unit">connections</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-title">Average Query Time</div>
                    <div class="metric-value" id="avgQueryTime">-</div>
                    <div class="metric-unit">ms</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-title">Queries Per Second</div>
                    <div class="metric-value" id="qps">-</div>
                    <div class="metric-unit">QPS</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-title">Cache Hit Rate</div>
                    <div class="metric-value" id="cacheHitRate">-</div>
                    <div class="metric-unit">%</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-title">High Risk Entities</div>
                    <div class="metric-value" id="highRiskEntities">-</div>
                    <div class="metric-unit">entities</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-title">Average Risk Score</div>
                    <div class="metric-value" id="avgRiskScore">-</div>
                    <div class="metric-unit">out of 10</div>
                </div>
            </div>
            
            <!-- Charts -->
            <div style="margin-top: 40px;">
                <h2>Performance Trends</h2>
                <div class="chart-container">
                    <canvas id="performanceChart"></canvas>
                </div>
            </div>
            
            <div style="margin-top: 40px;">
                <h2>Risk Distribution</h2>
                <div class="chart-container">
                    <canvas id="riskChart"></canvas>
                </div>
            </div>
        </div>
        
        <script>
            let performanceChart = null;
            let riskChart = null;
            
            async function fetchMetrics() {
                try {
                    const response = await fetch('/monitoring/metrics/summary');
                    return await response.json();
                } catch (error) {
                    console.error('Error fetching metrics:', error);
                    return null;
                }
            }
            
            async function fetchHistoricalMetrics(metric, hours = 1) {
                try {
                    const response = await fetch(`/monitoring/metrics/history?metric=${metric}&hours=${hours}`);
                    return await response.json();
                } catch (error) {
                    console.error('Error fetching historical metrics:', error);
                    return [];
                }
            }
            
            function updateMetricValue(elementId, value, format = 'number') {
                const element = document.getElementById(elementId);
                if (element) {
                    if (format === 'number') {
                        element.textContent = Number(value).toFixed(2);
                    } else if (format === 'integer') {
                        element.textContent = Math.round(value);
                    } else {
                        element.textContent = value;
                    }
                }
            }
            
            function updateSystemStatus(status) {
                const statusElement = document.getElementById('systemStatus');
                if (statusElement) {
                    let statusClass = 'status-healthy';
                    let statusText = 'Healthy';
                    
                    if (status === 'degraded') {
                        statusClass = 'status-warning';
                        statusText = 'Degraded';
                    } else if (status === 'critical') {
                        statusClass = 'status-critical';
                        statusText = 'Critical';
                    }
                    
                    statusElement.innerHTML = `
                        <span class="status-indicator ${statusClass}"></span>
                        <span>${statusText}</span>
                    `;
                }
            }
            
            async function updateCharts() {
                // Performance Chart
                const perfData = await fetchHistoricalMetrics('avg_query_time', 1);
                const qpsData = await fetchHistoricalMetrics('queries_per_second', 1);
                
                if (performanceChart) {
                    performanceChart.destroy();
                }
                
                const ctx1 = document.getElementById('performanceChart').getContext('2d');
                performanceChart = new Chart(ctx1, {
                    type: 'line',
                    data: {
                        labels: perfData.map(d => new Date(d.timestamp).toLocaleTimeString()),
                        datasets: [{
                            label: 'Avg Query Time (ms)',
                            data: perfData.map(d => d.value),
                            borderColor: 'rgb(0, 123, 255)',
                            backgroundColor: 'rgba(0, 123, 255, 0.1)',
                            yAxisID: 'y',
                        }, {
                            label: 'QPS',
                            data: qpsData.map(d => d.value),
                            borderColor: 'rgb(255, 99, 132)',
                            backgroundColor: 'rgba(255, 99, 132, 0.1)',
                            yAxisID: 'y1',
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        interaction: {
                            mode: 'index',
                            intersect: false,
                        },
                        scales: {
                            y: {
                                type: 'linear',
                                display: true,
                                position: 'left',
                                title: {
                                    display: true,
                                    text: 'Query Time (ms)'
                                }
                            },
                            y1: {
                                type: 'linear',
                                display: true,
                                position: 'right',
                                title: {
                                    display: true,
                                    text: 'QPS'
                                },
                                grid: {
                                    drawOnChartArea: false,
                                },
                            },
                        }
                    }
                });
            }
            
            async function refreshMetrics() {
                const metrics = await fetchMetrics();
                if (!metrics) return;
                
                // Update system status
                updateSystemStatus(metrics.health?.status || 'unknown');
                
                // Update graph metrics
                updateMetricValue('totalNodes', metrics.graph.total_nodes, 'integer');
                updateMetricValue('totalRelationships', metrics.graph.total_relationships, 'integer');
                
                // Update performance metrics
                updateMetricValue('avgQueryTime', metrics.performance.avg_query_time);
                updateMetricValue('qps', metrics.performance.queries_per_second);
                updateMetricValue('cacheHitRate', metrics.performance.cache_hit_rate);
                
                // Update risk metrics
                updateMetricValue('highRiskEntities', metrics.risk.high_risk_entities, 'integer');
                updateMetricValue('avgRiskScore', metrics.risk.avg_risk_score);
                
                // Update last updated time
                document.getElementById('lastUpdated').textContent = new Date().toLocaleString();
                
                // Update charts
                await updateCharts();
                
                // Risk Distribution Chart
                if (riskChart) {
                    riskChart.destroy();
                }
                
                const ctx2 = document.getElementById('riskChart').getContext('2d');
                riskChart = new Chart(ctx2, {
                    type: 'doughnut',
                    data: {
                        labels: ['Low Risk', 'Medium Risk', 'High Risk'],
                        datasets: [{
                            data: [
                                metrics.risk.risk_score_distribution.LOW || 0,
                                metrics.risk.risk_score_distribution.MEDIUM || 0,
                                metrics.risk.risk_score_distribution.HIGH || 0
                            ],
                            backgroundColor: [
                                'rgba(40, 167, 69, 0.8)',
                                'rgba(255, 193, 7, 0.8)',
                                'rgba(220, 53, 69, 0.8)'
                            ],
                            borderColor: [
                                'rgb(40, 167, 69)',
                                'rgb(255, 193, 7)',
                                'rgb(220, 53, 69)'
                            ],
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'bottom',
                            },
                            title: {
                                display: true,
                                text: 'Entity Risk Distribution'
                            }
                        }
                    }
                });
            }
            
            // Initial load
            refreshMetrics();
            
            // Auto-refresh every 30 seconds
            setInterval(refreshMetrics, 30000);
        </script>
    </body>
    </html>
    """


@router.get("/metrics/summary")
async def get_metrics_summary():
    """메트릭 요약 조회"""
    try:
        summary = metrics_collector.get_metrics_summary()
        
        # Health status 추가
        from src.monitoring.health_check import health_checker
        health_status = await health_checker.get_health_status()
        summary['health'] = health_status
        
        return summary
        
    except Exception as e:
        logger.error(f"Error getting metrics summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/history")
async def get_metrics_history(
    metric: str = Query(..., description="Metric name"),
    hours: int = Query(1, ge=1, le=24, description="Hours of history")
):
    """메트릭 히스토리 조회"""
    try:
        history = metrics_collector.get_historical_metrics(metric, hours)
        
        return [
            {
                "timestamp": point.timestamp.isoformat(),
                "value": point.value,
                "labels": point.labels
            }
            for point in history
        ]
        
    except Exception as e:
        logger.error(f"Error getting metrics history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/system")
async def get_system_metrics():
    """시스템 메트릭 조회"""
    try:
        metrics = metrics_collector.get_system_metrics()
        return {
            "timestamp": metrics.timestamp.isoformat(),
            "cpu_usage": metrics.cpu_usage,
            "memory_usage": metrics.memory_usage,
            "disk_usage": metrics.disk_usage,
            "neo4j_connections": metrics.neo4j_connections,
            "active_transactions": metrics.active_transactions,
            "query_cache_hit_rate": metrics.query_cache_hit_rate
        }
        
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/graph")
async def get_graph_metrics():
    """그래프 메트릭 조회"""
    try:
        metrics = metrics_collector.get_graph_metrics()
        return {
            "timestamp": metrics.timestamp.isoformat(),
            "total_nodes": metrics.total_nodes,
            "total_relationships": metrics.total_relationships,
            "node_types": metrics.node_types,
            "relationship_types": metrics.relationship_types,
            "avg_node_degree": metrics.avg_node_degree,
            "graph_density": metrics.graph_density
        }
        
    except Exception as e:
        logger.error(f"Error getting graph metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/performance")
async def get_performance_metrics():
    """성능 메트릭 조회"""
    try:
        metrics = metrics_collector.get_performance_metrics()
        return {
            "timestamp": metrics.timestamp.isoformat(),
            "avg_query_time": metrics.avg_query_time,
            "p95_query_time": metrics.p95_query_time,
            "p99_query_time": metrics.p99_query_time,
            "queries_per_second": metrics.queries_per_second,
            "failed_queries": metrics.failed_queries,
            "cache_hit_rate": metrics.cache_hit_rate
        }
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/risk")
async def get_risk_metrics():
    """리스크 메트릭 조회"""
    try:
        metrics = metrics_collector.get_risk_metrics()
        return {
            "timestamp": metrics.timestamp.isoformat(),
            "avg_risk_score": metrics.avg_risk_score,
            "high_risk_entities": metrics.high_risk_entities,
            "risk_score_distribution": metrics.risk_score_distribution,
            "risk_trends": metrics.risk_trends
        }
        
    except Exception as e:
        logger.error(f"Error getting risk metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts")
async def get_active_alerts(
    severity: Optional[str] = Query(None, regex="^(LOW|MEDIUM|HIGH|CRITICAL)$")
):
    """활성 알림 조회"""
    try:
        # 여기서는 간단한 예시 알림을 반환
        # 실제로는 알림 시스템과 연동
        alerts = []
        
        # 예시 알림 생성
        metrics = metrics_collector.get_metrics_summary()
        
        # 고위험 엔티티가 많은 경우
        if metrics['risk']['high_risk_entities'] > 100:
            alerts.append({
                "id": "risk-001",
                "timestamp": datetime.now().isoformat(),
                "severity": "HIGH",
                "type": "RISK_THRESHOLD",
                "message": f"High risk entities count exceeded threshold: {metrics['risk']['high_risk_entities']}",
                "details": {
                    "threshold": 100,
                    "current": metrics['risk']['high_risk_entities']
                }
            })
        
        # 쿼리 성능 저하
        if metrics['performance']['avg_query_time'] > 100:
            alerts.append({
                "id": "perf-001",
                "timestamp": datetime.now().isoformat(),
                "severity": "MEDIUM",
                "type": "PERFORMANCE",
                "message": f"Average query time is high: {metrics['performance']['avg_query_time']:.2f}ms",
                "details": {
                    "threshold": 100,
                    "current": metrics['performance']['avg_query_time']
                }
            })
        
        # 필터링
        if severity:
            alerts = [a for a in alerts if a['severity'] == severity]
        
        return alerts
        
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/metrics/record")
async def record_custom_metric(
    metric_name: str,
    value: float,
    labels: Optional[Dict[str, str]] = None
):
    """커스텀 메트릭 기록"""
    try:
        from src.monitoring.metrics import MetricPoint
        
        metric_point = MetricPoint(
            timestamp=datetime.now(),
            value=value,
            labels=labels
        )
        
        metrics_collector._store_metric(metric_name, value, metric_point.timestamp)
        
        return {
            "status": "success",
            "metric": metric_name,
            "value": value,
            "timestamp": metric_point.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error recording custom metric: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 대시보드 라우터 export
def get_monitoring_router():
    """모니터링 라우터 반환"""
    return router