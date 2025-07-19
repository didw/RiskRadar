"""
F1-Score 평가 모듈
F1-Score Evaluation Module for NER
"""
import json
import logging
from typing import List, Dict, Any, Tuple, Set
from dataclasses import dataclass
from collections import defaultdict
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class EntityMatch:
    """엔티티 매칭 결과"""
    text: str
    type: str
    start: int
    end: int
    
    def __hash__(self):
        return hash((self.text, self.type, self.start, self.end))
    
    def __eq__(self, other):
        if not isinstance(other, EntityMatch):
            return False
        return (self.text == other.text and 
                self.type == other.type and
                self.start == other.start and 
                self.end == other.end)


class F1ScoreEvaluator:
    """NER F1-Score 평가기"""
    
    def __init__(self):
        self.results = []
        self.entity_types = ["COMPANY", "PERSON", "EVENT"]
        
    def evaluate_single(self, predicted: List[Dict], expected: List[Dict]) -> Dict[str, float]:
        """
        단일 케이스 평가
        
        Args:
            predicted: 예측된 엔티티 리스트
            expected: 정답 엔티티 리스트
            
        Returns:
            평가 메트릭 (precision, recall, f1)
        """
        # Convert to EntityMatch sets
        pred_set = {
            EntityMatch(
                text=e.get('text', ''),
                type=e.get('type', ''),
                start=e.get('start', 0),
                end=e.get('end', 0)
            ) for e in predicted
        }
        
        expected_set = {
            EntityMatch(
                text=e.get('text', ''),
                type=e.get('type', ''),
                start=e.get('start', 0),
                end=e.get('end', 0)
            ) for e in expected
        }
        
        # Calculate metrics
        true_positives = len(pred_set & expected_set)
        false_positives = len(pred_set - expected_set)
        false_negatives = len(expected_set - pred_set)
        
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "true_positives": true_positives,
            "false_positives": false_positives,
            "false_negatives": false_negatives
        }
    
    def evaluate_batch(self, test_results: List[Dict]) -> Dict[str, Any]:
        """
        배치 평가
        
        Args:
            test_results: 테스트 결과 리스트 (predicted와 expected 포함)
            
        Returns:
            전체 평가 결과
        """
        all_metrics = []
        entity_type_metrics = defaultdict(list)
        
        for result in test_results:
            predicted = result.get('predicted', [])
            expected = result.get('expected', [])
            
            # Overall metrics
            metrics = self.evaluate_single(predicted, expected)
            all_metrics.append(metrics)
            
            # Per entity type metrics
            for entity_type in self.entity_types:
                pred_filtered = [e for e in predicted if e.get('type') == entity_type]
                expected_filtered = [e for e in expected if e.get('type') == entity_type]
                
                type_metrics = self.evaluate_single(pred_filtered, expected_filtered)
                entity_type_metrics[entity_type].append(type_metrics)
        
        # Calculate averages
        avg_precision = np.mean([m['precision'] for m in all_metrics])
        avg_recall = np.mean([m['recall'] for m in all_metrics])
        avg_f1 = np.mean([m['f1'] for m in all_metrics])
        
        # Calculate per entity type averages
        entity_type_averages = {}
        for entity_type, metrics_list in entity_type_metrics.items():
            if metrics_list:
                entity_type_averages[entity_type] = {
                    "precision": np.mean([m['precision'] for m in metrics_list]),
                    "recall": np.mean([m['recall'] for m in metrics_list]),
                    "f1": np.mean([m['f1'] for m in metrics_list]),
                    "support": len(metrics_list)
                }
        
        # Calculate total counts
        total_tp = sum(m['true_positives'] for m in all_metrics)
        total_fp = sum(m['false_positives'] for m in all_metrics)
        total_fn = sum(m['false_negatives'] for m in all_metrics)
        
        return {
            "overall": {
                "precision": avg_precision,
                "recall": avg_recall,
                "f1": avg_f1,
                "support": len(test_results)
            },
            "entity_types": entity_type_averages,
            "confusion": {
                "true_positives": total_tp,
                "false_positives": total_fp,
                "false_negatives": total_fn
            },
            "individual_results": all_metrics
        }
    
    def load_test_dataset(self, dataset_path: str) -> List[Dict]:
        """테스트 데이터셋 로드"""
        with open(dataset_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('test_cases', [])
    
    def evaluate_model(self, model_func, test_dataset_path: str) -> Dict[str, Any]:
        """
        모델 평가 실행
        
        Args:
            model_func: 엔티티 추출 함수 (text -> List[Entity])
            test_dataset_path: 테스트 데이터셋 경로
            
        Returns:
            평가 결과
        """
        # Load test dataset
        test_cases = self.load_test_dataset(test_dataset_path)
        
        # Run predictions
        test_results = []
        for test_case in test_cases:
            text = test_case['text']
            expected = test_case['expected_entities']
            
            # Get predictions
            try:
                predicted_entities = model_func(text)
                # Convert Entity objects to dicts if needed
                if predicted_entities and hasattr(predicted_entities[0], '__dict__'):
                    predicted = [
                        {
                            'text': e.text,
                            'type': e.type,
                            'start': e.start,
                            'end': e.end
                        } for e in predicted_entities
                    ]
                else:
                    predicted = predicted_entities
            except Exception as e:
                logger.error(f"Error predicting for text '{text}': {e}")
                predicted = []
            
            test_results.append({
                'id': test_case['id'],
                'text': text,
                'predicted': predicted,
                'expected': expected
            })
        
        # Evaluate
        evaluation = self.evaluate_batch(test_results)
        evaluation['test_cases'] = len(test_cases)
        
        return evaluation
    
    def print_evaluation_report(self, evaluation: Dict[str, Any]):
        """평가 결과 출력"""
        print("\n" + "="*60)
        print("NER F1-Score Evaluation Report")
        print("="*60)
        
        # Overall metrics
        overall = evaluation['overall']
        print(f"\n📊 Overall Performance:")
        print(f"  Precision: {overall['precision']:.3f}")
        print(f"  Recall:    {overall['recall']:.3f}")
        print(f"  F1-Score:  {overall['f1']:.3f}")
        print(f"  Support:   {overall['support']} test cases")
        
        # Entity type breakdown
        print(f"\n📈 Performance by Entity Type:")
        for entity_type, metrics in evaluation['entity_types'].items():
            print(f"\n  {entity_type}:")
            print(f"    Precision: {metrics['precision']:.3f}")
            print(f"    Recall:    {metrics['recall']:.3f}")
            print(f"    F1-Score:  {metrics['f1']:.3f}")
        
        # Confusion stats
        confusion = evaluation['confusion']
        print(f"\n🎯 Confusion Statistics:")
        print(f"  True Positives:  {confusion['true_positives']}")
        print(f"  False Positives: {confusion['false_positives']}")
        print(f"  False Negatives: {confusion['false_negatives']}")
        
        # Goal achievement
        f1_goal = 0.80
        achieved = overall['f1'] >= f1_goal
        print(f"\n🎯 Goal Achievement:")
        print(f"  Target F1-Score: {f1_goal:.2f}")
        print(f"  Achieved:        {overall['f1']:.3f} {'✅' if achieved else '❌'}")
        
        print("="*60)