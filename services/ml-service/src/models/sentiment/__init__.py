"""Sentiment analysis models"""
from .mock_sentiment import MockSentimentModel

# Placeholder for KoBERT sentiment model (not yet implemented)
class KoBERTSentimentModel:
    """Placeholder for KoBERT sentiment model"""
    def __init__(self):
        pass
    
    def analyze_sentiment(self, text: str):
        return {"label": "neutral", "confidence": 0.5}

__all__ = ['MockSentimentModel', 'KoBERTSentimentModel']