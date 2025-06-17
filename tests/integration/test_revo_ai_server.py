"""
Test Server for ReVo AI Chat Interface with Real AI Integration
Runs the backend with DeepSeek R1 0528, Llama, OpenAI, and Anthropic fallbacks
"""

import asyncio
import pytest
import logging
import pytest
import os
import pytest
import sys
import pytest
from pathlib import Path
from typing import Dict, Any

# Add packages to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
import pytest

# Import our components
from apps.backend.revo_websocket import (
    websocket_endpoint,
    websocket_health,
    broadcast_system_message,
    get_active_sessions,
    disconnect_session,
    manager
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="ReVo AI Chat Interface",
    description="Advanced Conversational AI Development Platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket endpoint
@app.websocket("/ws/revo")
async def revo_websocket(websocket: WebSocket, token: str = Query(None)):
    """ReVo AI Chat WebSocket endpoint."""
    await websocket_endpoint(websocket, token)

# Health check endpoints
@app.get("/health")
async def health_check():
    """General health check."""
    return {"status": "healthy", "service": "revo_ai_server"}

@app.get("/health/websocket")
async def websocket_health_check():
    """WebSocket service health check."""
    return await websocket_health()

@app.get("/health/llm")
async def llm_health_check():
    """LLM providers health check."""
    try:
        from packages.ai.llm_config import create_llm_client_from_env
        llm_client = create_llm_client_from_env()
        health_results = await llm_client.health_check()
        usage_stats = llm_client.get_usage_stats()
        
        return {
            "status": "healthy",
            "providers": health_results,
            "usage_stats": usage_stats
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

# Session management endpoints
@app.get("/sessions")
async def list_sessions():
    """List active WebSocket sessions."""
    return await get_active_sessions()

@app.post("/sessions/{session_id}/disconnect")
async def force_disconnect_session(session_id: str):
    """Forcefully disconnect a session."""
    return await disconnect_session(session_id)

@app.post("/broadcast")
async def broadcast_message(message: str, message_type: str = "system"):
    """Broadcast a message to all connected sessions."""
    return await broadcast_system_message(message, message_type)

# LLM testing endpoints
@app.post("/test/llm")
@pytest.mark.asyncio
async def test_llm(prompt: str = "Hello, how are you?"):
    """Test LLM functionality."""
    try:
        from packages.ai.llm_config import create_llm_client_from_env
        llm_client = create_llm_client_from_env()
        
        messages = [{"role": "user", "content": prompt}]
        response = await llm_client.chat_completion(messages)
        
        return {
            "status": "success",
            "response": {
                "content": response.content,
                "provider": response.provider.value,
                "model": response.model,
                "tokens_used": response.tokens_used,
                "response_time": response.response_time,
                "cost": response.cost
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@app.post("/test/function-calling")
@pytest.mark.asyncio
async def test_function_calling():
    """Test LLM function calling capability."""
    try:
        from packages.ai.llm_config import create_llm_client_from_env
        llm_client = create_llm_client_from_env()
        
        messages = [
            {"role": "user", "content": "Please run the command 'ls -la' to list files"}
        ]
        
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "run_terminal_command",
                    "description": "Execute a shell command",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string", "description": "Command to execute"}
                        },
                        "required": ["command"]
                    }
                }
            }
        ]
        
        response = await llm_client.chat_completion(messages, tools)
        
        return {
            "status": "success",
            "response": {
                "content": response.content,
                "provider": response.provider.value,
                "model": response.model,
                "function_calls": response.function_calls,
                "tokens_used": response.tokens_used,
                "response_time": response.response_time,
                "cost": response.cost
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

# Configuration endpoint
@app.get("/config/llm")
async def get_llm_config():
    """Get LLM configuration summary."""
    try:
        from packages.ai.llm_config import LLMConfigManager, create_llm_client_from_env
        
        # Get configurations
        configs = LLMConfigManager.get_default_configs()
        summary = LLMConfigManager.get_config_summary(configs)
        
        # Get client stats
        llm_client = create_llm_client_from_env()
        optimal_provider = llm_client.get_optimal_provider()
        
        return {
            "configurations": summary,
            "optimal_provider": optimal_provider.value,
            "fallback_order": [p.value for p in llm_client.fallback_order]
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

# Environment setup endpoint
@app.get("/setup/env-template")
async def get_env_template():
    """Get environment variable template for LLM setup."""
    from packages.ai.llm_config import setup_environment_template
    return {
        "template": setup_environment_template(),
        "instructions": [
            "1. Copy the template to a .env file",
            "2. Fill in your API keys for paid providers",
            "3. Ensure local LLM servers are running",
            "4. Restart the server to apply changes"
        ]
    }

# Static files for frontend (if needed)
if Path("frontend/dist").exists():
    app.mount("/static", StaticFiles(directory="frontend/dist"), name="static")
    
    @app.get("/")
    async def serve_frontend():
        """Serve the frontend application."""
        return HTMLResponse(open("frontend/dist/index.html").read())

# Development test page
@app.get("/test")
@pytest.mark.asyncio
async def test_page():
    """Simple test page for WebSocket connection."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>ReVo AI Chat Test</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #1a1a1a; color: white; }
            .container { max-width: 800px; margin: 0 auto; }
            .chat-box { border: 1px solid #333; height: 400px; overflow-y: auto; padding: 10px; margin: 10px 0; background: #2a2a2a; }
            .message { margin: 5px 0; padding: 5px; border-radius: 5px; }
            .user { background: #0066cc; text-align: right; }
            .revo { background: #333; }
            .agent { background: #660066; }
            .error { background: #cc0000; }
            input[type="text"] { width: 70%; padding: 10px; background: #333; color: white; border: 1px solid #555; }
            button { padding: 10px 20px; background: #0066cc; color: white; border: none; cursor: pointer; }
            button:hover { background: #0088ff; }
            .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
            .connected { background: #006600; }
            .disconnected { background: #cc0000; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 ReVo AI Chat Interface Test</h1>
            <div id="status" class="status disconnected">Disconnected</div>
            <div id="chatBox" class="chat-box"></div>
            <div>
                <input type="text" id="messageInput" placeholder="Type a message or use /help for commands..." />
                <button onclick="sendMessage()">Send</button>
                <button onclick="testLLM()">Test LLM</button>
                <button onclick="testFunctionCalling()">Test Functions</button>
            </div>
            <div style="margin-top: 20px;">
                <h3>Quick Commands:</h3>
                <button onclick="sendQuickMessage('/help')">Help</button>
                <button onclick="sendQuickMessage('/status')">Status</button>
                <button onclick="sendQuickMessage('/run ls -la')">List Files</button>
                <button onclick="sendQuickMessage('Create a Python function to calculate fibonacci')">AI Request</button>
            </div>
        </div>

        <script>
            let ws = null;
            const chatBox = document.getElementById('chatBox');
            const messageInput = document.getElementById('messageInput');
            const statusDiv = document.getElementById('status');

            function connect() {
                ws = new WebSocket('ws://localhost:8000/ws/revo?token=test_token');
                
                ws.onopen = function() {
                    statusDiv.textContent = 'Connected to ReVo AI';
                    statusDiv.className = 'status connected';
                    addMessage('system', 'Connected to ReVo AI Chat Interface');
                };
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    handleMessage(data);
                };
                
                ws.onclose = function() {
                    statusDiv.textContent = 'Disconnected';
                    statusDiv.className = 'status disconnected';
                    addMessage('system', 'Disconnected from server');
                    setTimeout(connect, 3000); // Reconnect after 3 seconds
                };
                
                ws.onerror = function(error) {
                    addMessage('error', 'WebSocket error: ' + error);
                };
            }

            function handleMessage(data) {
                if (data.type === 'message') {
                    const msg = data.data;
                    addMessage(msg.sender, msg.content, msg.message_type);
                } else if (data.type === 'status') {
                    addMessage('system', 'Status: ' + JSON.stringify(data.data));
                } else if (data.type === 'error') {
                    addMessage('error', 'Error: ' + data.data.message);
                }
            }

            function addMessage(sender, content, type = 'text') {
                const messageDiv = document.createElement('div');
                messageDiv.className = 'message ' + sender;
                
                const timestamp = new Date().toLocaleTimeString();
                const senderName = sender === 'user' ? 'You' : 
                                 sender === 'revo' ? 'ReVo AI' : 
                                 sender === 'agent' ? 'Agent' : 'System';
                
                messageDiv.innerHTML = `<strong>${senderName}</strong> <small>(${timestamp})</small><br/>${content}`;
                chatBox.appendChild(messageDiv);
                chatBox.scrollTop = chatBox.scrollHeight;
            }

            function sendMessage() {
                const message = messageInput.value.trim();
                if (message && ws && ws.readyState === WebSocket.OPEN) {
                    addMessage('user', message);
                    ws.send(JSON.stringify({
                        type: 'message',
                        data: { content: message }
                    }));
                    messageInput.value = '';
                }
            }

            function sendQuickMessage(message) {
                messageInput.value = message;
                sendMessage();
            }

            function testLLM() {
                fetch('/test/llm', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt: 'Hello, please introduce yourself as ReVo AI' })
                })
                .then(response => response.json())
                .then(data => {
                    addMessage('system', 'LLM Test Result: ' + JSON.stringify(data, null, 2));
                })
                .catch(error => {
                    addMessage('error', 'LLM Test Error: ' + error);
                });
            }

            function testFunctionCalling() {
                fetch('/test/function-calling', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    addMessage('system', 'Function Calling Test: ' + JSON.stringify(data, null, 2));
                })
                .catch(error => {
                    addMessage('error', 'Function Calling Test Error: ' + error);
                });
            }

            messageInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });

            // Connect on page load
            connect();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

async def startup_event():
    """Startup event handler."""
    logger.info("🚀 Starting ReVo AI Chat Interface Server")
    
    # Check LLM configuration
    try:
        from packages.ai.llm_config import create_llm_client_from_env, LLMConfigManager
        
        configs = LLMConfigManager.get_default_configs()
        logger.info(f"Found {len(configs)} LLM configurations")
        
        llm_client = create_llm_client_from_env()
        optimal_provider = llm_client.get_optimal_provider()
        logger.info(f"Optimal LLM provider: {optimal_provider.value}")
        
        # Test LLM connection
        test_response = await llm_client.chat_completion([
            {"role": "user", "content": "Hello, please respond with 'ReVo AI is ready!'"}
        ])
        
        if test_response.error:
            logger.warning(f"LLM test failed: {test_response.error}")
        else:
            logger.info(f"✅ LLM test successful with {test_response.provider.value}: {test_response.content}")
        
    except Exception as e:
        logger.error(f"❌ LLM initialization failed: {e}")
        logger.info("Server will start but AI features may not work properly")
    
    logger.info("🌐 Server ready at http://localhost:8000")
    logger.info("🧪 Test page available at http://localhost:8000/test")
    logger.info("📊 Health check at http://localhost:8000/health")

# Add startup event
app.add_event_handler("startup", startup_event)

if __name__ == "__main__":
    # Set up environment variables for development
    os.environ.setdefault("DEEPSEEK_ENDPOINT", "http://localhost:8001")
    os.environ.setdefault("LLAMA_ENDPOINT", "http://localhost:11434")
    
    print("🚀 ReVo AI Chat Interface Server")
    print("=" * 50)
    print("Starting server with multi-LLM support:")
    print("  🧠 Primary: DeepSeek R1 0528 (Local)")
    print("  🦙 Secondary: Llama (Local)")
    print("  ☁️  Fallback: OpenAI GPT-4")
    print("  🤖 Emergency: Anthropic Claude")
    print("=" * 50)
    
    uvicorn.run(
        "test_revo_ai_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )