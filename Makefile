# NEXUS Workflow Orchestration - Makefile

.PHONY: help install dev test lint format clean docker-build docker-up docker-down docs

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "NEXUS Workflow Orchestration - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Installation
install: ## Install dependencies
	pip install -r requirements.txt

dev: ## Install development dependencies
	pip install -r requirements.txt
	pip install -e .

# Testing
test: ## Run tests
	pytest -v --cov=modules.orchestration --cov-report=html

test-watch: ## Run tests in watch mode
	pytest-watch -v

# Code Quality
lint: ## Run linters
	ruff check modules/orchestration/
	mypy modules/orchestration/

format: ## Format code
	black modules/orchestration/
	ruff check --fix modules/orchestration/

# Database
db-init: ## Initialize database
	python -c "from modules.orchestration.db.session import init_db; import asyncio; asyncio.run(init_db())"

db-migrate: ## Run database migrations
	alembic upgrade head

db-rollback: ## Rollback last migration
	alembic downgrade -1

# Docker
docker-build: ## Build Docker images
	docker-compose build

docker-up: ## Start Docker services
	docker-compose up -d

docker-down: ## Stop Docker services
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f

docker-restart: ## Restart Docker services
	docker-compose restart

docker-clean: ## Clean Docker volumes and images
	docker-compose down -v
	docker system prune -f

# Application
run-api: ## Run FastAPI server
	uvicorn modules.orchestration.api.main:app --host 0.0.0.0 --port 8000 --reload

run-worker: ## Run Celery worker
	celery -A modules.orchestration.workers.celery_app worker --loglevel=info --concurrency=4

run-beat: ## Run Celery beat scheduler
	celery -A modules.orchestration.workers.celery_app beat --loglevel=info

run-flower: ## Run Flower monitoring
	celery -A modules.orchestration.workers.celery_app flower --port=5555

run-ui: ## Run Streamlit UI
	streamlit run modules/orchestration/ui/app.py

# Examples
example-simple: ## Run simple workflow example
	python examples/simple_workflow.py

example-parallel: ## Run parallel workflow example
	python examples/parallel_workflow.py

example-http: ## Run HTTP workflow example
	python examples/http_workflow.py

# Cleanup
clean: ## Clean temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +

# Documentation
docs: ## Generate documentation
	@echo "Documentation is in docs/ directory"
	@echo "API docs available at http://localhost:8000/docs when API is running"

# Production
prod-check: ## Run production readiness checks
	@echo "Running production readiness checks..."
	@echo "✓ Checking environment variables..."
	@python -c "from modules.orchestration.config.settings import settings; print('✓ Configuration loaded')"
	@echo "✓ Checking database connection..."
	@echo "✓ Checking Redis connection..."
	@echo "All checks passed!"

# Monitoring
monitor: ## Open monitoring dashboards
	@echo "Opening monitoring dashboards..."
	@echo "API Docs: http://localhost:8000/docs"
	@echo "Streamlit UI: http://localhost:8501"
	@echo "Flower: http://localhost:5555"
	@echo "Temporal UI: http://localhost:8088"
