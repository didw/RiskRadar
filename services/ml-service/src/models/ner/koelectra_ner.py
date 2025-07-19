"""
KoELECTRA NER Model
Leo97/KoELECTRA-small-v3-modu-ner 기반 한국어 개체명 인식 모델
"""
import time
import logging
import re
from typing import List, Dict, Any, Optional
import asyncio
from functools import lru_cache

try:
    import torch
    from transformers import AutoTokenizer, AutoModelForTokenClassification
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("Warning: transformers not available. Install with: pip install transformers torch")

from ...kafka.schemas import Entity
from .postprocessor import KoreanNERPostProcessor
from .entity_linker import KoreanEntityLinker
from .cache_manager import get_cache_manager

logger = logging.getLogger(__name__)


class KoELECTRANER:
    """KoELECTRA 기반 한국어 NER 모델"""
    
    def __init__(self, model_name: str = "Leo97/KoELECTRA-small-v3-modu-ner"):
        """모델 초기화"""
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.tokenizer = None
        self.is_loaded = False
        
        # 라벨 매핑 (Leo97/KoELECTRA-small-v3-modu-ner 모델 기준)
        self.label_mapping = {
            'O': 'O',
            'B-PS': 'PERSON',     # Person
            'I-PS': 'PERSON',
            'B-OG': 'COMPANY',    # Organization
            'I-OG': 'COMPANY',
            'B-LC': 'LOCATION',   # Location
            'I-LC': 'LOCATION',
            'B-FD': 'MISC',       # Field
            'I-FD': 'MISC',
            'B-CV': 'MISC',       # Civilization
            'I-CV': 'MISC',
            'B-DT': 'MISC',       # Date/Time
            'I-DT': 'MISC',
            'B-TI': 'MISC',       # Time
            'I-TI': 'MISC',
            'B-QT': 'MISC',       # Quantity
            'I-QT': 'MISC',
            'B-EV': 'EVENT',      # Event
            'I-EV': 'EVENT',
            'B-AM': 'MISC',       # Amount
            'I-AM': 'MISC',
            'B-PT': 'MISC',       # Part
            'I-PT': 'MISC',
            'B-MT': 'MISC',       # Material
            'I-MT': 'MISC',
            'B-TM': 'MISC',       # Term
            'I-TM': 'MISC',
            'B-AF': 'MISC',       # Artifact
            'I-AF': 'MISC',
            'B-TR': 'MISC',       # Tree
            'I-TR': 'MISC'
        }
        
        # 후처리 및 링킹
        self.postprocessor = KoreanNERPostProcessor(confidence_threshold=0.7)
        self.entity_linker = KoreanEntityLinker()
        self.cache_manager = get_cache_manager()
        
        # 성능 통계
        self.stats = {
            'total_calls': 0,
            'cache_hits': 0,
            'avg_processing_time': 0,
            'model_load_time': 0
        }
        
        # 모델 로드 시도
        if TRANSFORMERS_AVAILABLE:
            self._load_model()
        else:
            logger.warning("Transformers not available - KoELECTRA NER will not work")
    
    def _load_model(self):
        """모델 로드"""
        try:
            start_time = time.time()
            logger.info(f"Loading KoELECTRA model: {self.model_name}")
            
            # 토크나이저 로드
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            # 모델 로드
            self.model = AutoModelForTokenClassification.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            
            load_time = time.time() - start_time
            self.stats['model_load_time'] = load_time
            self.is_loaded = True
            
            logger.info(f"KoELECTRA model loaded successfully in {load_time:.2f}s on {self.device}")
            
        except Exception as e:
            logger.error(f"Failed to load KoELECTRA model: {e}")
            self.is_loaded = False
    
    @lru_cache(maxsize=128)
    def _get_label_list(self) -> List[str]:
        """라벨 리스트 캐싱"""
        if not self.is_loaded:
            return []
        return list(self.model.config.id2label.values())
    
    async def extract_entities(self, text: str) -> List[Entity]:
        """
        텍스트에서 엔티티 추출
        
        Args:
            text: 입력 텍스트
            
        Returns:
            추출된 엔티티 리스트
        """
        start_time = time.time()
        self.stats['total_calls'] += 1
        
        if not self.is_loaded:
            logger.warning("Model not loaded - returning empty results")
            return []
        
        if not text.strip():
            return []
        
        try:
            # 캐시 확인
            model_config = {
                "model_name": "koelectra_ner",
                "model_path": self.model_name,
                "confidence_threshold": 0.7,
                "version": "1.0"
            }
            
            cached_result = self.cache_manager.get_cached_result(text, model_config)
            if cached_result is not None:
                self.stats['cache_hits'] += 1
                processing_time = (time.time() - start_time) * 1000
                logger.debug(f"Cache hit: returned {len(cached_result)} entities in {processing_time:.2f}ms")
                return cached_result
            
            # 토크나이저로 인코딩
            encoding = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True,
                return_offsets_mapping=True,
                return_special_tokens_mask=True
            )
            
            # GPU로 이동
            input_ids = encoding['input_ids'].to(self.device)
            attention_mask = encoding['attention_mask'].to(self.device)
            offset_mapping = encoding['offset_mapping'][0]
            special_tokens_mask = encoding['special_tokens_mask'][0]
            
            # 모델 추론
            with torch.no_grad():
                outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
                predicted_token_class_ids = predictions.argmax(dim=-1)
            
            # 토큰 단위 예측을 문자 단위로 변환
            entities = self._decode_predictions(
                text,
                predicted_token_class_ids[0],
                predictions[0],
                offset_mapping,
                special_tokens_mask
            )
            
            # 후처리 적용
            original_count = len(entities)
            entities = self.postprocessor.process_entities(entities, text)
            
            # 엔티티 링킹
            entities = self.entity_linker.link_entities(entities)
            
            processing_time = (time.time() - start_time) * 1000
            self.stats['avg_processing_time'] = (
                self.stats['avg_processing_time'] * (self.stats['total_calls'] - 1) + processing_time
            ) / self.stats['total_calls']
            
            # 결과 캐싱
            self.cache_manager.cache_result(text, entities, processing_time, model_config)
            
            logger.debug(f"Extracted {len(entities)} entities ({original_count} raw) in {processing_time:.2f}ms")
            
            return entities
            
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return []
    
    def _decode_predictions(
        self,
        text: str,
        predictions: torch.Tensor,
        probabilities: torch.Tensor,
        offset_mapping: torch.Tensor,
        special_tokens_mask: torch.Tensor
    ) -> List[Entity]:
        """예측 결과를 엔티티로 디코딩"""
        entities = []
        current_entity = None
        
        for i, (pred_id, prob_tensor, offset, is_special) in enumerate(
            zip(predictions, probabilities, offset_mapping, special_tokens_mask)
        ):
            # 특수 토큰 건너뛰기
            if is_special or offset[0] == offset[1]:
                continue
            
            # 라벨 디코딩
            label = self.model.config.id2label[pred_id.item()]
            confidence = prob_tensor[pred_id].item()
            
            # 신뢰도가 낮으면 건너뛰기
            if confidence < 0.5:
                if current_entity:
                    entities.append(current_entity)
                    current_entity = None
                continue
            
            # BIO 태깅 처리
            if label.startswith('B-'):
                # 이전 엔티티 완료
                if current_entity:
                    entities.append(current_entity)
                
                # 새 엔티티 시작
                entity_type = self.label_mapping.get(label, 'MISC')
                start_pos = offset[0].item()
                end_pos = offset[1].item()
                
                current_entity = Entity(
                    text=text[start_pos:end_pos],
                    type=entity_type,
                    start=start_pos,
                    end=end_pos,
                    confidence=confidence
                )
                
            elif label.startswith('I-') and current_entity:
                # 기존 엔티티 확장
                entity_type = self.label_mapping.get(label, 'MISC')
                if current_entity.type == entity_type:
                    end_pos = offset[1].item()
                    current_entity.end = end_pos
                    current_entity.text = text[current_entity.start:end_pos]
                    current_entity.confidence = (current_entity.confidence + confidence) / 2
                else:
                    # 타입이 다르면 이전 엔티티 완료하고 새로 시작
                    entities.append(current_entity)
                    start_pos = offset[0].item()
                    end_pos = offset[1].item()
                    
                    current_entity = Entity(
                        text=text[start_pos:end_pos],
                        type=entity_type,
                        start=start_pos,
                        end=end_pos,
                        confidence=confidence
                    )
            else:
                # O 태그 또는 다른 라벨
                if current_entity:
                    entities.append(current_entity)
                    current_entity = None
        
        # 마지막 엔티티 추가
        if current_entity:
            entities.append(current_entity)
        
        # 엔티티 정리 및 검증
        return self._clean_entities(entities, text)
    
    def _clean_entities(self, entities: List[Entity], text: str) -> List[Entity]:
        """엔티티 정리 및 검증"""
        cleaned_entities = []
        
        for entity in entities:
            # 텍스트 범위 검증
            if entity.start < 0 or entity.end > len(text) or entity.start >= entity.end:
                continue
            
            # 실제 텍스트와 매칭 확인
            actual_text = text[entity.start:entity.end]
            if actual_text != entity.text:
                entity.text = actual_text
            
            # 텍스트 정리
            entity.text = entity.text.strip()
            if not entity.text:
                continue
            
            # 한글/영문 엔티티만 허용
            if not re.search(r'[가-힣a-zA-Z]', entity.text):
                continue
            
            # 너무 짧거나 긴 엔티티 제외
            if len(entity.text) < 2 or len(entity.text) > 20:
                continue
            
            cleaned_entities.append(entity)
        
        return cleaned_entities
    
    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보 반환"""
        return {
            "model_name": "koelectra_ner",
            "model_path": self.model_name,
            "model_type": "transformer",
            "framework": "transformers",
            "supported_entity_types": list(set(self.label_mapping.values())),
            "language": "ko",
            "version": "1.0.0",
            "device": self.device,
            "is_loaded": self.is_loaded,
            "transformers_available": TRANSFORMERS_AVAILABLE,
            "statistics": self.stats.copy()
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """성능 통계 반환"""
        return self.stats.copy()
    
    def update_confidence_threshold(self, threshold: float):
        """신뢰도 임계값 업데이트"""
        self.postprocessor.confidence_threshold = threshold
        logger.info(f"Updated confidence threshold to {threshold}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 반환"""
        return self.cache_manager.get_cache_stats()
    
    def clear_cache(self):
        """캐시 정리"""
        self.cache_manager.invalidate_cache()
        logger.info("Cache cleared")
    
    def is_model_ready(self) -> bool:
        """모델 준비 상태 확인"""
        return self.is_loaded and TRANSFORMERS_AVAILABLE
    
    def get_supported_labels(self) -> List[str]:
        """지원하는 라벨 리스트 반환"""
        if not self.is_loaded:
            return []
        return self._get_label_list()