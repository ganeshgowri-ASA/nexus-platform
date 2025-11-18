# Multi-stage Dockerfile for NEXUS Platform
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency files
COPY requirements.txt pyproject.toml ./

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

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

# Copy application code
COPY --chown=nexus:nexus . .

# Switch to non-root user
USER nexus

# Expose ports
EXPOSE 8000 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "modules.analytics.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
