"""데이터 로드 및 처리량 성능 테스트"""
import pytest
import time
import asyncio
import statistics
from typing import List, Dict, Any
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from src.kafka.handlers import GraphMessageHandler
from src.neo4j.driver import Neo4jDriver
from src.neo4j.transaction import TransactionManager

class TestLoadPerformance:
    """데이터 로드 및 처리량 테스트"""
    
    @pytest.fixture
    def driver(self):
        """Neo4j Driver fixture"""
        return Neo4jDriver()
    
    @pytest.fixture
    def handler(self):
        """Kafka 메시지 핸들러 fixture"""
        return GraphMessageHandler()
    
    @pytest.fixture
    def tm(self):
        """TransactionManager fixture"""
        return TransactionManager()
    
    def generate_test_messages(self, count: int) -> List[Dict[str, Any]]:
        """테스트 메시지 생성"""
        messages = []
        base_time = datetime.now()
        
        for i in range(count):
            messages.append({
                "id": f"perf-news-{i}",
                "title": f"Performance Test News {i}",
                "content": f"This is test content for performance testing message {i}",
                "url": f"https://example.com/news/{i}",
                "published_at": (base_time - timedelta(hours=i)).isoformat(),
                "source": f"TestSource{i % 5}",
                "entities": [
                    {
                        "text": f"Test Company {i % 100}",
                        "type": "COMPANY",
                        "confidence": 0.9,
                        "start_pos": 0,
                        "end_pos": 20
                    },
                    {
                        "text": f"Test Person {i % 50}",
                        "type": "PERSON", 
                        "confidence": 0.85,
                        "start_pos": 30,
                        "end_pos": 50
                    }
                ],
                "sentiment": (i % 20) / 10 - 1,  # -1 to 1
                "risk_score": (i % 10) + 1,  # 1 to 10
                "risk_indicators": ["test", "performance"],
                "topics": ["technology", "business"]
            })
        
        return messages
    
    def cleanup_test_data(self, driver):
        """테스트 데이터 정리"""
        driver.execute_query("MATCH (n:NewsArticle) WHERE n.id STARTS WITH 'perf-news-' DETACH DELETE n")
        driver.execute_query("MATCH (n:Company) WHERE n.name STARTS WITH 'Test Company' DETACH DELETE n")
        driver.execute_query("MATCH (n:Person) WHERE n.name STARTS WITH 'Test Person' DETACH DELETE n")
        driver.execute_query("MATCH (n:RiskEvent) WHERE n.id STARTS WITH 'risk-perf-news-' DETACH DELETE n")
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_message_processing_throughput(self, handler, driver):
        """메시지 처리 처리량 테스트"""
        self.cleanup_test_data(driver)
        
        # 100개 메시지 생성
        messages = self.generate_test_messages(100)
        
        # 순차 처리
        start_time = time.time()
        for msg in messages:
            await handler.handle_enriched_news(msg)
        sequential_time = time.time() - start_time
        
        print(f"\n순차 메시지 처리 (100개):")
        print(f"  총 시간: {sequential_time:.2f}초")
        print(f"  처리량: {100/sequential_time:.2f} messages/sec")
        print(f"  평균 처리 시간: {sequential_time/100:.4f}초/message")
        
        # 결과 확인
        news_count = driver.execute_query(
            "MATCH (n:NewsArticle) WHERE n.id STARTS WITH 'perf-news-' RETURN count(n) as count"
        )[0]['count']
        
        assert news_count == 100
        assert sequential_time < 30  # 100개 메시지 30초 이내
        
        self.cleanup_test_data(driver)
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_message_processing(self, handler, driver):
        """동시 메시지 처리 성능"""
        self.cleanup_test_data(driver)
        
        messages = self.generate_test_messages(50)
        
        # 동시 처리 (5개씩)
        async def process_batch(batch):
            tasks = [handler.handle_enriched_news(msg) for msg in batch]
            await asyncio.gather(*tasks)
        
        start_time = time.time()
        for i in range(0, len(messages), 5):
            batch = messages[i:i+5]
            await process_batch(batch)
        concurrent_time = time.time() - start_time
        
        print(f"\n동시 메시지 처리 (50개, 5개씩 배치):")
        print(f"  총 시간: {concurrent_time:.2f}초")
        print(f"  처리량: {50/concurrent_time:.2f} messages/sec")
        
        # 성능 향상 확인
        assert concurrent_time < 15  # 50개 메시지 15초 이내
        
        self.cleanup_test_data(driver)
    
    @pytest.mark.performance
    def test_bulk_node_creation(self, tm, driver):
        """대량 노드 생성 성능"""
        self.cleanup_test_data(driver)
        
        # 1000개 회사 노드 준비
        companies = []
        for i in range(1000):
            companies.append({
                "id": f"bulk-company-{i}",
                "name": f"Bulk Test Company {i}",
                "sector": f"Sector{i % 10}",
                "risk_score": (i % 10) + 1
            })
        
        # 배치 크기별 성능 측정
        batch_sizes = [10, 50, 100, 200]
        results = {}
        
        for batch_size in batch_sizes:
            # 데이터 정리
            driver.execute_query("MATCH (n:Company) WHERE n.id STARTS WITH 'bulk-company-' DELETE n")
            
            # 배치 작업 준비
            operations = []
            for company in companies:
                operations.append((
                    "CREATE (n:Company) SET n = $props",
                    {"props": company}
                ))
            
            # 실행 및 시간 측정
            start = time.time()
            tm.batch_write(operations, batch_size=batch_size)
            elapsed = time.time() - start
            
            results[batch_size] = elapsed
            
            print(f"\n배치 크기 {batch_size}:")
            print(f"  시간: {elapsed:.2f}초")
            print(f"  처리량: {1000/elapsed:.2f} nodes/sec")
        
        # 최적 배치 크기 확인
        optimal_batch = min(results, key=results.get)
        print(f"\n최적 배치 크기: {optimal_batch}")
        
        # 성능 기준: 1000개 노드 5초 이내
        assert min(results.values()) < 5
        
        self.cleanup_test_data(driver)
    
    @pytest.mark.performance
    def test_relationship_creation_performance(self, driver):
        """관계 생성 성능 테스트"""
        self.cleanup_test_data(driver)
        
        # 노드 생성
        companies = []
        for i in range(100):
            companies.append({
                "id": f"rel-company-{i}",
                "name": f"Relationship Test Company {i}",
                "sector": f"Sector{i % 5}"
            })
        
        driver.execute_query("""
            UNWIND $companies as company
            CREATE (c:Company)
            SET c = company
        """, companies=companies)
        
        # 관계 생성 성능 측정
        start = time.time()
        
        # 같은 섹터 내 회사들끼리 관계 생성
        driver.execute_query("""
            MATCH (c1:Company), (c2:Company)
            WHERE c1.sector = c2.sector 
              AND c1.id < c2.id
              AND c1.id STARTS WITH 'rel-company-'
              AND c2.id STARTS WITH 'rel-company-'
            WITH c1, c2 LIMIT 500
            CREATE (c1)-[:COMPETES_WITH {created_at: datetime()}]->(c2)
        """)
        
        rel_creation_time = time.time() - start
        
        # 생성된 관계 수 확인
        rel_count = driver.execute_query("""
            MATCH (c1:Company)-[r:COMPETES_WITH]->(c2:Company)
            WHERE c1.id STARTS WITH 'rel-company-'
            RETURN count(r) as count
        """)[0]['count']
        
        print(f"\n관계 생성 성능:")
        print(f"  생성된 관계 수: {rel_count}")
        print(f"  소요 시간: {rel_creation_time:.2f}초")
        print(f"  처리량: {rel_count/rel_creation_time:.2f} relationships/sec")
        
        # 성능 기준
        assert rel_creation_time < 2  # 2초 이내
        
        # 정리
        driver.execute_query("MATCH (n:Company) WHERE n.id STARTS WITH 'rel-company-' DETACH DELETE n")
    
    @pytest.mark.performance
    def test_memory_usage_large_result(self, driver):
        """대용량 결과 메모리 사용 테스트"""
        self.cleanup_test_data(driver)
        
        # 대량 데이터 생성
        print("\n대용량 데이터 생성 중...")
        for i in range(0, 5000, 100):
            batch = []
            for j in range(100):
                idx = i + j
                batch.append({
                    "id": f"mem-test-{idx}",
                    "title": f"Memory Test Article {idx}",
                    "content": "x" * 1000,  # 1KB content
                    "published_at": datetime.now().isoformat()
                })
            
            driver.execute_query("""
                UNWIND $articles as article
                CREATE (n:NewsArticle)
                SET n = article
            """, articles=batch)
        
        # 대용량 결과 쿼리
        queries = [
            ("전체 조회", "MATCH (n:NewsArticle) WHERE n.id STARTS WITH 'mem-test-' RETURN n LIMIT 1000"),
            ("집계", "MATCH (n:NewsArticle) WHERE n.id STARTS WITH 'mem-test-' RETURN count(n) as count"),
            ("프로젝션", "MATCH (n:NewsArticle) WHERE n.id STARTS WITH 'mem-test-' RETURN n.id, n.title LIMIT 2000")
        ]
        
        for query_name, query in queries:
            start = time.time()
            result = driver.execute_query(query)
            elapsed = time.time() - start
            
            print(f"\n{query_name}:")
            print(f"  결과 수: {len(result)}")
            print(f"  소요 시간: {elapsed:.2f}초")
        
        # 정리
        driver.execute_query("MATCH (n:NewsArticle) WHERE n.id STARTS WITH 'mem-test-' DETACH DELETE n")
    
    @pytest.mark.performance
    def test_transaction_isolation(self, tm, driver):
        """트랜잭션 격리 수준 테스트"""
        self.cleanup_test_data(driver)
        
        # 동시 트랜잭션 테스트
        def transaction1():
            with tm.transaction() as tx:
                tx.run("CREATE (n:Company {id: 'tx-test-1', value: 1})")
                time.sleep(0.1)  # 의도적 지연
                tx.run("MATCH (n:Company {id: 'tx-test-1'}) SET n.value = 2")
        
        def transaction2():
            with tm.transaction() as tx:
                tx.run("CREATE (n:Company {id: 'tx-test-2', value: 1})")
                time.sleep(0.05)
                tx.run("MATCH (n:Company {id: 'tx-test-2'}) SET n.value = 3")
        
        # 동시 실행
        with ThreadPoolExecutor(max_workers=2) as executor:
            start = time.time()
            future1 = executor.submit(transaction1)
            future2 = executor.submit(transaction2)
            future1.result()
            future2.result()
            elapsed = time.time() - start
        
        # 결과 확인
        result1 = driver.execute_query("MATCH (n:Company {id: 'tx-test-1'}) RETURN n.value as value")
        result2 = driver.execute_query("MATCH (n:Company {id: 'tx-test-2'}) RETURN n.value as value")
        
        print(f"\n트랜잭션 격리 테스트:")
        print(f"  동시 트랜잭션 실행 시간: {elapsed:.2f}초")
        print(f"  트랜잭션1 결과: {result1[0]['value'] if result1 else 'None'}")
        print(f"  트랜잭션2 결과: {result2[0]['value'] if result2 else 'None'}")
        
        assert result1[0]['value'] == 2
        assert result2[0]['value'] == 3
        
        # 정리
        driver.execute_query("MATCH (n:Company) WHERE n.id STARTS WITH 'tx-test-' DELETE n")