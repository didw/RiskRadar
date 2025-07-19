"""
Unit tests for YonhapCrawler
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch
from bs4 import BeautifulSoup
from src.crawlers.news.yonhap_crawler import YonhapCrawler


class TestYonhapCrawler:
    """Test YonhapCrawler functionality"""
    
    @pytest.fixture
    def crawler(self):
        return YonhapCrawler()
    
    @pytest.fixture
    def sample_article_list_html(self):
        """Sample HTML for article list page"""
        return """
        <html>
        <body>
            <div class="news-con">
                <a class="tit-wrap" href="/view/AKR20240115123456">경제 전망 발표</a>
            </div>
            <ul class="list">
                <li><a class="tit" href="/view/AKR20240115123457">정치 개혁안</a></li>
            </ul>
            <div class="item-box">
                <a href="/international/all/article/AKR20240115123458">국제 뉴스</a>
            </div>
            <div onclick="goToArticle('AKR20240115123459')">
                <h3>클릭 이벤트 기사</h3>
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
            <title>한국 경제 3% 성장 전망 | 연합뉴스</title>
            <meta property="og:title" content="한국 경제 3% 성장 전망">
            <meta property="og:description" content="(서울=연합뉴스) 한국은행이 올해 경제성장률을 3%로 전망했다">
            <meta property="og:image" content="https://img.yna.co.kr/photo/202401/01.jpg">
            <meta property="article:published_time" content="2024-01-15T10:30:00+09:00">
            <meta name="keywords" content="경제,성장률,한국은행,GDP">
        </head>
        <body>
            <div class="location">
                <a href="/">홈</a>
                <span>경제</span>
                <span>금융</span>
            </div>
            <h1 class="tit">한국 경제 3% 성장 전망</h1>
            <p class="update-time">송고시간 2024-01-15 10:30</p>
            <div class="article-txt">
                <p>(서울=연합뉴스) 김경제 기자 = 한국은행이 15일 발표한 경제전망 보고서에 따르면 올해 우리나라 경제성장률이 3%를 기록할 것으로 예상된다.</p>
                <div class="article-ad">광고</div>
                <p>이는 작년 2.5%보다 0.5%포인트 상승한 수치로, 수출 회복과 내수 개선이 주요 요인으로 분석된다.</p>
                <p>전문가들은 글로벌 경기 회복과 반도체 업황 개선을 긍정적 신호로 평가했다.</p>
                <p>kim@yna.co.kr</p>
            </div>
            <ul class="tag-list">
                <li>경제성장</li>
                <li>한국은행</li>
            </ul>
        </body>
        </html>
        """
    
    def test_initialization(self, crawler):
        """Test crawler initialization"""
        assert crawler.source_id == "yonhap"
        assert crawler.base_url == "https://www.yna.co.kr"
        assert crawler.rate_limiter is not None
        assert crawler.rate_limiter.min_interval > 3  # Slower rate for Yonhap
        assert len(crawler.section_urls) > 0
    
    @pytest.mark.asyncio
    async def test_fetch_article_list(self, crawler, sample_article_list_html):
        """Test fetching article list"""
        crawler.fetch_page = AsyncMock(return_value=sample_article_list_html)
        
        async with crawler:
            article_urls = await crawler.fetch_article_list()
            
            assert len(article_urls) > 0
            
            # Check that AKR IDs are found
            akr_urls = [url for url in article_urls if 'AKR' in url]
            assert len(akr_urls) >= 3  # Should find at least 3 AKR articles
            
            # All URLs should be absolute
            assert all(url.startswith('https://') for url in article_urls)
    
    def test_is_article_url(self, crawler):
        """Test article URL validation"""
        # Valid URLs
        assert crawler._is_article_url("/view/AKR20240115123456")
        assert crawler._is_article_url("/article/AKR20240115123456")
        assert crawler._is_article_url("?article_id=AKR20240115123456")
        assert crawler._is_article_url("/news/12345")
        assert crawler._is_article_url("/bulletin/2024/01/15/news")
        
        # Invalid URLs
        assert not crawler._is_article_url("/photo/gallery")
        assert not crawler._is_article_url("/graphics/chart")
        assert not crawler._is_article_url("/search?q=test")
        assert not crawler._is_article_url("javascript:void(0)")
        assert not crawler._is_article_url("")
    
    def test_extract_article_id(self, crawler):
        """Test article ID extraction"""
        test_cases = [
            ("https://www.yna.co.kr/view/AKR20240115123456", "AKR20240115123456"),
            ("/article/AKR20240115999999", "AKR20240115999999"),
            ("?article_id=IPR20240115000001", "IPR20240115000001")
        ]
        
        for url, expected_id in test_cases:
            assert crawler._extract_article_id(url) == expected_id
    
    @pytest.mark.asyncio
    async def test_parse_article(self, crawler, sample_article_html):
        """Test parsing article content"""
        url = "https://www.yna.co.kr/view/AKR20240115123456"
        article = await crawler.parse_article(url, sample_article_html)
        
        # Verify all fields
        assert article['url'] == url
        assert article['title'] == "한국 경제 3% 성장 전망"
        assert "한국은행이 15일 발표한" in article['content']
        assert "수출 회복과 내수 개선" in article['content']
        assert "(서울=연합뉴스)" not in article['content']  # Location pattern removed
        assert "광고" not in article['content']  # Ad removed
        assert article['summary'] == "한국은행이 올해 경제성장률을 3%로 전망했다"
        assert "김경제" in article['author']
        assert article['category'] == "경제"
        assert article['image_url'] == "https://img.yna.co.kr/photo/202401/01.jpg"
        assert article['published_at'].startswith("2024-01-15T10:30:00")
        assert "경제성장" in article['tags']
        assert "한국은행" in article['tags']
        assert article['metadata']['source_name'] == '연합뉴스'
        assert article['metadata']['article_id'] == 'AKR20240115123456'
    
    def test_extract_title_cleanup(self, crawler):
        """Test title extraction with cleanup"""
        html = """
        <html>
        <head><title>뉴스 제목 :: 연합뉴스</title></head>
        <body></body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        title = crawler._extract_title(soup)
        assert title == "뉴스 제목"  # Agency name removed
    
    def test_parse_korean_date_formats(self, crawler):
        """Test various Korean date formats"""
        test_cases = [
            ("2024-01-15 14:30", "2024-01-15T14:30:00"),
            ("송고시간 2024-01-15 14:30", "2024-01-15T14:30:00"),
            ("입력 2024.01.15 오후 2:30", "2024-01-15T14:30:00")
        ]
        
        for date_text, expected in test_cases:
            result = crawler._parse_korean_date(date_text)
            assert result.startswith(expected[:16])
    
    def test_extract_date_from_article_id(self, crawler):
        """Test date extraction from Yonhap article ID"""
        # AKR20240115143000 -> 2024-01-15 14:30
        url = "https://www.yna.co.kr/view/AKR20240115143000"
        soup = BeautifulSoup("<html></html>", 'html.parser')
        
        # Mock other extraction methods to fail
        with patch.object(crawler, '_parse_korean_date', return_value=""):
            date = crawler._extract_published_date(soup, url)
            assert date.startswith("2024-01-15T14")
    
    def test_extract_author_patterns(self, crawler):
        """Test author extraction with Yonhap patterns"""
        test_cases = [
            "<p>(서울=연합뉴스) 홍길동 기자 = 기사내용</p>",
            "<p>김철수 특파원 kim@yna.co.kr</p>",
            '<meta name="author" content="이영희 기자">',
            "<div>reporter@yna.co.kr</div>"
        ]
        
        for html in test_cases:
            full_html = f"<html><body>{html}</body></html>"
            soup = BeautifulSoup(full_html, 'html.parser')
            author = crawler._extract_author(soup)
            assert author != ""
            assert author != "연합뉴스" or "@yna.co.kr" in author
    
    def test_extract_category_from_url(self, crawler):
        """Test category extraction from URL"""
        test_cases = [
            ("https://www.yna.co.kr/economy/all/1", "경제"),
            ("https://www.yna.co.kr/politics/assembly/2", "정치"),
            ("https://www.yna.co.kr/international/all/3", "국제"),
            ("https://www.yna.co.kr/sports/football/4", "스포츠"),
            ("https://www.yna.co.kr/nk/news/5", "북한")
        ]
        
        for url, expected_category in test_cases:
            soup = BeautifulSoup("<html></html>", 'html.parser')
            category = crawler._extract_category(soup, url)
            assert category == expected_category
    
    def test_extract_content_cleanup(self, crawler):
        """Test content extraction with Yonhap-specific cleanup"""
        html = """
        <div class="article-txt">
            <p>(서울=연합뉴스) 김기자 기자 = 정상적인 기사 내용입니다. 이것은 충분히 긴 문단입니다.</p>
            <div class="article-ad">광고입니다</div>
            <p>또 다른 정상적인 기사 내용입니다. 이것도 충분히 긴 문단입니다.</p>
            <p>무단전재 및 재배포금지</p>
            <p>김기자 기자</p>
        </div>
        """
        soup = BeautifulSoup(html, 'html.parser')
        content = crawler._extract_content(soup)
        
        # Should include normal content
        assert "정상적인 기사 내용입니다" in content
        assert "또 다른 정상적인 기사 내용입니다" in content
        
        # Should exclude unwanted elements
        assert "(서울=연합뉴스)" not in content
        assert "광고입니다" not in content
        assert "무단전재" not in content
        assert content.count("김기자 기자") == 0  # Short signature removed
    
    def test_extract_summary_cleanup(self, crawler):
        """Test summary extraction with Yonhap format cleanup"""
        html = """
        <meta property="og:description" content="(서울=연합뉴스) 한국은행이 경제성장률을 상향 조정했다">
        """
        soup = BeautifulSoup(html, 'html.parser')
        summary = crawler._extract_summary(soup, "")
        
        # Should remove location pattern
        assert summary == "한국은행이 경제성장률을 상향 조정했다"
        assert "(서울=연합뉴스)" not in summary
    
    @pytest.mark.asyncio
    async def test_full_crawl_integration(self, crawler, sample_article_list_html, sample_article_html):
        """Test full crawling process"""
        async def mock_fetch(url):
            if any(section in url for section in crawler.section_urls):
                return sample_article_list_html
            else:
                return sample_article_html
        
        crawler.fetch_page = AsyncMock(side_effect=mock_fetch)
        
        async with crawler:
            articles = await crawler.fetch_articles(max_articles=2)
            
            assert len(articles) <= 2
            if articles:
                article = articles[0]
                assert article['source'] == 'yonhap'
                assert article['title'] != ""
                assert 'crawled_at' in article
                assert article['id'] == crawler.create_article_id(article['url'])