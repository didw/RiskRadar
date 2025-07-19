"""
Korean tokenizer using KoNLPy
Supports multiple backends: Mecab, Komoran, Hannanum
"""
import logging
from typing import List, Tuple, Optional
from konlpy.tag import Mecab, Komoran, Hannanum

logger = logging.getLogger(__name__)


class KoreanTokenizer:
    """Korean tokenizer wrapper for multiple backends"""
    
    def __init__(self, backend: str = 'komoran'):
        """
        Initialize tokenizer with specified backend
        
        Args:
            backend: Tokenizer backend ('mecab', 'komoran', 'hannanum')
        """
        self.backend_name = backend.lower()
        self.tokenizer = None
        self._initialize_backend()
        
    def _initialize_backend(self):
        """Initialize the selected tokenizer backend"""
        try:
            if self.backend_name == 'mecab':
                # Mecab requires system installation
                try:
                    self.tokenizer = Mecab()
                    logger.info("Initialized Mecab tokenizer")
                except Exception as e:
                    logger.warning(f"Mecab initialization failed: {e}. Falling back to Komoran.")
                    self.backend_name = 'komoran'
                    self.tokenizer = Komoran()
            elif self.backend_name == 'komoran':
                self.tokenizer = Komoran()
                logger.info("Initialized Komoran tokenizer")
            elif self.backend_name == 'hannanum':
                self.tokenizer = Hannanum()
                logger.info("Initialized Hannanum tokenizer")
            else:
                raise ValueError(f"Unknown backend: {self.backend_name}")
        except Exception as e:
            logger.error(f"Failed to initialize tokenizer: {e}")
            raise
            
    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into morphemes
        
        Args:
            text: Input text
            
        Returns:
            List of tokens
        """
        if not self.tokenizer:
            raise RuntimeError("Tokenizer not initialized")
            
        try:
            tokens = self.tokenizer.morphs(text)
            return tokens
        except Exception as e:
            logger.error(f"Tokenization failed: {e}")
            return text.split()  # Fallback to simple split
            
    def pos(self, text: str) -> List[Tuple[str, str]]:
        """
        Get part-of-speech tags
        
        Args:
            text: Input text
            
        Returns:
            List of (token, pos) tuples
        """
        if not self.tokenizer:
            raise RuntimeError("Tokenizer not initialized")
            
        try:
            return self.tokenizer.pos(text)
        except Exception as e:
            logger.error(f"POS tagging failed: {e}")
            return [(token, 'UNK') for token in text.split()]
            
    def nouns(self, text: str) -> List[str]:
        """
        Extract nouns from text
        
        Args:
            text: Input text
            
        Returns:
            List of nouns
        """
        if not self.tokenizer:
            raise RuntimeError("Tokenizer not initialized")
            
        try:
            return self.tokenizer.nouns(text)
        except Exception as e:
            logger.error(f"Noun extraction failed: {e}")
            return []
            
    def extract_keywords(self, text: str, pos_filter: Optional[List[str]] = None) -> List[str]:
        """
        Extract keywords based on POS tags
        
        Args:
            text: Input text
            pos_filter: List of POS tags to include (default: nouns and proper nouns)
            
        Returns:
            List of keywords
        """
        if pos_filter is None:
            # Default: Extract nouns and proper nouns
            pos_filter = ['NNG', 'NNP', 'NNB']  # General noun, Proper noun, Bound noun
            
        pos_tags = self.pos(text)
        keywords = [word for word, tag in pos_tags if tag in pos_filter]
        
        return keywords


class SimpleTokenizer:
    """Simple tokenizer for testing without Korean NLP dependencies"""
    
    def __init__(self):
        logger.info("Initialized SimpleTokenizer (for testing)")
        
    def tokenize(self, text: str) -> List[str]:
        """Simple whitespace tokenization"""
        return text.split()
        
    def pos(self, text: str) -> List[Tuple[str, str]]:
        """Mock POS tagging"""
        return [(token, 'NOUN') for token in text.split()]
        
    def nouns(self, text: str) -> List[str]:
        """Extract mock nouns (words longer than 2 chars)"""
        return [token for token in text.split() if len(token) > 2]
        
    def extract_keywords(self, text: str, pos_filter: Optional[List[str]] = None) -> List[str]:
        """Extract mock keywords"""
        return self.nouns(text)