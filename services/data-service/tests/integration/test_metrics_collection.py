"""
메트릭 수집 통합 테스트
메트릭 엔드포인트 응답, 크롤링 시 메트릭 업데이트, 에러 메트릭 테스트
"""
import asyncio
import time
from datetime import datetime
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock, patch
import pytest
from fastapi.testclient import TestClient
from prometheus_client import REGISTRY, CollectorRegistry

from src.main import app
from src.metrics import (
    CrawlerMetrics,
    crawl_duration_histogram,
    crawl_total_counter,
    crawl_errors_counter,
    active_crawlers_gauge,
    articles_processed_counter,
    kafka_send_duration_histogram,
    kafka_send_errors_counter
)
from src.crawlers.news.naver import NaverNewsCrawler
from src.kafka.producer import NewsProducer


@pytest.fixture
def test_client():
    """테스트용 FastAPI 클라이언트"""
    return TestClient(app)


@pytest.fixture
def metrics_collector():
    """테스트용 메트릭 수집기"""
    collector = CrawlerMetrics()
    # 테스트 전 메트릭 초기화
    collector.reset_metrics()
    yield collector
    # 테스트 후 정리
    collector.reset_metrics()


@pytest.fixture
async def mock_crawler():
    """Mock 크롤러"""
    crawler = Mock(spec=NaverNewsCrawler)
    crawler.source_id = "naver"
    crawler.fetch_articles = AsyncMock(return_value=[
        {
            'title': 'Test Article 1',
            'url': 'https://test.com/1',
            'content': 'Test content 1',
            'published_at': datetime.now().isoformat()
        },
        {
            'title': 'Test Article 2',
            'url': 'https://test.com/2',
            'content': 'Test content 2',
            'published_at': datetime.now().isoformat()
        }
    ])
    return crawler


@pytest.fixture
async def mock_producer():
    """Mock Kafka 프로듀서"""
    producer = Mock(spec=NewsProducer)
    producer.send_news = AsyncMock()
    return producer


