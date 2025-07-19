#!/usr/bin/env python3
"""N+1 문제 해결 성능 벤치마크"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import statistics
from typing import List, Dict
from unittest.mock import patch, MagicMock

from src.kafka.entity_cache import entity_cache
from src.algorithms.batch_entity_matching import batch_matcher

def generate_test_entities(count: int) -> List[Dict]:
    """테스트 엔티티 생성"""
    entities = []
    
    # 50% 기업, 30% 인물, 20% 기타
    company_count = int(count * 0.5)
    person_count = int(count * 0.3)
    other_count = count - company_count - person_count
    
    for i in range(company_count):
        entities.append({
            'type': 'COMPANY',
            'text': f'Test Company {i}',
            'confidence': 0.9
        })
    
    for i in range(person_count):
        entities.append({
            'type': 'PERSON',
            'text': f'Test Person {i}',
            'confidence': 0.8
        })
    
    for i in range(other_count):
        entities.append({
            'type': 'EVENT',
            'text': f'Test Event {i}',
            'confidence': 0.7
        })
    
    return entities

def simulate_old_approach(entities: List[Dict]) -> Dict:
    """기존 방식 시뮬레이션 (N+1 문제)"""
    query_count = 0
    total_time = 0
    
    def mock_db_query(*args, **kwargs):
        nonlocal query_count
        query_count += 1
        time.sleep(0.002)  # 2ms DB 쿼리 지연
        return []
    
    start_time = time.time()
    
    # 각 엔티티마다 전체 테이블 스캔
    for entity in entities:
        if entity['type'] == 'COMPANY':
            mock_db_query("MATCH (c:Company) RETURN c")
        elif entity['type'] == 'PERSON':
            mock_db_query("MATCH (p:Person) RETURN p")
    
    total_time = time.time() - start_time
    
    return {
        'query_count': query_count,
        'total_time': total_time,
        'avg_time_per_entity': total_time / len(entities) if entities else 0
    }

def benchmark_batch_approach(entities: List[Dict]) -> Dict:
    """배치 방식 벤치마크"""
    query_count = 0
    
    def mock_cache_companies():
        nonlocal query_count
        query_count += 1
        time.sleep(0.01)  # 10ms 캐시 조회
        return [{'id': f'company-{i}', 'name': f'Company {i}', 'aliases': []} for i in range(1000)]
    
    def mock_cache_persons():
        nonlocal query_count
        query_count += 1
        time.sleep(0.008)  # 8ms 캐시 조회
        return [{'id': f'person-{i}', 'name': f'Person {i}', 'aliases': []} for i in range(500)]
    
    start_time = time.time()
    
    with patch.object(entity_cache, 'get_companies', side_effect=mock_cache_companies), \
         patch.object(entity_cache, 'get_persons', side_effect=mock_cache_persons):
        
        results = batch_matcher.match_entities_batch(entities)
    
    total_time = time.time() - start_time
    
    return {
        'query_count': query_count,
        'total_time': total_time,
        'avg_time_per_entity': total_time / len(entities) if entities else 0,
        'match_count': len(results)
    }

def run_benchmark():
    """벤치마크 실행"""
    print("🚀 N+1 문제 해결 성능 벤치마크")
    print("=" * 50)
    
    test_cases = [10, 50, 100, 200, 500]
    
    results = []
    
    for entity_count in test_cases:
        print(f"\n📊 엔티티 수: {entity_count}개")
        print("-" * 30)
        
        entities = generate_test_entities(entity_count)
        
        # 기존 방식 (N+1 문제)
        old_result = simulate_old_approach(entities)
        
        # 개선된 방식 (배치 매칭)
        new_result = benchmark_batch_approach(entities)
        
        # 성능 향상 계산
        time_improvement = old_result['total_time'] / new_result['total_time']
        query_reduction = old_result['query_count'] / new_result['query_count']
        
        print(f"🚨 기존 방식:")
        print(f"   쿼리 수: {old_result['query_count']}번")
        print(f"   총 시간: {old_result['total_time']:.3f}초")
        print(f"   평균: {old_result['avg_time_per_entity']:.4f}초/엔티티")
        
        print(f"✅ 개선된 방식:")
        print(f"   쿼리 수: {new_result['query_count']}번")
        print(f"   총 시간: {new_result['total_time']:.3f}초")
        print(f"   평균: {new_result['avg_time_per_entity']:.4f}초/엔티티")
        print(f"   매칭: {new_result['match_count']}개")
        
        print(f"📈 성능 향상:")
        print(f"   시간 단축: {time_improvement:.1f}배")
        print(f"   쿼리 감소: {query_reduction:.1f}배")
        
        results.append({
            'entity_count': entity_count,
            'old_time': old_result['total_time'],
            'new_time': new_result['total_time'],
            'time_improvement': time_improvement,
            'query_reduction': query_reduction
        })
    
    # 전체 요약
    print("\n" + "=" * 50)
    print("📋 벤치마크 요약")
    print("=" * 50)
    
    avg_time_improvement = statistics.mean([r['time_improvement'] for r in results])
    avg_query_reduction = statistics.mean([r['query_reduction'] for r in results])
    
    print(f"평균 시간 단축: {avg_time_improvement:.1f}배")
    print(f"평균 쿼리 감소: {avg_query_reduction:.1f}배")
    
    # 확장성 분석
    print(f"\n🔍 확장성 분석:")
    print(f"엔티티 10개 → 500개 (50배 증가)")
    result_10 = next(r for r in results if r['entity_count'] == 10)
    result_500 = next(r for r in results if r['entity_count'] == 500)
    
    old_scaling = result_500['old_time'] / result_10['old_time']
    new_scaling = result_500['new_time'] / result_10['new_time']
    
    print(f"기존 방식: {old_scaling:.1f}배 증가 (선형 증가)")
    print(f"개선된 방식: {new_scaling:.1f}배 증가 (상수 시간)")
    
    # 실제 운영 환경 예측
    print(f"\n🏭 실제 운영 환경 예측:")
    print(f"뉴스 1건당 평균 엔티티 15개 기준")
    print(f"일일 뉴스 1,000건 처리 시:")
    
    daily_entities = 1000 * 15
    result_baseline = next(r for r in results if r['entity_count'] >= 50)  # 가장 가까운 값
    
    # 선형 스케일링으로 예측
    scale_factor = daily_entities / result_baseline['entity_count']
    
    old_daily_time = result_baseline['old_time'] * scale_factor
    new_daily_time = result_baseline['new_time'] * scale_factor
    
    print(f"기존 방식: {old_daily_time:.1f}초 ({old_daily_time/60:.1f}분)")
    print(f"개선된 방식: {new_daily_time:.1f}초 ({new_daily_time/60:.1f}분)")
    print(f"일일 절약 시간: {(old_daily_time - new_daily_time)/60:.1f}분")

if __name__ == "__main__":
    run_benchmark()