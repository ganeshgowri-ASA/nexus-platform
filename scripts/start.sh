#!/bin/bash

<<<<<<< HEAD
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
=======
# NEXUS Workflow Orchestration - Startup Script

set -e

echo "🚀 Starting NEXUS Workflow Orchestration..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Copy .env.example to .env if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration before starting services"
    exit 0
fi

# Start Docker services
echo "🐳 Starting Docker services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🔍 Checking service health..."

# Check PostgreSQL
if docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo "✅ PostgreSQL is ready"
else
    echo "❌ PostgreSQL is not ready"
fi

# Check Redis
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is ready"
else
    echo "❌ Redis is not ready"
fi

# Check API
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API is ready"
else
    echo "❌ API is not ready yet (may still be starting)"
fi

echo ""
echo "✨ NEXUS Workflow Orchestration is starting!"
echo ""
echo "📍 Access points:"
echo "   - API Documentation: http://localhost:8000/docs"
echo "   - Streamlit UI:      http://localhost:8501"
echo "   - Flower (Celery):   http://localhost:5555"
echo "   - Temporal UI:       http://localhost:8088"
echo ""
echo "📊 View logs:"
echo "   docker-compose logs -f"
echo ""
echo "🛑 Stop services:"
echo "   docker-compose down"
>>>>>>> origin/claude/build-orchestration-module-01Xe9ZAfD1FN1j7vgrCUBQ3a
echo ""
