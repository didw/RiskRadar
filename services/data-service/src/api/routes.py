from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, List
import logging
from datetime import datetime, timedelta
import asyncio

from .models import (
    CrawlerStatusResponse, CrawlerInfo, CrawlerStatus,
    CrawlRequest, CrawlResponse,
    CollectionStatsRequest, CollectionStatsResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1")

# 크롤러 상태 관리 (메모리 기반)
crawler_stats = {
    "chosun": {
        "id": "chosun",
        "source": "조선일보",
        "status": CrawlerStatus.STOPPED,
        "last_crawl": None,
        "items_collected": 0,
        "error_count": 0
    },
    "hankyung": {
        "id": "hankyung", 
        "source": "한국경제",
        "status": CrawlerStatus.STOPPED,
        "last_crawl": None,
        "items_collected": 0,
        "error_count": 0
    },
    "joongang": {
        "id": "joongang",
        "source": "중앙일보", 
        "status": CrawlerStatus.STOPPED,
        "last_crawl": None,
        "items_collected": 0,
        "error_count": 0
    },
    "yonhap": {
        "id": "yonhap",
        "source": "연합뉴스",
        "status": CrawlerStatus.STOPPED,
        "last_crawl": None,
        "items_collected": 0,
        "error_count": 0
    },
    "mk": {
        "id": "mk",
        "source": "매일경제",
        "status": CrawlerStatus.STOPPED,
        "last_crawl": None,
        "items_collected": 0,
        "error_count": 0
    }
}

# 수집 통계 (메모리 기반)
collection_stats = {
    "total_items": 0,
    "by_source": {},
    "by_hour": [],
    "duplicate_rate": 0.0
}


@router.get("/crawler/status", response_model=CrawlerStatusResponse)
async def get_crawler_status():
    """크롤러 상태 조회"""
    try:
        crawlers = [CrawlerInfo(**stats) for stats in crawler_stats.values()]
        return CrawlerStatusResponse(crawlers=crawlers)
    except Exception as e:
        logger.error(f"Error getting crawler status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/crawl", response_model=CrawlResponse)
async def trigger_crawl(request: CrawlRequest, background_tasks: BackgroundTasks):
    """수동 크롤링 트리거"""
    try:
        # 크롤링 대상 결정
        sources_to_crawl = []
        if request.source:
            if request.source not in crawler_stats:
                raise HTTPException(status_code=400, detail=f"Unknown source: {request.source}")
            sources_to_crawl = [request.source]
        else:
            sources_to_crawl = list(crawler_stats.keys())
        
        # 백그라운드에서 크롤링 실행
        background_tasks.add_task(execute_crawling, sources_to_crawl, request.limit)
        
        # 크롤러 상태를 RUNNING으로 변경
        for source in sources_to_crawl:
            crawler_stats[source]["status"] = CrawlerStatus.RUNNING
        
        return CrawlResponse(
            status="started",
            message=f"Crawling started for {len(sources_to_crawl)} sources",
            crawled_count=0,
            errors=[],
            data=[]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering crawl: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/collection", response_model=CollectionStatsResponse)
async def get_collection_stats(
    from_time: datetime = None,
    to_time: datetime = None
):
    """수집 통계 조회"""
    try:
        # 기본값 설정 (최근 24시간)
        if not to_time:
            to_time = datetime.now()
        if not from_time:
            from_time = to_time - timedelta(hours=24)
        
        # 현재는 메모리 기반 통계 반환
        # 실제 구현에서는 데이터베이스에서 조회
        stats = CollectionStatsResponse(
            total_items=collection_stats["total_items"],
            by_source=collection_stats["by_source"].copy(),
            by_hour=collection_stats["by_hour"].copy(),
            duplicate_rate=collection_stats["duplicate_rate"],
            time_range={
                "from": from_time,
                "to": to_time
            }
        )
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting collection stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def execute_crawling(sources: List[str], limit: int = 10):
    """실제 크롤링 실행 (백그라운드 태스크) - 배치 처리 적용"""
    from ..crawlers.news import (
        ChosunCrawler, HankyungCrawler, JoongangCrawler, 
        YonhapCrawler, MKCrawler
    )
    from ..kafka.producer import get_producer
    from ..processors.batch_processor import get_batch_processor
    
    crawler_map = {
        "chosun": ChosunCrawler,
        "hankyung": HankyungCrawler,
        "joongang": JoongangCrawler,
        "yonhap": YonhapCrawler,
        "mk": MKCrawler
    }
    
    # 서비스 인스턴스 가져오기
    producer = get_producer()
    batch_processor = get_batch_processor()
    
    # 배치 처리 함수 정의
    async def process_article_batch(batch_data: Dict[str, any]) -> Dict[str, any]:
        """단일 기사 처리 함수"""
        url = batch_data['url']
        source = batch_data['source']
        crawler_class = batch_data['crawler_class']
        
        try:
            async with crawler_class() as crawler:
                # 기사 크롤링
                html = await crawler.fetch_page(url)
                article = await crawler.parse_article(url, html)
                
                # 정규화
                normalized_article = crawler.normalize_article(article)
                
                # 중복 제거 확인
                from ..processors.deduplicator import get_deduplicator
                deduplicator = get_deduplicator()
                dup_result = deduplicator.is_duplicate(normalized_article)
                
                if dup_result.is_duplicate:
                    return {
                        'status': 'duplicate',
                        'reason': dup_result.reason,
                        'duplicate_type': dup_result.duplicate_type
                    }
                
                # Kafka 메시지로 변환 및 전송
                kafka_message = crawler.to_kafka_message(normalized_article)
                success = producer.send_message(kafka_message)
                
                if success:
                    # 통계 업데이트
                    crawler_stats[source]["items_collected"] += 1
                    collection_stats["total_items"] += 1
                    
                    if source not in collection_stats["by_source"]:
                        collection_stats["by_source"][source] = 0
                    collection_stats["by_source"][source] += 1
                    
                    return {
                        'status': 'success',
                        'article_id': normalized_article['id'],
                        'title': normalized_article['title']
                    }
                else:
                    return {
                        'status': 'kafka_failed',
                        'reason': 'Failed to send to Kafka'
                    }
                    
        except Exception as e:
            crawler_stats[source]["error_count"] += 1
            return {
                'status': 'error',
                'reason': str(e)
            }
    
    # 배치 처리 시작 (아직 시작되지 않았다면)
    if not batch_processor.get_queue_status()['is_running']:
        batch_processor.start(process_article_batch)
    
    for source in sources:
        try:
            logger.info(f"Starting batch crawl for {source}")
            crawler_stats[source]["status"] = CrawlerStatus.RUNNING
            crawler_stats[source]["last_crawl"] = datetime.now()
            
            # 크롤러 생성
            crawler_class = crawler_map.get(source)
            if not crawler_class:
                logger.error(f"No crawler found for source: {source}")
                crawler_stats[source]["status"] = CrawlerStatus.ERROR
                crawler_stats[source]["error_count"] += 1
                continue
            
            # 기사 URL 목록 가져오기 (개별 크롤러로 한 번만)
            async with crawler_class() as crawler:
                article_urls = await crawler.fetch_article_list()
                
                # 제한 적용
                if limit:
                    article_urls = article_urls[:limit]
                
                logger.info(f"Found {len(article_urls)} URLs for {source}")
                
                # 배치 처리를 위해 URL들을 큐에 추가
                batch_items = []
                for url in article_urls:
                    batch_data = {
                        'url': url,
                        'source': source,
                        'crawler_class': crawler_class
                    }
                    batch_items.append(batch_data)
                
                # 배치 단위로 큐에 추가 (100건씩)
                batch_size = 100
                for i in range(0, len(batch_items), batch_size):
                    batch_chunk = batch_items[i:i + batch_size]
                    
                    # 우선순위 설정 (소스별로 다르게 설정 가능)
                    priority = {
                        "yonhap": 3,    # 연합뉴스 최우선
                        "chosun": 2,    # 조선일보 높음
                        "hankyung": 2,  # 한국경제 높음
                        "joongang": 1,  # 중앙일보 보통
                        "mk": 1         # 매일경제 보통
                    }.get(source, 0)
                    
                    item_ids = batch_processor.add_items(batch_chunk, priority)
                    logger.info(f"Added {len(item_ids)} items to batch queue for {source}")
                
                # 배치 처리 완료 대기 (비동기적으로)
                await asyncio.sleep(1)  # 배치 처리가 시작될 시간 확보
                
                logger.info(f"Queued {len(batch_items)} articles for batch processing from {source}")
                
                # 성공적으로 큐에 추가됨
                crawler_stats[source]["status"] = CrawlerStatus.STOPPED
                
        except Exception as e:
            logger.error(f"Error in batch crawler {source}: {e}")
            crawler_stats[source]["status"] = CrawlerStatus.ERROR
            crawler_stats[source]["error_count"] += 1


@router.get("/crawler/{source_id}/status")
async def get_specific_crawler_status(source_id: str):
    """특정 크롤러 상태 조회"""
    if source_id not in crawler_stats:
        raise HTTPException(status_code=404, detail=f"Crawler {source_id} not found")
    
    return CrawlerInfo(**crawler_stats[source_id])


@router.post("/crawler/{source_id}/start")
async def start_crawler(source_id: str, background_tasks: BackgroundTasks):
    """특정 크롤러 시작"""
    if source_id not in crawler_stats:
        raise HTTPException(status_code=404, detail=f"Crawler {source_id} not found")
    
    if crawler_stats[source_id]["status"] == CrawlerStatus.RUNNING:
        raise HTTPException(status_code=400, detail=f"Crawler {source_id} is already running")
    
    # 백그라운드에서 크롤링 실행
    background_tasks.add_task(execute_crawling, [source_id], 10)
    
    return {"status": "started", "source": source_id}


@router.post("/crawler/{source_id}/stop")
async def stop_crawler(source_id: str):
    """특정 크롤러 중지"""
    if source_id not in crawler_stats:
        raise HTTPException(status_code=404, detail=f"Crawler {source_id} not found")
    
    crawler_stats[source_id]["status"] = CrawlerStatus.STOPPED
    
    return {"status": "stopped", "source": source_id}


@router.get("/kafka/stats")
async def get_kafka_stats():
    """Kafka Producer 통계 조회"""
    try:
        from ..kafka.producer import get_producer
        producer = get_producer()
        return producer.get_stats()
    except Exception as e:
        logger.error(f"Error getting Kafka stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kafka/health")
async def get_kafka_health():
    """Kafka 연결 상태 확인"""
    try:
        from ..kafka.producer import get_producer
        producer = get_producer()
        return producer.health_check()
    except Exception as e:
        logger.error(f"Error checking Kafka health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deduplication/stats")
async def get_deduplication_stats():
    """중복 제거 통계 조회"""
    try:
        from ..processors.deduplicator import get_deduplicator
        deduplicator = get_deduplicator()
        return deduplicator.get_stats()
    except Exception as e:
        logger.error(f"Error getting deduplication stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deduplication/health")
async def get_deduplication_health():
    """중복 제거 시스템 상태 확인"""
    try:
        from ..processors.deduplicator import get_deduplicator
        deduplicator = get_deduplicator()
        return deduplicator.health_check()
    except Exception as e:
        logger.error(f"Error checking deduplication health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/batch/stats")
async def get_batch_stats():
    """배치 처리 통계 조회"""
    try:
        from ..processors.batch_processor import get_batch_processor
        batch_processor = get_batch_processor()
        return batch_processor.get_stats()
    except Exception as e:
        logger.error(f"Error getting batch stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/batch/queue")
async def get_batch_queue_status():
    """배치 처리 큐 상태 조회"""
    try:
        from ..processors.batch_processor import get_batch_processor
        batch_processor = get_batch_processor()
        return batch_processor.get_queue_status()
    except Exception as e:
        logger.error(f"Error getting batch queue status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/batch/recent")
async def get_recent_batches(limit: int = 10):
    """최근 배치 처리 결과 조회"""
    try:
        from ..processors.batch_processor import get_batch_processor
        batch_processor = get_batch_processor()
        return {
            "recent_batches": batch_processor.get_recent_batches(limit),
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Error getting recent batches: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/retry/stats")
async def get_retry_stats():
    """재시도 메커니즘 통계 조회"""
    try:
        from ..processors.retry_manager import get_retry_manager
        retry_manager = get_retry_manager()
        return retry_manager.get_stats()
    except Exception as e:
        logger.error(f"Error getting retry stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/retry/circuit-breaker/{operation_key}")
async def get_circuit_breaker_status(operation_key: str):
    """특정 작업의 Circuit Breaker 상태 조회"""
    try:
        from ..processors.retry_manager import get_retry_manager
        retry_manager = get_retry_manager()
        status = retry_manager.get_circuit_breaker_status(operation_key)
        
        if status is None:
            raise HTTPException(
                status_code=404, 
                detail=f"Circuit breaker not found for operation: {operation_key}"
            )
        
        return {
            "operation_key": operation_key,
            "circuit_breaker": status
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting circuit breaker status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retry/reset-stats")
async def reset_retry_stats():
    """재시도 통계 초기화"""
    try:
        from ..processors.retry_manager import get_retry_manager
        retry_manager = get_retry_manager()
        retry_manager.reset_stats()
        return {"message": "Retry statistics reset successfully"}
    except Exception as e:
        logger.error(f"Error resetting retry stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))