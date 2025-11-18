# NEXUS Platform Makefile
# Convenient commands for development and deployment

.PHONY: help install setup dev clean test docker-build docker-up docker-down migrate db-upgrade db-downgrade

help:
	@echo "NEXUS Platform - Available Commands"
	@echo "===================================="
	@echo "setup          - Initial project setup"
	@echo "install        - Install all dependencies"
	@echo "dev            - Start development servers"
	@echo "docker-build   - Build Docker images"
	@echo "docker-up      - Start Docker containers"
	@echo "docker-down    - Stop Docker containers"
	@echo "migrate        - Create new database migration"
	@echo "db-upgrade     - Apply database migrations"
	@echo "db-downgrade   - Rollback database migration"
	@echo "test           - Run tests"
	@echo "clean          - Clean temporary files"
	@echo "lint           - Run linters"

# Initial setup
setup:
	@echo "Setting up NEXUS Platform..."
	cp .env.example .env
	@echo "Please update .env file with your configuration"
	mkdir -p uploads/assets
	@echo "Setup complete!"

# Install dependencies
install:
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && pip install -r requirements.txt
	@echo "Dependencies installed!"

# Development
dev:
	@echo "Starting NEXUS Platform in development mode..."
	docker-compose up

# Docker commands
docker-build:
	@echo "Building Docker images..."
	docker-compose build

docker-up:
	@echo "Starting Docker containers..."
	docker-compose up -d
	@echo "Services running at:"
	@echo "  - Backend API: http://localhost:8000"
	@echo "  - API Docs: http://localhost:8000/api/docs"
	@echo "  - Frontend: http://localhost:8501"

docker-down:
	@echo "Stopping Docker containers..."
	docker-compose down

docker-logs:
	docker-compose logs -f

# Database migrations
migrate:
	@echo "Creating new migration..."
	cd backend && alembic revision --autogenerate -m "$(m)"

db-upgrade:
	@echo "Applying database migrations..."
	cd backend && alembic upgrade head

db-downgrade:
	@echo "Rolling back database migration..."
	cd backend && alembic downgrade -1

db-reset:
	@echo "Resetting database..."
	docker-compose down -v
	docker-compose up -d postgres redis
	sleep 5
	$(MAKE) db-upgrade

# Testing
test:
	@echo "Running tests..."
	cd backend && pytest tests/ -v

test-coverage:
	@echo "Running tests with coverage..."
	cd backend && pytest tests/ --cov=app --cov-report=html

# Code quality
lint:
	@echo "Running linters..."
	cd backend && black app/ --check
	cd backend && flake8 app/
	cd backend && mypy app/

format:
	@echo "Formatting code..."
	cd backend && black app/

# Cleanup
clean:
	@echo "Cleaning temporary files..."
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	@echo "Cleanup complete!"

# Production
prod-build:
	@echo "Building for production..."
	docker-compose -f docker-compose.prod.yml build

prod-up:
	@echo "Starting production services..."
	docker-compose -f docker-compose.prod.yml up -d

prod-down:
	@echo "Stopping production services..."
	docker-compose -f docker-compose.prod.yml down
