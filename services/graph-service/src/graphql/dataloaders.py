"""GraphQL DataLoader 구현"""
from typing import List, Dict, Optional, Any
import logging
from aiodataloader import DataLoader

from src.neo4j.session import session

logger = logging.getLogger(__name__)


class CompanyDataLoader(DataLoader):
    """기업 데이터 로더"""
    
    async def batch_load_fn(self, company_ids: List[str]) -> List[Optional[Dict]]:
        """배치로 기업 데이터 로드"""
        try:
            query = """
            MATCH (c:Company)
            WHERE c.id IN $company_ids
            RETURN c.id as id, c
            """
            
            result = session.run_query(query, company_ids=company_ids)
            
            # ID별로 결과 매핑
            company_map = {row['id']: dict(row['c']) for row in result}
            
            # 요청된 순서대로 반환 (없는 경우 None)
            return [company_map.get(company_id) for company_id in company_ids]
            
        except Exception as e:
            logger.error(f"Error in CompanyDataLoader: {e}")
            return [None] * len(company_ids)


class PersonDataLoader(DataLoader):
    """인물 데이터 로더"""
    
    async def batch_load_fn(self, person_ids: List[str]) -> List[Optional[Dict]]:
        """배치로 인물 데이터 로드"""
        try:
            query = """
            MATCH (p:Person)
            WHERE p.id IN $person_ids
            RETURN p.id as id, p
            """
            
            result = session.run_query(query, person_ids=person_ids)
            
            person_map = {row['id']: dict(row['p']) for row in result}
            
            return [person_map.get(person_id) for person_id in person_ids]
            
        except Exception as e:
            logger.error(f"Error in PersonDataLoader: {e}")
            return [None] * len(person_ids)


class EventDataLoader(DataLoader):
    """이벤트 데이터 로더"""
    
    async def batch_load_fn(self, event_ids: List[str]) -> List[Optional[Dict]]:
        """배치로 이벤트 데이터 로드"""
        try:
            query = """
            MATCH (e:Event)
            WHERE e.id IN $event_ids
            RETURN e.id as id, e
            """
            
            result = session.run_query(query, event_ids=event_ids)
            
            event_map = {row['id']: dict(row['e']) for row in result}
            
            return [event_map.get(event_id) for event_id in event_ids]
            
        except Exception as e:
            logger.error(f"Error in EventDataLoader: {e}")
            return [None] * len(event_ids)


class RelationshipDataLoader(DataLoader):
    """관계 데이터 로더"""
    
    async def batch_load_fn(self, node_ids: List[str]) -> List[List[Dict]]:
        """배치로 관계 데이터 로드"""
        try:
            query = """
            MATCH (n)-[r]->(m)
            WHERE n.id IN $node_ids
            RETURN n.id as source_id, 
                   type(r) as rel_type,
                   properties(r) as rel_props,
                   m.id as target_id,
                   labels(m) as target_labels,
                   properties(m) as target_props
            """
            
            result = session.run_query(query, node_ids=node_ids)
            
            # 노드별로 관계 그룹화
            relationships_map = {}
            for row in result:
                source_id = row['source_id']
                if source_id not in relationships_map:
                    relationships_map[source_id] = []
                
                relationships_map[source_id].append({
                    'type': row['rel_type'],
                    'properties': row['rel_props'],
                    'target': {
                        'id': row['target_id'],
                        'labels': row['target_labels'],
                        'properties': row['target_props']
                    }
                })
            
            return [relationships_map.get(node_id, []) for node_id in node_ids]
            
        except Exception as e:
            logger.error(f"Error in RelationshipDataLoader: {e}")
            return [[] for _ in node_ids]


class CompanyCompetitorDataLoader(DataLoader):
    """기업 경쟁사 데이터 로더"""
    
    async def batch_load_fn(self, company_ids: List[str]) -> List[List[Dict]]:
        """배치로 경쟁사 데이터 로드"""
        try:
            query = """
            MATCH (c:Company)-[:COMPETES_WITH]->(competitor:Company)
            WHERE c.id IN $company_ids
            RETURN c.id as company_id, collect(competitor) as competitors
            """
            
            result = session.run_query(query, company_ids=company_ids)
            
            competitors_map = {row['company_id']: [dict(comp) for comp in row['competitors']] 
                             for row in result}
            
            return [competitors_map.get(company_id, []) for company_id in company_ids]
            
        except Exception as e:
            logger.error(f"Error in CompanyCompetitorDataLoader: {e}")
            return [[] for _ in company_ids]


