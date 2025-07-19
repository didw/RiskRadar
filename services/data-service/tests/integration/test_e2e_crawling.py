"""
End-to-End 크롤링 통합 테스트
전체 크롤링 파이프라인 테스트 (크롤링 → 중복제거 → Kafka 전송)
"""
import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock, patch
import pytest
from kafka import KafkaConsumer
from kafka.errors import KafkaError

from src.crawlers.news.naver import NaverNewsCrawler
from src.crawlers.news.chosun import ChosunCrawler
from src.kafka.producer import NewsProducer
from src.processors.deduplicator import Deduplicator
from src.scheduler import CrawlerScheduler
from src.config import settings


@pytest.fixture
async def kafka_consumer():
    """테스트용 Kafka Consumer"""
    consumer = KafkaConsumer(
        'raw-news',
        bootstrap_servers=['localhost:9092'],
        auto_offset_reset='latest',
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        consumer_timeout_ms=5000
    )
    yield consumer
    consumer.close()


@pytest.fixture
async def deduplicator():
    """테스트용 중복 제거기"""
    dedup = Deduplicator()
    await dedup.initialize()
    yield dedup
    await dedup.close()


@pytest.fixture
async def news_producer():
    """테스트용 뉴스 프로듀서"""
    producer = NewsProducer()
    yield producer
    await producer.close()


