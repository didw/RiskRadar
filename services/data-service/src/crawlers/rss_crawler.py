"""
RSS-based news crawler
"""
import feedparser
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import time

from .base_crawler import BaseCrawler

logger = logging.getLogger(__name__)


class RSSCrawler(BaseCrawler):
    """RSS-based news crawler for efficient news collection"""
    
    def __init__(self, source_id: str, rss_url: str, base_url: str, 
                 rate_limit: float = 2.0, timeout: int = 30, max_retries: int = 3):
        super().__init__(source_id, base_url, rate_limit, timeout, max_retries)
        self.rss_url = rss_url
        self.feed_parser = feedparser
    
    async def fetch_article_list(self) -> List[str]:
        """Fetch article URLs from RSS feed"""
        try:
            # Fetch RSS feed
            logger.info(f"Fetching RSS feed: {self.rss_url}")
            domain = urlparse(self.rss_url).netloc
            await self.rate_limiter.wait_if_needed(domain)
            
            if not self.session:
                raise RuntimeError("Session not initialized")
            
            async with self.session.get(self.rss_url) as response:
                response.raise_for_status()
                rss_content = await response.text()
            
            # Parse RSS feed
            feed = self.feed_parser.parse(rss_content)
            
            if feed.bozo:
                logger.warning(f"RSS feed may have issues: {feed.bozo_exception}")
            
            # Extract article URLs
            article_urls = []
            for entry in feed.entries:
                url = entry.get('link') or entry.get('id')
                if url:
                    article_urls.append(self.normalize_url(url))
            
            logger.info(f"Found {len(article_urls)} articles in RSS feed from {self.source_id}")
            return article_urls
            
        except Exception as e:
            logger.exception(f"Error fetching RSS feed from {self.rss_url}: {e}")
            raise
    
    async def parse_article(self, url: str, html: str) -> Dict[str, Any]:
        """Parse article content from HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract title
            title = self._extract_title(soup)
            if not title:
                raise ValueError("No title found")
            
            # Extract content
            content = self._extract_content(soup)
            if not content:
                logger.warning(f"No content found for {url}")
                content = ""
            
            # Extract metadata
            summary = self._extract_summary(soup)
            author = self._extract_author(soup)
            published_at = self._extract_published_date(soup)
            category = self._extract_category(soup)
            tags = self._extract_tags(soup)
            image_url = self._extract_image_url(soup)
            
            article_data = {
                'title': title,
                'content': content,
                'summary': summary,
                'url': url,
                'published_at': published_at,
                'author': author,
                'category': category,
                'tags': tags,
                'image_url': image_url,
                'metadata': {
                    'content_length': len(content),
                    'parsing_method': 'rss_crawler'
                }
            }
            
            return article_data
            
        except Exception as e:
            logger.exception(f"Error parsing article {url}: {e}")
            raise
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract article title"""
        # Try multiple selectors
        selectors = [
            'h1',
            '.article-title',
            '.entry-title', 
            '.post-title',
            '[property="og:title"]',
            'title'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                title = element.get('content') if element.name == 'meta' else element.get_text()
                if title and len(title.strip()) > 5:
                    return title.strip()
        
        return ""
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract article content"""
        # Common content selectors
        content_selectors = [
            '.article-content',
            '.entry-content',
            '.post-content',
            '.content',
            'article',
            '.article-body',
            '[property="articleBody"]'
        ]
        
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                # Remove unwanted elements
                for unwanted in content_elem.select('script, style, .advertisement, .ads, .social-share'):
                    unwanted.decompose()
                
                text = content_elem.get_text(separator=' ', strip=True)
                if len(text) > 100:  # Minimum content length
                    return text
        
        # Fallback: extract from body but exclude navigation/footer
        for unwanted in soup.select('nav, footer, header, .menu, .sidebar, .advertisement'):
            unwanted.decompose()
        
        body = soup.find('body')
        if body:
            text = body.get_text(separator=' ', strip=True)
            return text[:5000]  # Limit to prevent too long content
        
        return ""
    
    def _extract_summary(self, soup: BeautifulSoup) -> str:
        """Extract article summary/description"""
        # Try meta description first
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'].strip()
        
        # Try Open Graph description
        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc and og_desc.get('content'):
            return og_desc['content'].strip()
        
        # Try first paragraph
        first_p = soup.find('p')
        if first_p:
            text = first_p.get_text(strip=True)
            if len(text) > 20:
                return text[:200] + '...' if len(text) > 200 else text
        
        return ""
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        """Extract author information"""
        author_selectors = [
            '[rel="author"]',
            '.author',
            '.byline',
            '[property="article:author"]',
            '.post-author'
        ]
        
        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                author = author_elem.get('content') if author_elem.name == 'meta' else author_elem.get_text()
                if author and len(author.strip()) > 1:
                    return author.strip()
        
        return ""
    
    def _extract_published_date(self, soup: BeautifulSoup) -> str:
        """Extract published date"""
        # Try meta tags first
        time_selectors = [
            'meta[property="article:published_time"]',
            'meta[name="date"]',
            'meta[name="publishdate"]',
            'time[datetime]',
            '.published-date',
            '.post-date'
        ]
        
        for selector in time_selectors:
            time_elem = soup.select_one(selector)
            if time_elem:
                date_str = time_elem.get('content') or time_elem.get('datetime') or time_elem.get_text()
                if date_str:
                    try:
                        # Try to parse different date formats
                        parsed_date = self._parse_date_string(date_str.strip())
                        if parsed_date:
                            return parsed_date
                    except Exception:
                        continue
        
        # Fallback to current time
        return datetime.now().isoformat()
    
    def _parse_date_string(self, date_str: str) -> Optional[str]:
        """Parse various date string formats to ISO format"""
        # Common patterns
        patterns = [
            r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})',  # ISO format
            r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})',   # SQL datetime
            r'(\d{4}-\d{2}-\d{2})',                      # Date only
        ]
        
        for pattern in patterns:
            match = re.search(pattern, date_str)
            if match:
                try:
                    dt = datetime.fromisoformat(match.group(1).replace(' ', 'T'))
                    return dt.isoformat()
                except:
                    continue
        
        # Try feedparser's built-in date parsing
        try:
            import time
            parsed_time = feedparser._parse_date(date_str)
            if parsed_time:
                dt = datetime.fromtimestamp(time.mktime(parsed_time))
                return dt.isoformat()
        except:
            pass
        
        return None
    
    def _extract_category(self, soup: BeautifulSoup) -> str:
        """Extract article category"""
        category_selectors = [
            'meta[property="article:section"]',
            '.category',
            '.post-category',
            '[rel="category"]'
        ]
        
        for selector in category_selectors:
            cat_elem = soup.select_one(selector)
            if cat_elem:
                category = cat_elem.get('content') if cat_elem.name == 'meta' else cat_elem.get_text()
                if category and len(category.strip()) > 1:
                    return category.strip()
        
        return ""
    
    def _extract_tags(self, soup: BeautifulSoup) -> List[str]:
        """Extract article tags/keywords"""
        tags = []
        
        # Try meta keywords
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            keywords = [tag.strip() for tag in meta_keywords['content'].split(',')]
            tags.extend([tag for tag in keywords if tag])
        
        # Try article tags
        tag_selectors = [
            '.tags a',
            '.post-tags a',
            '[rel="tag"]'
        ]
        
        for selector in tag_selectors:
            tag_elements = soup.select(selector)
            for elem in tag_elements:
                tag = elem.get_text(strip=True)
                if tag and tag not in tags:
                    tags.append(tag)
        
        return tags[:10]  # Limit number of tags
    
    def _extract_image_url(self, soup: BeautifulSoup) -> str:
        """Extract featured image URL"""
        # Try Open Graph image
        og_image = soup.find('meta', attrs={'property': 'og:image'})
        if og_image and og_image.get('content'):
            return og_image['content']
        
        # Try first image in content
        content_img = soup.select_one('.article-content img, .entry-content img, article img')
        if content_img and content_img.get('src'):
            return self.normalize_url(content_img['src'])
        
        return ""