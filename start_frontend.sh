#!/bin/bash
# Start the enhanced frontend with proper environment variables

set -e

# Change to frontend directory
cd "$(dirname "$0")/frontend"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Node.js is required but not installed. Please install Node.js before proceeding."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "npm is required but not installed. Please install npm before proceeding."
    exit 1
fi

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Set environment variables for development
export VITE_API_URL="http://localhost:12001"
export VITE_WS_URL="ws://localhost:12001"

# Start the frontend in development mode
echo "Starting frontend server..."
npm run dev