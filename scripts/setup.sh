#!/bin/bash

<<<<<<< HEAD
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
=======
# NEXUS Platform Setup Script
# This script sets up the development environment

set -e

echo "🚀 NEXUS Platform Setup"
echo "======================="
echo ""

# Check Python version
echo "📌 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python $required_version or higher is required (found $python_version)"
    exit 1
fi
echo "✅ Python $python_version"

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Install development dependencies
echo ""
echo "📥 Installing development dependencies..."
pip install -e .

# Copy .env.example to .env if it doesn't exist
echo ""
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "✅ .env file created (please update with your configuration)"
>>>>>>> origin/claude/nexus-analytics-module-01FAKqqMpzB1WpxsYvosEHzE
else
    echo "✅ .env file already exists"
fi

<<<<<<< HEAD
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
=======
# Install pre-commit hooks
echo ""
echo "🔗 Installing pre-commit hooks..."
pip install pre-commit
pre-commit install

# Check if Docker is installed
echo ""
echo "🐳 Checking Docker..."
if command -v docker &> /dev/null; then
    echo "✅ Docker is installed"

    if command -v docker-compose &> /dev/null; then
        echo "✅ Docker Compose is installed"
    else
        echo "⚠️  Docker Compose is not installed"
    fi
else
    echo "⚠️  Docker is not installed"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env file with your configuration"
echo "2. Start services: make docker-up"
echo "3. Initialize database: make init-db"
echo "4. Run tests: make test"
echo ""
echo "Start development:"
echo "  - API: make api"
echo "  - Dashboard: make dashboard"
echo "  - Celery: make celery"
echo ""
echo "Happy coding! 🎉"
>>>>>>> origin/claude/nexus-analytics-module-01FAKqqMpzB1WpxsYvosEHzE
