.PHONY: help install dev test lint format clean run-api run-ui run-celery docker-up docker-down

help:
	@echo "NEXUS Translation Module - Make Commands"
	@echo ""
	@echo "install       Install dependencies"
	@echo "dev           Install development dependencies"
	@echo "test          Run tests"
	@echo "lint          Run linters"
	@echo "format        Format code"
	@echo "clean         Clean temporary files"
	@echo "run-api       Run FastAPI server"
	@echo "run-ui        Run Streamlit UI"
	@echo "run-celery    Run Celery worker"
	@echo "docker-up     Start Docker containers"
	@echo "docker-down   Stop Docker containers"
	@echo "db-init       Initialize database"
	@echo "db-migrate    Run database migrations"

install:
	pip install -r requirements.txt

dev:
	pip install -r requirements.txt
	pip install pytest pytest-asyncio black flake8 mypy

test:
	pytest tests/ -v --cov=modules.translation

lint:
	flake8 modules/translation/
	mypy modules/translation/

format:
	black modules/translation/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache .mypy_cache .coverage htmlcov/

run-api:
	uvicorn modules.translation.main:app --host 0.0.0.0 --port 8000 --reload

run-ui:
	streamlit run modules/translation/ui/streamlit_app.py

run-celery:
	celery -A modules.translation.tasks.celery_tasks worker --loglevel=info

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

db-init:
	python -c "from modules.translation.models.database import init_db; init_db()"

db-migrate:
	alembic upgrade head

db-revision:
	alembic revision --autogenerate -m "$(msg)"
