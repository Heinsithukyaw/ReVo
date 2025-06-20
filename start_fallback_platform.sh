#!/bin/bash
# Start the full reVoAgent platform with fallback LLM system

echo "Starting reVoAgent Platform with Fallback LLM System..."

# Create required directories
mkdir -p logs
mkdir -p models

# Check for required packages
pip show llama-cpp-python > /dev/null
if [ $? -ne 0 ]; then
    echo "Installing llama-cpp-python for GGUF model support..."
    pip install llama-cpp-python
fi

# Start backend
echo "Starting backend with fallback LLM system..."
python backend_main_fallback.py > logs/fallback_backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend started with PID: $BACKEND_PID"
echo $BACKEND_PID > .backend_pid

# Wait for backend to initialize
echo "Waiting for backend to initialize..."
sleep 5

# Start frontend
echo "Starting frontend..."
cd frontend
npm start > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo "Frontend started with PID: $FRONTEND_PID"
echo $FRONTEND_PID > .frontend_pid

echo
echo "ReVoAgent Platform started!"
echo
echo "Backend API: http://localhost:12001"
echo "Frontend: http://localhost:3000"
echo
echo "API Documentation: http://localhost:12001/docs"
echo "Health Check: http://localhost:12001/health"
echo
echo "Log files:"
echo "- Backend: logs/fallback_backend.log"
echo "- Frontend: logs/frontend.log"
echo
echo "To stop the platform, run: ./stop_fallback_platform.sh"