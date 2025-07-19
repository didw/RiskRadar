"""
엔티티 분리기 - 연결된 엔티티를 개별 엔티티로 분리
Entity Splitter - Split conjunctive entities into separate entities
"""
import re
import logging
from typing import List, Tuple, Optional
from ...kafka.schemas import Entity

logger = logging.getLogger(__name__)


class KoreanEntitySplitter:
    """한국어 엔티티 분리기"""
    
    def __init__(self):
        # 연결사 패턴
        self.conjunctions = [
            '와', '과', '및', '그리고', '또한', '뿐만 아니라',
            '이랑', '하고', '에', '의', '가'
        ]
        
        # 회사명 접미사
        self.company_suffixes = [
            '그룹', '홀딩스', '전자', '화학', '물산', '건설', '중공업',
            '자동차', '모빌리티', '엔터테인먼트', '금융', '은행', '증권',
            '칼텍스', 'Oil', 'oil', '항공', '마켓', '플러스', '마트'
        ]
        
        # 알려진 회사명 패턴
        self.known_companies = [
            '삼성', 'LG', 'SK', '현대', '롯데', 'CJ', 'GS', '한화', '두산',
            '포스코', 'KB', '신한', '우리', '하나', '국민', 'IBK', 'NH',
            '대한항공', '아시아나항공', '네이버', 'NAVER', '카카오', 'Kakao',
            '쿠팡', '배민', '토스', '당근', '이마트', '홈플러스', '롯데마트',
            '넷플릭스', '디즈니', '아마존', '구글', '애플', '마이크로소프트'
        ]
        
        # 특수 케이스 (분리하면 안 되는 경우)
        self.no_split_patterns = [
            r'배달의민족',  # 배달의민족은 하나의 서비스명
        ]
        
        # 특수 분리 패턴
        self.special_split_patterns = [
            (r'S-Oil', 'S-Oil'),  # S-Oil은 별도 회사
        ]
        
        logger.info("Korean Entity Splitter initialized")
    
    def should_split(self, text: str) -> bool:
        """엔티티를 분리해야 하는지 판단"""
        # 특수 케이스 체크
        for pattern in self.no_split_patterns:
            if re.search(pattern, text):
                return False
        
        # 연결사 포함 여부 체크
        for conj in self.conjunctions:
            if conj in text:
                return True
        
        return False
    
    def split_entity(self, entity: Entity) -> List[Entity]:
        """단일 엔티티를 여러 개로 분리"""
        if not self.should_split(entity.text):
            return [entity]
        
        # 연결사별로 시도
        for conj in self.conjunctions:
            if conj in entity.text:
                parts = self._split_by_conjunction(entity.text, conj)
                if len(parts) > 1:
                    # 성공적으로 분리된 경우
                    return self._create_split_entities(entity, parts, conj)
        
        # 분리 실패 시 원본 반환
        return [entity]
    
    def _split_by_conjunction(self, text: str, conj: str) -> List[str]:
        """연결사로 텍스트 분리"""
        # 특별한 경우 처리
        if conj in ['가', '이']:
            # "이마트가 쿠팡" -> ["이마트", "쿠팡"]
            # "대한항공이 아시아나항공" -> ["대한항공", "아시아나항공"]
            parts = []
            split_point = text.find(conj)
            if split_point > 0:
                first_part = text[:split_point]
                second_part = text[split_point + len(conj):].strip()
                
                # 두 부분 모두 회사명처럼 보이는지 확인
                if self._is_likely_company_name(first_part) and self._is_likely_company_name(second_part):
                    parts = [first_part, second_part]
                else:
                    parts = [text]  # 분리하지 않음
            else:
                parts = [text]
        else:
            parts = text.split(conj)
        
        # 각 부분 정리
        cleaned_parts = []
        for part in parts:
            part = part.strip()
            if part and self._is_likely_company_name(part):
                cleaned_parts.append(part)
        
        return cleaned_parts if len(cleaned_parts) > 1 else [text]
    
    def _is_likely_company_name(self, text: str) -> bool:
        """회사명일 가능성이 높은지 판단"""
        # 알려진 회사명 체크
        for company in self.known_companies:
            if company in text:
                return True
        
        # 회사명 접미사 체크
        for suffix in self.company_suffixes:
            if text.endswith(suffix):
                return True
        
        # 영어 대문자로 시작하는 경우
        if text and text[0].isupper():
            return True
        
        # 한글 2글자 이상
        korean_chars = re.findall(r'[가-힣]+', text)
        if korean_chars and len(''.join(korean_chars)) >= 2:
            return True
        
        return False
    
    def _create_split_entities(self, original: Entity, parts: List[str], conj: str) -> List[Entity]:
        """분리된 부분들로부터 새로운 엔티티 생성"""
        entities = []
        
        # 원본 텍스트에서 각 부분의 위치 찾기
        current_pos = original.start
        original_text = original.text
        
        for i, part in enumerate(parts):
            # 텍스트에서 해당 부분의 위치 찾기
            part_start = original_text.find(part, current_pos - original.start)
            if part_start == -1:
                continue
            
            # 절대 위치로 변환
            abs_start = original.start + part_start
            abs_end = abs_start + len(part)
            
            # 새 엔티티 생성
            new_entity = Entity(
                text=part,
                type=original.type,
                start=abs_start,
                end=abs_end,
                confidence=original.confidence * 0.9  # 분리로 인한 신뢰도 약간 감소
            )
            entities.append(new_entity)
            
            # 다음 검색을 위한 위치 업데이트
            current_pos = abs_end
        
        return entities if entities else [original]
    
    def split_entities(self, entities: List[Entity]) -> List[Entity]:
        """엔티티 리스트 전체 처리"""
        result = []
        
        for entity in entities:
            if entity.type == 'COMPANY':  # 주로 회사명에서 발생
                split_entities = self.split_entity(entity)
                result.extend(split_entities)
            else:
                result.append(entity)
        
        logger.debug(f"Split {len(entities)} entities into {len(result)} entities")
        return result