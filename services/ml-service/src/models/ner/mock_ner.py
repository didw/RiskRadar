"""
Mock NER model for development and testing
"""
import re
import time
import logging
from typing import List, Dict, Any
from ...kafka.schemas import Entity

logger = logging.getLogger(__name__)


class MockNERModel:
    """Mock implementation of KLUE-BERT NER model"""
    
    def __init__(self):
        # Mock entity patterns for Korean text
        self.patterns = {
            'COMPANY': [
                r'삼성전자', r'현대자동차', r'LG전자', r'SK하이닉스', r'네이버', r'카카오',
                r'포스코', r'한국전력', r'신한은행', r'KB금융', r'우리은행', r'하나은행',
                r'LG에너지솔루션', r'카카오뱅크', r'쿠팡', r'배달의민족', r'토스',
                r'([가-힣]+)(?:그룹|전자|자동차|은행|증권|생명|화학|제약|건설|통신)',
                r'([가-힣]+)(?:주식회사|㈜|유한회사)',
            ],
            'PERSON': [
                r'이재용', r'정의선', r'김범석', r'이해진', r'김택진', r'방민진',
                r'([가-힣]{2,4})\s*(?:회장|사장|대표|임원|부사장|상무|이사)',
                r'([가-힣]{2,4})\s*(?:씨|님)',
            ],
            'EVENT': [
                r'(?:인수합병|M&A)', r'상장', r'IPO', r'기업공개', r'투자유치',
                r'파업', r'노조', r'스트라이크', r'분할', r'합병', r'신제품출시',
                r'화재', r'사고', r'장애', r'시스템다운', r'해킹', r'보안사고',
                r'법정관리', r'워크아웃', r'구조조정', r'정리해고', r'감원',
                r'특허소송', r'소송', r'판결', r'배상', r'벌금', r'과징금',
                r'실적발표', r'어닝서프라이즈', r'어닝쇼크', r'감익', r'증익',
            ]
        }
        
        # Compile regex patterns for better performance
        self.compiled_patterns = {}
        for entity_type, patterns in self.patterns.items():
            self.compiled_patterns[entity_type] = [
                re.compile(pattern) for pattern in patterns
            ]
            
        logger.info("MockNERModel initialized with pattern matching")
        
    def extract_entities(self, text: str) -> List[Entity]:
        """
        Extract entities using pattern matching
        
        Args:
            text: Input Korean text
            
        Returns:
            List of Entity objects
        """
        start_time = time.time()
        entities = []
        
        try:
            for entity_type, patterns in self.compiled_patterns.items():
                for pattern in patterns:
                    for match in pattern.finditer(text):
                        # Extract the matched text
                        matched_text = match.group(0)
                        
                        # If there's a capture group, use that instead
                        if match.groups():
                            matched_text = match.group(1)
                            
                        # Skip if too short or not Korean
                        if len(matched_text) < 2:
                            continue
                            
                        # Calculate confidence based on pattern type
                        confidence = self._calculate_confidence(
                            matched_text, entity_type, text
                        )
                        
                        if confidence > 0.5:  # Threshold for inclusion
                            entity = Entity(
                                text=matched_text,
                                type=entity_type,
                                start=match.start(),
                                end=match.end(),
                                confidence=confidence
                            )
                            
                            # Avoid duplicates
                            if not self._is_duplicate(entity, entities):
                                entities.append(entity)
                                
            # Sort by position in text
            entities.sort(key=lambda x: x.start)
            
            processing_time = (time.time() - start_time) * 1000
            logger.debug(f"Extracted {len(entities)} entities in {processing_time:.2f}ms")
            
            return entities
            
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return []
            
    def _calculate_confidence(self, text: str, entity_type: str, context: str) -> float:
        """Calculate confidence score for entity"""
        base_confidence = 0.7
        
        # Boost confidence for well-known entities
        if entity_type == 'COMPANY':
            well_known = ['삼성전자', '현대자동차', '네이버', '카카오', 'LG전자']
            if text in well_known:
                base_confidence = 0.95
        elif entity_type == 'PERSON':
            well_known = ['이재용', '정의선', '김범석', '이해진']
            if text in well_known:
                base_confidence = 0.95
                
        # Boost confidence if entity appears multiple times
        occurrences = context.count(text)
        if occurrences > 1:
            base_confidence = min(0.98, base_confidence + 0.1 * (occurrences - 1))
            
        # Lower confidence for very short entities
        if len(text) < 3:
            base_confidence *= 0.8
            
        return base_confidence
        
    def _is_duplicate(self, new_entity: Entity, existing_entities: List[Entity]) -> bool:
        """Check if entity is duplicate"""
        for existing in existing_entities:
            # Same text and type
            if (new_entity.text == existing.text and 
                new_entity.type == existing.type):
                return True
                
            # Overlapping positions
            if (new_entity.start < existing.end and 
                new_entity.end > existing.start):
                return True
                
        return False
        
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "model_name": "MockNERModel",
            "model_type": "pattern_based",
            "supported_entity_types": list(self.patterns.keys()),
            "language": "ko",
            "version": "1.0.0"
        }