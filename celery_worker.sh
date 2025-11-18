#!/bin/bash
# Celery Worker Startup Script

# Exit on error
set -e

echo "Starting Celery workers for Nexus Platform..."

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Load environment variables if .env exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Start different workers for different queues in the background
echo "Starting default queue worker..."
celery -A config.celery_config worker --loglevel=info -Q default_queue -n worker1@%h &

echo "Starting email queue worker..."
celery -A config.celery_config worker --loglevel=info -Q email_queue -n worker2@%h &

echo "Starting file processing queue worker..."
celery -A config.celery_config worker --loglevel=info -Q file_processing_queue -n worker3@%h &

echo "Starting AI queue worker..."
celery -A config.celery_config worker --loglevel=info -Q ai_queue -n worker4@%h --concurrency=2 &

echo "Starting reports queue worker..."
celery -A config.celery_config worker --loglevel=info -Q reports_queue -n worker5@%h &

echo "Starting Celery Beat scheduler..."
celery -A config.celery_config beat --loglevel=info &

echo "All Celery workers started!"
echo "Press Ctrl+C to stop all workers..."

# Wait for all background processes
wait
