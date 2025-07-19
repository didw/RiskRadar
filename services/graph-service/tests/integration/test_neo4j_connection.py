"""Neo4j 연결 통합 테스트"""
import pytest
import os
from src.neo4j.driver import Neo4jDriver
from src.neo4j.session import Neo4jSession
from src.neo4j.transaction import TransactionManager

class TestNeo4jConnection:
    """Neo4j 연결 테스트"""
    
    @pytest.fixture
    def driver(self):
        """Neo4j 드라이버 fixture"""
        driver = Neo4jDriver()
        yield driver
        driver.close()
    
    @pytest.fixture
    def session(self):
        """Neo4j 세션 fixture"""
        return Neo4jSession()
    
    @pytest.mark.integration
    def test_driver_connection(self, driver):
        """드라이버 연결 테스트"""
        assert driver.driver is not None
        
        # 연결 확인
        result = driver.execute_query("RETURN 1 as num")
        assert result[0]['num'] == 1
    
    @pytest.mark.integration
    def test_session_query(self, session):
        """세션 쿼리 테스트"""
        result = session.run_query("RETURN 'hello' as greeting")
        assert len(result) == 1
        assert result[0]['greeting'] == 'hello'
    
    @pytest.mark.integration
    def test_transaction_commit(self):
        """트랜잭션 커밋 테스트"""
        tm = TransactionManager()
        
        # 테스트 노드 생성
        test_id = "test-node-1"
        
        with tm.transaction() as tx:
            tx.run(
                "CREATE (n:TestNode {id: $id, name: $name})",
                id=test_id,
                name="Test Node"
            )
        
        # 노드가 생성되었는지 확인
        result = tm.execute_with_retry(
            lambda: Neo4jDriver().execute_query(
                "MATCH (n:TestNode {id: $id}) RETURN n.name as name",
                id=test_id
            )
        )
        
        assert len(result) == 1
        assert result[0]['name'] == "Test Node"
        
        # 정리
        Neo4jDriver().execute_query(
            "MATCH (n:TestNode {id: $id}) DELETE n",
            id=test_id
        )
    
    @pytest.mark.integration
    def test_transaction_rollback(self):
        """트랜잭션 롤백 테스트"""
        tm = TransactionManager()
        test_id = "test-rollback-node"
        
        try:
            with tm.transaction() as tx:
                tx.run(
                    "CREATE (n:TestNode {id: $id, name: $name})",
                    id=test_id,
                    name="Rollback Test"
                )
                # 강제로 에러 발생
                raise Exception("Test rollback")
        except:
            pass
        
        # 노드가 생성되지 않았는지 확인
        result = Neo4jDriver().execute_query(
            "MATCH (n:TestNode {id: $id}) RETURN n",
            id=test_id
        )
        
        assert len(result) == 0
    
    @pytest.mark.integration
    def test_batch_write(self):
        """배치 쓰기 테스트"""
        tm = TransactionManager()
        
        # 배치 작업 준비
        operations = []
        for i in range(10):
            operations.append((
                "CREATE (n:BatchTest {id: $id, value: $value})",
                {"id": f"batch-{i}", "value": i}
            ))
        
        # 배치 실행
        failed = tm.batch_write(operations, batch_size=5)
        assert len(failed) == 0
        
        # 모든 노드가 생성되었는지 확인
        result = Neo4jDriver().execute_query(
            "MATCH (n:BatchTest) RETURN count(n) as count"
        )
        assert result[0]['count'] == 10
        
        # 정리
        Neo4jDriver().execute_query("MATCH (n:BatchTest) DELETE n")