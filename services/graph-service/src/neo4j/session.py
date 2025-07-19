"""Neo4j 세션 관리"""
import logging
from contextlib import contextmanager
from typing import Optional, Dict, Any, List
from neo4j import Session, Transaction
from neo4j.exceptions import ServiceUnavailable

from .driver import driver as neo4j_driver
from .config import config

logger = logging.getLogger(__name__)

class Neo4jSession:
    """Neo4j 세션 래퍼"""
    
    def __init__(self, database: Optional[str] = None):
        self.database = database or config.database
        self._driver = neo4j_driver.driver
    
    @contextmanager
    def session(self):
        """세션 컨텍스트 매니저"""
        if not self._driver:
            raise ServiceUnavailable("Neo4j driver not initialized")
        
        session = self._driver.session(database=self.database)
        try:
            yield session
        finally:
            session.close()
    
    def run_query(self, query: str, **params) -> List[Dict[str, Any]]:
        """단일 쿼리 실행"""
        with self.session() as session:
            result = session.run(query, **params)
            return result.data()
    
    def batch_write(self, queries: List[tuple], batch_size: int = 1000):
        """배치 쓰기 실행
        
        Args:
            queries: (query, params) 튜플 리스트
            batch_size: 배치 크기
        """
        with self.session() as session:
            for i in range(0, len(queries), batch_size):
                batch = queries[i:i+batch_size]
                
                def execute_batch(tx: Transaction):
                    for query, params in batch:
                        tx.run(query, **params)
                
                session.execute_write(execute_batch)
                logger.info(f"Executed batch {i//batch_size + 1}/{(len(queries)-1)//batch_size + 1}")
    
    def create_constraints(self, constraints: List[str]):
        """제약조건 생성"""
        with self.session() as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                    logger.info(f"Created constraint: {constraint}")
                except Exception as e:
                    logger.warning(f"Constraint might already exist: {e}")
    
    def create_indexes(self, indexes: List[str]):
        """인덱스 생성"""
        with self.session() as session:
            for index in indexes:
                try:
                    session.run(index)
                    logger.info(f"Created index: {index}")
                except Exception as e:
                    logger.warning(f"Index might already exist: {e}")

# 기본 세션 인스턴스
session = Neo4jSession()