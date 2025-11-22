<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
.PHONY: help install test lint format clean docker-up docker-down init-search

help:
	@echo "Nexus Search - Available commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linters"
	@echo "  make format       - Format code"
	@echo "  make clean        - Clean cache files"
	@echo "  make docker-up    - Start Docker services"
	@echo "  make docker-down  - Stop Docker services"
	@echo "  make init-search  - Initialize search indices"
=======
.PHONY: help install dev-install test lint format clean docker-build docker-up docker-down migrate

help:
	@echo "NEXUS A/B Testing Module - Available Commands"
	@echo "=============================================="
	@echo "install          - Install production dependencies"
	@echo "dev-install      - Install development dependencies"
	@echo "test             - Run tests with coverage"
	@echo "test-unit        - Run unit tests only"
	@echo "test-integration - Run integration tests only"
	@echo "lint             - Run code linters"
	@echo "format           - Format code with black and ruff"
	@echo "clean            - Clean up generated files"
	@echo "docker-build     - Build Docker images"
	@echo "docker-up        - Start Docker containers"
	@echo "docker-down      - Stop Docker containers"
	@echo "migrate          - Run database migrations"
	@echo "run-api          - Run FastAPI server"
	@echo "run-ui           - Run Streamlit UI"
>>>>>>> origin/claude/ab-testing-module-01D3o2ivEGbVpUmsgesHtDjA
=======
.PHONY: help install dev-install build up down restart logs clean test migrate

help:
	@echo "NEXUS Scheduler - Available Commands:"
	@echo ""
	@echo "  make install       - Install dependencies"
	@echo "  make dev-install   - Install development dependencies"
	@echo "  make build         - Build Docker containers"
	@echo "  make up            - Start all services"
	@echo "  make down          - Stop all services"
	@echo "  make restart       - Restart all services"
	@echo "  make logs          - View logs"
	@echo "  make migrate       - Run database migrations"
	@echo "  make test          - Run tests"
	@echo "  make clean         - Clean up containers and volumes"
	@echo ""
>>>>>>> origin/claude/build-scheduler-module-01SggaZRDvso4oULkWNKGR2U
=======
.PHONY: help install dev test clean docker-build docker-up docker-down init-db seed-data

help:
	@echo "NEXUS Platform - Makefile Commands"
	@echo "=================================="
	@echo "install        Install dependencies"
	@echo "dev            Run development server"
	@echo "test           Run tests"
	@echo "clean          Clean temporary files"
	@echo "docker-build   Build Docker images"
	@echo "docker-up      Start Docker containers"
	@echo "docker-down    Stop Docker containers"
	@echo "init-db        Initialize database"
	@echo "seed-data      Seed sample data"
	@echo "worker         Start Celery worker"
	@echo "flower         Start Flower monitoring"
	@echo "streamlit      Start Streamlit UI"
>>>>>>> origin/claude/batch-processing-module-01PCraqtfpn2xgwyYUuEev97

install:
	pip install -r requirements.txt

<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
test:
	pytest tests/ -v --cov=search --cov-report=html

lint:
	flake8 search/ tests/
	mypy search/

format:
	black search/ tests/ examples/
=======
dev:
	uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest tests/ -v --cov=.
>>>>>>> origin/claude/batch-processing-module-01PCraqtfpn2xgwyYUuEev97

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
<<<<<<< HEAD
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache htmlcov .coverage

docker-up:
	docker-compose up -d
	@echo "Waiting for services to be ready..."
	@sleep 10
	@echo "Services are ready!"
=======
dev-install:
	pip install -r requirements.txt
	pip install -e ".[dev]"

test:
	pytest --cov=modules/ab_testing --cov-report=term-missing --cov-report=html

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

lint:
	ruff check modules/ tests/
	mypy modules/

format:
	black modules/ tests/
	ruff check --fix modules/ tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
=======
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info
>>>>>>> origin/claude/batch-processing-module-01PCraqtfpn2xgwyYUuEev97
=======
.PHONY: help install dev test lint format clean docker-build docker-up docker-down migrate init-db

