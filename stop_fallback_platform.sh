#!/bin/bash
# Stop the reVoAgent platform with fallback LLM system

echo "Stopping reVoAgent Platform..."

# Stop backend
if [ -f .backend_pid ]; then
    BACKEND_PID=$(cat .backend_pid)
    echo "Stopping backend (PID: $BACKEND_PID)..."
    kill -15 $BACKEND_PID 2>/dev/null || echo "Backend already stopped"
    rm .backend_pid
else
    echo "Backend PID file not found"
    # Try to find and stop the process
    pkill -f "python backend_main_fallback.py" || echo "Backend not running"
fi

# Stop frontend
if [ -f .frontend_pid ]; then
    FRONTEND_PID=$(cat .frontend_pid)
    echo "Stopping frontend (PID: $FRONTEND_PID)..."
    kill -15 $FRONTEND_PID 2>/dev/null || echo "Frontend already stopped"
    rm .frontend_pid
else
    echo "Frontend PID file not found"
    # Try to find and stop the process
    pkill -f "node.*start" || echo "Frontend not running"
fi

echo "ReVoAgent Platform stopped"