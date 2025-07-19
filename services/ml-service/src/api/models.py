"""
API request/response models
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..kafka.schemas import Entity, Sentiment, Keyword, NLPResult


class ProcessRequest(BaseModel):
    """Request model for text processing"""
    text: str = Field(..., description="Text to process")
    options: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Processing options"
    )


class ProcessResponse(BaseModel):
    """Response model for text processing"""
    success: bool = Field(..., description="Processing success status")
    result: Optional[NLPResult] = Field(None, description="Processing result")
    error: Optional[str] = Field(None, description="Error message if failed")
    

class BatchProcessRequest(BaseModel):
    """Request model for batch processing"""
    texts: List[str] = Field(..., description="List of texts to process")
    options: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Processing options"
    )


class BatchProcessResponse(BaseModel):
    """Response model for batch processing"""
    success: bool = Field(..., description="Processing success status")
    results: List[NLPResult] = Field(default_factory=list, description="Processing results")
    errors: List[Optional[str]] = Field(default_factory=list, description="Error messages")
    total_processing_time_ms: float = Field(..., description="Total processing time")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    model_loaded: bool = Field(..., description="Model loading status")
    kafka_connected: bool = Field(..., description="Kafka connection status")
    timestamp: datetime = Field(default_factory=datetime.now)
    

class ModelInfoResponse(BaseModel):
    """Model information response"""
    version: str = Field(..., description="Model version")
    tokenizer_backend: str = Field(..., description="Tokenizer backend")
    supported_entity_types: List[str] = Field(..., description="Supported entity types")
    supported_languages: List[str] = Field(..., description="Supported languages")
    capabilities: Dict[str, bool] = Field(..., description="Model capabilities")