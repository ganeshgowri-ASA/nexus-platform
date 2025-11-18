#!/bin/bash
# Start script for NEXUS Speech-to-Text module

set -e

echo "🚀 Starting NEXUS Speech-to-Text Module"

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "❌ Error: Virtual environment not found. Run setup.sh first."
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found. Run setup.sh first."
    exit 1
fi

# Initialize database
echo "🗄️  Initializing database..."
python -c "from config.database import init_db; init_db()" || echo "⚠️  Database already initialized"

# Function to start a service in the background
start_service() {
    local name=$1
    local command=$2
    local log_file="logs/${name}.log"

    mkdir -p logs

    echo "▶️  Starting ${name}..."
    eval "$command" > "$log_file" 2>&1 &
    local pid=$!
    echo "$pid" > "logs/${name}.pid"
    echo "✅ ${name} started (PID: $pid)"
}

# Start services
start_service "api" "uvicorn api.app:app --host 0.0.0.0 --port 8000"
sleep 3

start_service "celery" "celery -A tasks.celery_app worker --loglevel=info"
sleep 2

start_service "ui" "streamlit run ui/app.py --server.port 8501"
sleep 2

echo ""
echo "✅ All services started!"
echo ""
echo "Access points:"
echo "- Streamlit UI: http://localhost:8501"
echo "- API Docs: http://localhost:8000/docs"
echo "- API ReDoc: http://localhost:8000/redoc"
echo ""
echo "Logs are in the logs/ directory"
echo ""
echo "To stop all services, run: ./scripts/stop.sh"
