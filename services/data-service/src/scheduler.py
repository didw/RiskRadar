"""
고성능 크롤링 스케줄러
- 처리량 1,000건/시간 달성
- 발행 후 5분 내 수집
- 동시성 최적화
- 실시간 모니터링
"""
import asyncio
import logging
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import time
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor
import heapq
import os

from .crawlers.news import (
    ChosunCrawler, HankyungCrawler, JoongangCrawler,
    YonhapCrawler, MKCrawler
)
from .crawlers.news.bbc_crawler import BBCCrawler
from .crawlers.news.guardian_crawler import GuardianCrawler
from .kafka.producer import get_producer
from .processors.batch_processor import get_batch_processor
from .processors.deduplicator import get_deduplicator
from .metrics import get_metrics_collector, track_crawl_metrics

logger = logging.getLogger(__name__)


class SourcePriority(Enum):
    """뉴스 소스 우선순위"""
    URGENT = 1    # 연합뉴스 등 속보성 매체
    HIGH = 2      # 주요 일간지
    NORMAL = 3    # 일반 매체
    LOW = 4       # 낮은 우선순위


@dataclass
class CrawlTask:
    """크롤링 태스크"""
    source_id: str
    priority: int
    scheduled_at: datetime
    interval_seconds: int
    last_run: Optional[datetime] = None
    last_success: Optional[datetime] = None
    consecutive_failures: int = 0
    is_running: bool = False
    
    def __lt__(self, other):
        """우선순위 큐 정렬을 위한 비교"""
        # 예정 시간이 빠른 것 우선
        if self.scheduled_at != other.scheduled_at:
            return self.scheduled_at < other.scheduled_at
        # 우선순위가 높은 것 우선 (숫자가 작을수록 높음)
        return self.priority < other.priority


@dataclass
class SchedulerConfig:
    """스케줄러 설정"""
    # 동시성 제어
    max_concurrent_crawlers: int = 5
    max_concurrent_articles: int = 20
    
    # 성능 목표
    target_throughput: int = 1000  # 시간당 처리 목표
    max_latency_seconds: int = 300  # 5분
    
    # 크롤링 간격 (초)
    crawl_intervals: Dict[str, int] = field(default_factory=lambda: {
        "yonhap": 60,      # 1분 (속보)
        "chosun": 180,     # 3분
        "hankyung": 180,   # 3분
        "joongang": 300,   # 5분
        "mk": 300,         # 5분
        "bbc": 360,        # 6분 (RSS)
        "guardian": 300    # 5분 (RSS)
    })
    
    # 소스별 우선순위
    source_priorities: Dict[str, SourcePriority] = field(default_factory=lambda: {
        "yonhap": SourcePriority.URGENT,
        "chosun": SourcePriority.HIGH,
        "hankyung": SourcePriority.HIGH,
        "joongang": SourcePriority.NORMAL,
        "mk": SourcePriority.NORMAL,
        "bbc": SourcePriority.HIGH,        # 국제 뉴스 우선순위
        "guardian": SourcePriority.HIGH    # 국제 뉴스 우선순위
    })
    
    # 재시도 설정
    max_consecutive_failures: int = 3
    failure_backoff_factor: float = 2.0
    
    @classmethod
    def from_env(cls) -> 'SchedulerConfig':
        """환경변수에서 설정 로드"""
        config = cls()
        
        # 동시성 설정
        config.max_concurrent_crawlers = int(
            os.getenv("SCHEDULER_MAX_CRAWLERS", "5")
        )
        config.max_concurrent_articles = int(
            os.getenv("SCHEDULER_MAX_ARTICLES", "20")
        )
        
        # 성능 목표
        config.target_throughput = int(
            os.getenv("SCHEDULER_TARGET_THROUGHPUT", "1000")
        )
        
        return config


