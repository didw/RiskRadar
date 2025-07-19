#!/bin/bash

# Graph Service 성능 테스트 실행 스크립트

echo "==================================="
echo "Graph Service Performance Tests"
echo "==================================="

# 환경 변수 설정
export NEO4J_URI=${NEO4J_URI:-bolt://localhost:7687}
export NEO4J_USER=${NEO4J_USER:-neo4j}
export NEO4J_PASSWORD=${NEO4J_PASSWORD:-password}
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Neo4j 연결 확인
echo -e "\n1. Checking Neo4j connection..."
python -c "
from src.neo4j.driver import Neo4jDriver
try:
    driver = Neo4jDriver()
    driver.driver.verify_connectivity()
    print('✓ Neo4j connection successful')
except Exception as e:
    print(f'✗ Neo4j connection failed: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "Please ensure Neo4j is running and accessible."
    exit 1
fi

# 성능 테스트 실행
echo -e "\n2. Running performance tests..."
echo "================================"

# 쿼리 성능 테스트
echo -e "\n📊 Query Performance Tests:"
pytest tests/performance/test_query_performance.py -v -s -m performance

# 로드 성능 테스트
echo -e "\n📈 Load Performance Tests:"
pytest tests/performance/test_load_performance.py -v -s -m performance

# 결과 요약
echo -e "\n==================================="
echo "Performance Test Summary"
echo "==================================="

# 테스트 결과 수집
if [ -f .pytest_cache/v/cache/lastfailed ]; then
    echo -e "\n⚠️  Some tests failed. Check the output above for details."
else
    echo -e "\n✅ All performance tests passed!"
fi

# 성능 메트릭 요약
echo -e "\n📊 Key Performance Metrics:"
echo "- Index query: < 10ms"
echo "- 1-hop traversal: < 50ms"
echo "- Aggregation (5K nodes): < 100ms"
echo "- Message processing: > 3 msg/sec"
echo "- Batch write: > 200 nodes/sec"

echo -e "\n==================================="
echo "Performance tests completed!"
echo "===================================" 