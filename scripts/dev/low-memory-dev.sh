#!/bin/bash

# 2GB RAM 환경에서 개발하기 위한 스크립트
# 한번에 하나의 서비스만 실행

echo "🔧 Low Memory Development Mode"
echo "=============================="
echo "Available commands:"
echo "  1) Data Service only"
echo "  2) API Gateway only" 
echo "  3) Web UI only"
echo "  4) Stop all services"
echo ""

read -p "Select option (1-4): " choice

# 모든 서비스 중지
stop_all() {
    echo "Stopping all services..."
    pkill -f "python.*main.py" 2>/dev/null
    pkill -f "node.*index.js" 2>/dev/null
    pkill -f "next dev" 2>/dev/null
    echo "✅ All services stopped"
}

case $choice in
    1)
        stop_all
        echo "🚀 Starting Data Service..."
        cd services/data-service
        export USE_MOCK_KAFKA=true
        export MOCK_MODE=true
        python main.py &
        echo "✅ Data Service running on http://localhost:8001"
        ;;
    2)
        stop_all
        echo "🚀 Starting API Gateway..."
        cd services/api-gateway
        export USE_MOCK_SERVICES=true
        node index.js &
        echo "✅ API Gateway running on http://localhost:8004"
        ;;
    3)
        stop_all
        echo "🚀 Starting Web UI..."
        cd services/web-ui
        export NEXT_PUBLIC_USE_MOCK_API=true
        npm run dev &
        echo "✅ Web UI running on http://localhost:3000"
        ;;
    4)
        stop_all
        ;;
    *)
        echo "Invalid option"
        ;;
esac

echo ""
echo "💡 Tips:"
echo "- Only run one service at a time"
echo "- Use Mock mode to reduce memory"
echo "- Close browser tabs when not needed"
echo "- Use lightweight editor (nano/vim) instead of VS Code"