"""
Enhanced Risk Analysis Model
향상된 리스크 분석 모델
"""
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)


@dataclass
class RiskFactor:
    """리스크 요소 클래스"""
    category: str
    keywords: List[str]
    base_weight: float
    severity_multiplier: Dict[str, float]
    context_dependent: bool = False


@dataclass
class RiskEvent:
    """리스크 이벤트"""
    event_type: str
    description: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    impact_areas: List[str]
    confidence: float
    detected_keywords: List[str]


class EnhancedRiskAnalyzer:
    """향상된 리스크 분석기"""
    
    def __init__(self):
        """모델 초기화"""
        
        # 금융 리스크 요소
        self.financial_risks = {
            'debt_default': RiskFactor(
                category='FINANCIAL',
                keywords=['연체', '부실', '채무불이행', '디폴트', '파산', '회생절차', '워크아웃'],
                base_weight=1.0,
                severity_multiplier={'연체': 0.7, '부실': 0.8, '파산': 1.0, '워크아웃': 0.9}
            ),
            'liquidity_crisis': RiskFactor(
                category='FINANCIAL',
                keywords=['유동성', '자금부족', '현금흐름', '단기차입', '긴급자금', '자금조달'],
                base_weight=0.8,
                severity_multiplier={'유동성': 0.6, '자금부족': 0.8, '긴급자금': 0.9}
            ),
            'credit_rating': RiskFactor(
                category='FINANCIAL', 
                keywords=['신용등급', '등급하향', '등급상향', '신용평가', '평점', 'BB', 'B등급'],
                base_weight=0.7,
                severity_multiplier={'등급하향': 0.8, '등급상향': -0.3, 'BB': 0.6}
            ),
            'earnings_decline': RiskFactor(
                category='FINANCIAL',
                keywords=['매출감소', '영업손실', '순손실', '적자', '손실확대', '수익성악화'],
                base_weight=0.6,
                severity_multiplier={'순손실': 0.8, '적자': 0.7, '영업손실': 0.9}
            )
        }
        
        # 운영 리스크 요소
        self.operational_risks = {
            'supply_chain': RiskFactor(
                category='OPERATIONAL',
                keywords=['공급망', '원재료', '부품부족', '납기지연', '공급중단', '물류대란'],
                base_weight=0.7,
                severity_multiplier={'공급중단': 0.9, '부품부족': 0.7, '물류대란': 0.8}
            ),
            'production_issues': RiskFactor(
                category='OPERATIONAL',
                keywords=['생산중단', '가동중단', '공장폐쇄', '시설점검', '품질문제', '리콜'],
                base_weight=0.8,
                severity_multiplier={'생산중단': 0.9, '리콜': 0.8, '공장폐쇄': 1.0}
            ),
            'labor_issues': RiskFactor(
                category='OPERATIONAL',
                keywords=['파업', '노사갈등', '임금협상', '정리해고', '구조조정', '노동분쟁'],
                base_weight=0.6,
                severity_multiplier={'파업': 0.8, '정리해고': 0.7, '구조조정': 0.9}
            )
        }
        
        # 법적/규제 리스크
        self.legal_risks = {
            'litigation': RiskFactor(
                category='LEGAL',
                keywords=['소송', '기소', '재판', '법정다툼', '손해배상', '집단소송'],
                base_weight=0.7,
                severity_multiplier={'기소': 0.9, '집단소송': 0.8, '손해배상': 0.7}
            ),
            'regulatory': RiskFactor(
                category='LEGAL',
                keywords=['규제', '제재', '과징금', '벌금', '행정처분', '영업정지'],
                base_weight=0.8,
                severity_multiplier={'영업정지': 1.0, '과징금': 0.7, '제재': 0.8}
            ),
            'compliance': RiskFactor(
                category='LEGAL',
                keywords=['컴플라이언스', '법규위반', '내부통제', '감사지적', '위법행위'],
                base_weight=0.6,
                severity_multiplier={'법규위반': 0.8, '위법행위': 0.9}
            )
        }
        
        # 시장/경쟁 리스크
        self.market_risks = {
            'market_decline': RiskFactor(
                category='MARKET',
                keywords=['시장축소', '수요감소', '경기침체', '불황', '매출하락', '점유율하락'],
                base_weight=0.6,
                severity_multiplier={'불황': 0.8, '시장축소': 0.7, '점유율하락': 0.6}
            ),
            'competition': RiskFactor(
                category='MARKET',
                keywords=['경쟁심화', '신규진입', '가격경쟁', '경쟁업체', '시장포화'],
                base_weight=0.5,
                severity_multiplier={'신규진입': 0.6, '가격경쟁': 0.7}
            ),
            'technology_disruption': RiskFactor(
                category='MARKET',
                keywords=['기술변화', '디지털전환', '플랫폼', '혁신', '구조변화', '신기술'],
                base_weight=0.6,
                severity_multiplier={'기술변화': 0.6, '구조변화': 0.7},
                context_dependent=True
            )
        }
        
        # ESG 리스크
        self.esg_risks = {
            'environmental': RiskFactor(
                category='ESG',
                keywords=['환경오염', '탄소배출', '폐수', '대기오염', '환경규제', '친환경'],
                base_weight=0.5,
                severity_multiplier={'환경오염': 0.8, '환경규제': 0.6}
            ),
            'social': RiskFactor(
                category='ESG',
                keywords=['사회적책임', '인권', '다양성', '지역사회', '윤리경영'],
                base_weight=0.4,
                severity_multiplier={'인권': 0.6}
            ),
            'governance': RiskFactor(
                category='ESG',
                keywords=['지배구조', '투명성', '이사회', '주주권익', '내부거래'],
                base_weight=0.5,
                severity_multiplier={'내부거래': 0.7}
            )
        }
        
        # 모든 리스크 요소 통합
        self.all_risk_factors = {
            **self.financial_risks,
            **self.operational_risks,
            **self.legal_risks,
            **self.market_risks,
            **self.esg_risks
        }
        
        # 심각도 키워드
        self.severity_indicators = {
            'critical': ['긴급', '심각', '위험', '급격', '대규모', '전면', '완전'],
            'high': ['크게', '대폭', '상당', '현저', '급증', '급감'],
            'medium': ['일부', '부분', '약간', '소폭', '다소'],
            'low': ['미미', '소량', '경미']
        }
        
        # 통계
        self.stats = {
            'total_analyses': 0,
            'high_risk_count': 0,
            'medium_risk_count': 0,
            'low_risk_count': 0,
            'avg_processing_time': 0,
            'avg_risk_score': 0
        }
        
        logger.info("Enhanced Risk Analyzer initialized")
    
    def analyze_risk(self, text: str, entities: Optional[List] = None, 
                    sentiment: Optional[Dict] = None) -> Dict[str, Any]:
        """
        종합적인 리스크 분석
        
        Args:
            text: 분석할 텍스트
            entities: 추출된 엔티티
            sentiment: 감정 분석 결과
            
        Returns:
            리스크 분석 결과
        """
        start_time = time.time()
        self.stats['total_analyses'] += 1
        
        try:
            # 1. 리스크 이벤트 감지
            risk_events = self._detect_risk_events(text)
            
            # 2. 카테고리별 리스크 점수 계산
            category_scores = self._calculate_category_scores(text, risk_events)
            
            # 3. 엔티티 기반 조정
            if entities:
                category_scores = self._adjust_with_entities(category_scores, entities, text)
            
            # 4. 감정 기반 조정
            if sentiment:
                category_scores = self._adjust_with_sentiment(category_scores, sentiment)
            
            # 5. 종합 리스크 점수 계산
            overall_risk_score = self._calculate_overall_risk(category_scores)
            
            # 6. 리스크 등급 결정
            risk_level = self._determine_risk_level(overall_risk_score)
            
            # 7. 주요 리스크 요약
            risk_summary = self._generate_risk_summary(risk_events, category_scores)
            
            processing_time = (time.time() - start_time) * 1000
            self._update_stats(overall_risk_score, processing_time)
            
            result = {
                'overall_risk_score': round(overall_risk_score, 3),
                'risk_level': risk_level,
                'category_scores': {k: round(v, 3) for k, v in category_scores.items()},
                'detected_events': [self._event_to_dict(event) for event in risk_events],
                'risk_summary': risk_summary,
                'processing_time_ms': round(processing_time, 2)
            }
            
            logger.debug(f"Risk analysis: {risk_level} (score: {overall_risk_score:.3f})")
            return result
            
        except Exception as e:
            logger.error(f"Risk analysis failed: {e}")
            return {
                'overall_risk_score': 0.0,
                'risk_level': 'UNKNOWN',
                'category_scores': {},
                'detected_events': [],
                'risk_summary': 'Analysis failed',
                'processing_time_ms': (time.time() - start_time) * 1000
            }
    
    def _detect_risk_events(self, text: str) -> List[RiskEvent]:
        """리스크 이벤트 감지"""
        events = []
        
        for risk_name, risk_factor in self.all_risk_factors.items():
            detected_keywords = []
            
            # 키워드 매칭
            for keyword in risk_factor.keywords:
                if keyword in text:
                    detected_keywords.append(keyword)
            
            if detected_keywords:
                # 심각도 결정
                severity = self._determine_event_severity(text, detected_keywords)
                
                # 신뢰도 계산
                confidence = self._calculate_event_confidence(
                    text, detected_keywords, risk_factor
                )
                
                event = RiskEvent(
                    event_type=risk_name,
                    description=f"{risk_factor.category} 리스크: {', '.join(detected_keywords)}",
                    severity=severity,
                    impact_areas=[risk_factor.category],
                    confidence=confidence,
                    detected_keywords=detected_keywords
                )
                
                events.append(event)
        
        return events
    
    def _determine_event_severity(self, text: str, keywords: List[str]) -> str:
        """이벤트 심각도 결정"""
        severity_scores = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        
        # 각 키워드 주변의 심각도 지시어 확인
        for keyword in keywords:
            keyword_pos = text.find(keyword)
            if keyword_pos != -1:
                # 키워드 주변 20글자 확인
                context_start = max(0, keyword_pos - 20)
                context_end = min(len(text), keyword_pos + len(keyword) + 20)
                context = text[context_start:context_end]
                
                for severity, indicators in self.severity_indicators.items():
                    for indicator in indicators:
                        if indicator in context:
                            severity_scores[severity] += 1
        
        # 가장 높은 심각도 반환
        if severity_scores['critical'] > 0:
            return 'CRITICAL'
        elif severity_scores['high'] > 0:
            return 'HIGH'
        elif severity_scores['medium'] > 0:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _calculate_event_confidence(self, text: str, keywords: List[str], 
                                  risk_factor: RiskFactor) -> float:
        """이벤트 신뢰도 계산"""
        base_confidence = 0.5
        
        # 키워드 개수에 따른 신뢰도 증가
        keyword_bonus = min(0.3, len(keywords) * 0.1)
        
        # 구체적인 키워드일수록 높은 신뢰도
        specificity_bonus = 0.0
        for keyword in keywords:
            if len(keyword) >= 4:  # 4글자 이상 구체적
                specificity_bonus += 0.1
        
        specificity_bonus = min(0.2, specificity_bonus)
        
        # 컨텍스트 관련성 확인
        context_bonus = 0.0
        if risk_factor.category == 'FINANCIAL':
            financial_context = ['회사', '기업', '매출', '영업', '재무', '경영']
            if any(word in text for word in financial_context):
                context_bonus = 0.1
        
        final_confidence = min(1.0, base_confidence + keyword_bonus + specificity_bonus + context_bonus)
        return final_confidence
    
    def _calculate_category_scores(self, text: str, events: List[RiskEvent]) -> Dict[str, float]:
        """카테고리별 리스크 점수 계산"""
        category_scores = {
            'FINANCIAL': 0.0,
            'OPERATIONAL': 0.0,
            'LEGAL': 0.0,
            'MARKET': 0.0,
            'ESG': 0.0
        }
        
        for event in events:
            category = event.impact_areas[0]
            
            # 기본 점수
            base_score = 0.3
            
            # 심각도에 따른 점수
            severity_multiplier = {
                'CRITICAL': 1.0,
                'HIGH': 0.8,
                'MEDIUM': 0.6,
                'LOW': 0.4
            }
            
            score = base_score * severity_multiplier.get(event.severity, 0.4) * event.confidence
            category_scores[category] = max(category_scores[category], score)
        
        return category_scores
    
    def _adjust_with_entities(self, scores: Dict[str, float], entities: List, text: str) -> Dict[str, float]:
        """엔티티 정보를 활용한 점수 조정"""
        # 회사 엔티티가 부정적 맥락에서 언급되면 점수 증가
        company_entities = [e for e in entities if getattr(e, 'type', '') == 'COMPANY']
        
        if company_entities:
            negative_context_words = ['문제', '우려', '손실', '하락', '급락', '리스크', '위험']
            
            for entity in company_entities:
                entity_text = getattr(entity, 'text', '')
                start_pos = text.find(entity_text)
                if start_pos != -1:
                    # 회사명 주변 30글자 컨텍스트
                    context_start = max(0, start_pos - 30)
                    context_end = min(len(text), start_pos + len(entity_text) + 30)
                    context = text[context_start:context_end]
                    
                    negative_words_found = sum(1 for word in negative_context_words if word in context)
                    
                    if negative_words_found > 0:
                        # 모든 카테고리 점수를 약간 증가
                        adjustment = min(0.2, negative_words_found * 0.05)
                        for category in scores:
                            scores[category] = min(1.0, scores[category] + adjustment)
        
        return scores
    
    def _adjust_with_sentiment(self, scores: Dict[str, float], sentiment: Dict) -> Dict[str, float]:
        """감정 분석 결과를 활용한 점수 조정"""
        sentiment_label = sentiment.get('label', 'neutral')
        sentiment_score = sentiment.get('score', 0.5)
        
        if sentiment_label == 'negative' and sentiment_score > 0.6:
            # 부정적 감정일 때 리스크 점수 증가
            adjustment = (sentiment_score - 0.5) * 0.3  # 최대 0.15 증가
            for category in scores:
                scores[category] = min(1.0, scores[category] + adjustment)
        
        elif sentiment_label == 'positive' and sentiment_score > 0.6:
            # 긍정적 감정일 때 리스크 점수 감소
            adjustment = (sentiment_score - 0.5) * 0.2  # 최대 0.1 감소
            for category in scores:
                scores[category] = max(0.0, scores[category] - adjustment)
        
        return scores
    
    def _calculate_overall_risk(self, category_scores: Dict[str, float]) -> float:
        """종합 리스크 점수 계산"""
        # 카테고리별 가중치
        weights = {
            'FINANCIAL': 0.35,
            'OPERATIONAL': 0.25,
            'LEGAL': 0.20,
            'MARKET': 0.15,
            'ESG': 0.05
        }
        
        weighted_score = sum(
            category_scores.get(category, 0) * weight
            for category, weight in weights.items()
        )
        
        return min(1.0, weighted_score)
    
    def _determine_risk_level(self, risk_score: float) -> str:
        """리스크 등급 결정"""
        if risk_score >= 0.8:
            return 'CRITICAL'
        elif risk_score >= 0.6:
            return 'HIGH'
        elif risk_score >= 0.4:
            return 'MEDIUM'
        elif risk_score >= 0.2:
            return 'LOW'
        else:
            return 'MINIMAL'
    
    def _generate_risk_summary(self, events: List[RiskEvent], 
                             category_scores: Dict[str, float]) -> str:
        """리스크 요약 생성"""
        if not events:
            return "특별한 리스크 요소가 감지되지 않았습니다."
        
        # 주요 리스크 카테고리 식별
        main_risks = [(cat, score) for cat, score in category_scores.items() if score > 0.3]
        main_risks.sort(key=lambda x: x[1], reverse=True)
        
        if not main_risks:
            return "낮은 수준의 리스크 요소들이 감지되었습니다."
        
        summary_parts = []
        
        # 주요 리스크 1-2개 언급
        for category, score in main_risks[:2]:
            category_name_kr = {
                'FINANCIAL': '재무',
                'OPERATIONAL': '운영',
                'LEGAL': '법적',
                'MARKET': '시장',
                'ESG': 'ESG'
            }.get(category, category)
            
            relevant_events = [e for e in events if category in e.impact_areas]
            if relevant_events:
                keywords = set()
                for event in relevant_events:
                    keywords.update(event.detected_keywords)
                
                summary_parts.append(
                    f"{category_name_kr} 리스크 감지 (관련: {', '.join(list(keywords)[:3])})"
                )
        
        return "; ".join(summary_parts)
    
    def _event_to_dict(self, event: RiskEvent) -> Dict[str, Any]:
        """RiskEvent를 딕셔너리로 변환"""
        return {
            'event_type': event.event_type,
            'description': event.description,
            'severity': event.severity,
            'impact_areas': event.impact_areas,
            'confidence': round(event.confidence, 3),
            'detected_keywords': event.detected_keywords
        }
    
    def _update_stats(self, risk_score: float, processing_time: float):
        """통계 업데이트"""
        if risk_score >= 0.6:
            self.stats['high_risk_count'] += 1
        elif risk_score >= 0.4:
            self.stats['medium_risk_count'] += 1
        else:
            self.stats['low_risk_count'] += 1
        
        # 평균 처리 시간 업데이트
        self.stats['avg_processing_time'] = (
            self.stats['avg_processing_time'] * (self.stats['total_analyses'] - 1) + processing_time
        ) / self.stats['total_analyses']
        
        # 평균 리스크 점수 업데이트
        self.stats['avg_risk_score'] = (
            self.stats['avg_risk_score'] * (self.stats['total_analyses'] - 1) + risk_score
        ) / self.stats['total_analyses']
    
    def get_statistics(self) -> Dict[str, Any]:
        """통계 정보 반환"""
        return self.stats.copy()
    
    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보 반환"""
        return {
            "model_name": "enhanced_risk_analyzer",
            "model_type": "multi_factor_rule_based",
            "version": "1.0.0",
            "supported_categories": list(set(
                factor.category for factor in self.all_risk_factors.values()
            )),
            "total_risk_factors": len(self.all_risk_factors),
            "features": [
                "multi_category_analysis",
                "severity_detection",
                "entity_context_adjustment",
                "sentiment_integration",
                "confidence_scoring"
            ],
            "statistics": self.stats.copy()
        }
    
    def add_custom_risk_factor(self, name: str, category: str, keywords: List[str], 
                              base_weight: float = 0.5):
        """사용자 정의 리스크 요소 추가"""
        self.all_risk_factors[name] = RiskFactor(
            category=category,
            keywords=keywords,
            base_weight=base_weight,
            severity_multiplier={kw: 0.7 for kw in keywords}
        )
        logger.info(f"Added custom risk factor: {name}")
