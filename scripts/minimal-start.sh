#!/bin/bash
# 모듈별 최소 환경 실행 스크립트

SERVICE=$1

# 색상 정의
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

case $SERVICE in
  "data")
    echo -e "${BLUE}Starting minimal environment for Data Service...${NC}"
    docker-compose -f docker-compose.minimal.yml up kafka zookeeper redis -d
    echo -e "${GREEN}✅ Data Service 환경 준비 완료${NC}"
    echo "   - Kafka: localhost:9092"
    echo "   - Redis: localhost:6379"
    ;;
  "ml")
    echo -e "${BLUE}Starting minimal environment for ML Service...${NC}"
    docker-compose -f docker-compose.minimal.yml up kafka zookeeper -d
    echo -e "${GREEN}✅ ML Service 환경 준비 완료${NC}"
    echo "   - Kafka: localhost:9092"
    ;;
  "graph")
    echo -e "${BLUE}Starting minimal environment for Graph Service...${NC}"
    docker-compose -f docker-compose.minimal.yml up kafka zookeeper neo4j -d
    echo -e "${GREEN}✅ Graph Service 환경 준비 완료${NC}"
    echo "   - Kafka: localhost:9092"
    echo "   - Neo4j: http://localhost:7474"
    ;;
  "api")
    echo -e "${BLUE}Starting minimal environment for API Gateway...${NC}"
    docker-compose -f docker-compose.minimal.yml up redis -d
    echo -e "${GREEN}✅ API Gateway 환경 준비 완료${NC}"
    echo "   - Redis: localhost:6379"
    ;;
  "web")
    echo -e "${GREEN}✅ Web UI는 독립 실행 가능${NC}"
    echo "   cd services/web-ui && npm run dev"
    ;;
  "stop")
    echo -e "${BLUE}Stopping all minimal services...${NC}"
    docker-compose -f docker-compose.minimal.yml down
    echo -e "${GREEN}✅ 모든 서비스 중지 완료${NC}"
    ;;
  *)
    echo "Usage: $0 [data|ml|graph|api|web|stop]"
    echo ""
    echo "Examples:"
    echo "  $0 data   # Start minimal services for Data Service"
    echo "  $0 ml     # Start minimal services for ML Service"
    echo "  $0 graph  # Start minimal services for Graph Service"
    echo "  $0 api    # Start minimal services for API Gateway"
    echo "  $0 web    # Show Web UI start command"
    echo "  $0 stop   # Stop all minimal services"
    exit 1
    ;;
esac