help:
	@echo "NEXUS Platform - Available Commands:"
	@echo ""
	@echo "Setup:"
	@echo "  make install       Install dependencies"
	@echo "  make dev           Install development dependencies"
	@echo "  make init-db       Initialize database"
	@echo ""
	@echo "Development:"
	@echo "  make api           Run FastAPI server"
	@echo "  make dashboard     Run Streamlit dashboard"
	@echo "  make celery        Run Celery worker"
	@echo "  make flower        Run Flower monitoring"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  make test          Run test suite"
	@echo "  make test-cov      Run tests with coverage"
	@echo "  make lint          Run linters"
	@echo "  make format        Format code"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build  Build Docker images"
	@echo "  make docker-up     Start all services"
	@echo "  make docker-down   Stop all services"
	@echo "  make docker-logs   View logs"
	@echo ""
	@echo "Database:"
	@echo "  make migrate       Run database migrations"
	@echo "  make migration     Create new migration"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean         Remove generated files"
	@echo ""

install:
	pip install --upgrade pip
	pip install -r requirements.txt

dev:
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install -e .

init-db:
	python app.py init-db

api:
	python app.py api --reload

dashboard:
	python app.py streamlit

celery:
	python app.py celery-worker

flower:
	python app.py flower

test:
	pytest modules/analytics/tests/ -v

test-cov:
	pytest modules/analytics/tests/ -v \
		--cov=modules/analytics \
		--cov=shared \
		--cov-report=html \
		--cov-report=term-missing

test-unit:
	pytest modules/analytics/tests/unit/ -v

test-integration:
	pytest modules/analytics/tests/integration/ -v

lint:
	ruff check .
	mypy modules/ shared/

format:
	black .
	isort .
	ruff check --fix .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/
>>>>>>> origin/claude/nexus-analytics-module-01FAKqqMpzB1WpxsYvosEHzE

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d
<<<<<<< HEAD
<<<<<<< HEAD
>>>>>>> origin/claude/ab-testing-module-01D3o2ivEGbVpUmsgesHtDjA
=======
>>>>>>> origin/claude/batch-processing-module-01PCraqtfpn2xgwyYUuEev97
=======
>>>>>>> origin/claude/nexus-analytics-module-01FAKqqMpzB1WpxsYvosEHzE

docker-down:
	docker-compose down

<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
init-search:
	python scripts/init_search.py

run-examples:
	python examples/basic_search.py
=======
migrate:
	alembic upgrade head

run-api:
	python -m modules.ab_testing.api.main

run-ui:
	streamlit run modules/ab_testing/ui/app.py
>>>>>>> origin/claude/ab-testing-module-01D3o2ivEGbVpUmsgesHtDjA
=======
dev-install:
	pip install -r requirements.txt
	pip install pytest pytest-asyncio pytest-cov black flake8 mypy

build:
	docker-compose build

up:
	docker-compose up -d
	@echo "✅ Services started!"
	@echo "📊 API: http://localhost:8000"
	@echo "🎨 UI: http://localhost:8501"
	@echo "📚 Docs: http://localhost:8000/docs"

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

logs-api:
	docker-compose logs -f api

logs-worker:
	docker-compose logs -f celery_worker

logs-beat:
	docker-compose logs -f celery_beat

logs-ui:
	docker-compose logs -f streamlit

migrate:
	alembic upgrade head

migrate-create:
	alembic revision --autogenerate -m "$(message)"

migrate-downgrade:
	alembic downgrade -1

test:
	pytest modules/scheduler/tests/ -v --cov=modules/scheduler

clean:
	docker-compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +

format:
	black modules/scheduler/

lint:
	flake8 modules/scheduler/
	mypy modules/scheduler/
>>>>>>> origin/claude/build-scheduler-module-01SggaZRDvso4oULkWNKGR2U
=======
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
>>>>>>> origin/claude/build-orchestration-module-01Xe9ZAfD1FN1j7vgrCUBQ3a
=======
docker-logs:
	docker-compose logs -f

init-db:
	python scripts/init_db.py

seed-data:
	python scripts/seed_data.py

worker:
	celery -A tasks.celery_app worker --loglevel=info --concurrency=4

beat:
	celery -A tasks.celery_app beat --loglevel=info

flower:
	celery -A tasks.celery_app flower --port=5555

streamlit:
	streamlit run ui/main.py --server.port 8501

format:
	black .
	isort .

lint:
	flake8 .
	mypy .

all: clean install init-db docker-build docker-up
>>>>>>> origin/claude/batch-processing-module-01PCraqtfpn2xgwyYUuEev97
=======
docker-logs:
	docker-compose logs -f

