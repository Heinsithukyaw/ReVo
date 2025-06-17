#!/bin/bash

# Enhanced Stop Script for reVoAgent
echo "🛑 Stopping reVoAgent Enhanced Platform..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to safely kill process
safe_kill() {
    local pid=$1
    local name=$2
    
    if [ ! -z "$pid" ] && kill -0 $pid 2>/dev/null; then
        log_info "Stopping $name (PID: $pid)..."
        kill $pid
        
        # Wait for graceful shutdown
        sleep 3
        
        # Force kill if still running
        if kill -0 $pid 2>/dev/null; then
            log_warning "Force killing $name..."
            kill -9 $pid
        fi
        
        log_success "$name stopped"
        return 0
    else
        log_warning "$name process not found or already stopped"
        return 1
    fi
}

# Stop backend using PID file
if [ -f .backend.pid ]; then
    BACKEND_PID=$(cat .backend.pid)
    if safe_kill $BACKEND_PID "Enhanced Backend"; then
        rm .backend.pid
    fi
else
    log_info "No backend PID file found, searching for process..."
    # Try to find and kill backend processes
    BACKEND_PIDS=$(pgrep -f "enhanced_backend_main.py\|backend_main.py")
    if [ ! -z "$BACKEND_PIDS" ]; then
        for pid in $BACKEND_PIDS; do
            safe_kill $pid "Backend"
        done
    else
        log_warning "No backend processes found"
    fi
fi

# Stop frontend using PID file
if [ -f .frontend.pid ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    if safe_kill $FRONTEND_PID "Frontend"; then
        rm .frontend.pid
    fi
else
    log_info "No frontend PID file found, searching for process..."
    # Try to find and kill frontend processes
    FRONTEND_PIDS=$(pgrep -f "frontend.*dev\|vite\|npm.*run.*dev")
    if [ ! -z "$FRONTEND_PIDS" ]; then
        for pid in $FRONTEND_PIDS; do
            safe_kill $pid "Frontend"
        done
    else
        log_warning "No frontend processes found"
    fi
fi

# Clean up any remaining reVoAgent processes
log_info "Cleaning up remaining processes..."

# Kill any remaining Python processes related to reVoAgent
PYTHON_PIDS=$(pgrep -f "revoagent\|enhanced_backend\|backend_main")
for pid in $PYTHON_PIDS; do
    if kill -0 $pid 2>/dev/null; then
        safe_kill $pid "reVoAgent Python process"
    fi
done

# Kill any remaining Node processes related to frontend
NODE_PIDS=$(pgrep -f "node.*frontend\|vite.*frontend")
for pid in $NODE_PIDS; do
    if kill -0 $pid 2>/dev/null; then
        safe_kill $pid "Frontend Node process"
    fi
done

# Clean up WebSocket connections (if any)
log_info "Cleaning up WebSocket connections..."
WS_PIDS=$(lsof -t -i:12001 2>/dev/null)
for pid in $WS_PIDS; do
    if kill -0 $pid 2>/dev/null; then
        safe_kill $pid "WebSocket connection"
    fi
done

# Clean up ports if still occupied
log_info "Checking for occupied ports..."

check_port() {
    local port=$1
    local service=$2
    
    if lsof -i:$port >/dev/null 2>&1; then
        log_warning "Port $port ($service) is still occupied"
        PIDS=$(lsof -t -i:$port)
        for pid in $PIDS; do
            safe_kill $pid "Process on port $port"
        done
    else
        log_success "Port $port ($service) is free"
    fi
}

check_port 12001 "Backend API"
check_port 12000 "Frontend"

# Remove any lock files
log_info "Cleaning up lock files..."
rm -f .backend.pid .frontend.pid 2>/dev/null

# Optional: Clean up temporary files
if [ "$1" = "--clean" ]; then
    log_info "Cleaning temporary files..."
    rm -rf logs/*.log.* 2>/dev/null
    rm -rf __pycache__ 2>/dev/null
    find . -name "*.pyc" -delete 2>/dev/null
    log_success "Temporary files cleaned"
fi

# Display final status
echo ""
log_success "🎉 reVoAgent Enhanced Platform stopped!"
echo ""
echo "📊 Final Status:"
echo "   Backend: Stopped"
echo "   Frontend: Stopped"
echo "   Ports: Released"
echo "   Lock files: Removed"
echo ""

if [ "$1" = "--clean" ]; then
    echo "🧹 Cleanup completed"
else
    echo "💡 Use --clean flag to remove temporary files: ./stop_enhanced.sh --clean"
fi

echo ""
echo "🚀 To restart: ./start_enhanced.sh"
echo ""

log_info "Platform shutdown complete"