#!/bin/bash

echo "🚀 RiskRadar Quick Start - Thin Vertical Slice"
echo "============================================="

# Kafka 토픽 생성 함수
create_kafka_topics() {
    echo "📋 Kafka 토픽 생성 중..."
    docker exec riskradar-kafka kafka-topics --create --if-not-exists --topic raw-news --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
    docker exec riskradar-kafka kafka-topics --create --if-not-exists --topic enriched-news --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
    echo "✅ Kafka 토픽 생성 완료"
}

# 1. 인프라 서비스만 먼저 시작
echo "1️⃣ 인프라 서비스 시작 (Kafka, Neo4j, Redis)..."
docker-compose up -d zookeeper kafka neo4j redis

# 인프라가 준비될 때까지 대기
echo "⏳ 인프라 준비 중... (30초)"
sleep 30

# Kafka 토픽 생성
create_kafka_topics

# 2. 애플리케이션 서비스 시작
echo "2️⃣ 애플리케이션 서비스 시작..."
docker-compose up -d data-service ml-service graph-service api-gateway web-ui

# 서비스가 준비될 때까지 대기
echo "⏳ 서비스 준비 중... (20초)"
sleep 20

# 3. Health Check
echo "3️⃣ Health Check 수행..."
echo ""

services=("data-service:8001" "ml-service:8002" "graph-service:8003" "api-gateway:8004" "web-ui:3000")

for service in "${services[@]}"; do
    IFS=':' read -r name port <<< "$service"
    echo -n "🔍 $name: "
    if curl -s -f "http://localhost:$port/health" > /dev/null; then
        echo "✅ Healthy"
    else
        echo "❌ Not responding"
    fi
done

echo ""
echo "============================================="
echo "🎉 시스템 준비 완료!"
echo ""
echo "📌 접속 정보:"
echo "  - Web UI: http://localhost:3000"
echo "  - GraphQL: http://localhost:8004/graphql"
echo "  - Neo4j: http://localhost:7474 (neo4j/password)"
echo ""
echo "📌 테스트:"
echo "  - Web UI에서 'Simulate News' 버튼 클릭"
echo "  - 또는: curl -X POST http://localhost:8001/simulate-news"
echo ""
echo "📌 로그 확인:"
echo "  - docker-compose logs -f [service-name]"
echo ""