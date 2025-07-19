#!/usr/bin/env python3
"""
RiskRadar Daily Report Generator
Comprehensive daily report with all available data
"""

import json
import requests
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Any
import os

class DailyReportGenerator:
    def __init__(self):
        self.graphql_url = "http://localhost:8004/graphql"
        self.report_date = datetime.now()
        
    def query_graphql(self, query: str) -> Dict[str, Any]:
        """Execute GraphQL query"""
        try:
            response = requests.post(
                self.graphql_url,
                json={"query": query},
                headers={"Content-Type": "application/json"}
            )
            return response.json()
        except Exception as e:
            print(f"GraphQL Error: {e}")
            return {}
    
    def get_neo4j_stats(self) -> Dict[str, int]:
        """Get statistics from Neo4j"""
        stats = {}
        try:
            # Company count
            result = subprocess.run(
                ['docker', 'exec', '-i', 'riskradar-neo4j', 'cypher-shell', 
                 '-u', 'neo4j', '-p', 'riskradar123'],
                input=b'MATCH (c:Company) RETURN count(c) as count;',
                capture_output=True
            )
            if result.returncode == 0:
                output = result.stdout.decode().strip().split('\n')
                stats['companies'] = int(output[-1]) if output[-1].isdigit() else 0
            
            # News count
            result = subprocess.run(
                ['docker', 'exec', '-i', 'riskradar-neo4j', 'cypher-shell',
                 '-u', 'neo4j', '-p', 'riskradar123'],
                input=b'MATCH (n:News) RETURN count(n) as count;',
                capture_output=True
            )
            if result.returncode == 0:
                output = result.stdout.decode().strip().split('\n')
                stats['news'] = int(output[-1]) if output[-1].isdigit() else 0
                
            # Person count
            result = subprocess.run(
                ['docker', 'exec', '-i', 'riskradar-neo4j', 'cypher-shell',
                 '-u', 'neo4j', '-p', 'riskradar123'],
                input=b'MATCH (p:Person) RETURN count(p) as count;',
                capture_output=True
            )
            if result.returncode == 0:
                output = result.stdout.decode().strip().split('\n')
                stats['persons'] = int(output[-1]) if output[-1].isdigit() else 0
                
        except Exception as e:
            print(f"Neo4j Error: {e}")
            
        return stats
    
    def get_kafka_stats(self) -> Dict[str, int]:
        """Get Kafka topic statistics"""
        stats = {}
        try:
            # Raw news topic
            result = subprocess.run(
                ['docker', 'exec', 'riskradar-kafka', 
                 'kafka-run-class', 'kafka.tools.GetOffsetShell',
                 '--broker-list', 'localhost:9092', '--topic', 'raw-news'],
                capture_output=True
            )
            if result.returncode == 0:
                total = sum(int(line.split(':')[-1]) for line in result.stdout.decode().strip().split('\n') if ':' in line)
                stats['raw_news'] = total
                
            # Enriched news topic  
            result = subprocess.run(
                ['docker', 'exec', 'riskradar-kafka',
                 'kafka-run-class', 'kafka.tools.GetOffsetShell',
                 '--broker-list', 'localhost:9092', '--topic', 'enriched-news'],
                capture_output=True
            )
            if result.returncode == 0:
                total = sum(int(line.split(':')[-1]) for line in result.stdout.decode().strip().split('\n') if ':' in line)
                stats['enriched_news'] = total
                
        except Exception as e:
            print(f"Kafka Error: {e}")
            
        return stats
    
    def get_service_health(self) -> Dict[str, str]:
        """Check health of all services"""
        services = {
            'data-service': 'http://localhost:8001/health',
            'ml-service': 'http://localhost:8082/api/v1/health',
            'graph-service': 'http://localhost:8003/health',
            'api-gateway': 'http://localhost:8004/health'
        }
        
        health = {}
        for service, url in services.items():
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    health[service] = "🟢 Healthy"
                else:
                    health[service] = "🟡 Degraded"
            except:
                health[service] = "🔴 Down"
                
        return health
    
    def generate_report(self):
        """Generate comprehensive daily report"""
        print("=" * 80)
        print("RISKRADAR DAILY REPORT".center(80))
        print(f"Date: {self.report_date.strftime('%Y-%m-%d %H:%M:%S')}".center(80))
        print("=" * 80)
        print()
        
        # 1. System Health
        print("🏥 SYSTEM HEALTH STATUS")
        print("-" * 60)
        health = self.get_service_health()
        for service, status in health.items():
            print(f"  {service:<20} {status}")
        print()
        
        # 2. Data Statistics
        print("📊 DATA STATISTICS")
        print("-" * 60)
        
        # Neo4j stats
        neo4j_stats = self.get_neo4j_stats()
        print("  Graph Database:")
        print(f"    • Companies: {neo4j_stats.get('companies', 0)}")
        print(f"    • News Articles: {neo4j_stats.get('news', 0)}")
        print(f"    • Executives: {neo4j_stats.get('persons', 0)}")
        print()
        
        # Kafka stats
        kafka_stats = self.get_kafka_stats()
        print("  Message Queue:")
        print(f"    • Raw News Messages: {kafka_stats.get('raw_news', 0)}")
        print(f"    • Enriched News Messages: {kafka_stats.get('enriched_news', 0)}")
        print()
        
        # 3. Company Risk Overview
        print("🏢 COMPANY RISK OVERVIEW")
        print("-" * 60)
        
        # Query companies
        query = """
        {
            companies(first: 10) {
                edges {
                    node {
                        id
                        name
                        industry
                        riskScore
                    }
                }
                totalCount
            }
        }
        """
        
        result = self.query_graphql(query)
        if result and "data" in result and result["data"]["companies"]:
            companies = result["data"]["companies"]["edges"]
            total = result["data"]["companies"]["totalCount"]
            
            print(f"  Total Companies Monitored: {total}")
            print()
            print("  Top Risk Companies:")
            
            # Sort by risk score
            sorted_companies = sorted(
                [c["node"] for c in companies], 
                key=lambda x: x["riskScore"], 
                reverse=True
            )
            
            for i, company in enumerate(sorted_companies[:5], 1):
                print(f"    {i}. {company['name']:<30} Risk: {company['riskScore']}/10 ({company['industry']})")
        else:
            print("  No company data available")
        print()
        
        # 4. Processing Statistics
        print("⚙️  PROCESSING STATISTICS (Last 24 Hours)")
        print("-" * 60)
        print("  News Collection:")
        print("    • Target: 1,000 articles/hour")
        print(f"    • Actual: {kafka_stats.get('raw_news', 0)} total messages")
        print()
        print("  ML Processing:")
        print("    • Target: <10ms per article")
        print("    • NLP Pipeline: NER + Sentiment + Risk Scoring")
        print()
        
        # 5. Recommendations
        print("💡 RECOMMENDATIONS")
        print("-" * 60)
        
        if kafka_stats.get('raw_news', 0) < 100:
            print("  ⚠️  Low news volume detected. Consider:")
            print("     - Check crawler status")
            print("     - Verify news sources are accessible")
            print("     - Review rate limiting settings")
        else:
            print("  ✅ News collection operating normally")
            
        if any(status == "🔴 Down" for status in health.values()):
            print("  ⚠️  Some services are down. Immediate attention required.")
        
        print()
        print("=" * 80)
        print("Report generated by RiskRadar Daily Report Generator v1.0")
        print("Full analytics and ML insights available in Phase 2")
        print("=" * 80)

if __name__ == "__main__":
    generator = DailyReportGenerator()
    generator.generate_report()