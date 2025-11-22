#!/bin/bash

# NEXUS Voice Assistant API Server Startup Script

set -e

echo "Starting NEXUS Voice Assistant API..."

# Check if virtual environment exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Check environment variables
if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ] && [ -z "$AWS_ACCESS_KEY_ID" ]; then
    echo "Warning: No speech service credentials found"
    echo "Set GOOGLE_APPLICATION_CREDENTIALS or AWS credentials"
fi

if [ -z "$ANTHROPIC_API_KEY" ] && [ -z "$OPENAI_API_KEY" ]; then
    echo "Warning: No LLM API key found"
    echo "Set ANTHROPIC_API_KEY or OPENAI_API_KEY"
fi

# Default values
HOST=${API_HOST:-0.0.0.0}
PORT=${API_PORT:-8000}

# Start API server
echo "Starting API server on $HOST:$PORT"
python -m uvicorn api.main:app --host $HOST --port $PORT --reload

echo "API server stopped"
