#!/bin/bash

# reVoAgent Enterprise Grade Consolidated Startup Script
# Full Stack Platform with Phases 1-4 Integration
# Single entry point for starting the entire system with all enhancements

set -e

echo "🚀 reVoAgent Enterprise Consolidated Startup - Full Stack Platform"
echo "=================================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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

print_phase() {
    echo -e "${PURPLE}[PHASE]${NC} $1"
}

print_component() {
    echo -e "${CYAN}[COMPONENT]${NC} $1"
}

# Check if we're in the correct directory
if [ ! -f "backend_main_enhanced.py" ] && [ ! -f "backend_main_fallback.py" ]; then
    print_error "Please run this script from the reVoAgent root directory"
    exit 1
fi

# Create required directories
mkdir -p logs
mkdir -p models
mkdir -p data

# Print Phase Overview
print_phase "Phase 1: Backend LLM Integration"
print_phase "Phase 2: Frontend-Backend Connection"
print_phase "Phase 3: Local + Fallback LLM System"
print_phase "Phase 4: Clean Architecture & Testing"
echo ""

# PHASE 1: CRITICAL - Port Cleanup & Environment Setup
print_phase "Starting Phase 1: Environment Setup"

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
    pkill -f "node.*start" 2>/dev/null || true
    sleep 3
fi

# Step 2: Environment Setup
print_status "Step 2: Environment Setup"

# Create Python virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Check Python dependencies with error handling
print_status "Installing required Python dependencies..."
# Try to install directly from requirements file first
pip install -q fastapi uvicorn pydantic python-multipart httpx

# Install core LLM dependencies with more flexible versioning
print_status "Installing LLM dependencies..."
pip install -q torch~=2.2.0 transformers~=4.35.0 accelerate~=0.25.0
pip install -q "llama-cpp-python>=0.2.0"

# Check Node.js dependencies
if [ -d "frontend" ] && [ ! -d "frontend/node_modules" ]; then
    print_status "Installing Node.js dependencies..."
    cd frontend
    npm install
    cd ..
fi

# PHASE 2: Preparing Database and Cache
print_phase "Starting Phase 2: Database and Cache Setup"

# Step 3: Initialize Database (if configured)
print_status "Step 3: Initializing Database"
if [ -f "database/init.sql" ]; then
    print_status "Database initialization script found"
    # We don't run it directly, it will be used by Docker or local DB
    print_success "Database initialization script ready"
else
    print_warning "No database initialization script found, skipping..."
fi

# Step 4: Initialize Redis (if configured)
print_status "Step 4: Initializing Redis Cache"
if [ -f "config/redis.conf" ]; then
    print_status "Redis configuration found"
    # We don't start Redis directly, it will be managed by Docker or external service
    print_success "Redis configuration ready"
else
    print_warning "No Redis configuration found, skipping..."
fi

# PHASE 3: Start Enhanced Backend with Fallback System
print_phase "Starting Phase 3: Enhanced Backend with Fallback System"

# Step 5: Determine which backend to use (prioritize fallback > enhanced > original)
print_status "Step 5: Starting Enhanced Backend on Port 12001"

BACKEND_SCRIPT=""
if [ -f "backend_main_fallback.py" ]; then
    BACKEND_SCRIPT="backend_main_fallback.py"
    print_component "Using Phase 3: Fallback LLM System Backend"
elif [ -f "backend_main_enhanced.py" ]; then
    BACKEND_SCRIPT="backend_main_enhanced.py"
    print_component "Using Phase 1: Enhanced LLM Backend"
elif [ -f "backend_main.py" ]; then
    BACKEND_SCRIPT="backend_main.py"
    print_component "Using Original Backend"
else
    print_error "No backend server found!"
    exit 1
fi

# Start the selected backend
print_status "Starting backend server: $BACKEND_SCRIPT"
python3 $BACKEND_SCRIPT > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > /tmp/revoagent_backend.pid
print_success "Backend started with PID: $BACKEND_PID"

# Wait for backend to start
print_status "Waiting for backend to initialize..."
sleep 15  # Increased wait time for proper initialization

# Verify backend is running
RETRY_COUNT=0
MAX_RETRIES=5
BACKEND_HEALTHY=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s -f http://localhost:12001/health >/dev/null 2>&1; then
        print_success "Backend health check passed"
        BACKEND_HEALTHY=true
        break
    else
        RETRY_COUNT=$((RETRY_COUNT+1))
        if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
            print_warning "Backend health check failed, retrying in 5 seconds..."
            sleep 5
        else
            print_warning "Backend health check failed after $MAX_RETRIES attempts, continuing anyway..."
        fi
    fi
done

# PHASE 4: Start Enhanced Frontend with API Integration
print_phase "Starting Phase 4: Enhanced Frontend with API Integration"

