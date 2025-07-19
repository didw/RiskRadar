"""Neo4j 트랜잭션 관리"""
import logging
from contextlib import contextmanager
from typing import Optional, Any, Callable, Dict, List
from neo4j import Session, Transaction
from neo4j.exceptions import ServiceUnavailable, TransientError, Neo4jError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .driver import driver as neo4j_driver

logger = logging.getLogger(__name__)

class TransactionManager:
    """트랜잭션 관리자"""
    
    def __init__(self):
        self.driver = neo4j_driver.driver
        
    @contextmanager
    def transaction(self, database: Optional[str] = None, read_only: bool = False):
        """트랜잭션 컨텍스트 매니저
        
        Args:
            database: 데이터베이스 이름
            read_only: 읽기 전용 트랜잭션 여부
            
        Yields:
            Transaction 객체
        """
        if not self.driver:
            raise ServiceUnavailable("Neo4j driver not initialized")
            
        session = self.driver.session(database=database)
        tx = None
        
        try:
            if read_only:
                tx = session.begin_transaction(access_mode="READ")
            else:
                tx = session.begin_transaction(access_mode="WRITE")
                
            yield tx
            
            # 트랜잭션 커밋
            tx.commit()
            logger.debug("Transaction committed successfully")
            
        except Exception as e:
            # 트랜잭션 롤백
            if tx:
                try:
                    tx.rollback()
                    logger.warning(f"Transaction rolled back due to: {e}")
                except:
                    pass  # 롤백 실패는 무시
            raise
            
        finally:
            if tx:
                tx.close()
            session.close()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((ServiceUnavailable, TransientError))
    )
    def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """재시도 로직이 포함된 실행
        
        Args:
            func: 실행할 함수
            *args, **kwargs: 함수 인자
            
        Returns:
            함수 실행 결과
        """
        try:
            return func(*args, **kwargs)
        except (ServiceUnavailable, TransientError) as e:
            logger.warning(f"Transient error occurred, will retry: {e}")
            raise
        except Neo4jError as e:
            logger.error(f"Neo4j error occurred: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise
    
    def batch_write(self, operations: List[tuple], batch_size: int = 1000):
        """배치 쓰기 트랜잭션
        
        Args:
            operations: (query, params) 튜플 리스트
            batch_size: 배치 크기
        """
        total = len(operations)
        completed = 0
        failed = []
        
        for i in range(0, total, batch_size):
            batch = operations[i:i+batch_size]
            
            try:
                with self.transaction() as tx:
                    for query, params in batch:
                        tx.run(query, **params)
                        
                completed += len(batch)
                logger.info(f"Batch progress: {completed}/{total}")
                
            except Exception as e:
                logger.error(f"Batch {i//batch_size + 1} failed: {e}")
                failed.extend(batch)
        
        if failed:
            logger.warning(f"{len(failed)} operations failed")
            return failed
        
        return []
    
    def execute_in_transaction(self, queries: List[Dict[str, Any]], read_only: bool = False) -> List[Dict[str, Any]]:
        """여러 쿼리를 하나의 트랜잭션에서 실행
        
        Args:
            queries: [{'query': str, 'params': dict}] 형식의 쿼리 리스트
            read_only: 읽기 전용 여부
            
        Returns:
            각 쿼리의 결과 리스트
        """
        results = []
        
        with self.transaction(read_only=read_only) as tx:
            for q in queries:
                query = q.get('query')
                params = q.get('params', {})
                
                try:
                    result = tx.run(query, **params)
                    results.append(result.data())
                except Exception as e:
                    logger.error(f"Query failed in transaction: {query}")
                    raise
        
        return results
    
    def safe_merge_node(self, node_type: str, node_id: str, properties: Dict[str, Any]) -> bool:
        """안전한 노드 MERGE 실행
        
        Args:
            node_type: 노드 타입 (Company, Person 등)
            node_id: 노드 ID
            properties: 노드 속성
            
        Returns:
            성공 여부
        """
        query = f"""
        MERGE (n:{node_type} {{id: $id}})
        ON CREATE SET n += $properties, n.created_at = datetime()
        ON MATCH SET n += $properties, n.updated_at = datetime()
        RETURN n
        """
        
        try:
            with self.transaction() as tx:
                result = tx.run(query, id=node_id, properties=properties)
                node = result.single()
                if node:
                    logger.debug(f"Node {node_type}:{node_id} merged successfully")
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Failed to merge node {node_type}:{node_id}: {e}")
            return False
    
    def create_relationship_safe(self, from_node: Dict, to_node: Dict, 
                               rel_type: str, properties: Dict[str, Any] = None) -> bool:
        """안전한 관계 생성
        
        Args:
            from_node: {'type': str, 'id': str}
            to_node: {'type': str, 'id': str}
            rel_type: 관계 타입
            properties: 관계 속성
            
        Returns:
            성공 여부
        """
        query = f"""
        MATCH (a:{from_node['type']} {{id: $from_id}})
        MATCH (b:{to_node['type']} {{id: $to_id}})
        MERGE (a)-[r:{rel_type}]->(b)
        SET r += $properties
        RETURN r
        """
        
        try:
            with self.transaction() as tx:
                result = tx.run(
                    query,
                    from_id=from_node['id'],
                    to_id=to_node['id'],
                    properties=properties or {}
                )
                rel = result.single()
                if rel:
                    logger.debug(f"Relationship {rel_type} created successfully")
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Failed to create relationship {rel_type}: {e}")
            return False

# 싱글톤 인스턴스
transaction_manager = TransactionManager()