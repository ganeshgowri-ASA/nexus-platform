.PHONY: help install dev test clean docker-up docker-down migrate

help:
	@echo "NEXUS Browser Automation - Available Commands"
	@echo "=============================================="
	@echo "install      - Install dependencies"
	@echo "dev          - Run development server"
	@echo "test         - Run tests"
	@echo "clean        - Clean up cache and temp files"
	@echo "docker-up    - Start all services with Docker"
	@echo "docker-down  - Stop all Docker services"
	@echo "migrate      - Run database migrations"
	@echo "celery       - Start Celery worker"
	@echo "beat         - Start Celery beat scheduler"
	@echo "flower       - Start Flower monitoring"
	@echo "streamlit    - Start Streamlit UI"

install:
	pip install -r requirements.txt
	playwright install chromium firefox webkit

dev:
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest tests/ -v --cov=. --cov-report=html

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache htmlcov .coverage

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

migrate:
	alembic upgrade head

celery:
	celery -A modules.browser_automation.tasks.celery_app worker --loglevel=info

beat:
	celery -A modules.browser_automation.tasks.celery_app beat --loglevel=info

flower:
	celery -A modules.browser_automation.tasks.celery_app flower --port=5555

streamlit:
	streamlit run ui/app.py
