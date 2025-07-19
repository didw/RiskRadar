"""엔티티 캐시 시스템 - N+1 문제 해결"""
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import threading
import time

from src.neo4j.session import session

logger = logging.getLogger(__name__)

class EntityCache:
    """엔티티 캐시 시스템"""
    
    def __init__(self, cache_ttl_minutes: int = 30):
        self.companies: Dict[str, Dict] = {}
        self.persons: Dict[str, Dict] = {}
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)
        self.last_refresh = {
            'companies': None,
            'persons': None
        }
        self._lock = threading.RLock()
        
    def get_companies(self, force_refresh: bool = False) -> List[Dict]:
        """기업 목록 조회 (캐시 우선)"""
        with self._lock:
            if self._should_refresh('companies', force_refresh):
                self._refresh_companies()
            return list(self.companies.values())
    
    def get_persons(self, force_refresh: bool = False) -> List[Dict]:
        """인물 목록 조회 (캐시 우선)"""
        with self._lock:
            if self._should_refresh('persons', force_refresh):
                self._refresh_persons()
            return list(self.persons.values())
    
    def find_company_by_name(self, name: str) -> Optional[Dict]:
        """이름으로 기업 찾기 (캐시에서)"""
        companies = self.get_companies()
        
        # 정확한 이름 매칭
        for company in companies:
            if company['name'].lower() == name.lower():
                return company
            # 별칭 확인
            if company.get('aliases'):
                for alias in company['aliases']:
                    if alias.lower() == name.lower():
                        return company
        return None
    
    def find_person_by_name(self, name: str) -> Optional[Dict]:
        """이름으로 인물 찾기 (캐시에서)"""
        persons = self.get_persons()
        
        # 정확한 이름 매칭
        for person in persons:
            if person['name'].lower() == name.lower():
                return person
            # 별칭 확인
            if person.get('aliases'):
                for alias in person['aliases']:
                    if alias.lower() == name.lower():
                        return person
        return None
    
    def add_company(self, company: Dict):
        """새 기업을 캐시에 추가"""
        with self._lock:
            self.companies[company['id']] = company
    
    def add_person(self, person: Dict):
        """새 인물을 캐시에 추가"""
        with self._lock:
            self.persons[person['id']] = person
    
    def _should_refresh(self, entity_type: str, force: bool = False) -> bool:
        """캐시 새로고침이 필요한지 확인"""
        if force:
            return True
        
        last_refresh = self.last_refresh.get(entity_type)
        if last_refresh is None:
            return True
        
        return datetime.now() - last_refresh > self.cache_ttl
    
    def _refresh_companies(self):
        """기업 캐시 새로고침"""
        logger.info("Refreshing company cache...")
        start_time = time.time()
        
        query = """
        MATCH (c:Company)
        RETURN c.id as id, c.name as name, c.aliases as aliases, 
               c.sector as sector, c.country as country,
               c.risk_score as risk_score
        ORDER BY c.name
        """
        
        try:
            results = session.run_query(query)
            self.companies.clear()
            
            for company in results:
                # aliases가 null이면 빈 리스트로 처리
                company['aliases'] = company.get('aliases') or []
                self.companies[company['id']] = company
            
            self.last_refresh['companies'] = datetime.now()
            elapsed = time.time() - start_time
            
            logger.info(f"Company cache refreshed: {len(self.companies)} companies in {elapsed:.2f}s")
            
        except Exception as e:
            logger.error(f"Failed to refresh company cache: {e}")
            raise
    
    def _refresh_persons(self):
        """인물 캐시 새로고침"""
        logger.info("Refreshing person cache...")
        start_time = time.time()
        
        query = """
        MATCH (p:Person)
        RETURN p.id as id, p.name as name, p.aliases as aliases,
               p.company as company, p.role as role,
               p.influence_score as influence_score
        ORDER BY p.name
        """
        
        try:
            results = session.run_query(query)
            self.persons.clear()
            
            for person in results:
                # aliases가 null이면 빈 리스트로 처리
                person['aliases'] = person.get('aliases') or []
                self.persons[person['id']] = person
            
            self.last_refresh['persons'] = datetime.now()
            elapsed = time.time() - start_time
            
            logger.info(f"Person cache refreshed: {len(self.persons)} persons in {elapsed:.2f}s")
            
        except Exception as e:
            logger.error(f"Failed to refresh person cache: {e}")
            raise
    
    def get_cache_stats(self) -> Dict:
        """캐시 통계 반환"""
        return {
            'companies_count': len(self.companies),
            'persons_count': len(self.persons),
            'last_refresh': {
                'companies': self.last_refresh['companies'].isoformat() if self.last_refresh['companies'] else None,
                'persons': self.last_refresh['persons'].isoformat() if self.last_refresh['persons'] else None
            },
            'cache_ttl_minutes': self.cache_ttl.total_seconds() / 60
        }
    
    def clear_cache(self):
        """캐시 초기화"""
        with self._lock:
            self.companies.clear()
            self.persons.clear()
            self.last_refresh = {'companies': None, 'persons': None}
            logger.info("Entity cache cleared")

# 전역 캐시 인스턴스
entity_cache = EntityCache(cache_ttl_minutes=30)