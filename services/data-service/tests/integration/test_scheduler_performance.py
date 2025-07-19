"""
스케줄러 성능 통합 테스트
스케줄러 시작/중지, 태스크 스케줄링 정확성, 재시도 및 백오프, 우선순위 테스트
"""
import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import pytest

from src.scheduler import CrawlerScheduler, TaskPriority, ScheduledTask
from src.crawlers.news.naver import NaverNewsCrawler
from src.crawlers.news.chosun import ChosunCrawler


@pytest.fixture
async def scheduler():
    """테스트용 스케줄러"""
    sched = CrawlerScheduler()
    yield sched
    await sched.stop()


@pytest.fixture
def mock_crawlers():
    """Mock 크롤러들"""
    naver_crawler = Mock(spec=NaverNewsCrawler)
    naver_crawler.fetch_articles = AsyncMock(return_value=[
        {
            'title': 'Mock Naver News',
            'url': 'https://news.naver.com/mock/1',
            'content': 'Mock content',
            'published_at': datetime.now().isoformat()
        }
    ])
    
    chosun_crawler = Mock(spec=ChosunCrawler)
    chosun_crawler.fetch_articles = AsyncMock(return_value=[
        {
            'title': 'Mock Chosun News',
            'url': 'https://www.chosun.com/mock/1',
            'content': 'Mock content',
            'published_at': datetime.now().isoformat()
        }
    ])
    
    return {
        'naver': naver_crawler,
        'chosun': chosun_crawler
    }


