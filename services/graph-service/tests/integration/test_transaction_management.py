"""트랜잭션 관리 통합 테스트"""
import pytest
from src.neo4j.transaction import TransactionManager
from src.neo4j.driver import Neo4jDriver
from neo4j.exceptions import TransientError

class TestTransactionManagement:
    """트랜잭션 관리 테스트"""
    
    @pytest.fixture
    def tm(self):
        """TransactionManager fixture"""
        return TransactionManager()
    
    @pytest.fixture
    def driver(self):
        """Neo4j Driver fixture"""
        return Neo4jDriver()
    
    def cleanup_test_data(self, driver):
        """테스트 데이터 정리"""
        driver.execute_query("MATCH (n:TestCompany) DETACH DELETE n")
        driver.execute_query("MATCH (n:TestPerson) DETACH DELETE n")
    
    @pytest.mark.integration
    def test_complex_transaction(self, tm, driver):
        """복잡한 트랜잭션 테스트"""
        self.cleanup_test_data(driver)
        
        # 여러 쿼리를 하나의 트랜잭션에서 실행
        queries = [
            {
                'query': "CREATE (c:TestCompany {id: $id, name: $name})",
                'params': {'id': 'test-company-1', 'name': 'Test Corp'}
            },
            {
                'query': "CREATE (p:TestPerson {id: $id, name: $name})",
                'params': {'id': 'test-person-1', 'name': 'John Doe'}
            },
            {
                'query': """
                    MATCH (c:TestCompany {id: $company_id})
                    MATCH (p:TestPerson {id: $person_id})
                    CREATE (p)-[:WORKS_AT]->(c)
                """,
                'params': {'company_id': 'test-company-1', 'person_id': 'test-person-1'}
            }
        ]
        
        # 트랜잭션 실행
        results = tm.execute_in_transaction(queries)
        assert len(results) == 3
        
        # 데이터 확인
        verify_result = driver.execute_query("""
            MATCH (p:TestPerson)-[:WORKS_AT]->(c:TestCompany)
            RETURN p.name as person, c.name as company
        """)
        
        assert len(verify_result) == 1
        assert verify_result[0]['person'] == 'John Doe'
        assert verify_result[0]['company'] == 'Test Corp'
        
        self.cleanup_test_data(driver)
    
    @pytest.mark.integration
    def test_safe_merge_node(self, tm, driver):
        """안전한 노드 MERGE 테스트"""
        self.cleanup_test_data(driver)
        
        node_id = "test-merge-company"
        
        # 첫 번째 merge - 생성
        success1 = tm.safe_merge_node(
            'TestCompany',
            node_id,
            {'name': 'Merge Test Corp', 'value': 1}
        )
        assert success1
        
        # 두 번째 merge - 업데이트
        success2 = tm.safe_merge_node(
            'TestCompany',
            node_id,
            {'value': 2}  # value만 업데이트
        )
        assert success2
        
        # 확인
        result = driver.execute_query(
            "MATCH (c:TestCompany {id: $id}) RETURN c",
            id=node_id
        )
        
        assert len(result) == 1
        assert result[0]['c']['name'] == 'Merge Test Corp'
        assert result[0]['c']['value'] == 2
        
        self.cleanup_test_data(driver)
    
    @pytest.mark.integration
    def test_create_relationship_safe(self, tm, driver):
        """안전한 관계 생성 테스트"""
        self.cleanup_test_data(driver)
        
        # 노드 생성
        driver.execute_write(
            "CREATE (c:TestCompany {id: 'rel-company-1', name: 'Company 1'})"
        )
        driver.execute_write(
            "CREATE (c:TestCompany {id: 'rel-company-2', name: 'Company 2'})"
        )
        
        # 관계 생성
        success = tm.create_relationship_safe(
            {'type': 'TestCompany', 'id': 'rel-company-1'},
            {'type': 'TestCompany', 'id': 'rel-company-2'},
            'PARTNERS_WITH',
            {'since': '2024', 'strength': 0.8}
        )
        assert success
        
        # 확인
        result = driver.execute_query("""
            MATCH (c1:TestCompany {id: 'rel-company-1'})
                  -[r:PARTNERS_WITH]->
                  (c2:TestCompany {id: 'rel-company-2'})
            RETURN r.strength as strength
        """)
        
        assert len(result) == 1
        assert result[0]['strength'] == 0.8
        
        self.cleanup_test_data(driver)
    
    @pytest.mark.integration
    def test_retry_on_transient_error(self, tm):
        """일시적 오류 시 재시도 테스트"""
        retry_count = 0
        
        def flaky_function():
            nonlocal retry_count
            retry_count += 1
            if retry_count < 3:
                raise TransientError("Simulated transient error")
            return "Success"
        
        # 재시도 성공
        result = tm.execute_with_retry(flaky_function)
        assert result == "Success"
        assert retry_count == 3
    
    @pytest.mark.integration
    def test_batch_write_partial_failure(self, tm, driver):
        """배치 쓰기 부분 실패 테스트"""
        self.cleanup_test_data(driver)
        
        # 일부 잘못된 쿼리 포함
        operations = [
            ("CREATE (n:TestCompany {id: $id})", {"id": "batch-1"}),
            ("CREATE (n:TestCompany {id: $id})", {"id": "batch-2"}),
            ("INVALID CYPHER QUERY", {}),  # 실패할 쿼리
            ("CREATE (n:TestCompany {id: $id})", {"id": "batch-3"}),
        ]
        
        # 배치 실행
        failed = tm.batch_write(operations, batch_size=2)
        
        # 실패한 배치 확인
        assert len(failed) > 0
        
        # 성공한 노드 확인
        result = driver.execute_query(
            "MATCH (n:TestCompany) WHERE n.id STARTS WITH 'batch-' RETURN count(n) as count"
        )
        
        # 최소한 첫 번째 배치는 성공
        assert result[0]['count'] >= 2
        
        self.cleanup_test_data(driver)