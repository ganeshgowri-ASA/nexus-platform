#!/bin/bash
###############################################################################
# NEXUS Platform Development Startup Script
#
# This script starts the development environment with:
# - FastAPI backend server (port 8000)
# - Streamlit frontend (port 8501)
# - Hot-reload enabled for both
#
# Usage:
#   ./scripts/start_dev.sh [OPTIONS]
#
# Options:
#   --backend-only    Start only the FastAPI backend
#   --frontend-only   Start only the Streamlit frontend
#   --port PORT       Override backend port (default: 8000)
#   --frontend-port   Override frontend port (default: 8501)
#   --help           Show this help message
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default configuration
BACKEND_PORT=8000
FRONTEND_PORT=8501
BACKEND_ONLY=false
FRONTEND_ONLY=false
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --backend-only)
            BACKEND_ONLY=true
            shift
            ;;
        --frontend-only)
            FRONTEND_ONLY=true
            shift
            ;;
        --port)
            BACKEND_PORT="$2"
            shift 2
            ;;
        --frontend-port)
            FRONTEND_PORT="$2"
            shift 2
            ;;
        --help)
            grep '^#' "$0" | sed 's/^# //' | sed 's/^#//'
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Change to project root
cd "$PROJECT_ROOT"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           NEXUS Platform - Development Mode                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠ Warning: .env file not found${NC}"
    echo -e "${YELLOW}Creating .env from example...${NC}"
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${GREEN}✓ Created .env file${NC}"
    else
        echo -e "${RED}✗ .env.example not found${NC}"
        echo -e "${YELLOW}Please create a .env file with required configuration${NC}"
    fi
    echo ""
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}⚠ Warning: Virtual environment not activated${NC}"
    echo -e "${YELLOW}Attempting to activate virtual environment...${NC}"

    if [ -d "venv" ]; then
        source venv/bin/activate
        echo -e "${GREEN}✓ Activated venv${NC}"
    elif [ -d ".venv" ]; then
        source .venv/bin/activate
        echo -e "${GREEN}✓ Activated .venv${NC}"
    else
        echo -e "${RED}✗ No virtual environment found${NC}"
        echo -e "${YELLOW}Please create and activate a virtual environment first${NC}"
        exit 1
    fi
    echo ""
fi

# Check if dependencies are installed
echo -e "${BLUE}Checking dependencies...${NC}"
if ! python -c "import fastapi" 2>/dev/null; then
    echo -e "${YELLOW}⚠ Dependencies not installed${NC}"
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip install -e . --quiet
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${GREEN}✓ Dependencies OK${NC}"
fi
echo ""

# Check database connectivity
echo -e "${BLUE}Checking database...${NC}"
if python -c "from backend.database import engine; engine.connect()" 2>/dev/null; then
    echo -e "${GREEN}✓ Database connection OK${NC}"
else
    echo -e "${YELLOW}⚠ Database connection failed${NC}"
    echo -e "${YELLOW}Make sure PostgreSQL is running or using SQLite${NC}"
fi
echo ""

# Create necessary directories
echo -e "${BLUE}Creating directories...${NC}"
mkdir -p logs storage/temp storage/uploads storage/versions
echo -e "${GREEN}✓ Directories created${NC}"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down services...${NC}"
    jobs -p | xargs -r kill 2>/dev/null
    echo -e "${GREEN}✓ Services stopped${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start backend
if [ "$FRONTEND_ONLY" = false ]; then
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  Starting FastAPI Backend                                  ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo -e "${GREEN}Backend URL: http://localhost:${BACKEND_PORT}${NC}"
    echo -e "${GREEN}API Docs: http://localhost:${BACKEND_PORT}/docs${NC}"
    echo -e "${GREEN}ReDoc: http://localhost:${BACKEND_PORT}/redoc${NC}"
    echo ""

    # Start uvicorn with hot reload
    uvicorn backend.main:app \
        --host 0.0.0.0 \
        --port "$BACKEND_PORT" \
        --reload \
        --reload-dir backend \
        --reload-dir modules \
        --log-level info \
        --access-log &

    BACKEND_PID=$!
    echo -e "${GREEN}✓ Backend started (PID: $BACKEND_PID)${NC}"
    echo ""
fi

# Wait a bit for backend to start
if [ "$FRONTEND_ONLY" = false ] && [ "$BACKEND_ONLY" = false ]; then
    echo -e "${BLUE}Waiting for backend to start...${NC}"
    sleep 3
    echo ""
fi

# Start frontend
if [ "$BACKEND_ONLY" = false ]; then
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  Starting Streamlit Frontend                               ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo -e "${GREEN}Frontend URL: http://localhost:${FRONTEND_PORT}${NC}"
    echo ""

    # Start Streamlit
    streamlit run frontend/app.py \
        --server.port "$FRONTEND_PORT" \
        --server.address 0.0.0.0 \
        --server.headless true \
        --browser.gatherUsageStats false \
        --server.runOnSave true &

    FRONTEND_PID=$!
    echo -e "${GREEN}✓ Frontend started (PID: $FRONTEND_PID)${NC}"
    echo ""
fi

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Development Environment Ready                              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Press Ctrl+C to stop all services${NC}"
echo ""
echo -e "${YELLOW}Logs will appear below:${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Wait for all background jobs
wait
