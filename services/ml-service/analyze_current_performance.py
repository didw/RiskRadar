#!/usr/bin/env python3
"""
현재 NER 모델 성능 분석
Current NER Model Performance Analysis
"""
import asyncio
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.processors.pipeline import NLPPipeline
from src.evaluation.f1_score_evaluator import F1ScoreEvaluator
from src.models.ner.koelectra_naver_ner import KoElectraNaverNERModel
from src.models.ner.mock_ner import MockNERModel


async def analyze_model_performance():
    """현재 모델 성능 분석"""
    print("🔍 Starting NER Model Performance Analysis...")
    
    # Initialize components
    evaluator = F1ScoreEvaluator()
    pipeline = NLPPipeline()
    
    # Test dataset path
    test_dataset_path = "tests/test_data/ner_test_dataset.json"
    
    # Test different models
    models_to_test = [
        ("Mock NER Model", MockNERModel()),
        ("KoELECTRA Naver NER", KoElectraNaverNERModel())
    ]
    
    results = {}
    
    for model_name, model in models_to_test:
        print(f"\n📊 Testing {model_name}...")
        
        # Create model function
        async def model_func(text):
            return await model.extract_entities(text)
        
        # Evaluate model
        try:
            evaluation = evaluator.evaluate_model(
                lambda text: asyncio.run(model_func(text)),
                test_dataset_path
            )
            results[model_name] = evaluation
            
            print(f"\n📈 {model_name} Results:")
            print(f"  F1-Score: {evaluation['overall']['f1']:.3f}")
            print(f"  Precision: {evaluation['overall']['precision']:.3f}")
            print(f"  Recall: {evaluation['overall']['recall']:.3f}")
            
        except Exception as e:
            print(f"❌ Error testing {model_name}: {e}")
            results[model_name] = None
    
    return results


def analyze_error_patterns(results):
    """오류 패턴 분석"""
    print("\n🔍 Error Pattern Analysis:")
    
    for model_name, evaluation in results.items():
        if evaluation is None:
            continue
            
        print(f"\n📊 {model_name} Error Analysis:")
        
        # Confusion matrix
        confusion = evaluation['confusion']
        total_expected = confusion['true_positives'] + confusion['false_negatives']
        total_predicted = confusion['true_positives'] + confusion['false_positives']
        
        print(f"  Total Expected Entities: {total_expected}")
        print(f"  Total Predicted Entities: {total_predicted}")
        print(f"  Missed Entities (FN): {confusion['false_negatives']}")
        print(f"  Wrong Entities (FP): {confusion['false_positives']}")
        
        # Entity type breakdown
        print(f"\n  📈 Performance by Entity Type:")
        for entity_type, metrics in evaluation['entity_types'].items():
            print(f"    {entity_type}:")
            print(f"      F1: {metrics['f1']:.3f}")
            print(f"      Precision: {metrics['precision']:.3f}")
            print(f"      Recall: {metrics['recall']:.3f}")


def suggest_improvements(results):
    """개선 방안 제안"""
    print("\n💡 Improvement Suggestions:")
    
    best_model = None
    best_f1 = 0
    
    for model_name, evaluation in results.items():
        if evaluation and evaluation['overall']['f1'] > best_f1:
            best_f1 = evaluation['overall']['f1']
            best_model = model_name
    
    print(f"\n🏆 Best Current Model: {best_model} (F1: {best_f1:.3f})")
    
    target_f1 = 0.80
    improvement_needed = target_f1 - best_f1
    
    print(f"\n🎯 Goal Analysis:")
    print(f"  Current Best F1: {best_f1:.3f}")
    print(f"  Target F1: {target_f1:.3f}")
    print(f"  Improvement Needed: {improvement_needed:.3f} ({improvement_needed/target_f1*100:.1f}%)")
    
    if improvement_needed > 0.2:
        print(f"\n🚀 Recommended Actions:")
        print(f"  1. Switch to KLUE-BERT NER model (Korean-specific)")
        print(f"  2. Add domain-specific fine-tuning")
        print(f"  3. Expand training dataset with financial news")
        print(f"  4. Implement ensemble methods")
        print(f"  5. Enhanced post-processing rules")
    else:
        print(f"\n✨ Minor improvements needed:")
        print(f"  1. Fine-tune existing model")
        print(f"  2. Improve post-processing")
        print(f"  3. Add more test cases")


async def main():
    """메인 실행"""
    print("="*60)
    print("NER Model Performance Analysis - Week 3")
    print("="*60)
    
    # Analyze current performance
    results = await analyze_model_performance()
    
    # Analyze error patterns
    analyze_error_patterns(results)
    
    # Suggest improvements
    suggest_improvements(results)
    
    print("\n" + "="*60)
    print("Analysis Complete! Next step: Implement KLUE-BERT")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())