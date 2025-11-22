.PHONY: help install dev start stop restart logs test clean

help:
	@echo "NEXUS Webhooks Module - Available Commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make dev          - Run in development mode"
	@echo "  make start        - Start all services with Docker Compose"
	@echo "  make stop         - Stop all services"
	@echo "  make restart      - Restart all services"
	@echo "  make logs         - View logs"
	@echo "  make test         - Run tests"
	@echo "  make clean        - Clean up containers and volumes"
	@echo "  make db-init      - Initialize database"
	@echo "  make db-migrate   - Run database migrations"

install:
	pip install -r requirements.txt

dev:
	uvicorn modules.webhooks.api.main:app --reload --host 0.0.0.0 --port 8000

start:
	docker-compose up -d
	@echo "Services started!"
	@echo "API: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"
	@echo "Streamlit UI: http://localhost:8501"

stop:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

test:
	pytest tests/ -v

clean:
	docker-compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

db-init:
	python -c "from modules.webhooks.models.base import init_db; init_db()"

db-migrate:
	alembic upgrade head
