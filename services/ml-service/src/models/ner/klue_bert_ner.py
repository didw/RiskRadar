"""
KLUE-BERT NER Model Implementation
로컬에서 실행되는 KLUE-BERT 기반 한국어 개체명 인식 모델
"""
import time
import logging
import asyncio
from typing import List, Dict, Any, Optional
import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
import numpy as np

from ...kafka.schemas import Entity
from .postprocessor import KoreanNERPostProcessor
from .entity_linker import KoreanEntityLinker
from .cache_manager import get_cache_manager

logger = logging.getLogger(__name__)


class KLUEBERTNERModel:
    """KLUE-BERT 기반 한국어 NER 모델"""
    
    def __init__(self, 
                 model_name: str = "klue/bert-base",
                 model_path: Optional[str] = None,
                 device: str = "cpu"):
        """
        KLUE-BERT NER 모델 초기화
        
        Args:
            model_name: HuggingFace 모델 이름
            model_path: 로컬 모델 경로 (선택사항)
            device: 실행 장치 ('cpu' 또는 'cuda')
        """
        self.model_name = model_name
        self.model_path = model_path or model_name
        self.device = device
        
        # KLUE NER 레이블 매핑
        # KLUE 데이터셋의 표준 BIO 태깅 체계
        self.label_mapping = {
            'B-PER': 'PERSON',      # 인물 시작
            'I-PER': 'PERSON',      # 인물 중간/끝
            'B-ORG': 'COMPANY',     # 기관/조직 시작
            'I-ORG': 'COMPANY',     # 기관/조직 중간/끝
            'B-LOC': 'LOCATION',    # 장소 시작
            'I-LOC': 'LOCATION',    # 장소 중간/끝
            'B-DAT': 'DATE',        # 날짜 시작
            'I-DAT': 'DATE',        # 날짜 중간/끝
            'B-TIM': 'TIME',        # 시간 시작
            'I-TIM': 'TIME',        # 시간 중간/끝
            'B-NUM': 'NUMBER',      # 숫자 시작
            'I-NUM': 'NUMBER',      # 숫자 중간/끝
            'B-EVT': 'EVENT',       # 사건 시작
            'I-EVT': 'EVENT',       # 사건 중간/끝
            'O': 'O'                # 개체가 아님
        }
        
        # 관심 있는 엔티티 타입
        self.target_entities = {'PERSON', 'COMPANY', 'EVENT'}
        
        # 모델 초기화
        self.tokenizer = None
        self.model = None
        self.ner_pipeline = None
        self._load_model()
        
        # 후처리 및 엔티티 링킹
        self.postprocessor = KoreanNERPostProcessor(confidence_threshold=0.7)
        self.entity_linker = KoreanEntityLinker()
        
        # 캐시 매니저
        self.cache_manager = get_cache_manager()
        
        logger.info(f"KLUE-BERT NER model initialized on {device}")
    
    def _load_model(self):
        """모델 로딩"""
        try:
            logger.info(f"Loading KLUE-BERT model from {self.model_path}")
            
            # 토크나이저 로딩
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                use_fast=True
            )
            
            # 모델 로딩 - NER용 KLUE-BERT 모델이 없으므로 임시로 일반 모델 사용
            # 실제 환경에서는 NER용으로 파인튜닝된 모델을 사용해야 함
            try:
                self.model = AutoModelForTokenClassification.from_pretrained(
                    self.model_path,
                    num_labels=len(self.label_mapping)
                )
            except Exception as e:
                logger.warning(f"Failed to load NER model: {e}. Using base KLUE model for demonstration.")
                # Fallback: 베이스 KLUE 모델로 NER 파이프라인 생성
                self._create_fallback_pipeline()
                return
            
            # GPU 사용 가능하면 모델을 GPU로 이동
            if self.device == "cuda" and torch.cuda.is_available():
                self.model.to(self.device)
                logger.info("Model moved to GPU")
            else:
                self.device = "cpu"
                logger.info("Using CPU for inference")
            
            # NER 파이프라인 생성
            self.ner_pipeline = pipeline(
                "ner",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device == "cuda" else -1,
                aggregation_strategy="simple"
            )
            
            logger.info("KLUE-BERT NER pipeline ready")
            
        except Exception as e:
            logger.error(f"Failed to load KLUE-BERT model: {e}")
            logger.info("Falling back to mock implementation")
            self._create_fallback_pipeline()
    
    def _create_fallback_pipeline(self):
        """폴백 파이프라인 생성 (모델 로딩 실패 시)"""
        logger.info("Creating fallback NER implementation")
        self.ner_pipeline = None
        self.model = None
        self.tokenizer = None
    
    async def extract_entities(self, text: str) -> List[Entity]:
        """
        텍스트에서 엔티티 추출
        
        Args:
            text: 입력 텍스트
            
        Returns:
            추출된 엔티티 리스트
        """
        start_time = time.time()
        
        try:
            # 캐시 확인
            model_config = {
                "model_name": self.model_name,
                "confidence_threshold": 0.7,
                "device": self.device
            }
            
            cached_result = self.cache_manager.get_cached_result(text, model_config)
            if cached_result is not None:
                processing_time = (time.time() - start_time) * 1000
                logger.debug(f"Cache hit: returned {len(cached_result)} entities in {processing_time:.2f}ms")
                return cached_result
            
            # 실제 추론 수행
            if self.ner_pipeline is None:
                # 폴백: 간단한 룰 기반 NER
                entities = await self._fallback_ner(text)
            else:
                # KLUE-BERT 모델 사용
                entities = await self._klue_bert_ner(text)
            
            # 후처리 적용
            original_count = len(entities)
            entities = self.postprocessor.process_entities(entities, text)
            
            # 엔티티 링킹
            entities = self.entity_linker.link_entities(entities)
            
            processing_time = (time.time() - start_time) * 1000
            
            # 결과 캐싱
            self.cache_manager.cache_result(text, entities, processing_time, model_config)
            
            logger.debug(f"Extracted {len(entities)} entities ({original_count} raw) in {processing_time:.2f}ms")
            
            return entities
            
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return []
    
    async def _klue_bert_ner(self, text: str) -> List[Entity]:
        """KLUE-BERT 모델을 사용한 NER"""
        try:
            # 비동기 실행을 위해 별도 스레드에서 실행
            loop = asyncio.get_event_loop()
            ner_results = await loop.run_in_executor(
                None, 
                self._run_ner_pipeline, 
                text
            )
            
            entities = []
            
            for result in ner_results:
                # 엔티티 타입 매핑
                entity_type = self._map_label_to_type(result.get('entity_group', ''))
                
                # 대상 엔티티만 필터링
                if entity_type not in self.target_entities:
                    continue
                
                # Entity 객체 생성
                entity = Entity(
                    text=result.get('word', '').replace('##', ''),  # BERT 서브워드 제거
                    type=entity_type,
                    start=result.get('start', 0),
                    end=result.get('end', 0),
                    confidence=result.get('score', 0.0)
                )
                
                entities.append(entity)
            
            return entities
            
        except Exception as e:
            logger.error(f"KLUE-BERT NER failed: {e}")
            return await self._fallback_ner(text)
    
    def _run_ner_pipeline(self, text: str) -> List[Dict]:
        """NER 파이프라인 실행 (동기)"""
        return self.ner_pipeline(text)
    
    async def _fallback_ner(self, text: str) -> List[Entity]:
        """폴백 NER (규칙 기반)"""
        logger.debug("Using fallback rule-based NER")
        
        entities = []
        
        # 한국 주요 기업명 패턴
        company_patterns = [
            '삼성전자', '삼성', 'LG전자', 'LG', 'LG화학', 'SK하이닉스', 'SK', 
            '현대자동차', '현대', '네이버', '카카오', '쿠팡', '배달의민족',
            '한화그룹', '한화', '포스코홀딩스', '포스코', 'KB금융', 'KB',
            '신한금융', '신한', 'CJ그룹', 'CJ', '롯데그룹', '롯데',
            '이마트', '두산그룹', '두산', 'GS칼텍스', 'GS', 'S-Oil',
            '대한항공', '아시아나항공', '셀트리온', '하이브', 'SM엔터테인먼트', 'SM',
            '토스', '우아한형제들', '당근마켓', '넷플릭스', '디즈니플러스'
        ]
        
        # 인명 패턴 (3글자 한국 이름)
        import re
        person_pattern = r'[가-힣]{2,3}(?=\s*(?:회장|대표|사장|부회장|부사장|이사|임원))'
        
        # 회사명 찾기
        for company in company_patterns:
            start_idx = text.find(company)
            if start_idx != -1:
                entities.append(Entity(
                    text=company,
                    type='COMPANY',
                    start=start_idx,
                    end=start_idx + len(company),
                    confidence=0.9
                ))
        
        # 인명 찾기
        person_matches = re.finditer(person_pattern, text)
        for match in person_matches:
            entities.append(Entity(
                text=match.group(),
                type='PERSON',
                start=match.start(),
                end=match.end(),
                confidence=0.8
            ))
        
        return entities
    
    def _map_label_to_type(self, label: str) -> str:
        """레이블을 엔티티 타입으로 매핑"""
        # LABEL_ 접두사 제거
        if label.startswith('LABEL_'):
            label = label[6:]
        
        return self.label_mapping.get(label, 'OTHER')
    
    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보 반환"""
        return {
            "model_name": self.model_name,
            "model_type": "klue_bert_ner",
            "supported_entity_types": list(self.target_entities),
            "language": "ko",
            "device": self.device,
            "version": "2.0.0",
            "model_loaded": self.model is not None,
            "pipeline_ready": self.ner_pipeline is not None
        }
    
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