class HighPerformanceScheduler:
    """고성능 크롤링 스케줄러"""
    
    def __init__(self, config: Optional[SchedulerConfig] = None):
        self.config = config or SchedulerConfig.from_env()
        
        # 크롤러 맵
        self.crawler_classes = {
            "chosun": ChosunCrawler,
            "hankyung": HankyungCrawler,
            "joongang": JoongangCrawler,
            "yonhap": YonhapCrawler,
            "mk": MKCrawler,
            "bbc": BBCCrawler,
            "guardian": GuardianCrawler
        }
        
        # 태스크 관리
        self.task_queue: List[CrawlTask] = []  # 우선순위 큐
        self.tasks_by_source: Dict[str, CrawlTask] = {}
        self.running_tasks: Set[str] = set()
        self._lock = threading.Lock()
        
        # 실행 상태
        self._running = False
        self._scheduler_task = None
        self._executor = ThreadPoolExecutor(
            max_workers=self.config.max_concurrent_crawlers,
            thread_name_prefix="crawler"
        )
        
        # 통계
        self._stats = {
            "total_crawls": 0,
            "successful_crawls": 0,
            "failed_crawls": 0,
            "total_articles": 0,
            "articles_per_source": {},
            "average_latency": 0.0,
            "throughput_per_hour": 0.0,
            "start_time": None,
            "last_reset": datetime.now()
        }
        
        # 서비스 인스턴스
        self.producer = get_producer()
        self.batch_processor = get_batch_processor()
        self.deduplicator = get_deduplicator()
        
        # 메트릭 수집기
        self.metrics_collector = get_metrics_collector()
        
        # 태스크 초기화
        self._initialize_tasks()
    
    def _initialize_tasks(self):
        """크롤링 태스크 초기화"""
        now = datetime.now()
        
        for source_id in self.crawler_classes.keys():
            interval = self.config.crawl_intervals.get(source_id, 300)
            priority = self.config.source_priorities.get(
                source_id, SourcePriority.NORMAL
            ).value
            
            task = CrawlTask(
                source_id=source_id,
                priority=priority,
                scheduled_at=now,
                interval_seconds=interval
            )
            
            self.tasks_by_source[source_id] = task
            heapq.heappush(self.task_queue, task)
            
            logger.info(
                f"Initialized task for {source_id}: "
                f"interval={interval}s, priority={priority}"
            )
    
    def _get_next_task(self) -> Optional[CrawlTask]:
        """다음 실행할 태스크 가져오기"""
        with self._lock:
            now = datetime.now()
            
            # 실행 가능한 태스크 찾기
            while self.task_queue:
                task = self.task_queue[0]
                
                # 이미 실행 중이면 스킵
                if task.is_running:
                    heapq.heappop(self.task_queue)
                    continue
                
                # 예정 시간이 되지 않았으면 대기
                if task.scheduled_at > now:
                    return None
                
                # 동시 실행 제한 확인
                if len(self.running_tasks) >= self.config.max_concurrent_crawlers:
                    return None
                
                # 태스크 실행 준비
                heapq.heappop(self.task_queue)
                task.is_running = True
                self.running_tasks.add(task.source_id)
                
                # 활성 크롤러 수 메트릭 업데이트
                self.metrics_collector.update_active_crawlers(len(self.running_tasks))
                
                return task
            
            return None
    
    def _reschedule_task(self, task: CrawlTask, success: bool):
        """태스크 재스케줄링"""
        with self._lock:
            now = datetime.now()
            task.is_running = False
            self.running_tasks.discard(task.source_id)
            
            # 활성 크롤러 수 메트릭 업데이트
            self.metrics_collector.update_active_crawlers(len(self.running_tasks))
            
            if success:
                task.last_success = now
                task.consecutive_failures = 0
                # 정상 간격으로 재스케줄
                task.scheduled_at = now + timedelta(seconds=task.interval_seconds)
            else:
                task.consecutive_failures += 1
                
                # 실패 시 백오프 적용
                if task.consecutive_failures >= self.config.max_consecutive_failures:
                    # 최대 실패 횟수 도달 - 더 긴 간격으로
                    backoff = task.interval_seconds * 10
                else:
                    # 지수 백오프
                    backoff = task.interval_seconds * (
                        self.config.failure_backoff_factor ** task.consecutive_failures
                    )
                
                task.scheduled_at = now + timedelta(seconds=backoff)
                
                logger.warning(
                    f"Task {task.source_id} failed {task.consecutive_failures} times, "
                    f"rescheduled for {task.scheduled_at}"
                )
                
                # 연속 실패 횟수 메트릭 업데이트
                self.metrics_collector.update_consecutive_failures(
                    task.source_id, task.consecutive_failures
                )
            
            # 우선순위 큐에 다시 추가
            heapq.heappush(self.task_queue, task)
    
    async def _execute_crawl(self, task: CrawlTask) -> bool:
        """크롤링 실행"""
        source_id = task.source_id
        crawler_class = self.crawler_classes.get(source_id)
        
        if not crawler_class:
            logger.error(f"No crawler found for {source_id}")
            return False
        
        start_time = time.time()
        
        try:
            logger.info(f"Starting crawl for {source_id}")
            self._stats["total_crawls"] += 1
            
            # 크롤링 시작 메트릭
            self.metrics_collector.record_crawl_request(source_id, True)
            
            async with crawler_class() as crawler:
                # 기사 목록 가져오기
                article_urls = await crawler.fetch_article_list()
                
                # 동시 처리를 위한 세마포어
                semaphore = asyncio.Semaphore(self.config.max_concurrent_articles)
                
                async def process_article(url: str) -> Optional[Dict[str, Any]]:
                    """개별 기사 처리"""
                    async with semaphore:
                        try:
                            html = await crawler.fetch_page(url)
                            article = await crawler.parse_article(url, html)
                            normalized = crawler.normalize_article(article)
                            
                            # 중복 확인
                            dup_result = self.deduplicator.is_duplicate(normalized)
                            if dup_result.is_duplicate:
                                # 중복 메트릭 기록
                                self.metrics_collector.record_article_processed(source_id, 'duplicate')
                                return None
                            
                            # Kafka 메시지 생성 및 전송
                            kafka_message = crawler.to_kafka_message(normalized)
                            success = self.producer.send_message(kafka_message)
                            
                            if success:
                                # 성공 메트릭 기록
                                self.metrics_collector.record_article_processed(source_id, 'processed')
                                self.metrics_collector.record_kafka_message('raw-news', True)
                            else:
                                self.metrics_collector.record_kafka_message('raw-news', False)
                            
                            return normalized
                            
                        except Exception as e:
                            logger.error(f"Error processing article {url}: {e}")
                            # 에러 메트릭 기록
                            error_type = self.metrics_collector.get_error_type_from_exception(e)
                            self.metrics_collector.record_crawl_error(source_id, error_type)
                            self.metrics_collector.record_article_processed(source_id, 'error')
                            return None
                
                # 병렬 처리
                tasks = [process_article(url) for url in article_urls]
                results = await asyncio.gather(*tasks)
                
                # 성공한 기사 수 계산
                successful_articles = [r for r in results if r is not None]
                article_count = len(successful_articles)
                
                # 통계 업데이트
                self._stats["successful_crawls"] += 1
                self._stats["total_articles"] += article_count
                
                if source_id not in self._stats["articles_per_source"]:
                    self._stats["articles_per_source"][source_id] = 0
                self._stats["articles_per_source"][source_id] += article_count
                
                # 지연시간 계산 (가장 최신 기사 기준)
                if successful_articles:
                    latest_article = max(
                        successful_articles,
                        key=lambda x: x.get('published_at', '')
                    )
                    
                    try:
                        published_at = datetime.fromisoformat(
                            latest_article['published_at'].replace('Z', '+00:00')
                        )
                        crawled_at = datetime.fromisoformat(
                            latest_article['crawled_at'].replace('Z', '+00:00')
                        )
                        latency = (crawled_at - published_at).total_seconds()
                        
                        # 평균 지연시간 업데이트
                        total_crawls = self._stats["successful_crawls"]
                        self._stats["average_latency"] = (
                            (self._stats["average_latency"] * (total_crawls - 1) + latency) /
                            total_crawls
                        )
                    except Exception as e:
                        logger.debug(f"Error calculating latency: {e}")
                
                processing_time = time.time() - start_time
                logger.info(
                    f"Completed crawl for {source_id}: "
                    f"{article_count} articles in {processing_time:.2f}s"
                )
                
                # 크롤링 소요 시간 메트릭 기록
                self.metrics_collector.record_crawl_duration(source_id, processing_time)
                
                return True
                
        except Exception as e:
            logger.error(f"Error in crawler {source_id}: {e}")
            self._stats["failed_crawls"] += 1
            
            # 에러 메트릭 기록
            error_type = self.metrics_collector.get_error_type_from_exception(e)
            self.metrics_collector.record_crawl_error(source_id, error_type)
            self.metrics_collector.record_crawl_request(source_id, False)
            
            return False
    
    async def _scheduler_loop(self):
        """스케줄러 메인 루프"""
        logger.info("Scheduler started")
        self._stats["start_time"] = datetime.now()
        
        while self._running:
            try:
                # 다음 태스크 가져오기
                task = self._get_next_task()
                
                if task:
                    # 비동기로 크롤링 실행
                    asyncio.create_task(self._run_task(task))
                else:
                    # 대기
                    await asyncio.sleep(0.5)
                
                # 처리량 계산 (1분마다)
                now = datetime.now()
                if (now - self._stats["last_reset"]).total_seconds() >= 60:
                    self._update_throughput()
                    self._stats["last_reset"] = now
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(1)
    
    async def _run_task(self, task: CrawlTask):
        """태스크 실행 래퍼"""
        try:
            success = await self._execute_crawl(task)
        except Exception as e:
            logger.error(f"Unexpected error in task {task.source_id}: {e}")
            success = False
        finally:
            self._reschedule_task(task, success)
    
    def _update_throughput(self):
        """처리량 계산 및 업데이트"""
        if self._stats["start_time"]:
            elapsed_hours = (
                datetime.now() - self._stats["start_time"]
            ).total_seconds() / 3600
            
            if elapsed_hours > 0:
                self._stats["throughput_per_hour"] = (
                    self._stats["total_articles"] / elapsed_hours
                )
                
                # 처리량 메트릭 업데이트
                self.metrics_collector.update_throughput(self._stats["throughput_per_hour"])
                
                # 평균 지연시간 메트릭 업데이트
                self.metrics_collector.update_latency(self._stats["average_latency"])
                
                # 배치 큐 크기 메트릭 업데이트
                queue_status = self.batch_processor.get_queue_status()
                self.metrics_collector.update_batch_queue_size(queue_status.get('queue_size', 0))
                
                # 중복 제거율 업데이트
                self.metrics_collector.update_deduplication_rate('1h')
                
                logger.info(
                    f"Current throughput: "
                    f"{self._stats['throughput_per_hour']:.1f} articles/hour"
                )
                
                # 목표 달성 여부 확인
                if self._stats["throughput_per_hour"] >= self.config.target_throughput:
                    logger.info(
                        f"✅ Target throughput achieved: "
                        f"{self._stats['throughput_per_hour']:.1f} >= "
                        f"{self.config.target_throughput}"
                    )
    
    def start(self):
        """스케줄러 시작"""
        if self._running:
            logger.warning("Scheduler already running")
            return
        
        self._running = True
        
        # 배치 프로세서 시작
        if not self.batch_processor.get_queue_status()['is_running']:
            logger.info("Starting batch processor")
            # 배치 프로세서는 별도로 시작됨
        
        # 스케줄러 루프 시작
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        
        logger.info("High-performance scheduler started")
    
    def stop(self):
        """스케줄러 중지"""
        logger.info("Stopping scheduler...")
        self._running = False
        
        if self._scheduler_task:
            self._scheduler_task.cancel()
        
        # 실행 중인 태스크 대기
        with self._lock:
            if self.running_tasks:
                logger.info(f"Waiting for {len(self.running_tasks)} tasks to complete")
        
        # Executor 종료
        self._executor.shutdown(wait=True)
        
        logger.info("Scheduler stopped")
    
    def get_stats(self) -> Dict[str, Any]:
        """통계 정보 반환"""
        with self._lock:
            stats = self._stats.copy()
            
            # 실행 중인 태스크 정보
            stats["running_tasks"] = list(self.running_tasks)
            stats["scheduled_tasks"] = len(self.task_queue)
            
            # 성능 지표
            if stats["start_time"]:
                uptime = datetime.now() - stats["start_time"]
                stats["uptime_seconds"] = uptime.total_seconds()
                
                # 목표 대비 달성률
                stats["throughput_achievement"] = (
                    stats["throughput_per_hour"] / self.config.target_throughput * 100
                    if self.config.target_throughput > 0 else 0
                )
                
                # 지연시간 목표 달성 여부
                stats["latency_within_target"] = (
                    stats["average_latency"] <= self.config.max_latency_seconds
                )
            
            # 성공률
            total_crawls = stats["total_crawls"]
            if total_crawls > 0:
                stats["success_rate"] = stats["successful_crawls"] / total_crawls * 100
            else:
                stats["success_rate"] = 0.0
            
            return stats
    
    def get_task_status(self) -> List[Dict[str, Any]]:
        """태스크별 상태 반환"""
        with self._lock:
            task_status = []
            
            for source_id, task in self.tasks_by_source.items():
                status = {
                    "source_id": source_id,
                    "priority": task.priority,
                    "interval_seconds": task.interval_seconds,
                    "is_running": task.is_running,
                    "scheduled_at": task.scheduled_at.isoformat(),
                    "last_run": task.last_run.isoformat() if task.last_run else None,
                    "last_success": task.last_success.isoformat() if task.last_success else None,
                    "consecutive_failures": task.consecutive_failures
                }
                task_status.append(status)
            
            return sorted(task_status, key=lambda x: x["priority"])


# 글로벌 인스턴스
_scheduler_instance: Optional[HighPerformanceScheduler] = None


def get_scheduler() -> HighPerformanceScheduler:
    """글로벌 스케줄러 인스턴스 반환"""
    global _scheduler_instance
    
    if _scheduler_instance is None:
        config = SchedulerConfig.from_env()
        _scheduler_instance = HighPerformanceScheduler(config)
    
    return _scheduler_instance


def stop_scheduler():
    """글로벌 스케줄러 중지"""
    global _scheduler_instance
    
    if _scheduler_instance:
        _scheduler_instance.stop()
        _scheduler_instance = None