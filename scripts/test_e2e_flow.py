#!/usr/bin/env python3
"""
Test end-to-end data flow for RiskRadar
"""
import json
import time
import requests
from kafka import KafkaProducer, KafkaConsumer
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
KAFKA_BOOTSTRAP_SERVERS = 'localhost:9092'
DATA_SERVICE_URL = 'http://localhost:8001'
ML_SERVICE_URL = 'http://localhost:8002'
GRAPH_SERVICE_URL = 'http://localhost:8003'
API_GATEWAY_URL = 'http://localhost:8004'

def test_data_service_health():
    """Test data service health"""
    try:
        response = requests.get(f"{DATA_SERVICE_URL}/health")
        if response.status_code == 200:
            logger.info("✓ Data Service is healthy")
            return True
        else:
            logger.error(f"✗ Data Service health check failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"✗ Data Service is not accessible: {e}")
        return False

def test_ml_service_health():
    """Test ML service health"""
    try:
        response = requests.get(f"{ML_SERVICE_URL}/api/v1/health")
        if response.status_code == 200:
            health = response.json()
            logger.info(f"✓ ML Service is healthy: {health}")
            return True
        else:
            logger.error(f"✗ ML Service health check failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"✗ ML Service is not accessible: {e}")
        return False

def test_ml_service_nlp():
    """Test ML service NLP processing"""
    try:
        test_text = "삼성전자가 새로운 반도체 공장 건설을 발표했습니다. 투자 규모는 10조원입니다."
        response = requests.post(
            f"{ML_SERVICE_URL}/api/v1/process",
            json={"text": test_text}
        )
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✓ ML Service NLP processing works: {result}")
            return True
        else:
            logger.error(f"✗ ML Service NLP processing failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"✗ ML Service NLP processing error: {e}")
        return False

def send_test_news_to_kafka():
    """Send test news to Kafka raw-news topic"""
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        test_news = {
            "id": f"test-{int(time.time())}",
            "title": "삼성전자, AI 반도체 시장 공략 강화",
            "content": "삼성전자가 AI 반도체 시장 공략을 위해 대규모 투자를 단행한다. 회사는 향후 3년간 50조원을 투자해 차세대 메모리 반도체 생산 능력을 확대할 계획이다.",
            "url": "https://example.com/news/samsung-ai-chip",
            "published_at": datetime.now().isoformat(),
            "source": "테스트 뉴스",
            "metadata": {
                "author": "테스트 기자",
                "category": "technology"
            }
        }
        
        producer.send('raw-news', test_news)
        producer.flush()
        logger.info(f"✓ Sent test news to Kafka: {test_news['id']}")
        return test_news['id']
    except Exception as e:
        logger.error(f"✗ Failed to send test news to Kafka: {e}")
        return None

def check_enriched_news(news_id, timeout=30):
    """Check if news was processed and enriched"""
    try:
        consumer = KafkaConsumer(
            'enriched-news',
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',
            consumer_timeout_ms=timeout * 1000
        )
        
        start_time = time.time()
        for message in consumer:
            enriched = message.value
            if enriched.get('original', {}).get('id') == news_id:
                logger.info(f"✓ Found enriched news: {json.dumps(enriched['nlp'], indent=2)}")
                consumer.close()
                return True
            
            if time.time() - start_time > timeout:
                break
        
        consumer.close()
        logger.error(f"✗ Enriched news not found within {timeout} seconds")
        return False
    except Exception as e:
        logger.error(f"✗ Failed to check enriched news: {e}")
        return False

def test_graph_service_query():
    """Test graph service GraphQL query"""
    try:
        query = """
        query {
            companies {
                id
                name
                riskScore
            }
        }
        """
        response = requests.post(
            f"{GRAPH_SERVICE_URL}/graphql",
            json={"query": query}
        )
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✓ Graph Service query works: {result}")
            return True
        else:
            logger.error(f"✗ Graph Service query failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"✗ Graph Service query error: {e}")
        return False

def test_api_gateway():
    """Test API Gateway"""
    try:
        # Test health endpoint
        response = requests.get(f"{API_GATEWAY_URL}/health")
        if response.status_code == 200:
            logger.info("✓ API Gateway is healthy")
        else:
            logger.error(f"✗ API Gateway health check failed: {response.status_code}")
            return False
            
        # Test GraphQL query
        query = """
        query {
            companies(first: 5) {
                edges {
                    node {
                        id
                        name
                        riskScore
                    }
                }
                totalCount
            }
        }
        """
        response = requests.post(
            f"{API_GATEWAY_URL}/graphql",
            json={"query": query}
        )
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✓ API Gateway GraphQL works: {result}")
            return True
        else:
            logger.error(f"✗ API Gateway GraphQL failed: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
    except Exception as e:
        logger.error(f"✗ API Gateway error: {e}")
        return False

def run_e2e_test():
    """Run end-to-end test"""
    logger.info("Starting end-to-end test...")
    
    # Phase 1: Check all services
    logger.info("\n=== Phase 1: Service Health Checks ===")
    services_ok = all([
        test_data_service_health(),
        test_ml_service_health(),
        test_graph_service_query(),
        test_api_gateway()
    ])
    
    if not services_ok:
        logger.error("Some services are not healthy. Aborting test.")
        return False
    
    # Phase 2: Test ML Service directly
    logger.info("\n=== Phase 2: ML Service Direct Test ===")
    test_ml_service_nlp()
    
    # Phase 3: Test data flow through Kafka
    logger.info("\n=== Phase 3: Kafka Data Flow Test ===")
    news_id = send_test_news_to_kafka()
    if news_id:
        time.sleep(2)  # Give services time to process
        check_enriched_news(news_id)
    
    # Phase 4: Test integrated query
    logger.info("\n=== Phase 4: Integrated Query Test ===")
    test_api_gateway()
    
    logger.info("\n=== End-to-End Test Complete ===")
    return True

if __name__ == "__main__":
    run_e2e_test()