#!/bin/bash
<<<<<<< HEAD
# NEXUS Platform API - Quick Start Script

echo "Starting NEXUS Platform API..."
echo "================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo ""
    echo "⚠️  Please edit .env file with your configuration before running in production!"
    echo ""
fi

# Run the server
echo "Starting FastAPI server..."
echo ""
echo "API Documentation available at:"
echo "  - Swagger UI: http://localhost:8000/docs"
echo "  - ReDoc:      http://localhost:8000/redoc"
echo ""

python -m api.main
=======

# NEXUS Platform - Quick Start Script
# This script helps you quickly start the NEXUS Platform

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Banner
echo -e "${BLUE}"
cat << "EOF"
 _   _ _____ __  ____  ______
| \ | | ____|\ \/ / / / / ___|
|  \| |  _|   \  /| | | \___ \
| |\  | |___  /  \| |_| |___) |
|_| \_|_____||/\_\\___/|____/

NEXUS Platform - Unified Productivity Suite
EOF
echo -e "${NC}"

# Check if .env file exists
if [ ! -f .env ]; then
    print_warning ".env file not found. Creating from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        print_info "Please edit .env file and add your ANTHROPIC_API_KEY"
        print_info "Then run this script again."
        exit 1
    else
        print_error ".env.example not found!"
        exit 1
    fi
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_info "Creating virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate || {
    print_error "Failed to activate virtual environment"
    exit 1
}

# Check if dependencies are installed
if ! python -c "import streamlit" 2>/dev/null; then
    print_info "Installing dependencies..."
    pip install -r requirements.txt
    print_success "Dependencies installed"
else
    print_info "Dependencies already installed"
fi

# Create necessary directories
print_info "Creating necessary directories..."
mkdir -p logs data uploads temp

# Check for Anthropic API key
source .env
if [ -z "$ANTHROPIC__API_KEY" ] || [ "$ANTHROPIC__API_KEY" = "your-anthropic-api-key-here" ]; then
    print_error "ANTHROPIC_API_KEY not set in .env file!"
    print_info "Please add your Anthropic API key to the .env file"
    exit 1
fi

# Initialize database (if needed)
print_info "Initializing database..."
python -c "from database import init_db; init_db()" 2>/dev/null || print_warning "Database initialization skipped"

# Start the application
print_success "Starting NEXUS Platform..."
print_info "Access the application at: http://localhost:8501"
print_info ""
print_info "Press Ctrl+C to stop the server"
print_info ""

streamlit run app/main.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false

print_info "NEXUS Platform stopped"
>>>>>>> origin/claude/nexus-platform-setup-01GgK8vgMUpRwMXvUmBp8eNW
