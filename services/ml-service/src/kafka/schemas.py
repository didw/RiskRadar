"""
Data schemas for Kafka messages
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class RawNewsModel(BaseModel):
    """Schema for raw news from data-service"""
    id: str = Field(..., description="Unique news identifier")
    source: str = Field(..., description="News source (e.g., chosun, joongang)")
    title: str = Field(..., description="News title")
    content: str = Field(..., description="News content")
    published_at: str = Field(..., description="Publication timestamp")
    url: str = Field(..., description="Original article URL")


class Entity(BaseModel):
    """Extracted entity"""
    text: str = Field(..., description="Entity text")
    type: str = Field(..., description="Entity type (COMPANY, PERSON, EVENT)")
    start: int = Field(..., description="Start position in text")
    end: int = Field(..., description="End position in text")
    confidence: float = Field(..., description="Confidence score")


class Sentiment(BaseModel):
    """Sentiment analysis result"""
    label: str = Field(..., description="Sentiment label (positive, neutral, negative)")
    score: float = Field(..., description="Confidence score")
    probabilities: Dict[str, float] = Field(
        default_factory=dict,
        description="Probability distribution"
    )


class Keyword(BaseModel):
    """Extracted keyword"""
    text: str = Field(..., description="Keyword text")
    score: float = Field(..., description="TF-IDF or importance score")


class RiskAnalysis(BaseModel):
    """Enhanced risk analysis result"""
    overall_risk_score: float = Field(0.0, description="Overall risk score (0-1)")
    risk_level: str = Field("MINIMAL", description="Risk level (MINIMAL, LOW, MEDIUM, HIGH, CRITICAL)")
    category_scores: Dict[str, float] = Field(default_factory=dict, description="Category-wise risk scores")
    detected_events: List[Dict[str, Any]] = Field(default_factory=list, description="Detected risk events")
    risk_summary: str = Field("", description="Risk summary description")


class NLPResult(BaseModel):
    """Complete NLP processing result"""
    entities: List[Entity] = Field(default_factory=list)
    sentiment: Sentiment
    keywords: List[Keyword] = Field(default_factory=list)
    risk_score: float = Field(0.0, description="Risk score (0-1)")
    risk_analysis: Optional[RiskAnalysis] = Field(None, description="Enhanced risk analysis")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")


class EnrichedNewsModel(BaseModel):
    """Schema for enriched news to graph-service"""
    original: RawNewsModel = Field(..., description="Original news data")
    nlp: NLPResult = Field(..., description="NLP processing results")
    processed_at: datetime = Field(..., description="Processing timestamp")
    ml_service_version: str = Field(..., description="ML service version")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }