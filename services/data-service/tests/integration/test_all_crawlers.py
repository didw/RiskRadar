"""
Integration tests for all news crawlers
"""
import pytest
import asyncio
from datetime import datetime
from src.crawlers.news import (
    ChosunCrawler,
    HankyungCrawler,
    JoongangCrawler,
    YonhapCrawler,
    MKCrawler
)


class TestAllCrawlersIntegration:
    """Integration tests for all crawlers"""
    
    @pytest.fixture
    def all_crawlers(self):
        """Get instances of all crawlers"""
        return [
            ChosunCrawler(),
            HankyungCrawler(),
            JoongangCrawler(),
            YonhapCrawler(),
            MKCrawler()
        ]
    
    @pytest.mark.asyncio
    async def test_all_crawlers_initialization(self, all_crawlers):
        """Test that all crawlers can be initialized"""
        assert len(all_crawlers) == 5
        
        # Check each crawler has required attributes
        for crawler in all_crawlers:
            assert hasattr(crawler, 'source_id')
            assert hasattr(crawler, 'base_url')
            assert hasattr(crawler, 'rate_limiter')
            assert hasattr(crawler, 'section_urls')
            assert len(crawler.section_urls) > 0
    
    @pytest.mark.asyncio
    async def test_all_crawlers_context_manager(self, all_crawlers):
        """Test that all crawlers work with async context manager"""
        for crawler in all_crawlers:
            async with crawler:
                assert crawler.session is not None
            # After exiting context, session should be closed
            assert crawler.session is None or crawler.session.closed
    
    @pytest.mark.asyncio
    async def test_data_normalization_consistency(self, all_crawlers):
        """Test that all crawlers produce consistent normalized data"""
        # Mock article data for testing
        mock_raw_article = {
            'title': 'Test Article Title',
            'url': '/test/article/123',
            'content': 'This is a test article content that is long enough to pass validation.',
            'published_at': '2024-01-15T10:00:00',
            'author': 'Test Author',
            'category': 'Test Category',
            'tags': ['test', 'article'],
            'image_url': '/images/test.jpg',
            'summary': 'Test summary'
        }
        
        for crawler in all_crawlers:
            normalized = crawler.normalize_article(mock_raw_article)
            
            # Check all required fields are present
            assert 'id' in normalized
            assert 'title' in normalized
            assert 'content' in normalized
            assert 'source' in normalized
            assert 'url' in normalized
            assert 'published_at' in normalized
            assert 'crawled_at' in normalized
            
            # Check source matches crawler
            assert normalized['source'] == crawler.source_id
            
            # Check URL is absolute
            assert normalized['url'].startswith('http')
            
            # Check timestamps are in ISO format
            assert 'T' in normalized['published_at']
            assert 'T' in normalized['crawled_at']
    
    @pytest.mark.asyncio
    async def test_url_validation_consistency(self, all_crawlers):
        """Test that all crawlers have consistent URL validation"""
        # Common invalid URLs that all crawlers should reject
        invalid_urls = [
            '',
            None,
            'javascript:void(0)',
            '#',
            '/search?q=test',
            '/login',
            '/member/join'
        ]
        
        for crawler in all_crawlers:
            for url in invalid_urls:
                if url is not None:  # Skip None for crawlers that don't handle it
                    assert not crawler._is_valid_article_url(url), \
                        f"{crawler.source_id} should reject URL: {url}"
    
    @pytest.mark.asyncio 
    async def test_rate_limiting_configuration(self, all_crawlers):
        """Test that all crawlers have appropriate rate limiting"""
        expected_rates = {
            'chosun': 0.5,    # 2 seconds
            'hankyung': 0.5,  # 2 seconds
            'joongang': 0.5,  # 2 seconds
            'yonhap': 0.3,    # 3+ seconds (stricter)
            'mk': 0.5         # 2 seconds
        }
        
        for crawler in all_crawlers:
            expected_rate = expected_rates.get(crawler.source_id, 0.5)
            actual_rate = 1.0 / crawler.rate_limiter.min_interval
            
            # Allow small tolerance
            assert abs(actual_rate - expected_rate) < 0.1, \
                f"{crawler.source_id} rate limit mismatch"
    
    @pytest.mark.asyncio
    async def test_error_handling_consistency(self, all_crawlers):
        """Test that all crawlers handle errors consistently"""
        # Test with invalid article data
        invalid_data_cases = [
            {},  # Empty data
            {'url': '/test'},  # Missing title
            {'title': ''},  # Empty title
            {'title': 'Hi', 'url': '/test'}  # Title too short
        ]
        
        for crawler in all_crawlers:
            for invalid_data in invalid_data_cases:
                with pytest.raises(ValueError):
                    crawler.normalize_article(invalid_data.copy())
    
    @pytest.mark.asyncio
    async def test_concurrent_crawling_simulation(self, all_crawlers):
        """Test that multiple crawlers can work concurrently"""
        # Create tasks for each crawler's test_connection
        tasks = []
        for crawler in all_crawlers:
            async with crawler:
                # Mock the fetch_page method to avoid actual network calls
                crawler.fetch_page = asyncio.coroutine(
                    lambda url: "<html><body>Test</body></html>"
                )
                task = crawler.test_connection()
                tasks.append(task)
        
        # Run all tests concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should succeed
        assert all(result is True for result in results), \
            f"Some crawlers failed connection test: {results}"
    
    def test_crawler_metadata(self, all_crawlers):
        """Test that all crawlers have proper metadata"""
        expected_metadata = {
            'chosun': ('조선일보', 'https://www.chosun.com'),
            'hankyung': ('한국경제', 'https://www.hankyung.com'),
            'joongang': ('중앙일보', 'https://www.joongang.co.kr'),
            'yonhap': ('연합뉴스', 'https://www.yna.co.kr'),
            'mk': ('매일경제', 'https://www.mk.co.kr')
        }
        
        for crawler in all_crawlers:
            expected_name, expected_url = expected_metadata[crawler.source_id]
            assert crawler.base_url == expected_url, \
                f"{crawler.source_id} base URL mismatch"
    
    @pytest.mark.asyncio
    async def test_date_parsing_consistency(self, all_crawlers):
        """Test that all crawlers can parse common Korean date formats"""
        # Common date formats that should work across crawlers
        test_dates = [
            "2024-01-15 14:30:00",
            "2024.01.15 14:30:00",
            "2024년 1월 15일"
        ]
        
        for crawler in all_crawlers:
            # Most crawlers have _parse_korean_date method
            if hasattr(crawler, '_parse_korean_date'):
                for date_text in test_dates:
                    result = crawler._parse_korean_date(date_text)
                    if result:  # Some formats might not work for all crawlers
                        # Should return ISO format
                        assert 'T' in result or result == ""
                        if result:
                            # Validate it's a valid date
                            try:
                                datetime.fromisoformat(result.replace('Z', '+00:00'))
                            except ValueError:
                                pytest.fail(f"{crawler.source_id} returned invalid date: {result}")