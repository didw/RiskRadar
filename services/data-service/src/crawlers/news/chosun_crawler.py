"""
Chosun Ilbo news crawler implementation
"""
from typing import List, Dict, Any
from datetime import datetime
import re
from bs4 import BeautifulSoup
import logging
from ..base_crawler import BaseCrawler

logger = logging.getLogger(__name__)


class ChosunCrawler(BaseCrawler):
    """Crawler for Chosun Ilbo news articles"""
    
    def __init__(self):
        super().__init__(
            source_id="chosun",
            base_url="https://www.chosun.com",
            rate_limit=0.5,  # 2 seconds between requests
            timeout=30,
            max_retries=3
        )
        self.section_urls = [
            "/economy/",
            "/national/",
            "/international/",
            "/politics/",
            "/it/",
            "/culture/"
        ]
        # Chosun-specific selectors based on actual site structure
        self.selectors = {
            'article_links': [
                'div.story_list ul li a',
                'div.news_box a.news_tit',
                'section.article-list a',
                'ul.list_item li a'
            ],
            'title': [
                'header.article-header h1',
                'div.article_title h1',
                'h1.news-title',
                'meta[property="og:title"]'
            ],
            'content': [
                'section.article-body',
                'div.article_body',
                'div.par',
                'div[itemprop="articleBody"]'
            ]
        }
    
    async def fetch_article_list(self) -> List[str]:
        """Fetch list of article URLs from Chosun Ilbo main sections"""
        article_urls = set()  # Use set for automatic deduplication
        
        for section in self.section_urls:
            try:
                section_url = self.normalize_url(section)
                html = await self.fetch_page(section_url)
                soup = BeautifulSoup(html, 'html.parser')
                
                # Find article links using predefined selectors
                article_links = []
                
                for selector in self.selectors['article_links']:
                    elements = soup.select(selector)
                    for element in elements:
                        href = element.get('href')
                        if href:
                            # Check if it's likely an article URL
                            if self._is_article_url(href):
                                article_links.append(href)
                
                # Also check for data attributes that might contain URLs
                for element in soup.find_all(attrs={'data-href': True}):
                    href = element.get('data-href')
                    if href and self._is_article_url(href):
                        article_links.append(href)
                
                # Normalize and add to set
                for link in article_links:
                    normalized_url = self.normalize_url(link)
                    article_urls.add(normalized_url)
                
                logger.info(f"Found {len(article_links)} articles in {section}")
                
            except Exception as e:
                logger.error(f"Error fetching section {section}: {e}")
                continue
        
        # Convert to list and sort by URL (newest articles often have higher IDs)
        sorted_urls = sorted(list(article_urls), reverse=True)
        logger.info(f"Total unique articles found: {len(sorted_urls)}")
        
        return sorted_urls[:50]  # Limit to 50 most recent articles
    
    def _is_article_url(self, url: str) -> bool:
        """Check if URL is likely an article"""
        if not url:
            return False
        
        # Positive patterns for Chosun articles
        article_patterns = [
            '/news/',
            '/article/',
            '/view/',
            r'/\d{4}/\d{2}/\d{2}/',  # Date pattern
            r'[?&]aid=\d+',  # Article ID parameter
        ]
        
        # Negative patterns to exclude
        exclude_patterns = [
            '/photo/',
            '/cartoon/',
            '/multimedia/',
            '/search/',
            '/member/',
            '#',
            'javascript:'
        ]
        
        url_lower = url.lower()
        
        # Check exclusions first
        for pattern in exclude_patterns:
            if pattern in url_lower:
                return False
        
        # Check if matches article patterns
        for pattern in article_patterns:
            if pattern in url or re.search(pattern, url):
                return True
        
        return False
    
    async def parse_article(self, url: str, html: str) -> Dict[str, Any]:
        """Parse Chosun Ilbo article content"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract title
        title = self._extract_title(soup)
        
        # Extract content
        content = self._extract_content(soup)
        
        # Extract published date
        published_at = self._extract_published_date(soup)
        
        # Extract author
        author = self._extract_author(soup)
        
        # Extract category
        category = self._extract_category(soup, url)
        
        # Extract image
        image_url = self._extract_image(soup)
        
        # Extract summary/description
        summary = self._extract_summary(soup)
        
        return {
            'url': url,
            'title': title,
            'content': content,
            'summary': summary,
            'published_at': published_at,
            'author': author,
            'category': category,
            'image_url': image_url,
            'tags': self._extract_tags(soup),
            'metadata': {
                'source_name': '조선일보',
                'language': 'ko',
                'scraped_at': datetime.now().isoformat()
            }
        }
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract article title"""
        # Try multiple selectors
        selectors = [
            'h1.article-title',
            'h1#article_title',
            'div.article_header h1',
            'meta[property="og:title"]'
        ]
        
        for selector in selectors:
            if selector.startswith('meta'):
                meta = soup.select_one(selector)
                if meta and meta.get('content'):
                    return meta['content'].strip()
            else:
                element = soup.select_one(selector)
                if element:
                    return element.get_text(strip=True)
        
        # Fallback to page title
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text(strip=True)
            # Remove site name suffix if present
            title = re.sub(r'\s*[-|]\s*조선일보.*$', '', title)
            return title
        
        return ""
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract article content"""
        # Use predefined selectors
        for selector in self.selectors['content']:
            content_div = soup.select_one(selector)
            if content_div:
                # Clone to avoid modifying original
                content_div = content_div.__copy__()
                
                # Remove unwanted elements
                for tag in content_div(['script', 'style', 'iframe', 'video']):
                    tag.decompose()
                
                # Remove ads and related content
                for ad in content_div.select('.ad, .advertisement, .related-articles, .share-buttons'):
                    ad.decompose()
                
                # Get text from paragraphs
                paragraphs = content_div.find_all(['p', 'div'], recursive=True)
                content_parts = []
                seen_texts = set()  # Avoid duplicate paragraphs
                
                for p in paragraphs:
                    # Skip if it has nested block elements (likely a container)
                    if p.find(['p', 'div', 'h1', 'h2', 'h3']):
                        continue
                    
                    text = p.get_text(separator=' ', strip=True)
                    # Filter out short texts and duplicates
                    if text and len(text) > 30 and text not in seen_texts:
                        content_parts.append(text)
                        seen_texts.add(text)
                
                if content_parts:
                    return '\n\n'.join(content_parts)
        
        # Fallback: try to extract from script tags (some sites use JSON-LD)
        json_ld = soup.find('script', type='application/ld+json')
        if json_ld:
            try:
                import json
                data = json.loads(json_ld.string)
                if isinstance(data, dict) and 'articleBody' in data:
                    return data['articleBody']
            except:
                pass
        
        # Last resort: get all paragraphs
        all_paragraphs = soup.find_all('p')
        content = '\n\n'.join(
            p.get_text(strip=True) for p in all_paragraphs 
            if p.get_text(strip=True) and len(p.get_text(strip=True)) > 50
        )
        
        return content
    
    def _extract_published_date(self, soup: BeautifulSoup) -> str:
        """Extract published date"""
        # Try meta tags first
        meta_selectors = [
            'meta[property="article:published_time"]',
            'meta[name="article:published_time"]',
            'meta[property="datePublished"]',
            'meta[name="publish_date"]'
        ]
        
        for selector in meta_selectors:
            meta_tag = soup.select_one(selector)
            if meta_tag and meta_tag.get('content'):
                return self._normalize_date(meta_tag['content'])
        
        # Try common date selectors
        date_selectors = [
            'time[datetime]',
            'span.date',
            'div.article_date',
            'span.article-date',
            'div.news_date',
            'span.created',
            'p.date'
        ]
        
        for selector in date_selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'time' and element.get('datetime'):
                    return self._normalize_date(element['datetime'])
                else:
                    date_text = element.get_text(strip=True)
                    parsed_date = self._parse_korean_date(date_text)
                    if parsed_date:
                        return parsed_date
        
        # Try to find date in URL
        url_date = self._extract_date_from_url(soup.get('url', ''))
        if url_date:
            return url_date
        
        # Default to current time
        return datetime.now().isoformat()
    
    def _normalize_date(self, date_str: str) -> str:
        """Normalize various date formats to ISO format"""
        try:
            # Handle timezone
            if 'T' in date_str and ('+' in date_str or 'Z' in date_str):
                return date_str  # Already in ISO format
            
            # Try parsing common formats
            from dateutil import parser
            dt = parser.parse(date_str)
            return dt.isoformat()
        except:
            return date_str
    
    def _extract_date_from_url(self, url: str) -> str:
        """Extract date from URL if present"""
        # Pattern: /2024/01/15/ or /20240115/
        patterns = [
            r'/(\d{4})/(\d{2})/(\d{2})/',
            r'/(\d{8})/',
            r'[?&]date=(\d{8})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                if len(match.groups()) == 3:
                    year, month, day = match.groups()
                elif len(match.groups()) == 1:
                    date_str = match.group(1)
                    if len(date_str) == 8:
                        year, month, day = date_str[:4], date_str[4:6], date_str[6:8]
                    else:
                        continue
                
                try:
                    dt = datetime(int(year), int(month), int(day))
                    return dt.isoformat()
                except:
                    pass
        
        return ""
    
    def _parse_korean_date(self, date_text: str) -> str:
        """Parse Korean date format to ISO format"""
        try:
            # Common patterns: "2024.01.15 14:30", "2024-01-15 14:30"
            patterns = [
                r'(\d{4})\.(\d{1,2})\.(\d{1,2})\s+(\d{1,2}):(\d{1,2})',
                r'(\d{4})-(\d{1,2})-(\d{1,2})\s+(\d{1,2}):(\d{1,2})',
                r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일\s*(\d{1,2}):(\d{1,2})'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, date_text)
                if match:
                    year, month, day, hour, minute = match.groups()
                    dt = datetime(int(year), int(month), int(day), int(hour), int(minute))
                    return dt.isoformat()
        except Exception as e:
            logger.debug(f"Error parsing date {date_text}: {e}")
        
        return ""
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        """Extract article author"""
        author_selectors = [
            'span.author',
            'div.reporter',
            'span.reporter_name',
            'meta[name="author"]'
        ]
        
        for selector in author_selectors:
            if selector.startswith('meta'):
                meta = soup.select_one(selector)
                if meta and meta.get('content'):
                    return meta['content'].strip()
            else:
                element = soup.select_one(selector)
                if element:
                    return element.get_text(strip=True)
        
        # Try to find reporter email pattern
        email_pattern = r'([가-힣]+)\s*기자'
        for text in soup.stripped_strings:
            match = re.search(email_pattern, text)
            if match:
                return match.group(1) + ' 기자'
        
        return ""
    
    def _extract_category(self, soup: BeautifulSoup, url: str) -> str:
        """Extract article category"""
        # From URL
        url_patterns = {
            '/economy/': '경제',
            '/national/': '사회',
            '/international/': '국제',
            '/politics/': '정치',
            '/culture/': '문화',
            '/sports/': '스포츠'
        }
        
        for pattern, category in url_patterns.items():
            if pattern in url:
                return category
        
        # From breadcrumb
        breadcrumb = soup.select_one('nav.breadcrumb, ol.breadcrumb')
        if breadcrumb:
            items = breadcrumb.find_all(['li', 'a'])
            if len(items) > 1:
                return items[1].get_text(strip=True)
        
        # From meta tags
        section_meta = soup.select_one('meta[property="article:section"]')
        if section_meta and section_meta.get('content'):
            return section_meta['content']
        
        return "일반"
    
    def _extract_image(self, soup: BeautifulSoup) -> str:
        """Extract main article image"""
        # Try og:image first
        og_image = soup.select_one('meta[property="og:image"]')
        if og_image and og_image.get('content'):
            return og_image['content']
        
        # Try article image
        img_selectors = [
            'div.article_photo img',
            'figure.article-image img',
            'div.article_body img'
        ]
        
        for selector in img_selectors:
            img = soup.select_one(selector)
            if img and img.get('src'):
                return self.normalize_url(img['src'])
        
        return ""
    
    def _extract_summary(self, soup: BeautifulSoup) -> str:
        """Extract article summary"""
        # Try og:description
        og_desc = soup.select_one('meta[property="og:description"]')
        if og_desc and og_desc.get('content'):
            return og_desc['content'].strip()
        
        # Try meta description
        meta_desc = soup.select_one('meta[name="description"]')
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'].strip()
        
        # Try article subtitle
        subtitle = soup.select_one('h2.subtitle, div.article_subtitle')
        if subtitle:
            return subtitle.get_text(strip=True)
        
        # Generate from content
        content = self._extract_content(soup)
        if content:
            # Take first 200 characters
            summary = content[:200].strip()
            if len(content) > 200:
                summary += '...'
            return summary
        
        return ""
    
    def _extract_tags(self, soup: BeautifulSoup) -> List[str]:
        """Extract article tags/keywords"""
        tags = set()  # Use set to avoid duplicates
        
        # From meta keywords
        keywords_meta = soup.select_one('meta[name="keywords"], meta[property="article:tag"]')
        if keywords_meta and keywords_meta.get('content'):
            raw_tags = keywords_meta['content'].split(',')
            for tag in raw_tags:
                tag = tag.strip()
                if tag and len(tag) > 1 and len(tag) < 50:  # Basic validation
                    tags.add(tag)
        
        # From article tags
        tag_selectors = [
            'a.tag',
            'span.keyword',
            'div.tags a',
            'ul.tag-list li',
            'a[rel="tag"]'
        ]
        
        for selector in tag_selectors:
            tag_elements = soup.select(selector)
            for tag_elem in tag_elements:
                tag_text = tag_elem.get_text(strip=True)
                if tag_text and len(tag_text) > 1 and len(tag_text) < 50:
                    # Remove common prefixes
                    tag_text = re.sub(r'^(#|태그:|Tag:)\s*', '', tag_text)
                    if tag_text:
                        tags.add(tag_text)
        
        # Sort by length (shorter tags are often more relevant)
        sorted_tags = sorted(list(tags), key=len)
        return sorted_tags[:10]  # Limit to 10 tags