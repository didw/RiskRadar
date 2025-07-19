#!/usr/bin/env python3
"""
Seed initial data into Neo4j for RiskRadar
"""
import os
from neo4j import GraphDatabase
import logging
from datetime import datetime, timedelta
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Neo4j connection settings
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

class Neo4jSeeder:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        
    def close(self):
        self.driver.close()
        
    def clear_database(self):
        """Clear existing data"""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            logger.info("Cleared existing data")
            
    def create_constraints(self):
        """Create constraints and indexes"""
        constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Company) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:News) REQUIRE n.id IS UNIQUE",
            "CREATE INDEX IF NOT EXISTS FOR (c:Company) ON (c.name)",
            "CREATE INDEX IF NOT EXISTS FOR (p:Person) ON (p.name)",
            "CREATE INDEX IF NOT EXISTS FOR (n:News) ON (n.published_at)"
        ]
        
        with self.driver.session() as session:
            for constraint in constraints:
                session.run(constraint)
                logger.info(f"Created: {constraint}")
                
    def seed_companies(self):
        """Seed sample companies"""
        companies = [
            {"id": "c1", "name": "삼성전자", "industry": "Technology", "risk_score": 0.3, "country": "Korea"},
            {"id": "c2", "name": "SK하이닉스", "industry": "Technology", "risk_score": 0.25, "country": "Korea"},
            {"id": "c3", "name": "현대자동차", "industry": "Automotive", "risk_score": 0.35, "country": "Korea"},
            {"id": "c4", "name": "LG화학", "industry": "Chemical", "risk_score": 0.4, "country": "Korea"},
            {"id": "c5", "name": "네이버", "industry": "Technology", "risk_score": 0.2, "country": "Korea"},
            {"id": "c6", "name": "카카오", "industry": "Technology", "risk_score": 0.22, "country": "Korea"},
            {"id": "c7", "name": "포스코", "industry": "Steel", "risk_score": 0.45, "country": "Korea"},
            {"id": "c8", "name": "KB금융", "industry": "Finance", "risk_score": 0.38, "country": "Korea"},
            {"id": "c9", "name": "신한금융", "industry": "Finance", "risk_score": 0.36, "country": "Korea"},
            {"id": "c10", "name": "셀트리온", "industry": "Pharmaceutical", "risk_score": 0.42, "country": "Korea"}
        ]
        
        with self.driver.session() as session:
            for company in companies:
                session.run(
                    """
                    CREATE (c:Company {
                        id: $id,
                        name: $name,
                        industry: $industry,
                        risk_score: $risk_score,
                        country: $country,
                        created_at: datetime(),
                        updated_at: datetime()
                    })
                    """,
                    **company
                )
            logger.info(f"Created {len(companies)} companies")
            
    def seed_relationships(self):
        """Seed company relationships"""
        relationships = [
            # Supply chain relationships
            ("c1", "c2", "SUPPLIES_TO", {"type": "semiconductor", "strength": 0.8}),
            ("c4", "c1", "SUPPLIES_TO", {"type": "battery", "strength": 0.7}),
            ("c4", "c3", "SUPPLIES_TO", {"type": "battery", "strength": 0.9}),
            
            # Investment relationships
            ("c1", "c5", "INVESTS_IN", {"amount": 1000000000, "percentage": 5.0}),
            ("c6", "c8", "INVESTS_IN", {"amount": 500000000, "percentage": 3.0}),
            
            # Partnership relationships
            ("c5", "c6", "PARTNERS_WITH", {"type": "strategic", "since": "2020"}),
            ("c8", "c9", "PARTNERS_WITH", {"type": "financial", "since": "2019"}),
            
            # Competition relationships
            ("c1", "c2", "COMPETES_WITH", {"market": "memory chips"}),
            ("c5", "c6", "COMPETES_WITH", {"market": "social media"}),
            ("c8", "c9", "COMPETES_WITH", {"market": "banking"})
        ]
        
        with self.driver.session() as session:
            for source, target, rel_type, props in relationships:
                query = f"""
                MATCH (s:Company {{id: $source}})
                MATCH (t:Company {{id: $target}})
                CREATE (s)-[r:{rel_type} $props]->(t)
                """
                session.run(query, source=source, target=target, props=props)
            logger.info(f"Created {len(relationships)} relationships")
            
    def seed_executives(self):
        """Seed company executives"""
        executives = [
            {"id": "p1", "name": "이재용", "company": "c1", "position": "CEO"},
            {"id": "p2", "name": "박정호", "company": "c2", "position": "CEO"},
            {"id": "p3", "name": "정의선", "company": "c3", "position": "CEO"},
            {"id": "p4", "name": "신학철", "company": "c4", "position": "CEO"},
            {"id": "p5", "name": "최수연", "company": "c5", "position": "CEO"},
            {"id": "p6", "name": "홍은택", "company": "c6", "position": "CEO"},
            {"id": "p7", "name": "최정우", "company": "c7", "position": "CEO"},
            {"id": "p8", "name": "윤종규", "company": "c8", "position": "CEO"},
            {"id": "p9", "name": "진옥동", "company": "c9", "position": "CEO"},
            {"id": "p10", "name": "서정진", "company": "c10", "position": "CEO"}
        ]
        
        with self.driver.session() as session:
            for exec in executives:
                session.run(
                    """
                    CREATE (p:Person {
                        id: $id,
                        name: $name,
                        created_at: datetime()
                    })
                    """,
                    id=exec["id"],
                    name=exec["name"]
                )
                
                session.run(
                    """
                    MATCH (p:Person {id: $person_id})
                    MATCH (c:Company {id: $company_id})
                    CREATE (p)-[:WORKS_AT {position: $position, since: date('2020-01-01')}]->(c)
                    """,
                    person_id=exec["id"],
                    company_id=exec["company"],
                    position=exec["position"]
                )
            logger.info(f"Created {len(executives)} executives")
            
    def seed_news(self):
        """Seed sample news articles"""
        news_templates = [
            {"title": "{company} 분기 실적 발표", "sentiment": "positive", "risk_impact": -0.05},
            {"title": "{company} 신제품 출시 계획", "sentiment": "positive", "risk_impact": -0.03},
            {"title": "{company} 리콜 사태 발생", "sentiment": "negative", "risk_impact": 0.15},
            {"title": "{company} 임원 구속 영장", "sentiment": "negative", "risk_impact": 0.20},
            {"title": "{company} 해외 진출 확대", "sentiment": "positive", "risk_impact": -0.08},
            {"title": "{company} 노사 분규 발생", "sentiment": "negative", "risk_impact": 0.10}
        ]
        
        companies = ["c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8", "c9", "c10"]
        
        with self.driver.session() as session:
            news_id = 1
            for i in range(30):  # Create 30 news articles
                company_id = random.choice(companies)
                template = random.choice(news_templates)
                
                # Get company name
                result = session.run("MATCH (c:Company {id: $id}) RETURN c.name as name", id=company_id)
                company_name = result.single()["name"]
                
                # Create news
                published_at = datetime.now() - timedelta(days=random.randint(0, 30))
                session.run(
                    """
                    CREATE (n:News {
                        id: $id,
                        title: $title,
                        content: $content,
                        sentiment: $sentiment,
                        risk_impact: $risk_impact,
                        published_at: $published_at,
                        source: $source
                    })
                    """,
                    id=f"news{news_id}",
                    title=template["title"].format(company=company_name),
                    content=f"Sample news content about {company_name}",
                    sentiment=template["sentiment"],
                    risk_impact=template["risk_impact"],
                    published_at=published_at,
                    source="Financial News"
                )
                
                # Link to company
                session.run(
                    """
                    MATCH (n:News {id: $news_id})
                    MATCH (c:Company {id: $company_id})
                    CREATE (n)-[:MENTIONS]->(c)
                    """,
                    news_id=f"news{news_id}",
                    company_id=company_id
                )
                
                news_id += 1
            logger.info("Created 30 news articles")
            
    def verify_data(self):
        """Verify seeded data"""
        with self.driver.session() as session:
            # Count nodes
            for label in ["Company", "Person", "News"]:
                result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
                count = result.single()["count"]
                logger.info(f"{label} nodes: {count}")
                
            # Count relationships
            result = session.run("MATCH ()-[r]->() RETURN type(r) as type, count(r) as count")
            for record in result:
                logger.info(f"{record['type']} relationships: {record['count']}")
                
    def run(self):
        """Run the seeding process"""
        try:
            logger.info("Starting Neo4j seeding...")
            self.clear_database()
            self.create_constraints()
            self.seed_companies()
            self.seed_relationships()
            self.seed_executives()
            self.seed_news()
            self.verify_data()
            logger.info("Neo4j seeding completed successfully!")
        except Exception as e:
            logger.error(f"Seeding failed: {e}")
            raise
        finally:
            self.close()

if __name__ == "__main__":
    seeder = Neo4jSeeder()
    seeder.run()