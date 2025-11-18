#!/bin/bash

# NEXUS Workflow Orchestration - Setup Script

set -e

echo "🔧 Setting up NEXUS Workflow Orchestration..."

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p data/postgres
mkdir -p data/redis

# Copy environment file
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "✅ Created .env file. Please edit it with your configuration."
else
    echo "✅ .env file already exists"
fi

# Make scripts executable
echo "🔐 Making scripts executable..."
chmod +x scripts/*.sh

# Install Python dependencies (if not using Docker)
if [ "$1" = "--local" ]; then
    echo "📦 Installing Python dependencies..."
    pip install -r requirements.txt
    echo "✅ Python dependencies installed"
fi

# Build Docker images
echo "🐳 Building Docker images..."
docker-compose build

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Edit .env file with your configuration"
echo "   2. Run './scripts/start.sh' to start services"
echo "   3. Access the UI at http://localhost:8501"
echo ""
