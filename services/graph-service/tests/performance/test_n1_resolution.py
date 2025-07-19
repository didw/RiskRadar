"""N+1 문제 해결 성능 테스트"""
import pytest
import time
from unittest.mock import patch, MagicMock
from src.kafka.handlers import GraphMessageHandler
from src.kafka.entity_cache import entity_cache
from src.algorithms.batch_entity_matching import batch_matcher

class TestN1Resolution:
    """N+1 문제 해결 성능 테스트"""
    
    @pytest.fixture
    def handler(self):
        """핸들러 fixture"""
        return GraphMessageHandler()
    
    @pytest.fixture
    def sample_news_with_entities(self):
        """엔티티가 많은 뉴스 샘플"""
        return {
            'id': 'n1-test-news',
            'title': 'N+1 Performance Test News',
            'content': 'Test content',
            'url': 'https://example.com/test',
            'published_at': '2024-01-01T00:00:00',
            'source': 'Test Source',
            'entities': [
                {'type': 'COMPANY', 'text': f'Test Company {i}', 'confidence': 0.9}
                for i in range(20)  # 20개 기업 엔티티
            ] + [
                {'type': 'PERSON', 'text': f'Test Person {i}', 'confidence': 0.8}
                for i in range(15)  # 15개 인물 엔티티
            ],
            'sentiment': 0.5,
            'risk_score': 3.0,
            'risk_indicators': ['test'],
            'topics': ['performance']
        }
    
    @pytest.mark.performance
    def test_n1_problem_demonstration(self, sample_news_with_entities):
        """N+1 문제 시뮬레이션 - 기존 방식"""
        # 기존 방식 시뮬레이션: 각 엔티티마다 DB 쿼리
        query_count = 0
        
        def mock_db_query(*args, **kwargs):
            nonlocal query_count
            query_count += 1
            time.sleep(0.01)  # DB 쿼리 지연 시뮬레이션
            return []  # 빈 결과 반환
        
        start_time = time.time()
        
        # 35개 엔티티 × 2번 쿼리 (Company, Person) = 70번 예상
        with patch('src.neo4j.session.session.run_query', side_effect=mock_db_query):
            for entity in sample_news_with_entities['entities']:
                if entity['type'] == 'COMPANY':
                    mock_db_query("MATCH (c:Company) RETURN c")  # 전체 Company 조회
                elif entity['type'] == 'PERSON':
                    mock_db_query("MATCH (p:Person) RETURN p")  # 전체 Person 조회
        
        elapsed_old = time.time() - start_time
        
        print(f"\n🚨 기존 방식 (N+1 문제):")
        print(f"  쿼리 수: {query_count}번")
        print(f"  소요 시간: {elapsed_old:.3f}초")
        print(f"  엔티티당 평균: {elapsed_old/len(sample_news_with_entities['entities']):.3f}초")
        
        assert query_count == len(sample_news_with_entities['entities'])  # 엔티티마다 1번씩
    
    @pytest.mark.performance
    def test_batch_matching_performance(self, sample_news_with_entities):
        """배치 매칭 성능 테스트 - 개선된 방식"""
        query_count = 0
        
        def mock_cache_get_companies():
            nonlocal query_count
            query_count += 1
            time.sleep(0.05)  # 캐시 조회 시뮬레이션
            return [{'id': f'company-{i}', 'name': f'Test Company {i}', 'aliases': []} for i in range(100)]
        
        def mock_cache_get_persons():
            nonlocal query_count
            query_count += 1
            time.sleep(0.03)  # 캐시 조회 시뮬레이션
            return [{'id': f'person-{i}', 'name': f'Test Person {i}', 'aliases': []} for i in range(50)]
        
        start_time = time.time()
        
        # 배치 매칭: 2번의 캐시 조회만
        with patch.object(entity_cache, 'get_companies', side_effect=mock_cache_get_companies), \
             patch.object(entity_cache, 'get_persons', side_effect=mock_cache_get_persons):
            
            # 배치 매칭 실행
            results = batch_matcher.match_entities_batch(sample_news_with_entities['entities'])
        
        elapsed_new = time.time() - start_time
        
        print(f"\n✅ 개선된 방식 (배치 매칭):")
        print(f"  쿼리 수: {query_count}번")
        print(f"  소요 시간: {elapsed_new:.3f}초")
        print(f"  엔티티당 평균: {elapsed_new/len(sample_news_with_entities['entities']):.3f}초")
        print(f"  매칭 결과: {len(results)}개")
        
        # 성능 기준
        assert query_count <= 2  # 최대 2번의 캐시 조회
        assert elapsed_new < 0.2  # 0.2초 이내
        assert len(results) == len(sample_news_with_entities['entities'])
    
    @pytest.mark.performance
    def test_cache_effectiveness(self):
        """캐시 효과성 테스트"""
        query_count = 0
        
        def mock_db_query(*args, **kwargs):
            nonlocal query_count
            query_count += 1
            return [{'id': f'test-{i}', 'name': f'Test Entity {i}', 'aliases': []} for i in range(10)]
        
        # 캐시 초기화
        entity_cache.clear_cache()
        
        with patch('src.neo4j.session.session.run_query', side_effect=mock_db_query):
            # 첫 번째 조회 - 캐시 미스
            start1 = time.time()
            companies1 = entity_cache.get_companies()
            time1 = time.time() - start1
            
            # 두 번째 조회 - 캐시 히트
            start2 = time.time()
            companies2 = entity_cache.get_companies()
            time2 = time.time() - start2
        
        print(f"\n📊 캐시 효과성:")
        print(f"  첫 번째 조회 (캐시 미스): {time1:.3f}초, DB 쿼리: {query_count}번")
        print(f"  두 번째 조회 (캐시 히트): {time2:.3f}초, 추가 쿼리: 0번")
        print(f"  성능 향상: {time1/time2:.1f}배")
        
        # 검증
        assert query_count == 1  # 첫 번째만 DB 쿼리
        assert companies1 == companies2  # 동일한 결과
        assert time2 < time1 / 10  # 캐시가 최소 10배 빨라야 함
    
    @pytest.mark.performance
    def test_entity_matching_accuracy(self):
        """엔티티 매칭 정확도 테스트"""
        # 테스트 데이터
        test_entities = [
            {'type': 'COMPANY', 'text': 'Samsung Electronics'},
            {'type': 'COMPANY', 'text': 'Samsung'},  # 약어
            {'type': 'COMPANY', 'text': '삼성전자'},  # 한글명
            {'type': 'PERSON', 'text': 'Lee Jae-yong'},
            {'type': 'PERSON', 'text': 'Jay Y. Lee'},  # 영문명
        ]
        
        mock_companies = [
            {'id': 'samsung-1', 'name': 'Samsung Electronics', 'aliases': ['삼성전자', 'Samsung']},
            {'id': 'lg-1', 'name': 'LG Electronics', 'aliases': ['엘지전자']}
        ]
        
        mock_persons = [
            {'id': 'lee-1', 'name': 'Lee Jae-yong', 'aliases': ['Jay Y. Lee', '이재용']},
            {'id': 'kim-1', 'name': 'Kim Dong-jin', 'aliases': ['김동진']}
        ]
        
        with patch.object(entity_cache, 'get_companies', return_value=mock_companies), \
             patch.object(entity_cache, 'get_persons', return_value=mock_persons):
            
            results = batch_matcher.match_entities_batch(test_entities)
        
        print(f"\n🎯 매칭 정확도:")
        for entity in test_entities:
            entity_key = f"{entity['type']}:{entity['text']}"
            matched_id = results.get(entity_key)
            print(f"  {entity['text']} → {matched_id}")
        
        # Samsung 관련 엔티티들이 모두 같은 ID로 매칭되어야 함
        samsung_matches = [
            results.get('COMPANY:Samsung Electronics'),
            results.get('COMPANY:Samsung'),
            results.get('COMPANY:삼성전자')
        ]
        
        # 모든 Samsung 관련 엔티티가 매칭되어야 함
        assert all(match_id for match_id in samsung_matches)
        # 모두 같은 ID여야 함
        assert len(set(samsung_matches)) == 1
        
        # Lee Jae-yong 관련 매칭
        lee_matches = [
            results.get('PERSON:Lee Jae-yong'),
            results.get('PERSON:Jay Y. Lee')
        ]
        
        assert all(match_id for match_id in lee_matches)
        assert len(set(lee_matches)) == 1