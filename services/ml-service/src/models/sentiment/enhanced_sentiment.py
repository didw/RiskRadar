"""
Enhanced Sentiment Analysis Model
향상된 감정 분석 모델 - 한국어 뉴스 특화
"""
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
import re
from dataclasses import dataclass

from ...kafka.schemas import Sentiment

logger = logging.getLogger(__name__)


@dataclass
class SentimentIndicator:
    """감정 지표 클래스"""
    words: List[str]
    weight: float
    context_dependent: bool = False


class EnhancedSentimentAnalyzer:
    """향상된 한국어 뉴스 감정 분석기"""
    
    def __init__(self):
        """모델 초기화"""
        
        # 긍정적 지표들
        self.positive_indicators = {
            'growth': SentimentIndicator(
                words=['증가', '상승', '성장', '확대', '급증', '호조', '개선', '향상', '회복', '반등'],
                weight=0.8
            ),
            'success': SentimentIndicator(
                words=['성공', '달성', '기록', '성과', '수익', '이익', '흑자', '수주', '계약', '협약'],
                weight=0.7
            ),
            'positive_business': SentimentIndicator(
                words=['투자', '확장', '진출', '출시', '런칭', '신규', '혁신', '개발', '발표'],
                weight=0.6
            ),
            'market_positive': SentimentIndicator(
                words=['신고가', '최고치', '최대', '강세', '호황', '활황', '급등'],
                weight=0.9
            )
        }
        
        # 부정적 지표들
        self.negative_indicators = {
            'decline': SentimentIndicator(
                words=['감소', '하락', '급락', '폭락', '하향', '축소', '둔화', '악화', '부진'],
                weight=0.8
            ),
            'problems': SentimentIndicator(
                words=['문제', '이슈', '우려', '위험', '리스크', '어려움', '고민', '압박'],
                weight=0.7
            ),
            'business_negative': SentimentIndicator(
                words=['손실', '적자', '실패', '중단', '연기', '취소', '철수', '포기'],
                weight=0.9
            ),
            'market_negative': SentimentIndicator(
                words=['신저가', '최저치', '최소', '약세', '불황', '침체', '폭락'],
                weight=0.9
            ),
            'legal_issues': SentimentIndicator(
                words=['소송', '기소', '조사', '수사', '제재', '처벌', '벌금', '과징금'],
                weight=0.8
            ),
            'financial_stress': SentimentIndicator(
                words=['연체', '부실', '파산', '회생', '구조조정', '정리해고', '부채'],
                weight=1.0
            )
        }
        
        # 중립적 지표들 (맥락에 따라 다름)
        self.neutral_indicators = {
            'change': SentimentIndicator(
                words=['변화', '변동', '조정', '개편', '재편', '전환'],
                weight=0.3,
                context_dependent=True
            ),
            'announcement': SentimentIndicator(
                words=['발표', '공개', '공지', '안내', '보고'],
                weight=0.2,
                context_dependent=True
            )
        }
        
        # 강화/약화 수식어
        self.intensifiers = {
            'strong_positive': ['대폭', '크게', '급격히', '현저히', '상당히', '대규모'],
            'strong_negative': ['대폭', '크게', '급격히', '현저히', '상당히', '심각하게'],
            'mild': ['소폭', '약간', '다소', '일부', '부분적으로']
        }
        
        # 부정 표현 패턴
        self.negation_patterns = [
            r'([^가-힣]|^)(아니다|아님|않다|못하다|없다|못한다)\s*([가-힣]*)',
            r'(불|무|미|비|반)([가-힣]+)',  # 접두사를 통한 부정
            r'([가-힣]+)(않다|안된다|못한다)'
        ]
        
        # 통계
        self.stats = {
            'total_analyses': 0,
            'positive_count': 0,
            'negative_count': 0,
            'neutral_count': 0,
            'avg_processing_time': 0
        }
        
        logger.info("Enhanced Sentiment Analyzer initialized")
    
    def analyze_sentiment(self, text: str, entities: Optional[List] = None) -> Sentiment:
        """
        향상된 감정 분석
        
        Args:
            text: 분석할 텍스트
            entities: 추출된 엔티티 (컨텍스트에 활용)
            
        Returns:
            Sentiment 객체
        """
        start_time = time.time()
        self.stats['total_analyses'] += 1
        
        try:
            # 텍스트 전처리
            cleaned_text = self._preprocess_text(text)
            
            # 감정 점수 계산
            sentiment_scores = self._calculate_sentiment_scores(cleaned_text)
            
            # 엔티티 기반 조정
            if entities:
                sentiment_scores = self._adjust_with_entities(sentiment_scores, entities, cleaned_text)
            
            # 최종 감정 결정
            final_sentiment = self._determine_final_sentiment(sentiment_scores)
            
            # 통계 업데이트
            self._update_stats(final_sentiment)
            
            processing_time = (time.time() - start_time) * 1000
            self.stats['avg_processing_time'] = (
                self.stats['avg_processing_time'] * (self.stats['total_analyses'] - 1) + processing_time
            ) / self.stats['total_analyses']
            
            logger.debug(f"Sentiment analysis: {final_sentiment['label']} (score: {final_sentiment['score']:.3f})")
            
            return Sentiment(
                label=final_sentiment['label'],
                score=final_sentiment['score'],
                probabilities=final_sentiment['probabilities']
            )
            
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return Sentiment(
                label="neutral",
                score=0.5,
                probabilities={"positive": 0.33, "neutral": 0.34, "negative": 0.33}
            )
    
    def _preprocess_text(self, text: str) -> str:
        """텍스트 전처리"""
        # 특수문자 정리
        text = re.sub(r'[^가-힣a-zA-Z0-9\s]', ' ', text)
        # 연속 공백 정리
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _calculate_sentiment_scores(self, text: str) -> Dict[str, float]:
        """감정 점수 계산"""
        positive_score = 0.0
        negative_score = 0.0
        neutral_score = 0.0
        
        # 긍정 지표 검사
        for category, indicator in self.positive_indicators.items():
            matches = self._find_indicator_matches(text, indicator.words)
            if matches:
                # 강화/약화 수식어 확인
                intensity = self._get_intensity_modifier(text, matches)
                score = len(matches) * indicator.weight * intensity
                positive_score += score
                logger.debug(f"Positive indicator '{category}': {matches} (score: +{score:.2f})")
        
        # 부정 지표 검사
        for category, indicator in self.negative_indicators.items():
            matches = self._find_indicator_matches(text, indicator.words)
            if matches:
                # 강화/약화 수식어 확인
                intensity = self._get_intensity_modifier(text, matches)
                score = len(matches) * indicator.weight * intensity
                negative_score += score
                logger.debug(f"Negative indicator '{category}': {matches} (score: -{score:.2f})")
        
        # 중립 지표 검사
        for category, indicator in self.neutral_indicators.items():
            matches = self._find_indicator_matches(text, indicator.words)
            if matches:
                score = len(matches) * indicator.weight
                neutral_score += score
        
        # 부정 표현 확인 (긍정/부정 점수 반전)
        positive_score, negative_score = self._handle_negations(
            text, positive_score, negative_score
        )
        
        return {
            'positive': positive_score,
            'negative': negative_score,
            'neutral': neutral_score
        }
    
    def _find_indicator_matches(self, text: str, words: List[str]) -> List[str]:
        """지표 단어 매칭"""
        matches = []
        for word in words:
            if word in text:
                matches.append(word)
        return matches
    
    def _get_intensity_modifier(self, text: str, matches: List[str]) -> float:
        """강화/약화 수식어에 따른 가중치 조정"""
        intensity = 1.0
        
        for match in matches:
            # 해당 단어 주변 10글자 내에서 수식어 찾기
            start_pos = text.find(match)
            if start_pos != -1:
                context_start = max(0, start_pos - 10)
                context_end = min(len(text), start_pos + len(match) + 10)
                context = text[context_start:context_end]
                
                # 강한 긍정/부정 수식어
                for intensifier in self.intensifiers['strong_positive'] + self.intensifiers['strong_negative']:
                    if intensifier in context:
                        intensity *= 1.5
                        break
                
                # 약한 수식어
                for mild_word in self.intensifiers['mild']:
                    if mild_word in context:
                        intensity *= 0.7
                        break
        
        return intensity
    
    def _handle_negations(self, text: str, positive_score: float, negative_score: float) -> Tuple[float, float]:
        """부정 표현 처리"""
        negation_count = 0
        
        for pattern in self.negation_patterns:
            matches = re.findall(pattern, text)
            negation_count += len(matches)
        
        # 부정 표현이 있으면 점수 반전 (완전 반전이 아닌 약화)
        if negation_count > 0:
            # 부정 표현 개수에 따른 조정
            negation_factor = min(0.8, negation_count * 0.3)
            
            # 긍정과 부정 점수 부분 교환
            new_positive = positive_score * (1 - negation_factor) + negative_score * negation_factor
            new_negative = negative_score * (1 - negation_factor) + positive_score * negation_factor
            
            logger.debug(f"Negation detected (count: {negation_count}), scores adjusted")
            return new_positive, new_negative
        
        return positive_score, negative_score
    
    def _adjust_with_entities(self, scores: Dict[str, float], entities: List, text: str) -> Dict[str, float]:
        """엔티티 정보를 활용한 감정 점수 조정"""
        # 회사 엔티티가 부정적 맥락에 언급되면 가중치 증가
        company_entities = [e for e in entities if getattr(e, 'type', '') == 'COMPANY']
        
        if company_entities:
            for entity in company_entities:
                entity_text = getattr(entity, 'text', '')
                # 회사 주변 맥락 분석 (앞뒤 20글자)
                start_pos = text.find(entity_text)
                if start_pos != -1:
                    context_start = max(0, start_pos - 20)
                    context_end = min(len(text), start_pos + len(entity_text) + 20)
                    context = text[context_start:context_end]
                    
                    # 부정적 맥락에서 회사가 언급되면 부정 점수 강화
                    negative_context_words = ['문제', '우려', '손실', '하락', '급락', '리스크']
                    if any(word in context for word in negative_context_words):
                        scores['negative'] *= 1.3
                        logger.debug(f"Company '{entity_text}' in negative context, increased negative score")
        
        return scores
    
    def _determine_final_sentiment(self, scores: Dict[str, float]) -> Dict[str, Any]:
        """최종 감정 결정"""
        positive_score = scores['positive']
        negative_score = scores['negative']
        neutral_score = scores['neutral']
        
        total_score = positive_score + negative_score + neutral_score
        
        if total_score == 0:
            return {
                'label': 'neutral',
                'score': 0.5,
                'probabilities': {'positive': 0.33, 'neutral': 0.34, 'negative': 0.33}
            }
        
        # 확률 계산
        pos_prob = positive_score / total_score
        neg_prob = negative_score / total_score
        neu_prob = neutral_score / total_score
        
        # 추가 보정 (극단적인 경우 방지)
        pos_prob = max(0.05, min(0.95, pos_prob))
        neg_prob = max(0.05, min(0.95, neg_prob))
        neu_prob = max(0.05, min(0.95, neu_prob))
        
        # 정규화
        total_prob = pos_prob + neg_prob + neu_prob
        pos_prob /= total_prob
        neg_prob /= total_prob
        neu_prob /= total_prob
        
        # 최종 레이블 결정
        if pos_prob > 0.5:
            label = 'positive'
            confidence = pos_prob
        elif neg_prob > 0.5:
            label = 'negative'
            confidence = neg_prob
        else:
            label = 'neutral'
            confidence = max(pos_prob, neg_prob, neu_prob)
        
        return {
            'label': label,
            'score': confidence,
            'probabilities': {
                'positive': round(pos_prob, 3),
                'neutral': round(neu_prob, 3),
                'negative': round(neg_prob, 3)
            }
        }
    
    def _update_stats(self, sentiment: Dict[str, Any]):
        """통계 업데이트"""
        label = sentiment['label']
        if label == 'positive':
            self.stats['positive_count'] += 1
        elif label == 'negative':
            self.stats['negative_count'] += 1
        else:
            self.stats['neutral_count'] += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """통계 정보 반환"""
        return self.stats.copy()
    
    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보 반환"""
        return {
            "model_name": "enhanced_sentiment_analyzer",
            "model_type": "rule_based_enhanced",
            "language": "ko",
            "version": "1.0.0",
            "features": [
                "keyword_based_analysis",
                "intensity_modifiers",
                "negation_handling",
                "entity_context_adjustment",
                "business_domain_specialized"
            ],
            "statistics": self.stats.copy()
        }
