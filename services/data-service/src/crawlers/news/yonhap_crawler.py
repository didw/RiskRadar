"""
Yonhap News Agency crawler implementation
"""
from typing import List, Dict, Any
from datetime import datetime
import re
from bs4 import BeautifulSoup
import logging
from ..base_crawler import BaseCrawler

logger = logging.getLogger(__name__)


class YonhapCrawler(BaseCrawler):
    """Crawler for Yonhap News Agency (연합뉴스) articles"""
    
    def __init__(self):
        super().__init__(
            source_id="yonhap",
            base_url="https://www.yna.co.kr",
            rate_limit=0.3,  # Slower rate for Yonhap (3+ seconds between requests)
            timeout=30,
            max_retries=3
        )
        self.section_urls = [
            "/economy/all",
            "/politics/all",
            "/society/all", 
            "/international/all",
            "/culture/all",
            "/sports/all"
        ]
        # Yonhap-specific selectors
        self.selectors = {
            'article_links': [
                'div.news-con a.tit-wrap',
                'ul.list li a.tit',
                'div.item-box a',
                'h3.news-tl a',
                'div.cont a'
            ],
            'title': [
                'h1.tit',
                'h1.article-tit',
                'div.article-head h1',
                'meta[property="og:title"]'
            ],
            'content': [
                'div.article-txt',
                'article.story-news',
                'div#articleBody',
                'div.article-body'
            ],
            'date': [
                'p.update-time',
                'span.article-time',
                'div.info-box time',
                'meta[property="article:published_time"]'
            ]
        }
    
    async def fetch_article_list(self) -> List[str]:
        """Fetch list of article URLs from Yonhap News sections"""
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
                
                # Yonhap sometimes uses onclick handlers
                for element in soup.find_all(attrs={'onclick': True}):
                    onclick = element.get('onclick', '')
                    # Look for AKR (Korea) or other article IDs
                    id_match = re.search(r'[\'"]([A-Z]{3}\d{14})[\'"]', onclick)
                    if id_match:
                        article_id = id_match.group(1)
                        href = f"/view/{article_id}"
                        article_links.append(href)
                
                # Normalize and add to set
                for link in article_links:
                    normalized_url = self.normalize_url(link)
                    article_urls.add(normalized_url)
                
                logger.info(f"Found {len(article_links)} articles in {section}")
                
            except Exception as e:
                logger.error(f"Error fetching section {section}: {e}")
                continue
        
        # Sort by URL (newer articles typically have higher IDs)
        sorted_urls = sorted(list(article_urls), reverse=True)
        logger.info(f"Total unique articles found: {len(sorted_urls)}")
        
        return sorted_urls[:50]
    
    def _is_article_url(self, url: str) -> bool:
        """Check if URL is likely an article"""
        if not url:
            return False
        
        # Positive patterns for Yonhap articles
        article_patterns = [
            r'/view/[A-Z]{3}\d+',  # Standard Yonhap format: /view/AKR20240115123456
            r'/article/[A-Z]{3}\d+',
            r'[?&]article_id=[A-Z]{3}\d+',
            r'/news/\d+',
            '/bulletin/'
        ]
        
        # Negative patterns
        exclude_patterns = [
            '/photo/',
            '/cartoon/',
            '/graphics/',
            '/special/',
            '/search',
            '/member/',
            '/about/',
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
        
        # Yonhap article ID pattern
        if re.search(r'[A-Z]{3}\d{14}', url):
            return True
        
        return False
    
    async def parse_article(self, url: str, html: str) -> Dict[str, Any]:
        """Parse Yonhap News article content"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract components
        title = self._extract_title(soup)
        content = self._extract_content(soup)
        published_at = self._extract_published_date(soup, url)
        author = self._extract_author(soup)
        category = self._extract_category(soup, url)
        image_url = self._extract_image(soup)
        summary = self._extract_summary(soup, content)
        
        # Extract article ID from URL if available
        article_id = self._extract_article_id(url)
        
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
                'source_name': '연합뉴스',
                'language': 'ko',
                'article_id': article_id,
                'scraped_at': datetime.now().isoformat()
            }
        }
    
    def _extract_article_id(self, url: str) -> str:
        """Extract Yonhap article ID from URL"""
        # Pattern: AKR20240115123456
        match = re.search(r'([A-Z]{3}\d{14})', url)
        if match:
            return match.group(1)
        return ""
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract article title"""
        # Try predefined selectors
        for selector in self.selectors['title']:
            if selector.startswith('meta'):
                meta = soup.select_one(selector)
                if meta and meta.get('content'):
                    title = meta['content'].strip()
                    # Remove agency suffix
                    title = re.sub(r'\s*\|\s*연합뉴스.*$', '', title)
                    title = re.sub(r'\s*::\s*연합뉴스.*$', '', title)
                    return title
            else:
                element = soup.select_one(selector)
                if element:
                    return element.get_text(strip=True)
        
        # Fallback to page title
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text(strip=True)
            # Clean up
            title = re.sub(r'\s*[\|:]+\s*연합뉴스.*$', '', title)
            title = re.sub(r'\s*[\|:]+\s*Yonhap.*$', '', title, flags=re.IGNORECASE)
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
                
                # Remove ads and related content
                for unwanted in content_div.select('.ad, .advertisement, .related-news, .copyright'):
                    unwanted.decompose()
                
                # Remove Yonhap specific elements
                for yonhap_elem in content_div.select('.article-ad, .article-sns, .func-box'):
                    yonhap_elem.decompose()
                
                # Extract paragraphs
                paragraphs = []
                seen_texts = set()
                
                # Get text content
                for elem in content_div.find_all(['p', 'div'], recursive=True):
                    # Skip containers
                    if elem.find(['p', 'div', 'h1', 'h2']):
                        continue
                    
                    text = elem.get_text(separator=' ', strip=True)
                    
                    # Filter
                    if text and len(text) > 30 and text not in seen_texts:
                        # Skip Yonhap signatures and copyright
                        if '무단전재' in text or '재배포금지' in text:
                            continue
                        if text.endswith('특파원') or text.endswith('기자'):
                            if len(text) < 50:
                                continue
                        
                        # Remove location pattern from beginning
                        text = re.sub(r'^\([^)]+=[^)]+\)\s*[^=]+=\s*', '', text)
                        
                        if text and len(text) > 30:
                            paragraphs.append(text)
                            seen_texts.add(text)
                
                if paragraphs:
                    return '\n\n'.join(paragraphs)
        
        # Fallback
        article_elem = soup.find('article')
        if article_elem:
            text = article_elem.get_text(separator='\n', strip=True)
            # Clean up
            lines = []
            for line in text.split('\n'):
                line = line.strip()
                if line and len(line) > 30:
                    if not re.search(r'^\(.+\)\s*=', line):
                        lines.append(line)
            return '\n\n'.join(lines)
        
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
                    if element.name == 'time' and element.get('datetime'):
                        return self._normalize_date(element['datetime'])
                    
                    date_text = element.get_text(strip=True)
                    parsed_date = self._parse_korean_date(date_text)
                    if parsed_date:
                        return parsed_date
        
        # Try to extract from article ID (contains date)
        article_id = self._extract_article_id(url)
        if article_id and len(article_id) >= 11:
            # AKR20240115... -> 2024-01-15
            try:
                year = int(article_id[3:7])
                month = int(article_id[7:9])
                day = int(article_id[9:11])
                if len(article_id) >= 13:
                    hour = int(article_id[11:13])
                    dt = datetime(year, month, day, hour)
                else:
                    dt = datetime(year, month, day)
                return dt.isoformat()
            except:
                pass
        
        # Look for date in text
        for text in soup.stripped_strings:
            parsed = self._parse_korean_date(text)
            if parsed:
                return parsed
        
        return datetime.now().isoformat()
    
    def _normalize_date(self, date_str: str) -> str:
        """Normalize various date formats to ISO format"""
        try:
            from dateutil import parser
            dt = parser.parse(date_str)
            return dt.isoformat()
        except:
            return date_str
    
    def _parse_korean_date(self, date_text: str) -> str:
        """Parse Korean date format to ISO format"""
        try:
            date_text = ' '.join(date_text.split())
            
            # Yonhap patterns
            patterns = [
                # 2024-01-15 14:30
                (r'(\d{4})-(\d{1,2})-(\d{1,2})\s+(\d{1,2}):(\d{1,2})', 5),
                # 2024.01.15 14:30
                (r'(\d{4})\.(\d{1,2})\.(\d{1,2})\s+(\d{1,2}):(\d{1,2})', 5),
                # 송고시간 2024-01-15 14:30
                (r'송고시간.*?(\d{4})-(\d{1,2})-(\d{1,2})\s+(\d{1,2}):(\d{1,2})', 5),
                # 입력 2024.01.15 오후 2:30
                (r'입력.*?(\d{4})\.(\d{1,2})\.(\d{1,2}).*?(\d{1,2}):(\d{1,2})', 5)
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
                        
                        dt = datetime(year, month, day, hour, minute)
                    else:
                        dt = datetime(year, month, day)
                    
                    return dt.isoformat()
                    
        except Exception as e:
            logger.debug(f"Error parsing date {date_text}: {e}")
        
        return ""
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        """Extract article author"""
        # Yonhap has specific patterns
        # Look for (location=연합뉴스) reporter pattern
        content_text = soup.get_text()
        
        # Pattern: (서울=연합뉴스) 홍길동 기자
        location_pattern = r'\([가-힣]+=[가-힣]+\)\s*([가-힣]+)\s*(기자|특파원|통신원)'
        match = re.search(location_pattern, content_text)
        if match:
            return f"{match.group(1)} {match.group(2)}"
        
        # Try selectors
        author_selectors = [
            'span.reporter',
            'div.reporter-name',
            'p.correspondent',
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
        
        # Look for email
        email_match = re.search(r'([a-zA-Z0-9_.]+@yna\.co\.kr)', content_text)
        if email_match:
            return email_match.group(1)
        
        # Simple name pattern
        name_match = re.search(r'([가-힣]{2,4})\s*(기자|특파원)', content_text)
        if name_match:
            return name_match.group(0)
        
        return "연합뉴스"  # Default to agency name
    
    def _extract_category(self, soup: BeautifulSoup, url: str) -> str:
        """Extract article category"""
        # From URL
        url_patterns = {
            '/economy': '경제',
            '/politics': '정치',
            '/society': '사회',
            '/international': '국제',
            '/culture': '문화',
            '/sports': '스포츠',
            '/nk': '북한',
            '/local': '지역'
        }
        
        for pattern, category in url_patterns.items():
            if pattern in url.lower():
                return category
        
        # From breadcrumb
        breadcrumb = soup.select_one('.location, .breadcrumb, .path')
        if breadcrumb:
            items = breadcrumb.find_all(['a', 'span'])
            if len(items) > 1:
                return items[1].get_text(strip=True)
        
        # From meta
        section_meta = soup.select_one('meta[property="article:section"]')
        if section_meta and section_meta.get('content'):
            return section_meta['content']
        
        # From category element
        category_elem = soup.select_one('.category-name, .section-name')
        if category_elem:
            return category_elem.get_text(strip=True)
        
        return "종합"
    
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
            'div.article-img img',
            'figure.article-photo img',
            'div.img-container img',
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
            summary = og_desc['content'].strip()
            # Clean up Yonhap format
            summary = re.sub(r'^\(.*?=연합뉴스\)\s*', '', summary)
            return summary
        
        # Try meta description
        meta_desc = soup.select_one('meta[name="description"]')
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'].strip()
        
        # Try lead paragraph
        lead = soup.select_one('.lead, .summary, p.intro')
        if lead:
            text = lead.get_text(strip=True)
            if text and len(text) > 20:
                return text
        
        # Generate from content
        if content:
            # Skip location pattern at start
            content_clean = re.sub(r'^\(.*?=연합뉴스\)\s*[가-힣]+\s*(기자|특파원)\s*=\s*', '', content)
            
            # Take first paragraph
            paragraphs = content_clean.split('\n\n')
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
                    if tag not in ['연합뉴스', 'Yonhap', 'YNA']:
                        tags.add(tag)
        
        # From tag elements
        tag_selectors = [
            'ul.tag-list li',
            'div.tags a',
            'span.tag',
            'a.keyword'
        ]
        
        for selector in tag_selectors:
            tag_elements = soup.select(selector)
            for tag_elem in tag_elements:
                tag_text = tag_elem.get_text(strip=True)
                if tag_text and len(tag_text) > 1 and len(tag_text) < 50:
                    tags.add(tag_text)
        
        return sorted(list(tags))[:10]