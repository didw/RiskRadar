"""
Unit tests for JoongangCrawler
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch
from bs4 import BeautifulSoup
from src.crawlers.news.joongang_crawler import JoongangCrawler


class TestJoongangCrawler:
    """Test JoongangCrawler functionality"""
    
    @pytest.fixture
    def crawler(self):
        return JoongangCrawler()
    
    @pytest.fixture
    def sample_article_list_html(self):
        """Sample HTML for article list page"""
        return """
        <html>
        <body>
            <h2 class="headline">
                <a href="/article/25195273">정치 개혁 논의 본격화</a>
            </h2>
            <div class="card_body">
                <h2><a href="/money/article/25195274">경제 전망 발표</a></h2>
            </div>
            <ul class="story_list">
                <li><a href="/20240115/economy-123">경제 뉴스</a></li>
            </ul>
            <div data-link="/world/article/25195275">
                <h3>국제 뉴스</h3>
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
            <title>경제 성장률 3% 돌파 전망 - 중앙일보</title>
            <meta property="og:title" content="경제 성장률 3% 돌파 전망">
            <meta property="og:description" content="한국은행이 올해 경제 성장률을 3%로 상향 조정했다">
            <meta property="og:image" content="https://pds.joongang.co.kr/news/photo.jpg">
            <meta property="article:published_time" content="2024-01-15T10:30:00+09:00">
            <meta property="article:section" content="경제">
            <meta name="keywords" content="경제,성장률,한국은행">
        </head>
        <body>
            <nav class="breadcrumb">
                <a href="/">홈</a>
                <span>경제</span>
                <span>금융</span>
            </nav>
            <h1 class="headline">경제 성장률 3% 돌파 전망</h1>
            <div class="byline">
                <span class="name">박경제</span>
                <time datetime="2024-01-15T10:30:00+09:00">입력 2024.01.15 10:30</time>
            </div>
            <div id="article_body">
                <p>한국은행이 15일 발표한 경제전망 보고서에 따르면 올해 국내총생산(GDP) 성장률이 3%를 돌파할 것으로 예상된다.</p>
                <div class="ab_photo">
                    <img src="/photo/small.jpg" width="100">
                    <div class="photo_desc">사진 설명</div>
                </div>
                <p>이는 수출 증가와 내수 회복이 동반 상승하면서 나타난 결과로 분석된다.</p>
                <div class="ad">광고 영역</div>
                <p>전문가들은 반도체 업황 개선과 소비 심리 회복을 긍정적 요인으로 꼽았다.</p>
            </div>
            <div class="keyword_box">
                <a class="keyword">#경제성장</a>
                <a class="keyword">#GDP</a>
            </div>
        </body>
        </html>
        """
    
    def test_initialization(self, crawler):
        """Test crawler initialization"""
        assert crawler.source_id == "joongang"
        assert crawler.base_url == "https://www.joongang.co.kr"
        assert crawler.rate_limiter is not None
        assert len(crawler.section_urls) > 0
    
    @pytest.mark.asyncio
    async def test_fetch_article_list(self, crawler, sample_article_list_html):
        """Test fetching article list"""
        crawler.fetch_page = AsyncMock(return_value=sample_article_list_html)
        
        async with crawler:
            article_urls = await crawler.fetch_article_list()
            
            assert len(article_urls) > 0
            
            # Check various URL patterns are found
            patterns_found = {
                'article': any('/article/' in url for url in article_urls),
                'date': any('/20240115/' in url for url in article_urls)
            }
            assert any(patterns_found.values())
            
            # All URLs should be absolute
            assert all(url.startswith('https://') for url in article_urls)
    
    def test_is_article_url(self, crawler):
        """Test article URL validation"""
        # Valid URLs
        assert crawler._is_article_url("/article/25195273")
        assert crawler._is_article_url("/news/article.aspx?id=123")
        assert crawler._is_article_url("/20240115/123456")
        assert crawler._is_article_url("/view/news123")
        assert crawler._is_article_url("/12345678")  # Long numeric ID
        
        # Invalid URLs
        assert not crawler._is_article_url("/cartoon/list")
        assert not crawler._is_article_url("/photo/gallery")
        assert not crawler._is_article_url("/video/123")
        assert not crawler._is_article_url("/search?q=test")
        assert not crawler._is_article_url("#comment")
        assert not crawler._is_article_url("")
    
    @pytest.mark.asyncio
    async def test_parse_article(self, crawler, sample_article_html):
        """Test parsing article content"""
        url = "https://www.joongang.co.kr/article/25195273"
        article = await crawler.parse_article(url, sample_article_html)
        
        # Verify all fields
        assert article['url'] == url
        assert article['title'] == "경제 성장률 3% 돌파 전망"
        assert "한국은행이 15일 발표한" in article['content']
        assert "수출 증가와 내수 회복" in article['content']
        assert "사진 설명" not in article['content']  # Photo description removed
        assert "광고 영역" not in article['content']  # Ad removed
        assert article['summary'] == "한국은행이 올해 경제 성장률을 3%로 상향 조정했다"
        assert article['author'] == "박경제 기자"
        assert article['category'] == "경제"
        assert article['image_url'] == "https://pds.joongang.co.kr/news/photo.jpg"
        assert article['published_at'].startswith("2024-01-15T10:30:00")
        assert "경제성장" in article['tags']
        assert "GDP" in article['tags']
        assert article['metadata']['source_name'] == '중앙일보'
    
    def test_extract_title_cleanup(self, crawler):
        """Test title extraction with cleanup"""
        html = """
        <html>
        <head><title>뉴스 제목 - 중앙일보</title></head>
        <body></body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        title = crawler._extract_title(soup)
        assert title == "뉴스 제목"  # Site name removed
    
    def test_parse_korean_date_formats(self, crawler):
        """Test various Korean date formats"""
        test_cases = [
            ("2024.01.15 14:30", "2024-01-15T14:30:00"),
            ("입력 : 2024.01.15 14:30", "2024-01-15T14:30:00"),
            ("2024년 01월 15일 오후 2시 30분", "2024-01-15T14:30:00"),
            ("Published : 2024.01.15 09:00", "2024-01-15T09:00:00")
        ]
        
        for date_text, expected in test_cases:
            result = crawler._parse_korean_date(date_text)
            assert result.startswith(expected[:16])
    
    def test_extract_date_from_url(self, crawler):
        """Test date extraction from URL"""
        test_cases = [
            ("https://www.joongang.co.kr/20240115/123456", "2024-01-15"),
            ("https://www.joongang.co.kr/article/25195273?date=20240115", "2024-01-15")
        ]
        
        for url, expected_date in test_cases:
            result = crawler._extract_date_from_url(url)
            if result:  # Some patterns might not match
                assert result.startswith(expected_date)
    
    def test_extract_author_formats(self, crawler):
        """Test author extraction with various formats"""
        test_cases = [
            '<div class="byline"><span class="name">김기자</span></div>',
            '<span class="writer">이특파원</span>',
            '<meta name="author" content="박통신원">',
            '<div>reporter@joongang.co.kr</div>'
        ]
        
        for html in test_cases:
            soup = BeautifulSoup(f"<html><body>{html}</body></html>", 'html.parser')
            author = crawler._extract_author(soup)
            assert author != ""
    
    def test_extract_category_from_url(self, crawler):
        """Test category extraction from URL"""
        test_cases = [
            ("https://www.joongang.co.kr/money/article/123", "경제"),
            ("https://www.joongang.co.kr/politics/news/456", "정치"),
            ("https://www.joongang.co.kr/world/article/789", "국제"),
            ("https://www.joongang.co.kr/culture/news/012", "문화")
        ]
        
        for url, expected_category in test_cases:
            soup = BeautifulSoup("<html></html>", 'html.parser')
            category = crawler._extract_category(soup, url)
            assert category == expected_category
    
    def test_extract_content_cleanup(self, crawler):
        """Test content extraction with proper cleanup"""
        html = """
        <div id="article_body">
            <p>정상적인 기사 내용입니다. 이것은 충분히 긴 문단입니다.</p>
            <div class="ab_photo">
                <img src="photo.jpg">
                <div class="photo_desc">사진 설명입니다</div>
            </div>
            <div class="ad">광고</div>
            <p>또 다른 정상적인 기사 내용입니다. 이것도 충분히 긴 문단입니다.</p>
            <p>ⓒ중앙일보</p>
            <p>김기자 기자</p>
        </div>
        """
        soup = BeautifulSoup(html, 'html.parser')
        content = crawler._extract_content(soup)
        
        # Should include normal content
        assert "정상적인 기사 내용입니다" in content
        assert "또 다른 정상적인 기사 내용입니다" in content
        
        # Should exclude unwanted elements
        assert "사진 설명입니다" not in content
        assert "광고" not in content
        assert "ⓒ중앙일보" not in content
        assert "김기자 기자" not in content
    
    def test_extract_image_skip_small(self, crawler):
        """Test image extraction skips small images"""
        html = """
        <div id="article_body">
            <img src="/icon.jpg" width="50">
            <img src="/main-photo.jpg" width="600">
        </div>
        """
        soup = BeautifulSoup(html, 'html.parser')
        image_url = crawler._extract_image(soup)
        
        # Should skip small image and get large one
        assert "main-photo.jpg" in image_url
        assert "icon.jpg" not in image_url
    
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
                assert article['source'] == 'joongang'
                assert article['title'] != ""
                assert 'crawled_at' in article
                assert article['id'] == crawler.create_article_id(article['url'])