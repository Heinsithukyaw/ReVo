#!/bin/bash
echo "🛑 Stopping reVoAgent Consolidated System..."

# Kill processes by PID
if [ -f /tmp/revoagent_backend.pid ]; then
    BACKEND_PID=$(cat /tmp/revoagent_backend.pid)
    kill $BACKEND_PID 2>/dev/null || true
    rm -f /tmp/revoagent_backend.pid
    echo "✅ Backend stopped"
fi

if [ -f /tmp/revoagent_frontend.pid ]; then
    FRONTEND_PID=$(cat /tmp/revoagent_frontend.pid)
    kill $FRONTEND_PID 2>/dev/null || true
    rm -f /tmp/revoagent_frontend.pid
    echo "✅ Frontend stopped"
fi

# Cleanup ports
./scripts/cleanup_ports.sh

echo "🎉 System stopped successfully"
