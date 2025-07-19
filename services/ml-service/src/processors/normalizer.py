"""
Text normalization for Korean news articles
"""
import re
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class TextNormalizer:
    """Korean text normalizer for preprocessing"""
    
    def __init__(self):
        # Regex patterns for normalization
        self.patterns = {
            'email': re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),
            'url': re.compile(r'https?://[^\s]+'),
            'phone': re.compile(r'\d{2,4}-\d{3,4}-\d{4}'),
            'date': re.compile(r'\d{4}년\s*\d{1,2}월\s*\d{1,2}일'),
            'time': re.compile(r'\d{1,2}시\s*\d{1,2}분'),
            'number_with_unit': re.compile(r'\d+\.?\d*\s*[가-힣]+'),
            'repeated_chars': re.compile(r'(.)\1{2,}'),
            'multiple_spaces': re.compile(r'\s+'),
            'special_chars': re.compile(r'[^\w\s가-힣.,!?%\-()]'),
        }
        
    def normalize(self, text: str, **options) -> str:
        """
        Normalize Korean text
        
        Args:
            text: Input text
            **options: Normalization options
                - remove_urls: Remove URLs (default: True)
                - remove_emails: Remove emails (default: True)
                - normalize_numbers: Normalize numbers (default: True)
                - remove_special: Remove special characters (default: False)
                
        Returns:
            Normalized text
        """
        if not text:
            return ""
            
        # Default options
        opts = {
            'remove_urls': True,
            'remove_emails': True,
            'normalize_numbers': True,
            'remove_special': False,
            'lowercase': False
        }
        opts.update(options)
        
        result = text
        
        # Remove or replace patterns
        if opts['remove_emails']:
            result = self.patterns['email'].sub('[EMAIL]', result)
            
        if opts['remove_urls']:
            result = self.patterns['url'].sub('[URL]', result)
            
        if opts['normalize_numbers']:
            # Preserve numbers with units (e.g., "3조원", "50%")
            result = self._normalize_numbers(result)
            
        # Remove repeated characters (e.g., "ㅋㅋㅋㅋ" -> "ㅋㅋ")
        result = self.patterns['repeated_chars'].sub(r'\1\1', result)
        
        # Normalize whitespace
        result = self.patterns['multiple_spaces'].sub(' ', result)
        result = result.strip()
        
        # Optional: remove special characters
        if opts['remove_special']:
            result = self.patterns['special_chars'].sub(' ', result)
            
        # Optional: lowercase
        if opts['lowercase']:
            result = result.lower()
            
        return result
        
    def _normalize_numbers(self, text: str) -> str:
        """Normalize number representations"""
        # Replace phone numbers
        text = self.patterns['phone'].sub('[PHONE]', text)
        
        # Normalize large numbers (e.g., "1,234,567" -> "1234567")
        text = re.sub(r'(\d{1,3}),(\d{3})', r'\1\2', text)
        
        return text
        
    def extract_metadata(self, text: str) -> Dict[str, Any]:
        """
        Extract metadata from text
        
        Returns:
            Dictionary containing extracted metadata
        """
        metadata = {
            'has_email': bool(self.patterns['email'].search(text)),
            'has_url': bool(self.patterns['url'].search(text)),
            'has_phone': bool(self.patterns['phone'].search(text)),
            'dates': self.patterns['date'].findall(text),
            'times': self.patterns['time'].findall(text),
            'urls': self.patterns['url'].findall(text),
            'length': len(text),
            'word_count': len(text.split())
        }
        
        return metadata
        
    def clean_for_nlp(self, text: str) -> str:
        """
        Clean text specifically for NLP processing
        
        Args:
            text: Input text
            
        Returns:
            Cleaned text suitable for NLP
        """
        # Remove URLs and emails
        cleaned = self.normalize(
            text,
            remove_urls=True,
            remove_emails=True,
            normalize_numbers=True,
            remove_special=False,
            lowercase=False
        )
        
        # Remove quotes if they're unbalanced
        quote_count = cleaned.count('"')
        if quote_count % 2 != 0:
            cleaned = cleaned.replace('"', '')
            
        # Remove parentheses content if it's metadata
        cleaned = re.sub(r'\([^)]*기자\)', '', cleaned)
        cleaned = re.sub(r'\([^)]*뉴스\)', '', cleaned)
        
        return cleaned