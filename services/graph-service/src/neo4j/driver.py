"""Neo4j 드라이버 관리"""
import logging
import time
from typing import Optional
from neo4j import GraphDatabase, Driver
from neo4j.exceptions import ServiceUnavailable, TransientError, AuthError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .config import config

logger = logging.getLogger(__name__)

class Neo4jDriver:
    """Neo4j 드라이버 싱글톤"""
    _instance: Optional['Neo4jDriver'] = None
    _driver: Optional[Driver] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        # Delay initialization until first use
        pass
    
    @retry(
        stop=stop_after_attempt(30),  # 최대 30번 시도 (약 5분)
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ServiceUnavailable, ConnectionRefusedError)),
        before_sleep=lambda retry_state: logger.info(f"Waiting for Neo4j to be ready... Attempt {retry_state.attempt_number}")
    )
    def _initialize_driver(self):
        """드라이버 초기화 with 재시도"""
        try:
            self._driver = GraphDatabase.driver(
                config.uri,
                auth=(config.username, config.password),
                max_connection_pool_size=config.max_connection_pool_size,
                connection_acquisition_timeout=config.connection_acquisition_timeout,
                encrypted=config.encrypted
            )
            self._driver.verify_connectivity()
            logger.info(f"Successfully connected to Neo4j at {config.uri}")
        except AuthError as e:
            logger.error(f"Authentication failed for Neo4j: {e}")
            self._driver = None
            raise
        except ServiceUnavailable as e:
            logger.warning(f"Neo4j is not available yet: {e}")
            self._driver = None
            raise
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            self._driver = None
            raise
    
    @property
    def driver(self) -> Optional[Driver]:
        """드라이버 인스턴스 반환 (lazy initialization)"""
        if self._driver is None:
            self._initialize_driver()
        return self._driver
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=(ServiceUnavailable, TransientError)
    )
    def execute_query(self, query: str, **params):
        """쿼리 실행 with 재시도"""
        if not self._driver:
            raise ServiceUnavailable("Neo4j driver not initialized")
        
        with self._driver.session(database=config.database) as session:
            return session.run(query, **params).data()
    
    def execute_write(self, query: str, **params):
        """쓰기 트랜잭션 실행"""
        if not self._driver:
            raise ServiceUnavailable("Neo4j driver not initialized")
        
        with self._driver.session(database=config.database) as session:
            return session.execute_write(lambda tx: tx.run(query, **params).data())
    
    def execute_read(self, query: str, **params):
        """읽기 트랜잭션 실행"""
        if not self._driver:
            raise ServiceUnavailable("Neo4j driver not initialized")
        
        with self._driver.session(database=config.database) as session:
            return session.execute_read(lambda tx: tx.run(query, **params).data())
    
    def close(self):
        """드라이버 종료"""
        if self._driver:
            self._driver.close()
            self._driver = None
            logger.info("Neo4j driver closed")
    
    def __del__(self):
        """소멸자"""
        self.close()

# 싱글톤 인스턴스
driver = Neo4jDriver()