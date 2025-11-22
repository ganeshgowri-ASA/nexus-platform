# NEXUS API Gateway - Makefile

.PHONY: help install dev test clean run docker-build docker-up docker-down db-init db-migrate

help:
	@echo "NEXUS API Gateway - Available commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make dev          - Install development dependencies"
	@echo "  make test         - Run tests"
	@echo "  make clean        - Clean temporary files"
	@echo "  make run          - Run the API Gateway"
	@echo "  make run-ui       - Run the Admin UI"
	@echo "  make docker-build - Build Docker images"
	@echo "  make docker-up    - Start Docker containers"
	@echo "  make docker-down  - Stop Docker containers"
	@echo "  make db-init      - Initialize database"
	@echo "  make db-migrate   - Run database migrations"
	@echo "  make format       - Format code with black"
	@echo "  make lint         - Lint code with flake8"

install:
	pip install -r requirements.txt

dev:
	pip install -r requirements.txt
	pip install -e .

test:
	pytest tests/ -v

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/

run:
	python -m uvicorn modules.api_gateway.app.main:app --reload --host 0.0.0.0 --port 8000

run-ui:
	streamlit run ui/admin.py --server.port=8501

docker-build:
	docker-compose -f nginx/docker-compose.yml build

docker-up:
	docker-compose -f nginx/docker-compose.yml up -d

docker-down:
	docker-compose -f nginx/docker-compose.yml down

docker-logs:
	docker-compose -f nginx/docker-compose.yml logs -f

db-init:
	python -c "from modules.api_gateway.database import init_db; init_db()"

db-migrate:
	alembic upgrade head

format:
	black .

lint:
	flake8 .
	mypy .
