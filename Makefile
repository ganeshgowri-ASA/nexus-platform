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

install:
	pip install -r requirements.txt

dev:
	uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest tests/ -v --cov=.

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

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
