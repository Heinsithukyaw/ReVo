#!/bin/bash
# Start script for the reVoAgent backend with fallback LLM system

echo "Starting reVoAgent Backend with Fallback LLM System..."

# Ensure required directories exist
mkdir -p models
mkdir -p logs

# Check if llama-cpp-python is installed for GGUF support
pip show llama-cpp-python > /dev/null
if [ $? -ne 0 ]; then
    echo "Installing llama-cpp-python for GGUF model support..."
    pip install llama-cpp-python
fi

# Start the backend
python backend_main_fallback.py > logs/fallback_backend.log 2>&1 &
BACKEND_PID=$!

echo "Backend started with PID: $BACKEND_PID"
echo "Log file: logs/fallback_backend.log"
echo
echo "API is available at: http://localhost:12001"
echo "API Documentation: http://localhost:12001/docs"
echo "Health Check: http://localhost:12001/health"
echo
echo "Use 'kill $BACKEND_PID' to stop the server"

# Save PID for later use
echo $BACKEND_PID > .backend_pid