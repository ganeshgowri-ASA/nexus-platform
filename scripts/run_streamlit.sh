#!/bin/bash
# Run Streamlit Document Management UI

set -e

# Get the project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root
cd "$PROJECT_ROOT"

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Set default values if not in .env
export STREAMLIT_SERVER_PORT=${STREAMLIT_SERVER_PORT:-8501}
export BACKEND_API_URL=${BACKEND_API_URL:-http://localhost:8000}

echo "Starting NEXUS Document Management System..."
echo "Streamlit UI: http://localhost:$STREAMLIT_SERVER_PORT"
echo "Backend API: $BACKEND_API_URL"
echo ""

# Run Streamlit
streamlit run frontend/app.py \
    --server.port=$STREAMLIT_SERVER_PORT \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false \
    --theme.primaryColor="#667eea" \
    --theme.backgroundColor="#ffffff" \
    --theme.secondaryBackgroundColor="#f8f9fa" \
    --theme.textColor="#212529" \
    --theme.font="sans serif"
