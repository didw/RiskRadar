"""
ML Service 통합 테스트
Full Pipeline Integration Tests
"""
import pytest
import asyncio
import json
import time
from typing import Dict, Any
from fastapi.testclient import TestClient

# Test configuration
TEST_ARTICLES = [
    {
        "id": "test-001",
        "text": "삼성전자가 새로운 반도체 공장을 건설한다고 이재용 회장이 발표했습니다."
    },
    {
        "id": "test-002", 
        "text": "현대자동차 정의선 회장은 전기차 시장 진출을 선언했다."
    },
    {
        "id": "test-003",
        "text": "SK하이닉스가 메모리 반도체 증산을 위해 대규모 투자를 진행합니다."
    }
]


class TestFullPipeline:
    """통합 파이프라인 테스트"""
    
    @pytest.fixture
    def client(self):
        """FastAPI 테스트 클라이언트"""
        from src.main import app
        return TestClient(app)
    
    def test_health_check(self, client):
        """헬스체크 테스트"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["model_loaded"] is True
        assert "version" in data
    
    def test_single_process(self, client):
        """단일 문서 처리 테스트"""
        # Process single article
        response = client.post(
            "/api/v1/process",
            json={"text": TEST_ARTICLES[0]["text"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert data["success"] is True
        assert "result" in data
        assert "entities" in data["result"]
        assert "sentiment" in data["result"]
        assert "keywords" in data["result"]
        assert "processing_time_ms" in data["result"]
        
        # Verify entities
        entities = data["result"]["entities"]
        assert isinstance(entities, list)
        
        # Check for expected entities
        entity_texts = [e["text"] for e in entities]
        assert any("삼성" in text for text in entity_texts)
    
    def test_batch_process(self, client):
        """배치 처리 테스트"""
        # Prepare batch request
        texts = [article["text"] for article in TEST_ARTICLES]
        
        # Process batch
        response = client.post(
            "/api/v1/batch",
            json={"texts": texts}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response
        assert data["success"] is True
        assert "results" in data
        assert len(data["results"]) == len(texts)
        assert "total_processing_time_ms" in data
        
        # Verify each result
        for result in data["results"]:
            assert "entities" in result
            assert "sentiment" in result
            assert "keywords" in result
    
    def test_performance_requirements(self, client):
        """성능 요구사항 테스트"""
        # Test processing time < 100ms per article
        texts = [article["text"] for article in TEST_ARTICLES[:10]]
        
        start_time = time.time()
        response = client.post(
            "/api/v1/batch",
            json={"texts": texts}
        )
        end_time = time.time()
        
        assert response.status_code == 200
        data = response.json()
        
        # Check processing time
        total_time_ms = (end_time - start_time) * 1000
        avg_time_per_doc = total_time_ms / len(texts)
        
        print(f"\nPerformance Test Results:")
        print(f"  Total time: {total_time_ms:.2f}ms")
        print(f"  Avg per doc: {avg_time_per_doc:.2f}ms")
        print(f"  Throughput: {len(texts) / (total_time_ms / 1000):.2f} docs/sec")
        
        # Verify performance requirements
        assert avg_time_per_doc < 100  # < 100ms per article
        
    def test_cache_effectiveness(self, client):
        """캐시 효과 테스트"""
        text = TEST_ARTICLES[0]["text"]
        
        # First request (cache miss)
        response1 = client.post(
            "/api/v1/process",
            json={"text": text}
        )
        assert response1.status_code == 200
        time1 = response1.json()["result"]["processing_time_ms"]
        
        # Second request (cache hit)
        response2 = client.post(
            "/api/v1/process",
            json={"text": text}
        )
        assert response2.status_code == 200
        time2 = response2.json()["result"]["processing_time_ms"]
        
        # Cache should be faster
        print(f"\nCache Test Results:")
        print(f"  First request: {time1:.2f}ms")
        print(f"  Second request: {time2:.2f}ms")
        print(f"  Speedup: {time1/time2:.2f}x")
        
        assert time2 < time1  # Cache hit should be faster
    
    def test_knowledge_base_search(self, client):
        """지식 베이스 검색 테스트"""
        # Search for company
        response = client.get(
            "/api/v1/knowledge-base/search",
            params={"query": "삼성", "entity_type": "COMPANY"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "results" in data
        assert len(data["results"]) > 0
        
        # Verify result structure
        for result in data["results"]:
            assert "canonical_name" in result
            assert "entity_type" in result
            assert "aliases" in result
    
    def test_batch_configuration(self, client):
        """배치 설정 테스트"""
        # Configure batch processor
        response = client.post(
            "/api/v1/batch/configure",
            params={"batch_size": 5, "max_workers": 2}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["batch_size"] == 5
        assert data["max_workers"] == 2
        
        # Get batch stats
        response = client.get("/api/v1/batch/stats")
        assert response.status_code == 200
        
    def test_cache_management(self, client):
        """캐시 관리 테스트"""
        # Get cache stats
        response = client.get("/api/v1/cache/stats")
        assert response.status_code == 200
        
        initial_stats = response.json()
        
        # Process some texts
        for article in TEST_ARTICLES[:3]:
            client.post(
                "/api/v1/process",
                json={"text": article["text"]}
            )
        
        # Check updated stats
        response = client.get("/api/v1/cache/stats")
        updated_stats = response.json()
        
        assert updated_stats["cache_size"] >= initial_stats["cache_size"]
        
        # Clear cache
        response = client.post("/api/v1/cache/clear")
        assert response.status_code == 200
        
        # Verify cache cleared
        response = client.get("/api/v1/cache/stats")
        cleared_stats = response.json()
        assert cleared_stats["cache_size"] == 0
    
    def test_error_handling(self, client):
        """에러 처리 테스트"""
        # Test with empty text
        response = client.post(
            "/api/v1/process",
            json={"text": ""}
        )
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # Test with very long text
        long_text = "테스트 " * 1000
        response = client.post(
            "/api/v1/process",
            json={"text": long_text}
        )
        assert response.status_code == 200
        
        # Test batch with mixed valid/invalid
        response = client.post(
            "/api/v1/batch",
            json={"texts": ["유효한 텍스트", "", "또 다른 텍스트"]}
        )
        assert response.status_code == 200
        assert len(response.json()["results"]) == 3


@pytest.mark.asyncio
class TestAsyncIntegration:
    """비동기 통합 테스트"""
    
    async def test_concurrent_requests(self):
        """동시 요청 처리 테스트"""
        from src.processors import NLPPipeline, ProcessingConfig
        
        # Create pipeline
        config = ProcessingConfig()
        pipeline = NLPPipeline(config)
        
        # Process multiple texts concurrently
        tasks = []
        for article in TEST_ARTICLES:
            task = pipeline.process(article["text"])
            tasks.append(task)
        
        # Wait for all tasks
        results = await asyncio.gather(*tasks)
        
        # Verify results
        assert len(results) == len(TEST_ARTICLES)
        for result in results:
            assert result.entities is not None
            assert result.sentiment is not None
            assert result.processing_time_ms > 0
    
    async def test_kafka_integration(self):
        """Kafka 통합 테스트 (Mock)"""
        from src.kafka import MockKafkaConsumer, MockKafkaProducer
        from src.processors import NLPPipeline, ProcessingConfig
        
        # Setup
        consumer = MockKafkaConsumer()
        producer = MockKafkaProducer()
        config = ProcessingConfig()
        pipeline = NLPPipeline(config)
        
        # Process messages
        processed_count = 0
        async for message in consumer.consume():
            # Process
            result = await pipeline.process(message.content)
            
            # Produce enriched message
            enriched = {
                "original": message.dict(),
                "nlp_result": result.dict()
            }
            
            await producer.send_enriched(json.dumps(enriched))
            processed_count += 1
            
            if processed_count >= 3:
                break
        
        assert processed_count >= 3
        assert len(producer.produced_messages) >= 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])