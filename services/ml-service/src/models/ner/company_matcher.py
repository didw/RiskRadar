"""
한국어 기업명 고급 매칭 시스템
Korean Company Name Advanced Matching System
"""
import re
import logging
from typing import List, Dict, Set, Optional, Tuple
from difflib import SequenceMatcher
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CompanyMatch:
    """기업명 매칭 결과"""
    canonical_name: str
    confidence: float
    match_type: str  # exact, alias, fuzzy, pattern
    matched_text: str


class KoreanCompanyMatcher:
    """한국어 기업명 고급 매칭기"""
    
    def __init__(self):
        """초기화"""
        
        # 한국 기업 패턴
        self.company_patterns = [
            # 대기업 그룹
            r'삼성(?:전자|SDI|바이오로직스|물산|생명|화재|카드)?',
            r'LG(?:전자|화학|에너지솔루션|유플러스|디스플레이)?',
            r'SK(?:하이닉스|텔레콤|이노베이션|바이오팜|머티리얼즈)?',
            r'현대(?:자동차|모비스|글로비스|건설|중공업)?',
            r'롯데(?:쇼핑|케미칼|정밀화학|웰푸드|칠성)?',
            
            # IT/기술 기업
            r'네이버|NAVER',
            r'카카오(?:톡|페이|뱅크|게임즈)?',
            r'쿠팡|Coupang',
            r'배달의민족',
            r'토스|비바리퍼블리카',
            
            # 금융
            r'(?:국민|신한|하나|우리|농협)(?:은행|금융|카드|증권|생명|손해보험)?',
            r'KB(?:국민은행|금융|카드|손해보험|생명보험)?',
            
            # 제조업
            r'포스코(?:홀딩스|강판|케미칼)?',
            r'한화(?:시스템|에어로스페이스|솔루션|케미칼)?',
            
            # 항공/운송
            r'대한항공|아시아나항공',
            r'한진(?:해운|택배|칼)?',
        ]
        
        # 기업 접미사 패턴
        self.suffix_patterns = [
            r'\(주\)|\(유\)|\(재\)',
            r'주식회사|유한회사|재단법인|사단법인',
            r'㈜|㈜|㈲',
            r'그룹|홀딩스|Holdings|Group',
            r'코퍼레이션|Corporation|Corp\.?',
            r'컴퍼니|Company|Co\.?',
            r'리미티드|Limited|Ltd\.?',
            r'인코퍼레이티드|Incorporated|Inc\.?',
        ]
        
        # 산업별 키워드
        self.industry_keywords = {
            '전자/IT': ['전자', '컴퓨터', '소프트웨어', '시스템', '테크', '테크놀로지'],
            '자동차': ['자동차', '차량', '모터', '모빌리티'],
            '화학': ['화학', '케미칼', '정유', '석유'],
            '금융': ['은행', '금융', '보험', '증권', '카드', '캐피탈'],
            '건설': ['건설', '건축', '토목', '부동산'],
            '식품': ['식품', '음료', '제과', '육류'],
            '의료': ['제약', '바이오', '의료', '병원']
        }
        
        # 컴파일된 패턴 캐시
        self._compiled_patterns = {}
        self._compile_patterns()
        
        logger.info("Korean Company Matcher initialized")
    
    def _compile_patterns(self):
        """정규표현식 패턴 컴파일"""
        self._compiled_patterns['companies'] = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.company_patterns
        ]
        self._compiled_patterns['suffixes'] = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.suffix_patterns
        ]
    
    def match_company(self, text: str, candidates: List[str] = None) -> List[CompanyMatch]:
        """
        기업명 매칭 수행
        
        Args:
            text: 매칭할 텍스트
            candidates: 후보 기업명 리스트 (None이면 패턴 매칭)
            
        Returns:
            매칭 결과 리스트
        """
        matches = []
        
        # 1. 정확 매칭
        exact_matches = self._exact_match(text, candidates)
        matches.extend(exact_matches)
        
        # 2. 패턴 매칭
        pattern_matches = self._pattern_match(text)
        matches.extend(pattern_matches)
        
        # 3. 퍼지 매칭
        if candidates:
            fuzzy_matches = self._fuzzy_match(text, candidates)
            matches.extend(fuzzy_matches)
        
        # 4. 부분 매칭
        partial_matches = self._partial_match(text, candidates)
        matches.extend(partial_matches)
        
        # 중복 제거 및 정렬
        matches = self._deduplicate_matches(matches)
        matches.sort(key=lambda x: x.confidence, reverse=True)
        
        return matches[:5]  # 상위 5개만 반환
    
    def _exact_match(self, text: str, candidates: List[str] = None) -> List[CompanyMatch]:
        """정확 매칭"""
        matches = []
        
        if candidates:
            for candidate in candidates:
                if text.lower() == candidate.lower():
                    matches.append(CompanyMatch(
                        canonical_name=candidate,
                        confidence=1.0,
                        match_type="exact",
                        matched_text=text
                    ))
        
        return matches
    
    def _pattern_match(self, text: str) -> List[CompanyMatch]:
        """패턴 기반 매칭"""
        matches = []
        
        for pattern in self._compiled_patterns['companies']:
            match = pattern.search(text)
            if match:
                matched_text = match.group(0)
                canonical_name = self._normalize_company_name(matched_text)
                
                matches.append(CompanyMatch(
                    canonical_name=canonical_name,
                    confidence=0.9,
                    match_type="pattern",
                    matched_text=matched_text
                ))
        
        return matches
    
    def _fuzzy_match(self, text: str, candidates: List[str]) -> List[CompanyMatch]:
        """퍼지 매칭 (편집 거리 기반)"""
        matches = []
        
        for candidate in candidates:
            # 기본 유사도 계산
            similarity = SequenceMatcher(None, text.lower(), candidate.lower()).ratio()
            
            # 한국어 특화 유사도 보정
            adjusted_similarity = self._adjust_korean_similarity(text, candidate, similarity)
            
            if adjusted_similarity > 0.7:  # 70% 이상 유사
                matches.append(CompanyMatch(
                    canonical_name=candidate,
                    confidence=adjusted_similarity,
                    match_type="fuzzy",
                    matched_text=text
                ))
        
        return matches
    
    def _partial_match(self, text: str, candidates: List[str] = None) -> List[CompanyMatch]:
        """부분 매칭"""
        matches = []
        
        if candidates:
            for candidate in candidates:
                # 텍스트가 후보에 포함되는지 확인
                if text.lower() in candidate.lower() or candidate.lower() in text.lower():
                    # 포함 비율 계산
                    overlap = len(text) / max(len(candidate), len(text))
                    
                    if overlap > 0.5:  # 50% 이상 겹침
                        matches.append(CompanyMatch(
                            canonical_name=candidate,
                            confidence=0.6 + (overlap * 0.3),  # 0.6~0.9 범위
                            match_type="partial",
                            matched_text=text
                        ))
        
        return matches
    
    def _adjust_korean_similarity(self, text1: str, text2: str, base_similarity: float) -> float:
        """한국어 특성을 반영한 유사도 조정"""
        
        # 자소 분해를 통한 유사도 보정 (간단한 버전)
        # 실제로는 더 정교한 한글 유사도 알고리즘 사용 가능
        
        # 길이 차이 페널티
        length_diff = abs(len(text1) - len(text2))
        length_penalty = min(length_diff * 0.1, 0.3)
        
        # 접미사 유사성 보너스
        suffix_bonus = 0.0
        if self._has_similar_suffix(text1, text2):
            suffix_bonus = 0.1
        
        # 산업 키워드 보너스
        industry_bonus = 0.0
        if self._has_common_industry_keywords(text1, text2):
            industry_bonus = 0.05
        
        adjusted = base_similarity - length_penalty + suffix_bonus + industry_bonus
        return max(0.0, min(1.0, adjusted))
    
    def _has_similar_suffix(self, text1: str, text2: str) -> bool:
        """유사한 접미사를 가지는지 확인"""
        suffixes1 = self._extract_suffixes(text1)
        suffixes2 = self._extract_suffixes(text2)
        
        return bool(suffixes1.intersection(suffixes2))
    
    def _extract_suffixes(self, text: str) -> Set[str]:
        """텍스트에서 접미사 추출"""
        suffixes = set()
        
        for pattern in self._compiled_patterns['suffixes']:
            matches = pattern.findall(text)
            suffixes.update(matches)
        
        return suffixes
    
    def _has_common_industry_keywords(self, text1: str, text2: str) -> bool:
        """공통 산업 키워드를 가지는지 확인"""
        for industry, keywords in self.industry_keywords.items():
            keywords1 = [kw for kw in keywords if kw in text1]
            keywords2 = [kw for kw in keywords if kw in text2]
            
            if keywords1 and keywords2:
                return True
        
        return False
    
    def _normalize_company_name(self, name: str) -> str:
        """기업명 정규화"""
        # 접미사 제거 후 정규화
        normalized = name
        
        # 불필요한 접미사 제거
        for pattern in self._compiled_patterns['suffixes']:
            normalized = pattern.sub('', normalized).strip()
        
        # 알려진 정규명으로 변환
        aliases = {
            '삼성전': '삼성전자',
            '삼성': '삼성전자',
            '현대차': '현대자동차',
            '현대': '현대자동차',
            'LG': 'LG전자',
            '하이닉스': 'SK하이닉스',
            '네이버': 'NAVER',
            '카카오': 'Kakao'
        }
        
        return aliases.get(normalized, normalized)
    
    def _deduplicate_matches(self, matches: List[CompanyMatch]) -> List[CompanyMatch]:
        """중복 매칭 제거"""
        seen = {}
        unique_matches = []
        
        for match in matches:
            key = match.canonical_name.lower()
            
            if key not in seen or match.confidence > seen[key].confidence:
                if key in seen:
                    # 기존 매칭 제거
                    unique_matches = [m for m in unique_matches if m.canonical_name.lower() != key]
                
                seen[key] = match
                unique_matches.append(match)
        
        return unique_matches
    
    def extract_all_companies(self, text: str, candidates: List[str] = None) -> List[CompanyMatch]:
        """텍스트에서 모든 기업명 추출"""
        all_matches = []
        
        # 문장을 단어별로 분할하여 각각 매칭
        words = re.findall(r'[가-힣a-zA-Z0-9]+', text)
        
        for word in words:
            if len(word) >= 2:  # 2글자 이상만 처리
                matches = self.match_company(word, candidates)
                all_matches.extend(matches)
        
        # 전체 텍스트에 대해서도 매칭
        full_matches = self.match_company(text, candidates)
        all_matches.extend(full_matches)
        
        return self._deduplicate_matches(all_matches)
    
    def get_industry_classification(self, company_name: str) -> Optional[str]:
        """기업명으로부터 산업 분류 추정"""
        company_lower = company_name.lower()
        
        for industry, keywords in self.industry_keywords.items():
            if any(keyword in company_lower for keyword in keywords):
                return industry
        
        return None
    
    def validate_company_name(self, name: str) -> bool:
        """기업명 형식 유효성 검사"""
        # 너무 짧거나 긴 이름 거부
        if len(name) < 2 or len(name) > 50:
            return False
        
        # 숫자만으로 구성된 이름 거부
        if name.isdigit():
            return False
        
        # 특수 문자만으로 구성된 이름 거부
        if not re.search(r'[가-힣a-zA-Z]', name):
            return False
        
        return True