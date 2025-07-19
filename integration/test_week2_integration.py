#!/usr/bin/env python3
"""
Week 2 Integration Test Script
Tests the complete data flow through all services
"""
import time
import json
import requests
from datetime import datetime
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import NoBrokersAvailable

class IntegrationTester:
    def __init__(self):
        self.kafka_bootstrap = 'localhost:9092'
        self.services = {
            'data-service': 'http://localhost:8001',
            'ml-service': 'http://localhost:8002',
            'graph-service': 'http://localhost:8003',
            'api-gateway': 'http://localhost:8004'
        }
        self.test_results = []
        
    def log(self, message):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def test_service_health(self):
        """Test 1: Check all services are healthy"""
        self.log("=== Test 1: Service Health Check ===")
        
        healthy_services = []
        for service, url in self.services.items():
            try:
                response = requests.get(f"{url}/health", timeout=5)
                if response.status_code == 200:
                    healthy_services.append(service)
                    self.log(f"✅ {service} is healthy")
                else:
                    self.log(f"❌ {service} returned status {response.status_code}")
            except Exception as e:
                self.log(f"❌ {service} health check failed: {e}")
                
        success = len(healthy_services) == len(self.services)
        self.test_results.append(("Service Health", success))
        return success
        
    def test_kafka_connectivity(self):
        """Test 2: Verify Kafka connectivity"""
        self.log("\n=== Test 2: Kafka Connectivity ===")
        
        try:
            # Test producer
            producer = KafkaProducer(
                bootstrap_servers=self.kafka_bootstrap,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            self.log("✅ Kafka producer connected")
            
            # Test consumer
            consumer = KafkaConsumer(
                'enriched-news',
                bootstrap_servers=self.kafka_bootstrap,
                auto_offset_reset='latest',
                consumer_timeout_ms=1000
            )
            self.log("✅ Kafka consumer connected")
            
            producer.close()
            consumer.close()
            
            self.test_results.append(("Kafka Connectivity", True))
            return True
            
        except NoBrokersAvailable:
            self.log("❌ No Kafka brokers available")
            self.test_results.append(("Kafka Connectivity", False))
            return False
        except Exception as e:
            self.log(f"❌ Kafka connectivity test failed: {e}")
            self.test_results.append(("Kafka Connectivity", False))
            return False
            
    def test_data_service_crawl(self):
        """Test 3: Test data service crawling"""
        self.log("\n=== Test 3: Data Service Crawling ===")
        
        try:
            # Trigger crawl
            response = requests.post(
                f"{self.services['data-service']}/api/v1/crawl",
                json={"source": "chosun", "limit": 1},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"✅ Crawl completed: {result.get('crawled_count', 0)} articles")
                self.test_results.append(("Data Service Crawl", True))
                return True
            else:
                self.log(f"❌ Crawl failed with status {response.status_code}")
                self.test_results.append(("Data Service Crawl", False))
                return False
                
        except Exception as e:
            self.log(f"❌ Data service crawl test failed: {e}")
            self.test_results.append(("Data Service Crawl", False))
            return False
            
    def test_ml_service_processing(self):
        """Test 4: Test ML service NER processing"""
        self.log("\n=== Test 4: ML Service NER Processing ===")
        
        test_text = "삼성전자가 새로운 반도체 공장을 건설합니다. 이재용 회장과 현대차 정의선 회장이 만났습니다."
        
        try:
            response = requests.post(
                f"{self.services['ml-service']}/api/v1/process",
                json={"text": test_text},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                entities = result.get('entities', [])
                
                self.log(f"✅ NLP processing completed:")
                self.log(f"   - Entities found: {len(entities)}")
                self.log(f"   - Sentiment: {result.get('sentiment', {}).get('label', 'N/A')}")
                self.log(f"   - Risk score: {result.get('risk_score', 0):.2f}")
                
                # Check if expected entities were found
                entity_texts = [e['text'] for e in entities]
                expected_entities = ['삼성전자', '이재용', '현대자동차', '정의선']
                found_expected = sum(1 for e in expected_entities if any(e in text for text in entity_texts))
                
                self.log(f"   - Found {found_expected}/{len(expected_entities)} expected entities")
                
                success = len(entities) > 0 and found_expected >= 2
                self.test_results.append(("ML Service Processing", success))
                return success
            else:
                self.log(f"❌ ML processing failed with status {response.status_code}")
                self.test_results.append(("ML Service Processing", False))
                return False
                
        except Exception as e:
            self.log(f"❌ ML service processing test failed: {e}")
            self.test_results.append(("ML Service Processing", False))
            return False
            
    def test_graph_service_storage(self):
        """Test 5: Test graph service data storage"""
        self.log("\n=== Test 5: Graph Service Storage ===")
        
        try:
            # Get graph statistics
            response = requests.get(
                f"{self.services['graph-service']}/api/v1/graph/stats",
                timeout=10
            )
            
            if response.status_code == 200:
                stats = response.json()
                self.log(f"✅ Graph statistics retrieved:")
                self.log(f"   - Total nodes: {stats.get('node_count', 0)}")
                self.log(f"   - Total relationships: {stats.get('relationship_count', 0)}")
                
                # Test company detail query
                test_company_id = "samsung-electronics"
                detail_response = requests.get(
                    f"{self.services['graph-service']}/api/v1/graph/companies/{test_company_id}",
                    timeout=10
                )
                
                if detail_response.status_code in [200, 404]:
                    if detail_response.status_code == 200:
                        self.log(f"✅ Company detail query successful")
                    else:
                        self.log(f"ℹ️ Company '{test_company_id}' not found (expected for fresh DB)")
                    
                    self.test_results.append(("Graph Service Storage", True))
                    return True
                else:
                    self.log(f"❌ Company detail query failed with status {detail_response.status_code}")
                    self.test_results.append(("Graph Service Storage", False))
                    return False
            else:
                self.log(f"❌ Graph stats query failed with status {response.status_code}")
                self.test_results.append(("Graph Service Storage", False))
                return False
                
        except Exception as e:
            self.log(f"❌ Graph service storage test failed: {e}")
            self.test_results.append(("Graph Service Storage", False))
            return False
            
    def test_api_gateway_graphql(self):
        """Test 6: Test API Gateway GraphQL"""
        self.log("\n=== Test 6: API Gateway GraphQL ===")
        
        graphql_query = """
        query {
            companies(limit: 5) {
                edges {
                    node {
                        id
                        name
                        industry
                        riskScore
                    }
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
            }
        }
        """
        
        try:
            response = requests.post(
                f"{self.services['api-gateway']}/graphql",
                json={"query": graphql_query},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if 'errors' not in result:
                    companies = result.get('data', {}).get('companies', {}).get('edges', [])
                    self.log(f"✅ GraphQL query successful:")
                    self.log(f"   - Companies returned: {len(companies)}")
                    
                    self.test_results.append(("API Gateway GraphQL", True))
                    return True
                else:
                    self.log(f"❌ GraphQL query returned errors: {result['errors']}")
                    self.test_results.append(("API Gateway GraphQL", False))
                    return False
            else:
                self.log(f"❌ GraphQL query failed with status {response.status_code}")
                self.test_results.append(("API Gateway GraphQL", False))
                return False
                
        except Exception as e:
            self.log(f"❌ API Gateway GraphQL test failed: {e}")
            self.test_results.append(("API Gateway GraphQL", False))
            return False
            
    def test_end_to_end_flow(self):
        """Test 7: End-to-end data flow test"""
        self.log("\n=== Test 7: End-to-End Data Flow ===")
        
        try:
            # Create test article
            test_article = {
                "id": f"test-article-{int(time.time())}",
                "title": "삼성전자, AI 반도체 개발 가속화",
                "content": "삼성전자가 차세대 AI 반도체 개발에 박차를 가하고 있다. 이재용 회장은 '반도체 초격차 전략'을 강조했다.",
                "url": "https://example.com/test-article",
                "published_at": datetime.now().isoformat(),
                "source": "test-source"
            }
            
            # Send to Kafka raw-news topic
            producer = KafkaProducer(
                bootstrap_servers=self.kafka_bootstrap,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            
            producer.send('raw-news', test_article)
            producer.flush()
            self.log("✅ Test article sent to raw-news topic")
            
            # Set up consumer for enriched-news
            consumer = KafkaConsumer(
                'enriched-news',
                bootstrap_servers=self.kafka_bootstrap,
                auto_offset_reset='latest',
                consumer_timeout_ms=30000,  # 30 second timeout
                value_deserializer=lambda m: json.loads(m.decode('utf-8'))
            )
            
            self.log("⏳ Waiting for enriched message...")
            
            # Wait for enriched message
            enriched_found = False
            start_time = time.time()
            
            for message in consumer:
                if time.time() - start_time > 30:
                    break
                    
                enriched = message.value
                if enriched.get('original', {}).get('id') == test_article['id']:
                    enriched_found = True
                    self.log("✅ Enriched message received:")
                    self.log(f"   - Entities: {len(enriched.get('nlp', {}).get('entities', []))}")
                    self.log(f"   - Sentiment: {enriched.get('nlp', {}).get('sentiment', {}).get('label', 'N/A')}")
                    self.log(f"   - Risk score: {enriched.get('nlp', {}).get('risk_score', 0)}")
                    break
            
            producer.close()
            consumer.close()
            
            if enriched_found:
                self.log("✅ End-to-end flow completed successfully")
                self.test_results.append(("End-to-End Flow", True))
                return True
            else:
                self.log("❌ Enriched message not received within timeout")
                self.test_results.append(("End-to-End Flow", False))
                return False
                
        except Exception as e:
            self.log(f"❌ End-to-end flow test failed: {e}")
            self.test_results.append(("End-to-End Flow", False))
            return False
            
    def run_all_tests(self):
        """Run all integration tests"""
        self.log("Starting Week 2 Integration Tests")
        self.log("=" * 60)
        
        # Run tests in sequence
        self.test_service_health()
        self.test_kafka_connectivity()
        self.test_data_service_crawl()
        self.test_ml_service_processing()
        self.test_graph_service_storage()
        self.test_api_gateway_graphql()
        self.test_end_to_end_flow()
        
        # Print summary
        self.log("\n" + "=" * 60)
        self.log("TEST SUMMARY:")
        self.log("=" * 60)
        
        passed = 0
        for test_name, result in self.test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name}: {status}")
            if result:
                passed += 1
                
        self.log(f"\nTotal: {passed}/{len(self.test_results)} tests passed")
        
        if passed == len(self.test_results):
            self.log("\n🎉 All integration tests passed!")
            self.log("Week 2 integration is working correctly!")
        elif passed > len(self.test_results) * 0.7:
            self.log("\n⚠️ Most tests passed, but some issues remain")
        else:
            self.log("\n❌ Integration tests failed - troubleshooting needed")
            
        return passed == len(self.test_results)

if __name__ == "__main__":
    tester = IntegrationTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)