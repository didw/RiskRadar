"""
KoELECTRA Naver NER model implementation using local model
"""
import time
import logging
import torch
from typing import List, Dict, Any, Optional
from transformers import ElectraTokenizerFast, ElectraForTokenClassification
from ...kafka.schemas import Entity
from .postprocessor import KoreanNERPostProcessor
from .entity_linker import KoreanEntityLinker
from .cache_manager import get_cache_manager
from .entity_splitter import KoreanEntitySplitter

logger = logging.getLogger(__name__)


class KoElectraNaverNERModel:
    """KoELECTRA Naver NER model using local model"""
    
    def __init__(self, 
                 model_name: str = "monologg/koelectra-base-v3-naver-ner",
                 device: str = "cpu"):
        """
        Initialize KoELECTRA Naver NER model
        
        Args:
            model_name: HuggingFace model name
            device: Device to use (cpu or cuda)
        """
        self.model_name = model_name
        self.device = device
        
        try:
            logger.info(f"Loading KoELECTRA Naver NER model: {model_name}")
            
            # Load tokenizer and model
            self.tokenizer = ElectraTokenizerFast.from_pretrained(model_name)
            self.model = ElectraForTokenClassification.from_pretrained(model_name)
            self.model.to(device)
            self.model.eval()
            
            # Get label mappings from model config
            self.id2label = self.model.config.id2label
            self.label2id = self.model.config.label2id
            
            logger.info(f"Model loaded successfully. Labels: {list(self.id2label.values())}")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
        
        # Entity label mapping for Naver NER
        # Based on Naver NER tagset
        self.label_mapping = {
            'PER': 'PERSON',      # 인물
            'LOC': 'LOCATION',    # 장소
            'ORG': 'COMPANY',     # 기관/조직
            'POH': 'OTHER',       # 기타
            'DAT': 'DATE',        # 날짜
            'TIM': 'TIME',        # 시간
            'DUR': 'DURATION',    # 기간
            'MNY': 'MONEY',       # 통화
            'PNT': 'PERCENT',     # 백분율
            'QTY': 'QUANTITY',    # 기타 수량
            'ORD': 'ORDINAL',     # 서수
            'CVL': 'CIVILIZATION', # 문명
            'ANM': 'ANIMAL',      # 동물
            'PLT': 'PLANT',       # 식물
            'MAT': 'MATERIAL',    # 물질
            'TRM': 'TERM',        # 용어
            'EVT': 'EVENT',       # 사건
            'FLD': 'FIELD',       # 분야
            'AFW': 'ARTIFACT',    # 인공물
            'O': 'O'
        }
        
        # Target entities for our use case
        self.target_entities = {'PERSON', 'COMPANY', 'EVENT'}
        
        # Initialize post-processor, splitter and entity linker
        self.postprocessor = KoreanNERPostProcessor(confidence_threshold=0.5)
        self.entity_splitter = KoreanEntitySplitter()
        self.entity_linker = KoreanEntityLinker()
        
        # Initialize cache manager
        self.cache_manager = get_cache_manager()
        
        logger.info(f"KoELECTRA Naver NER model initialized on {device}")
        
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
            
            # Tokenize
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                padding=True,
                max_length=512
            )
            
            # Move to device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Run inference
            with torch.no_grad():
                outputs = self.model(**inputs)
                predictions = torch.argmax(outputs.logits, dim=-1)
            
            # Convert predictions to entities
            tokens = self.tokenizer.convert_ids_to_tokens(inputs['input_ids'][0])
            
            # Get offset mappings for accurate position
            encoding = self.tokenizer(
                text,
                return_offsets_mapping=True,
                truncation=True,
                max_length=512,
                return_tensors="pt"
            )
            offset_mapping = encoding['offset_mapping'][0].tolist()
            
            entities = []
            current_entity = None
            token_idx = 0  # Track position in offset_mapping
            
            for idx, (token, pred_id) in enumerate(zip(tokens, predictions[0].tolist())):
                if token in ['[CLS]', '[SEP]', '[PAD]']:  # Special tokens
                    token_idx += 1
                    continue
                    
                label = self.id2label.get(pred_id, 'O')
                
                # Handle BIO tagging (format is "PER-B" not "B-PER")
                if label.endswith('-B'):
                    # Save previous entity if exists
                    if current_entity and current_entity['type'] in self.target_entities:
                        entities.append(Entity(
                            text=current_entity['text'],
                            type=current_entity['type'],
                            start=current_entity['start'],
                            end=current_entity['end'],
                            confidence=0.9  # High confidence for this model
                        ))
                    
                    # Start new entity
                    entity_label = label[:-2]  # Remove "-B"
                    entity_type = self.label_mapping.get(entity_label, 'OTHER')
                    if entity_type in self.target_entities and token_idx < len(offset_mapping):
                        current_entity = {
                            'text': token.replace('##', ''),
                            'type': entity_type,
                            'start': offset_mapping[token_idx][0],
                            'end': offset_mapping[token_idx][1]
                        }
                    else:
                        current_entity = None
                        
                elif label.endswith('-I') and current_entity:
                    # Continue current entity
                    entity_label = label[:-2]  # Remove "-I"
                    entity_type = self.label_mapping.get(entity_label, 'OTHER')
                    if entity_type == current_entity['type']:
                        # Handle space or word boundaries
                        if token.startswith('##'):
                            current_entity['text'] += token.replace('##', '')
                        else:
                            current_entity['text'] += ' ' + token
                        if token_idx < len(offset_mapping):
                            current_entity['end'] = offset_mapping[token_idx][1]
                    else:
                        # Type mismatch, save current and reset
                        if current_entity['type'] in self.target_entities:
                            entities.append(Entity(
                                text=current_entity['text'],
                                type=current_entity['type'],
                                start=current_entity['start'],
                                end=current_entity['end'],
                                confidence=0.9
                            ))
                        current_entity = None
                else:
                    # 'O' label or other
                    if current_entity and current_entity['type'] in self.target_entities:
                        entities.append(Entity(
                            text=current_entity['text'],
                            type=current_entity['type'],
                            start=current_entity['start'],
                            end=current_entity['end'],
                            confidence=0.9
                        ))
                    current_entity = None
                
                token_idx += 1
            
            # Don't forget the last entity
            if current_entity and current_entity['type'] in self.target_entities:
                entities.append(Entity(
                    text=current_entity['text'],
                    type=current_entity['type'],
                    start=current_entity['start'],
                    end=current_entity['end'],
                    confidence=0.9
                ))
            
            # Apply entity splitting first (for conjunctive entities)
            entities = self.entity_splitter.split_entities(entities)
            
            # Apply post-processing
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
        
        for text in texts:
            entities = self.extract_entities(text)
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
            "model_type": "koelectra_naver_ner",
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