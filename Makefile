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

install:
	pip install -r requirements.txt

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

docker-down:
	docker-compose down

migrate:
	alembic upgrade head

run-api:
	python -m modules.ab_testing.api.main

run-ui:
	streamlit run modules/ab_testing/ui/app.py
