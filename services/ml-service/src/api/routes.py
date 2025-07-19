"""
API routes for ML Service
"""
import time
import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional

from .models import (
    ProcessRequest, ProcessResponse,
    BatchProcessRequest, BatchProcessResponse,
    HealthResponse, ModelInfoResponse
)
from ..processors import NLPPipeline, ProcessingConfig
from ..processors.batch_processor import get_batch_processor, BatchRequest as BatchReq, BatchResult
from ..config import Settings, get_settings

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Global pipeline instance (initialized in main.py)
nlp_pipeline = None


def get_pipeline() -> NLPPipeline:
    """Dependency to get NLP pipeline"""
    if nlp_pipeline is None:
        raise HTTPException(status_code=503, detail="NLP pipeline not initialized")
    return nlp_pipeline


@router.post("/process", response_model=ProcessResponse)
async def process_text(
    request: ProcessRequest,
    pipeline: NLPPipeline = Depends(get_pipeline)
) -> ProcessResponse:
    """Process a single text through NLP pipeline"""
    try:
        result = await pipeline.process(request.text)
        return ProcessResponse(success=True, result=result)
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        return ProcessResponse(success=False, error=str(e))


@router.post("/batch", response_model=BatchProcessResponse)
async def process_batch(
    request: BatchProcessRequest,
    pipeline: NLPPipeline = Depends(get_pipeline)
) -> BatchProcessResponse:
    """Process multiple texts in batch using optimized batch processor"""
    start_time = time.time()
    
    try:
        # 배치 프로세서 가져오기
        batch_processor = get_batch_processor()
        
        # 배치 요청 생성
        batch_requests = []
        for i, text in enumerate(request.texts):
            batch_req = BatchReq(
                id=str(i),
                text=text,
                priority=0  # 기본 우선순위
            )
            batch_requests.append(batch_req)
        
        # 배치 처리 실행
        batch_results = await batch_processor.process_batch(batch_requests, pipeline)
        
        # 결과 변환
        results = []
        errors = []
        
        for batch_result in batch_results:
            if batch_result.error:
                results.append(None)
                errors.append(batch_result.error)
            else:
                results.append(batch_result.result)
                errors.append(None)
        
        total_time_ms = (time.time() - start_time) * 1000
        
        return BatchProcessResponse(
            success=all(e is None for e in errors),
            results=[r for r in results if r is not None],
            errors=errors,
            total_processing_time_ms=total_time_ms
        )
        
    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        return BatchProcessResponse(
            success=False,
            results=[],
            errors=[str(e)] * len(request.texts),
            total_processing_time_ms=(time.time() - start_time) * 1000
        )


