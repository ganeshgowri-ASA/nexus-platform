# Multi-stage Dockerfile for NEXUS Platform

# ============================================================================
# Stage 1: Base
# ============================================================================
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# ============================================================================
# Stage 2: Dependencies
# ============================================================================
FROM base as dependencies

# Copy requirements
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -e .

# ============================================================================
# Stage 3: Development
# ============================================================================
FROM dependencies as development

# Install development dependencies
RUN pip install -e ".[dev]"

# Copy application code
COPY . .

# Expose ports
EXPOSE 8501 8000 8001 9090

# Default command for development
CMD ["streamlit", "run", "nexus/app.py", "--server.port=8501", "--server.address=0.0.0.0"]

# ============================================================================
# Stage 4: Production
# ============================================================================
FROM dependencies as production

# Copy application code
COPY . .

# Create non-root user
RUN groupadd -r nexus && useradd -r -g nexus nexus && \
    chown -R nexus:nexus /app

# Switch to non-root user
USER nexus

# Expose ports
EXPOSE 8501 8000 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Default command for production
CMD ["streamlit", "run", "nexus/app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
