"""
KoELECTRA NER model implementation using Hugging Face Inference API
"""
import time
import logging
import requests
import json
from typing import List, Dict, Any, Optional
from ...kafka.schemas import Entity
from .postprocessor import KoreanNERPostProcessor
from .entity_linker import KoreanEntityLinker
from .cache_manager import get_cache_manager

logger = logging.getLogger(__name__)


class KLUEBERTNERModel:
    """Multilingual NER model using Hugging Face Inference API"""
    
    def __init__(self, 
                 model_name: str = "koorukuroo/korean_bert_ner",
                 api_token: str = ""):
        """
        Initialize Multilingual NER model with Hugging Face Inference API
        
        Args:
            model_name: HuggingFace model name
            api_token: Hugging Face API token
        """
        self.model_name = model_name
        self.api_token = api_token
        self.api_url = f"https://api-inference.huggingface.co/models/{model_name}"
        
        # Request headers
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        
        # Entity label mapping (Naver NER labels)
        # https://github.com/naver/nlp-challenge/tree/master/missions/ner
        self.label_mapping = {
            'PER': 'PERSON',      # 인물
            'FLD': 'FIELD',       # 분야
            'AFW': 'ARTIFACT',    # 인공물
            'ORG': 'COMPANY',     # 기관/조직
            'LOC': 'LOCATION',    # 장소
            'CVL': 'CIVILIZATION', # 문명
            'DAT': 'DATE',        # 날짜
            'TIM': 'TIME',        # 시간
            'NUM': 'NUMBER',      # 숫자
            'EVT': 'EVENT',       # 사건
            'ANM': 'ANIMAL',      # 동물
            'PLT': 'PLANT',       # 식물
            'MAT': 'MATERIAL',    # 물질
            'TRM': 'TERM',        # 용어
            'O': 'O'
        }
        
        # Target entities for our use case
        self.target_entities = {'PERSON', 'COMPANY', 'EVENT'}
        
        # API configuration
        self.request_timeout = 30  # seconds
        self.max_retries = 3
        
        # Initialize post-processor and entity linker
        self.postprocessor = KoreanNERPostProcessor(confidence_threshold=0.5)
        self.entity_linker = KoreanEntityLinker()
        
        # Initialize cache manager
        self.cache_manager = get_cache_manager()
        
        logger.info(f"Multilingual NER model initialized with {model_name} via Hugging Face API")
        
    def test_api_connection(self) -> bool:
        """
        Test connection to Hugging Face Inference API
        
        Returns:
            bool: True if API is accessible, False otherwise
        """
        try:
            # Test with a simple Korean text
            test_payload = {
                "inputs": "안녕하세요"
            }
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=test_payload,
                timeout=self.request_timeout
            )
            
            if response.status_code == 200:
                logger.info("Hugging Face API connection successful")
                return True
            else:
                logger.warning(f"API test failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to Hugging Face API: {e}")
            return False
            
    def extract_entities(self, text: str) -> List[Entity]:
        """
        Extract entities from Korean text using Hugging Face Inference API with caching
        
        Args:
            text: Input Korean text
            
        Returns:
            List of Entity objects
        """
        start_time = time.time()
        
        try:
            # Check cache first
            model_config = {
                "model_name": self.model_name,
                "confidence_threshold": 0.5
            }
            
            cached_result = self.cache_manager.get_cached_result(text, model_config)
            if cached_result is not None:
                processing_time = (time.time() - start_time) * 1000
                logger.debug(f"Cache hit: returned {len(cached_result)} entities in {processing_time:.2f}ms")
                return cached_result
            
            # Cache miss - proceed with API call
            # Prepare API request
            payload = {
                "inputs": text,
                "options": {
                    "wait_for_model": True
                }
            }
            
            # Make API request with retries
            ner_results = self._make_api_request(payload)
            
            if not ner_results:
                logger.warning("No results from API")
                return []
            
            # Convert to our Entity format
            entities = []
            for result in ner_results:
                # Map API labels to our entity types
                entity_type = self._map_label_to_type(result.get('entity_group', result.get('entity', '')))
                
                # Skip if not target entity type
                if entity_type not in self.target_entities:
                    continue
                    
                # Create Entity object
                entity = Entity(
                    text=result.get('word', ''),
                    type=entity_type,
                    start=result.get('start', 0),
                    end=result.get('end', 0),
                    confidence=result.get('score', 0.0)
                )
                
                entities.append(entity)
                
            # Apply comprehensive post-processing
            original_count = len(entities)
            entities = self.postprocessor.process_entities(entities, text)
            
            # Apply entity linking
            entities = self.entity_linker.link_entities(entities)
            
            processing_time = (time.time() - start_time) * 1000
            
            # Cache the result
            self.cache_manager.cache_result(text, entities, processing_time, model_config)
            
            logger.debug(f"Extracted {len(entities)} entities ({original_count} raw) in {processing_time:.2f}ms via API")
            
            return entities
            
        except Exception as e:
            logger.error(f"Entity extraction via API failed: {e}")
            return []
            
    def _make_api_request(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Make API request with retry logic
        
        Args:
            payload: Request payload
            
        Returns:
            List of NER results
        """
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload,
                    timeout=self.request_timeout
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 503:
                    # Model is loading, wait and retry
                    logger.info(f"Model loading, attempt {attempt + 1}/{self.max_retries}")
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    logger.error(f"API request failed with status {response.status_code}: {response.text}")
                    return []
                    
            except requests.exceptions.Timeout:
                logger.warning(f"API request timeout, attempt {attempt + 1}/{self.max_retries}")
                if attempt < self.max_retries - 1:
                    time.sleep(1)
                    continue
            except Exception as e:
                logger.error(f"API request error: {e}")
                return []
                
        logger.error("All API request attempts failed")
        return []
            
    def _map_label_to_type(self, label: str) -> str:
        """Map Naver NER label to our entity type"""
        # The label format from the API might include entity prefix
        # Extract the base label
        label = label.upper()
        
        # Remove any prefix like "LABEL_" or numbers
        if '_' in label:
            parts = label.split('_')
            base_label = parts[-1]
        else:
            base_label = label
            
        # Direct mapping
        return self.label_mapping.get(base_label, 'OTHER')
        
    def update_confidence_threshold(self, threshold: float):
        """Update confidence threshold for post-processing"""
        self.postprocessor.confidence_threshold = threshold
        logger.info(f"Updated confidence threshold to {threshold}")
        
    def get_postprocessing_stats(self, original_entities: List[Entity], 
                                processed_entities: List[Entity]) -> Dict[str, int]:
        """Get post-processing statistics"""
        return self.postprocessor.get_statistics(original_entities, processed_entities)
    
    def search_knowledge_base(self, query: str, entity_type: Optional[str] = None):
        """Search entities in knowledge base"""
        return self.entity_linker.search_entities(query, entity_type)
    
    def get_entity_info(self, canonical_name: str):
        """Get detailed entity information"""
        return self.entity_linker.get_entity_info(canonical_name)
    
    def get_knowledge_base_stats(self) -> Dict[str, int]:
        """Get knowledge base statistics"""
        return self.entity_linker.get_statistics()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return self.cache_manager.get_cache_stats()
    
    def clear_cache(self):
        """Clear all cached results"""
        self.cache_manager.invalidate_cache()
        logger.info("Cache cleared")
    
    def configure_cache(self, max_size: int = None, ttl_seconds: int = None, enabled: bool = None):
        """Configure cache settings"""
        if max_size is not None:
            self.cache_manager.resize_cache(max_size)
        if ttl_seconds is not None:
            self.cache_manager.ttl_seconds = ttl_seconds
        if enabled is not None:
            if enabled:
                self.cache_manager.enable_cache()
            else:
                self.cache_manager.disable_cache()
        
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "model_name": self.model_name,
            "model_type": "koelectra_ner_api",
            "supported_entity_types": list(self.target_entities),
            "language": "ko",
            "api_url": self.api_url,
            "version": "1.0.0",
            "api_available": self.test_api_connection()
        }