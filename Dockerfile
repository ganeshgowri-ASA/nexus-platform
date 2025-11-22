<<<<<<< HEAD
FROM python:3.11-slim

<<<<<<< HEAD
# Set working directory
=======
>>>>>>> origin/claude/elasticsearch-search-implementation-013e5Tg92YLzoP4Dme7tcjZR
WORKDIR /app
=======
# Multi-stage Dockerfile for NEXUS A/B Testing Module

# Stage 1: Base
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
>>>>>>> origin/claude/ab-testing-module-01D3o2ivEGbVpUmsgesHtDjA

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
<<<<<<< HEAD
<<<<<<< HEAD
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
=======
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
>>>>>>> origin/claude/elasticsearch-search-implementation-013e5Tg92YLzoP4Dme7tcjZR
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

<<<<<<< HEAD
# Create necessary directories
RUN mkdir -p uploads temp logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Expose ports
EXPOSE 8501 5555

# Default command (can be overridden in docker-compose)
CMD ["streamlit", "run", "app.py"]
=======
# Create non-root user
RUN useradd -m -u 1000 nexus && chown -R nexus:nexus /app
USER nexus

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import asyncio; from search.client import es_client; asyncio.run(es_client.ping())"

# Default command
CMD ["python", "-m", "pytest", "tests/"]
>>>>>>> origin/claude/elasticsearch-search-implementation-013e5Tg92YLzoP4Dme7tcjZR
=======
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Stage 2: Dependencies
FROM base as dependencies

# Copy dependency files
COPY requirements.txt pyproject.toml ./

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Stage 3: Application
FROM dependencies as application

# Copy application code
COPY modules/ ./modules/
COPY migrations/ ./migrations/
COPY alembic.ini ./
COPY .env.example ./.env

# Create logs directory
RUN mkdir -p logs

# Expose ports
EXPOSE 8000 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')"

# Default command (API server)
CMD ["python", "-m", "modules.ab_testing.api.main"]
>>>>>>> origin/claude/ab-testing-module-01D3o2ivEGbVpUmsgesHtDjA
