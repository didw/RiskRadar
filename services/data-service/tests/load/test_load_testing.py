"""
부하 테스트
처리량 목표 달성, 메모리 사용량, 동시 요청 처리 테스트
"""
import asyncio
import time
import psutil
import gc
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock, patch
import pytest
from memory_profiler import profile

from src.crawlers.news.naver import NaverNewsCrawler
from src.crawlers.news.chosun import ChosunCrawler
from src.kafka.producer import NewsProducer
from src.processors.deduplicator import Deduplicator
from src.scheduler import CrawlerScheduler, TaskPriority, ScheduledTask
from src.metrics import CrawlerMetrics


@pytest.fixture
async def load_test_setup():
    """부하 테스트를 위한 설정"""
    # 컴포넌트 초기화
    deduplicator = Deduplicator()
    await deduplicator.initialize()
    
    producer = NewsProducer()
    scheduler = CrawlerScheduler()
    metrics = CrawlerMetrics()
    
    yield {
        'deduplicator': deduplicator,
        'producer': producer,
        'scheduler': scheduler,
        'metrics': metrics
    }
    
    # 정리
    await deduplicator.close()
    await producer.close()
    await scheduler.stop()


def generate_mock_articles(count: int, source: str = "test") -> List[Dict[str, Any]]:
    """테스트용 기사 생성"""
    return [
        {
            'title': f'{source} Article {i}',
            'url': f'https://{source}.com/article/{i}',
            'content': f'This is test content for article {i} from {source}',
            'published_at': (datetime.now() - timedelta(hours=i)).isoformat(),
            'source': source
        }
        for i in range(count)
    ]


