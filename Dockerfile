FROM python:3.11-slim

<<<<<<< HEAD
# Set working directory
=======
>>>>>>> origin/claude/elasticsearch-search-implementation-013e5Tg92YLzoP4Dme7tcjZR
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
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
