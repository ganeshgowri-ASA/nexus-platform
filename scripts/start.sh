#!/bin/bash

# NEXUS Scheduler Startup Script

set -e

echo "🚀 Starting NEXUS Scheduler..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "📋 Creating .env file from .env.example..."
    cp .env.example .env
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Build containers
echo "🔨 Building Docker containers..."
docker-compose build

# Start services
echo "▶️ Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 10

# Run migrations
echo "🗄️ Running database migrations..."
docker-compose exec -T api alembic upgrade head

# Show status
echo ""
echo "✅ NEXUS Scheduler is running!"
echo ""
echo "📊 API Server:    http://localhost:8000"
echo "📚 API Docs:      http://localhost:8000/docs"
echo "🎨 Streamlit UI:  http://localhost:8501"
echo ""
echo "📋 To view logs:  docker-compose logs -f"
echo "🛑 To stop:       docker-compose down"
echo ""
