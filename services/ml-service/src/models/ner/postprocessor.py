"""
한국어 NER 후처리 모듈
Korean NER Post-processing Module
"""
import re
import logging
from typing import List, Dict, Set, Tuple
from ...kafka.schemas import Entity

logger = logging.getLogger(__name__)


class KoreanNERPostProcessor:
    """한국어 NER 결과 후처리기"""
    
    def __init__(self, confidence_threshold: float = 0.5):
        """
        Initialize Korean NER post-processor
        
        Args:
            confidence_threshold: Minimum confidence for entity acceptance
        """
        self.confidence_threshold = confidence_threshold
        
        # 한국어 기업명 접미사 패턴
        self.company_suffixes = {
            '(주)', '주식회사', '㈜', '(유)', '유한회사', '(재)', '재단법인',
            '(사)', '사단법인', '(합)', '합자회사', '합명회사', '(영)', '영농조합법인',
            '코퍼레이션', '코퍼레이숀', '코퍼레이션', 'Corp', 'Corporation', 'Inc',
            'Co.', 'Ltd', '그룹', 'Group', '홀딩스', 'Holdings', '테크', 'Tech',
            '시스템', 'System', '솔루션', 'Solutions', '서비스', 'Service'
        }
        
        # 한국어 인명 패턴 (성+이름)
        self.korean_name_patterns = [
            r'[가-힣]{2,4}(?:\s+[가-힣]{1,3})?(?:\s+(?:회장|사장|대표|이사|부장|과장|팀장|실장|본부장))?',
            r'[가-힣]{2,4}(?:\s+(?:CEO|CFO|CTO|CMO|COO))?'
        ]
        
        # 정규화할 기업명 매핑
        self.company_aliases = {
            '삼성전': '삼성전자',
            '삼성': '삼성전자',
            '현대차': '현대자동차',
            '현대': '현대자동차',
            'SK하이닉스': 'SK하이닉스',
            'LG전자': 'LG전자',
            'LG': 'LG전자',
            '네이버': 'NAVER',
            '카카오': 'Kakao',
            '포스코': 'POSCO'
        }
        
        # 무시할 일반 단어들 (over-detection 방지)
        self.ignore_words = {
            '한국', '서울', '부산', '대구', '인천', '광주', '대전', '울산',
            '경기', '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주',
            '오늘', '어제', '내일', '지난', '다음', '이번', '올해', '작년', '내년',
            '시장', '업계', '기업', '회사', '산업', '분야', '부문'
        }
        
        logger.info("Korean NER Post-processor initialized")
    
    def process_entities(self, entities: List[Entity], text: str) -> List[Entity]:
        """
        종합적인 엔티티 후처리
        
        Args:
            entities: 원본 엔티티 리스트
            text: 원본 텍스트
            
        Returns:
            후처리된 엔티티 리스트
        """
        if not entities:
            return entities
        
        # 1. 신뢰도 필터링
        entities = self._filter_by_confidence(entities)
        
        # 2. 텍스트 정규화
        entities = self._normalize_entity_text(entities)
        
        # 3. 위치 기반 정렬
        entities = self._sort_by_position(entities)
        
        # 4. 인접 엔티티 병합
        entities = self._merge_adjacent_entities(entities, text)
        
        # 5. 한국어 특화 정규화
        entities = self._apply_korean_normalization(entities)
        
        # 6. 중복 제거
        entities = self._remove_duplicates(entities)
        
        # 7. 무의미한 엔티티 필터링
        entities = self._filter_irrelevant_entities(entities)
        
        logger.debug(f"Post-processing: {len(entities)} entities after processing")
        return entities
    
    def _filter_by_confidence(self, entities: List[Entity]) -> List[Entity]:
        """신뢰도 기반 필터링"""
        return [
            entity for entity in entities 
            if entity.confidence >= self.confidence_threshold
        ]
    
    def _normalize_entity_text(self, entities: List[Entity]) -> List[Entity]:
        """엔티티 텍스트 정규화"""
        normalized_entities = []
        
        for entity in entities:
            # 기본 텍스트 정리
            text = entity.text.strip()
            
            # 특수 토큰 제거
            text = re.sub(r'##', '', text)
            
            # 불필요한 공백 제거
            text = re.sub(r'\s+', ' ', text).strip()
            
            # 불필요한 구두점 제거
            text = re.sub(r'^[^\w가-힣]+|[^\w가-힣]+$', '', text)
            
            if text:  # 빈 문자열이 아닌 경우만 유지
                entity.text = text
                normalized_entities.append(entity)
        
        return normalized_entities
    
    def _sort_by_position(self, entities: List[Entity]) -> List[Entity]:
        """위치 기반 정렬"""
        return sorted(entities, key=lambda x: x.start)
    
    def _merge_adjacent_entities(self, entities: List[Entity], text: str) -> List[Entity]:
        """인접한 동일 타입 엔티티 병합"""
        if len(entities) <= 1:
            return entities
        
        merged_entities = []
        current_entity = entities[0]
        
        for next_entity in entities[1:]:
            # 같은 타입이고 거리가 가까운 경우 병합
            if (current_entity.type == next_entity.type and
                next_entity.start - current_entity.end <= 3):  # 3글자 이내 간격
                
                # 원본 텍스트에서 병합된 부분 추출
                merged_text = text[current_entity.start:next_entity.end].strip()
                
                current_entity = Entity(
                    text=merged_text,
                    type=current_entity.type,
                    start=current_entity.start,
                    end=next_entity.end,
                    confidence=max(current_entity.confidence, next_entity.confidence)
                )
            else:
                merged_entities.append(current_entity)
                current_entity = next_entity
        
        merged_entities.append(current_entity)
        return merged_entities
    
    def _apply_korean_normalization(self, entities: List[Entity]) -> List[Entity]:
        """한국어 특화 정규화"""
        normalized_entities = []
        
        for entity in entities:
            if entity.type == 'COMPANY':
                entity = self._normalize_company_name(entity)
            elif entity.type == 'PERSON':
                entity = self._normalize_person_name(entity)
            
            if entity:  # None이 아닌 경우만 추가
                normalized_entities.append(entity)
        
        return normalized_entities
    
    def _normalize_company_name(self, entity: Entity) -> Entity:
        """기업명 정규화"""
        text = entity.text
        
        # 알려진 별칭을 정규명으로 변환
        for alias, canonical in self.company_aliases.items():
            if alias in text:
                text = text.replace(alias, canonical)
                break
        
        # 기업명 접미사 추가/정규화
        if entity.type == 'COMPANY':
            text = self._add_company_suffix(text)
        
        entity.text = text
        return entity
    
    def _add_company_suffix(self, company_name: str) -> str:
        """기업명에 적절한 접미사 추가"""
        # 이미 접미사가 있는지 확인
        for suffix in self.company_suffixes:
            if company_name.endswith(suffix):
                return company_name
        
        # 특정 기업의 경우 고유 접미사 추가
        if company_name in ['삼성전자', 'LG전자', 'SK하이닉스']:
            return company_name  # 이미 완전한 형태
        elif '전자' in company_name or '하이닉스' in company_name:
            return company_name
        elif len(company_name) >= 2:
            return f"{company_name}"  # 접미사 없이 유지
        
        return company_name
    
    def _normalize_person_name(self, entity: Entity) -> Entity:
        """인명 정규화"""
        text = entity.text
        
        # 직급 정보 제거 (선택적)
        titles = ['회장', '사장', '대표', '이사', '부장', '과장', '팀장', '실장', '본부장',
                 'CEO', 'CFO', 'CTO', 'CMO', 'COO']
        
        for title in titles:
            if text.endswith(title):
                text = text[:-len(title)].strip()
                break
        
        entity.text = text
        return entity
    
    def _remove_duplicates(self, entities: List[Entity]) -> List[Entity]:
        """중복 엔티티 제거"""
        seen = set()
        unique_entities = []
        
        for entity in entities:
            # 텍스트와 타입 조합으로 중복 판단
            key = (entity.text.lower(), entity.type)
            
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)
            else:
                # 같은 엔티티가 여러 번 검출된 경우, 더 높은 신뢰도 유지
                for existing in unique_entities:
                    if (existing.text.lower() == entity.text.lower() and 
                        existing.type == entity.type):
                        if entity.confidence > existing.confidence:
                            existing.confidence = entity.confidence
                        break
        
        return unique_entities
    
    def _filter_irrelevant_entities(self, entities: List[Entity]) -> List[Entity]:
        """무의미한 엔티티 필터링"""
        filtered_entities = []
        
        for entity in entities:
            # 너무 짧은 엔티티 제거
            if len(entity.text) < 2:
                continue
            
            # 무시할 단어 제거
            if entity.text in self.ignore_words:
                continue
            
            # 숫자만으로 구성된 엔티티 제거 (날짜/시간 제외)
            if entity.text.isdigit():
                continue
            
            # 한 글자 영문자 제거
            if len(entity.text) == 1 and entity.text.isalpha():
                continue
            
            filtered_entities.append(entity)
        
        return filtered_entities
    
    def get_statistics(self, original_entities: List[Entity], 
                      processed_entities: List[Entity]) -> Dict[str, int]:
        """후처리 통계 반환"""
        return {
            "original_count": len(original_entities),
            "processed_count": len(processed_entities),
            "removed_count": len(original_entities) - len(processed_entities),
            "company_count": len([e for e in processed_entities if e.type == 'COMPANY']),
            "person_count": len([e for e in processed_entities if e.type == 'PERSON']),
            "event_count": len([e for e in processed_entities if e.type == 'EVENT'])
        }