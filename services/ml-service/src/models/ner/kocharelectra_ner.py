"""
KoCharELECTRA NER model implementation using local model
"""
import time
import logging
import torch
from typing import List, Dict, Any, Optional
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
from ...kafka.schemas import Entity
from .postprocessor import KoreanNERPostProcessor
from .entity_linker import KoreanEntityLinker
from .cache_manager import get_cache_manager

logger = logging.getLogger(__name__)


class KoCharELECTRANERModel:
    """KoCharELECTRA NER model using local model"""
    
    def __init__(self, 
                 model_name: str = "monologg/kocharelectra-base-modu-ner-all",
                 device: str = "cpu"):
        """
        Initialize KoCharELECTRA NER model
        
        Args:
            model_name: HuggingFace model name
            device: Device to use (cpu or cuda)
        """
        self.model_name = model_name
        self.device = device
        
        try:
            logger.info(f"Loading KoCharELECTRA model: {model_name}")
            
            # Load tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForTokenClassification.from_pretrained(model_name)
            self.model.to(device)
            self.model.eval()
            
            # Create NER pipeline
            self.nlp = pipeline(
                "ner",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if device == "cuda" else -1,
                aggregation_strategy="simple"
            )
            
            # Get label mappings from model config
            self.id2label = self.model.config.id2label
            self.label2id = self.model.config.label2id
            
            logger.info(f"Model loaded successfully. Labels: {list(self.id2label.values())}")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
        
        # Entity label mapping for modu NER
        # https://github.com/monologg/KoCharELECTRA
        self.label_mapping = {
            'PS': 'PERSON',       # 인물
            'LC': 'LOCATION',     # 장소
            'OG': 'COMPANY',      # 기관/조직
            'DT': 'DATE',         # 날짜
            'TI': 'TIME',         # 시간
            'QT': 'QUANTITY',     # 수량
            'EV': 'EVENT',        # 사건
            'FD': 'FIELD',        # 분야
            'TR': 'THEORY',       # 이론
            'AF': 'ARTIFACT',     # 인공물
            'CV': 'CIVILIZATION', # 문명
            'PT': 'PLANT',        # 식물
            'AM': 'ANIMAL',       # 동물
            'MT': 'MATERIAL',     # 물질
            'TM': 'TERM',         # 용어
            'O': 'O'
        }
        
        # Target entities for our use case
        self.target_entities = {'PERSON', 'COMPANY', 'EVENT'}
        
        # Initialize post-processor and entity linker
        self.postprocessor = KoreanNERPostProcessor(confidence_threshold=0.5)
        self.entity_linker = KoreanEntityLinker()
        
        # Initialize cache manager
        self.cache_manager = get_cache_manager()
        
        logger.info(f"KoCharELECTRA NER model initialized on {device}")
        
    def extract_entities(self, text: str) -> List[Entity]:
        """
        Extract entities from Korean text using local model
        
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
            
            # Run NER pipeline
            ner_results = self.nlp(text)
            
            if not ner_results:
                logger.warning("No results from model")
                return []
            
            # Convert to our Entity format
            entities = []
            for result in ner_results:
                # Extract entity type from label
                label = result.get('entity_group', '')
                if label.startswith('B-') or label.startswith('I-'):
                    label = label[2:]
                
                entity_type = self.label_mapping.get(label, 'OTHER')
                
                # Skip if not target entity type
                if entity_type not in self.target_entities:
                    continue
                    
                # Create Entity object
                entity = Entity(
                    text=result.get('word', '').replace('##', ''),  # Remove subword tokens
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
            
            logger.debug(f"Extracted {len(entities)} entities ({original_count} raw) in {processing_time:.2f}ms")
            
            return entities
            
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return []
            
    def batch_extract_entities(self, texts: List[str]) -> List[List[Entity]]:
        """
        Extract entities from multiple texts
        
        Args:
            texts: List of input texts
            
        Returns:
            List of entity lists
        """
        results = []
        
        # Process in batches for efficiency
        batch_size = 8
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            # Run pipeline on batch
            batch_results = self.nlp(batch)
            
            # Process each text's results
            for text, text_results in zip(batch, batch_results):
                entities = []
                
                for result in text_results:
                    # Extract entity type from label
                    label = result.get('entity_group', '')
                    if label.startswith('B-') or label.startswith('I-'):
                        label = label[2:]
                    
                    entity_type = self.label_mapping.get(label, 'OTHER')
                    
                    # Skip if not target entity type
                    if entity_type not in self.target_entities:
                        continue
                        
                    # Create Entity object
                    entity = Entity(
                        text=result.get('word', '').replace('##', ''),
                        type=entity_type,
                        start=result.get('start', 0),
                        end=result.get('end', 0),
                        confidence=result.get('score', 0.0)
                    )
                    
                    entities.append(entity)
                
                # Apply post-processing
                entities = self.postprocessor.process_entities(entities, text)
                entities = self.entity_linker.link_entities(entities)
                
                results.append(entities)
        
        return results
        
    def update_confidence_threshold(self, threshold: float):
        """Update confidence threshold for post-processing"""
        self.postprocessor.confidence_threshold = threshold
        logger.info(f"Updated confidence threshold to {threshold}")
        
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "model_name": self.model_name,
            "model_type": "kocharelectra_ner_local",
            "supported_entity_types": list(self.target_entities),
            "all_labels": list(self.label_mapping.keys()),
            "language": "ko",
            "device": self.device,
            "version": "1.0.0"
        }
    
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