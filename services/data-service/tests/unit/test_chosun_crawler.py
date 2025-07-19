"""
Unit tests for ChosunCrawler
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch
from bs4 import BeautifulSoup
from src.crawlers.news.chosun_crawler import ChosunCrawler


class TestChosunCrawler:
    """Test ChosunCrawler functionality"""
    
    @pytest.fixture
    def crawler(self):
        return ChosunCrawler()
    
    @pytest.fixture
    def sample_article_list_html(self):
        """Sample HTML for article list page"""
        return """
        <html>
        <body>
            <div class="news_item">
                <a href="/news/article1">Article 1</a>
            </div>
            <ul class="news_list">
                <li><a href="/news/article2">Article 2</a></li>
            </ul>
            <article>
                <a href="/news/article3">Article 3</a>
            </article>
        </body>
        </html>
        """
    
    @pytest.fixture
    def sample_article_html(self):
        """Sample HTML for article page"""
        return """
        <html>
        <head>
            <title>Test Article Title - 조선일보</title>
            <meta property="og:title" content="Test Article Title">
            <meta property="og:description" content="This is a test article summary">
            <meta property="og:image" content="https://example.com/image.jpg">
            <meta property="article:published_time" content="2024-01-15T10:00:00+09:00">
            <meta property="article:section" content="경제">
            <meta name="keywords" content="test,article,news">
        </head>
        <body>
            <h1 class="article-title">Test Article Title</h1>
            <div class="article_date">2024.01.15 10:00</div>
            <span class="reporter_name">홍길동 기자</span>
            <div class="article-body">
                <p>This is the first paragraph of the article.</p>
                <p>This is the second paragraph with more content.</p>
                <script>console.log('should be removed');</script>
                <p>This is the third paragraph after script.</p>
            </div>
            <div class="tags">
                <a class="tag">태그1</a>
                <a class="tag">태그2</a>
            </div>
        </body>
        </html>
        """
    
    def test_initialization(self, crawler):
        """Test crawler initialization"""
        assert crawler.source_id == "chosun"
        assert crawler.base_url == "https://www.chosun.com"
        assert crawler.rate_limiter is not None
        assert len(crawler.section_urls) > 0
    
    @pytest.mark.asyncio
    async def test_fetch_article_list(self, crawler, sample_article_list_html):
        """Test fetching article list"""
        # Mock fetch_page
        crawler.fetch_page = AsyncMock(return_value=sample_article_list_html)
        
        async with crawler:
            article_urls = await crawler.fetch_article_list()
            
            # Should find articles from different selectors
            assert len(article_urls) > 0
            assert any('/news/article1' in url for url in article_urls)
            assert any('/news/article2' in url for url in article_urls)
            assert any('/news/article3' in url for url in article_urls)
            
            # URLs should be normalized (absolute)
            assert all(url.startswith('https://') for url in article_urls)
    
    @pytest.mark.asyncio
    async def test_parse_article(self, crawler, sample_article_html):
        """Test parsing article content"""
        url = "https://www.chosun.com/news/test-article"
        article = await crawler.parse_article(url, sample_article_html)
        
        # Check all fields are extracted
        assert article['url'] == url
        assert article['title'] == "Test Article Title"
        assert "first paragraph" in article['content']
        assert "second paragraph" in article['content']
        assert "third paragraph" in article['content']
        assert "console.log" not in article['content']  # Script should be removed
        assert article['summary'] == "This is a test article summary"
        assert article['author'] == "홍길동 기자"
        assert article['category'] == "경제"
        assert article['image_url'] == "https://example.com/image.jpg"
        assert article['published_at'] == "2024-01-15T10:00:00+09:00"
        assert '태그1' in article['tags']
        assert '태그2' in article['tags']
        assert article['metadata']['source_name'] == '조선일보'
        assert article['metadata']['language'] == 'ko'
    
    def test_extract_title_fallback(self, crawler):
        """Test title extraction with fallback"""
        # No og:title or h1, only page title
        html = """
        <html>
        <head><title>Fallback Title - 조선일보</title></head>
        <body></body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        title = crawler._extract_title(soup)
        assert title == "Fallback Title"  # Site name should be removed
    
    def test_extract_content_fallback(self, crawler):
        """Test content extraction with fallback"""
        # No article-body div, use main content area
        html = """
        <html>
        <body>
            <main>
                <p>Paragraph in main.</p>
                <p>Another paragraph.</p>
            </main>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        content = crawler._extract_content(soup)
        assert "Paragraph in main" in content
        assert "Another paragraph" in content
    
    def test_parse_korean_date(self, crawler):
        """Test Korean date parsing"""
        # Test different date formats
        test_cases = [
            ("2024.01.15 14:30", "2024-01-15T14:30:00"),
            ("2024-01-15 09:45", "2024-01-15T09:45:00"),
            ("2024년 1월 15일 10:00", "2024-01-15T10:00:00")
        ]
        
        for date_text, expected in test_cases:
            result = crawler._parse_korean_date(date_text)
            assert result.startswith(expected[:16])  # Compare up to minutes
    
    def test_extract_category_from_url(self, crawler):
        """Test category extraction from URL"""
        html = "<html><body></body></html>"
        soup = BeautifulSoup(html, 'html.parser')
        
        # Test URL-based extraction
        category = crawler._extract_category(soup, "https://www.chosun.com/economy/article")
        assert category == "경제"
        
        category = crawler._extract_category(soup, "https://www.chosun.com/politics/article")
        assert category == "정치"
        
        # Default category
        category = crawler._extract_category(soup, "https://www.chosun.com/unknown/article")
        assert category == "일반"
    
    def test_extract_author_with_email_pattern(self, crawler):
        """Test author extraction with email/reporter pattern"""
        html = """
        <html>
        <body>
            <div>기사 내용... 김철수 기자 (kim@chosun.com)</div>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        author = crawler._extract_author(soup)
        assert author == "김철수 기자"
    
    def test_extract_summary_generation(self, crawler):
        """Test summary generation from content"""
        html = """
        <html>
        <body>
            <div class="article-body">
                <p>This is a long article with many paragraphs that needs to be summarized. 
                The content goes on and on with lots of details about various topics that 
                are very interesting but too long to fit in a summary field completely.</p>
            </div>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Mock _extract_content to return long text
        with patch.object(crawler, '_extract_content', return_value="A" * 300):
            summary = crawler._extract_summary(soup)
            assert len(summary) <= 203  # 200 chars + "..."
            assert summary.endswith("...")
    
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
            articles = await crawler.fetch_articles(max_articles=2)
            
            assert len(articles) <= 2
            if articles:  # If any articles were found
                article = articles[0]
                assert article['source'] == 'chosun'
                assert article['title'] == 'Test Article Title'
                assert 'crawled_at' in article
                assert article['id'] == crawler.create_article_id(article['url'])