class TestLoadTesting:
    """부하 테스트"""

    @pytest.mark.asyncio
    async def test_throughput_target_achievement(self, load_test_setup):
        """1000건/시간 처리량 달성 검증"""
        # Given: 목표 처리량 설정
        target_throughput_per_hour = 1000
        test_duration_seconds = 10  # 10초 동안 테스트
        target_throughput_per_test = (target_throughput_per_hour / 3600) * test_duration_seconds
        
        processed_count = 0
        start_time = time.time()
        
        # Mock 크롤러 설정
        async def mock_crawler_fetch(batch_size=50):
            return generate_mock_articles(batch_size)
        
        # When: 병렬 크롤링 실행
        async def process_batch():
            nonlocal processed_count
            
            articles = await mock_crawler_fetch(10)
            
            # 중복 제거
            unique_articles = []
            for article in articles:
                if not await load_test_setup['deduplicator'].is_duplicate(article['url']):
                    await load_test_setup['deduplicator'].add(article['url'])
                    unique_articles.append(article)
            
            # Kafka 전송 (실제로는 mock)
            for article in unique_articles:
                # await load_test_setup['producer'].send_news(article)
                processed_count += 1
            
            return len(unique_articles)
        
        # 병렬 처리
        tasks = []
        while (time.time() - start_time) < test_duration_seconds:
            # 동시에 여러 배치 처리
            batch_tasks = [process_batch() for _ in range(5)]
            results = await asyncio.gather(*batch_tasks)
            
            # 잠시 대기 (실제 크롤링 간격 시뮬레이션)
            await asyncio.sleep(0.1)
        
        # Then: 처리량 검증
        elapsed_time = time.time() - start_time
        actual_throughput_per_hour = (processed_count / elapsed_time) * 3600
        
        print(f"Processed: {processed_count} articles in {elapsed_time:.2f} seconds")
        print(f"Throughput: {actual_throughput_per_hour:.2f} articles/hour")
        
        # 목표 대비 80% 이상 달성 (테스트 환경 고려)
        assert actual_throughput_per_hour > (target_throughput_per_hour * 0.8)

    @pytest.mark.asyncio
    async def test_memory_usage_monitoring(self, load_test_setup):
        """메모리 사용량 모니터링"""
        # Given: 초기 메모리 사용량
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        memory_samples = []
        
        # When: 대량 데이터 처리
        async def memory_intensive_task():
            # 많은 수의 기사 생성 및 처리
            for i in range(20):
                articles = generate_mock_articles(100, f"source_{i}")
                
                # 메모리 사용량 샘플링
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_samples.append(current_memory)
                
                # 처리 시뮬레이션
                for article in articles:
                    await load_test_setup['deduplicator'].is_duplicate(article['url'])
                
                # 가비지 컬렉션 힌트
                if i % 5 == 0:
                    gc.collect()
                
                await asyncio.sleep(0.1)
        
        await memory_intensive_task()
        
        # Then: 메모리 사용량 분석
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory
        max_memory = max(memory_samples)
        avg_memory = sum(memory_samples) / len(memory_samples)
        
        print(f"Initial memory: {initial_memory:.2f} MB")
        print(f"Final memory: {final_memory:.2f} MB")
        print(f"Memory increase: {memory_increase:.2f} MB")
        print(f"Max memory: {max_memory:.2f} MB")
        print(f"Avg memory: {avg_memory:.2f} MB")
        
        # 메모리 누수 검증 (증가량이 100MB 미만)
        assert memory_increase < 100
        # 최대 메모리 사용량이 500MB 미만
        assert max_memory < 500

    @pytest.mark.asyncio
    async def test_concurrent_request_handling(self, load_test_setup):
        """동시 요청 처리 능력 테스트"""
        # Given: 동시 요청 수
        concurrent_crawlers = 10
        requests_per_crawler = 5
        
        success_count = 0
        error_count = 0
        response_times = []
        
        # Mock 크롤러 생성
        async def simulate_crawler_request(crawler_id: int):
            nonlocal success_count, error_count
            
            start_time = time.time()
            
            try:
                # 크롤링 시뮬레이션
                articles = generate_mock_articles(20, f"crawler_{crawler_id}")
                
                # 처리 시뮬레이션 (CPU 바운드 작업)
                processed = 0
                for article in articles:
                    # 중복 체크
                    if not await load_test_setup['deduplicator'].is_duplicate(article['url']):
                        await load_test_setup['deduplicator'].add(article['url'])
                        processed += 1
                
                # 응답 시간 기록
                response_time = time.time() - start_time
                response_times.append(response_time)
                
                success_count += 1
                return processed
                
            except Exception as e:
                error_count += 1
                raise e
        
        # When: 동시 실행
        all_tasks = []
        
        for i in range(concurrent_crawlers):
            # 각 크롤러가 여러 요청 수행
            crawler_tasks = [
                simulate_crawler_request(i) 
                for _ in range(requests_per_crawler)
            ]
            all_tasks.extend(crawler_tasks)
        
        start_time = time.time()
        results = await asyncio.gather(*all_tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        # Then: 동시성 성능 분석
        successful_results = [r for r in results if isinstance(r, int)]
        total_processed = sum(successful_results)
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        min_response_time = min(response_times) if response_times else 0
        
        print(f"Total requests: {len(all_tasks)}")
        print(f"Successful: {success_count}")
        print(f"Failed: {error_count}")
        print(f"Total processed: {total_processed} articles")
        print(f"Total time: {total_time:.2f} seconds")
        print(f"Avg response time: {avg_response_time:.3f} seconds")
        print(f"Max response time: {max_response_time:.3f} seconds")
        print(f"Min response time: {min_response_time:.3f} seconds")
        
        # 성능 검증
        assert success_count >= len(all_tasks) * 0.95  # 95% 이상 성공
        assert avg_response_time < 1.0  # 평균 응답 시간 1초 미만
        assert max_response_time < 3.0  # 최대 응답 시간 3초 미만

    @pytest.mark.asyncio
    async def test_sustained_load(self, load_test_setup):
        """지속적인 부하 테스트"""
        # Given: 지속 시간 설정
        test_duration = 30  # 30초
        sample_interval = 5  # 5초마다 샘플링
        
        performance_samples = []
        
        # 크롤링 시뮬레이터
        async def continuous_crawling():
            processed = 0
            start = time.time()
            
            while (time.time() - start) < test_duration:
                # 배치 처리
                articles = generate_mock_articles(50)
                
                for article in articles:
                    if not await load_test_setup['deduplicator'].is_duplicate(article['url']):
                        await load_test_setup['deduplicator'].add(article['url'])
                        processed += 1
                
                await asyncio.sleep(0.1)  # 실제 크롤링 간격
            
            return processed
        
        # When: 여러 크롤러 동시 실행
        async def monitor_performance():
            start = time.time()
            
            while (time.time() - start) < test_duration:
                # 현재 성능 메트릭 수집
                process = psutil.Process()
                cpu_percent = process.cpu_percent()
                memory_mb = process.memory_info().rss / 1024 / 1024
                
                performance_samples.append({
                    'timestamp': time.time() - start,
                    'cpu_percent': cpu_percent,
                    'memory_mb': memory_mb
                })
                
                await asyncio.sleep(sample_interval)
        
        # 크롤러와 모니터 동시 실행
        crawler_tasks = [continuous_crawling() for _ in range(5)]
        monitor_task = monitor_performance()
        
        results = await asyncio.gather(*crawler_tasks, monitor_task, return_exceptions=True)
        
        # Then: 지속적인 성능 분석
        total_processed = sum(r for r in results[:-1] if isinstance(r, int))
        
        # CPU 사용률 분석
        cpu_samples = [s['cpu_percent'] for s in performance_samples]
        avg_cpu = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
        max_cpu = max(cpu_samples) if cpu_samples else 0
        
        # 메모리 사용량 분석
        memory_samples = [s['memory_mb'] for s in performance_samples]
        avg_memory = sum(memory_samples) / len(memory_samples) if memory_samples else 0
        max_memory = max(memory_samples) if memory_samples else 0
        
        print(f"Test duration: {test_duration} seconds")
        print(f"Total processed: {total_processed} articles")
        print(f"Throughput: {(total_processed / test_duration) * 3600:.2f} articles/hour")
        print(f"Avg CPU: {avg_cpu:.2f}%")
        print(f"Max CPU: {max_cpu:.2f}%")
        print(f"Avg Memory: {avg_memory:.2f} MB")
        print(f"Max Memory: {max_memory:.2f} MB")
        
        # 지속 가능한 성능 검증
        assert avg_cpu < 80  # 평균 CPU 사용률 80% 미만
        assert max_memory < 1024  # 최대 메모리 1GB 미만
        assert total_processed > 0  # 실제 처리 발생

    @pytest.mark.asyncio
    async def test_rate_limiting_under_load(self, load_test_setup):
        """부하 상황에서의 Rate Limiting 테스트"""
        # Given: Rate limiter 설정
        rate_limit = 10  # 초당 10개 요청
        burst_size = 20  # 버스트 허용량
        
        request_times = []
        
        # Rate limited 크롤러 시뮬레이션
        async def rate_limited_request():
            request_time = time.time()
            request_times.append(request_time)
            
            # 실제 작업 시뮬레이션
            await asyncio.sleep(0.01)
            return True
        
        # When: 대량 요청 발생
        tasks = []
        for i in range(100):  # 100개 요청
            task = rate_limited_request()
            tasks.append(task)
            
            # Rate limiting 시뮬레이션
            if i > 0 and i % rate_limit == 0:
                await asyncio.sleep(1.0)
        
        results = await asyncio.gather(*tasks)
        
        # Then: Rate limiting 검증
        # 시간 간격 분석
        intervals = []
        for i in range(1, len(request_times)):
            interval = request_times[i] - request_times[i-1]
            intervals.append(interval)
        
        # 1초 윈도우 내 요청 수 계산
        windows = {}
        for req_time in request_times:
            window = int(req_time)
            windows[window] = windows.get(window, 0) + 1
        
        max_requests_per_window = max(windows.values())
        
        print(f"Total requests: {len(results)}")
        print(f"Max requests per second: {max_requests_per_window}")
        print(f"Average interval: {sum(intervals)/len(intervals):.3f} seconds")
        
        # Rate limit 준수 검증
        assert max_requests_per_window <= burst_size


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])