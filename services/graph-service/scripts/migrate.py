#!/usr/bin/env python3
"""데이터베이스 마이그레이션 실행 스크립트"""
import sys
import os
import argparse
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.migrations.migration import runner
from scripts.migrations.001_initial_schema import InitialSchema

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 마이그레이션 등록
def register_migrations():
    """모든 마이그레이션 등록"""
    migrations = [
        InitialSchema(),
        # 추가 마이그레이션은 여기에
    ]
    
    for migration in migrations:
        runner.register(migration)

def main():
    parser = argparse.ArgumentParser(description="Neo4j Database Migration Tool")
    parser.add_argument('command', choices=['up', 'down', 'status', 'run'],
                       help='Migration command')
    parser.add_argument('--version', help='Specific version to migrate to')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without executing')
    
    args = parser.parse_args()
    
    # 마이그레이션 등록
    register_migrations()
    
    if args.command == 'status':
        # 마이그레이션 상태 확인
        status = runner.status()
        logger.info(f"Migration Status:")
        logger.info(f"  Executed: {len(status['executed'])} migrations")
        for v in status['executed']:
            logger.info(f"    - {v}")
        logger.info(f"  Pending: {len(status['pending'])} migrations")
        for v in status['pending']:
            logger.info(f"    - {v}")
        logger.info(f"  Up to date: {status['up_to_date']}")
        
    elif args.command == 'up':
        # 모든 대기 중인 마이그레이션 실행
        if args.dry_run:
            pending = runner.get_pending_migrations()
            logger.info(f"Would run {len(pending)} migrations:")
            for m in pending:
                logger.info(f"  - {m.version}: {m.description}")
        else:
            runner.run_all()
            
    elif args.command == 'run':
        # 특정 버전 실행
        if not args.version:
            logger.error("--version required for 'run' command")
            sys.exit(1)
        
        if args.dry_run:
            logger.info(f"Would run migration {args.version}")
        else:
            runner.run_specific(args.version)
            
    elif args.command == 'down':
        # 롤백
        if not args.version:
            logger.error("--version required for 'down' command")
            sys.exit(1)
        
        if args.dry_run:
            executed = runner.get_executed_migrations()
            to_rollback = [v for v in executed if v > args.version]
            logger.info(f"Would rollback {len(to_rollback)} migrations:")
            for v in reversed(to_rollback):
                logger.info(f"  - {v}")
        else:
            runner.rollback_to(args.version)

if __name__ == "__main__":
    main()