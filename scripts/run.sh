#!/bin/bash
# Script to run NEXUS A/B Testing module

set -e

echo "Starting NEXUS A/B Testing Module..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "Please update .env with your configuration"
fi

# Check if PostgreSQL is running
if ! pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo "Error: PostgreSQL is not running"
    echo "Please start PostgreSQL or use Docker: make docker-up"
    exit 1
fi

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "Warning: Redis is not running"
    echo "Some features will be unavailable without Redis"
fi

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# Start API server in background
echo "Starting FastAPI server..."
python -m modules.ab_testing.api.main &
API_PID=$!

# Wait for API to be ready
echo "Waiting for API server to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null; then
        echo "API server is ready!"
        break
    fi
    sleep 1
done

# Start Streamlit UI
echo "Starting Streamlit UI..."
streamlit run modules/ab_testing/ui/app.py &
UI_PID=$!

echo "
=============================================
NEXUS A/B Testing Module is running!
=============================================

API Server:   http://localhost:8000
API Docs:     http://localhost:8000/api/docs
Streamlit UI: http://localhost:8501

Press Ctrl+C to stop all services
"

# Wait for user interrupt
trap "echo 'Stopping services...'; kill $API_PID $UI_PID; exit 0" INT
wait
