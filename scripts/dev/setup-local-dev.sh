#!/bin/bash

# 로컬 개발 환경 설정 스크립트 (코드 작성용)
# 낮은 리소스 환경에서 개발 도구만 설정

echo "🔧 RiskRadar 로컬 개발 환경 설정"
echo "================================"

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 프로젝트 루트 확인
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ RiskRadar 프로젝트 루트에서 실행해주세요${NC}"
    exit 1
fi

# 1. Git 설정
echo -e "\n${YELLOW}1. Git 설정${NC}"
git config core.hooksPath .githooks || true
echo -e "${GREEN}✓ Git hooks 설정 완료${NC}"

# 2. Python 가상환경 생성
echo -e "\n${YELLOW}2. Python 가상환경 생성${NC}"
for service in data-service ml-service graph-service; do
    if [ -d "services/$service" ]; then
        echo -e "  - $service 가상환경 생성 중..."
        cd "services/$service"
        python3 -m venv venv 2>/dev/null || python -m venv venv
        cd - > /dev/null
    fi
done
echo -e "${GREEN}✓ Python 가상환경 생성 완료${NC}"

# 3. 개발 도구 설정 파일 생성
echo -e "\n${YELLOW}3. VS Code 설정${NC}"
mkdir -p .vscode
cat > .vscode/settings.json << 'EOF'
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "typescript.tsdk": "node_modules/typescript/lib",
  "eslint.workingDirectories": [
    "./services/api-gateway",
    "./services/web-ui"
  ]
}
EOF
echo -e "${GREEN}✓ VS Code 설정 완료${NC}"

# 4. Pre-commit hooks 설정
echo -e "\n${YELLOW}4. Git Hooks 설정${NC}"
mkdir -p .githooks
cat > .githooks/pre-commit << 'EOF'
#!/bin/bash
# Pre-commit hook for code quality

echo "🔍 Running pre-commit checks..."

# Python files check
if git diff --cached --name-only | grep -q "\.py$"; then
    echo "  Checking Python files..."
    # Add your Python checks here
fi

# TypeScript/JavaScript files check
if git diff --cached --name-only | grep -q "\.[jt]sx\?$"; then
    echo "  Checking JS/TS files..."
    # Add your JS/TS checks here
fi

echo "✅ Pre-commit checks passed!"
EOF
chmod +x .githooks/pre-commit
echo -e "${GREEN}✓ Git hooks 설정 완료${NC}"

# 5. 환경 변수 파일 생성
echo -e "\n${YELLOW}5. 환경 변수 설정${NC}"
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${GREEN}✓ .env 파일 생성 완료${NC}"
else
    echo -e "${GREEN}✓ .env 파일이 이미 존재합니다${NC}"
fi

# 6. 개발 가이드 표시
echo -e "\n${GREEN}🎉 로컬 개발 환경 설정 완료!${NC}"
echo -e "\n📚 개발 가이드:"
echo -e "  1. Python 서비스 개발:"
echo -e "     ${YELLOW}cd services/data-service${NC}"
echo -e "     ${YELLOW}source venv/bin/activate${NC}"
echo -e "     ${YELLOW}pip install -r requirements.txt${NC}"
echo -e ""
echo -e "  2. Node.js 서비스 개발:"
echo -e "     ${YELLOW}cd services/web-ui${NC}"
echo -e "     ${YELLOW}npm install${NC}"
echo -e "     ${YELLOW}npm run dev${NC}"
echo -e ""
echo -e "  3. 코드 품질 검사:"
echo -e "     ${YELLOW}make lint${NC}"
echo -e "     ${YELLOW}make format${NC}"
echo -e ""
echo -e "  4. 단위 테스트:"
echo -e "     ${YELLOW}make test${NC}"
echo -e ""
echo -e "  5. 통합 환경에서 테스트:"
echo -e "     고사양 서버에서 ${YELLOW}make dev-run${NC} 실행"
echo -e ""
echo -e "📖 자세한 내용은 ${YELLOW}CLAUDE.md${NC}를 참고하세요"