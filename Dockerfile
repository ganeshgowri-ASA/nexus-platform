<<<<<<< HEAD
<<<<<<< HEAD
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
=======
# NEXUS Platform Dockerfile
# Multi-stage build for optimized production image

# ============================================================================
# Stage 1: Builder
# ============================================================================
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /build

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --user -r requirements.txt

# ============================================================================
# Stage 2: Runtime
# ============================================================================
FROM python:3.11-slim

# Set metadata
LABEL maintainer="NEXUS Team <team@nexus-platform.com>"
LABEL description="NEXUS Platform - Unified Productivity Suite"
LABEL version="1.0.0"
>>>>>>> origin/claude/nexus-platform-setup-01GgK8vgMUpRwMXvUmBp8eNW

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
<<<<<<< HEAD
    PIP_DISABLE_PIP_VERSION_CHECK=1
>>>>>>> origin/claude/ab-testing-module-01D3o2ivEGbVpUmsgesHtDjA
=======
FROM python:3.11-slim

WORKDIR /app
>>>>>>> origin/claude/build-etl-integration-hub-01CuRDV55w16up98jJhFz8Ts

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
=======
    curl \
=======
    g++ \
    postgresql-client \
>>>>>>> origin/claude/build-etl-integration-hub-01CuRDV55w16up98jJhFz8Ts
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
<<<<<<< HEAD
>>>>>>> origin/claude/elasticsearch-search-implementation-013e5Tg92YLzoP4Dme7tcjZR
=======
>>>>>>> origin/claude/build-etl-integration-hub-01CuRDV55w16up98jJhFz8Ts
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

<<<<<<< HEAD
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
=======
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 nexus && \
    mkdir -p /app /app/logs /app/data && \
    chown -R nexus:nexus /app
>>>>>>> origin/claude/nexus-platform-setup-01GgK8vgMUpRwMXvUmBp8eNW

# Set working directory
WORKDIR /app

<<<<<<< HEAD
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
=======
# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/nexus/.local

# Update PATH
ENV PATH=/home/nexus/.local/bin:$PATH

# Copy application code
COPY --chown=nexus:nexus . .

# Create necessary directories
RUN mkdir -p logs data uploads temp && \
    chown -R nexus:nexus logs data uploads temp

# Switch to non-root user
USER nexus

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Expose port
EXPOSE 8501

# Set entrypoint
ENTRYPOINT ["streamlit", "run"]

# Default command
CMD ["app/main.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]

# ============================================================================
# Build Instructions:
# ============================================================================
# Build: docker build -t nexus-platform:latest .
# Run:   docker run -p 8501:8501 --env-file .env nexus-platform:latest
#
# With volume mounts:
# docker run -p 8501:8501 \
#   -v $(pwd)/data:/app/data \
#   -v $(pwd)/logs:/app/logs \
#   --env-file .env \
#   nexus-platform:latest
#
# With Docker Compose:
# docker-compose up -d
# ============================================================================
>>>>>>> origin/claude/nexus-platform-setup-01GgK8vgMUpRwMXvUmBp8eNW
=======
# Create data directory
RUN mkdir -p /app/data

# Set Python path
ENV PYTHONPATH=/app

# Expose ports
EXPOSE 8001 8002 8501 8502 5555

CMD ["uvicorn", "modules.etl.api.main:app", "--host", "0.0.0.0", "--port", "8001"]
>>>>>>> origin/claude/build-etl-integration-hub-01CuRDV55w16up98jJhFz8Ts