@router.get("/health", response_model=HealthResponse)
async def health_check(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Health check endpoint"""
    # Check Kafka connection
    kafka_connected = False
    try:
        # TODO: Implement actual Kafka connection check
        kafka_connected = settings.use_mock_kafka
    except Exception:
        pass
        
    return HealthResponse(
        status="healthy" if nlp_pipeline is not None else "unhealthy",
        version=settings.service_version,
        model_loaded=nlp_pipeline is not None,
        kafka_connected=kafka_connected
    )


@router.get("/model/info", response_model=ModelInfoResponse)
async def model_info(
    settings: Settings = Depends(get_settings),
    pipeline: NLPPipeline = Depends(get_pipeline)
) -> ModelInfoResponse:
    """Get model information"""
    return ModelInfoResponse(
        version=settings.model_version,
        tokenizer_backend=pipeline.config.tokenizer_backend,
        supported_entity_types=["COMPANY", "PERSON", "EVENT"],
        supported_languages=["ko"],
        capabilities={
            "ner": pipeline.config.enable_ner,
            "sentiment": pipeline.config.enable_sentiment,
            "keywords": pipeline.config.enable_keywords
        }
    )


@router.get("/knowledge-base/search")
async def search_knowledge_base(
    query: str,
    entity_type: Optional[str] = None,
    pipeline: NLPPipeline = Depends(get_pipeline)
):
    """Search entities in knowledge base"""
    try:
        if hasattr(pipeline.ner_model, 'search_knowledge_base'):
            results = pipeline.ner_model.search_knowledge_base(query, entity_type)
            return {
                "query": query,
                "entity_type": entity_type,
                "results": [
                    {
                        "canonical_name": result.canonical_name,
                        "entity_type": result.entity_type,
                        "aliases": result.aliases,
                        "industry": getattr(result, 'industry', None),
                        "stock_code": getattr(result, 'stock_code', None),
                        "description": getattr(result, 'description', None)
                    }
                    for result in results
                ]
            }
        else:
            return {"error": "Knowledge base search not available"}
    except Exception as e:
        logger.error(f"Knowledge base search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge-base/entity/{canonical_name}")
async def get_entity_info(
    canonical_name: str,
    pipeline: NLPPipeline = Depends(get_pipeline)
):
    """Get detailed entity information"""
    try:
        if hasattr(pipeline.ner_model, 'get_entity_info'):
            entity_info = pipeline.ner_model.get_entity_info(canonical_name)
            if entity_info:
                return {
                    "canonical_name": entity_info.canonical_name,
                    "entity_type": entity_info.entity_type,
                    "aliases": entity_info.aliases,
                    "industry": getattr(entity_info, 'industry', None),
                    "stock_code": getattr(entity_info, 'stock_code', None),
                    "description": getattr(entity_info, 'description', None)
                }
            else:
                raise HTTPException(status_code=404, detail="Entity not found")
        else:
            return {"error": "Entity info lookup not available"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Entity info lookup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge-base/stats")
async def get_knowledge_base_stats(
    pipeline: NLPPipeline = Depends(get_pipeline)
):
    """Get knowledge base statistics"""
    try:
        if hasattr(pipeline.ner_model, 'get_knowledge_base_stats'):
            stats = pipeline.ner_model.get_knowledge_base_stats()
            return stats
        else:
            return {"error": "Knowledge base stats not available"}
    except Exception as e:
        logger.error(f"Knowledge base stats failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/stats")
async def get_cache_stats(
    pipeline: NLPPipeline = Depends(get_pipeline)
):
    """Get cache statistics"""
    try:
        if hasattr(pipeline.ner_model, 'get_cache_stats'):
            stats = pipeline.ner_model.get_cache_stats()
            return stats
        else:
            return {"error": "Cache stats not available"}
    except Exception as e:
        logger.error(f"Cache stats failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/clear")
async def clear_cache(
    pipeline: NLPPipeline = Depends(get_pipeline)
):
    """Clear all cached results"""
    try:
        if hasattr(pipeline.ner_model, 'clear_cache'):
            pipeline.ner_model.clear_cache()
            return {"message": "Cache cleared successfully"}
        else:
            return {"error": "Cache clear not available"}
    except Exception as e:
        logger.error(f"Cache clear failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/configure")
async def configure_cache(
    max_size: Optional[int] = None,
    ttl_seconds: Optional[int] = None,
    enabled: Optional[bool] = None,
    pipeline: NLPPipeline = Depends(get_pipeline)
):
    """Configure cache settings"""
    try:
        if hasattr(pipeline.ner_model, 'configure_cache'):
            pipeline.ner_model.configure_cache(max_size, ttl_seconds, enabled)
            return {"message": "Cache configured successfully"}
        else:
            return {"error": "Cache configuration not available"}
    except Exception as e:
        logger.error(f"Cache configuration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/batch/stats")
async def get_batch_stats():
    """Get batch processing statistics"""
    try:
        batch_processor = get_batch_processor()
        stats = batch_processor.get_adaptation_stats()
        return stats
    except Exception as e:
        logger.error(f"Batch stats failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch/configure")
async def configure_batch_processor(
    max_workers: Optional[int] = None,
    batch_size: Optional[int] = None
):
    """Configure batch processor settings"""
    try:
        from ..processors.batch_processor import configure_batch_processor
        
        # 현재 설정 가져오기
        current_processor = get_batch_processor()
        current_workers = current_processor.max_workers
        current_batch_size = current_processor.batch_size
        
        # 새 설정 적용
        new_workers = max_workers if max_workers is not None else current_workers
        new_batch_size = batch_size if batch_size is not None else current_batch_size
        
        configure_batch_processor(new_workers, new_batch_size)
        
        return {
            "message": "Batch processor configured successfully",
            "max_workers": new_workers,
            "batch_size": new_batch_size
        }
    except Exception as e:
        logger.error(f"Batch configuration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch/reset-stats")
async def reset_batch_stats():
    """Reset batch processing statistics"""
    try:
        batch_processor = get_batch_processor()
        batch_processor.reset_stats()
        return {"message": "Batch statistics reset successfully"}
    except Exception as e:
        logger.error(f"Batch stats reset failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def set_pipeline(pipeline: NLPPipeline):
    """Set the global pipeline instance"""
    global nlp_pipeline
    nlp_pipeline = pipeline