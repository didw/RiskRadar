"""그래프 쿼리 성능 테스트"""
import pytest
import time
import statistics
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.neo4j.driver import Neo4jDriver
from src.neo4j.transaction import TransactionManager

class TestQueryPerformance:
    """쿼리 성능 테스트"""
    
    @pytest.fixture
    def driver(self):
        """Neo4j Driver fixture"""
        return Neo4jDriver()
    
    @pytest.fixture
    def tm(self):
        """TransactionManager fixture"""
        return TransactionManager()
    
    def setup_test_data(self, driver, node_count: int = 1000):
        """테스트 데이터 설정"""
        print(f"\n설정: {node_count}개의 테스트 노드 생성 중...")
        
        # 기존 테스트 데이터 삭제
        driver.execute_query("MATCH (n:PerfTestCompany) DETACH DELETE n")
        driver.execute_query("MATCH (n:PerfTestPerson) DETACH DELETE n")
        
        # 배치로 노드 생성
        batch_size = 100
        for i in range(0, node_count, batch_size):
            batch_companies = []
            batch_people = []
            
            for j in range(min(batch_size, node_count - i)):
                idx = i + j
                batch_companies.append({
                    "id": f"perf-company-{idx}",
                    "name": f"Test Company {idx}",
                    "risk_score": (idx % 10) + 1,
                    "sector": f"Sector{idx % 5}",
                    "country": f"Country{idx % 3}"
                })
                batch_people.append({
                    "id": f"perf-person-{idx}",
                    "name": f"Test Person {idx}",
                    "company": f"Test Company {idx}"
                })
            
            # 회사 노드 생성
            driver.execute_query("""
                UNWIND $companies as company
                CREATE (c:PerfTestCompany)
                SET c = company
            """, companies=batch_companies)
            
            # 인물 노드 생성
            driver.execute_query("""
                UNWIND $people as person
                CREATE (p:PerfTestPerson)
                SET p = person
            """, people=batch_people)
        
        # 관계 생성 (일부만)
        driver.execute_query("""
            MATCH (p:PerfTestPerson), (c:PerfTestCompany)
            WHERE p.company = c.name
            WITH p, c LIMIT 500
            CREATE (p)-[:WORKS_AT]->(c)
        """)
        
        # 회사 간 관계 생성
        driver.execute_query("""
            MATCH (c1:PerfTestCompany), (c2:PerfTestCompany)
            WHERE c1.sector = c2.sector 
              AND c1.id < c2.id
              AND rand() < 0.1
            WITH c1, c2 LIMIT 200
            CREATE (c1)-[:COMPETES_WITH {intensity: rand()}]->(c2)
        """)
    
    def cleanup_test_data(self, driver):
        """테스트 데이터 정리"""
        driver.execute_query("MATCH (n:PerfTestCompany) DETACH DELETE n")
        driver.execute_query("MATCH (n:PerfTestPerson) DETACH DELETE n")
    
    def measure_query_time(self, driver, query: str, params: Dict[str, Any] = None, iterations: int = 10) -> Dict[str, float]:
        """쿼리 실행 시간 측정"""
        times = []
        
        for _ in range(iterations):
            start = time.time()
            driver.execute_query(query, **(params or {}))
            end = time.time()
            times.append(end - start)
        
        return {
            "min": min(times),
            "max": max(times),
            "avg": statistics.mean(times),
            "median": statistics.median(times),
            "stddev": statistics.stdev(times) if len(times) > 1 else 0
        }
    
    @pytest.mark.performance
    def test_simple_node_lookup(self, driver):
        """단순 노드 조회 성능"""
        self.setup_test_data(driver, 1000)
        
        # ID로 조회 (인덱스 사용)
        query = "MATCH (c:PerfTestCompany {id: $id}) RETURN c"
        params = {"id": "perf-company-500"}
        
        results = self.measure_query_time(driver, query, params)
        
        print(f"\n단순 노드 조회 (ID 인덱스):")
        print(f"  평균: {results['avg']:.4f}초")
        print(f"  중간값: {results['median']:.4f}초")
        print(f"  최소: {results['min']:.4f}초")
        print(f"  최대: {results['max']:.4f}초")
        
        # 성능 기준: 인덱스 조회는 10ms 이하
        assert results['avg'] < 0.01
        
        self.cleanup_test_data(driver)
    
    @pytest.mark.performance
    def test_pattern_matching(self, driver):
        """패턴 매칭 성능"""
        self.setup_test_data(driver, 1000)
        
        # 1-hop 관계 탐색
        query = """
        MATCH (c:PerfTestCompany {id: $id})-[:COMPETES_WITH]-(competitor)
        RETURN c.name, collect(competitor.name) as competitors
        """
        params = {"id": "perf-company-100"}
        
        results = self.measure_query_time(driver, query, params)
        
        print(f"\n1-hop 관계 탐색:")
        print(f"  평균: {results['avg']:.4f}초")
        print(f"  중간값: {results['median']:.4f}초")
        
        # 성능 기준: 1-hop 탐색은 50ms 이하
        assert results['avg'] < 0.05
        
        self.cleanup_test_data(driver)
    
    @pytest.mark.performance
    def test_aggregation_query(self, driver):
        """집계 쿼리 성능"""
        self.setup_test_data(driver, 5000)
        
        # 섹터별 평균 리스크 점수
        query = """
        MATCH (c:PerfTestCompany)
        RETURN c.sector as sector, 
               count(c) as count,
               avg(c.risk_score) as avg_risk
        ORDER BY count DESC
        """
        
        results = self.measure_query_time(driver, query)
        
        print(f"\n집계 쿼리 (5000개 노드):")
        print(f"  평균: {results['avg']:.4f}초")
        print(f"  중간값: {results['median']:.4f}초")
        
        # 성능 기준: 5000개 노드 집계는 100ms 이하
        assert results['avg'] < 0.1
        
        self.cleanup_test_data(driver)
    
    @pytest.mark.performance
    def test_multi_hop_traversal(self, driver):
        """다중 홉 탐색 성능"""
        self.setup_test_data(driver, 1000)
        
        # 2-hop 네트워크 분석
        query = """
        MATCH path = (c:PerfTestCompany {id: $id})-[*1..2]-(connected)
        WHERE c <> connected
        WITH c, connected, length(path) as distance
        RETURN c.name, 
               count(DISTINCT connected) as network_size,
               avg(connected.risk_score) as avg_network_risk
        """
        params = {"id": "perf-company-200"}
        
        results = self.measure_query_time(driver, query, params, iterations=5)
        
        print(f"\n2-hop 네트워크 분석:")
        print(f"  평균: {results['avg']:.4f}초")
        print(f"  중간값: {results['median']:.4f}초")
        
        # 성능 기준: 2-hop 탐색은 200ms 이하
        assert results['avg'] < 0.2
        
        self.cleanup_test_data(driver)
    
    @pytest.mark.performance
    def test_concurrent_queries(self, driver):
        """동시 쿼리 처리 성능"""
        self.setup_test_data(driver, 2000)
        
        def run_query(company_id: str):
            """개별 쿼리 실행"""
            query = """
            MATCH (c:PerfTestCompany {id: $id})
            OPTIONAL MATCH (c)-[:COMPETES_WITH]-(competitor)
            RETURN c.name, count(competitor) as competitor_count
            """
            start = time.time()
            driver.execute_query(query, id=company_id)
            return time.time() - start
        
        # 동시에 20개 쿼리 실행
        concurrent_queries = 20
        company_ids = [f"perf-company-{i}" for i in range(concurrent_queries)]
        
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(run_query, cid) for cid in company_ids]
            individual_times = [f.result() for f in as_completed(futures)]
        total_time = time.time() - start_time
        
        print(f"\n동시 쿼리 처리 ({concurrent_queries}개):")
        print(f"  총 실행 시간: {total_time:.4f}초")
        print(f"  평균 개별 시간: {statistics.mean(individual_times):.4f}초")
        print(f"  처리량: {concurrent_queries/total_time:.2f} queries/sec")
        
        # 성능 기준: 20개 동시 쿼리는 1초 이내
        assert total_time < 1.0
        
        self.cleanup_test_data(driver)
    
    @pytest.mark.performance
    def test_write_performance(self, tm, driver):
        """쓰기 성능 테스트"""
        # 기존 데이터 정리
        driver.execute_query("MATCH (n:PerfTestWrite) DETACH DELETE n")
        
        # 단일 노드 생성
        single_write_times = []
        for i in range(10):
            start = time.time()
            tm.safe_merge_node(
                "PerfTestWrite",
                f"write-test-{i}",
                {"name": f"Write Test {i}", "value": i}
            )
            single_write_times.append(time.time() - start)
        
        # 배치 쓰기
        batch_operations = []
        for i in range(100):
            batch_operations.append((
                "CREATE (n:PerfTestWrite {id: $id, name: $name})",
                {"id": f"batch-write-{i}", "name": f"Batch Write {i}"}
            ))
        
        start = time.time()
        tm.batch_write(batch_operations, batch_size=20)
        batch_time = time.time() - start
        
        print(f"\n쓰기 성능:")
        print(f"  단일 노드 생성 평균: {statistics.mean(single_write_times):.4f}초")
        print(f"  배치 쓰기 (100개): {batch_time:.4f}초")
        print(f"  배치 처리량: {100/batch_time:.2f} nodes/sec")
        
        # 성능 기준
        assert statistics.mean(single_write_times) < 0.05  # 단일 쓰기 50ms 이하
        assert batch_time < 1.0  # 100개 배치 1초 이하
        
        # 정리
        driver.execute_query("MATCH (n:PerfTestWrite) DETACH DELETE n")
    
    @pytest.mark.performance
    def test_index_effectiveness(self, driver):
        """인덱스 효과성 테스트"""
        self.setup_test_data(driver, 10000)
        
        # 인덱스가 있는 쿼리 (id)
        indexed_query = "MATCH (c:PerfTestCompany {id: $id}) RETURN c"
        indexed_results = self.measure_query_time(
            driver, indexed_query, {"id": "perf-company-5000"}
        )
        
        # 인덱스가 없는 쿼리 (name contains)
        non_indexed_query = "MATCH (c:PerfTestCompany) WHERE c.name CONTAINS $text RETURN c LIMIT 10"
        non_indexed_results = self.measure_query_time(
            driver, non_indexed_query, {"text": "Company 500"}
        )
        
        print(f"\n인덱스 효과성:")
        print(f"  인덱스 쿼리 평균: {indexed_results['avg']:.4f}초")
        print(f"  비인덱스 쿼리 평균: {non_indexed_results['avg']:.4f}초")
        print(f"  성능 향상: {non_indexed_results['avg']/indexed_results['avg']:.2f}배")
        
        # 인덱스가 최소 10배 이상 빠를 것으로 예상
        assert indexed_results['avg'] * 10 < non_indexed_results['avg']
        
        self.cleanup_test_data(driver)