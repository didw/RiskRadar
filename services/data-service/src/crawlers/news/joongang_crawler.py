"""
JoongAng Ilbo news crawler implementation
"""
from typing import List, Dict, Any
from datetime import datetime
import re
from bs4 import BeautifulSoup
import logging
from ..base_crawler import BaseCrawler

logger = logging.getLogger(__name__)


class JoongangCrawler(BaseCrawler):
    """Crawler for JoongAng Ilbo (중앙일보) news articles"""
    
    def __init__(self):
        super().__init__(
            source_id="joongang",
            base_url="https://www.joongang.co.kr",
            rate_limit=0.5,  # 2 seconds between requests
            timeout=30,
            max_retries=3
        )
        self.section_urls = [
            "/money",      # 경제
            "/society",    # 사회
            "/politics",   # 정치
            "/world",      # 국제
            "/culture",    # 문화
            "/sports"      # 스포츠
        ]
        # JoongAng-specific selectors
        self.selectors = {
            'article_links': [
                'h2.headline a',
                'h3.headline a',
                'div.card_body h2 a',
                'ul.story_list li a',
                'div.article_list a'
            ],
            'title': [
                'h1.headline',
                'h1[itemprop="headline"]',
                'div.article_header h1',
                'meta[property="og:title"]'
            ],
            'content': [
                'div#article_body',
                'div[itemprop="articleBody"]',
                'div.article_body',
                'section.article_body'
            ],
            'date': [
                'div.byline time',
                'time.date',
                'div.article_info time',
                'meta[property="article:published_time"]'
            ]
        }
    
    async def fetch_article_list(self) -> List[str]:
        """Fetch list of article URLs from JoongAng Ilbo sections"""
        article_urls = set()
        
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
                
                # JoongAng often uses data attributes
                for element in soup.find_all(attrs={'data-link': True}):
                    href = element.get('data-link')
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
        
        return sorted_urls[:50]  # Limit to 50 most recent articles
    
    def _is_article_url(self, url: str) -> bool:
        """Check if URL is likely an article"""
        if not url:
            return False
        
        # Positive patterns for JoongAng articles
        article_patterns = [
            r'/article/\d+',
            r'/news/article\.aspx',
            r'article_id=\d+',
            r'/\d{8}/\d+',  # Date pattern with article ID
            '/view/'
        ]
        
        # Negative patterns to exclude
        exclude_patterns = [
            '/cartoon/',
            '/photo/',
            '/video/',
            '/podcast/',
            '/newsletter/',
            '/search',
            '/login',
            '#comment',
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
        
        # JoongAng specific: article URLs often contain long numeric IDs
        if re.search(r'/\d{8,}', url):
            return True
        
        return False
    
    async def parse_article(self, url: str, html: str) -> Dict[str, Any]:
        """Parse JoongAng Ilbo article content"""
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
                'source_name': '중앙일보',
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
                    # Remove common suffixes
                    title = re.sub(r'\s*[-|]\s*중앙일보.*$', '', title)
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
            title = re.sub(r'\s*[-|]\s*중앙일보.*$', '', title)
            title = re.sub(r'\s*[-|]\s*JoongAng.*$', '', title)
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
                
                # Remove ads, captions, related articles
                for unwanted in content_div.select('.ad, .advertisement, .caption, .related_article, .ab_photo'):
                    unwanted.decompose()
                
                # JoongAng specific: remove photo descriptions
                for photo_desc in content_div.select('.photo_desc, .img_desc'):
                    photo_desc.decompose()
                
                # Extract paragraphs
                paragraphs = []
                seen_texts = set()
                
                # Look for paragraph tags
                for p in content_div.find_all(['p', 'div'], recursive=True):
                    # Skip containers
                    if p.find(['p', 'div', 'h1', 'h2', 'h3']):
                        continue
                    
                    text = p.get_text(separator=' ', strip=True)
                    
                    # Filter out short texts and duplicates
                    if text and len(text) > 30 and text not in seen_texts:
                        # Skip copyright and reporter signatures
                        if any(skip in text for skip in ['ⓒ', '©', 'Copyright', '무단전재']):
                            continue
                        if re.match(r'^.{1,20}\s*(기자|특파원|통신원)$', text):
                            continue
                        
                        paragraphs.append(text)
                        seen_texts.add(text)
                
                if paragraphs:
                    return '\n\n'.join(paragraphs)
        
        # Fallback: try article tag
        article_tag = soup.find('article')
        if article_tag:
            paragraphs = []
            for p in article_tag.find_all('p'):
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
                    if element.name == 'time':
                        # Try datetime attribute first
                        if element.get('datetime'):
                            return self._normalize_date(element['datetime'])
                        # Then pubdate attribute
                        if element.get('pubdate'):
                            return self._normalize_date(element['pubdate'])
                    
                    date_text = element.get_text(strip=True)
                    parsed_date = self._parse_korean_date(date_text)
                    if parsed_date:
                        return parsed_date
        
        # Try to find date in byline
        byline = soup.select_one('.byline, .article_info, .date_area')
        if byline:
            date_text = byline.get_text()
            parsed_date = self._parse_korean_date(date_text)
            if parsed_date:
                return parsed_date
        
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
        # JoongAng patterns: /20240115/123456, /article/25195273
        patterns = [
            r'/(\d{8})/\d+',  # /20240115/123456
            r'/(\d{4})/(\d{2})/(\d{2})/',  # /2024/01/15/
            r'[?&]date=(\d{8})'  # ?date=20240115
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                try:
                    if len(match.groups()) == 1:
                        date_str = match.group(1)
                        if len(date_str) == 8:
                            year = int(date_str[:4])
                            month = int(date_str[4:6])
                            day = int(date_str[6:8])
                            dt = datetime(year, month, day)
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
            # Clean the text
            date_text = ' '.join(date_text.split())
            
            # Common JoongAng patterns
            patterns = [
                # 2024.01.15 14:30
                (r'(\d{4})\.(\d{1,2})\.(\d{1,2})\s+(\d{1,2}):(\d{1,2})', 5),
                # 2024-01-15 14:30
                (r'(\d{4})-(\d{1,2})-(\d{1,2})\s+(\d{1,2}):(\d{1,2})', 5),
                # 2024년 01월 15일 오후 2시 30분
                (r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일.*?(\d{1,2})시\s*(\d{1,2})분', 5),
                # 입력 2024.01.15 14:30
                (r'입력\s*:?\s*(\d{4})\.(\d{1,2})\.(\d{1,2})\s+(\d{1,2}):(\d{1,2})', 5),
                # Published 2024.01.15 14:30
                (r'Published\s*:?\s*(\d{4})\.(\d{1,2})\.(\d{1,2})\s+(\d{1,2}):(\d{1,2})', 5)
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
                        
                        dt = datetime(year, month, day, hour, minute)
                    else:
                        dt = datetime(year, month, day)
                    
                    return dt.isoformat()
                    
        except Exception as e:
            logger.debug(f"Error parsing date {date_text}: {e}")
        
        return ""
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        """Extract article author"""
        author_selectors = [
            'div.byline .name',
            'span.byline',
            'div.reporter',
            'span.writer',
            'div.article_info .name',
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
                    author_text = re.sub(r'\s+', ' ', author_text)  # Normalize spaces
                    
                    # Add 기자 if not present
                    if author_text and '기자' not in author_text and '@' not in author_text:
                        author_text += ' 기자'
                    
                    return author_text
        
        # Look for email pattern or byline text
        for text in soup.stripped_strings:
            # Email pattern
            email_match = re.search(r'([a-zA-Z0-9_.]+@joongang\.co\.kr)', text)
            if email_match:
                return email_match.group(1)
            
            # Name pattern
            name_match = re.search(r'([가-힣]{2,4})\s*(기자|특파원|통신원)', text)
            if name_match:
                return name_match.group(0)
        
        return ""
    
    def _extract_category(self, soup: BeautifulSoup, url: str) -> str:
        """Extract article category"""
        # From URL
        url_patterns = {
            '/money': '경제',
            '/economy': '경제',
            '/society': '사회',
            '/politics': '정치',
            '/world': '국제',
            '/culture': '문화',
            '/sports': '스포츠',
            '/opinion': '오피니언',
            '/it': 'IT'
        }
        
        for pattern, category in url_patterns.items():
            if pattern in url.lower():
                return category
        
        # From breadcrumb
        breadcrumb = soup.select_one('.breadcrumb, .location, nav[aria-label="breadcrumb"]')
        if breadcrumb:
            items = breadcrumb.find_all(['a', 'span', 'li'])
            if len(items) > 1:
                category_text = items[1].get_text(strip=True)
                if category_text and len(category_text) < 20:
                    return category_text
        
        # From meta
        section_meta = soup.select_one('meta[property="article:section"]')
        if section_meta and section_meta.get('content'):
            return section_meta['content']
        
        # From category tag
        category_elem = soup.select_one('.category, .section, .article_section')
        if category_elem:
            return category_elem.get_text(strip=True)
        
        return "뉴스"
    
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
            'div#article_body img',
            'div.article_photo img',
            'figure.photo img',
            'div.ab_photo img',
            'div.image img'
        ]
        
        for selector in img_selectors:
            imgs = soup.select(selector)
            for img in imgs:
                if img and img.get('src'):
                    img_url = img['src']
                    # Skip small images (likely icons)
                    if 'width' in img.attrs:
                        try:
                            width = int(img['width'])
                            if width < 200:
                                continue
                        except:
                            pass
                    
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
            # Remove ellipsis and clean up
            summary = re.sub(r'\.{2,}$', '', summary)
            return summary
        
        # Try meta description
        meta_desc = soup.select_one('meta[name="description"]')
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'].strip()
        
        # Try subtitle
        subtitle_selectors = ['h2.sub_title', 'div.sub_title', 'p.summary', 'div.lead']
        for selector in subtitle_selectors:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                if text and len(text) > 20:
                    return text
        
        # Generate from content
        if content:
            # Take first substantial paragraph
            paragraphs = content.split('\n\n')
            for para in paragraphs:
                if len(para) > 50:
                    summary = para[:200].strip()
                    if len(para) > 200:
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
            'div.tag_list a',
            'ul.tags li',
            'span.tag',
            'a.keyword',
            'div.keyword_box a'
        ]
        
        for selector in tag_selectors:
            tag_elements = soup.select(selector)
            for tag_elem in tag_elements:
                tag_text = tag_elem.get_text(strip=True)
                if tag_text and len(tag_text) > 1 and len(tag_text) < 50:
                    # Remove hashtags
                    tag_text = tag_text.lstrip('#')
                    if tag_text:
                        tags.add(tag_text)
        
        return sorted(list(tags))[:10]