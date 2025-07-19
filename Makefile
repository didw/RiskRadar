# RiskRadar Makefile
# 개발 및 운영을 위한 명령어 모음

.PHONY: help
help: ## 도움말 표시
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

# ==================== 개발 환경 ====================

.PHONY: dev-setup
dev-setup: ## 개발 환경 초기 설정
	@echo "🔧 개발 환경 설정 중..."
	@cp .env.example .env || true
	@docker-compose pull
	@make install-all
	@echo "✅ 개발 환경 설정 완료!"

.PHONY: dev-run
dev-run: ## 개발 환경 실행 (Sprint 0)
	@echo "🚀 개발 환경 시작..."
	docker-compose up -d
	@echo "✅ 서비스가 시작되었습니다!"
	@echo "📋 서비스 상태 확인: make status"
	@echo "🌐 Web UI: http://localhost:3000"
	@echo "📊 GraphQL: http://localhost:4000/graphql"

.PHONY: dev-stop
dev-stop: ## 개발 환경 중지
	docker-compose down

.PHONY: dev-clean
dev-clean: ## 개발 환경 초기화 (볼륨 포함)
	docker-compose down -v
	rm -rf node_modules services/*/node_modules
	rm -rf services/*/__pycache__ services/*/.pytest_cache

# ==================== 서비스 관리 ====================

.PHONY: install-all
install-all: ## 모든 서비스 의존성 설치
	@echo "📦 의존성 설치 중..."
	@make install-data-service
	@make install-ml-service
	@make install-graph-service
	@make install-api-gateway
	@make install-web-ui

.PHONY: install-data-service
install-data-service:
	cd services/data-service && pip install -r requirements.txt || true

.PHONY: install-ml-service
install-ml-service:
	cd services/ml-service && pip install -r requirements.txt || true

.PHONY: install-graph-service
install-graph-service:
	cd services/graph-service && pip install -r requirements.txt || true

.PHONY: install-api-gateway
install-api-gateway:
	cd services/api-gateway && npm install || true

.PHONY: install-web-ui
install-web-ui:
	cd services/web-ui && npm install || true

# ==================== 빌드 ====================

.PHONY: build-all
build-all: ## 모든 서비스 Docker 이미지 빌드
	@echo "🔨 Docker 이미지 빌드 중..."
	docker-compose build

.PHONY: build-data-service
build-data-service: ## Data Service 빌드
	docker-compose build data-service

.PHONY: build-ml-service
build-ml-service: ## ML Service 빌드
	docker-compose build ml-service

.PHONY: build-graph-service
build-graph-service: ## Graph Service 빌드
	docker-compose build graph-service

.PHONY: build-api-gateway
build-api-gateway: ## API Gateway 빌드
	docker-compose build api-gateway

.PHONY: build-web-ui
build-web-ui: ## Web UI 빌드
	docker-compose build web-ui

# ==================== 개별 서비스 실행 ====================

.PHONY: run-data-service
run-data-service: ## Data Service만 실행
	docker-compose up -d kafka zookeeper
	docker-compose up data-service

.PHONY: run-ml-service
run-ml-service: ## ML Service만 실행
	docker-compose up -d kafka zookeeper
	docker-compose up ml-service

.PHONY: run-graph-service
run-graph-service: ## Graph Service만 실행
	docker-compose up -d kafka zookeeper neo4j
	docker-compose up graph-service

.PHONY: run-api-gateway
run-api-gateway: ## API Gateway만 실행
	docker-compose up api-gateway

.PHONY: run-web-ui
run-web-ui: ## Web UI만 실행
	docker-compose up web-ui

# ==================== 테스트 ====================

.PHONY: test
test: ## 모든 단위 테스트 실행
	@echo "🧪 단위 테스트 실행 중..."
	cd services/data-service && pytest tests/unit/ || true
	cd services/ml-service && pytest tests/unit/ || true
	cd services/graph-service && pytest tests/unit/ || true
	cd services/api-gateway && npm test || true
	cd services/web-ui && npm test || true

.PHONY: test-integration
test-integration: ## 통합 테스트 실행
	@echo "🔗 통합 테스트 실행 중..."
	cd integration && make test-all

.PHONY: test-e2e
test-e2e: ## E2E 테스트 실행
	@echo "🌐 E2E 테스트 실행 중..."
	cd integration && make test-e2e

# ==================== 코드 품질 ====================

.PHONY: lint
lint: ## 린트 실행
	@echo "🔍 코드 검사 중..."
	cd services/data-service && ruff check . || true
	cd services/ml-service && ruff check . || true
	cd services/graph-service && ruff check . || true
	cd services/api-gateway && npm run lint || true
	cd services/web-ui && npm run lint || true

.PHONY: format
format: ## 코드 포맷팅
	@echo "✨ 코드 포맷팅 중..."
	cd services/data-service && black . || true
	cd services/ml-service && black . || true
	cd services/graph-service && black . || true
	cd services/api-gateway && npm run format || true
	cd services/web-ui && npm run format || true

# ==================== 모니터링 ====================

.PHONY: status
status: ## 서비스 상태 확인
	@echo "📊 서비스 상태:"
	@docker-compose ps
	@echo "\n🏥 Health 체크:"
	@curl -s http://localhost:8001/health | jq '.' || echo "❌ Data Service"
	@curl -s http://localhost:8002/health | jq '.' || echo "❌ ML Service"
	@curl -s http://localhost:8003/health | jq '.' || echo "❌ Graph Service"
	@curl -s http://localhost:4000/health | jq '.' || echo "❌ API Gateway"
	@curl -s http://localhost:3000 > /dev/null && echo "✅ Web UI" || echo "❌ Web UI"

.PHONY: logs
logs: ## 모든 서비스 로그 확인
	docker-compose logs -f

.PHONY: logs-data
logs-data: ## Data Service 로그
	docker-compose logs -f data-service

.PHONY: logs-ml
logs-ml: ## ML Service 로그
	docker-compose logs -f ml-service

.PHONY: logs-graph
logs-graph: ## Graph Service 로그
	docker-compose logs -f graph-service

.PHONY: logs-api
logs-api: ## API Gateway 로그
	docker-compose logs -f api-gateway

.PHONY: logs-web
logs-web: ## Web UI 로그
	docker-compose logs -f web-ui

# ==================== 데이터베이스 ====================

.PHONY: neo4j-shell
neo4j-shell: ## Neo4j 쉘 접속
	docker-compose exec neo4j cypher-shell -u neo4j -p password

.PHONY: kafka-topics
kafka-topics: ## Kafka 토픽 목록
	docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092

.PHONY: kafka-consumer
kafka-consumer: ## Kafka 메시지 확인 (raw-news)
	docker-compose exec kafka kafka-console-consumer \
		--bootstrap-server localhost:9092 \
		--topic raw-news \
		--from-beginning

# ==================== Sprint 0 데모 ====================

.PHONY: demo-sprint0
demo-sprint0: ## Sprint 0 데모 실행
	@echo "🎬 Sprint 0 데모 시작..."
	@echo "1️⃣ Mock 뉴스 생성 중..."
	@curl -X POST http://localhost:8001/generate-mock-news
	@echo "\n\n2️⃣ 3초 대기 중..."
	@sleep 3
	@echo "3️⃣ GraphQL 쿼리 실행..."
	@curl -s http://localhost:4000/graphql \
		-H "Content-Type: application/json" \
		-d '{"query":"{ companies { name riskScore newsCount } }"}' | jq '.'
	@echo "\n✅ 데모 완료! Web UI 확인: http://localhost:3000"

# ==================== 유틸리티 ====================

.PHONY: clean-docker
clean-docker: ## Docker 정리 (사용하지 않는 이미지/컨테이너)
	docker system prune -af

.PHONY: backup
backup: ## 데이터 백업
	@echo "💾 백업 생성 중..."
	@mkdir -p backups/$(shell date +%Y%m%d)
	@docker-compose exec neo4j neo4j-admin dump --to=/backups/graph.dump
	@echo "✅ 백업 완료: backups/$(shell date +%Y%m%d)/"

.PHONY: version
version: ## 버전 정보 표시
	@echo "RiskRadar v0.1.0 (Sprint 0)"
	@echo "Docker: $(shell docker --version)"
	@echo "Docker Compose: $(shell docker-compose --version)"
	@echo "Node.js: $(shell node --version 2>/dev/null || echo 'Not installed')"
	@echo "Python: $(shell python --version 2>/dev/null || echo 'Not installed')"

# ==================== 개발 단축키 ====================

.PHONY: up
up: dev-run ## docker-compose up 단축키

.PHONY: down
down: dev-stop ## docker-compose down 단축키

.PHONY: restart
restart: ## 서비스 재시작
	@make down
	@make up

.PHONY: fresh
fresh: ## 클린 재시작 (볼륨 삭제)
	@make dev-clean
	@make dev-setup
	@make dev-run