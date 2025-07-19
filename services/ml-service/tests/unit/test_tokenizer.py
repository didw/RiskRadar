"""
Unit tests for Korean tokenizer
"""
import pytest
from src.processors.tokenizer import KoreanTokenizer, SimpleTokenizer


class TestSimpleTokenizer:
    """Test simple tokenizer"""
    
    def test_tokenize(self):
        tokenizer = SimpleTokenizer()
        text = "삼성전자가 새로운 반도체 공장을 건설합니다"
        tokens = tokenizer.tokenize(text)
        
        assert isinstance(tokens, list)
        assert len(tokens) > 0
        assert "삼성전자가" in tokens
        
    def test_pos(self):
        tokenizer = SimpleTokenizer()
        text = "현대차그룹이 전기차 시장에 진출합니다"
        pos_tags = tokenizer.pos(text)
        
        assert isinstance(pos_tags, list)
        assert all(isinstance(tag, tuple) and len(tag) == 2 for tag in pos_tags)
        
    def test_nouns(self):
        tokenizer = SimpleTokenizer()
        text = "카카오뱅크의 대출 연체율이 증가했습니다"
        nouns = tokenizer.nouns(text)
        
        assert isinstance(nouns, list)
        # Simple tokenizer extracts words longer than 2 chars
        assert any(len(noun) > 2 for noun in nouns)


class TestKoreanTokenizer:
    """Test Korean tokenizer with KoNLPy"""
    
    @pytest.fixture
    def tokenizer(self):
        # Use Komoran as it's more likely to be available
        return KoreanTokenizer(backend='komoran')
        
    def test_initialization(self):
        # Test different backends
        for backend in ['komoran', 'hannanum']:
            tokenizer = KoreanTokenizer(backend=backend)
            assert tokenizer.backend_name == backend
            assert tokenizer.tokenizer is not None
            
    def test_tokenize(self, tokenizer):
        text = "삼성전자가 3분기 영업이익이 전년대비 40% 증가했다"
        tokens = tokenizer.tokenize(text)
        
        assert isinstance(tokens, list)
        assert len(tokens) > 0
        # Check if morphemes are extracted
        assert any('삼성' in token for token in tokens)
        
    def test_pos(self, tokenizer):
        text = "이재용 회장은 혁신적인 기술 개발을 강조했다"
        pos_tags = tokenizer.pos(text)
        
        assert isinstance(pos_tags, list)
        assert all(isinstance(tag, tuple) and len(tag) == 2 for tag in pos_tags)
        # Check if POS tags are present
        assert any(tag[1].startswith('N') for tag in pos_tags)  # Nouns
        
    def test_nouns(self, tokenizer):
        text = "LG에너지솔루션의 배터리 공장에서 화재가 발생했다"
        nouns = tokenizer.nouns(text)
        
        assert isinstance(nouns, list)
        assert len(nouns) > 0
        # Check if important nouns are extracted
        assert any('공장' in noun or '화재' in noun for noun in nouns)
        
    def test_extract_keywords(self, tokenizer):
        text = "현대자동차가 전기차 시장 점유율을 확대하고 있다"
        keywords = tokenizer.extract_keywords(text)
        
        assert isinstance(keywords, list)
        assert len(keywords) > 0
        # Keywords should be nouns
        assert all(isinstance(kw, str) for kw in keywords)
        
    def test_fallback_on_error(self, tokenizer):
        # Test with empty text
        tokens = tokenizer.tokenize("")
        assert tokens == []
        
        # Test with None (should handle gracefully)
        try:
            tokens = tokenizer.tokenize(None)
        except:
            # Should handle the error internally
            pass