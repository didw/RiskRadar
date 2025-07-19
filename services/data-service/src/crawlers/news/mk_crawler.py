"""
Maeil Business News (MK) crawler implementation
"""
from typing import List, Dict, Any
from datetime import datetime
import re
from bs4 import BeautifulSoup
import logging
from ..base_crawler import BaseCrawler

logger = logging.getLogger(__name__)


class MKCrawler(BaseCrawler):
    """Crawler for Maeil Business News (매일경제) articles"""
    
    def __init__(self):
        super().__init__(
            source_id="mk",
            base_url="https://www.mk.co.kr",
            rate_limit=0.5,  # 2 seconds between requests
            timeout=30,
            max_retries=3
        )
        self.section_urls = [
            "/economy/",
            "/stock/",
            "/realestate/",
            "/it/",
            "/industry/",
            "/financial/"
        ]
        # MK-specific selectors
        self.selectors = {
            'article_links': [
                'h3.article_title a',
                'dt.tit a',
                'div.article-list a',
                'ul.article_list a',
                'h2.news_ttl a'
            ],
            'title': [
                'h2.news_ttl',
                'h1.view_title',
                'div.article_head h1',
                'meta[property="og:title"]'
            ],
            'content': [
                'div.art_txt',
                'div#artText',
                'div.view_txt',
                'div[itemprop="articleBody"]'
            ],
            'date': [
                'div.time_area',
                'span.registration',
                'li.lasttime',
                'meta[property="article:published_time"]'
            ]
        }
    
    async def fetch_article_list(self) -> List[str]:
        """Fetch list of article URLs from MK sections"""
        article_urls = set()
        
        for section in self.section_urls:
            try:
                section_url = self.normalize_url(section)
                html = await self.fetch_page(section_url)
                soup = BeautifulSoup(html, 'html.parser')
                
                # Find article links
                article_links = []
                
                for selector in self.selectors['article_links']:
                    elements = soup.select(selector)
                    for element in elements:
                        href = element.get('href')
                        if href and self._is_article_url(href):
                            article_links.append(href)
                
                # MK sometimes uses JavaScript onclick
                for element in soup.find_all(attrs={'onclick': True}):
                    onclick = element.get('onclick', '')
                    # Extract URL from JavaScript function
                    url_match = re.search(r"['\"]([^'\"]*article[^'\"]*)['\"]", onclick)
                    if url_match:
                        href = url_match.group(1)
                        if self._is_article_url(href):
                            article_links.append(href)
                
                # MK also uses data attributes
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
        
        sorted_urls = sorted(list(article_urls), reverse=True)
        logger.info(f"Total unique articles found: {len(sorted_urls)}")
        
        return sorted_urls[:50]
    
    def _is_article_url(self, url: str) -> bool:
        """Check if URL is likely an article"""
        if not url:
            return False
        
        # Positive patterns for MK articles
        article_patterns = [
            r'/news/.*\.php.*no=\d+',  # newsRead.php?no=123456
            r'articleV2\.php.*t=\d+',   # articleV2.php?t=20240115
            r'/article/\d+',
            r'/news/\d+',
            r'[\?&]no=\d+',
            r'[\?&]aid=\d+'
        ]
        
        # Negative patterns
        exclude_patterns = [
            '/premium/',  # Premium content
            '/gallery/',
            '/cartoon/',
            '/search/',
            '/login',
            '/member/',
            '/board/',
            '#',
            'javascript:'
        ]
        
        url_lower = url.lower()
        
        # Check exclusions
        for pattern in exclude_patterns:
            if pattern in url_lower:
                return False
        
        # Check article patterns
        for pattern in article_patterns:
            if re.search(pattern, url):
                return True
        
        # MK specific: URLs with long numbers
        if re.search(r'/\d{8,}', url):
            return True
        
        return False
    
    async def parse_article(self, url: str, html: str) -> Dict[str, Any]:
        """Parse MK article content"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract all components
        title = self._extract_title(soup)
        content = self._extract_content(soup)
        published_at = self._extract_published_date(soup, url)
        author = self._extract_author(soup)
        category = self._extract_category(soup, url)
        image_url = self._extract_image(soup)
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
                'source_name': '매일경제',
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
                    title = meta['content'].strip()
                    # Remove MK suffix
                    title = re.sub(r'\s*-\s*매일경제.*$', '', title)
                    title = re.sub(r'\s*\|\s*MK.*$', '', title)
                    return title
            else:
                element = soup.select_one(selector)
                if element:
                    return element.get_text(strip=True)
        
        # Fallback to page title
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text(strip=True)
            # Remove site name
            title = re.sub(r'\s*[-|]\s*매일경제.*$', '', title)
            title = re.sub(r'\s*[-|]\s*MK.*$', '', title)
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
                for tag in content_div(['script', 'style', 'iframe']):
                    tag.decompose()
                
                # Remove MK specific elements
                for unwanted in content_div.select('.art_bottom, .copyright, .reporter_area, .ad_area'):
                    unwanted.decompose()
                
                # Remove photo captions
                for caption in content_div.select('.img_caption, .desc_photo, .photo_caption'):
                    caption.decompose()
                
                # Extract paragraphs
                paragraphs = []
                seen_texts = set()
                
                # Process text
                for elem in content_div.find_all(['p', 'div'], recursive=True):
                    # Skip containers
                    if elem.find(['p', 'div', 'table']):
                        continue
                    
                    text = elem.get_text(separator=' ', strip=True)
                    
                    # Filter
                    if text and len(text) > 30 and text not in seen_texts:
                        # Skip copyright and reporter info
                        if any(skip in text for skip in ['ⓒ', '©', '무단전재', '재배포']):
                            continue
                        # Skip email addresses as single lines
                        if re.match(r'^[a-zA-Z0-9_.]+@mk\.co\.kr$', text):
                            continue
                        # Skip short reporter names
                        if re.match(r'^[가-힣]{2,4}\s*(기자|특파원)$', text):
                            continue
                        
                        paragraphs.append(text)
                        seen_texts.add(text)
                
                if paragraphs:
                    return '\n\n'.join(paragraphs)
        
        # Fallback: find any article-like container
        for container in soup.find_all(['article', 'div'], class_=re.compile('article|content')):
            paragraphs = []
            for p in container.find_all('p'):
                text = p.get_text(strip=True)
                if text and len(text) > 50:
                    paragraphs.append(text)
            if paragraphs:
                return '\n\n'.join(paragraphs)
        
        return ""
    
    def _extract_published_date(self, soup: BeautifulSoup, url: str) -> str:
        """Extract published date"""
        # Try predefined selectors
        for selector in self.selectors['date']:
            if selector.startswith('meta'):
                meta = soup.select_one(selector)
                if meta and meta.get('content'):
                    return self._normalize_date(meta['content'])
            else:
                element = soup.select_one(selector)
                if element:
                    date_text = element.get_text(strip=True)
                    # Remove labels
                    date_text = re.sub(r'^(기사입력|최종수정|입력)\s*:?\s*', '', date_text)
                    parsed_date = self._parse_korean_date(date_text)
                    if parsed_date:
                        return parsed_date
        
        # Try to find in any text with date pattern
        for text in soup.stripped_strings:
            if '입력' in text or '기사' in text:
                parsed = self._parse_korean_date(text)
                if parsed:
                    return parsed
        
        # Try URL extraction
        url_date = self._extract_date_from_url(url)
        if url_date:
            return url_date
        
        return datetime.now().isoformat()
    
    def _normalize_date(self, date_str: str) -> str:
        """Normalize various date formats to ISO format"""
        try:
            from dateutil import parser
            dt = parser.parse(date_str)
            return dt.isoformat()
        except:
            return date_str
    
    def _extract_date_from_url(self, url: str) -> str:
        """Extract date from URL if present"""
        # MK patterns: t=20240115123456
        patterns = [
            r't=(\d{14})',  # Full timestamp
            r't=(\d{8})',   # Date only
            r'/(\d{4})(\d{2})(\d{2})/',  # Path date
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                try:
                    if len(match.groups()) == 1:
                        timestamp = match.group(1)
                        if len(timestamp) == 14:
                            # YYYYMMDDHHmmss
                            year = int(timestamp[:4])
                            month = int(timestamp[4:6])
                            day = int(timestamp[6:8])
                            hour = int(timestamp[8:10])
                            minute = int(timestamp[10:12])
                            dt = datetime(year, month, day, hour, minute)
                        elif len(timestamp) == 8:
                            # YYYYMMDD
                            year = int(timestamp[:4])
                            month = int(timestamp[4:6])
                            day = int(timestamp[6:8])
                            dt = datetime(year, month, day)
                        else:
                            continue
                        return dt.isoformat()
                    elif len(match.groups()) == 3:
                        year, month, day = match.groups()
                        dt = datetime(int(year), int(month), int(day))
                        return dt.isoformat()
                except:
                    pass
        
        return ""
    
    def _parse_korean_date(self, date_text: str) -> str:
        """Parse Korean date format to ISO format"""
        try:
            # Clean text
            date_text = ' '.join(date_text.split())
            
            # MK patterns
            patterns = [
                # 2024.01.15 14:30:00
                (r'(\d{4})\.(\d{1,2})\.(\d{1,2})\s+(\d{1,2}):(\d{1,2}):(\d{1,2})', 6),
                # 2024.01.15 14:30
                (r'(\d{4})\.(\d{1,2})\.(\d{1,2})\s+(\d{1,2}):(\d{1,2})', 5),
                # 2024-01-15 14:30
                (r'(\d{4})-(\d{1,2})-(\d{1,2})\s+(\d{1,2}):(\d{1,2})', 5),
                # 기사입력 2024.01.15 오후 2:30
                (r'기사입력\s*:?\s*(\d{4})\.(\d{1,2})\.(\d{1,2}).*?(\d{1,2}):(\d{1,2})', 5),
                # 2024년 1월 15일
                (r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일', 3)
            ]
            
            for pattern, group_count in patterns:
                match = re.search(pattern, date_text)
                if match:
                    groups = match.groups()
                    year = int(groups[0])
                    month = int(groups[1])
                    day = int(groups[2])
                    
                    if group_count >= 5:
                        hour = int(groups[3])
                        minute = int(groups[4])
                        
                        # Handle 오후/오전
                        if '오후' in date_text and hour < 12:
                            hour += 12
                        elif '오전' in date_text and hour == 12:
                            hour = 0
                            
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
            'div.reporter_area',
            'span.reporter',
            'div.byline',
            'p.writer',
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
                    # Clean up
                    author_text = re.sub(r'\s*\[.*?\]', '', author_text)  # Remove brackets
                    author_text = re.sub(r'\s+', ' ', author_text)
                    
                    # Extract name from common patterns
                    name_match = re.search(r'([가-힣]{2,4})\s*(기자|특파원)', author_text)
                    if name_match:
                        return name_match.group(0)
                    
                    return author_text
        
        # Look for email or name in content
        content_text = soup.get_text()
        
        # Email pattern
        email_match = re.search(r'([a-zA-Z0-9_.]+@mk\.co\.kr)', content_text)
        if email_match:
            # Try to find name near email
            context = content_text[max(0, email_match.start()-50):email_match.end()]
            name_match = re.search(r'([가-힣]{2,4})\s*(기자|특파원)', context)
            if name_match:
                return name_match.group(0)
            return email_match.group(1)
        
        # Simple name pattern
        name_match = re.search(r'([가-힣]{2,4})\s*(기자|특파원)', content_text)
        if name_match:
            return name_match.group(0)
        
        return ""
    
    def _extract_category(self, soup: BeautifulSoup, url: str) -> str:
        """Extract article category"""
        # From URL
        url_patterns = {
            '/economy': '경제',
            '/stock': '증권',
            '/realestate': '부동산',
            '/it': 'IT',
            '/industry': '산업',
            '/financial': '금융',
            '/world': '국제',
            '/politics': '정치',
            '/society': '사회'
        }
        
        for pattern, category in url_patterns.items():
            if pattern in url.lower():
                return category
        
        # From breadcrumb
        breadcrumb = soup.select_one('.location, .path, .breadcrumb')
        if breadcrumb:
            items = breadcrumb.find_all(['a', 'span', 'li'])
            if len(items) > 1:
                category_text = items[1].get_text(strip=True)
                if category_text and len(category_text) < 20:
                    return category_text
        
        # From section name
        section = soup.select_one('.section_name, .category_name')
        if section:
            return section.get_text(strip=True)
        
        # From meta
        section_meta = soup.select_one('meta[property="article:section"]')
        if section_meta and section_meta.get('content'):
            return section_meta['content']
        
        return "경제"  # Default for 매일경제
    
    def _extract_image(self, soup: BeautifulSoup) -> str:
        """Extract main article image"""
        # Try og:image
        og_image = soup.select_one('meta[property="og:image"]')
        if og_image and og_image.get('content'):
            img_url = og_image['content']
            if img_url.startswith('//'):
                img_url = 'https:' + img_url
            return img_url
        
        # Try article images
        img_selectors = [
            'div.art_txt img',
            'div#artText img',
            'div.thumb img',
            'figure img',
            'div.view_txt img'
        ]
        
        for selector in img_selectors:
            imgs = soup.select(selector)
            for img in imgs:
                if img and img.get('src'):
                    img_url = img['src']
                    
                    # Skip small images
                    if 'thumb' in img_url.lower() and 's_' in img_url.lower():
                        continue
                    
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
        
        # Try subtitle
        subtitle_selectors = ['h3.sub_tit', 'div.summary', 'p.lead']
        for selector in subtitle_selectors:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                if text and len(text) > 20:
                    return text
        
        # Generate from content
        if content:
            # Take first paragraph
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
                    # Skip generic tags
                    if tag not in ['매일경제', 'MK', '뉴스']:
                        tags.add(tag)
        
        # From tag elements
        tag_selectors = [
            'div.tag_area a',
            'ul.tag_list li',
            'span.tag',
            'a.hash_tag'
        ]
        
        for selector in tag_selectors:
            tag_elements = soup.select(selector)
            for tag_elem in tag_elements:
                tag_text = tag_elem.get_text(strip=True)
                if tag_text and len(tag_text) > 1 and len(tag_text) < 50:
                    # Remove # prefix
                    tag_text = tag_text.lstrip('#')
                    if tag_text:
                        tags.add(tag_text)
        
        return sorted(list(tags))[:10]