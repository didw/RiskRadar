"""
Unit tests for text normalizer
"""
import pytest
from src.processors.normalizer import TextNormalizer


class TestTextNormalizer:
    """Test text normalization"""
    
    @pytest.fixture
    def normalizer(self):
        return TextNormalizer()
        
    def test_normalize_empty_text(self, normalizer):
        assert normalizer.normalize("") == ""
        assert normalizer.normalize(None) == ""
        
    def test_remove_urls(self, normalizer):
        text = "자세한 내용은 https://example.com/news 에서 확인하세요"
        normalized = normalizer.normalize(text, remove_urls=True)
        assert "https://" not in normalized
        assert "[URL]" in normalized
        
    def test_remove_emails(self, normalizer):
        text = "문의사항은 contact@example.com 으로 보내주세요"
        normalized = normalizer.normalize(text, remove_emails=True)
        assert "@" not in normalized
        assert "[EMAIL]" in normalized
        
    def test_normalize_phone_numbers(self, normalizer):
        text = "연락처는 02-1234-5678 입니다"
        normalized = normalizer.normalize(text, normalize_numbers=True)
        assert "[PHONE]" in normalized
        
    def test_remove_repeated_chars(self, normalizer):
        text = "대박ㅋㅋㅋㅋㅋ 진짜 웃겨요ㅎㅎㅎㅎ"
        normalized = normalizer.normalize(text)
        assert "ㅋㅋㅋㅋㅋ" not in normalized
        assert "ㅋㅋ" in normalized
        
    def test_normalize_whitespace(self, normalizer):
        text = "이것은    여러개의     공백이     있는 텍스트입니다"
        normalized = normalizer.normalize(text)
        assert "    " not in normalized
        assert normalized.count(" ") < text.count(" ")
        
    def test_extract_metadata(self, normalizer):
        text = """
        삼성전자가 2024년 1월 15일 실적을 발표했습니다.
        자세한 내용은 https://samsung.com 에서 확인하세요.
        문의: investor@samsung.com 또는 02-1234-5678
        """
        metadata = normalizer.extract_metadata(text)
        
        assert metadata['has_email'] is True
        assert metadata['has_url'] is True
        assert metadata['has_phone'] is True
        assert len(metadata['dates']) > 0
        assert metadata['word_count'] > 0
        
    def test_clean_for_nlp(self, normalizer):
        text = '삼성전자가 "새로운 기술"을 발표했다(김철수 기자)'
        cleaned = normalizer.clean_for_nlp(text)
        
        assert "(김철수 기자)" not in cleaned
        assert "새로운 기술" in cleaned
        
    def test_normalize_numbers(self, normalizer):
        text = "매출액은 1,234,567원 입니다"
        normalized = normalizer.normalize(text, normalize_numbers=True)
        assert "1234567" in normalized
        
    def test_special_chars_option(self, normalizer):
        text = "이익률 50%↑ & 매출 30%↓"
        
        # With remove_special=False (default)
        normalized1 = normalizer.normalize(text, remove_special=False)
        assert "%" in normalized1
        
        # With remove_special=True
        normalized2 = normalizer.normalize(text, remove_special=True)
        assert normalized2.count("%") < text.count("%")
        
    def test_lowercase_option(self, normalizer):
        text = "Samsung Electronics announced NEW products"
        
        # Default (no lowercase)
        normalized1 = normalizer.normalize(text, lowercase=False)
        assert "Samsung" in normalized1
        
        # With lowercase
        normalized2 = normalizer.normalize(text, lowercase=True)
        assert "samsung" in normalized2
        assert "Samsung" not in normalized2