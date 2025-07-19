"""
Reuters RSS Crawler
"""
import logging
from typing import Dict, Any
from bs4 import BeautifulSoup

from ..rss_crawler import RSSCrawler

logger = logging.getLogger(__name__)


class ReutersCrawler(RSSCrawler):
    """Reuters news crawler using RSS feed"""
    
    def __init__(self):
        super().__init__(
            source_id='reuters',
            rss_url='https://www.reuters.com/tools/rss',
            base_url='https://www.reuters.com',
            rate_limit=1.0,  # 1 request per second
            timeout=45,
            max_retries=3
        )
        
        # Reuters specific RSS feeds
        self.category_feeds = {
            'business': 'https://www.reuters.com/news/archive/businessnews.xml',
            'technology': 'https://www.reuters.com/news/archive/technologynews.xml',
            'markets': 'https://www.reuters.com/news/archive/marketsNews.xml',
            'world': 'https://www.reuters.com/news/archive/worldnews.xml',
            'politics': 'https://www.reuters.com/news/archive/politicsnews.xml'
        }
        
        # Use business feed as primary
        self.rss_url = self.category_feeds['business']
    
    async def parse_article(self, url: str, html: str) -> Dict[str, Any]:
        """Parse Reuters article content"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Reuters specific selectors
            title = self._extract_reuters_title(soup)
            content = self._extract_reuters_content(soup)
            summary = self._extract_reuters_summary(soup)
            author = self._extract_reuters_author(soup)
            published_at = self._extract_reuters_date(soup)
            category = self._extract_reuters_category(soup)
            tags = self._extract_reuters_tags(soup)
            image_url = self._extract_reuters_image(soup)
            
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
                    'parsing_method': 'reuters_rss_crawler',
                    'source_type': 'international_news',
                    'language': 'en'
                }
            }
            
            return article_data
            
        except Exception as e:
            logger.exception(f"Error parsing Reuters article {url}: {e}")
            raise
    
    def _extract_reuters_title(self, soup: BeautifulSoup) -> str:
        """Extract Reuters article title"""
        # Reuters specific title selectors
        title_selectors = [
            'h1[data-testid="Heading"]',
            'h1.ArticleHeader_headline',
            'h1.article-heading',
            'h1',
            '[data-testid="headline"]'
        ]
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                if title and len(title) > 5:
                    return title
        
        # Fallback to meta title
        return self._extract_title(soup)
    
    def _extract_reuters_content(self, soup: BeautifulSoup) -> str:
        """Extract Reuters article content"""
        # Reuters specific content selectors
        content_selectors = [
            '[data-testid="paragraph"]',
            '.ArticleBody_container',
            '.article-body',
            '.StandardArticleBody_body'
        ]
        
        content_parts = []
        for selector in content_selectors:
            elements = soup.select(selector)
            for elem in elements:
                # Skip unwanted elements
                for unwanted in elem.select('.ad, .advertisement, .social, .related'):
                    unwanted.decompose()
                
                text = elem.get_text(separator=' ', strip=True)
                if text and len(text) > 20:
                    content_parts.append(text)
        
        if content_parts:
            return ' '.join(content_parts)
        
        # Fallback to base method
        return self._extract_content(soup)
    
    def _extract_reuters_summary(self, soup: BeautifulSoup) -> str:
        """Extract Reuters article summary"""
        # Try Reuters specific summary elements
        summary_selectors = [
            '[data-testid="Paragraph-0"]',
            '.ArticleLede_container',
            '.article-lede'
        ]
        
        for selector in summary_selectors:
            summary_elem = soup.select_one(selector)
            if summary_elem:
                summary = summary_elem.get_text(strip=True)
                if summary and len(summary) > 20:
                    return summary[:300] + '...' if len(summary) > 300 else summary
        
        # Fallback to base method
        return self._extract_summary(soup)
    
    def _extract_reuters_author(self, soup: BeautifulSoup) -> str:
        """Extract Reuters author information"""
        # Reuters specific author selectors
        author_selectors = [
            '[data-testid="authors"]',
            '.ArticleHeader_byline',
            '.author-name',
            '.byline-name'
        ]
        
        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                author = author_elem.get_text(strip=True)
                # Clean up author text
                author = author.replace('By ', '').strip()
                if author and len(author) > 1:
                    return author
        
        # Fallback to base method
        return self._extract_author(soup)
    
    def _extract_reuters_date(self, soup: BeautifulSoup) -> str:
        """Extract Reuters published date"""
        # Reuters specific date selectors
        date_selectors = [
            '[data-testid="timestamp"]',
            '.ArticleHeader_date',
            'time[datetime]',
            '.date-time'
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
    
    def _extract_reuters_category(self, soup: BeautifulSoup) -> str:
        """Extract Reuters category"""
        # Reuters specific category selectors
        category_selectors = [
            '[data-testid="breadcrumb"] a',
            '.breadcrumb a',
            '.section-name'
        ]
        
        for selector in category_selectors:
            cat_elems = soup.select(selector)
            if cat_elems and len(cat_elems) > 1:  # Skip home breadcrumb
                category = cat_elems[1].get_text(strip=True)
                if category and category.lower() != 'home':
                    return category
        
        # Default category for Reuters
        return "Business"
    
    def _extract_reuters_tags(self, soup: BeautifulSoup) -> list:
        """Extract Reuters tags"""
        tags = []
        
        # Reuters specific tag selectors
        tag_selectors = [
            '[data-testid="topic-tag"]',
            '.topic-tag',
            '.article-tags a'
        ]
        
        for selector in tag_selectors:
            tag_elements = soup.select(selector)
            for elem in tag_elements:
                tag = elem.get_text(strip=True)
                if tag and tag not in tags:
                    tags.append(tag)
        
        # Add default tags for Reuters
        if not tags:
            tags = ['Reuters', 'International', 'Business News']
        
        return tags[:10]
    
    def _extract_reuters_image(self, soup: BeautifulSoup) -> str:
        """Extract Reuters featured image"""
        # Reuters specific image selectors
        image_selectors = [
            '[data-testid="Image"] img',
            '.media-img img',
            '.article-media img',
            'figure img'
        ]
        
        for selector in image_selectors:
            img_elem = soup.select_one(selector)
            if img_elem:
                img_src = img_elem.get('src') or img_elem.get('data-src')
                if img_src:
                    return self.normalize_url(img_src)
        
        # Fallback to base method
        return self._extract_image_url(soup)