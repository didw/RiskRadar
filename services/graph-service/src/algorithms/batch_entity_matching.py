"""배치 엔티티 매칭 - N+1 문제 해결"""
import logging
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher
from concurrent.futures import ThreadPoolExecutor
import time

from src.kafka.entity_cache import entity_cache
from src.algorithms.entity_matching import matcher

logger = logging.getLogger(__name__)

class BatchEntityMatcher:
    """배치 엔티티 매칭 시스템"""
    
    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold
    
    def match_entities_batch(self, entities: List[Dict]) -> Dict[str, Optional[str]]:
        """엔티티 배치 매칭 - 한 번의 캐시 조회로 모든 엔티티 처리"""
        start_time = time.time()
        results = {}
        
        # 엔티티 타입별로 그룹화
        companies_to_match = []
        persons_to_match = []
        
        for entity in entities:
            if entity['type'] == 'COMPANY':
                companies_to_match.append(entity)
            elif entity['type'] == 'PERSON':
                persons_to_match.append(entity)
        
        # 캐시에서 한 번에 모든 후보 조회
        company_candidates = entity_cache.get_companies() if companies_to_match else []
        person_candidates = entity_cache.get_persons() if persons_to_match else []
        
        logger.info(f"Batch matching: {len(companies_to_match)} companies, {len(persons_to_match)} persons")
        logger.info(f"Cache candidates: {len(company_candidates)} companies, {len(person_candidates)} persons")
        
        # 기업 엔티티 배치 매칭
        for entity in companies_to_match:
            entity_key = f"{entity['type']}:{entity['text']}"
            matched_id = self._match_single_entity(entity['text'], company_candidates)
            results[entity_key] = matched_id
        
        # 인물 엔티티 배치 매칭
        for entity in persons_to_match:
            entity_key = f"{entity['type']}:{entity['text']}"
            matched_id = self._match_single_entity(entity['text'], person_candidates)
            results[entity_key] = matched_id
        
        elapsed = time.time() - start_time
        logger.info(f"Batch entity matching completed in {elapsed:.3f}s")
        
        return results
    
    def _match_single_entity(self, entity_text: str, candidates: List[Dict]) -> Optional[str]:
        """단일 엔티티 매칭"""
        if not candidates:
            return None
        
        best_match = None
        best_score = 0.0
        
        # 빠른 정확 매칭 먼저 시도
        entity_lower = entity_text.lower()
        for candidate in candidates:
            # 정확한 이름 매칭
            if candidate['name'].lower() == entity_lower:
                return candidate['id']
            
            # 별칭 매칭
            if candidate.get('aliases'):
                for alias in candidate['aliases']:
                    if alias.lower() == entity_lower:
                        return candidate['id']
        
        # 유사도 매칭
        for candidate in candidates:
            # 메인 이름 유사도
            score = self._calculate_similarity(entity_text, candidate['name'])
            if score > best_score and score >= self.similarity_threshold:
                best_score = score
                best_match = candidate['id']
            
            # 별칭 유사도
            if candidate.get('aliases'):
                for alias in candidate['aliases']:
                    score = self._calculate_similarity(entity_text, alias)
                    if score > best_score and score >= self.similarity_threshold:
                        best_score = score
                        best_match = candidate['id']
        
        if best_match:
            logger.debug(f"Fuzzy matched '{entity_text}' with score {best_score:.3f}")
        
        return best_match
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """텍스트 유사도 계산"""
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

# 전역 배치 매처 인스턴스
batch_matcher = BatchEntityMatcher()