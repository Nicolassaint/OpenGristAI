# OpenGristAI - Development Makefile
# Simple commands for common development tasks

.PHONY: help install dev-backend dev-frontend docker-up docker-down docker-logs test-backend test-unit test-integration test-api test-coverage test-frontend clean

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  OpenGristAI - Development Commands"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""

install: ## Install dependencies (backend + frontend)
	@echo "📦 Installing backend dependencies..."
	pip install -r backend/requirements.txt
	@echo "📦 Installing frontend dependencies..."
	cd frontend && npm install
	@echo "✅ All dependencies installed!"

dev-backend: ## Start backend development server (requires Python env activated)
	@./scripts/dev-backend.sh

dev-frontend: ## Start frontend development server
	@./scripts/dev-frontend.sh

docker-up: ## Start all services with Docker Compose
	@echo "🐳 Starting Docker Compose..."
	docker-compose up -d
	@echo "✅ Services started!"
	@echo "   Backend:  http://localhost:8000"
	@echo "   Frontend: http://localhost:5173"

docker-down: ## Stop all Docker services
	@echo "🛑 Stopping Docker Compose..."
	docker-compose down

docker-logs: ## Show Docker Compose logs
	docker-compose logs -f

test-backend: ## Run all backend tests (unit + integration, mocked only)
	@echo "🧪 Running backend tests..."
	cd backend && pytest -v

test-unit: ## Run only unit tests
	@echo "🧪 Running unit tests..."
	cd backend && pytest -v -m unit

test-integration: ## Run only integration tests (mocked)
	@echo "🧪 Running integration tests..."
	cd backend && pytest -v -m integration

test-api: ## Run integration tests with real Grist API (requires GRIST_API_KEY)
	@echo "🧪 Running integration tests with real API..."
	@echo "⚠️  Warning: This will create temporary data in your Grist document"
	cd backend && pytest -v -m requires_api

test-coverage: ## Run tests with coverage report
	@echo "🧪 Running tests with coverage..."
	cd backend && pytest --cov=app --cov-report=html --cov-report=term
	@echo "📊 Coverage report: backend/htmlcov/index.html"

test-frontend: ## Run frontend type checking
	@echo "🧪 Running frontend checks..."
	cd frontend && npm run check

lint-backend: ## Lint backend code
	@echo "🔍 Linting backend..."
	cd backend && ruff app/ tests/ || echo "⚠️  ruff not installed, skipping..."

format-backend: ## Format backend code
	@echo "✨ Formatting backend..."
	cd backend && black app/ tests/ || echo "⚠️  black not installed, skipping..."

lint-frontend: ## Lint frontend code
	@echo "🔍 Linting frontend..."
	cd frontend && npm run lint

format-frontend: ## Format frontend code
	@echo "✨ Formatting frontend..."
	cd frontend && npm run format

clean: ## Clean temporary files and caches
	@echo "🧹 Cleaning..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Cleaned!"
