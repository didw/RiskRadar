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
    """실제 크롤링 실행 (백그라운드 태스크)"""
    from ..crawlers.news import (
        ChosunCrawler, HankyungCrawler, JoongangCrawler, 
        YonhapCrawler, MKCrawler
    )
    
    crawler_map = {
        "chosun": ChosunCrawler,
        "hankyung": HankyungCrawler,
        "joongang": JoongangCrawler,
        "yonhap": YonhapCrawler,
        "mk": MKCrawler
    }
    
    for source in sources:
        try:
            logger.info(f"Starting crawl for {source}")
            crawler_stats[source]["status"] = CrawlerStatus.RUNNING
            crawler_stats[source]["last_crawl"] = datetime.now()
            
            # 크롤러 생성 및 실행
            crawler_class = crawler_map.get(source)
            if not crawler_class:
                logger.error(f"No crawler found for source: {source}")
                crawler_stats[source]["status"] = CrawlerStatus.ERROR
                crawler_stats[source]["error_count"] += 1
                continue
            
            async with crawler_class() as crawler:
                # 기사 목록 가져오기
                article_urls = await crawler.fetch_article_list()
                
                # 제한 적용
                if limit:
                    article_urls = article_urls[:limit]
                
                crawled_articles = []
                
                # 각 기사 크롤링
                for url in article_urls:
                    try:
                        html = await crawler.fetch_page(url)
                        article = await crawler.parse_article(url, html)
                        crawled_articles.append(article)
                        
                        # 통계 업데이트
                        crawler_stats[source]["items_collected"] += 1
                        collection_stats["total_items"] += 1
                        
                        if source not in collection_stats["by_source"]:
                            collection_stats["by_source"][source] = 0
                        collection_stats["by_source"][source] += 1
                        
                    except Exception as e:
                        logger.error(f"Error crawling article {url}: {e}")
                        crawler_stats[source]["error_count"] += 1
                
                logger.info(f"Crawled {len(crawled_articles)} articles from {source}")
                
                # 성공적으로 완료
                crawler_stats[source]["status"] = CrawlerStatus.STOPPED
                
        except Exception as e:
            logger.error(f"Error in crawler {source}: {e}")
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