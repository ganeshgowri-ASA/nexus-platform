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

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

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
