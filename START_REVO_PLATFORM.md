# reVoAgent Platform Startup Guide

This guide explains how to start the enhanced reVoAgent platform with the LLM integration.

## Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher
- npm or yarn

## Starting the Backend

The backend server provides the LLM integration and API endpoints.

```bash
# Start the LLM-integrated backend
./start_llm_integrated_backend.sh
```

This script will:
1. Create a Python virtual environment if it doesn't exist
2. Install required dependencies
3. Start the backend server on port 12001

You should see output indicating the server has started successfully.

## Starting the Frontend

The frontend provides the user interface and connects to the backend API.

```bash
# Start the frontend development server
./start_frontend.sh
```

This script will:
1. Navigate to the frontend directory
2. Install Node.js dependencies if needed
3. Set required environment variables
4. Start the development server on port 3000

Once started, you can access the application at:
http://localhost:3000

## Testing the Integration

1. When the application loads, it will automatically open the LLM Test page
2. Check the status indicator in the top-right to verify backend connection
3. Select a model from the dropdown (if available)
4. Type a message and click Send
5. The LLM should respond with a generated message

## Additional Testing Tools

You can test the backend API directly using curl:

```bash
# Test backend health
curl http://localhost:12001/health

# Test LLM chat API
curl -X POST http://localhost:12001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, how are you?", "model": "deepseek-r1"}'
```

## Available Models

The system supports multiple LLM models:

1. **deepseek-r1** - Default CPU-optimized model
2. **llama-3.1-70b** - Local Llama model (when available)
3. Other API-based models (when API keys are configured)

## API Keys (Optional)

To use API-based models, set these environment variables before starting the backend:

```bash
export DEEPSEEK_API_KEY=your_key_here
export OPENAI_API_KEY=your_key_here
export ANTHROPIC_API_KEY=your_key_here
export GEMINI_API_KEY=your_key_here
```

## Troubleshooting

1. **Backend fails to start**
   - Check Python version: `python3 --version`
   - Verify dependencies: `pip list`
   - Check for error messages in terminal

2. **Frontend fails to start**
   - Check Node.js version: `node --version`
   - Verify dependencies: `npm list --depth=0`
   - Check for error messages in terminal

3. **Connection issues**
   - Verify the backend is running: `curl http://localhost:12001/health`
   - Check if frontend environment variables are set correctly
   - Inspect browser console for connection errors

4. **LLM not responding**
   - Check backend logs for LLM initialization issues
   - Verify that at least one model is available
   - Try using the CPU-optimized model if other models fail