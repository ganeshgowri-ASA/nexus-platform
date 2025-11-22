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

install:
	pip install -r requirements.txt

<<<<<<< HEAD
<<<<<<< HEAD
test:
	pytest tests/ -v --cov=search --cov-report=html

lint:
	flake8 search/ tests/
	mypy search/

format:
	black search/ tests/ examples/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
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

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d
>>>>>>> origin/claude/ab-testing-module-01D3o2ivEGbVpUmsgesHtDjA

docker-down:
	docker-compose down

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
