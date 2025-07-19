"""엔티티 매칭 단위 테스트"""
import pytest
from src.algorithms.entity_matching import EntityMatcher, MatchResult

class TestEntityMatcher:
    """EntityMatcher 테스트"""
    
    @pytest.fixture
    def matcher(self):
        """EntityMatcher 인스턴스"""
        return EntityMatcher(similarity_threshold=0.85)
    
    @pytest.fixture
    def sample_companies(self):
        """샘플 기업 데이터"""
        return [
            {
                'id': 'company-1',
                'name': 'Apple Inc.',
                'aliases': ['Apple', 'AAPL']
            },
            {
                'id': 'company-2',
                'name': 'Microsoft Corporation',
                'aliases': ['Microsoft', 'MSFT']
            },
            {
                'id': 'company-3',
                'name': 'Amazon Web Services',
                'aliases': ['AWS']
            }
        ]
    
    def test_exact_match(self, matcher, sample_companies):
        """정확한 매칭 테스트"""
        result = matcher.find_matching_entity('Apple Inc.', sample_companies)
        
        assert result is not None
        assert result.entity_id == 'company-1'
        assert result.similarity_score == 1.0
        assert result.match_type == 'exact'
    
    def test_alias_match(self, matcher, sample_companies):
        """별칭 매칭 테스트"""
        result = matcher.find_matching_entity('MSFT', sample_companies)
        
        assert result is not None
        assert result.entity_id == 'company-2'
        assert result.similarity_score == 1.0
        assert result.match_type == 'alias'
    
    def test_fuzzy_match(self):
        """유사도 매칭 테스트"""
        # 낮은 임계값으로 fuzzy 매칭 테스트
        matcher_low = EntityMatcher(similarity_threshold=0.5)
        sample_companies = [{
            'id': 'company-1',
            'name': 'Apple Inc.',
            'aliases': ['Apple', 'AAPL']
        }]
        
        result = matcher_low.find_matching_entity('Apple Ink', sample_companies)
        
        assert result is not None
        assert result.entity_id == 'company-1'
        assert result.similarity_score >= 0.5
        assert result.match_type == 'fuzzy'
    
    def test_no_match(self, matcher, sample_companies):
        """매칭 실패 테스트"""
        result = matcher.find_matching_entity('Google Inc.', sample_companies)
        
        assert result is None
    
    def test_normalize_name(self, matcher):
        """이름 정규화 테스트"""
        test_cases = [
            ('Apple Inc.', 'apple'),
            ('Microsoft Corporation', 'microsoft'),
            ('Amazon.com, Inc.', 'amazoncom'),
            ('  Multiple   Spaces  ', 'multiple spaces'),
            ('Company Ltd.', 'company')
        ]
        
        for input_name, expected in test_cases:
            assert matcher._normalize_name(input_name) == expected
    
    def test_abbreviation_matching(self, matcher):
        """약어 매칭 테스트"""
        candidates = [{
            'id': 'company-ibm',
            'name': 'International Business Machines',
            'aliases': ['IBM']  # 별칭으로 추가
        }]
        
        result = matcher.find_matching_entity('IBM', candidates)
        assert result is not None
        assert result.similarity_score == 1.0
        assert result.match_type == 'alias'
    
    def test_similarity_threshold(self):
        """유사도 임계값 테스트"""
        matcher_low = EntityMatcher(similarity_threshold=0.5)
        matcher_high = EntityMatcher(similarity_threshold=0.95)
        
        candidates = [{
            'id': 'company-1',
            'name': 'Apple Inc.',
            'aliases': []
        }]
        
        # 낮은 임계값: 매칭 성공
        result_low = matcher_low.find_matching_entity('Apple Company', candidates)
        assert result_low is not None
        
        # 높은 임계값: 완전히 다른 이름으로 테스트
        result_high = matcher_high.find_matching_entity('Banana Corp', candidates)
        assert result_high is None