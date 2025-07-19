"""
BBC News RSS Crawler
"""
import logging
from typing import Dict, Any
from bs4 import BeautifulSoup
import re

from ..rss_crawler import RSSCrawler

logger = logging.getLogger(__name__)


class BBCCrawler(RSSCrawler):
    """BBC News crawler using RSS feed"""
    
    def __init__(self):
        super().__init__(
            source_id='bbc',
            rss_url='http://feeds.bbci.co.uk/news/business/rss.xml',
            base_url='https://www.bbc.com',
            rate_limit=1.5,  # 1.5 requests per second
            timeout=45,
            max_retries=3
        )
        
        # BBC specific RSS feeds
        self.category_feeds = {
            'business': 'http://feeds.bbci.co.uk/news/business/rss.xml',
            'technology': 'http://feeds.bbci.co.uk/news/technology/rss.xml',
            'world': 'http://feeds.bbci.co.uk/news/world/rss.xml',
            'politics': 'http://feeds.bbci.co.uk/news/politics/rss.xml',
            'science': 'http://feeds.bbci.co.uk/news/science_and_environment/rss.xml'
        }
    
    async def parse_article(self, url: str, html: str) -> Dict[str, Any]:
        """Parse BBC article content"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # BBC specific selectors
            title = self._extract_bbc_title(soup)
            content = self._extract_bbc_content(soup)
            summary = self._extract_bbc_summary(soup)
            author = self._extract_bbc_author(soup)
            published_at = self._extract_bbc_date(soup)
            category = self._extract_bbc_category(soup, url)
            tags = self._extract_bbc_tags(soup, url)
            image_url = self._extract_bbc_image(soup)
            
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
                    'parsing_method': 'bbc_rss_crawler',
                    'source_type': 'international_news',
                    'language': 'en'
                }
            }
            
            return article_data
            
        except Exception as e:
            logger.exception(f"Error parsing BBC article {url}: {e}")
            raise
    
    def _extract_bbc_title(self, soup: BeautifulSoup) -> str:
        """Extract BBC article title"""
        # BBC specific title selectors
        title_selectors = [
            'h1[data-testid="headline"]',
            'h1.story-body__h1',
            'h1.gel-trafalgar-bold',
            '.story-headline h1',
            'h1'
        ]
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                if title and len(title) > 5:
                    return title
        
        # Fallback to meta title
        return self._extract_title(soup)
    
    def _extract_bbc_content(self, soup: BeautifulSoup) -> str:
        """Extract BBC article content"""
        # BBC specific content selectors
        content_selectors = [
            '[data-component="text-block"]',
            '.story-body__inner',
            '.gel-body-copy',
            'div[data-module="StoryBodyModule"]'
        ]
        
        content_parts = []
        for selector in content_selectors:
            elements = soup.select(selector)
            for elem in elements:
                # Skip unwanted elements
                for unwanted in elem.select('.ad, .media, .related, .share-tools'):
                    unwanted.decompose()
                
                text = elem.get_text(separator=' ', strip=True)
                if text and len(text) > 20:
                    content_parts.append(text)
        
        if content_parts:
            return ' '.join(content_parts)
        
        # Alternative BBC content selector
        story_body = soup.select_one('.story-body')
        if story_body:
            # Remove unwanted elements
            for unwanted in story_body.select('.media, .related, .share-tools, .story-footer'):
                unwanted.decompose()
            
            paragraphs = story_body.select('p')
            content_parts = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
            if content_parts:
                return ' '.join(content_parts)
        
        # Fallback to base method
        return self._extract_content(soup)
    
    def _extract_bbc_summary(self, soup: BeautifulSoup) -> str:
        """Extract BBC article summary"""
        # Try BBC specific summary elements
        summary_selectors = [
            '[data-component="introduction-block"]',
            '.story-body__introduction',
            '.gel-great-primer-bold'
        ]
        
        for selector in summary_selectors:
            summary_elem = soup.select_one(selector)
            if summary_elem:
                summary = summary_elem.get_text(strip=True)
                if summary and len(summary) > 20:
                    return summary[:300] + '...' if len(summary) > 300 else summary
        
        # Try first paragraph as summary
        first_p = soup.select_one('.story-body p')
        if first_p:
            summary = first_p.get_text(strip=True)
            if len(summary) > 20:
                return summary[:300] + '...' if len(summary) > 300 else summary
        
        # Fallback to base method
        return self._extract_summary(soup)
    
    def _extract_bbc_author(self, soup: BeautifulSoup) -> str:
        """Extract BBC author information"""
        # BBC specific author selectors
        author_selectors = [
            '.qa-contributor-name',
            '.story-body__byline',
            '[data-component="byline-block"]',
            '.gel-minion'
        ]
        
        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                author = author_elem.get_text(strip=True)
                # Clean up author text
                author = re.sub(r'^By\s+', '', author, flags=re.IGNORECASE)
                author = re.sub(r'BBC\s+\w+\s+correspondent', '', author, flags=re.IGNORECASE)
                if author and len(author.strip()) > 1:
                    return author.strip()
        
        # BBC often doesn't show bylines, default to BBC
        return "BBC News"
    
    def _extract_bbc_date(self, soup: BeautifulSoup) -> str:
        """Extract BBC published date"""
        # BBC specific date selectors
        date_selectors = [
            '[data-testid="timestamp"]',
            'time[datetime]',
            '.date',
            '.story-body__mini-info-list-item time'
        ]
        
        for selector in date_selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                date_str = date_elem.get('datetime') or date_elem.get('title') or date_elem.get_text()
                if date_str:
                    parsed_date = self._parse_date_string(date_str.strip())
                    if parsed_date:
                        return parsed_date
        
        # Try to extract from URL if it has date pattern
        date_match = re.search(r'/(\d{4})/(\d{2})/(\d{2})/', url)
        if date_match:
            year, month, day = date_match.groups()
            try:
                from datetime import datetime
                dt = datetime(int(year), int(month), int(day))
                return dt.isoformat()
            except:
                pass
        
        # Fallback to base method
        return self._extract_published_date(soup)
    
    def _extract_bbc_category(self, soup: BeautifulSoup, url: str = "") -> str:
        """Extract BBC category"""
        # BBC specific category selectors
        category_selectors = [
            '.story-body__link-back a',
            '.navigation-wide-list__link',
            '.breadcrumb__link'
        ]
        
        for selector in category_selectors:
            cat_elem = soup.select_one(selector)
            if cat_elem:
                category = cat_elem.get_text(strip=True)
                if category and category.lower() not in ['bbc', 'home']:
                    return category.title()
        
        # Extract from URL path if provided
        if url:
            if '/business/' in url:
                return "Business"
            elif '/technology/' in url:
                return "Technology"
            elif '/science/' in url:
                return "Science"
            elif '/politics/' in url:
                return "Politics"
            elif '/world/' in url:
                return "World"
        
        return "News"
    
    def _extract_bbc_tags(self, soup: BeautifulSoup, url: str = "") -> list:
        """Extract BBC tags"""
        tags = []
        
        # BBC specific tag selectors
        tag_selectors = [
            '.story-body__tags a',
            '.tags-list a',
            '.topic-tags a'
        ]
        
        for selector in tag_selectors:
            tag_elements = soup.select(selector)
            for elem in tag_elements:
                tag = elem.get_text(strip=True)
                if tag and tag not in tags:
                    tags.append(tag)
        
        # Add default tags for BBC
        if not tags:
            tags = ['BBC', 'International', 'News']
            
            # Add category-specific tags based on URL
            if '/business/' in url:
                tags.append('Business')
            elif '/technology/' in url:
                tags.append('Technology')
            elif '/science/' in url:
                tags.append('Science')
        
        return tags[:10]
    
    def _extract_bbc_image(self, soup: BeautifulSoup) -> str:
        """Extract BBC featured image"""
        # BBC specific image selectors
        image_selectors = [
            '.story-body__image img',
            '[data-component="image-block"] img',
            '.media-landscape img',
            'figure img'
        ]
        
        for selector in image_selectors:
            img_elem = soup.select_one(selector)
            if img_elem:
                img_src = img_elem.get('src') or img_elem.get('data-src')
                if img_src:
                    # BBC images might be relative URLs
                    if img_src.startswith('//'):
                        img_src = 'https:' + img_src
                    return self.normalize_url(img_src)
        
        # Fallback to base method
        return self._extract_image_url(soup)