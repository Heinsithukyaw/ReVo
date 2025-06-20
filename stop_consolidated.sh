#!/bin/bash
echo "🛑 Stopping reVoAgent Enterprise System..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Kill processes by PID
if [ -f /tmp/revoagent_backend.pid ]; then
    BACKEND_PID=$(cat /tmp/revoagent_backend.pid)
    echo -e "${YELLOW}[STOPPING]${NC} Backend process (PID: $BACKEND_PID)"
    kill $BACKEND_PID 2>/dev/null || true
    rm -f /tmp/revoagent_backend.pid
    echo -e "${GREEN}[STOPPED]${NC} Backend process"
fi

if [ -f /tmp/revoagent_frontend.pid ]; then
    FRONTEND_PID=$(cat /tmp/revoagent_frontend.pid)
    echo -e "${YELLOW}[STOPPING]${NC} Frontend process (PID: $FRONTEND_PID)"
    kill $FRONTEND_PID 2>/dev/null || true
    rm -f /tmp/revoagent_frontend.pid
    echo -e "${GREEN}[STOPPED]${NC} Frontend process"
fi

# Additional cleanup for monitoring services
pkill -f prometheus 2>/dev/null || true
pkill -f grafana 2>/dev/null || true

# Cleanup ports
if [ -f "scripts/cleanup_ports.sh" ]; then
    echo -e "${YELLOW}[CLEANUP]${NC} Running port cleanup"
    ./scripts/cleanup_ports.sh
    echo -e "${GREEN}[CLEANUP]${NC} Port cleanup completed"
else
    # Manual cleanup
    echo -e "${YELLOW}[CLEANUP]${NC} Running manual port cleanup"
    pkill -f "python.*backend" 2>/dev/null || true
    pkill -f "npm.*dev" 2>/dev/null || true
    pkill -f "node.*start" 2>/dev/null || true
    echo -e "${GREEN}[CLEANUP]${NC} Manual port cleanup completed"
fi

echo ""
echo "=================================================================="
echo -e "${GREEN}[SUCCESS]${NC} reVoAgent Enterprise System stopped successfully"
echo "=================================================================="
