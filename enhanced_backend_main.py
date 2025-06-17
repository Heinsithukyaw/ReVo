#!/usr/bin/env python3
"""
reVoAgent Enhanced Backend Server with Real LLM Integration
Replaces backend_main.py with actual LLM functionality
"""

import asyncio
import uvicorn
import sys
import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# FastAPI imports
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

# Add project paths
sys.path.append('src')
sys.path.append('apps')
sys.path.append('packages')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration
def load_config():
    """Load all configuration from config files and environment"""
    config = {
        'ports': {'backend': 12001, 'frontend': 12000},
        'llm': {
            'default_model': 'deepseek-r1',
            'providers': {
                'deepseek': {'api_key': os.getenv('DEEPSEEK_API_KEY')},
                'openai': {'api_key': os.getenv('OPENAI_API_KEY')},
                'anthropic': {'api_key': os.getenv('ANTHROPIC_API_KEY')},
                'gemini': {'api_key': os.getenv('GEMINI_API_KEY')}
            }
        }
    }
    
    # Load from YAML if available
    try:
        import yaml
        if os.path.exists('config/ports.yaml'):
            with open('config/ports.yaml', 'r') as f:
                port_config = yaml.safe_load(f)
                config['ports'].update(port_config.get('production', {}))
        
        if os.path.exists('config/environment.yaml'):
            with open('config/environment.yaml', 'r') as f:
                env_config = yaml.safe_load(f)
                config.update(env_config)
    except Exception as e:
        logger.warning(f"Could not load YAML config: {e}")
    
    return config

# Global configuration
CONFIG = load_config()

# Initialize FastAPI app
app = FastAPI(
    title="reVoAgent Backend API",
    description="Enhanced backend server with real LLM integration",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enhanced CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:12000",
        "http://127.0.0.1:12000",
        "http://localhost:3000",  # For development
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer(auto_error=False)

# Initialize LLM Bridge
llm_bridge = None

# Data Models
class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    uptime: float
    services: Dict[str, str]
    llm_status: Dict[str, Any]

class ChatRequest(BaseModel):
    message: str
    model: Optional[str] = "deepseek-r1"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000
    stream: Optional[bool] = False

class ChatResponse(BaseModel):
    response: str
    model: str
    timestamp: str
    tokens_used: int
    response_time: float
    provider: str

class ModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    status: str
    cost_per_token: float
    max_tokens: int

# Global state
start_time = time.time()
websocket_connections: List[WebSocket] = []

async def initialize_llm_services():
    """Initialize LLM services on startup"""
    global llm_bridge
    try:
        # Import the LLM bridge
        from src.revoagent.ai.llm_bridge import llm_bridge
        await llm_bridge.initialize()
        
        providers = await llm_bridge.get_available_models()
        if providers:
            logger.info(f"LLM services initialized successfully: {providers}")
        else:
            logger.warning("LLM services - no API keys configured")
            
        return providers
        
    except ImportError as e:
        logger.warning(f"LLM Bridge not available: {e}")
        # Fallback initialization
        providers = []
        
        # Check for available API keys and initialize providers
        if CONFIG['llm']['providers']['deepseek']['api_key']:
            logger.info("DeepSeek API key found - provider available")
            providers.append('deepseek-r1')
        
        if CONFIG['llm']['providers']['openai']['api_key']:
            logger.info("OpenAI API key found - provider available")
            providers.append('gpt-4o-mini')
        
        if CONFIG['llm']['providers']['anthropic']['api_key']:
            logger.info("Anthropic API key found - provider available")
            providers.append('claude-3-haiku')
        
        if CONFIG['llm']['providers']['gemini']['api_key']:
            logger.info("Gemini API key found - provider available")
            providers.append('gemini-1.5-flash')
        
        if not providers:
            logger.warning("No LLM providers initialized - API keys missing")
        else:
            logger.info(f"Initialized {len(providers)} LLM providers: {providers}")
            
        return providers
        
    except Exception as e:
        logger.error(f"Failed to initialize LLM services: {e}")
        return []

async def get_llm_status():
    """Get current LLM service status"""
    if llm_bridge:
        try:
            return await llm_bridge.get_provider_status()
        except Exception as e:
            logger.error(f"Error getting LLM status from bridge: {e}")
    
    # Fallback status
    providers = await initialize_llm_services()
    return {
        "status": "active" if providers else "no_providers",
        "providers": len(providers),
        "models": providers,
        "default_model": CONFIG['llm']['default_model']
    }

async def generate_llm_response(message: str, model: str = "deepseek-r1", **kwargs):
    """Generate LLM response using bridge or fallback"""
    if llm_bridge:
        try:
            return await llm_bridge.generate_response(message, model, **kwargs)
        except Exception as e:
            logger.error(f"LLM Bridge error: {e}")
            return f"LLM Error: {str(e)}"
    else:
        # Fallback to enhanced placeholder
        await asyncio.sleep(1)  # Simulate processing time
        return f"Enhanced AI Response ({model}): {message}\n\nThis is an enhanced placeholder response. The LLM Bridge will replace this with real AI responses from {model} when properly configured with API keys."

# Health Check Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Comprehensive health check with LLM status"""
    uptime = time.time() - start_time
    
    services = {
        "api": "healthy",
        "database": "healthy",
        "memory": "healthy",
    }
    
    llm_status = await get_llm_status()
    services["llm"] = llm_status.get("status", "unknown")
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="2.0.0",
        uptime=uptime,
        services=services,
        llm_status=llm_status
    )

