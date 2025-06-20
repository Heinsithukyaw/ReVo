# reVoAgent LLM Integration Documentation

This document explains the implementation of the LLM integration for the reVoAgent platform.

## Overview

The LLM integration is implemented in a 4-phase plan:

1. **Phase 1: Fix Backend LLM Integration**
   - Create `llm_manager.py` to centralize LLM operations
   - Replace mock responses with real LLM calls
   - Add proper configuration management
   - Set up CPU-optimized DeepSeek integration

2. **Phase 2: Fix Frontend-Backend Connection**
   - Update frontend API service to match backend endpoints
   - Fix runtime environment URL detection
   - Ensure proper CORS and WebSocket configuration

3. **Phase 3: Add Local + Fallback LLM System**
   - Implement local model support (DeepSeek R1 GGUF, Llama)
   - Add API fallback configuration
   - Implement intelligent model switching

4. **Phase 4: Clean Architecture & Testing**
   - Add comprehensive error handling
   - Test full stack integration
   - Validate LLM responses

## Phase 1: Backend LLM Integration

### Implementation Details

1. **LLM Manager (`src/revoagent/ai/llm_manager.py`)**
   - Centralizes all LLM operations
   - Manages multiple model backends:
     - Local models via ModelManager
     - API-based models via LLMBridge
     - CPU-optimized DeepSeek model
   - Provides unified interface for all LLM operations
   - Handles automatic fallbacks and resource optimization

2. **Enhanced Backend (`backend_main_enhanced.py`)**
   - Replaces mock responses with real LLM calls
   - Uses LLM Manager for all AI operations
   - Implements enhanced configuration management
   - Provides improved error handling
   - Maintains compatibility with existing endpoints

3. **CPU-Optimized DeepSeek (`src/revoagent/ai/cpu_optimized_deepseek.py`)**
   - Provides a reliable CPU-compatible implementation
   - Uses template-based generation when resources are limited
   - Fall back gracefully when GPU is not available
   - Optimized for performance on CPU-only systems

4. **Configuration Management**
   - Uses YAML configuration files in the `config` directory
   - Environment variables for sensitive information (API keys)
   - Default fallbacks when configuration is not available
   - Centralized configuration loading

### Architecture

The LLM Integration architecture follows a layered approach:

1. **API Layer** (`backend_main_enhanced.py`)
   - Handles HTTP and WebSocket requests
   - Routes requests to appropriate services
   - Formats responses for clients

2. **LLM Management Layer** (`llm_manager.py`)
   - Coordinates between different LLM backends
   - Manages resource allocation
   - Handles fallbacks and error recovery
   - Provides unified interface for all LLM operations

3. **Model Implementation Layer**
   - Local models via ModelManager
   - API-based models via LLMBridge
   - CPU-optimized models

4. **Infrastructure Layer**
   - Configuration management
   - Logging
   - Error handling
   - Performance monitoring

### API Endpoints

The following API endpoints are implemented:

- **GET /health** - Overall health check with LLM status
- **GET /api/models** - List available AI models
- **POST /api/chat** - Generate responses using LLM
- **POST /api/chat/multi-agent** - Multi-agent collaboration
- **POST /api/agent** - Single specialized agent
- **GET /api/config/llm** - Get LLM configuration
- **WebSocket /ws/chat** - Real-time chat with streaming responses

### Configuration

Configuration is loaded from:

1. `config/environment.yaml` - Main configuration
2. `config/ports.yaml` - Port configuration
3. Environment variables - API keys and sensitive data

## Usage

### Starting the LLM-Integrated Backend

```bash
./start_llm_integrated_backend.sh
```

This script:
1. Creates a virtual environment
2. Installs dependencies
3. Starts the enhanced backend

### Environment Variables

Set the following environment variables for API access:

```bash
export DEEPSEEK_API_KEY=your_key_here  # For DeepSeek API access
export OPENAI_API_KEY=your_key_here    # For OpenAI models
export ANTHROPIC_API_KEY=your_key_here # For Anthropic models
export GEMINI_API_KEY=your_key_here    # For Gemini models
```

### Testing

Test the enhanced backend with:

```bash
curl http://localhost:12001/health
```

You should see a health check response that includes LLM status.

To test chat:

```bash
curl -X POST http://localhost:12001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello, how are you?","model":"deepseek-r1"}'
```

## Next Steps

- Implement Phase 2: Fix Frontend-Backend Connection
- Implement Phase 3: Add Local + Fallback LLM System
- Implement Phase 4: Clean Architecture & Testing