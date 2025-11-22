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

install:
	pip install -r requirements.txt

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

docker-down:
	docker-compose down

init-search:
	python scripts/init_search.py

run-examples:
	python examples/basic_search.py
