#!/usr/bin/env python3
"""
KLUE-BERT NER 모델 테스트
Test KLUE-BERT NER Model
"""
import asyncio
import sys
import os
import json

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.models.ner.klue_bert_ner import KLUEBERTNERModel
from src.evaluation.f1_score_evaluator import F1ScoreEvaluator


async def test_klue_bert_model():
    """KLUE-BERT 모델 테스트"""
    print("🧪 Testing KLUE-BERT NER Model...")
    
    # 모델 초기화
    model = KLUEBERTNERModel()
    
    # 모델 정보 출력
    model_info = model.get_model_info()
    print(f"\n📊 Model Information:")
    for key, value in model_info.items():
        print(f"  {key}: {value}")
    
    # 간단한 테스트
    test_texts = [
        "삼성전자가 새로운 반도체 공장을 건설한다고 이재용 회장이 발표했습니다.",
        "현대자동차 정의선 회장은 전기차 시장 진출을 선언했다.",
        "네이버 최수연 대표가 AI 플랫폼 고도화 계획을 발표했다.",
        "KB금융 윤종규 회장과 신한금융 진옥동 회장이 핀테크 협력을 논의했다."
    ]
    
    print(f"\n🔍 Individual Test Results:")
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n  Test {i}: '{text}'")
        
        try:
            entities = await model.extract_entities(text)
            print(f"    Found {len(entities)} entities:")
            
            for entity in entities:
                print(f"      - {entity.text} ({entity.type}) [confidence: {entity.confidence:.2f}]")
                
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    return model


async def evaluate_klue_bert_performance():
    """KLUE-BERT 성능 평가"""
    print(f"\n📈 KLUE-BERT Performance Evaluation...")
    
    # 모델 초기화
    model = KLUEBERTNERModel()
    
    # 평가기 초기화
    evaluator = F1ScoreEvaluator()
    
    # 테스트 데이터셋 경로
    test_dataset_path = "tests/test_data/ner_test_dataset.json"
    
    if not os.path.exists(test_dataset_path):
        print(f"❌ Test dataset not found: {test_dataset_path}")
        return None
    
    try:
        # 모델 평가 실행
        async def model_func(text):
            return await model.extract_entities(text)
        
        evaluation = evaluator.evaluate_model(
            lambda text: asyncio.run(model_func(text)),
            test_dataset_path
        )
        
        # 결과 출력
        evaluator.print_evaluation_report(evaluation)
        
        return evaluation
        
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        return None


def compare_with_previous_models():
    """이전 모델들과 성능 비교"""
    print(f"\n📊 Performance Comparison:")
    
    previous_results = {
        "Mock NER Model": 32.3,
        "Multilingual NER (API)": 37.8,
        "KoELECTRA Naver NER": 56.3
    }
    
    print(f"  Previous Models:")
    for model_name, f1_score in previous_results.items():
        print(f"    {model_name}: {f1_score}% F1")
    
    print(f"\n  🎯 Target F1-Score: 80.0%")
    print(f"  📈 Expected improvement with KLUE-BERT: +15-20%")


async def test_model_features():
    """모델 기능 테스트"""
    print(f"\n🔧 Testing Model Features...")
    
    model = KLUEBERTNERModel()
    
    # 캐시 테스트
    test_text = "삼성전자 이재용 회장이 새로운 전략을 발표했다."
    
    print(f"  Testing caching...")
    # 첫 번째 호출 (캐시 미스)
    start_time = asyncio.get_event_loop().time()
    entities1 = await model.extract_entities(test_text)
    time1 = (asyncio.get_event_loop().time() - start_time) * 1000
    
    # 두 번째 호출 (캐시 히트)
    start_time = asyncio.get_event_loop().time()
    entities2 = await model.extract_entities(test_text)
    time2 = (asyncio.get_event_loop().time() - start_time) * 1000
    
    print(f"    First call: {time1:.2f}ms ({len(entities1)} entities)")
    print(f"    Second call: {time2:.2f}ms ({len(entities2)} entities)")
    print(f"    Speed improvement: {time1/time2:.1f}x")
    
    # 캐시 통계
    cache_stats = model.get_cache_stats()
    print(f"  Cache statistics:")
    for key, value in cache_stats.items():
        print(f"    {key}: {value}")


async def main():
    """메인 실행"""
    print("="*60)
    print("KLUE-BERT NER Model Testing - Week 3")
    print("="*60)
    
    # 모델 기본 테스트
    model = await test_klue_bert_model()
    
    # 성능 평가
    evaluation = await evaluate_klue_bert_performance()
    
    # 이전 모델과 비교
    compare_with_previous_models()
    
    # 모델 기능 테스트
    await test_model_features()
    
    print("\n" + "="*60)
    
    if evaluation:
        current_f1 = evaluation['overall']['f1'] * 100
        target_f1 = 80.0
        
        if current_f1 >= target_f1:
            print(f"🎉 SUCCESS: Target F1-Score achieved! ({current_f1:.1f}% >= {target_f1}%)")
        else:
            improvement_needed = target_f1 - current_f1
            print(f"📈 PROGRESS: F1-Score improved, {improvement_needed:.1f}% more needed")
            print(f"   Current: {current_f1:.1f}%")
            print(f"   Target: {target_f1}%")
    else:
        print("⚠️  Evaluation incomplete - check model implementation")
    
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())