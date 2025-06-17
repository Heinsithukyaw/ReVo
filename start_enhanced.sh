#!/bin/bash

# Enhanced Startup Script for reVoAgent
echo "🚀 Starting reVoAgent Enhanced Platform..."

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

# Check if .env file exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    log_success "Environment variables loaded from .env"
else
    log_warning "No .env file found. Using default configuration."
    log_info "Create .env from .env.example: cp .env.example .env"
fi

# Create necessary directories
mkdir -p logs
mkdir -p backup
mkdir -p config
log_success "Directories created"

# Check Python dependencies
log_info "Checking Python dependencies..."
if ! python3 -c "import fastapi, uvicorn, pydantic" 2>/dev/null; then
    log_warning "Installing missing Python dependencies..."
    pip install -r requirements.txt
fi

# Check for enhanced LLM dependencies
if ! python3 -c "import yaml" 2>/dev/null; then
    log_info "Installing enhanced dependencies..."
    pip install PyYAML python-dotenv aiofiles websockets
fi

log_success "Dependencies checked"

# Start enhanced backend
log_info "Starting enhanced backend server..."
if [ -f enhanced_backend_main.py ]; then
    python3 enhanced_backend_main.py &
    BACKEND_PID=$!
    log_success "Enhanced backend started (PID: $BACKEND_PID)"
else
    log_warning "Enhanced backend not found, starting regular backend..."
    python3 backend_main.py &
    BACKEND_PID=$!
    log_success "Regular backend started (PID: $BACKEND_PID)"
fi

# Wait for backend to start
log_info "Waiting for backend to initialize..."
sleep 5

# Check backend health
log_info "Checking backend health..."
for i in {1..10}; do
    if curl -s http://localhost:12001/health > /dev/null 2>&1; then
        log_success "Backend is healthy"
        break
    fi
    if [ $i -eq 10 ]; then
        log_error "Backend health check failed after 10 attempts"
        log_info "Check logs: tail -f logs/revoagent.log"
    fi
    sleep 2
done

# Start frontend (if npm is available)
if command -v npm &> /dev/null; then
    log_info "Starting frontend..."
    cd frontend
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        log_info "Installing frontend dependencies..."
        npm install
    fi
    
    npm run dev &
    FRONTEND_PID=$!
    cd ..
    log_success "Frontend started (PID: $FRONTEND_PID)"
else
    log_warning "npm not found. Please start frontend manually:"
    log_info "   cd frontend && npm install && npm run dev"
fi

# Save PIDs for stopping
echo $BACKEND_PID > .backend.pid
[ ! -z "$FRONTEND_PID" ] && echo $FRONTEND_PID > .frontend.pid

echo ""
log_success "🎉 reVoAgent Enhanced Platform Started!"
echo ""
echo "📊 Services:"
echo "   Backend API: http://localhost:12001"
echo "   API Documentation: http://localhost:12001/docs"
echo "   Frontend: http://localhost:12000"
echo "   Health Check: http://localhost:12001/health"
echo ""
echo "🔧 Management:"
echo "   Stop Platform: ./stop_enhanced.sh"
echo "   Monitor System: ./monitor_enhanced.sh"
echo "   View Logs: tail -f logs/revoagent.log"
echo ""
echo "🧪 Testing:"
echo "   Test Integration: python3 test_enhanced_integration.py"
echo "   Validate Setup: python3 validate_implementation.py"
echo ""

# Display LLM status
log_info "Checking LLM configuration..."
if curl -s http://localhost:12001/api/config/llm 2>/dev/null | grep -q "active"; then
    log_success "LLM providers are active"
else
    log_warning "LLM providers may need configuration. Check API keys in .env"
fi

# Display process information
echo "🔧 Platform running with:"
echo "   Backend PID: $BACKEND_PID"
echo "   Frontend PID: ${FRONTEND_PID:-manual}"
echo ""

# Keep script running and monitor processes
if [ "$1" = "--monitor" ]; then
    log_info "Monitoring mode enabled. Press Ctrl+C to stop."
    while true; do
        sleep 30
        
        # Check if backend is still running
        if ! kill -0 $BACKEND_PID 2>/dev/null; then
            log_error "Backend process died! Restarting..."
            if [ -f enhanced_backend_main.py ]; then
                python3 enhanced_backend_main.py &
                BACKEND_PID=$!
            else
                python3 backend_main.py &
                BACKEND_PID=$!
            fi
            echo $BACKEND_PID > .backend.pid
        fi
        
        # Check if frontend is still running (if we started it)
        if [ ! -z "$FRONTEND_PID" ] && ! kill -0 $FRONTEND_PID 2>/dev/null; then
            log_warning "Frontend process died! Please restart manually."
        fi
    done
else
    log_info "Platform started successfully! Use --monitor flag for continuous monitoring."
fi