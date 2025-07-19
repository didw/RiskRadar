"""Graph Service Main Application"""
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import os
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from src.neo4j.driver import driver as neo4j_driver
from src.kafka.consumer import consumer as kafka_consumer
from src.models.schemas import (
    GraphStatsResponse, 
    GraphQueryRequest,
    NetworkRiskRequest,
    NetworkAnalysisResponse
)
from src.kafka.entity_cache import entity_cache
from src.graphql.server import get_graphql_router, GRAPHQL_PLAYGROUND_HTML
from src.queries.optimized import get_optimized_queries
from src.queries.performance_tuning import get_performance_tuner

# 로깅 설정
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # Startup
    logger.info("Starting Graph Service...")
    
    # Neo4j 연결 확인 (재시도 로직 포함)
    import time
    max_retries = 30
    retry_interval = 2
    
    for attempt in range(max_retries):
        try:
            neo4j_driver.driver.verify_connectivity()
            logger.info("Connected to Neo4j")
            break
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Neo4j connection attempt {attempt + 1}/{max_retries} failed: {e}. Retrying in {retry_interval}s...")
                time.sleep(retry_interval)
            else:
                logger.error(f"Failed to connect to Neo4j after {max_retries} attempts: {e}")
                raise e
    
    # Kafka Consumer 시작
    kafka_consumer.start()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Graph Service...")
    kafka_consumer.stop()
    neo4j_driver.close()