class CompanyPartnerDataLoader(DataLoader):
    """기업 파트너 데이터 로더"""
    
    async def batch_load_fn(self, company_ids: List[str]) -> List[List[Dict]]:
        """배치로 파트너 데이터 로드"""
        try:
            query = """
            MATCH (c:Company)-[:PARTNERS_WITH]->(partner:Company)
            WHERE c.id IN $company_ids
            RETURN c.id as company_id, collect(partner) as partners
            """
            
            result = session.run_query(query, company_ids=company_ids)
            
            partners_map = {row['company_id']: [dict(partner) for partner in row['partners']] 
                          for row in result}
            
            return [partners_map.get(company_id, []) for company_id in company_ids]
            
        except Exception as e:
            logger.error(f"Error in CompanyPartnerDataLoader: {e}")
            return [[] for _ in company_ids]


class CompanyEmployeeDataLoader(DataLoader):
    """기업 직원 데이터 로더"""
    
    async def batch_load_fn(self, company_ids: List[str]) -> List[List[Dict]]:
        """배치로 직원 데이터 로드"""
        try:
            query = """
            MATCH (c:Company)<-[:WORKS_AT]-(person:Person)
            WHERE c.id IN $company_ids
            RETURN c.id as company_id, collect(person) as employees
            """
            
            result = session.run_query(query, company_ids=company_ids)
            
            employees_map = {row['company_id']: [dict(emp) for emp in row['employees']] 
                           for row in result}
            
            return [employees_map.get(company_id, []) for company_id in company_ids]
            
        except Exception as e:
            logger.error(f"Error in CompanyEmployeeDataLoader: {e}")
            return [[] for _ in company_ids]


class CompanyNewsDataLoader(DataLoader):
    """기업 뉴스 데이터 로더"""
    
    async def batch_load_fn(self, company_ids: List[str]) -> List[List[Dict]]:
        """배치로 뉴스 데이터 로드"""
        try:
            query = """
            MATCH (c:Company)<-[:MENTIONED_IN]-(news:NewsArticle)
            WHERE c.id IN $company_ids
            RETURN c.id as company_id, 
                   collect(news)[..10] as recent_news
            ORDER BY news.published_at DESC
            """
            
            result = session.run_query(query, company_ids=company_ids)
            
            news_map = {row['company_id']: [dict(news) for news in row['recent_news']] 
                       for row in result}
            
            return [news_map.get(company_id, []) for company_id in company_ids]
            
        except Exception as e:
            logger.error(f"Error in CompanyNewsDataLoader: {e}")
            return [[] for _ in company_ids]


class CompanyRiskDataLoader(DataLoader):
    """기업 리스크 데이터 로더"""
    
    async def batch_load_fn(self, company_ids: List[str]) -> List[List[Dict]]:
        """배치로 리스크 데이터 로드"""
        try:
            query = """
            MATCH (c:Company)<-[:AFFECTS]-(risk:Risk)
            WHERE c.id IN $company_ids
            RETURN c.id as company_id, collect(risk) as risks
            """
            
            result = session.run_query(query, company_ids=company_ids)
            
            risks_map = {row['company_id']: [dict(risk) for risk in row['risks']] 
                        for row in result}
            
            return [risks_map.get(company_id, []) for company_id in company_ids]
            
        except Exception as e:
            logger.error(f"Error in CompanyRiskDataLoader: {e}")
            return [[] for _ in company_ids]


class CompanyEventDataLoader(DataLoader):
    """기업 이벤트 데이터 로더"""
    
    async def batch_load_fn(self, company_ids: List[str]) -> List[List[Dict]]:
        """배치로 이벤트 데이터 로드"""
        try:
            query = """
            MATCH (c:Company)<-[:AFFECTS]-(event:Event)
            WHERE c.id IN $company_ids
            RETURN c.id as company_id, 
                   collect(event)[..20] as recent_events
            ORDER BY event.date DESC
            """
            
            result = session.run_query(query, company_ids=company_ids)
            
            events_map = {row['company_id']: [dict(event) for event in row['recent_events']] 
                         for row in result}
            
            return [events_map.get(company_id, []) for company_id in company_ids]
            
        except Exception as e:
            logger.error(f"Error in CompanyEventDataLoader: {e}")
            return [[] for _ in company_ids]


# DataLoader 인스턴스 생성 (싱글톤 패턴)
company_loader = CompanyDataLoader()
person_loader = PersonDataLoader()
event_loader = EventDataLoader()
relationship_loader = RelationshipDataLoader()
company_competitor_loader = CompanyCompetitorDataLoader()
company_partner_loader = CompanyPartnerDataLoader()
company_employee_loader = CompanyEmployeeDataLoader()
company_news_loader = CompanyNewsDataLoader()
company_risk_loader = CompanyRiskDataLoader()
company_event_loader = CompanyEventDataLoader()