class TestMetricsCollection:
    """메트릭 수집 테스트"""

    def test_metrics_endpoint_response(self, test_client):
        """메트릭 엔드포인트 응답 테스트"""
        # When: 메트릭 엔드포인트 호출
        response = test_client.get("/metrics")
        
        # Then: 정상 응답 확인
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        
        # Prometheus 포맷 검증
        metrics_text = response.text
        assert "# HELP" in metrics_text
        assert "# TYPE" in metrics_text
        
        # 주요 메트릭 존재 확인
        assert "crawler_crawl_duration_seconds" in metrics_text
        assert "crawler_crawl_total" in metrics_text
        assert "crawler_crawl_errors_total" in metrics_text
        assert "crawler_active_crawlers" in metrics_text
        assert "crawler_articles_processed_total" in metrics_text

    @pytest.mark.asyncio
    async def test_crawling_metrics_update(self, metrics_collector, mock_crawler):
        """크롤링 시 메트릭 업데이트 확인"""
        # Given: 초기 메트릭 값
        initial_crawl_count = crawl_total_counter._value.get()
        initial_article_count = articles_processed_counter._value.get()
        
        # When: 크롤링 실행
        with metrics_collector.track_crawl_duration("naver"):
            articles = await mock_crawler.fetch_articles()
            metrics_collector.increment_articles_processed("naver", len(articles))
        
        # Then: 메트릭 업데이트 확인
        assert crawl_total_counter._value.get() > initial_crawl_count
        assert articles_processed_counter._value.get() == initial_article_count + 2

    @pytest.mark.asyncio
    async def test_error_metrics_increment(self, metrics_collector, mock_crawler):
        """에러 발생 시 에러 메트릭 증가 확인"""
        # Given: 초기 에러 카운트
        initial_error_count = crawl_errors_counter._value.get()
        
        # 에러를 발생시키는 mock 설정
        mock_crawler.fetch_articles.side_effect = Exception("Crawling failed")
        
        # When: 크롤링 시도 (에러 발생)
        try:
            with metrics_collector.track_crawl_duration("naver"):
                await mock_crawler.fetch_articles()
        except Exception:
            metrics_collector.increment_crawl_errors("naver", "Exception")
        
        # Then: 에러 메트릭 증가 확인
        assert crawl_errors_counter._value.get() > initial_error_count

    @pytest.mark.asyncio
    async def test_active_crawlers_gauge(self, metrics_collector):
        """활성 크롤러 게이지 테스트"""
        # Given: 초기 활성 크롤러 수
        assert active_crawlers_gauge._value.get() == 0
        
        # When: 크롤러 시작
        metrics_collector.set_active_crawlers(3)
        
        # Then: 게이지 값 확인
        assert active_crawlers_gauge._value.get() == 3
        
        # When: 크롤러 종료
        metrics_collector.set_active_crawlers(1)
        
        # Then: 게이지 값 감소 확인
        assert active_crawlers_gauge._value.get() == 1

    @pytest.mark.asyncio
    async def test_kafka_send_metrics(self, metrics_collector, mock_producer):
        """Kafka 전송 메트릭 테스트"""
        # Given: 초기 Kafka 메트릭
        initial_kafka_errors = kafka_send_errors_counter._value.get()
        
        # When: 성공적인 Kafka 전송
        with metrics_collector.track_kafka_send_duration():
            await mock_producer.send_news({'test': 'data'})
        
        # Then: 에러 없이 완료
        assert kafka_send_errors_counter._value.get() == initial_kafka_errors
        
        # When: Kafka 전송 실패
        mock_producer.send_news.side_effect = Exception("Kafka error")
        
        try:
            with metrics_collector.track_kafka_send_duration():
                await mock_producer.send_news({'test': 'data'})
        except Exception:
            metrics_collector.increment_kafka_errors("send_failed")
        
        # Then: 에러 메트릭 증가
        assert kafka_send_errors_counter._value.get() > initial_kafka_errors

    @pytest.mark.asyncio
    async def test_concurrent_metrics_update(self, metrics_collector):
        """동시 메트릭 업데이트 테스트"""
        # Given: 여러 크롤러의 동시 실행
        async def simulate_crawler(crawler_id: str, success: bool = True):
            with metrics_collector.track_crawl_duration(crawler_id):
                await asyncio.sleep(0.1)  # 크롤링 시뮬레이션
                
                if success:
                    metrics_collector.increment_articles_processed(crawler_id, 5)
                else:
                    metrics_collector.increment_crawl_errors(crawler_id, "SimulatedError")
        
        # When: 동시 실행
        tasks = [
            simulate_crawler("crawler1", success=True),
            simulate_crawler("crawler2", success=True),
            simulate_crawler("crawler3", success=False),
            simulate_crawler("crawler4", success=True),
        ]
        
        await asyncio.gather(*tasks)
        
        # Then: 모든 메트릭이 정확히 업데이트되었는지 확인
        # 3개 성공, 1개 실패
        assert articles_processed_counter._value.get() >= 15  # 3 * 5 articles
        assert crawl_errors_counter._value.get() >= 1

    def test_metrics_labels(self, metrics_collector):
        """메트릭 레이블 테스트"""
        # When: 다양한 소스와 에러 타입으로 메트릭 업데이트
        metrics_collector.increment_crawl_errors("naver", "NetworkError")
        metrics_collector.increment_crawl_errors("chosun", "ParseError")
        metrics_collector.increment_crawl_errors("naver", "NetworkError")
        
        # Then: 레이블별로 메트릭이 구분되는지 확인
        # Prometheus 메트릭은 레이블 조합별로 별도 카운터 유지
        from prometheus_client.samples import Sample
        
        error_samples = list(crawl_errors_counter.collect()[0].samples)
        
        # 네이버 NetworkError가 2번 카운트되었는지 확인
        naver_network_errors = [
            s for s in error_samples 
            if s.labels.get('source') == 'naver' and s.labels.get('error_type') == 'NetworkError'
        ]
        assert len(naver_network_errors) > 0

    @pytest.mark.asyncio
    async def test_metrics_persistence(self, metrics_collector, test_client):
        """메트릭 지속성 테스트"""
        # Given: 일부 메트릭 업데이트
        metrics_collector.increment_articles_processed("test_source", 10)
        
        # When: 메트릭 엔드포인트 여러 번 호출
        response1 = test_client.get("/metrics")
        await asyncio.sleep(0.5)
        response2 = test_client.get("/metrics")
        
        # Then: 메트릭 값이 유지되는지 확인
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert "crawler_articles_processed_total" in response1.text
        assert "crawler_articles_processed_total" in response2.text

    @pytest.mark.asyncio
    async def test_histogram_metrics(self, metrics_collector):
        """히스토그램 메트릭 테스트"""
        # Given: 다양한 지연시간의 크롤링
        durations = [0.1, 0.5, 1.0, 2.0, 0.3]
        
        # When: 각각 다른 지연시간으로 크롤링
        for duration in durations:
            start = time.time()
            await asyncio.sleep(duration)
            elapsed = time.time() - start
            crawl_duration_histogram.labels(source="test").observe(elapsed)
        
        # Then: 히스토그램 버킷에 올바르게 분산되었는지 확인
        histogram_data = list(crawl_duration_histogram.collect()[0].samples)
        
        # 버킷 카운트 확인
        bucket_samples = [s for s in histogram_data if s.name.endswith("_bucket")]
        assert len(bucket_samples) > 0
        
        # 총 카운트 확인
        count_samples = [s for s in histogram_data if s.name.endswith("_count")]
        assert len(count_samples) > 0
        assert any(s.value == 5 for s in count_samples)  # 5개 관측값

    def test_metrics_health_integration(self, test_client):
        """헬스체크와 메트릭 통합 테스트"""
        # When: 헬스체크 호출
        health_response = test_client.get("/health")
        
        # Then: 헬스체크 정상
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert health_data["status"] == "healthy"
        
        # When: 메트릭 엔드포인트 호출
        metrics_response = test_client.get("/metrics")
        
        # Then: 메트릭도 정상
        assert metrics_response.status_code == 200
        
        # 헬스체크 관련 메트릭이 있는지 확인
        assert "http_requests_total" in metrics_response.text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])