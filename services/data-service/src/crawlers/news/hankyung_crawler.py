"""
Hankyung (Korea Economic Daily) news crawler implementation
"""
from typing import List, Dict, Any
from datetime import datetime
import re
from bs4 import BeautifulSoup
import logging
from ..base_crawler import BaseCrawler

logger = logging.getLogger(__name__)


class HankyungCrawler(BaseCrawler):
    """Crawler for Hankyung (한국경제) news articles"""
    
    def __init__(self):
        super().__init__(
            source_id="hankyung",
            base_url="https://www.hankyung.com",
            rate_limit=0.5,  # 2 seconds between requests
            timeout=30,
            max_retries=3
        )
        self.section_urls = [
            "/economy",
            "/finance", 
            "/industry",
            "/it",
            "/society",
            "/politics",
            "/international"
        ]
        # Hankyung-specific selectors
        self.selectors = {
            'article_links': [
                'div.article_list a.tit',
                'ul.article_list li a',
                'div.newslist a',
                'h3.news_tit a',
                'div.article a'
            ],
            'title': [
                'h1.headline',
                'div.article_tit h1',
                'h1.tit',
                'meta[property="og:title"]'
            ],
            'content': [
                'div#articletxt',
                'div.article_body',
                'div.article_txt',
                'div[itemprop="articleBody"]'
            ],
            'date': [
                'span.date_time',
                'div.date_txt',
                'span.txt_date',
                'time[datetime]',
                'meta[property="article:published_time"]'
            ]
        }
    
    async def fetch_article_list(self) -> List[str]:
        """Fetch list of article URLs from Hankyung sections"""
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
                        if href and self._is_article_url(href):
                            article_links.append(href)
                
                # Also check for onclick attributes (common in Korean news sites)
                for element in soup.find_all(attrs={'onclick': True}):
                    onclick = element.get('onclick', '')
                    url_match = re.search(r"location\.href='([^']+)'", onclick)
                    if url_match:
                        href = url_match.group(1)
                        if self._is_article_url(href):
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
        
        # Positive patterns for Hankyung articles
        article_patterns = [
            r'/article/\d+',
            r'/news/article\.php',
            r'news_id=\d+',
            r'/\d{4}/\d{2}/\d{2}/',
            '/articleView'
        ]
        
        # Negative patterns to exclude
        exclude_patterns = [
            '/opinion/',
            '/photo/',
            '/tv/',
            '/land/',  # Real estate section often has different format
            '/search',
            '/login',
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
            if re.search(pattern, url):
                return True
        
        # Additional check: URLs with numeric IDs are often articles
        if re.search(r'/\d{6,}', url):  # 6+ digit number in URL
            return True
        
        return False
    
    async def parse_article(self, url: str, html: str) -> Dict[str, Any]:
        """Parse Hankyung article content"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract title
        title = self._extract_title(soup)
        if not title:
            logger.warning(f"No title found for {url}")
        
        # Extract content
        content = self._extract_content(soup)
        if not content:
            logger.warning(f"No content found for {url}")
        
        # Extract published date
        published_at = self._extract_published_date(soup, url)
        
        # Extract author
        author = self._extract_author(soup)
        
        # Extract category
        category = self._extract_category(soup, url)
        
        # Extract image
        image_url = self._extract_image(soup)
        
        # Extract summary
        summary = self._extract_summary(soup, content)
        
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
                'source_name': '한국경제',
                'language': 'ko',
                'scraped_at': datetime.now().isoformat()
            }
        }
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract article title"""
        # Try predefined selectors
        for selector in self.selectors['title']:
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
            # Remove site name suffix
            title = re.sub(r'\s*[-|]\s*한국경제.*$', '', title)
            title = re.sub(r'\s*[-|]\s*한경.*$', '', title)
            return title
        
        return ""
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract article content"""
        # Try predefined selectors
        for selector in self.selectors['content']:
            content_div = soup.select_one(selector)
            if content_div:
                # Clone to avoid modifying original
                content_div = content_div.__copy__()
                
                # Remove unwanted elements
                for tag in content_div(['script', 'style', 'iframe', 'video']):
                    tag.decompose()
                
                # Remove ads and related content
                for unwanted in content_div.select('.ad, .advertisement, .related_news, .copyright'):
                    unwanted.decompose()
                
                # Get text from paragraphs
                paragraphs = []
                seen_texts = set()
                
                # Try to find paragraphs
                for p in content_div.find_all(['p', 'div'], recursive=True):
                    # Skip if it has nested block elements
                    if p.find(['p', 'div', 'h1', 'h2', 'h3']):
                        continue
                    
                    text = p.get_text(separator=' ', strip=True)
                    # Filter out short texts and duplicates
                    if text and len(text) > 30 and text not in seen_texts:
                        # Skip common footer texts
                        if any(skip in text for skip in ['기자', '저작권', 'Copyright']):
                            if len(text) < 100:  # Short texts with these words are often signatures
                                continue
                        paragraphs.append(text)
                        seen_texts.add(text)
                
                if paragraphs:
                    return '\n\n'.join(paragraphs)
        
        # Fallback: get all text nodes
        all_text = []
        for p in soup.find_all('p'):
            text = p.get_text(strip=True)
            if text and len(text) > 50:
                all_text.append(text)
        
        return '\n\n'.join(all_text)
    
    def _extract_published_date(self, soup: BeautifulSoup, url: str) -> str:
        """Extract published date"""
        # Try predefined date selectors
        for selector in self.selectors['date']:
            if selector.startswith('meta'):
                meta = soup.select_one(selector)
                if meta and meta.get('content'):
                    return self._normalize_date(meta['content'])
            else:
                element = soup.select_one(selector)
                if element:
                    if element.name == 'time' and element.get('datetime'):
                        return self._normalize_date(element['datetime'])
                    else:
                        date_text = element.get_text(strip=True)
                        parsed_date = self._parse_korean_date(date_text)
                        if parsed_date:
                            return parsed_date
        
        # Try to extract from URL
        url_date = self._extract_date_from_url(url)
        if url_date:
            return url_date
        
        # Try to find date in text
        date_pattern = r'(\d{4})\.(\d{1,2})\.(\d{1,2})\s+(\d{1,2}):(\d{1,2})'
        for text in soup.stripped_strings:
            match = re.search(date_pattern, text)
            if match:
                parsed = self._parse_korean_date(text)
                if parsed:
                    return parsed
        
        # Default to current time
        return datetime.now().isoformat()
    
    def _normalize_date(self, date_str: str) -> str:
        """Normalize various date formats to ISO format"""
        try:
            # If already in ISO format with timezone, keep it
            if 'T' in date_str and ('+' in date_str or 'Z' in date_str):
                return date_str
            
            # Try parsing with dateutil
            from dateutil import parser
            dt = parser.parse(date_str)
            
            # If timezone aware, convert to ISO with timezone
            if dt.tzinfo is not None:
                return dt.isoformat()
            else:
                # If no timezone, return without timezone
                return dt.isoformat()
        except:
            return date_str
    
    def _extract_date_from_url(self, url: str) -> str:
        """Extract date from URL if present"""
        # Patterns: /2024/01/15/, article/202401151234
        patterns = [
            r'/(\d{4})/(\d{2})/(\d{2})/',
            r'article/(\d{4})(\d{2})(\d{2})',
            r'[?&]date=(\d{8})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                try:
                    if len(match.groups()) == 3:
                        year, month, day = match.groups()
                    elif len(match.groups()) == 1:
                        date_str = match.group(1)
                        year, month, day = date_str[:4], date_str[4:6], date_str[6:8]
                    else:
                        continue
                    
                    dt = datetime(int(year), int(month), int(day))
                    return dt.isoformat()
                except:
                    pass
        
        return ""
    
    def _parse_korean_date(self, date_text: str) -> str:
        """Parse Korean date format to ISO format"""
        try:
            # Remove extra spaces
            date_text = ' '.join(date_text.split())
            
            # Common patterns
            patterns = [
                # 2024.01.15 14:30:00
                (r'(\d{4})\.(\d{1,2})\.(\d{1,2})\s+(\d{1,2}):(\d{1,2}):(\d{1,2})', 6),
                # 2024.01.15 14:30
                (r'(\d{4})\.(\d{1,2})\.(\d{1,2})\s+(\d{1,2}):(\d{1,2})', 5),
                # 2024-01-15 14:30
                (r'(\d{4})-(\d{1,2})-(\d{1,2})\s+(\d{1,2}):(\d{1,2})', 5),
                # 2024년 1월 15일 오후 2:30
                (r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일.*?(\d{1,2}):(\d{1,2})', 5),
                # 입력 2024.01.15 14:30
                (r'입력\s*(\d{4})\.(\d{1,2})\.(\d{1,2})\s+(\d{1,2}):(\d{1,2})', 5)
            ]
            
            for pattern, group_count in patterns:
                match = re.search(pattern, date_text)
                if match:
                    groups = match.groups()
                    year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                    
                    if group_count >= 5:
                        hour, minute = int(groups[3]), int(groups[4])
                        # Handle 오후/PM
                        if '오후' in date_text and hour < 12:
                            hour += 12
                        second = int(groups[5]) if group_count == 6 else 0
                        dt = datetime(year, month, day, hour, minute, second)
                    else:
                        dt = datetime(year, month, day)
                    
                    return dt.isoformat()
        except Exception as e:
            logger.debug(f"Error parsing date {date_text}: {e}")
        
        return ""
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        """Extract article author"""
        author_selectors = [
            'span.reporter',
            'div.reporter_info',
            'p.reporter',
            'span.name',
            'div.byline',
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
                    author_text = element.get_text(strip=True)
                    # Clean up author text
                    author_text = re.sub(r'\s+기자.*$', ' 기자', author_text)
                    return author_text
        
        # Try to find reporter email/name pattern
        patterns = [
            r'([가-힣]+)\s*기자',
            r'([가-힣]+)\s*특파원',
            r'기자\s*([가-힣]+)',
            r'([a-zA-Z0-9_.]+@hankyung\.com)'
        ]
        
        for text in soup.stripped_strings:
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    author = match.group(1)
                    if '@' not in author:  # If not email, add 기자
                        author += ' 기자'
                    return author
        
        return ""
    
    def _extract_category(self, soup: BeautifulSoup, url: str) -> str:
        """Extract article category"""
        # From URL patterns
        url_patterns = {
            '/economy': '경제',
            '/finance': '금융',
            '/industry': '산업',
            '/it': 'IT',
            '/society': '사회',
            '/politics': '정치',
            '/international': '국제',
            '/stock': '증권',
            '/realestate': '부동산'
        }
        
        for pattern, category in url_patterns.items():
            if pattern in url.lower():
                return category
        
        # From breadcrumb
        breadcrumb = soup.select_one('div.breadcrumb, ol.breadcrumb, ul.location')
        if breadcrumb:
            items = breadcrumb.find_all(['li', 'a', 'span'])
            if len(items) > 1:
                # Usually second item is category
                category_text = items[1].get_text(strip=True)
                if category_text and len(category_text) < 20:
                    return category_text
        
        # From meta tags
        section_meta = soup.select_one('meta[property="article:section"]')
        if section_meta and section_meta.get('content'):
            return section_meta['content']
        
        return "경제"  # Default for 한국경제
    
    def _extract_image(self, soup: BeautifulSoup) -> str:
        """Extract main article image"""
        # Try og:image first
        og_image = soup.select_one('meta[property="og:image"]')
        if og_image and og_image.get('content'):
            img_url = og_image['content']
            if img_url.startswith('//'):
                img_url = 'https:' + img_url
            return img_url
        
        # Try article image selectors
        img_selectors = [
            'div.article_img img',
            'div.thumb img',
            'figure img',
            'div#articletxt img',
            'div.photo img'
        ]
        
        for selector in img_selectors:
            img = soup.select_one(selector)
            if img and img.get('src'):
                img_url = img['src']
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url
                elif not img_url.startswith('http'):
                    img_url = self.normalize_url(img_url)
                return img_url
        
        return ""
    
    def _extract_summary(self, soup: BeautifulSoup, content: str) -> str:
        """Extract or generate article summary"""
        # Try og:description
        og_desc = soup.select_one('meta[property="og:description"]')
        if og_desc and og_desc.get('content'):
            return og_desc['content'].strip()
        
        # Try meta description
        meta_desc = soup.select_one('meta[name="description"]')
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'].strip()
        
        # Try subtitle or lead paragraph
        subtitle_selectors = ['h2.subtitle', 'div.subtitle', 'p.lead', 'div.summary']
        for selector in subtitle_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if text and len(text) > 20:
                    return text
        
        # Generate from content
        if content:
            # Take first paragraph or 200 characters
            paragraphs = content.split('\n\n')
            if paragraphs:
                summary = paragraphs[0][:200].strip()
                if len(paragraphs[0]) > 200:
                    summary += '...'
                return summary
        
        return ""
    
    def _extract_tags(self, soup: BeautifulSoup) -> List[str]:
        """Extract article tags/keywords"""
        tags = set()
        
        # From meta keywords
        keywords_meta = soup.select_one('meta[name="keywords"], meta[property="article:tag"]')
        if keywords_meta and keywords_meta.get('content'):
            raw_tags = keywords_meta['content'].split(',')
            for tag in raw_tags:
                tag = tag.strip()
                if tag and len(tag) > 1 and len(tag) < 50:
                    tags.add(tag)
        
        # From tag elements
        tag_selectors = [
            'a.tag',
            'span.tag',
            'div.keyword a',
            'ul.tag_list li',
            'div.tags span'
        ]
        
        for selector in tag_selectors:
            tag_elements = soup.select(selector)
            for tag_elem in tag_elements:
                tag_text = tag_elem.get_text(strip=True)
                if tag_text and len(tag_text) > 1 and len(tag_text) < 50:
                    # Remove common prefixes
                    tag_text = re.sub(r'^[#·]\s*', '', tag_text)
                    if tag_text:
                        tags.add(tag_text)
        
        # Sort and limit
        return sorted(list(tags))[:10]