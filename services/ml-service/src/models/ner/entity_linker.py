"""
엔티티 연결 및 지식 베이스 매핑 모듈
Entity Linking and Knowledge Base Mapping Module
"""
import logging
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
from ...kafka.schemas import Entity
from .company_matcher import KoreanCompanyMatcher

logger = logging.getLogger(__name__)


@dataclass
class EntityMapping:
    """엔티티 매핑 정보"""
    canonical_name: str  # 정규화된 이름
    entity_type: str     # 엔티티 타입
    aliases: List[str]   # 별칭 리스트
    industry: Optional[str] = None  # 산업 분류
    stock_code: Optional[str] = None  # 주식 코드
    description: Optional[str] = None  # 설명


class KoreanEntityLinker:
    """한국어 엔티티 연결기"""
    
    def __init__(self):
        """엔티티 연결기 초기화"""
        
        # 한국 주요 기업 지식베이스
        self.company_kb = {
            "삼성전자": EntityMapping(
                canonical_name="삼성전자",
                entity_type="COMPANY",
                aliases=["삼성전", "삼성", "Samsung Electronics", "Samsung"],
                industry="전자/반도체",
                stock_code="005930",
                description="대한민국 최대 전자기업"
            ),
            "SK하이닉스": EntityMapping(
                canonical_name="SK하이닉스",
                entity_type="COMPANY", 
                aliases=["SK하이닉스", "하이닉스", "Hynix"],
                industry="반도체",
                stock_code="000660",
                description="메모리 반도체 전문기업"
            ),
            "현대자동차": EntityMapping(
                canonical_name="현대자동차",
                entity_type="COMPANY",
                aliases=["현대차", "현대", "Hyundai Motor", "Hyundai"],
                industry="자동차",
                stock_code="005380",
                description="대한민국 대표 자동차 제조사"
            ),
            "LG전자": EntityMapping(
                canonical_name="LG전자",
                entity_type="COMPANY",
                aliases=["LG", "LG Electronics"],
                industry="전자/가전",
                stock_code="066570",
                description="종합 전자기업"
            ),
            "NAVER": EntityMapping(
                canonical_name="NAVER",
                entity_type="COMPANY",
                aliases=["네이버", "NAVER"],
                industry="IT/인터넷",
                stock_code="035420",
                description="대한민국 대표 인터넷 기업"
            ),
            "Kakao": EntityMapping(
                canonical_name="Kakao",
                entity_type="COMPANY",
                aliases=["카카오", "Kakao"],
                industry="IT/인터넷",
                stock_code="035720",
                description="모바일 플랫폼 기업"
            ),
            "POSCO": EntityMapping(
                canonical_name="POSCO",
                entity_type="COMPANY",
                aliases=["포스코", "POSCO"],
                industry="철강",
                stock_code="005490",
                description="종합 철강기업"
            )
        }
        
        # 주요 인물 지식베이스
        self.person_kb = {
            "이재용": EntityMapping(
                canonical_name="이재용",
                entity_type="PERSON",
                aliases=["이재용", "Jay Y. Lee"],
                description="삼성그룹 회장"
            ),
            "정의선": EntityMapping(
                canonical_name="정의선",
                entity_type="PERSON",
                aliases=["정의선"],
                description="현대자동차그룹 회장"
            ),
            "최태원": EntityMapping(
                canonical_name="최태원",
                entity_type="PERSON",
                aliases=["최태원"],
                description="SK그룹 회장"
            )
        }
        
        # 빠른 검색을 위한 역방향 인덱스
        self._build_reverse_index()
        
        # 고급 기업명 매칭기 초기화
        self.company_matcher = KoreanCompanyMatcher()
        
        logger.info("Korean Entity Linker initialized with knowledge base and company matcher")
    
    def _build_reverse_index(self):
        """별칭에서 정규명으로의 역방향 인덱스 구축"""
        self.alias_to_canonical = {}
        
        # 기업 별칭 인덱싱
        for canonical, mapping in self.company_kb.items():
            self.alias_to_canonical[canonical.lower()] = canonical
            for alias in mapping.aliases:
                self.alias_to_canonical[alias.lower()] = canonical
        
        # 인물 별칭 인덱싱 
        for canonical, mapping in self.person_kb.items():
            self.alias_to_canonical[canonical.lower()] = canonical
            for alias in mapping.aliases:
                self.alias_to_canonical[alias.lower()] = canonical
    
    def link_entities(self, entities: List[Entity]) -> List[Entity]:
        """
        엔티티를 지식베이스에 연결하여 정규화
        
        Args:
            entities: 원본 엔티티 리스트
            
        Returns:
            연결된 엔티티 리스트
        """
        linked_entities = []
        
        for entity in entities:
            linked_entity = self._link_single_entity(entity)
            if linked_entity:
                linked_entities.append(linked_entity)
        
        # 연결 후 중복 제거
        deduplicated = self._remove_duplicates_after_linking(linked_entities)
        
        logger.debug(f"Linked {len(entities)} entities -> {len(deduplicated)} after deduplication")
        
        return deduplicated
    
    def _link_single_entity(self, entity: Entity) -> Optional[Entity]:
        """단일 엔티티를 지식베이스에 연결"""
        
        # 정확한 매칭 시도
        canonical_name = self._find_canonical_name(entity.text)
        
        if canonical_name:
            # 지식베이스에서 매핑 정보 가져오기
            mapping = self._get_entity_mapping(canonical_name)
            
            if mapping:
                # 정규화된 엔티티 생성
                return Entity(
                    text=mapping.canonical_name,
                    type=mapping.entity_type,
                    start=entity.start,
                    end=entity.end,
                    confidence=min(entity.confidence + 0.1, 1.0)  # 연결 보너스
                )
        
        # 기업명인 경우 고급 매칭 시도
        if entity.type == "COMPANY":
            company_matches = self._advanced_company_matching(entity.text)
            if company_matches:
                best_match = company_matches[0]  # 최고 점수 매칭
                mapping = self._get_entity_mapping(best_match.canonical_name)
                
                if mapping:
                    return Entity(
                        text=mapping.canonical_name,
                        type=mapping.entity_type,
                        start=entity.start,
                        end=entity.end,
                        confidence=min(entity.confidence * best_match.confidence, 1.0)
                    )
        
        # 매칭되지 않은 경우 부분 매칭 시도
        partial_match = self._partial_matching(entity.text)
        if partial_match:
            mapping = self._get_entity_mapping(partial_match)
            if mapping:
                return Entity(
                    text=mapping.canonical_name,
                    type=mapping.entity_type,
                    start=entity.start,
                    end=entity.end,
                    confidence=max(entity.confidence - 0.1, 0.1)  # 부분매칭 페널티
                )
        
        # 연결되지 않은 경우 원본 반환
        return entity
    
    def _find_canonical_name(self, text: str) -> Optional[str]:
        """텍스트에 대한 정규명 찾기"""
        text_lower = text.lower()
        return self.alias_to_canonical.get(text_lower)
    
    def _partial_matching(self, text: str) -> Optional[str]:
        """부분 문자열 매칭"""
        text_lower = text.lower()
        
        # 텍스트가 별칭에 포함되는지 확인
        for alias, canonical in self.alias_to_canonical.items():
            if text_lower in alias or alias in text_lower:
                # 유사도가 충분히 높은 경우만 매칭
                similarity = len(text_lower) / max(len(alias), len(text_lower))
                if similarity > 0.6:  # 60% 이상 유사
                    return canonical
        
        return None
    
    def _advanced_company_matching(self, text: str) -> List:
        """고급 기업명 매칭"""
        # 지식베이스의 기업명들을 후보로 사용
        candidates = list(self.company_kb.keys())
        
        # 모든 별칭도 후보에 포함
        for mapping in self.company_kb.values():
            candidates.extend(mapping.aliases)
        
        # 중복 제거
        candidates = list(set(candidates))
        
        # 고급 매칭 수행
        matches = self.company_matcher.match_company(text, candidates)
        
        # 신뢰도 0.6 이상만 반환
        return [match for match in matches if match.confidence >= 0.6]
    
    def _get_entity_mapping(self, canonical_name: str) -> Optional[EntityMapping]:
        """정규명으로 엔티티 매핑 정보 가져오기"""
        if canonical_name in self.company_kb:
            return self.company_kb[canonical_name]
        elif canonical_name in self.person_kb:
            return self.person_kb[canonical_name]
        return None
    
    def _remove_duplicates_after_linking(self, entities: List[Entity]) -> List[Entity]:
        """연결 후 중복 제거"""
        seen = {}
        unique_entities = []
        
        for entity in entities:
            key = (entity.text.lower(), entity.type)
            
            if key not in seen:
                seen[key] = entity
                unique_entities.append(entity)
            else:
                # 더 높은 신뢰도 유지
                if entity.confidence > seen[key].confidence:
                    # 기존 엔티티를 새 엔티티로 교체
                    idx = unique_entities.index(seen[key])
                    unique_entities[idx] = entity
                    seen[key] = entity
        
        return unique_entities
    
    def add_company(self, mapping: EntityMapping):
        """새로운 기업을 지식베이스에 추가"""
        self.company_kb[mapping.canonical_name] = mapping
        self._build_reverse_index()
        logger.info(f"Added company: {mapping.canonical_name}")
    
    def add_person(self, mapping: EntityMapping):
        """새로운 인물을 지식베이스에 추가"""
        self.person_kb[mapping.canonical_name] = mapping
        self._build_reverse_index()
        logger.info(f"Added person: {mapping.canonical_name}")
    
    def get_entity_info(self, canonical_name: str) -> Optional[EntityMapping]:
        """정규명으로 엔티티 상세 정보 조회"""
        return self._get_entity_mapping(canonical_name)
    
    def search_entities(self, query: str, entity_type: Optional[str] = None) -> List[EntityMapping]:
        """엔티티 검색"""
        results = []
        query_lower = query.lower()
        
        # 검색 대상 지식베이스 결정
        knowledge_bases = []
        if not entity_type or entity_type == "COMPANY":
            knowledge_bases.append(self.company_kb)
        if not entity_type or entity_type == "PERSON":
            knowledge_bases.append(self.person_kb)
        
        for kb in knowledge_bases:
            for canonical, mapping in kb.items():
                # 정규명 또는 별칭에서 검색
                if (query_lower in canonical.lower() or
                    any(query_lower in alias.lower() for alias in mapping.aliases)):
                    results.append(mapping)
        
        return results
    
    def extract_companies_from_text(self, text: str) -> List[EntityMapping]:
        """텍스트에서 모든 기업명 추출 (고급 매칭 사용)"""
        # 지식베이스의 기업명들을 후보로 사용
        candidates = list(self.company_kb.keys())
        for mapping in self.company_kb.values():
            candidates.extend(mapping.aliases)
        candidates = list(set(candidates))
        
        # 고급 매칭으로 기업명 추출
        matches = self.company_matcher.extract_all_companies(text, candidates)
        
        # 매핑 정보와 함께 반환
        results = []
        for match in matches:
            mapping = self._get_entity_mapping(match.canonical_name)
            if mapping:
                results.append(mapping)
        
        return results
    
    def validate_entity_name(self, name: str, entity_type: str) -> bool:
        """엔티티 이름 유효성 검사"""
        if entity_type == "COMPANY":
            return self.company_matcher.validate_company_name(name)
        
        # 인명 유효성 검사 (기본적인 규칙)
        if entity_type == "PERSON":
            return (len(name) >= 2 and len(name) <= 10 and 
                    not name.isdigit() and 
                    any(ord('가') <= ord(c) <= ord('힣') for c in name))
        
        return True
    
    def get_statistics(self) -> Dict[str, int]:
        """지식베이스 통계"""
        return {
            "total_companies": len(self.company_kb),
            "total_persons": len(self.person_kb),
            "total_aliases": len(self.alias_to_canonical),
        }
    
    def export_knowledge_base(self) -> Dict[str, Dict]:
        """지식베이스 내보내기 (백업/공유용)"""
        return {
            "companies": {k: {
                "canonical_name": v.canonical_name,
                "entity_type": v.entity_type,
                "aliases": v.aliases,
                "industry": v.industry,
                "stock_code": v.stock_code,
                "description": v.description
            } for k, v in self.company_kb.items()},
            "persons": {k: {
                "canonical_name": v.canonical_name,
                "entity_type": v.entity_type,
                "aliases": v.aliases,
                "description": v.description
            } for k, v in self.person_kb.items()}
        }