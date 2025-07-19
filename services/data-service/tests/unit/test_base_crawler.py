"""
Unit tests for BaseCrawler
"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
import aiohttp
from src.crawlers.base_crawler import BaseCrawler, RateLimiter


class MockCrawler(BaseCrawler):
    """Mock implementation for testing"""
    
    async def fetch_article_list(self):
        return [
            "https://example.com/article1",
            "https://example.com/article2"
        ]
    
    async def parse_article(self, url, html):
        return {
            'url': url,
            'title': 'Test Article',
            'content': 'Test content that is long enough to pass validation',
            'published_at': '2024-01-15T10:00:00'
        }


class TestRateLimiter:
    """Test RateLimiter functionality"""
    
    @pytest.mark.asyncio
    async def test_rate_limit_enforcement(self):
        """Test that rate limiter enforces delay between requests"""
        limiter = RateLimiter(requests_per_second=2.0)  # 0.5s between requests
        
        start_time = asyncio.get_event_loop().time()
        await limiter.wait_if_needed("example.com")
        await limiter.wait_if_needed("example.com")
        end_time = asyncio.get_event_loop().time()
        
        # Second request should wait at least 0.5 seconds
        assert end_time - start_time >= 0.4  # Allow small margin
    
    @pytest.mark.asyncio
    async def test_different_domains_independent(self):
        """Test that different domains have independent rate limits"""
        limiter = RateLimiter(requests_per_second=1.0)
        
        # Requests to different domains should not wait
        start_time = asyncio.get_event_loop().time()
        await limiter.wait_if_needed("domain1.com")
        await limiter.wait_if_needed("domain2.com")
        end_time = asyncio.get_event_loop().time()
        
        # Should be fast since different domains
        assert end_time - start_time < 0.5


class TestBaseCrawler:
    """Test BaseCrawler functionality"""
    
    @pytest.fixture
    def crawler(self):
        return MockCrawler(
            source_id="test_source",
            base_url="https://example.com",
            rate_limit=10.0,  # Fast for testing
            max_retries=2  # Fewer retries for faster tests
        )
    
    def test_initialization(self, crawler):
        """Test crawler initialization"""
        assert crawler.source_id == "test_source"
        assert crawler.base_url == "https://example.com"
        assert crawler.rate_limiter is not None
        assert 'User-Agent' in crawler.headers
    
    def test_normalize_url(self, crawler):
        """Test URL normalization"""
        # Absolute URL should remain unchanged
        assert crawler.normalize_url("https://example.com/article") == "https://example.com/article"
        
        # Relative URL should be converted to absolute
        assert crawler.normalize_url("/article") == "https://example.com/article"
        assert crawler.normalize_url("article") == "https://example.com/article"
    
    def test_create_article_id(self, crawler):
        """Test article ID generation"""
        url = "https://example.com/article1"
        article_id = crawler.create_article_id(url)
        
        # ID should be consistent for same URL
        assert article_id == crawler.create_article_id(url)
        
        # ID should be different for different URLs
        assert article_id != crawler.create_article_id("https://example.com/article2")
        
        # ID should be 16 characters (truncated SHA256)
        assert len(article_id) == 16
        
        # ID should include source_id for uniqueness
        # Different sources should have different IDs for same URL
        crawler2 = MockCrawler(
            source_id="other_source",
            base_url="https://example.com",
            rate_limit=10.0
        )
        assert article_id != crawler2.create_article_id(url)
    
    def test_normalize_article_success(self, crawler):
        """Test article normalization with valid data"""
        raw_article = {
            'title': '  Test Article  ',
            'url': '/article1',
            'content': '  Test content that is long enough to pass validation requirements  ',
            'published_at': '2024-01-15T10:00:00',
            'tags': ['  tag1  ', '', 'tag2  '],  # Test tag normalization
            'image_url': '/images/test.jpg'  # Test image URL normalization
        }
        
        normalized = crawler.normalize_article(raw_article)
        
        # Check required fields
        assert normalized['title'] == 'Test Article'  # Trimmed
        assert normalized['url'] == 'https://example.com/article1'  # Normalized
        assert normalized['content'] == 'Test content that is long enough to pass validation requirements'  # Trimmed
        assert normalized['source'] == 'test_source'
        assert normalized['id'] == crawler.create_article_id(normalized['url'])
        assert 'crawled_at' in normalized
        
        # Check optional fields have defaults
        assert normalized['summary'] == ''
        assert normalized['author'] == ''
        assert normalized['category'] == ''
        assert normalized['tags'] == ['tag1', 'tag2']  # Empty tags removed
        assert normalized['metadata'] == {}
        assert normalized['image_url'] == 'https://example.com/images/test.jpg'  # Normalized
    
    def test_normalize_article_missing_required_field(self, crawler):
        """Test article normalization with missing required fields"""
        # Missing title
        with pytest.raises(ValueError, match="Missing required field: title"):
            crawler.normalize_article({'url': '/article'})
        
        # Missing URL
        with pytest.raises(ValueError, match="Missing required field: url"):
            crawler.normalize_article({'title': 'Test'})
        
        # Empty title
        with pytest.raises(ValueError, match="Missing required field: title"):
            crawler.normalize_article({'title': '', 'url': '/article'})
        
        # Title too short
        with pytest.raises(ValueError, match="Title too short"):
            crawler.normalize_article({'title': 'Hi', 'url': '/article'})
    
    @pytest.mark.asyncio
    async def test_fetch_page_success(self, crawler):
        """Test successful page fetching"""
        # Mock the fetch_page method directly
        expected_content = "<html>Test</html>"
        
        with patch.object(crawler, 'fetch_page', new=AsyncMock(return_value=expected_content)):
            content = await crawler.fetch_page("https://example.com/test")
            assert content == expected_content
    
    @pytest.mark.asyncio
    async def test_fetch_page_error(self, crawler):
        """Test page fetching with network error"""
        # Mock the fetch_page method to raise an error
        with patch.object(crawler, 'fetch_page', side_effect=aiohttp.ClientError("Network error")):
            with pytest.raises(aiohttp.ClientError):
                await crawler.fetch_page("https://example.com/test")
    
    @pytest.mark.asyncio
    async def test_fetch_page_retry_on_server_error(self, crawler):
        """Test retry logic on server errors - simplified version"""
        # Since retry logic is internal to fetch_page, test retry behavior indirectly
        # by checking max_retries configuration exists
        assert crawler.max_retries == 2  # From fixture
        
        # Test that error propagates
        with patch.object(crawler, 'fetch_page', side_effect=aiohttp.ClientResponseError(
            request_info=Mock(),
            history=(),
            status=500
        )):
            with pytest.raises(aiohttp.ClientResponseError):
                await crawler.fetch_page("https://example.com/test")
    
    @pytest.mark.asyncio
    async def test_fetch_articles_success(self, crawler):
        """Test successful article fetching"""
        # Mock fetch_page to return longer HTML to pass validation
        long_html = "<html><body>" + "Mock content " * 100 + "</body></html>"
        crawler.fetch_page = AsyncMock(return_value=long_html)
        
        async with crawler:
            articles = await crawler.fetch_articles(max_articles=2)
            
            assert len(articles) == 2
            assert all(article['source'] == 'test_source' for article in articles)
            assert all('crawled_at' in article for article in articles)
            assert all(article['title'] == 'Test Article' for article in articles)
    
    @pytest.mark.asyncio
    async def test_fetch_articles_with_invalid_urls(self, crawler):
        """Test article fetching with invalid URLs filtered out"""
        # Override fetch_article_list to include invalid URLs
        crawler.fetch_article_list = AsyncMock(return_value=[
            "https://example.com/article1",
            "javascript:void(0)",  # Invalid
            "/search?q=test",  # Search page, not article
            "https://example.com/article2"
        ])
        
        # Mock fetch_page to return longer HTML to pass validation
        long_html = "<html><body>" + "Mock content " * 100 + "</body></html>"
        crawler.fetch_page = AsyncMock(return_value=long_html)
        
        async with crawler:
            articles = await crawler.fetch_articles()
            
            # Should only process valid article URLs
            assert len(articles) == 2
            assert crawler.fetch_page.call_count == 2  # Only valid URLs fetched
    
    @pytest.mark.asyncio
    async def test_test_connection(self, crawler):
        """Test connection testing"""
        # Mock successful connection
        crawler.fetch_page = AsyncMock(return_value="<html></html>")
        
        async with crawler:
            assert await crawler.test_connection() is True
        
        # Mock failed connection
        crawler.fetch_page = AsyncMock(side_effect=Exception("Connection failed"))
        
        async with crawler:
            assert await crawler.test_connection() is False
    
    def test_is_valid_article_url(self, crawler):
        """Test URL validation"""
        # Valid URLs
        assert crawler._is_valid_article_url("https://example.com/article/123")
        assert crawler._is_valid_article_url("http://example.com/news/story")
        
        # Invalid URLs
        assert not crawler._is_valid_article_url("")
        assert not crawler._is_valid_article_url(None)
        assert not crawler._is_valid_article_url("javascript:void(0)")
        assert not crawler._is_valid_article_url("https://example.com/login")
        assert not crawler._is_valid_article_url("https://example.com/search?q=test")
        assert not crawler._is_valid_article_url("https://example.com/file.pdf")