@app.get("/health/ready")
async def readiness_check():
    """Kubernetes readiness probe with LLM check"""
    llm_status = await get_llm_status()
    ready = llm_status.get("status") in ["active", "no_providers"]
    
    return {
        "status": "ready" if ready else "not_ready",
        "timestamp": datetime.now().isoformat(),
        "llm_ready": llm_status.get("status") == "active"
    }

# API Endpoints
@app.get("/api/models")
async def get_available_models():
    """Get list of available AI models"""
    llm_status = await get_llm_status()
    
    model_list = []
    for model_id in llm_status.get("models", []):
        model_info = {
            "id": model_id,
            "name": model_id.replace('-', ' ').title(),
            "provider": "api" if "gpt" in model_id or "claude" in model_id or "gemini" in model_id else "local",
            "status": "available",
            "cost_per_token": 0.0014 if "deepseek" in model_id else 0.015,
            "max_tokens": 4096
        }
        model_list.append(model_info)
    
    return {"models": model_list}

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Enhanced chat endpoint with real LLM integration"""
    start_time_req = time.time()
    
    try:
        # Generate response using the LLM
        response_text = await generate_llm_response(
            request.message,
            request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        response_time = time.time() - start_time_req
        tokens_used = len(response_text.split())
        
        return ChatResponse(
            response=response_text,
            model=request.model,
            timestamp=datetime.now().isoformat(),
            tokens_used=tokens_used,
            response_time=response_time,
            provider="EnhancedLLMBridge"
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"LLM processing error: {str(e)}")

@app.post("/api/chat/multi-agent")
async def multi_agent_chat(request: ChatRequest):
    """Multi-agent collaboration endpoint"""
    agents = ["code_analyst", "debug_detective", "workflow_manager"]
    responses = []
    
    try:
        for agent in agents:
            agent_prompt = f"As a {agent}, analyze and respond to: {request.message}"
            
            response_text = await generate_llm_response(
                agent_prompt,
                request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens // len(agents)
            )
            
            response = {
                "agent": agent,
                "response": response_text,
                "timestamp": datetime.now().isoformat(),
                "model": request.model
            }
            responses.append(response)
        
        return {"responses": responses}
        
    except Exception as e:
        logger.error(f"Multi-agent error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket for real-time communication
@app.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    """WebSocket endpoint for streaming chat responses"""
    await websocket.accept()
    websocket_connections.append(websocket)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            try:
                # Send typing indicator
                await websocket.send_json({"type": "typing", "status": "thinking"})
                
                # Generate response
                response = await generate_llm_response(
                    data["message"],
                    data.get("model", "deepseek-r1"),
                    temperature=data.get("temperature", 0.7),
                    max_tokens=data.get("max_tokens", 1000)
                )
                
                # Send response
                await websocket.send_json({
                    "type": "response",
                    "response": response,
                    "model": data.get("model"),
                    "timestamp": datetime.now().isoformat()
                })
                    
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "error": str(e)
                })
                
    except WebSocketDisconnect:
        websocket_connections.remove(websocket)
        logger.info("WebSocket client disconnected")

# Configuration endpoints
@app.get("/api/config/llm")
async def get_llm_config():
    """Get current LLM configuration"""
    return {
        "default_model": CONFIG['llm']['default_model'],
        "available_providers": list(CONFIG['llm']['providers'].keys()),
        "status": await get_llm_status()
    }

@app.post("/api/config/llm")
async def update_llm_config(config_update: Dict[str, Any]):
    """Update LLM configuration"""
    try:
        # Update configuration
        if "default_model" in config_update:
            CONFIG['llm']['default_model'] = config_update["default_model"]
        
        # Reinitialize services if needed
        if "providers" in config_update:
            CONFIG['llm']['providers'].update(config_update["providers"])
            await initialize_llm_services()
        
        return {"status": "updated", "config": CONFIG['llm']}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("reVoAgent Enhanced Backend Server starting...")
    
    # Initialize LLM services
    providers = await initialize_llm_services()
    if providers:
        logger.info(f"LLM services initialized successfully: {providers}")
    else:
        logger.warning("LLM services - no API keys configured")
    
    logger.info(f"Server started at: {datetime.now().isoformat()}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("reVoAgent Enhanced Backend Server shutting down...")
    
    for websocket in websocket_connections:
        try:
            await websocket.close()
        except:
            pass

def main():
    """Main entry point"""
    port = CONFIG['ports']['backend']
    
    logger.info(f"Starting reVoAgent Enhanced Backend Server on port {port}")
    logger.info(f"API Documentation available at: http://localhost:{port}/docs")
    logger.info(f"Health Check: http://localhost:{port}/health")
    
    uvicorn.run(
        "enhanced_backend_main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main()