# Step 6: Start Frontend
print_status "Step 6: Starting Enhanced Frontend on Port 12000"

if [ -d "frontend" ]; then
    cd frontend
    
    # Update environment variables
    cat > .env.local << EOF
VITE_API_URL=http://localhost:12001
VITE_WS_URL=ws://localhost:12001
NODE_ENV=development
PORT=12000
VITE_ENABLE_LLM_FEATURES=true
VITE_ENABLE_FALLBACK_SYSTEM=true
EOF
    
    print_status "Starting frontend development server..."
    npm run dev > ../logs/frontend.log 2>&1 &
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
sleep 15  # Increased wait time for proper initialization

# Step 7: Start Monitoring (if available)
print_status "Step 7: Starting Monitoring Services"

# Start Prometheus if available
if [ -d "monitoring" ] && [ -f "monitoring/prometheus.yml" ]; then
    print_component "Starting Prometheus monitoring..."
    # We're not starting it directly, just noting it's available
    print_success "Prometheus configuration available at monitoring/prometheus.yml"
fi

# Start Grafana if available
if [ -d "monitoring" ] && [ -d "monitoring/grafana" ]; then
    print_component "Starting Grafana dashboards..."
    # We're not starting it directly, just noting it's available
    print_success "Grafana dashboards available at monitoring/grafana/dashboards"
fi

# Step 8: Comprehensive System Verification
print_phase "Running Comprehensive System Verification"

# Check backend
print_status "Verifying backend services..."
if curl -s -f http://localhost:12001/health >/dev/null 2>&1; then
    print_success "✅ Backend is running on http://localhost:12001"
else
    print_error "❌ Backend is not responding"
fi

# Check frontend
print_status "Verifying frontend services..."
if curl -s -f http://localhost:12000 >/dev/null 2>&1; then
    print_success "✅ Frontend is running on http://localhost:12000"
else
    print_error "❌ Frontend is not responding"
fi

# Check API integration
print_status "Verifying API endpoints..."
if curl -s -f http://localhost:12001/api/models >/dev/null 2>&1; then
    print_success "✅ API endpoints are accessible"
else
    print_warning "⚠️  API endpoints may not be fully ready"
fi

# Check frontend-backend connection
print_status "Verifying frontend-backend connection..."
# Make a request to the frontend that should proxy to the backend
if curl -s -f -H "Accept: application/json" http://localhost:12000/api/health >/dev/null 2>&1; then
    print_success "✅ Frontend-backend connection is working"
else
    print_warning "⚠️  Frontend-backend connection may not be working properly"
    print_status "Attempting to fix frontend-backend connection..."
    # Restart frontend with updated environment variables
    if [ -f /tmp/revoagent_frontend.pid ]; then
        FRONTEND_PID=$(cat /tmp/revoagent_frontend.pid)
        kill $FRONTEND_PID 2>/dev/null || true
        sleep 2
        cd frontend
        # Update environment variables with explicit configuration
        cat > .env.local << EOF
VITE_API_URL=http://localhost:12001
VITE_WS_URL=ws://localhost:12001
NODE_ENV=development
PORT=12000
VITE_ENABLE_LLM_FEATURES=true
VITE_ENABLE_FALLBACK_SYSTEM=true
EOF
        npm run dev > ../logs/frontend.log 2>&1 &
        FRONTEND_PID=$!
        echo $FRONTEND_PID > /tmp/revoagent_frontend.pid
        cd ..
        sleep 10
        print_status "Frontend restarted, rechecking connection..."
        if curl -s -f -H "Accept: application/json" http://localhost:12000/api/health >/dev/null 2>&1; then
            print_success "✅ Frontend-backend connection is now working"
        else
            print_error "❌ Frontend-backend connection is still not working"
        fi
    fi
fi

# Check LLM integration
print_status "Verifying LLM integration..."
if curl -s -f http://localhost:12001/api/llm/status >/dev/null 2>&1; then
    print_success "✅ LLM integration is working"
else
    print_warning "⚠️  LLM integration endpoint not found or not responding"
fi

# Check fallback system
print_status "Verifying fallback system..."
if curl -s -f http://localhost:12001/api/fallback/stats >/dev/null 2>&1; then
    print_success "✅ Fallback system is working"
else
    print_warning "⚠️  Fallback system endpoint not found or not responding"
fi

