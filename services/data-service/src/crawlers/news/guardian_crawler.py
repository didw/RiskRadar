"""
The Guardian RSS Crawler
"""
import logging
from typing import Dict, Any
from bs4 import BeautifulSoup
import re

from ..rss_crawler import RSSCrawler

logger = logging.getLogger(__name__)


class GuardianCrawler(RSSCrawler):
    """The Guardian news crawler using RSS feed"""
    
    def __init__(self):
        super().__init__(
            source_id='guardian',
            rss_url='https://www.theguardian.com/business/rss',
            base_url='https://www.theguardian.com',
            rate_limit=1.0,  # 1 request per second
            timeout=45,
            max_retries=3
        )
        
        # Guardian specific RSS feeds
        self.category_feeds = {
            'business': 'https://www.theguardian.com/business/rss',
            'technology': 'https://www.theguardian.com/technology/rss',
            'world': 'https://www.theguardian.com/world/rss',
            'politics': 'https://www.theguardian.com/politics/rss',
            'environment': 'https://www.theguardian.com/environment/rss'
        }
    
    async def parse_article(self, url: str, html: str) -> Dict[str, Any]:
        """Parse Guardian article content"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Guardian specific selectors
            title = self._extract_guardian_title(soup)
            content = self._extract_guardian_content(soup)
            summary = self._extract_guardian_summary(soup)
            author = self._extract_guardian_author(soup)
            published_at = self._extract_guardian_date(soup)
            category = self._extract_guardian_category(soup, url)
            tags = self._extract_guardian_tags(soup)
            image_url = self._extract_guardian_image(soup)
            
            if not title:
                raise ValueError("No title found")
            
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
                    'parsing_method': 'guardian_rss_crawler',
                    'source_type': 'international_news',
                    'language': 'en'
                }
            }
            
            return article_data
            
        except Exception as e:
            logger.exception(f"Error parsing Guardian article {url}: {e}")
            raise
    
    def _extract_guardian_title(self, soup: BeautifulSoup) -> str:
        """Extract Guardian article title"""
        # Guardian specific title selectors
        title_selectors = [
            'h1[data-gu-name="headline"]',
            'h1.content__headline',
            'h1',
            '[property="og:title"]'
        ]
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get('content') if title_elem.name == 'meta' else title_elem.get_text()
                if title and len(title.strip()) > 5:
                    return title.strip()
        
        # Fallback to base method
        return self._extract_title(soup)
    
    def _extract_guardian_content(self, soup: BeautifulSoup) -> str:
        """Extract Guardian article content"""
        # Guardian specific content selectors
        content_selectors = [
            '.content__article-body p',
            '.prose p',
            '[data-gu-name="body"] p'
        ]
        
        content_parts = []
        for selector in content_selectors:
            elements = soup.select(selector)
            for elem in elements:
                # Skip unwanted elements
                if any(cls in elem.get('class', []) for cls in ['ad', 'aside', 'pullquote']):
                    continue
                
                text = elem.get_text(separator=' ', strip=True)
                if text and len(text) > 20:
                    content_parts.append(text)
        
        if content_parts:
            return ' '.join(content_parts)
        
        # Alternative Guardian content approach
        article_body = soup.select_one('.content__article-body, .prose')
        if article_body:
            # Remove unwanted elements
            for unwanted in article_body.select('.ad, .aside, .element-rich-link, .submeta'):
                unwanted.decompose()
            
            text = article_body.get_text(separator=' ', strip=True)
            if len(text) > 100:
                return text
        
        # Fallback to base method
        return self._extract_content(soup)
    
    def _extract_guardian_summary(self, soup: BeautifulSoup) -> str:
        """Extract Guardian article summary"""
        # Guardian specific summary elements
        summary_selectors = [
            '.content__standfirst',
            '.standfirst',
            '[data-gu-name="standfirst"]'
        ]
        
        for selector in summary_selectors:
            summary_elem = soup.select_one(selector)
            if summary_elem:
                summary = summary_elem.get_text(strip=True)
                if summary and len(summary) > 20:
                    return summary[:300] + '...' if len(summary) > 300 else summary
        
        # Fallback to base method
        return self._extract_summary(soup)
    
    def _extract_guardian_author(self, soup: BeautifulSoup) -> str:
        """Extract Guardian author information"""
        # Guardian specific author selectors
        author_selectors = [
            '[data-gu-name="meta"] a[rel="author"]',
            '.byline a',
            '.content__meta-byline a',
            '[rel="author"]'
        ]
        
        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                author = author_elem.get_text(strip=True)
                if author and len(author) > 1:
                    return author
        
        # Try author from meta
        author_meta = soup.select_one('meta[name="author"]')
        if author_meta and author_meta.get('content'):
            return author_meta['content'].strip()
        
        # Default to The Guardian
        return "The Guardian"
    
    def _extract_guardian_date(self, soup: BeautifulSoup) -> str:
        """Extract Guardian published date"""
        # Guardian specific date selectors
        date_selectors = [
            'time[datetime]',
            '[data-gu-name="meta"] time',
            '.content__dateline time'
        ]
        
        for selector in date_selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                date_str = date_elem.get('datetime') or date_elem.get_text()
                if date_str:
                    parsed_date = self._parse_date_string(date_str.strip())
                    if parsed_date:
                        return parsed_date
        
        # Fallback to base method
        return self._extract_published_date(soup)
    
    def _extract_guardian_category(self, soup: BeautifulSoup, url: str = "") -> str:
        """Extract Guardian category"""
        # Guardian specific category selectors
        category_selectors = [
            '[data-gu-name="nav2"] a.subnav-link--current',
            '.breadcrumb a',
            '.pillar-link'
        ]
        
        for selector in category_selectors:
            cat_elem = soup.select_one(selector)
            if cat_elem:
                category = cat_elem.get_text(strip=True)
                if category and category.lower() not in ['the guardian', 'home']:
                    return category.title()
        
        # Extract from URL path
        if url:
            if '/business/' in url:
                return "Business"
            elif '/technology/' in url:
                return "Technology"
            elif '/environment/' in url:
                return "Environment"
            elif '/politics/' in url:
                return "Politics"
            elif '/world/' in url:
                return "World"
        
        return "News"
    
    def _extract_guardian_tags(self, soup: BeautifulSoup) -> list:
        """Extract Guardian tags"""
        tags = []
        
        # Guardian specific tag selectors
        tag_selectors = [
            '.submeta__keywords a',
            '.content__tags a',
            '[data-gu-name="keywords"] a'
        ]
        
        for selector in tag_selectors:
            tag_elements = soup.select(selector)
            for elem in tag_elements:
                tag = elem.get_text(strip=True)
                if tag and tag not in tags and len(tag) > 1:
                    tags.append(tag)
        
        # Add default tags for Guardian
        if not tags:
            tags = ['The Guardian', 'International', 'News']
        
        return tags[:10]
    
    def _extract_guardian_image(self, soup: BeautifulSoup) -> str:
        """Extract Guardian featured image"""
        # Guardian specific image selectors
        image_selectors = [
            '.media-primary img',
            '.content__main-picture img',
            'figure.element-image img',
            '.gu-image img'
        ]
        
        for selector in image_selectors:
            img_elem = soup.select_one(selector)
            if img_elem:
                img_src = img_elem.get('src') or img_elem.get('data-src')
                if img_src:
                    return self.normalize_url(img_src)
        
        # Fallback to base method
        return self._extract_image_url(soup)