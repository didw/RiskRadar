"""
Enhanced Rule-based NER Model
강화된 규칙 기반 한국어 개체명 인식 모델
"""
import time
import logging
import re
from typing import List, Dict, Any, Optional, Set, Tuple
import json

from ...kafka.schemas import Entity
from .postprocessor import KoreanNERPostProcessor
from .entity_linker import KoreanEntityLinker
from .cache_manager import get_cache_manager

logger = logging.getLogger(__name__)


class EnhancedRuleBasedNER:
    """강화된 규칙 기반 NER 모델"""
    
    def __init__(self):
        """모델 초기화"""
        
        # 회사명 데이터베이스 (확장된 버전)
        # 순서 중요: 더 긴 이름을 먼저 매칭 (SK하이닉스 vs SK)
        self.company_database = {
            # 대기업 그룹 (정확한 매칭 우선)
            'SK하이닉스': {'aliases': [], 'type': 'COMPANY', 'industry': '반도체', 'priority': 1},
            'SK이노베이션': {'aliases': [], 'type': 'COMPANY', 'industry': '정유', 'priority': 1},
            'SK텔레콤': {'aliases': ['SKT'], 'type': 'COMPANY', 'industry': '통신', 'priority': 1},
            'SK': {'aliases': [], 'type': 'COMPANY', 'industry': '그룹', 'priority': 2},  # 낮은 우선순위
            
            '삼성전자': {'aliases': [], 'type': 'COMPANY', 'industry': '전자', 'priority': 1},
            '삼성물산': {'aliases': [], 'type': 'COMPANY', 'industry': '건설', 'priority': 1},
            '삼성': {'aliases': [], 'type': 'COMPANY', 'industry': '그룹', 'priority': 2},
            
            'LG전자': {'aliases': [], 'type': 'COMPANY', 'industry': '전자', 'priority': 1},
            'LG화학': {'aliases': ['LG Chem'], 'type': 'COMPANY', 'industry': '화학', 'priority': 1},
            'LG에너지솔루션': {'aliases': [], 'type': 'COMPANY', 'industry': '배터리', 'priority': 1},
            'LG': {'aliases': [], 'type': 'COMPANY', 'industry': '그룹', 'priority': 2},
            
            '현대자동차': {'aliases': ['현대차'], 'type': 'COMPANY', 'industry': '자동차', 'priority': 1},
            '현대모비스': {'aliases': [], 'type': 'COMPANY', 'industry': '자동차부품', 'priority': 1},
            '현대': {'aliases': [], 'type': 'COMPANY', 'industry': '그룹', 'priority': 2},
            
            '기아': {'aliases': ['기아자동차'], 'type': 'COMPANY', 'industry': '자동차', 'priority': 1},
            
            # 금융 (정확한 매칭 우선)
            'KB금융': {'aliases': ['KB금융그룹'], 'type': 'COMPANY', 'industry': '금융', 'priority': 1},
            'KB국민은행': {'aliases': ['국민은행'], 'type': 'COMPANY', 'industry': '은행', 'priority': 1},
            'KB': {'aliases': [], 'type': 'COMPANY', 'industry': '금융', 'priority': 2},
            
            '신한금융': {'aliases': ['신한금융그룹'], 'type': 'COMPANY', 'industry': '금융', 'priority': 1},
            '신한은행': {'aliases': [], 'type': 'COMPANY', 'industry': '은행', 'priority': 1},
            '신한': {'aliases': [], 'type': 'COMPANY', 'industry': '금융', 'priority': 2},
            
            '우리금융': {'aliases': ['우리금융그룹'], 'type': 'COMPANY', 'industry': '금융', 'priority': 1},
            '우리': {'aliases': [], 'type': 'COMPANY', 'industry': '금융', 'priority': 2},
            '하나금융': {'aliases': ['하나금융그룹'], 'type': 'COMPANY', 'industry': '금융', 'priority': 1},
            '하나': {'aliases': [], 'type': 'COMPANY', 'industry': '금융', 'priority': 2},
            
            # IT/플랫폼 (별칭 포함)
            '네이버': {'aliases': ['NAVER'], 'type': 'COMPANY', 'industry': 'IT', 'priority': 1},
            '카카오모빌리티': {'aliases': [], 'type': 'COMPANY', 'industry': '모빌리티', 'priority': 1},
            '카카오페이': {'aliases': [], 'type': 'COMPANY', 'industry': '핀테크', 'priority': 1},
            '카카오': {'aliases': ['Kakao'], 'type': 'COMPANY', 'industry': 'IT', 'priority': 1},
            '쿠팡': {'aliases': ['Coupang'], 'type': 'COMPANY', 'industry': '이커머스', 'priority': 1},
            '배달의민족': {'aliases': ['배민'], 'type': 'COMPANY', 'industry': '배달', 'priority': 1},
            '우아한형제들': {'aliases': [], 'type': 'COMPANY', 'industry': 'IT', 'priority': 1},
            '토스': {'aliases': ['Toss'], 'type': 'COMPANY', 'industry': '핀테크', 'priority': 1},
            '당근마켓': {'aliases': ['당근'], 'type': 'COMPANY', 'industry': '플랫폼', 'priority': 1},
            
            # 기타 대기업
            '한화그룹': {'aliases': [], 'type': 'COMPANY', 'industry': '화학', 'priority': 1},
            '한화': {'aliases': [], 'type': 'COMPANY', 'industry': '화학', 'priority': 2},
            '포스코홀딩스': {'aliases': ['POSCO'], 'type': 'COMPANY', 'industry': '철강', 'priority': 1},
            '포스코': {'aliases': [], 'type': 'COMPANY', 'industry': '철강', 'priority': 2},
            
            'CJ그룹': {'aliases': [], 'type': 'COMPANY', 'industry': '식품', 'priority': 1},
            'CJ': {'aliases': [], 'type': 'COMPANY', 'industry': '식품', 'priority': 2},
            '롯데그룹': {'aliases': [], 'type': 'COMPANY', 'industry': '유통', 'priority': 1},
            '롯데마트': {'aliases': [], 'type': 'COMPANY', 'industry': '유통', 'priority': 1},
            '롯데': {'aliases': [], 'type': 'COMPANY', 'industry': '유통', 'priority': 2},
            
            '이마트': {'aliases': ['E-mart'], 'type': 'COMPANY', 'industry': '유통', 'priority': 1},
            '홈플러스': {'aliases': [], 'type': 'COMPANY', 'industry': '유통', 'priority': 1},
            '두산그룹': {'aliases': [], 'type': 'COMPANY', 'industry': '중공업', 'priority': 1},
            '두산': {'aliases': [], 'type': 'COMPANY', 'industry': '중공업', 'priority': 2},
            
            'GS칼텍스': {'aliases': [], 'type': 'COMPANY', 'industry': '정유', 'priority': 1},
            'GS': {'aliases': [], 'type': 'COMPANY', 'industry': '그룹', 'priority': 2},
            'S-Oil': {'aliases': ['에스오일'], 'type': 'COMPANY', 'industry': '정유', 'priority': 1},
            
            # 항공
            '대한항공': {'aliases': ['Korean Air'], 'type': 'COMPANY', 'industry': '항공', 'priority': 1},
            '아시아나항공': {'aliases': ['아시아나'], 'type': 'COMPANY', 'industry': '항공', 'priority': 1},
            
            # 바이오/제약
            '셀트리온': {'aliases': [], 'type': 'COMPANY', 'industry': '바이오', 'priority': 1},
            
            # 엔터테인먼트
            'SM엔터테인먼트': {'aliases': [], 'type': 'COMPANY', 'industry': '엔터', 'priority': 1},
            '하이브': {'aliases': ['HYBE'], 'type': 'COMPANY', 'industry': '엔터', 'priority': 1},
            'SM': {'aliases': [], 'type': 'COMPANY', 'industry': '엔터', 'priority': 2},
            
            # 글로벌
            '디즈니플러스': {'aliases': ['Disney+'], 'type': 'COMPANY', 'industry': 'OTT', 'priority': 1},
            '넷플릭스': {'aliases': ['Netflix'], 'type': 'COMPANY', 'industry': 'OTT', 'priority': 1},
        }
        
        # 인명 데이터베이스 (확장된 버전)
        self.person_database = {
            # 삼성
            '이재용': {'company': '삼성전자', 'position': '회장', 'type': 'PERSON'},
            '이부진': {'company': '신라호텔', 'position': '사장', 'type': 'PERSON'},
            
            # 현대차
            '정의선': {'company': '현대자동차', 'position': '회장', 'type': 'PERSON'},
            
            # 네이버
            '최수연': {'company': '네이버', 'position': '대표', 'type': 'PERSON'},
            
            # 한화
            '김승연': {'company': '한화그룹', 'position': '회장', 'type': 'PERSON'},
            
            # 포스코
            '최정우': {'company': '포스코홀딩스', 'position': '회장', 'type': 'PERSON'},
            
            # 금융
            '윤종규': {'company': 'KB금융', 'position': '회장', 'type': 'PERSON'},
            '진옥동': {'company': '신한금융', 'position': '회장', 'type': 'PERSON'},
            
            # 두산
            '박정원': {'company': '두산그룹', 'position': '회장', 'type': 'PERSON'},
            
            # 대한항공
            '조원태': {'company': '대한항공', 'position': '회장', 'type': 'PERSON'},
            
            # 셀트리온
            '서정진': {'company': '셀트리온', 'position': '회장', 'type': 'PERSON'},
            
            # 토스
            '이승건': {'company': '토스', 'position': '대표', 'type': 'PERSON'},
        }
        
        # 직책 패턴
        self.position_patterns = [
            '회장', '대표', '사장', '부회장', '부사장', '전무', '상무', '이사', 
            '임원', '대표이사', '최고경영자', 'CEO', 'CFO', 'CTO', 'COO'
        ]
        
        # 연결사 패턴
        self.conjunctions = ['와', '과', '이', '가', '은', '는', '및', '그리고', '또한']
        
        # 회사 접미사 패턴
        self.company_suffixes = [
            '그룹', '홀딩스', '전자', '화학', '물산', '건설', '중공업', '자동차', 
            '모빌리티', '엔터테인먼트', '금융', '은행', '증권', '보험', '카드',
            'Oil', 'oil', '항공', '마켓', '플러스', '마트', '바이오'
        ]
        
        # 후처리 및 링킹
        self.postprocessor = KoreanNERPostProcessor(confidence_threshold=0.8)
        self.entity_linker = KoreanEntityLinker()
        self.cache_manager = get_cache_manager()
        
        # 성능 통계
        self.stats = {
            'total_calls': 0,
            'cache_hits': 0,
            'companies_found': 0,
            'persons_found': 0,
            'avg_processing_time': 0
        }
        
        logger.info("Enhanced Rule-based NER model initialized")
    
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
        
        try:
            # 캐시 확인
            model_config = {
                "model_name": "enhanced_rule_ner",
                "confidence_threshold": 0.8,
                "version": "2.0"
            }
            
            cached_result = self.cache_manager.get_cached_result(text, model_config)
            if cached_result is not None:
                self.stats['cache_hits'] += 1
                processing_time = (time.time() - start_time) * 1000
                logger.debug(f"Cache hit: returned {len(cached_result)} entities in {processing_time:.2f}ms")
                return cached_result
            
            # 실제 엔티티 추출
            entities = []
            
            # 1. 알려진 회사명 추출
            company_entities = self._extract_companies(text)
            entities.extend(company_entities)
            self.stats['companies_found'] += len(company_entities)
            
            # 2. 알려진 인명 추출
            person_entities = self._extract_persons(text)
            entities.extend(person_entities)
            self.stats['persons_found'] += len(person_entities)
            
            # 3. 패턴 기반 회사명 추출 (이미 찾은 위치 제외)
            found_positions_for_pattern = set()
            for entity in entities:
                found_positions_for_pattern.add((entity.start, entity.end - entity.start))
            pattern_companies = self._extract_companies_by_pattern(text, found_positions_for_pattern)
            entities.extend(pattern_companies)
            
            # 4. 패턴 기반 인명 추출
            pattern_persons = self._extract_persons_by_pattern(text)
            entities.extend(pattern_persons)
            
            # 중복 제거
            entities = self._remove_duplicates(entities)
            
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
    
    def _extract_companies(self, text: str) -> List[Entity]:
        """알려진 회사명 추출 (정확한 매칭 우선)"""
        entities = []
        found_positions = set()  # 중복 위치 방지
        
        # 1단계: 정확한 이름 매칭 (긴 이름부터)
        sorted_companies = sorted(
            self.company_database.items(),
            key=lambda x: (-len(x[0]), x[1].get('priority', 1))  # 길이 우선, 그 다음 우선순위
        )
        
        for company_name, company_info in sorted_companies:
            # 정확한 매칭만 (별칭보다 원래 이름 우선)
            start_idx = text.find(company_name)
            if start_idx != -1:
                end_idx = start_idx + len(company_name)
                # 위치 겹침 확인
                if not self._position_overlaps(start_idx, end_idx, found_positions):
                    entities.append(Entity(
                        text=company_name,
                        type='COMPANY',
                        start=start_idx,
                        end=end_idx,
                        confidence=0.98  # 정확한 매칭은 높은 신뢰도
                    ))
                    found_positions.add((start_idx, len(company_name)))
        
        # 2단계: 별칭 매칭 (남은 위치에서만)
        for company_name, company_info in sorted_companies:
            for alias in company_info.get('aliases', []):
                start_idx = text.find(alias)
                if start_idx != -1:
                    end_idx = start_idx + len(alias)
                    if not self._position_overlaps(start_idx, end_idx, found_positions):
                        # 별칭을 원래 이름으로 매핑하되, 텍스트에서 찾은 형태로 반환
                        entities.append(Entity(
                            text=alias,  # 실제 텍스트에 나타난 형태로 반환
                            type='COMPANY',
                            start=start_idx,
                            end=end_idx,
                            confidence=0.95
                        ))
                        found_positions.add((start_idx, len(alias)))
        
        # 3단계: 연결사 처리로 추가 엔티티 찾기
        conjunction_entities = self._extract_companies_by_conjunction(text, found_positions)
        entities.extend(conjunction_entities)
        
        return entities
    
    def _position_overlaps(self, start: int, end: int, found_positions: set) -> bool:
        """위치 겹침 확인"""
        for pos, length in found_positions:
            pos_end = pos + length
            # 겹침 조건: (start < pos_end) and (end > pos)
            if start < pos_end and end > pos:
                return True
        return False
    
    def _extract_companies_by_conjunction(self, text: str, found_positions: set) -> List[Entity]:
        """연결사 패턴으로 추가 회사명 찾기"""
        entities = []
        
        # 연결사 패턴을 더 정교하게 처리
        conjunctions = ['와', '과']
        
        for conjunction in conjunctions:
            # 개선된 패턴: 회사명 + 연결사 + 회사명
            patterns = [
                # 한글 회사명 패턴 (더 구체적)
                rf'([가-힣]+(?:그룹|전자|화학|물산|건설|금융|은행|홀딩스|모빌리티|엔터테인먼트|마켓|플러스)?){conjunction}\s*([가-힣]+(?:그룹|전자|화학|물산|건설|금융|은행|홀딩스|모빌리티|엔터테인먼트|마켓|플러스)?)',
                # 영문 포함 패턴
                rf'([가-힣A-Za-z0-9]+){conjunction}\s*([가-힣A-Za-z0-9]+)',
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                
                for match in matches:
                    company1 = match.group(1).strip()
                    company2 = match.group(2).strip()
                    
                    logger.debug(f"Found conjunction pattern: '{company1}' {conjunction} '{company2}'")
                    
                    # 각 회사가 데이터베이스에 있는지 확인
                    entities_to_add = []
                    
                    # 첫 번째 회사 확인
                    if self._is_valid_company_entity(company1):
                        start1 = match.start(1)
                        end1 = match.end(1)
                        
                        if not self._position_overlaps(start1, end1, found_positions):
                            entities_to_add.append(Entity(
                                text=company1,  # 실제 텍스트 형태로 반환
                                type='COMPANY',
                                start=start1,
                                end=end1,
                                confidence=0.9
                            ))
                    
                    # 두 번째 회사 확인
                    if self._is_valid_company_entity(company2):
                        start2 = match.start(2)
                        end2 = match.end(2)
                        
                        if not self._position_overlaps(start2, end2, found_positions):
                            entities_to_add.append(Entity(
                                text=company2,  # 실제 텍스트 형태로 반환
                                type='COMPANY',
                                start=start2,
                                end=end2,
                                confidence=0.9
                            ))
                    
                    # 엔티티 추가
                    for entity in entities_to_add:
                        entities.append(entity)
                        found_positions.add((entity.start, entity.end - entity.start))
                        logger.debug(f"Added conjunction entity: {entity.text}")
        
        return entities
    
    def _is_known_company_alias(self, company_text: str) -> bool:
        """알려진 회사 별칭인지 확인"""
        for company_name, company_info in self.company_database.items():
            if company_text in company_info.get('aliases', []):
                return True
        return False
    
    def _get_canonical_name(self, company_text: str) -> str:
        """별칭을 정식 이름으로 변환"""
        # 직접 매칭
        if company_text in self.company_database:
            return company_text
        
        # 별칭 매칭
        for company_name, company_info in self.company_database.items():
            if company_text in company_info.get('aliases', []):
                return company_name
        
        return company_text  # 찾지 못하면 원본 반환
    
    def _is_valid_company_entity(self, company_text: str) -> bool:
        """회사 엔티티로 유효한지 확인"""
        # 데이터베이스에 직접 있는 경우
        if company_text in self.company_database:
            return True
        
        # 별칭인 경우
        if self._is_known_company_alias(company_text):
            return True
        
        # 회사 접미사가 있는 경우
        for suffix in self.company_suffixes:
            if company_text.endswith(suffix) and len(company_text) > len(suffix):
                return True
        
        # 최소 길이 조건
        if len(company_text) >= 2:
            return True
        
        return False
    
    def _extract_persons(self, text: str) -> List[Entity]:
        """알려진 인명 추출"""
        entities = []
        
        for person_name, person_info in self.person_database.items():
            start_idx = text.find(person_name)
            if start_idx != -1:
                entities.append(Entity(
                    text=person_name,
                    type='PERSON',
                    start=start_idx,
                    end=start_idx + len(person_name),
                    confidence=0.95
                ))
        
        return entities
    
    def _extract_companies_by_pattern(self, text: str, found_positions: set = None) -> List[Entity]:
        """패턴 기반 회사명 추출"""
        entities = []
        if found_positions is None:
            found_positions = set()
        
        # 회사 접미사 패턴 (더 보수적으로)
        for suffix in self.company_suffixes:
            # 단어 경계를 고려한 패턴
            pattern = rf'\b([가-힣A-Za-z0-9]+{re.escape(suffix)})\b'
            matches = re.finditer(pattern, text)
            
            for match in matches:
                company_text = match.group(1)
                start_pos = match.start(1)
                end_pos = match.end(1)
                
                # 이미 찾은 위치와 겹치는지 확인
                if self._position_overlaps(start_pos, end_pos, found_positions):
                    continue
                
                # 너무 짧거나 긴 경우 제외
                if 2 <= len(company_text) <= 15:
                    # 연결사가 포함된 경우 제외 (예: "CJ그룹과 롯데그룹")
                    if any(conj in company_text for conj in ['와', '과', '이', '가']):
                        continue
                    
                    entities.append(Entity(
                        text=company_text,
                        type='COMPANY',
                        start=start_pos,
                        end=end_pos,
                        confidence=0.7
                    ))
                    
                    # 추가된 위치 기록
                    found_positions.add((start_pos, end_pos - start_pos))
        
        return entities
    
    def _extract_persons_by_pattern(self, text: str) -> List[Entity]:
        """패턴 기반 인명 추출"""
        entities = []
        
        # 한국 이름 + 직책 패턴
        position_pattern = '|'.join(self.position_patterns)
        person_pattern = rf'([가-힣]{{2,4}})\s*({position_pattern})'
        
        matches = re.finditer(person_pattern, text)
        for match in matches:
            person_name = match.group(1)
            position = match.group(2)
            
            # 일반적인 한국 이름인지 확인 (간단한 휴리스틱)
            if self._is_likely_korean_name(person_name):
                entities.append(Entity(
                    text=person_name,
                    type='PERSON',
                    start=match.start(1),
                    end=match.end(1),
                    confidence=0.8
                ))
        
        return entities
    
    def _is_likely_korean_name(self, name: str) -> bool:
        """한국 이름일 가능성 확인"""
        # 2-4글자 한글
        if not (2 <= len(name) <= 4 and all('\uAC00' <= char <= '\uD7A3' for char in name)):
            return False
        
        # 일반적이지 않은 패턴 제외
        exclude_patterns = [
            r'같은', r'때문', r'그룹', r'회사', r'기업', r'사업', r'시장', r'분야',
            r'제품', r'서비스', r'시스템', r'플랫폼', r'솔루션'
        ]
        
        for pattern in exclude_patterns:
            if re.search(pattern, name):
                return False
        
        return True
    
    def _remove_duplicates(self, entities: List[Entity]) -> List[Entity]:
        """중복 엔티티 제거"""
        seen = set()
        unique_entities = []
        
        for entity in entities:
            # 위치와 텍스트로 중복 확인
            key = (entity.text, entity.start, entity.end, entity.type)
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)
        
        return unique_entities
    
    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보 반환"""
        return {
            "model_name": "enhanced_rule_ner",
            "model_type": "rule_based",
            "supported_entity_types": ['PERSON', 'COMPANY'],
            "language": "ko",
            "version": "2.0.0",
            "company_database_size": len(self.company_database),
            "person_database_size": len(self.person_database),
            "statistics": self.stats.copy()
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """성능 통계 반환"""
        return self.stats.copy()
    
    def add_company(self, name: str, aliases: List[str] = None, industry: str = "Unknown"):
        """회사 데이터베이스에 새 회사 추가"""
        self.company_database[name] = {
            'aliases': aliases or [],
            'type': 'COMPANY',
            'industry': industry
        }
        logger.info(f"Added company: {name}")
    
    def add_person(self, name: str, company: str = "", position: str = ""):
        """인명 데이터베이스에 새 인물 추가"""
        self.person_database[name] = {
            'company': company,
            'position': position,
            'type': 'PERSON'
        }
        logger.info(f"Added person: {name}")
    
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