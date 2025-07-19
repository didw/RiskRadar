#!/bin/bash

# Feature Branch 생성 스크립트
# Usage: ./create-feature-branch.sh <service-name> <feature-name>

SERVICE=$1
FEATURE=$2

if [ -z "$SERVICE" ] || [ -z "$FEATURE" ]; then
    echo "Usage: $0 <service-name> <feature-name>"
    echo "Example: $0 data-service chosun-crawler"
    echo ""
    echo "Available services:"
    echo "  - data-service"
    echo "  - ml-service"
    echo "  - graph-service"
    echo "  - api-gateway"
    echo "  - web-ui"
    exit 1
fi

# 유효한 서비스 확인
VALID_SERVICES="data-service ml-service graph-service api-gateway web-ui"
if [[ ! " $VALID_SERVICES " =~ " $SERVICE " ]]; then
    echo "Error: Invalid service name '$SERVICE'"
    echo "Valid services: $VALID_SERVICES"
    exit 1
fi

BRANCH_NAME="feature/$SERVICE/$FEATURE"

echo "🌳 Creating feature branch: $BRANCH_NAME"

# develop 브랜치 최신화
echo "📥 Updating develop branch..."
git checkout develop
git pull origin develop

# Feature 브랜치 생성
echo "🔀 Creating new branch..."
git checkout -b "$BRANCH_NAME"

echo "✅ Feature branch created successfully!"
echo ""
echo "📝 Next steps:"
echo "1. Develop your feature in: services/$SERVICE/"
echo "2. Run tests: cd services/$SERVICE && pytest"
echo "3. Commit changes: git add . && git commit -m \"feat($SERVICE): your message\""
echo "4. Push branch: git push origin $BRANCH_NAME"
echo "5. Create PR: gh pr create --base develop"
echo ""
echo "⏰ Remember: Daily integration at 14:00!"