<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
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
=======
=======
>>>>>>> origin/claude/build-orchestration-module-01Xe9ZAfD1FN1j7vgrCUBQ3a
=======
>>>>>>> origin/claude/build-nexus-pipeline-module-01QTVSb9CH4TjcrrT8nhjeJp
=======
# NEXUS Content Calendar Dockerfile
>>>>>>> origin/claude/content-calendar-module-01FvYrYmkZAP6rXZEaW6DyDq
FROM python:3.11-slim

# Set working directory
WORKDIR /app
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
>>>>>>> origin/claude/build-rpa-module-011gc98wDCMg5EmJGgT8DFqE

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
<<<<<<< HEAD
    git \
=======
=======
>>>>>>> origin/claude/build-nexus-pipeline-module-01QTVSb9CH4TjcrrT8nhjeJp

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
<<<<<<< HEAD
>>>>>>> origin/claude/build-orchestration-module-01Xe9ZAfD1FN1j7vgrCUBQ3a
=======
>>>>>>> origin/claude/build-nexus-pipeline-module-01QTVSb9CH4TjcrrT8nhjeJp
=======

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    python3-dev \
>>>>>>> origin/claude/content-calendar-module-01FvYrYmkZAP6rXZEaW6DyDq
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
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
=======
# Multi-stage Dockerfile for NEXUS Platform

# Base stage
FROM python:3.11-slim as base
>>>>>>> origin/claude/batch-processing-module-01PCraqtfpn2xgwyYUuEev97
=======
# Multi-stage Dockerfile for NEXUS Platform
FROM python:3.11-slim as base
>>>>>>> origin/claude/nexus-analytics-module-01FAKqqMpzB1WpxsYvosEHzE

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
    PIP_DISABLE_PIP_VERSION_CHECK=1
>>>>>>> origin/claude/ab-testing-module-01D3o2ivEGbVpUmsgesHtDjA
=======
FROM python:3.11-slim

WORKDIR /app
>>>>>>> origin/claude/build-etl-integration-hub-01CuRDV55w16up98jJhFz8Ts
=======
    PIP_DISABLE_PIP_VERSION_CHECK=1
>>>>>>> origin/claude/batch-processing-module-01PCraqtfpn2xgwyYUuEev97

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
<<<<<<< HEAD
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
=======
>>>>>>> origin/claude/build-orchestration-module-01Xe9ZAfD1FN1j7vgrCUBQ3a
=======
>>>>>>> origin/claude/build-nexus-pipeline-module-01QTVSb9CH4TjcrrT8nhjeJp
=======
>>>>>>> origin/claude/content-calendar-module-01FvYrYmkZAP6rXZEaW6DyDq
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
# Create necessary directories
RUN mkdir -p uploads temp logs
=======
    software-properties-common \
    git \
    postgresql-client \
    libpq-dev \
    scrot \
    xvfb \
    x11vnc \
    fluxbox \
    wmctrl \
    xdotool \
    tesseract-ocr \
    libopencv-dev \
    python3-opencv \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install --with-deps chromium

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/data/screenshots /app/data/recordings /app/data/uploads

# Expose ports
EXPOSE 8000 8501
>>>>>>> origin/claude/build-rpa-module-011gc98wDCMg5EmJGgT8DFqE
=======
# Create necessary directories
RUN mkdir -p logs airflow/dags

# Expose ports
EXPOSE 8000 8501
>>>>>>> origin/claude/build-nexus-pipeline-module-01QTVSb9CH4TjcrrT8nhjeJp

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

<<<<<<< HEAD
<<<<<<< HEAD
# Expose ports
EXPOSE 8501 5555

# Default command (can be overridden in docker-compose)
CMD ["streamlit", "run", "app.py"]
=======
=======
>>>>>>> origin/claude/build-orchestration-module-01Xe9ZAfD1FN1j7vgrCUBQ3a
# Create non-root user
RUN useradd -m -u 1000 nexus && chown -R nexus:nexus /app
USER nexus

<<<<<<< HEAD
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

=======
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

>>>>>>> origin/claude/nexus-analytics-module-01FAKqqMpzB1WpxsYvosEHzE
# Copy dependency files
COPY requirements.txt pyproject.toml ./

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

<<<<<<< HEAD
# Stage 3: Application
FROM dependencies as application

# Copy application code
COPY modules/ ./modules/
COPY migrations/ ./migrations/
COPY alembic.ini ./
COPY .env.example ./.env
=======
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app
=======
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*
>>>>>>> origin/claude/build-advertising-lead-generation-01Skr8pwxfdGAtz4wHoobrUL

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .
<<<<<<< HEAD
>>>>>>> origin/claude/batch-processing-module-01PCraqtfpn2xgwyYUuEev97

# Create logs directory
RUN mkdir -p logs

<<<<<<< HEAD
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
=======
# Development stage
FROM base as development

# Copy application code
COPY . .

# Expose ports
EXPOSE 8000 8501 5555

CMD ["python", "app.py", "api"]

# Production stage
FROM base as production

# Create non-root user
RUN useradd -m -u 1000 nexus && \
    mkdir -p /app/logs /app/exports /app/data && \
    chown -R nexus:nexus /app
>>>>>>> origin/claude/nexus-analytics-module-01FAKqqMpzB1WpxsYvosEHzE

# Copy application code
COPY --chown=nexus:nexus . .

<<<<<<< HEAD
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
=======
# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Default command (can be overridden in docker-compose)
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
>>>>>>> origin/claude/build-rpa-module-011gc98wDCMg5EmJGgT8DFqE
=======
# Expose ports
EXPOSE 8000 8501

# Default command
CMD ["uvicorn", "modules.orchestration.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
>>>>>>> origin/claude/build-orchestration-module-01Xe9ZAfD1FN1j7vgrCUBQ3a
=======
# Default command
CMD ["streamlit", "run", "main.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
>>>>>>> origin/claude/build-nexus-pipeline-module-01QTVSb9CH4TjcrrT8nhjeJp
=======
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
>>>>>>> origin/claude/batch-processing-module-01PCraqtfpn2xgwyYUuEev97
=======
# Switch to non-root user
USER nexus

# Expose ports
EXPOSE 8000 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "modules.analytics.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
>>>>>>> origin/claude/nexus-analytics-module-01FAKqqMpzB1WpxsYvosEHzE
=======
# Expose ports
EXPOSE 8000 8501

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Default command (can be overridden)
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
>>>>>>> origin/claude/content-calendar-module-01FvYrYmkZAP6rXZEaW6DyDq
=======

# Expose ports
EXPOSE 8000

# Run application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
>>>>>>> origin/claude/build-advertising-lead-generation-01Skr8pwxfdGAtz4wHoobrUL
