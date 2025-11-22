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

install:
	pip install -r requirements.txt

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
