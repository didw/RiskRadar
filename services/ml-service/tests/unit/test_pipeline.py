"""
Unit tests for NLP pipeline
"""
import pytest
import asyncio
from src.processors.pipeline import NLPPipeline, ProcessingConfig
from src.kafka.schemas import NLPResult, Entity, Sentiment, Keyword


class TestNLPPipeline:
    """Test NLP processing pipeline"""
    
    @pytest.fixture
    def pipeline(self):
        config = ProcessingConfig(
            use_simple_tokenizer=True,  # Use simple tokenizer for tests
            enable_ner=True,
            enable_sentiment=True,
            enable_keywords=True
        )
        return NLPPipeline(config)
        
    @pytest.mark.asyncio
    async def test_process_basic(self, pipeline):
        text = "삼성전자가 3분기 영업이익이 전년대비 40% 증가했다고 발표했다"
        result = await pipeline.process(text)
        
        assert isinstance(result, NLPResult)
        assert isinstance(result.entities, list)
        assert isinstance(result.sentiment, Sentiment)
        assert isinstance(result.keywords, list)
        assert 0 <= result.risk_score <= 1
        assert result.processing_time_ms > 0
        
    @pytest.mark.asyncio
    async def test_process_empty_text(self, pipeline):
        result = await pipeline.process("")
        
        assert isinstance(result, NLPResult)
        assert len(result.entities) == 0
        assert len(result.keywords) == 0
        assert result.sentiment.label == "neutral"
        
    @pytest.mark.asyncio
    async def test_entity_extraction(self, pipeline):
        text = "이재용 삼성전자 회장이 현대차그룹과 협력을 논의했다"
        result = await pipeline.process(text)
        
        # Should extract some entities
        assert len(result.entities) > 0
        
        # Check entity structure
        for entity in result.entities:
            assert isinstance(entity, Entity)
            assert entity.text
            assert entity.type in ["COMPANY", "PERSON", "EVENT", "UNKNOWN"]
            assert 0 <= entity.confidence <= 1
            
    @pytest.mark.asyncio 
    async def test_sentiment_analysis(self, pipeline):
        # Positive text
        positive_text = "매출이 크게 증가하고 실적이 개선되었다"
        pos_result = await pipeline.process(positive_text)
        
        # Negative text
        negative_text = "손실이 증가하고 실적이 급락했다"
        neg_result = await pipeline.process(negative_text)
        
        # Check sentiment structure
        assert pos_result.sentiment.label in ["positive", "neutral", "negative"]
        assert 0 <= pos_result.sentiment.score <= 1
        assert isinstance(pos_result.sentiment.probabilities, dict)
        
        # Basic sentiment detection (mock implementation)
        # The mock should detect some difference
        assert pos_result.sentiment.label != neg_result.sentiment.label or \
               abs(pos_result.sentiment.score - neg_result.sentiment.score) > 0.1
               
    @pytest.mark.asyncio
    async def test_keyword_extraction(self, pipeline):
        text = "인공지능 기술과 자율주행 자동차 개발에 투자를 확대한다"
        result = await pipeline.process(text)
        
        assert len(result.keywords) > 0
        assert len(result.keywords) <= pipeline.config.max_keywords
        
        for keyword in result.keywords:
            assert isinstance(keyword, Keyword)
            assert keyword.text
            assert 0 <= keyword.score <= 1
            
    @pytest.mark.asyncio
    async def test_risk_score_calculation(self, pipeline):
        # Low risk text
        low_risk_text = "실적이 개선되고 매출이 증가했다"
        low_result = await pipeline.process(low_risk_text)
        
        # High risk text
        high_risk_text = "대규모 손실과 연체율 급증으로 위기에 직면했다"
        high_result = await pipeline.process(high_risk_text)
        
        assert 0 <= low_result.risk_score <= 1
        assert 0 <= high_result.risk_score <= 1
        
        # High risk should have higher score (in mock implementation)
        assert high_result.risk_score >= low_result.risk_score
        
    @pytest.mark.asyncio
    async def test_processing_config(self):
        # Test with NER disabled
        config = ProcessingConfig(
            use_simple_tokenizer=True,
            enable_ner=False,
            enable_sentiment=True,
            enable_keywords=True
        )
        pipeline = NLPPipeline(config)
        
        result = await pipeline.process("테스트 텍스트")
        assert len(result.entities) == 0
        
    @pytest.mark.asyncio
    async def test_error_handling(self, pipeline):
        # Test with None
        result = await pipeline.process(None)
        assert isinstance(result, NLPResult)
        assert result.risk_score == 0.0
        
    @pytest.mark.asyncio
    async def test_concurrent_processing(self, pipeline):
        # Test concurrent processing
        texts = [
            "첫 번째 뉴스 기사입니다",
            "두 번째 뉴스 기사입니다",
            "세 번째 뉴스 기사입니다"
        ]
        
        tasks = [pipeline.process(text) for text in texts]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == len(texts)
        assert all(isinstance(r, NLPResult) for r in results)