# FastAPI 앱 생성
app = FastAPI(
    title=os.getenv("API_TITLE", "RiskRadar Graph Service API"),
    version=os.getenv("API_VERSION", "1.0.0"),
    description="""
    ## RiskRadar Graph Service API
    
    Neo4j 기반 Risk Knowledge Graph 서비스입니다.
    
    ### 주요 기능
    - 🕸️ **그래프 데이터 관리**: 기업, 인물, 이벤트 간 복잡한 관계 저장
    - 📊 **리스크 분석**: 네트워크 기반 리스크 전파 및 영향도 분석
    - 🔍 **고급 쿼리**: GraphQL과 REST API를 통한 유연한 데이터 조회
    - ⚡ **고성능**: 최적화된 Cypher 쿼리와 캐싱으로 빠른 응답
    - 📈 **실시간 모니터링**: 시스템 성능 및 헬스 상태 모니터링
    
    ### Performance Goals
    - 1-hop 쿼리: < 50ms
    - 3-hop 경로 분석: < 200ms
    - 동시 처리: 100+ concurrent queries
    
    ### 관련 문서
    - [GraphQL Playground](/playground)
    - [Monitoring Dashboard](/monitoring/dashboard)
    - [Performance Metrics](/monitoring/metrics/summary)
    """,
    contact={
        "name": "Graph Squad",
        "email": "graph-team@riskradar.com"
    },
    license_info={
        "name": "RiskRadar License",
        "url": "https://riskradar.com/license"
    },
    servers=[
        {
            "url": "http://localhost:8003",
            "description": "Development server"
        },
        {
            "url": "https://api.riskradar.com/graph",
            "description": "Production server"
        }
    ],
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# GraphQL 라우터 추가
graphql_router = get_graphql_router()
app.include_router(graphql_router, prefix="/graphql")

# 모니터링 대시보드 라우터 추가
from src.monitoring.dashboard import get_monitoring_router
monitoring_router = get_monitoring_router()
app.include_router(monitoring_router)

@app.get("/playground", response_class=HTMLResponse)
async def graphql_playground():
    """GraphQL Playground 인터페이스"""
    return GRAPHQL_PLAYGROUND_HTML

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    from src.monitoring.health_check import health_checker, HealthStatus
    
    try:
        # 통합 헬스 체크 사용
        health_status = await health_checker.get_health_status()
        
        # 상태에 따른 HTTP 응답 코드 결정
        status = health_status.get("status", HealthStatus.UNKNOWN)
        
        if status == HealthStatus.CRITICAL:
            raise HTTPException(status_code=503, detail=health_status)
        elif status == HealthStatus.DEGRADED:
            # Degraded는 200을 반환하되 상태를 명시
            return health_status
        else:
            return health_status
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        error_response = {
            "status": HealthStatus.UNKNOWN,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        raise HTTPException(status_code=503, detail=error_response)

@app.get("/api/v1/graph/stats", response_model=GraphStatsResponse)
async def get_graph_stats():
    """그래프 통계 조회"""
    try:
        # 노드 수 조회
        node_query = """
        MATCH (n)
        RETURN labels(n)[0] as type, count(n) as count
        """
        node_results = neo4j_driver.execute_read(node_query)
        
        # 관계 수 조회
        rel_query = """
        MATCH ()-[r]->()
        RETURN type(r) as type, count(r) as count
        """
        rel_results = neo4j_driver.execute_read(rel_query)
        
        # 결과 집계
        node_types = {row['type']: row['count'] for row in node_results if row['type']}
        rel_types = {row['type']: row['count'] for row in rel_results}
        
        total_nodes = sum(node_types.values())
        total_rels = sum(rel_types.values())
        
        return GraphStatsResponse(
            node_count=total_nodes,
            relationship_count=total_rels,
            node_types=node_types,
            relationship_types=rel_types,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error getting graph stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/graph/query")
async def query_graph(request: GraphQueryRequest):
    """그래프 쿼리 실행"""
    try:
        query = """
        MATCH path = (n {id: $entity_id})-[*1..$depth]-()
        RETURN path
        LIMIT 100
        """
        
        results = neo4j_driver.execute_read(
            query,
            entity_id=request.entity_id,
            depth=request.depth
        )
        
        return {
            "entity_id": request.entity_id,
            "paths": len(results),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error querying graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/graph/network-risk", response_model=NetworkAnalysisResponse)
async def analyze_network_risk(request: NetworkRiskRequest):
    """네트워크 리스크 분석"""
    try:
        # 연결된 고위험 엔티티 찾기
        risk_query = """
        MATCH (c:Company {id: $company_id})
        MATCH path = (c)-[*1..$depth]-(connected)
        WHERE connected.risk_score >= $min_risk_score
        WITH c, connected, path
        RETURN 
            c.name as central_entity,
            count(DISTINCT connected) as connected_count,
            avg(connected.risk_score) as avg_risk,
            collect(DISTINCT {
                id: connected.id,
                name: connected.name,
                risk_score: connected.risk_score,
                type: labels(connected)[0]
            }) as high_risk_entities
        """
        
        results = neo4j_driver.execute_read(
            risk_query,
            company_id=request.company_id,
            depth=request.depth,
            min_risk_score=request.min_risk_score
        )
        
        if not results:
            raise HTTPException(status_code=404, detail="Company not found")
        
        result = results[0]
        
        return NetworkAnalysisResponse(
            central_entity=result['central_entity'],
            connected_entities=result['connected_count'],
            average_risk_score=result['avg_risk'] or 0.0,
            high_risk_entities=result['high_risk_entities'][:10],  # Top 10
            risk_paths=[],  # TODO: 경로 분석 추가
            analysis_timestamp=datetime.now()
        )
        
    except HTTPException:
        # HTTPException은 그대로 re-raise
        raise
    except Exception as e:
        logger.error(f"Error analyzing network risk: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/graph/companies/{company_id}")
async def get_company_details(company_id: str):
    """기업 상세 정보 조회"""
    try:
        # 입력 검증
        if not company_id or not company_id.strip():
            raise HTTPException(status_code=400, detail="Company ID is required")
        
        query = """
        MATCH (c:Company {id: $company_id})
        OPTIONAL MATCH (c)-[r:MENTIONED_IN]->(n:NewsArticle)
        WITH c, count(n) as news_count, avg(r.sentiment) as avg_sentiment
        OPTIONAL MATCH (c)-[:AFFECTS]-(e:Event)
        RETURN c as company, 
               news_count,
               avg_sentiment,
               count(e) as event_count
        """
        
        logger.info(f"Querying company details for ID: {company_id}")
        results = neo4j_driver.execute_read(query, company_id=company_id)
        
        if not results:
            logger.info(f"Company not found: {company_id}")
            raise HTTPException(status_code=404, detail=f"Company with ID '{company_id}' not found")
        
        logger.info(f"Successfully retrieved company details for ID: {company_id}")
        return results[0]
        
    except HTTPException:
        # HTTPException은 그대로 re-raise (404, 400 등)
        raise
    except Exception as e:
        logger.error(f"Error getting company details for ID '{company_id}': {e}")
        # Neo4j 연결 관련 오류인지 확인
        if "connection" in str(e).lower() or "timeout" in str(e).lower():
            raise HTTPException(status_code=503, detail="Database connection unavailable")
        else:
            raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/graph/cache/stats")
async def get_cache_stats():
    """엔티티 캐시 통계 조회"""
    try:
        return entity_cache.get_cache_stats()
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/graph/cache/refresh")
async def refresh_cache():
    """엔티티 캐시 수동 새로고침"""
    try:
        # 강제 새로고침
        entity_cache.get_companies(force_refresh=True)
        entity_cache.get_persons(force_refresh=True)
        
        stats = entity_cache.get_cache_stats()
        return {
            "message": "Cache refreshed successfully",
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error refreshing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Week 4: 최적화된 쿼리 API
@app.get("/api/v1/graph/optimized/company/{company_id}")
async def get_optimized_company_info(company_id: str):
    """최적화된 기업 정보 조회 (< 50ms 목표)"""
    try:
        optimized_queries = get_optimized_queries()
        company_info = optimized_queries.get_company_basic_info(company_id)
        
        if not company_info:
            raise HTTPException(status_code=404, detail=f"Company '{company_id}' not found")
        
        return {
            "company": company_info,
            "cached": True  # 캐시 여부는 실제로는 내부 로직에서 결정됨
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in optimized company query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/graph/optimized/company/{company_id}/connections")
async def get_optimized_company_connections(company_id: str, limit: int = 10):
    """최적화된 기업 연결 관계 조회 (< 50ms 목표)"""
    try:
        optimized_queries = get_optimized_queries()
        connections = optimized_queries.get_company_connections(company_id, limit)
        
        return {
            "company_id": company_id,
            "connections": connections,
            "total": len(connections)
        }
    except Exception as e:
        logger.error(f"Error in optimized connections query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/graph/optimized/company/{company_id}/risk-paths")
async def get_optimized_risk_paths(company_id: str, max_depth: int = 3):
    """최적화된 리스크 전파 경로 분석 (< 200ms 목표)"""
    try:
        optimized_queries = get_optimized_queries()
        risk_paths = optimized_queries.analyze_risk_propagation_paths(company_id, max_depth)
        
        return {
            "company_id": company_id,
            "risk_paths": risk_paths,
            "analysis_depth": max_depth,
            "total_paths": len(risk_paths)
        }
    except Exception as e:
        logger.error(f"Error in optimized risk paths query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/graph/optimized/company/{company_id}/network-risk")
async def get_optimized_network_risk(company_id: str):
    """최적화된 네트워크 리스크 요약 (< 100ms 목표)"""
    try:
        optimized_queries = get_optimized_queries()
        network_risk = optimized_queries.calculate_network_risk_summary(company_id)
        
        if not network_risk:
            raise HTTPException(status_code=404, detail=f"Company '{company_id}' not found")
        
        return network_risk
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in optimized network risk query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/graph/optimized/sectors/risk-distribution")
async def get_optimized_sector_risk_distribution(limit: int = 20):
    """최적화된 섹터별 리스크 분포 (< 150ms 목표)"""
    try:
        optimized_queries = get_optimized_queries()
        distribution = optimized_queries.get_sector_risk_distribution(limit)
        
        return {
            "sectors": distribution,
            "total_sectors": len(distribution),
            "analysis_timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in sector risk distribution query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/graph/optimized/events/recent")
async def get_optimized_recent_events(
    company_id: Optional[str] = None, 
    days: int = 30, 
    limit: int = 50
):
    """최적화된 최근 리스크 이벤트 조회 (< 100ms 목표)"""
    try:
        optimized_queries = get_optimized_queries()
        events = optimized_queries.get_recent_risk_events(company_id, days, limit)
        
        return {
            "events": events,
            "filters": {
                "company_id": company_id,
                "days": days,
                "limit": limit
            },
            "total_events": len(events)
        }
    except Exception as e:
        logger.error(f"Error in recent events query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Week 4: 성능 튜닝 API
@app.get("/api/v1/graph/performance/stats")
async def get_performance_stats():
    """쿼리 성능 통계 조회"""
    try:
        optimized_queries = get_optimized_queries()
        performance_tuner = get_performance_tuner()
        
        return {
            "optimized_queries": optimized_queries.get_performance_stats(),
            "query_analysis": performance_tuner.get_query_performance_summary(),
            "slow_queries": performance_tuner.get_slow_queries(10)
        }
    except Exception as e:
        logger.error(f"Error getting performance stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/graph/performance/indexes")
async def get_index_status():
    """인덱스 상태 및 분석"""
    try:
        performance_tuner = get_performance_tuner()
        index_analysis = performance_tuner.analyze_index_usage()
        
        return index_analysis
    except Exception as e:
        logger.error(f"Error getting index status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/graph/performance/indexes/create")
async def create_performance_indexes():
    """성능 최적화 인덱스 생성"""
    try:
        performance_tuner = get_performance_tuner()
        results = performance_tuner.create_performance_indexes()
        
        return {
            "message": "Performance indexes creation completed",
            "results": results,
            "success_count": sum(1 for success in results.values() if success),
            "total_count": len(results)
        }
    except Exception as e:
        logger.error(f"Error creating performance indexes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/graph/performance/diagnostics")
async def run_performance_diagnostics():
    """성능 진단 실행"""
    try:
        performance_tuner = get_performance_tuner()
        diagnostics = performance_tuner.run_performance_diagnostics()
        
        return diagnostics
    except Exception as e:
        logger.error(f"Error running performance diagnostics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/graph/performance/cache/warmup")
async def warmup_query_cache(company_ids: List[str]):
    """쿼리 캐시 워밍업"""
    try:
        optimized_queries = get_optimized_queries()
        optimized_queries.warm_up_cache(company_ids)
        
        return {
            "message": "Cache warmup completed",
            "warmed_companies": len(company_ids),
            "cache_stats": optimized_queries.get_performance_stats()
        }
    except Exception as e:
        logger.error(f"Error warming up cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/graph/performance/query/analyze")
async def analyze_query_performance(
    query: str,
    parameters: Optional[Dict[str, Any]] = None
):
    """쿼리 성능 분석"""
    try:
        performance_tuner = get_performance_tuner()
        
        # 쿼리 플랜 분석
        query_plan = performance_tuner.analyze_query_plan(query, parameters or {})
        
        # 최적화 제안
        optimization = performance_tuner.optimize_query(query)
        
        return {
            "query_plan": {
                "execution_time_ms": query_plan.execution_time_ms,
                "db_hits": query_plan.db_hits,
                "actual_rows": query_plan.actual_rows,
                "index_usage": query_plan.index_usage
            },
            "optimization": optimization,
            "performance_classification": (
                "excellent" if query_plan.execution_time_ms < 50 else
                "good" if query_plan.execution_time_ms < 200 else
                "needs_optimization"
            )
        }
    except Exception as e:
        logger.error(f"Error analyzing query performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("SERVICE_PORT", "8003"))
    uvicorn.run(app, host="0.0.0.0", port=port)