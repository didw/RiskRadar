"""
Base crawler class for all news crawlers
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import aiohttp
import logging
from urllib.parse import urljoin, urlparse
import time
from collections import defaultdict

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter to prevent overwhelming news servers"""
    
    def __init__(self, requests_per_second: float = 1.0):
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = defaultdict(float)
    
    async def wait_if_needed(self, domain: str):
        """Wait if necessary to maintain rate limit"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time[domain]
        
        if elapsed < self.min_interval:
            wait_time = self.min_interval - elapsed
            logger.debug(f"Rate limiting: waiting {wait_time:.2f}s for {domain}")
            await asyncio.sleep(wait_time)
        
        self.last_request_time[domain] = time.time()


class BaseCrawler(ABC):
    """Base class for all news crawlers"""
    
    def __init__(self, source_id: str, base_url: str, 
                 rate_limit: float = 1.0, timeout: int = 30,
                 max_retries: int = 3):
        self.source_id = source_id
        self.base_url = base_url
        self.rate_limiter = RateLimiter(requests_per_second=rate_limit)
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self.session: Optional[aiohttp.ClientSession] = None
        self.headers = {
            'User-Agent': 'RiskRadar/1.0 (News Monitoring System; +https://riskradar.ai/bot)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'DNT': '1'
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=self.timeout,
            headers=self.headers
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def fetch_page(self, url: str, **kwargs) -> str:
        """Fetch a page with rate limiting, retries, and error handling"""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")
        
        domain = urlparse(url).netloc
        
        for attempt in range(self.max_retries):
            try:
                await self.rate_limiter.wait_if_needed(domain)
                
                async with self.session.get(url, **kwargs) as response:
                    response.raise_for_status()
                    content = await response.text()
                    logger.info(f"Fetched {url} - Status: {response.status}")
                    return content
                    
            except aiohttp.ClientResponseError as e:
                if e.status == 429:  # Too Many Requests
                    wait_time = min(60 * (2 ** attempt), 300)  # Exponential backoff, max 5 min
                    logger.warning(f"Rate limited on {url}, waiting {wait_time}s")
                    await asyncio.sleep(wait_time)
                elif e.status >= 500 and attempt < self.max_retries - 1:
                    wait_time = 5 * (attempt + 1)
                    logger.warning(f"Server error {e.status} on {url}, retry {attempt + 1}/{self.max_retries} after {wait_time}s")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"HTTP error {e.status} fetching {url}: {e}")
                    raise
            except aiohttp.ClientError as e:
                if attempt < self.max_retries - 1:
                    wait_time = 2 * (attempt + 1)
                    logger.warning(f"Network error on {url}, retry {attempt + 1}/{self.max_retries} after {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Failed to fetch {url} after {self.max_retries} attempts: {e}")
                    raise
            except Exception as e:
                logger.exception(f"Unexpected error fetching {url}: {e}")
                raise
    
    def normalize_url(self, url: str) -> str:
        """Normalize URL to absolute form"""
        if url.startswith(('http://', 'https://')):
            return url
        return urljoin(self.base_url, url)
    
    def create_article_id(self, url: str) -> str:
        """Create unique article ID from URL"""
        import hashlib
        # Include source_id to ensure uniqueness across sources
        id_string = f"{self.source_id}:{url}"
        return hashlib.sha256(id_string.encode()).hexdigest()[:16]
    
    def normalize_article(self, raw_article: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize article data to standard format"""
        # Ensure required fields
        required_fields = ['title', 'url']
        for field in required_fields:
            if field not in raw_article or not raw_article[field]:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate title length
        title = raw_article['title'].strip()
        if len(title) < 5:
            raise ValueError(f"Title too short: {title}")
        
        # Normalize URL
        normalized_url = self.normalize_url(raw_article['url'])
        
        # Validate and normalize content
        content = raw_article.get('content', '').strip()
        if content and len(content) < 50:
            logger.warning(f"Content suspiciously short for {normalized_url}: {len(content)} chars")
        
        # Ensure published_at is valid ISO format
        published_at = raw_article.get('published_at', '')
        if not published_at:
            published_at = datetime.now().isoformat()
        else:
            try:
                # Validate ISO format
                datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            except ValueError:
                logger.warning(f"Invalid published_at format: {published_at}, using current time")
                published_at = datetime.now().isoformat()
        
        # Create standardized article
        normalized_article = {
            'id': raw_article.get('id', self.create_article_id(normalized_url)),
            'title': title,
            'content': content,
            'summary': raw_article.get('summary', '').strip(),
            'source': self.source_id,
            'url': normalized_url,
            'published_at': published_at,
            'crawled_at': datetime.now().isoformat(),
            'author': raw_article.get('author', '').strip(),
            'category': raw_article.get('category', '').strip(),
            'tags': [tag.strip() for tag in raw_article.get('tags', []) if tag.strip()],
            'image_url': self.normalize_url(raw_article.get('image_url', '')) if raw_article.get('image_url') else '',
            'metadata': raw_article.get('metadata', {})
        }
        
        return normalized_article
    
    def to_kafka_message(self, article_data: Dict[str, Any]):
        """기사 데이터를 Kafka 메시지로 변환"""
        from ..kafka.producer import NewsMessage
        
        # images 배열 생성
        images = []
        if article_data.get('image_url'):
            images = [article_data['image_url']]
        
        return NewsMessage(
            id=article_data['id'],
            title=article_data['title'],
            content=article_data['content'],
            source=article_data['source'],
            url=article_data['url'],
            published_at=article_data['published_at'],
            crawled_at=article_data['crawled_at'],
            summary=article_data.get('summary'),
            author=article_data.get('author'),
            category=article_data.get('category'),
            tags=article_data.get('tags'),
            images=images,
            metadata=article_data.get('metadata')
        )
    
    @abstractmethod
    async def fetch_article_list(self) -> List[str]:
        """
        Fetch list of article URLs to crawl
        Must be implemented by each crawler
        """
        pass
    
    @abstractmethod
    async def parse_article(self, url: str, html: str) -> Dict[str, Any]:
        """
        Parse article content from HTML
        Must be implemented by each crawler
        Returns dict with at least: title, content, url, published_at
        """
        pass
    
    async def fetch_articles(self, max_articles: Optional[int] = None) -> List[Dict[str, Any]]:
        """Main method to fetch and parse articles"""
        try:
            # Get article URLs
            article_urls = await self.fetch_article_list()
            logger.info(f"Found {len(article_urls)} articles from {self.source_id}")
            
            # Validate URLs
            valid_urls = []
            for url in article_urls:
                if self._is_valid_article_url(url):
                    valid_urls.append(url)
                else:
                    logger.warning(f"Skipping invalid URL: {url}")
            
            # Limit number of articles if specified
            if max_articles:
                valid_urls = valid_urls[:max_articles]
            
            # Fetch and parse each article
            articles = []
            errors = 0
            for i, url in enumerate(valid_urls):
                try:
                    logger.debug(f"Processing article {i+1}/{len(valid_urls)}: {url}")
                    html = await self.fetch_page(url)
                    
                    # Basic HTML validation
                    if len(html) < 1000:
                        logger.warning(f"HTML too short for {url}: {len(html)} chars")
                        continue
                    
                    raw_article = await self.parse_article(url, html)
                    normalized_article = self.normalize_article(raw_article)
                    articles.append(normalized_article)
                    
                except ValueError as e:
                    logger.warning(f"Validation error for article {url}: {e}")
                    errors += 1
                except Exception as e:
                    logger.error(f"Error processing article {url}: {e}")
                    errors += 1
                    if errors > len(valid_urls) * 0.5:  # If more than 50% fail, something's wrong
                        logger.error(f"Too many errors ({errors}/{len(valid_urls)}), stopping crawl")
                        break
            
            logger.info(f"Successfully crawled {len(articles)}/{len(valid_urls)} articles from {self.source_id}")
            return articles
            
        except Exception as e:
            logger.exception(f"Error in fetch_articles for {self.source_id}: {e}")
            raise
    
    def _is_valid_article_url(self, url: str) -> bool:
        """Validate if URL is likely an article URL"""
        if not url or not isinstance(url, str):
            return False
        
        # Check URL format
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False
        
        # Skip common non-article paths
        skip_patterns = [
            '/search', '/login', '/register', '/admin',
            '.pdf', '.jpg', '.png', '.gif', '.zip',
            '/advertisement', '/ads/', '/subscribe'
        ]
        
        lower_url = url.lower()
        for pattern in skip_patterns:
            if pattern in lower_url:
                return False
        
        return True
    
    async def test_connection(self) -> bool:
        """Test connection to the news source"""
        try:
            await self.fetch_page(self.base_url)
            return True
        except Exception as e:
            logger.error(f"Connection test failed for {self.source_id}: {e}")
            return False