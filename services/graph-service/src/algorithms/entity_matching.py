"""엔티티 매칭 알고리즘"""
import re
import logging
from typing import List, Dict, Tuple, Optional
from difflib import SequenceMatcher
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class MatchResult:
    """매칭 결과"""
    entity_id: str
    entity_name: str
    similarity_score: float
    match_type: str  # exact, alias, fuzzy

class EntityMatcher:
    """엔티티 매칭 클래스"""
    
    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold
        
    def find_matching_entity(self, 
                           name: str, 
                           candidates: List[Dict[str, any]]) -> Optional[MatchResult]:
        """가장 유사한 엔티티 찾기
        
        Args:
            name: 매칭할 이름
            candidates: 후보 엔티티 리스트 (id, name, aliases 포함)
            
        Returns:
            MatchResult or None
        """
        name_normalized = self._normalize_name(name)
        best_match = None
        best_score = 0.0
        
        for candidate in candidates:
            # 정확한 매칭 확인
            if self._exact_match(name_normalized, candidate['name']):
                return MatchResult(
                    entity_id=candidate['id'],
                    entity_name=candidate['name'],
                    similarity_score=1.0,
                    match_type='exact'
                )
            
            # 별칭 매칭 확인
            aliases = candidate.get('aliases', [])
            for alias in aliases:
                if self._exact_match(name_normalized, alias):
                    return MatchResult(
                        entity_id=candidate['id'],
                        entity_name=candidate['name'],
                        similarity_score=1.0,
                        match_type='alias'
                    )
            
            # 유사도 매칭
            score = self._calculate_similarity(name_normalized, candidate['name'])
            if score > best_score:
                best_score = score
                best_match = candidate
        
        # 임계값 이상이면 매칭 성공
        if best_score >= self.similarity_threshold and best_match:
            return MatchResult(
                entity_id=best_match['id'],
                entity_name=best_match['name'],
                similarity_score=best_score,
                match_type='fuzzy'
            )
        
        return None
    
    def _normalize_name(self, name: str) -> str:
        """이름 정규화"""
        # 소문자 변환
        normalized = name.lower()
        
        # 특수문자 제거 (하이픈, 언더스코어 제외)
        normalized = re.sub(r'[^\w\s\-_]', '', normalized)
        
        # 연속된 공백 제거
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        # 일반적인 접미사 제거
        suffixes = [
            'inc', 'incorporated', 'corp', 'corporation', 
            'ltd', 'limited', 'llc', 'plc', 'co', 'company',
            'group', 'holdings', 'international', 'global'
        ]
        
        words = normalized.split()
        if words and words[-1] in suffixes:
            words = words[:-1]
        normalized = ' '.join(words)
        
        return normalized
    
    def _exact_match(self, name1: str, name2: str) -> bool:
        """정확한 매칭 확인"""
        return self._normalize_name(name1) == self._normalize_name(name2)
    
    def _calculate_similarity(self, name1: str, name2: str) -> float:
        """유사도 계산 (여러 방법 조합)"""
        # 1. 기본 시퀀스 매칭
        sequence_score = SequenceMatcher(
            None, 
            self._normalize_name(name1), 
            self._normalize_name(name2)
        ).ratio()
        
        # 2. 토큰 기반 매칭
        token_score = self._token_similarity(name1, name2)
        
        # 3. 약어 매칭
        abbrev_score = self._abbreviation_similarity(name1, name2)
        
        # 가중 평균 (시퀀스 매칭에 더 높은 가중치)
        final_score = (
            sequence_score * 0.6 + 
            token_score * 0.3 + 
            abbrev_score * 0.1
        )
        
        return final_score
    
    def _token_similarity(self, name1: str, name2: str) -> float:
        """토큰 기반 유사도"""
        tokens1 = set(self._normalize_name(name1).split())
        tokens2 = set(self._normalize_name(name2).split())
        
        if not tokens1 or not tokens2:
            return 0.0
        
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        
        return len(intersection) / len(union)
    
    def _abbreviation_similarity(self, name1: str, name2: str) -> float:
        """약어 유사도 (예: IBM <-> International Business Machines)"""
        # 한 이름이 다른 이름의 약어인지 확인
        abbrev1 = self._get_abbreviation(name1)
        abbrev2 = self._get_abbreviation(name2)
        
        norm1 = self._normalize_name(name1)
        norm2 = self._normalize_name(name2)
        
        if abbrev1 == norm2 or abbrev2 == norm1:
            return 1.0
        elif abbrev1 == abbrev2:
            return 0.8
        
        return 0.0
    
    def _get_abbreviation(self, name: str) -> str:
        """이름의 약어 생성"""
        words = self._normalize_name(name).split()
        if len(words) > 1:
            return ''.join(word[0] for word in words if word)
        return name.lower()
    
    def merge_entities(self, primary_id: str, duplicate_ids: List[str]):
        """중복 엔티티 병합 쿼리 생성"""
        merge_query = """
        // 모든 중복 엔티티의 관계를 주 엔티티로 이동
        MATCH (primary {id: $primary_id})
        MATCH (duplicate) WHERE duplicate.id IN $duplicate_ids
        
        // 들어오는 관계 이동
        MATCH (duplicate)<-[r]-()
        WITH primary, duplicate, r, type(r) as rel_type, properties(r) as props
        CALL apoc.create.relationship(startNode(r), rel_type, props, primary) YIELD rel
        DELETE r
        
        // 나가는 관계 이동
        MATCH (duplicate)-[r]->()
        WITH primary, duplicate, r, type(r) as rel_type, properties(r) as props
        CALL apoc.create.relationship(primary, rel_type, props, endNode(r)) YIELD rel
        DELETE r
        
        // 중복 노드의 속성을 주 노드에 병합 (별칭 추가)
        WITH primary, duplicate
        SET primary.aliases = COALESCE(primary.aliases, []) + duplicate.name
        
        // 중복 노드 삭제
        DELETE duplicate
        """
        
        return merge_query, {
            'primary_id': primary_id,
            'duplicate_ids': duplicate_ids
        }

# 싱글톤 인스턴스
matcher = EntityMatcher()