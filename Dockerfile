# Multi-stage Dockerfile for NEXUS Platform

# Base stage
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Development stage
FROM base as development
ENV DEBUG=True
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM base as production
ENV DEBUG=False
CMD ["gunicorn", "api.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]

# Celery worker stage
FROM base as celery-worker
CMD ["celery", "-A", "tasks.celery_app", "worker", "--loglevel=info", "--concurrency=4"]

# Celery beat stage (for scheduled tasks)
FROM base as celery-beat
CMD ["celery", "-A", "tasks.celery_app", "beat", "--loglevel=info"]

# Streamlit UI stage
FROM base as streamlit
CMD ["streamlit", "run", "ui/main.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
