# Multi-stage Dockerfile for NEXUS Platform
# This creates an optimized production image with minimal size

###############################################################################
# Stage 1: Builder - Install dependencies and build application
###############################################################################
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    g++ \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Install Poetry
RUN pip install poetry==1.7.1

# Copy dependency files
COPY pyproject.toml ./
COPY README.md ./

# Configure poetry to not create virtual environment
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-interaction --no-ansi --only main

###############################################################################
# Stage 2: Runtime - Create minimal production image
###############################################################################
FROM python:3.11-slim as runtime

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/usr/local/bin:$PATH" \
    PYTHONPATH="/app:$PYTHONPATH"

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # PostgreSQL client
    libpq5 \
    # For file type detection
    libmagic1 \
    # For OCR
    tesseract-ocr \
    tesseract-ocr-eng \
    # For PDF processing
    poppler-utils \
    # For image processing
    libjpeg62-turbo \
    libpng16-16 \
    # Utilities
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r nexus && useradd -r -g nexus nexus

# Create application directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=nexus:nexus backend ./backend
COPY --chown=nexus:nexus frontend ./frontend
COPY --chown=nexus:nexus modules ./modules
COPY --chown=nexus:nexus alembic ./alembic
COPY --chown=nexus:nexus alembic.ini ./
COPY --chown=nexus:nexus scripts ./scripts

# Create necessary directories
RUN mkdir -p /app/logs /app/storage/temp /app/storage/uploads /app/storage/versions \
    && chown -R nexus:nexus /app

# Switch to non-root user
USER nexus

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose ports
EXPOSE 8000

# Default command (can be overridden in docker-compose)
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

###############################################################################
# Stage 3: Development - Include development dependencies
###############################################################################
FROM runtime as development

USER root

# Install development dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Install development Python packages
RUN pip install --no-cache-dir \
    ipython \
    ipdb \
    pytest \
    pytest-asyncio \
    pytest-cov \
    black \
    ruff \
    mypy

USER nexus

# Override command for development
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
