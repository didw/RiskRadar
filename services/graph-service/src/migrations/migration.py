"""마이그레이션 시스템 기본 클래스"""
import os
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any
from src.neo4j.session import session

logger = logging.getLogger(__name__)

class Migration(ABC):
    """마이그레이션 기본 클래스"""
    
    def __init__(self, version: str, description: str):
        self.version = version
        self.description = description
        self.executed_at = None
        
    @abstractmethod
    def up(self):
        """마이그레이션 적용"""
        pass
    
    @abstractmethod
    def down(self):
        """마이그레이션 롤백"""
        pass
    
    def execute(self):
        """마이그레이션 실행"""
        try:
            logger.info(f"Executing migration {self.version}: {self.description}")
            self.up()
            self._mark_as_executed()
            logger.info(f"Migration {self.version} completed successfully")
        except Exception as e:
            logger.error(f"Migration {self.version} failed: {e}")
            raise
    
    def rollback(self):
        """마이그레이션 롤백"""
        try:
            logger.info(f"Rolling back migration {self.version}")
            self.down()
            self._mark_as_rolled_back()
            logger.info(f"Migration {self.version} rolled back successfully")
        except Exception as e:
            logger.error(f"Rollback of migration {self.version} failed: {e}")
            raise
    
    def _mark_as_executed(self):
        """마이그레이션 실행 기록"""
        query = """
        CREATE (m:Migration {
            version: $version,
            description: $description,
            executed_at: datetime(),
            status: 'executed'
        })
        """
        session.run_query(query, version=self.version, description=self.description)
    
    def _mark_as_rolled_back(self):
        """마이그레이션 롤백 기록"""
        query = """
        MATCH (m:Migration {version: $version})
        SET m.status = 'rolled_back',
            m.rolled_back_at = datetime()
        """
        session.run_query(query, version=self.version)

class MigrationRunner:
    """마이그레이션 실행기"""
    
    def __init__(self):
        self.migrations: List[Migration] = []
        self._ensure_migration_tracking()
    
    def _ensure_migration_tracking(self):
        """마이그레이션 추적을 위한 제약조건 생성"""
        constraint = "CREATE CONSTRAINT migration_version IF NOT EXISTS FOR (m:Migration) REQUIRE m.version IS UNIQUE"
        try:
            session.run_query(constraint)
        except Exception as e:
            logger.debug(f"Migration constraint might already exist: {e}")
    
    def register(self, migration: Migration):
        """마이그레이션 등록"""
        self.migrations.append(migration)
        self.migrations.sort(key=lambda m: m.version)
    
    def get_executed_migrations(self) -> List[str]:
        """실행된 마이그레이션 목록 조회"""
        query = """
        MATCH (m:Migration)
        WHERE m.status = 'executed'
        RETURN m.version as version
        ORDER BY m.version
        """
        results = session.run_query(query)
        return [r['version'] for r in results]
    
    def get_pending_migrations(self) -> List[Migration]:
        """실행 대기 중인 마이그레이션 목록"""
        executed = set(self.get_executed_migrations())
        return [m for m in self.migrations if m.version not in executed]
    
    def run_all(self):
        """모든 대기 중인 마이그레이션 실행"""
        pending = self.get_pending_migrations()
        if not pending:
            logger.info("No pending migrations")
            return
        
        logger.info(f"Found {len(pending)} pending migrations")
        for migration in pending:
            migration.execute()
    
    def run_specific(self, version: str):
        """특정 버전의 마이그레이션 실행"""
        migration = next((m for m in self.migrations if m.version == version), None)
        if not migration:
            raise ValueError(f"Migration {version} not found")
        
        executed = self.get_executed_migrations()
        if version in executed:
            logger.warning(f"Migration {version} already executed")
            return
        
        migration.execute()
    
    def rollback_to(self, version: str):
        """특정 버전까지 롤백"""
        executed = self.get_executed_migrations()
        to_rollback = [v for v in executed if v > version]
        
        if not to_rollback:
            logger.info("No migrations to rollback")
            return
        
        # 역순으로 롤백
        for v in reversed(to_rollback):
            migration = next((m for m in self.migrations if m.version == v), None)
            if migration:
                migration.rollback()
    
    def status(self) -> Dict[str, Any]:
        """마이그레이션 상태 조회"""
        executed = self.get_executed_migrations()
        pending = self.get_pending_migrations()
        
        return {
            "executed": executed,
            "pending": [m.version for m in pending],
            "total": len(self.migrations),
            "up_to_date": len(pending) == 0
        }

# 전역 마이그레이션 러너
runner = MigrationRunner()