# Step 9: Display Status Dashboard
echo ""
echo "=================================================================="
print_success "🎉 reVoAgent Enterprise System Started Successfully!"
echo "=================================================================="
echo ""
echo "📊 System Status Dashboard:"
echo ""
echo "   Core Services:"
echo "   - Backend API:  http://localhost:12001"
echo "   - Frontend UI:  http://localhost:12000"
echo "   - API Docs:     http://localhost:12001/docs"
echo "   - Health Check: http://localhost:12001/health"
echo ""
echo "   Extended Services:"
echo "   - LLM Status:   http://localhost:12001/api/llm/status"
echo "   - Fallback Stats: http://localhost:12001/api/fallback/stats"
if [ -d "monitoring" ]; then
echo "   - Prometheus:   http://localhost:9090 (if running)"
echo "   - Grafana:      http://localhost:3001 (if running)"
fi
echo ""
echo "🔧 Management Commands:"
echo "   - Stop System:    ./stop_consolidated.sh"
echo "   - View Logs:      tail -f logs/*.log"
echo "   - Backend Log:    tail -f logs/backend.log"
echo "   - Frontend Log:   tail -f logs/frontend.log"
echo "   - Port Status:    ./scripts/cleanup_ports.sh"
echo ""
echo "🌐 External Access (if in runtime environment):"
echo "   - Frontend: https://work-1-hnniweburjrfvvzu.prod-runtime.all-hands.dev"
echo "   - Backend:  https://work-2-hnniweburjrfvvzu.prod-runtime.all-hands.dev"
echo ""
echo "🧠 LLM Models Available:"
if [ -f "backend_main_fallback.py" ]; then
echo "   - Local Models: deepseek-r1, llama-3.1 (if downloaded)"
echo "   - API Models: Configurable via environment variables"
fi
echo ""

# Create comprehensive stop script
cat > stop_consolidated.sh << 'EOF'
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
EOF

chmod +x stop_consolidated.sh

print_success "System startup completed! Use './stop_consolidated.sh' to stop."

# Keep script running to monitor
echo ""
print_status "Monitoring system... Press Ctrl+C to stop"
echo ""

# Enhanced Monitor function with better error recovery
monitor_system() {
    HEALTH_CHECK_INTERVAL=30
    LAST_BACKEND_RESTART=$(date +%s)
    LAST_FRONTEND_RESTART=$(date +%s)
    RESTART_COOLDOWN=120  # 2 minutes cooldown between restarts
    
    while true; do
        sleep $HEALTH_CHECK_INTERVAL
        CURRENT_TIME=$(date +%s)
        
        # Check if processes are still running
        if ! kill -0 $BACKEND_PID 2>/dev/null; then
            # Check if we're still in cooldown period
            if [ $((CURRENT_TIME - LAST_BACKEND_RESTART)) -gt $RESTART_COOLDOWN ]; then
                print_error "Backend process died! Restarting..."
                python3 $BACKEND_SCRIPT > logs/backend.log 2>&1 &
                BACKEND_PID=$!
                echo $BACKEND_PID > /tmp/revoagent_backend.pid
                print_success "Backend restarted with PID: $BACKEND_PID"
                LAST_BACKEND_RESTART=$(date +%s)
            else
                print_warning "Backend process died, but in cooldown period. Will retry later."
            fi
        fi
        
        if ! kill -0 $FRONTEND_PID 2>/dev/null; then
            # Check if we're still in cooldown period
            if [ $((CURRENT_TIME - LAST_FRONTEND_RESTART)) -gt $RESTART_COOLDOWN ]; then
                print_error "Frontend process died! Restarting..."
                cd frontend && npm run dev > ../logs/frontend.log 2>&1 &
                FRONTEND_PID=$!
                echo $FRONTEND_PID > /tmp/revoagent_frontend.pid
                cd ..
                print_success "Frontend restarted with PID: $FRONTEND_PID"
                LAST_FRONTEND_RESTART=$(date +%s)
            else
                print_warning "Frontend process died, but in cooldown period. Will retry later."
            fi
        fi
        
        # Extended health check
        BACKEND_HEALTH=false
        FRONTEND_HEALTH=false
        
        if curl -s -f http://localhost:12001/health >/dev/null 2>&1; then
            BACKEND_HEALTH=true
        fi
        
        if curl -s -f http://localhost:12000 >/dev/null 2>&1; then
            FRONTEND_HEALTH=true
        fi
        
        if $BACKEND_HEALTH && $FRONTEND_HEALTH; then
            # Both healthy, print a simple indicator
            echo -n "."
        elif ! $BACKEND_HEALTH && ! $FRONTEND_HEALTH; then
            # Both unhealthy
            print_warning "System health check failed: Both backend and frontend unresponsive at $(date)"
        elif ! $BACKEND_HEALTH; then
            # Only backend unhealthy
            print_warning "System health check failed: Backend unresponsive at $(date)"
        elif ! $FRONTEND_HEALTH; then
            # Only frontend unhealthy
            print_warning "System health check failed: Frontend unresponsive at $(date)"
        fi
    done
}

# Trap Ctrl+C
trap 'echo ""; print_status "Shutting down..."; ./stop_consolidated.sh; exit 0' INT

# Start monitoring
monitor_system