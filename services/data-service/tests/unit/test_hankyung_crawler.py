"""
Unit tests for HankyungCrawler
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch
from bs4 import BeautifulSoup
from src.crawlers.news.hankyung_crawler import HankyungCrawler


class TestHankyungCrawler:
    """Test HankyungCrawler functionality"""
    
    @pytest.fixture
    def crawler(self):
        return HankyungCrawler()
    
    @pytest.fixture
    def sample_article_list_html(self):
        """Sample HTML for article list page"""
        return """
        <html>
        <body>
            <div class="article_list">
                <a class="tit" href="/article/202401150001">경제 전망 기사</a>
                <a class="tit" href="/article/202401150002">금융 시장 분석</a>
            </div>
            <ul class="article_list">
                <li><a href="/news/article.php?news_id=12345">IT 신기술 소개</a></li>
            </ul>
            <div class="newslist">
                <a href="/2024/01/15/economy-news">경제 뉴스</a>
            </div>
            <div onclick="location.href='/article/202401150003'">
                <h3>온클릭 기사</h3>
            </div>
        </body>
        </html>
        """
    
    @pytest.fixture
    def sample_article_html(self):
        """Sample HTML for article page"""
        return """
        <html>
        <head>
            <title>한국 경제 성장률 전망 - 한국경제</title>
            <meta property="og:title" content="한국 경제 성장률 전망">
            <meta property="og:description" content="올해 한국 경제는 3% 성장이 예상된다">
            <meta property="og:image" content="https://img.hankyung.com/photo/202401/01.jpg">
            <meta property="article:published_time" content="2024-01-15T10:30:00+09:00">
            <meta property="article:section" content="경제">
            <meta name="keywords" content="경제,성장률,GDP,한국경제">
        </head>
        <body>
            <div class="breadcrumb">
                <a href="/">홈</a>
                <span>경제</span>
                <span>거시경제</span>
            </div>
            <h1 class="headline">한국 경제 성장률 전망</h1>
            <span class="date_time">입력 2024.01.15 10:30</span>
            <div class="reporter_info">
                <span>김경제 기자</span>
                <span>kim@hankyung.com</span>
            </div>
            <div id="articletxt">
                <p>한국은행이 발표한 경제전망 보고서에 따르면 올해 한국 경제는 3% 성장이 예상된다.</p>
                <p>이는 작년 2.5% 성장률보다 높은 수치로, 수출 회복과 내수 증가가 주요 요인으로 꼽힌다.</p>
                <div class="ad">광고</div>
                <p>전문가들은 반도체 산업의 회복과 함께 전반적인 경기 개선을 전망하고 있다.</p>
            </div>
            <div class="keyword">
                <a class="tag">경제성장</a>
                <a class="tag">한국은행</a>
            </div>
        </body>
        </html>
        """
    
    def test_initialization(self, crawler):
        """Test crawler initialization"""
        assert crawler.source_id == "hankyung"
        assert crawler.base_url == "https://www.hankyung.com"
        assert crawler.rate_limiter is not None
        assert len(crawler.section_urls) > 0
        assert len(crawler.selectors) > 0
    
    @pytest.mark.asyncio
    async def test_fetch_article_list(self, crawler, sample_article_list_html):
        """Test fetching article list"""
        # Mock fetch_page
        crawler.fetch_page = AsyncMock(return_value=sample_article_list_html)
        
        async with crawler:
            article_urls = await crawler.fetch_article_list()
            
            # Should find articles from different selectors
            assert len(article_urls) > 0
            
            # Check that various URL patterns are captured
            url_patterns = ['/article/', '/news/article.php', '/2024/01/15/']
            found_patterns = []
            for url in article_urls:
                for pattern in url_patterns:
                    if pattern in url:
                        found_patterns.append(pattern)
            
            assert len(set(found_patterns)) >= 2  # At least 2 different patterns found
            
            # URLs should be normalized (absolute)
            assert all(url.startswith('https://') for url in article_urls)
    
    def test_is_article_url(self, crawler):
        """Test article URL validation"""
        # Valid article URLs
        assert crawler._is_article_url("/article/202401150001")
        assert crawler._is_article_url("/news/article.php?news_id=12345")
        assert crawler._is_article_url("/2024/01/15/economy-news")
        assert crawler._is_article_url("/articleView?id=123456")
        assert crawler._is_article_url("/news/123456789")  # Numeric ID
        
        # Invalid URLs
        assert not crawler._is_article_url("/search?q=test")
        assert not crawler._is_article_url("/login")
        assert not crawler._is_article_url("javascript:void(0)")
        assert not crawler._is_article_url("/photo/gallery")
        assert not crawler._is_article_url("/opinion/column")
        assert not crawler._is_article_url("")
        assert not crawler._is_article_url(None)
    
    @pytest.mark.asyncio
    async def test_parse_article(self, crawler, sample_article_html):
        """Test parsing article content"""
        url = "https://www.hankyung.com/article/202401150001"
        article = await crawler.parse_article(url, sample_article_html)
        
        # Check all fields are extracted
        assert article['url'] == url
        assert article['title'] == "한국 경제 성장률 전망"
        assert "한국은행이 발표한" in article['content']
        assert "전문가들은 반도체" in article['content']
        assert "광고" not in article['content']  # Ad should be removed
        assert article['summary'] == "올해 한국 경제는 3% 성장이 예상된다"
        assert article['author'] == "김경제 기자"
        assert article['category'] == "경제"
        assert article['image_url'] == "https://img.hankyung.com/photo/202401/01.jpg"
        # Check that date is properly parsed (timezone info might be preserved or not)
        assert article['published_at'].startswith("2024-01-15T10:30:00")
        assert "경제성장" in article['tags']
        assert "한국은행" in article['tags']
        assert article['metadata']['source_name'] == '한국경제'
    
    def test_extract_title_fallback(self, crawler):
        """Test title extraction with fallback"""
        # Only page title available
        html = """
        <html>
        <head><title>경제 뉴스 - 한국경제신문</title></head>
        <body></body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        title = crawler._extract_title(soup)
        assert title == "경제 뉴스"  # Site name should be removed
    
    def test_parse_korean_date_formats(self, crawler):
        """Test parsing various Korean date formats"""
        test_cases = [
            ("2024.01.15 14:30:00", "2024-01-15T14:30:00"),
            ("2024.01.15 14:30", "2024-01-15T14:30:00"),
            ("2024-01-15 09:45", "2024-01-15T09:45:00"),
            ("입력 2024.01.15 10:30", "2024-01-15T10:30:00"),
            ("2024년 1월 15일 오후 2:30", "2024-01-15T14:30:00")  # 오후 handling
        ]
        
        for date_text, expected in test_cases:
            result = crawler._parse_korean_date(date_text)
            assert result.startswith(expected[:16])  # Compare up to minutes
    
    def test_extract_date_from_url(self, crawler):
        """Test date extraction from URL"""
        test_cases = [
            ("https://www.hankyung.com/2024/01/15/article", "2024-01-15"),
            ("https://www.hankyung.com/article/20240115123456", "2024-01-15"),
            ("https://www.hankyung.com/news?date=20240115", "2024-01-15")
        ]
        
        for url, expected_date in test_cases:
            result = crawler._extract_date_from_url(url)
            assert result.startswith(expected_date)
    
    def test_extract_author_patterns(self, crawler):
        """Test author extraction with various patterns"""
        test_cases = [
            '<span class="reporter">홍길동 기자</span>',
            '<div class="byline">김철수 특파원</div>',
            '<p>기자 이영희</p>',
            '<span>reporter@hankyung.com</span>'
        ]
        
        for html in test_cases:
            soup = BeautifulSoup(f"<html><body>{html}</body></html>", 'html.parser')
            author = crawler._extract_author(soup)
            assert author != ""  # Should find author in all cases
    
    def test_extract_category_from_url(self, crawler):
        """Test category extraction from URL"""
        test_cases = [
            ("https://www.hankyung.com/economy/article/123", "경제"),
            ("https://www.hankyung.com/finance/news/456", "금융"),
            ("https://www.hankyung.com/it/article/789", "IT"),
            ("https://www.hankyung.com/politics/news/012", "정치")
        ]
        
        for url, expected_category in test_cases:
            soup = BeautifulSoup("<html></html>", 'html.parser')
            category = crawler._extract_category(soup, url)
            assert category == expected_category
    
    def test_extract_content_filtering(self, crawler):
        """Test content extraction with filtering"""
        html = """
        <div id="articletxt">
            <p>정상적인 기사 내용입니다. 이것은 충분히 긴 문단입니다.</p>
            <div class="ad">광고입니다</div>
            <p>짧은 텍스트</p>
            <div class="related_news">관련 뉴스</div>
            <p>또 다른 정상적인 기사 내용입니다. 이것도 충분히 긴 문단입니다.</p>
            <p>김기자 기자</p>
            <p>Copyright 한국경제</p>
        </div>
        """
        soup = BeautifulSoup(html, 'html.parser')
        content = crawler._extract_content(soup)
        
        # Should include normal paragraphs
        assert "정상적인 기사 내용입니다" in content
        assert "또 다른 정상적인 기사 내용입니다" in content
        
        # Should exclude short texts, ads, related news
        assert "짧은 텍스트" not in content
        assert "광고입니다" not in content
        assert "관련 뉴스" not in content
        assert "김기자 기자" not in content  # Short signature
        assert "Copyright" not in content  # Copyright notice
    
    @pytest.mark.asyncio
    async def test_full_crawl_integration(self, crawler, sample_article_list_html, sample_article_html):
        """Test full crawling process"""
        # Mock fetch_page for both list and articles
        async def mock_fetch(url):
            if any(section in url for section in crawler.section_urls):
                return sample_article_list_html
            else:
                return sample_article_html
        
        crawler.fetch_page = AsyncMock(side_effect=mock_fetch)
        
        async with crawler:
            articles = await crawler.fetch_articles(max_articles=3)
            
            assert len(articles) <= 3
            if articles:
                article = articles[0]
                assert article['source'] == 'hankyung'
                assert article['title'] != ""
                assert 'crawled_at' in article
                assert article['id'] == crawler.create_article_id(article['url'])