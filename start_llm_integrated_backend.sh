#!/bin/bash
# Start the LLM-integrated backend server

set -e

# Create a virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
pip install python-multipart pyyaml

# Make sure config directory exists
mkdir -p config

# Start the backend server
echo "Starting LLM-integrated backend server..."
python backend_main_enhanced.py