docker-restart:
	docker-compose restart

docker-clean:
	docker-compose down -v
	docker system prune -f

migrate:
	alembic upgrade head

migration:
	@read -p "Enter migration message: " message; \
	alembic revision --autogenerate -m "$$message"

health:
	python app.py health-check

version:
	python app.py version

# Production deployment
deploy-prod:
	@echo "Deploying to production..."
	docker-compose -f docker-compose.prod.yml build
	docker-compose -f docker-compose.prod.yml up -d
	@echo "Deployment complete!"

# Database backup
backup-db:
	@echo "Creating database backup..."
	docker exec nexus-postgres pg_dump -U nexus nexus_analytics > backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "Backup complete!"

# Database restore
restore-db:
	@read -p "Enter backup file name: " file; \
	docker exec -i nexus-postgres psql -U nexus nexus_analytics < $$file

# Generate API documentation
docs:
	@echo "Generating API documentation..."
	cd docs && make html

# Security audit
security:
	pip-audit
	safety check
	bandit -r modules/ shared/
>>>>>>> origin/claude/nexus-analytics-module-01FAKqqMpzB1WpxsYvosEHzE
=======
# NEXUS Platform Makefile
# Convenient commands for development and deployment

.PHONY: help install setup dev clean test docker-build docker-up docker-down migrate db-upgrade db-downgrade

help:
	@echo "NEXUS Platform - Available Commands"
	@echo "===================================="
	@echo "setup          - Initial project setup"
	@echo "install        - Install all dependencies"
	@echo "dev            - Start development servers"
	@echo "docker-build   - Build Docker images"
	@echo "docker-up      - Start Docker containers"
	@echo "docker-down    - Stop Docker containers"
	@echo "migrate        - Create new database migration"
	@echo "db-upgrade     - Apply database migrations"
	@echo "db-downgrade   - Rollback database migration"
	@echo "test           - Run tests"
	@echo "clean          - Clean temporary files"
	@echo "lint           - Run linters"

# Initial setup
setup:
	@echo "Setting up NEXUS Platform..."
	cp .env.example .env
	@echo "Please update .env file with your configuration"
	mkdir -p uploads/assets
	@echo "Setup complete!"

# Install dependencies
install:
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && pip install -r requirements.txt
	@echo "Dependencies installed!"

# Development
dev:
	@echo "Starting NEXUS Platform in development mode..."
	docker-compose up

# Docker commands
docker-build:
	@echo "Building Docker images..."
	docker-compose build

docker-up:
	@echo "Starting Docker containers..."
	docker-compose up -d
	@echo "Services running at:"
	@echo "  - Backend API: http://localhost:8000"
	@echo "  - API Docs: http://localhost:8000/api/docs"
	@echo "  - Frontend: http://localhost:8501"

docker-down:
	@echo "Stopping Docker containers..."
	docker-compose down

docker-logs:
	docker-compose logs -f

# Database migrations
migrate:
	@echo "Creating new migration..."
	cd backend && alembic revision --autogenerate -m "$(m)"

db-upgrade:
	@echo "Applying database migrations..."
	cd backend && alembic upgrade head

db-downgrade:
	@echo "Rolling back database migration..."
	cd backend && alembic downgrade -1

db-reset:
	@echo "Resetting database..."
	docker-compose down -v
	docker-compose up -d postgres redis
	sleep 5
	$(MAKE) db-upgrade

# Testing
test:
	@echo "Running tests..."
	cd backend && pytest tests/ -v

test-coverage:
	@echo "Running tests with coverage..."
	cd backend && pytest tests/ --cov=app --cov-report=html

# Code quality
lint:
	@echo "Running linters..."
	cd backend && black app/ --check
	cd backend && flake8 app/
	cd backend && mypy app/

format:
	@echo "Formatting code..."
	cd backend && black app/

# Cleanup
clean:
	@echo "Cleaning temporary files..."
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	@echo "Cleanup complete!"

# Production
prod-build:
	@echo "Building for production..."
	docker-compose -f docker-compose.prod.yml build

prod-up:
	@echo "Starting production services..."
	docker-compose -f docker-compose.prod.yml up -d

prod-down:
	@echo "Stopping production services..."
	docker-compose -f docker-compose.prod.yml down
>>>>>>> origin/claude/build-campaign-manager-01KFpVYVNSuz2bfrpAMAZpwp