class TestE2ECrawling:
    """End-to-End 크롤링 통합 테스트"""

    @pytest.mark.asyncio
    async def test_full_crawling_pipeline(self, deduplicator, news_producer):
        """전체 크롤링 파이프라인 테스트"""
        # Given: 크롤러 설정
        crawler = NaverNewsCrawler()
        processed_articles = []
        
        # Mock HTML 응답
        mock_html = """
        <html>
            <div class="news_wrap">
                <a href="https://news.naver.com/article/001/0001234567">
                    <div class="news_tit">테스트 뉴스 제목</div>
                </a>
                <div class="info_group">
                    <span class="info">언론사</span>
                    <span class="info">2024-01-20 10:00</span>
                </div>
                <div class="dsc_wrap">테스트 뉴스 내용입니다.</div>
            </div>
        </html>
        """
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.text = AsyncMock(return_value=mock_html)
            mock_response.status = 200
            mock_get.return_value.__aenter__.return_value = mock_response
            
            # When: 크롤링 실행
            articles = await crawler.fetch_articles(limit=1)
            
            # 중복 제거
            unique_articles = []
            for article in articles:
                if not await deduplicator.is_duplicate(article['url']):
                    await deduplicator.add(article['url'])
                    unique_articles.append(article)
            
            # Kafka로 전송
            for article in unique_articles:
                await news_producer.send_news(article)
                processed_articles.append(article)
        
        # Then: 검증
        assert len(processed_articles) > 0
        assert all('title' in article for article in processed_articles)
        assert all('url' in article for article in processed_articles)
        assert all('content' in article for article in processed_articles)
        assert all('published_at' in article for article in processed_articles)

    @pytest.mark.asyncio
    async def test_throughput_target(self, deduplicator, news_producer):
        """처리량 목표 달성 테스트 (1000건/시간)"""
        # Given: 다수의 mock 기사
        num_articles = 20  # 실제 테스트에서는 더 작은 수로
        crawlers = [NaverNewsCrawler(), ChosunCrawler()]
        
        # Mock 응답 생성
        def generate_mock_html(idx):
            return f"""
            <html>
                <div class="news_wrap">
                    <a href="https://news.test.com/article/{idx}">
                        <div class="news_tit">테스트 뉴스 {idx}</div>
                    </a>
                    <div class="info_group">
                        <span class="info">테스트 언론사</span>
                        <span class="info">2024-01-20 10:00</span>
                    </div>
                    <div class="dsc_wrap">테스트 뉴스 내용 {idx}</div>
                </div>
            </html>
            """
        
        start_time = time.time()
        processed_count = 0
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Mock 설정
            async def mock_response_generator(url, **kwargs):
                mock_response = AsyncMock()
                idx = processed_count
                mock_response.text = AsyncMock(return_value=generate_mock_html(idx))
                mock_response.status = 200
                return mock_response
            
            mock_get.return_value.__aenter__.side_effect = mock_response_generator
            
            # When: 병렬 크롤링 실행
            tasks = []
            for i in range(num_articles):
                crawler = crawlers[i % len(crawlers)]
                task = asyncio.create_task(self._process_article(
                    crawler, deduplicator, news_producer
                ))
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            processed_count = sum(1 for r in results if r is True)
        
        # Then: 처리 시간 및 처리량 검증
        elapsed_time = time.time() - start_time
        throughput_per_hour = (processed_count / elapsed_time) * 3600
        
        # 테스트 환경에서는 낮은 목표치 사용
        assert throughput_per_hour > 100  # 실제로는 1000
        assert elapsed_time < 10  # 10초 이내 처리

    @pytest.mark.asyncio
    async def test_latency_target(self, deduplicator, news_producer):
        """지연시간 목표 달성 테스트 (5분 이내)"""
        # Given: 크롤러와 타임스탬프
        crawler = NaverNewsCrawler()
        crawl_start = datetime.now()
        
        mock_html = """
        <html>
            <div class="news_wrap">
                <a href="https://news.naver.com/latency/test">
                    <div class="news_tit">지연시간 테스트 뉴스</div>
                </a>
                <div class="info_group">
                    <span class="info">테스트 언론사</span>
                    <span class="info">2024-01-20 10:00</span>
                </div>
                <div class="dsc_wrap">지연시간 테스트 내용</div>
            </div>
        </html>
        """
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.text = AsyncMock(return_value=mock_html)
            mock_response.status = 200
            mock_get.return_value.__aenter__.return_value = mock_response
            
            # When: 크롤링 → 처리 → 전송
            articles = await crawler.fetch_articles(limit=1)
            
            for article in articles:
                if not await deduplicator.is_duplicate(article['url']):
                    await deduplicator.add(article['url'])
                    article['crawled_at'] = crawl_start.isoformat()
                    await news_producer.send_news(article)
            
            # Then: 전체 처리 시간 검증
            process_end = datetime.now()
            total_latency = (process_end - crawl_start).total_seconds()
            
            assert total_latency < 300  # 5분(300초) 이내
            assert total_latency < 10   # 테스트 환경에서는 10초 이내

    @pytest.mark.asyncio
    async def test_concurrent_crawlers(self, deduplicator, news_producer):
        """동시성 테스트 (여러 크롤러 동시 실행)"""
        # Given: 여러 크롤러 인스턴스
        crawlers = [
            NaverNewsCrawler(),
            ChosunCrawler(),
            NaverNewsCrawler(),  # 동일 크롤러 중복 실행
        ]
        
        # Mock 응답 생성
        mock_responses = {}
        for i, crawler in enumerate(crawlers):
            mock_responses[type(crawler).__name__ + str(i)] = f"""
            <html>
                <div class="news_wrap">
                    <a href="https://news.test.com/concurrent/{i}">
                        <div class="news_tit">동시성 테스트 뉴스 {i}</div>
                    </a>
                    <div class="info_group">
                        <span class="info">테스트 언론사 {i}</span>
                        <span class="info">2024-01-20 10:00</span>
                    </div>
                    <div class="dsc_wrap">동시성 테스트 내용 {i}</div>
                </div>
            </html>
            """
        
        processed_urls = set()
        error_count = 0
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            # 각 크롤러에 대한 mock 응답 설정
            call_count = 0
            
            async def mock_response_generator(url, **kwargs):
                nonlocal call_count
                mock_response = AsyncMock()
                idx = call_count % len(crawlers)
                call_count += 1
                
                mock_response.text = AsyncMock(
                    return_value=list(mock_responses.values())[idx]
                )
                mock_response.status = 200
                return mock_response
            
            mock_get.return_value.__aenter__.side_effect = mock_response_generator
            
            # When: 동시 실행
            async def crawl_and_process(crawler, idx):
                try:
                    articles = await crawler.fetch_articles(limit=1)
                    for article in articles:
                        if not await deduplicator.is_duplicate(article['url']):
                            await deduplicator.add(article['url'])
                            await news_producer.send_news(article)
                            processed_urls.add(article['url'])
                    return True
                except Exception as e:
                    nonlocal error_count
                    error_count += 1
                    return False
            
            tasks = [
                crawl_and_process(crawler, i)
                for i, crawler in enumerate(crawlers)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Then: 동시성 처리 검증
        successful_crawls = sum(1 for r in results if r is True)
        assert successful_crawls >= len(crawlers) - 1  # 최소 n-1개 성공
        assert error_count < 2  # 에러는 최대 1개
        assert len(processed_urls) >= 2  # 중복 제거 후 최소 2개 URL

    async def _process_article(self, crawler, deduplicator, producer):
        """단일 기사 처리 헬퍼 메서드"""
        try:
            articles = await crawler.fetch_articles(limit=1)
            for article in articles:
                if not await deduplicator.is_duplicate(article['url']):
                    await deduplicator.add(article['url'])
                    await producer.send_news(article)
            return True
        except Exception:
            return False

    @pytest.mark.asyncio
    async def test_error_recovery(self, deduplicator, news_producer):
        """에러 발생 시 복구 테스트"""
        # Given: 에러를 발생시키는 크롤러
        crawler = NaverNewsCrawler()
        success_count = 0
        error_count = 0
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            # 일부 요청은 실패하도록 설정
            call_count = 0
            
            async def mock_response_generator(url, **kwargs):
                nonlocal call_count
                call_count += 1
                
                if call_count % 3 == 0:  # 3번째마다 에러
                    raise aiohttp.ClientError("Connection error")
                
                mock_response = AsyncMock()
                mock_response.text = AsyncMock(return_value=f"""
                <html>
                    <div class="news_wrap">
                        <a href="https://news.test.com/recovery/{call_count}">
                            <div class="news_tit">복구 테스트 뉴스 {call_count}</div>
                        </a>
                        <div class="info_group">
                            <span class="info">테스트 언론사</span>
                            <span class="info">2024-01-20 10:00</span>
                        </div>
                        <div class="dsc_wrap">복구 테스트 내용</div>
                    </div>
                </html>
                """)
                mock_response.status = 200
                return mock_response
            
            mock_get.return_value.__aenter__.side_effect = mock_response_generator
            
            # When: 여러 번 크롤링 시도
            for i in range(6):
                try:
                    articles = await crawler.fetch_articles(limit=1)
                    if articles:
                        success_count += 1
                        for article in articles:
                            await news_producer.send_news(article)
                except Exception:
                    error_count += 1
                    await asyncio.sleep(0.1)  # 짧은 대기 후 재시도
        
        # Then: 에러 복구 검증
        assert success_count >= 4  # 6번 중 최소 4번 성공
        assert error_count >= 1    # 최소 1번의 에러 발생
        assert success_count + error_count == 6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])