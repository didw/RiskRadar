"""Neo4j 연결 설정"""
import os
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Neo4jConfig:
    """Neo4j 연결 설정"""
    uri: str
    username: str
    password: str
    database: Optional[str] = None
    max_connection_pool_size: int = 50
    connection_acquisition_timeout: int = 30
    encrypted: bool = False
    
    @classmethod
    def from_env(cls) -> 'Neo4jConfig':
        """환경 변수에서 설정 로드"""
        # Docker Compose 환경에서는 서비스명 사용
        is_docker = os.getenv("DOCKER_ENV", "false").lower() == "true"
        default_host = "neo4j" if is_docker else "localhost"
        
        return cls(
            uri=os.getenv("NEO4J_URI", f"bolt://{default_host}:7687"),
            username=os.getenv("NEO4J_USER", "neo4j"),
            password=os.getenv("NEO4J_PASSWORD", "password123"),
            database=os.getenv("NEO4J_DATABASE", "neo4j"),
            max_connection_pool_size=int(os.getenv("NEO4J_MAX_POOL_SIZE", "50")),
            connection_acquisition_timeout=int(os.getenv("NEO4J_CONN_TIMEOUT", "30")),
            encrypted=os.getenv("NEO4J_ENCRYPTED", "false").lower() == "true"
        )

# 싱글톤 설정 인스턴스
config = Neo4jConfig.from_env()