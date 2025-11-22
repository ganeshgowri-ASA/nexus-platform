#!/bin/bash

# NEXUS Voice Assistant UI Startup Script

set -e

echo "Starting NEXUS Voice Assistant UI..."

# Check if virtual environment exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Set default API URL if not set
export VOICE_API_URL=${VOICE_API_URL:-http://localhost:8000/api/voice}

# Start Streamlit UI
echo "Starting Streamlit UI..."
echo "API URL: $VOICE_API_URL"
streamlit run ui/app.py

echo "UI stopped"
