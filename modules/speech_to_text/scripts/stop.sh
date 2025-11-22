#!/bin/bash
# Stop script for NEXUS Speech-to-Text module

echo "🛑 Stopping NEXUS Speech-to-Text Module"

# Function to stop a service
stop_service() {
    local name=$1
    local pid_file="logs/${name}.pid"

    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "⏹️  Stopping ${name} (PID: $pid)..."
            kill "$pid" 2>/dev/null || true
            sleep 2
            if ps -p "$pid" > /dev/null 2>&1; then
                echo "⚠️  Force stopping ${name}..."
                kill -9 "$pid" 2>/dev/null || true
            fi
            rm "$pid_file"
            echo "✅ ${name} stopped"
        else
            echo "ℹ️  ${name} is not running"
            rm "$pid_file"
        fi
    else
        echo "ℹ️  ${name} PID file not found"
    fi
}

# Stop services in reverse order
stop_service "ui"
stop_service "celery"
stop_service "api"

echo ""
echo "✅ All services stopped"