class TestSchedulerPerformance:
    """스케줄러 성능 테스트"""

    @pytest.mark.asyncio
    async def test_scheduler_start_stop(self, scheduler):
        """스케줄러 시작/중지 테스트"""
        # Given: 스케줄러 초기 상태
        assert not scheduler.is_running
        
        # When: 스케줄러 시작
        await scheduler.start()
        
        # Then: 실행 상태 확인
        assert scheduler.is_running
        assert scheduler._scheduler_task is not None
        
        # When: 스케줄러 중지
        await scheduler.stop()
        
        # Then: 중지 상태 확인
        assert not scheduler.is_running
        assert scheduler._scheduler_task is None

    @pytest.mark.asyncio
    async def test_task_scheduling_accuracy(self, scheduler, mock_crawlers):
        """태스크 스케줄링 정확성 테스트"""
        # Given: 다양한 스케줄의 태스크들
        execution_times = []
        
        async def track_execution(crawler_name: str):
            execution_times.append({
                'crawler': crawler_name,
                'time': datetime.now()
            })
            await mock_crawlers[crawler_name].fetch_articles()
        
        # 즉시 실행 태스크
        immediate_task = ScheduledTask(
            id="immediate-task",
            crawler_name="naver",
            schedule_type="immediate",
            priority=TaskPriority.HIGH,
            callback=lambda: track_execution("naver")
        )
        
        # 1초 후 실행 태스크
        delayed_task = ScheduledTask(
            id="delayed-task",
            crawler_name="chosun",
            schedule_type="once",
            next_run=datetime.now() + timedelta(seconds=1),
            priority=TaskPriority.MEDIUM,
            callback=lambda: track_execution("chosun")
        )
        
        # When: 태스크 추가 및 스케줄러 실행
        scheduler.add_task(immediate_task)
        scheduler.add_task(delayed_task)
        
        await scheduler.start()
        await asyncio.sleep(2)  # 충분한 실행 시간
        await scheduler.stop()
        
        # Then: 실행 시간 정확성 검증
        assert len(execution_times) >= 2
        
        # 즉시 실행 태스크는 바로 실행되어야 함
        immediate_exec = next(e for e in execution_times if e['crawler'] == 'naver')
        assert immediate_exec is not None
        
        # 지연 실행 태스크는 약 1초 후 실행되어야 함
        delayed_exec = next(e for e in execution_times if e['crawler'] == 'chosun')
        if delayed_exec and immediate_exec:
            time_diff = (delayed_exec['time'] - immediate_exec['time']).total_seconds()
            assert 0.8 < time_diff < 1.5  # 오차 범위 허용

    @pytest.mark.asyncio
    async def test_retry_and_backoff(self, scheduler):
        """실패 시 재시도 및 백오프 테스트"""
        # Given: 실패하는 크롤러
        execution_attempts = []
        retry_count = 0
        
        async def failing_crawler():
            nonlocal retry_count
            retry_count += 1
            execution_attempts.append({
                'attempt': retry_count,
                'time': datetime.now()
            })
            
            if retry_count < 3:  # 처음 2번은 실패
                raise Exception("Crawling failed")
            
            return [{'title': 'Success', 'url': 'http://success.com'}]
        
        # 재시도 설정이 있는 태스크
        retry_task = ScheduledTask(
            id="retry-task",
            crawler_name="test",
            schedule_type="immediate",
            priority=TaskPriority.HIGH,
            callback=failing_crawler,
            max_retries=3,
            retry_delay=0.5  # 0.5초 백오프
        )
        
        # When: 태스크 실행
        scheduler.add_task(retry_task)
        await scheduler.start()
        await asyncio.sleep(3)  # 재시도 시간 고려
        await scheduler.stop()
        
        # Then: 재시도 및 백오프 검증
        assert len(execution_attempts) == 3  # 초기 시도 + 2번 재시도
        
        # 백오프 시간 검증
        for i in range(1, len(execution_attempts)):
            time_diff = (
                execution_attempts[i]['time'] - 
                execution_attempts[i-1]['time']
            ).total_seconds()
            
            # 지수 백오프: 0.5초 * (2^(i-1))
            expected_delay = 0.5 * (2 ** (i-1))
            assert abs(time_diff - expected_delay) < 0.2  # 오차 허용

    @pytest.mark.asyncio
    async def test_priority_based_scheduling(self, scheduler, mock_crawlers):
        """우선순위 기반 스케줄링 테스트"""
        # Given: 다양한 우선순위의 태스크들
        execution_order = []
        
        async def track_priority_execution(crawler_name: str, priority: str):
            execution_order.append({
                'crawler': crawler_name,
                'priority': priority,
                'time': datetime.now()
            })
            await mock_crawlers.get(crawler_name, mock_crawlers['naver']).fetch_articles()
        
        # 동시에 실행될 태스크들 (다른 우선순위)
        tasks = [
            ScheduledTask(
                id="low-priority",
                crawler_name="naver",
                schedule_type="immediate",
                priority=TaskPriority.LOW,
                callback=lambda: track_priority_execution("naver", "LOW")
            ),
            ScheduledTask(
                id="high-priority",
                crawler_name="chosun",
                schedule_type="immediate",
                priority=TaskPriority.HIGH,
                callback=lambda: track_priority_execution("chosun", "HIGH")
            ),
            ScheduledTask(
                id="medium-priority",
                crawler_name="naver",
                schedule_type="immediate",
                priority=TaskPriority.MEDIUM,
                callback=lambda: track_priority_execution("naver", "MEDIUM")
            ),
            ScheduledTask(
                id="critical-priority",
                crawler_name="chosun",
                schedule_type="immediate",
                priority=TaskPriority.CRITICAL,
                callback=lambda: track_priority_execution("chosun", "CRITICAL")
            )
        ]
        
        # When: 모든 태스크 추가 (순서 섞기)
        import random
        random.shuffle(tasks)
        for task in tasks:
            scheduler.add_task(task)
        
        await scheduler.start()
        await asyncio.sleep(2)  # 모든 태스크 실행 대기
        await scheduler.stop()
        
        # Then: 우선순위 순서 검증
        assert len(execution_order) == 4
        
        # 우선순위 순서: CRITICAL > HIGH > MEDIUM > LOW
        priority_values = {
            'CRITICAL': 4,
            'HIGH': 3,
            'MEDIUM': 2,
            'LOW': 1
        }
        
        # 실행 순서가 우선순위 순서와 일치하는지 확인
        for i in range(1, len(execution_order)):
            prev_priority = priority_values[execution_order[i-1]['priority']]
            curr_priority = priority_values[execution_order[i]['priority']]
            assert prev_priority >= curr_priority

    @pytest.mark.asyncio
    async def test_concurrent_task_limit(self, scheduler):
        """동시 실행 태스크 제한 테스트"""
        # Given: 동시 실행 카운터
        concurrent_count = 0
        max_concurrent = 0
        
        async def slow_task(task_id: int):
            nonlocal concurrent_count, max_concurrent
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
            
            await asyncio.sleep(0.5)  # 느린 작업 시뮬레이션
            
            concurrent_count -= 1
            return [{'title': f'Task {task_id}', 'url': f'http://test.com/{task_id}'}]
        
        # 많은 수의 태스크 생성
        for i in range(10):
            task = ScheduledTask(
                id=f"concurrent-{i}",
                crawler_name="test",
                schedule_type="immediate",
                priority=TaskPriority.MEDIUM,
                callback=lambda i=i: slow_task(i)
            )
            scheduler.add_task(task)
        
        # 동시 실행 제한 설정
        scheduler.max_concurrent_tasks = 3
        
        # When: 스케줄러 실행
        await scheduler.start()
        await asyncio.sleep(3)  # 충분한 실행 시간
        await scheduler.stop()
        
        # Then: 동시 실행 제한 검증
        assert max_concurrent <= scheduler.max_concurrent_tasks
        assert max_concurrent > 0  # 실제로 동시 실행이 발생했는지

    @pytest.mark.asyncio
    async def test_periodic_task_scheduling(self, scheduler, mock_crawlers):
        """주기적 태스크 스케줄링 테스트"""
        # Given: 주기적으로 실행되는 태스크
        execution_times = []
        
        async def periodic_execution():
            execution_times.append(datetime.now())
            return await mock_crawlers['naver'].fetch_articles()
        
        periodic_task = ScheduledTask(
            id="periodic-task",
            crawler_name="naver",
            schedule_type="interval",
            interval_seconds=0.5,  # 0.5초마다 실행
            priority=TaskPriority.MEDIUM,
            callback=periodic_execution
        )
        
        # When: 태스크 추가 및 실행
        scheduler.add_task(periodic_task)
        await scheduler.start()
        await asyncio.sleep(2.2)  # 약 4번 실행 예상
        await scheduler.stop()
        
        # Then: 주기적 실행 검증
        assert len(execution_times) >= 3  # 최소 3번 실행
        
        # 실행 간격 검증
        intervals = []
        for i in range(1, len(execution_times)):
            interval = (execution_times[i] - execution_times[i-1]).total_seconds()
            intervals.append(interval)
        
        # 평균 간격이 설정값과 비슷한지 확인
        avg_interval = sum(intervals) / len(intervals)
        assert 0.4 < avg_interval < 0.6  # 오차 범위 허용

    @pytest.mark.asyncio
    async def test_task_cancellation(self, scheduler):
        """태스크 취소 테스트"""
        # Given: 장시간 실행되는 태스크
        task_started = False
        task_completed = False
        
        async def long_running_task():
            nonlocal task_started, task_completed
            task_started = True
            await asyncio.sleep(2)  # 장시간 작업
            task_completed = True
            return []
        
        task = ScheduledTask(
            id="cancellable-task",
            crawler_name="test",
            schedule_type="immediate",
            priority=TaskPriority.LOW,
            callback=long_running_task
        )
        
        # When: 태스크 추가 후 취소
        scheduler.add_task(task)
        await scheduler.start()
        await asyncio.sleep(0.5)  # 태스크 시작 대기
        
        # 태스크 취소
        scheduler.remove_task("cancellable-task")
        await asyncio.sleep(2)  # 원래 완료 시간까지 대기
        await scheduler.stop()
        
        # Then: 태스크가 시작되었지만 완료되지 않았는지 확인
        assert task_started
        assert not task_completed

    @pytest.mark.asyncio
    async def test_scheduler_metrics(self, scheduler, mock_crawlers):
        """스케줄러 메트릭 수집 테스트"""
        # Given: 메트릭 추적을 위한 태스크들
        successful_task = ScheduledTask(
            id="success-task",
            crawler_name="naver",
            schedule_type="immediate",
            priority=TaskPriority.MEDIUM,
            callback=lambda: mock_crawlers['naver'].fetch_articles()
        )
        
        async def failing_task():
            raise Exception("Task failed")
        
        failed_task = ScheduledTask(
            id="fail-task",
            crawler_name="chosun",
            schedule_type="immediate",
            priority=TaskPriority.MEDIUM,
            callback=failing_task,
            max_retries=0  # 재시도 없음
        )
        
        # When: 태스크 실행
        scheduler.add_task(successful_task)
        scheduler.add_task(failed_task)
        
        await scheduler.start()
        await asyncio.sleep(1)
        await scheduler.stop()
        
        # Then: 메트릭 검증
        metrics = scheduler.get_metrics()
        assert metrics['total_tasks'] == 2
        assert metrics['successful_tasks'] >= 1
        assert metrics['failed_tasks'] >= 1
        assert metrics['active_tasks'] == 0  # 스케줄러 중지 후
        assert 'average_execution_time' in metrics
        assert 'tasks_by_priority' in metrics


if __name__ == "__main__":
    pytest.main([__file__, "-v"])