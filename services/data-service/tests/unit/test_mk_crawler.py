"""
Unit tests for MKCrawler
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch
from bs4 import BeautifulSoup
from src.crawlers.news.mk_crawler import MKCrawler


class TestMKCrawler:
    """Test MKCrawler functionality"""
    
    @pytest.fixture
    def crawler(self):
        return MKCrawler()
    
    @pytest.fixture
    def sample_article_list_html(self):
        """Sample HTML for article list page"""
        return """
        <html>
        <body>
            <h3 class="article_title">
                <a href="/news/newsRead.php?no=123456">경제 성장 전망</a>
            </h3>
            <dt class="tit">
                <a href="/stock/article/202401151234">주식 시장 분석</a>
            </dt>
            <ul class="article_list">
                <li><a href="/economy/articleV2.php?t=20240115123456">경제 뉴스</a></li>
            </ul>
            <div onclick="viewArticle('/it/news/987654')">
                <h2 class="news_ttl">IT 혁신 소식</h2>
            </div>
            <div data-href="/realestate/article/555555">
                <span>부동산 시장</span>
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
            <title>한국 경제 3% 성장률 달성 전망 - 매일경제</title>
            <meta property="og:title" content="한국 경제 3% 성장률 달성 전망">
            <meta property="og:description" content="올해 한국 경제가 3% 성장을 달성할 것으로 전망된다">
            <meta property="og:image" content="https://file.mk.co.kr/meet/2024/01/image_01.jpg">
            <meta property="article:published_time" content="2024-01-15T10:30:00+09:00">
            <meta name="keywords" content="경제,성장률,GDP,한국은행">
        </head>
        <body>
            <div class="location">
                <a href="/">홈</a>
                <span>경제</span>
                <span>거시경제</span>
            </div>
            <h2 class="news_ttl">한국 경제 3% 성장률 달성 전망</h2>
            <div class="time_area">
                <span class="registration">기사입력 : 2024.01.15 10:30:00</span>
            </div>
            <div class="reporter_area">
                <span>박경제 기자 park@mk.co.kr</span>
            </div>
            <div class="art_txt">
                <p>한국은행이 15일 발표한 경제전망 보고서에 따르면 올해 우리나라 국내총생산(GDP) 성장률이 3%를 달성할 것으로 예상된다.</p>
                <div class="ad_area">광고 영역</div>
                <p>이는 지난해 2.5% 성장률 대비 0.5%포인트 상승한 수치로, 글로벌 경기 회복과 수출 증가가 주요 동력이 될 전망이다.</p>
                <div class="img_caption">사진 설명</div>
                <p>전문가들은 반도체 산업의 회복세와 내수 시장 개선을 긍정적으로 평가하고 있다.</p>
                <div class="copyright">ⓒ 매일경제 & mk.co.kr, 무단전재 및 재배포 금지</div>
            </div>
            <div class="tag_area">
                <a class="hash_tag">#경제성장</a>
                <a class="hash_tag">#GDP</a>
            </div>
        </body>
        </html>
        """
    
    def test_initialization(self, crawler):
        """Test crawler initialization"""
        assert crawler.source_id == "mk"
        assert crawler.base_url == "https://www.mk.co.kr"
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
                'newsRead': any('newsRead.php' in url for url in article_urls),
                'articleV2': any('articleV2.php' in url for url in article_urls),
                'numeric': any('/article/' in url for url in article_urls)
            }
            assert sum(patterns_found.values()) >= 2  # At least 2 patterns
            
            # All URLs should be absolute
            assert all(url.startswith('https://') for url in article_urls)
    
    def test_is_article_url(self, crawler):
        """Test article URL validation"""
        # Valid URLs
        assert crawler._is_article_url("/news/newsRead.php?no=123456")
        assert crawler._is_article_url("/economy/articleV2.php?t=20240115")
        assert crawler._is_article_url("/article/987654321")
        assert crawler._is_article_url("?aid=123456")
        assert crawler._is_article_url("/12345678")  # Long number
        
        # Invalid URLs
        assert not crawler._is_article_url("/premium/special")
        assert not crawler._is_article_url("/gallery/photos")
        assert not crawler._is_article_url("/search?q=test")
        assert not crawler._is_article_url("/member/login")
        assert not crawler._is_article_url("javascript:void(0)")
        assert not crawler._is_article_url("")
    
    @pytest.mark.asyncio
    async def test_parse_article(self, crawler, sample_article_html):
        """Test parsing article content"""
        url = "https://www.mk.co.kr/economy/article/123456"
        article = await crawler.parse_article(url, sample_article_html)
        
        # Verify all fields
        assert article['url'] == url
        assert article['title'] == "한국 경제 3% 성장률 달성 전망"
        assert "한국은행이 15일 발표한" in article['content']
        assert "글로벌 경기 회복과 수출 증가" in article['content']
        assert "광고 영역" not in article['content']  # Ad removed
        assert "사진 설명" not in article['content']  # Caption removed
        assert "무단전재" not in article['content']  # Copyright removed
        assert article['summary'] == "올해 한국 경제가 3% 성장을 달성할 것으로 전망된다"
        assert article['author'] == "박경제 기자"
        assert article['category'] == "경제"
        assert article['image_url'] == "https://file.mk.co.kr/meet/2024/01/image_01.jpg"
        assert article['published_at'].startswith("2024-01-15T10:30:00")
        assert "경제성장" in article['tags']
        assert "GDP" in article['tags']
        assert article['metadata']['source_name'] == '매일경제'
    
    def test_extract_title_cleanup(self, crawler):
        """Test title extraction with cleanup"""
        html = """
        <html>
        <head><title>뉴스 제목 | MK 매일경제</title></head>
        <body></body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        title = crawler._extract_title(soup)
        assert title == "뉴스 제목"  # Site name removed
    
    def test_parse_korean_date_formats(self, crawler):
        """Test various Korean date formats"""
        test_cases = [
            ("2024.01.15 14:30:00", "2024-01-15T14:30:00"),
            ("2024.01.15 14:30", "2024-01-15T14:30:00"),
            ("기사입력 : 2024.01.15 오후 2:30", "2024-01-15T14:30:00"),
            ("2024년 1월 15일", "2024-01-15T00:00:00")
        ]
        
        for date_text, expected in test_cases:
            result = crawler._parse_korean_date(date_text)
            assert result.startswith(expected[:16])
    
    def test_extract_date_from_url(self, crawler):
        """Test date extraction from URL"""
        test_cases = [
            ("https://www.mk.co.kr/news/articleV2.php?t=20240115143000", "2024-01-15T14:30:00"),
            ("https://www.mk.co.kr/news/articleV2.php?t=20240115", "2024-01-15"),
            ("https://www.mk.co.kr/economy/20240115/article", "2024-01-15")
        ]
        
        for url, expected_date in test_cases:
            result = crawler._extract_date_from_url(url)
            if result:
                assert result.startswith(expected_date)
    
    def test_extract_author_with_email(self, crawler):
        """Test author extraction including email pattern"""
        test_cases = [
            '<div class="reporter_area">김기자 기자 kim@mk.co.kr</div>',
            '<span class="reporter">이특파원</span>',
            '<meta name="author" content="박경제 기자">',
            '<p>reporter@mk.co.kr</p>'
        ]
        
        for html in test_cases:
            soup = BeautifulSoup(f"<html><body>{html}</body></html>", 'html.parser')
            author = crawler._extract_author(soup)
            assert author != ""
    
    def test_extract_category_from_url(self, crawler):
        """Test category extraction from URL"""
        test_cases = [
            ("https://www.mk.co.kr/economy/article/123", "경제"),
            ("https://www.mk.co.kr/stock/news/456", "증권"),
            ("https://www.mk.co.kr/realestate/article/789", "부동산"),
            ("https://www.mk.co.kr/it/news/012", "IT")
        ]
        
        for url, expected_category in test_cases:
            soup = BeautifulSoup("<html></html>", 'html.parser')
            category = crawler._extract_category(soup, url)
            assert category == expected_category
    
    def test_extract_content_cleanup(self, crawler):
        """Test content extraction with MK-specific cleanup"""
        html = """
        <div class="art_txt">
            <p>정상적인 기사 내용입니다. 이것은 충분히 긴 문단입니다.</p>
            <div class="art_bottom">기사 하단 정보</div>
            <div class="ad_area">광고</div>
            <p>또 다른 정상적인 기사 내용입니다. 이것도 충분히 긴 문단입니다.</p>
            <div class="img_caption">사진 설명입니다</div>
            <p>ⓒ 매일경제</p>
            <p>김기자 기자</p>
            <p>kim@mk.co.kr</p>
        </div>
        """
        soup = BeautifulSoup(html, 'html.parser')
        content = crawler._extract_content(soup)
        
        # Should include normal content
        assert "정상적인 기사 내용입니다" in content
        assert "또 다른 정상적인 기사 내용입니다" in content
        
        # Should exclude unwanted elements
        assert "기사 하단 정보" not in content
        assert "광고" not in content
        assert "사진 설명입니다" not in content
        assert "ⓒ 매일경제" not in content
        assert "김기자 기자" not in content  # Short signature
        assert "kim@mk.co.kr" not in content  # Email only line
    
    def test_extract_tags_cleanup(self, crawler):
        """Test tag extraction with hashtag cleanup"""
        html = """
        <div class="tag_area">
            <a class="hash_tag">#경제성장</a>
            <a class="hash_tag">#GDP</a>
            <a class="hash_tag">#한국은행</a>
        </div>
        """
        soup = BeautifulSoup(html, 'html.parser')
        tags = crawler._extract_tags(soup)
        
        # Should remove # prefix
        assert "경제성장" in tags
        assert "GDP" in tags
        assert "#경제성장" not in tags  # # removed
    
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
                assert article['source'] == 'mk'
                assert article['title'] != ""
                assert 'crawled_at' in article
                assert article['id'] == crawler.create_article_id(article['url'])