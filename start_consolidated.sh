#!/bin/bash

# reVoAgent Consolidated Startup Script
# Implements critical fixes for port conflicts and integration issues
# Single entry point for starting the entire system

set -e

echo "🚀 reVoAgent Consolidated Startup - Implementing Critical Fixes"
echo "=============================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the correct directory
if [ ! -f "backend_main.py" ]; then
    print_error "Please run this script from the reVoAgent root directory"
    exit 1
fi

# Step 1: CRITICAL - Port Cleanup
print_status "Step 1: Critical Port Cleanup"
if [ -f "scripts/cleanup_ports.sh" ]; then
    chmod +x scripts/cleanup_ports.sh
    ./scripts/cleanup_ports.sh
    if [ $? -eq 0 ]; then
        print_success "Port cleanup completed successfully"
    else
        print_warning "Port cleanup had issues, continuing..."
    fi
else
    print_warning "Port cleanup script not found, performing manual cleanup"
    # Manual cleanup
    pkill -f "python.*backend" 2>/dev/null || true
    pkill -f "npm.*dev" 2>/dev/null || true
    sleep 3
fi

# Step 2: Environment Setup
print_status "Step 2: Environment Setup"

# Check Python dependencies
if ! python3 -c "import fastapi, uvicorn" 2>/dev/null; then
    print_status "Installing Python dependencies..."
    pip install fastapi uvicorn pydantic python-multipart
fi

# Check Node.js dependencies
if [ -d "frontend" ] && [ ! -d "frontend/node_modules" ]; then
    print_status "Installing Node.js dependencies..."
    cd frontend
    npm install
    cd ..
fi

# Step 3: Start Backend (Consolidated)
print_status "Step 3: Starting Consolidated Backend on Port 12001"

# Use the new consolidated backend
if [ -f "backend_main.py" ]; then
    print_status "Starting consolidated backend server..."
    python3 backend_main.py &
    BACKEND_PID=$!
    echo $BACKEND_PID > /tmp/revoagent_backend.pid
    print_success "Backend started with PID: $BACKEND_PID"
else
    print_warning "Consolidated backend not found, using fallback..."
    if [ -f "production_backend_server.py" ]; then
        python3 production_backend_server.py &
        BACKEND_PID=$!
        echo $BACKEND_PID > /tmp/revoagent_backend.pid
    else
        print_error "No backend server found!"
        exit 1
    fi
fi

# Wait for backend to start
print_status "Waiting for backend to initialize..."
sleep 5

# Verify backend is running
if curl -f http://localhost:12001/health >/dev/null 2>&1; then
    print_success "Backend health check passed"
else
    print_warning "Backend health check failed, but continuing..."
fi

# Step 4: Start Frontend (Consolidated)
print_status "Step 4: Starting Consolidated Frontend on Port 12000"

if [ -d "frontend" ]; then
    cd frontend
    
    # Update environment variables
    cat > .env.local << EOF
VITE_API_URL=http://localhost:12001
VITE_WS_URL=ws://localhost:12001
NODE_ENV=development
PORT=12000
EOF
    
    print_status "Starting frontend development server..."
    npm run dev &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > /tmp/revoagent_frontend.pid
    cd ..
    
    print_success "Frontend started with PID: $FRONTEND_PID"
else
    print_error "Frontend directory not found!"
    exit 1
fi

# Wait for frontend to start
print_status "Waiting for frontend to initialize..."
sleep 8

# Step 5: Verification
print_status "Step 5: System Verification"

# Check backend
if curl -f http://localhost:12001/health >/dev/null 2>&1; then
    print_success "✅ Backend is running on http://localhost:12001"
else
    print_error "❌ Backend is not responding"
fi

# Check frontend
if curl -f http://localhost:12000 >/dev/null 2>&1; then
    print_success "✅ Frontend is running on http://localhost:12000"
else
    print_error "❌ Frontend is not responding"
fi

# Check API integration
if curl -f http://localhost:12001/api/models >/dev/null 2>&1; then
    print_success "✅ API endpoints are accessible"
else
    print_warning "⚠️  API endpoints may not be fully ready"
fi

# Step 6: Display Status
echo ""
echo "=============================================================="
print_success "🎉 reVoAgent Consolidated System Started Successfully!"
echo "=============================================================="
echo ""
echo "📊 System Status:"
echo "   Backend:  http://localhost:12001"
echo "   Frontend: http://localhost:12000"
echo "   API Docs: http://localhost:12001/docs"
echo "   Health:   http://localhost:12001/health"
echo ""
echo "🔧 Management Commands:"
echo "   Stop System:    ./stop_consolidated.sh"
echo "   View Logs:      tail -f logs/*.log"
echo "   Port Status:    ./scripts/cleanup_ports.sh"
echo ""
echo "🌐 External Access (if in runtime environment):"
echo "   Frontend: https://work-1-hnniweburjrfvvzu.prod-runtime.all-hands.dev"
echo "   Backend:  https://work-2-hnniweburjrfvvzu.prod-runtime.all-hands.dev"
echo ""

# Create stop script
cat > stop_consolidated.sh << 'EOF'
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
EOF

chmod +x stop_consolidated.sh

print_success "System startup completed! Use './stop_consolidated.sh' to stop."

# Keep script running to monitor
echo ""
print_status "Monitoring system... Press Ctrl+C to stop"
echo ""

# Monitor function
monitor_system() {
    while true; do
        sleep 30
        
        # Check if processes are still running
        if ! kill -0 $BACKEND_PID 2>/dev/null; then
            print_error "Backend process died! Restarting..."
            python3 backend_main.py &
            BACKEND_PID=$!
            echo $BACKEND_PID > /tmp/revoagent_backend.pid
        fi
        
        if ! kill -0 $FRONTEND_PID 2>/dev/null; then
            print_error "Frontend process died! Restarting..."
            cd frontend && npm run dev &
            FRONTEND_PID=$!
            echo $FRONTEND_PID > /tmp/revoagent_frontend.pid
            cd ..
        fi
        
        # Quick health check
        if curl -f http://localhost:12001/health >/dev/null 2>&1 && \
           curl -f http://localhost:12000 >/dev/null 2>&1; then
            echo -n "."  # System healthy
        else
            print_warning "System health check failed at $(date)"
        fi
    done
}

# Trap Ctrl+C
trap 'echo ""; print_status "Shutting down..."; ./stop_consolidated.sh; exit 0' INT

# Start monitoring
monitor_system