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

install:
	pip install -r requirements.txt

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
