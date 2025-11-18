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

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
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

# Set working directory
WORKDIR /app

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
