"""Mock sentiment analysis model"""
import random
from typing import Dict, Any
from ...kafka.schemas import Sentiment

class MockSentimentModel:
    """Mock sentiment analysis model for testing"""
    
    def __init__(self):
        self.labels = ["positive", "negative", "neutral"]
        
    def analyze_sentiment(self, text: str) -> Sentiment:
        """
        Mock sentiment analysis
        
        Args:
            text: Input text
            
        Returns:
            Sentiment object
        """
        # Simple keyword-based mock
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["좋다", "훌륭", "성공", "증가", "확대", "성장"]):
            label = "positive"
            confidence = 0.8 + random.random() * 0.15
        elif any(word in text_lower for word in ["나쁘다", "실패", "감소", "하락", "위험", "문제"]):
            label = "negative"
            confidence = 0.8 + random.random() * 0.15
        else:
            label = "neutral"
            confidence = 0.5 + random.random() * 0.3
            
        return Sentiment(
            label=label,
            confidence=confidence
        )