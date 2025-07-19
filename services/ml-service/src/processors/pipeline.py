"""
NLP processing pipeline for Korean news articles
"""
import time
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .tokenizer import KoreanTokenizer, SimpleTokenizer
from .normalizer import TextNormalizer
from ..kafka.schemas import NLPResult, Entity, Sentiment, Keyword
from ..models.ner import MockNERModel, KLUEBERTNERModel

logger = logging.getLogger(__name__)


@dataclass
class ProcessingConfig:
    """Configuration for NLP pipeline"""
    tokenizer_backend: str = 'komoran'  # mecab, komoran, hannanum
    use_simple_tokenizer: bool = False  # For testing
    max_entities: int = 10
    max_keywords: int = 10
    min_keyword_length: int = 2
    enable_ner: bool = True
    enable_sentiment: bool = True
    enable_keywords: bool = True
    
    # NER model settings
    use_mock_ner: bool = True  # Use mock NER for development
    ner_model_name: str = "Babelscape/wikineural-multilingual-ner"
    ner_confidence_threshold: float = 0.5


class NLPPipeline:
    """Main NLP processing pipeline"""
    
    def __init__(self, config: Optional[ProcessingConfig] = None):
        self.config = config or ProcessingConfig()
        
        # Initialize components
        self.normalizer = TextNormalizer()
        
        # Initialize tokenizer
        if self.config.use_simple_tokenizer:
            self.tokenizer = SimpleTokenizer()
        else:
            self.tokenizer = KoreanTokenizer(backend=self.config.tokenizer_backend)
            
        # Initialize NER model based on global settings
        from ..config import get_settings
        settings = get_settings()
        
        if settings.use_mock_ner or self.config.use_mock_ner:
            self.ner_model = MockNERModel()
            logger.info("Using MockNERModel for development")
        else:
            # Check if API token is available
            api_token = settings.huggingface_api_token
            if not api_token:
                logger.warning("No Hugging Face API token provided. Falling back to MockNERModel")
                self.ner_model = MockNERModel()
            else:
                self.ner_model = KLUEBERTNERModel(
                    model_name=settings.ner_model_name,
                    api_token=api_token
                )
                logger.info("Using Multilingual NER model via Hugging Face API")
            
        # Sentiment model placeholder
        self.sentiment_model = None
        
        logger.info("NLP Pipeline initialized")
        
    async def process(self, text: str) -> NLPResult:
        """
        Process text through complete NLP pipeline
        
        Args:
            text: Input text
            
        Returns:
            NLPResult with extracted entities, sentiment, keywords, and risk score
        """
        start_time = time.time()
        
        try:
            # 1. Text normalization
            normalized_text = self.normalizer.clean_for_nlp(text)
            logger.debug(f"Normalized text length: {len(normalized_text)}")
            
            # 2. Tokenization
            tokens = self.tokenizer.tokenize(normalized_text)
            pos_tags = self.tokenizer.pos(normalized_text)
            
            # 3. Entity extraction (mock for now)
            entities = []
            if self.config.enable_ner:
                entities = await self._extract_entities(normalized_text, pos_tags)
                
            # 4. Sentiment analysis (mock for now)
            sentiment = Sentiment(label="neutral", score=0.5, probabilities={})
            if self.config.enable_sentiment:
                sentiment = await self._analyze_sentiment(normalized_text, tokens)
                
            # 5. Keyword extraction
            keywords = []
            if self.config.enable_keywords:
                keywords = await self._extract_keywords(normalized_text, pos_tags)
                
            # 6. Risk score calculation
            risk_score = self._calculate_risk_score(entities, sentiment, keywords)
            
            # Calculate processing time
            processing_time_ms = (time.time() - start_time) * 1000
            
            return NLPResult(
                entities=entities,
                sentiment=sentiment,
                keywords=keywords,
                risk_score=risk_score,
                processing_time_ms=processing_time_ms
            )
            
        except Exception as e:
            logger.error(f"Pipeline processing failed: {e}")
            # Return minimal result on error
            return NLPResult(
                entities=[],
                sentiment=Sentiment(label="neutral", score=0.0, probabilities={}),
                keywords=[],
                risk_score=0.0,
                processing_time_ms=(time.time() - start_time) * 1000
            )
            
    async def _extract_entities(self, text: str, pos_tags: List[tuple]) -> List[Entity]:
        """
        Extract named entities using configured NER model
        """
        try:
            # Use the configured NER model (MockNERModel or KLUEBERTNERModel)
            entities = self.ner_model.extract_entities(text)
            
            # Apply configuration limits
            entities = entities[:self.config.max_entities]
            
            # Filter by confidence threshold if specified
            if hasattr(self.config, 'ner_confidence_threshold'):
                entities = [
                    entity for entity in entities 
                    if entity.confidence >= self.config.ner_confidence_threshold
                ]
            
            logger.debug(f"Extracted {len(entities)} entities using {type(self.ner_model).__name__}")
            return entities
            
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            # Fallback to empty list
            return []
        
    async def _analyze_sentiment(self, text: str, tokens: List[str]) -> Sentiment:
        """
        Analyze sentiment (mock implementation for Week 1)
        """
        # Simple keyword-based sentiment for testing
        positive_words = ['증가', '상승', '호조', '성장', '개선', '긍정', '성공']
        negative_words = ['감소', '하락', '부진', '손실', '우려', '부정', '실패', '연체', '급락']
        
        positive_count = sum(1 for token in tokens if token in positive_words)
        negative_count = sum(1 for token in tokens if token in negative_words)
        
        total = positive_count + negative_count
        if total == 0:
            return Sentiment(
                label="neutral",
                score=0.5,
                probabilities={"positive": 0.33, "neutral": 0.34, "negative": 0.33}
            )
            
        positive_ratio = positive_count / total
        
        if positive_ratio > 0.6:
            label = "positive"
            score = positive_ratio
        elif positive_ratio < 0.4:
            label = "negative" 
            score = 1 - positive_ratio
        else:
            label = "neutral"
            score = 0.5
            
        return Sentiment(
            label=label,
            score=score,
            probabilities={
                "positive": positive_ratio,
                "neutral": 0.5 - abs(positive_ratio - 0.5),
                "negative": 1 - positive_ratio
            }
        )
        
    async def _extract_keywords(self, text: str, pos_tags: List[tuple]) -> List[Keyword]:
        """
        Extract keywords using POS tags
        """
        # Extract nouns as keywords
        nouns = self.tokenizer.nouns(text)
        
        # Filter by length
        keywords = [
            noun for noun in nouns 
            if len(noun) >= self.config.min_keyword_length
        ]
        
        # Simple frequency-based scoring
        keyword_scores = {}
        for keyword in keywords:
            keyword_scores[keyword] = keyword_scores.get(keyword, 0) + 1
            
        # Convert to Keyword objects
        keyword_objects = [
            Keyword(text=kw, score=score/len(keywords))
            for kw, score in keyword_scores.items()
        ]
        
        # Sort by score and return top N
        keyword_objects.sort(key=lambda x: x.score, reverse=True)
        return keyword_objects[:self.config.max_keywords]
        
    def _calculate_risk_score(self, entities: List[Entity], 
                            sentiment: Sentiment, 
                            keywords: List[Keyword]) -> float:
        """
        Calculate risk score based on extracted features
        """
        # Simple risk calculation for testing
        risk_score = 0.0
        
        # Sentiment contribution
        if sentiment.label == "negative":
            risk_score += 0.5 * sentiment.score
        elif sentiment.label == "positive":
            risk_score -= 0.2 * sentiment.score
            
        # Entity contribution (companies in negative context)
        company_count = sum(1 for e in entities if e.type == "COMPANY")
        if company_count > 0 and sentiment.label == "negative":
            risk_score += 0.3
            
        # Keyword contribution
        risk_keywords = ['손실', '연체', '급락', '화재', '사고', '우려', '하락']
        risk_keyword_count = sum(
            1 for kw in keywords 
            if any(risk_word in kw.text for risk_word in risk_keywords)
        )
        risk_score += 0.1 * risk_keyword_count
        
        # Normalize to 0-1 range
        risk_score = max(0.0, min(1.0, risk_score))
        
        return risk_score