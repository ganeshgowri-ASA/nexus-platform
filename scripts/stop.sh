#!/bin/bash

# NEXUS Scheduler Stop Script

set -e

echo "🛑 Stopping NEXUS Scheduler..."

# Stop services
docker-compose down

echo "✅ All services stopped!"
