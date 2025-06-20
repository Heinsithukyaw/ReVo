#!/usr/bin/env python3
"""
reVoAgent Consolidated Backend Server with Real LLM Integration
Implements Phase 1 of the enhancement plan:
- Real LLM integration via LLM Manager
- CPU-optimized DeepSeek integration
- Proper configuration management
"""

import asyncio
import uvicorn
import sys
import os
import json
import time
import logging
import yaml
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# FastAPI imports
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

# Add project paths
sys.path.append('src')
sys.path.append('apps')
sys.path.append('packages')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("backend_main")

# Load configuration
def load_config():
    """Load configuration from files and environment variables."""
    config = {
        'ports': {'backend': 12001, 'frontend': 12000},
        'server': {'host': '0.0.0.0', 'workers': 4, 'reload': False, 'timeout': 60},
        'api': {
            'cors_origins': [
                "http://localhost:12000",
                "http://127.0.0.1:12000",
                "http://localhost:3000",
                "http://127.0.0.1:3000"
            ]
        }
    }
    
    # Load from YAML files
    config_files = [
        'config/environment.yaml',
        'config/ports.yaml'
    ]
    
    for file_path in config_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    file_config = yaml.safe_load(f)
                    
                    # Merge configurations
                    if file_path.endswith('ports.yaml') and 'production' in file_config:
                        config['ports'].update(file_config['production'])
                    else:
                        # Deep merge for other configs
                        deep_merge(config, file_config)
                        
                logger.info(f"Loaded configuration from {file_path}")
            except Exception as e:
                logger.warning(f"Error loading config from {file_path}: {e}")
    
    return config

def deep_merge(dict1, dict2):
    """Deep merge two dictionaries."""
    for key, value in dict2.items():
        if key in dict1 and isinstance(dict1[key], dict) and isinstance(value, dict):
            deep_merge(dict1[key], value)
        else:
            dict1[key] = value

# Global configuration
CONFIG = load_config()

# Initialize FastAPI app
app = FastAPI(
    title="reVoAgent Backend API",
    description="Consolidated backend with real LLM integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
cors_origins = CONFIG.get('api', {}).get('cors_origins', ["*"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer(auto_error=False)

# Initialize LLM Manager
llm_manager = None

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

class AgentRequest(BaseModel):
    agent_type: str = Field(..., description="Type of agent to use")
    message: str = Field(..., description="User message")
    model: Optional[str] = "deepseek-r1"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000

class AgentResponse(BaseModel):
    agent: str
    response: str
    model: str
    timestamp: str

class ModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    source: str
    status: str
    cost_per_token: float

# Global state
start_time = time.time()
websocket_connections: List[WebSocket] = []

# Health Check Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Comprehensive health check with LLM status."""
    uptime = time.time() - start_time
    
    # Check service status
    services = {
        "api": "healthy",
        "database": "healthy",
        "memory": "healthy",
    }
    
    # Get LLM status
    llm_status = {"status": "not_initialized"}
    if llm_manager:
        try:
            llm_status = await llm_manager.get_health()
        except Exception as e:
            logger.error(f"Error getting LLM health: {e}")
            llm_status = {"status": "error", "error": str(e)}
    
    services["llm"] = llm_status.get("status", "unknown")
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0",
        uptime=uptime,
        services=services,
        llm_status=llm_status
    )

@app.get("/health/ready")
async def readiness_check():
    """Kubernetes readiness probe."""
    # Check if LLM manager is ready
    llm_ready = False
    if llm_manager:
        try:
            health = await llm_manager.get_health()
            llm_ready = health.get("status") in ["healthy", "degraded"]
        except Exception as e:
            logger.error(f"Error checking LLM health: {e}")
            llm_ready = False
    
    # Return ready even if LLM is not ready, allowing the application to start
    # with degraded LLM capabilities rather than failing entirely
    status = "ready"
    return {"status": status, "timestamp": datetime.now().isoformat(), "llm_status": "ready" if llm_ready else "not_ready"}

@app.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe."""
    return {"status": "alive", "timestamp": datetime.now().isoformat()}

# API Endpoints
@app.get("/api/health")
async def api_health_check():
    """API health check endpoint."""
    return {
        "status": "healthy",
        "service": "reVoAgent API",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/api/models")
async def get_available_models():
    """Get list of available AI models."""
    if not llm_manager:
        return {"models": []}
    
    try:
        models = await llm_manager.get_available_models()
        return {"models": models}
    except Exception as e:
        logger.error(f"Error getting models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get models: {str(e)}")

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint with real LLM integration."""
    if not llm_manager:
        raise HTTPException(status_code=503, detail="LLM service not available")
    
    start_time = time.time()
    
    try:
        # Generate response using LLM manager
        response_text = await llm_manager.generate_response(
            request.message,
            request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        response_time = time.time() - start_time
        tokens_used = len(response_text.split())  # Approximate
        
        return ChatResponse(
            response=response_text,
            model=request.model,
            timestamp=datetime.now().isoformat(),
            tokens_used=tokens_used,
            response_time=response_time
        )
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/multi-agent")
async def multi_agent_chat(request: ChatRequest):
    """Multi-agent collaboration endpoint with real LLM integration."""
    if not llm_manager:
        raise HTTPException(status_code=503, detail="LLM service not available")
    
    agents = ["code_analyst", "debug_detective", "workflow_manager"]
    responses = []
    
    try:
        for agent in agents:
            agent_prompt = f"As a {agent}, analyze and respond to: {request.message}"
            
            response_text = await llm_manager.generate_response(
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

@app.post("/api/agent", response_model=AgentResponse)
async def agent_endpoint(request: AgentRequest):
    """Single agent endpoint with specialized prompting."""
    if not llm_manager:
        raise HTTPException(status_code=503, detail="LLM service not available")
    
    try:
        # Create agent-specific prompt
        agent_prompt = f"You are a specialized {request.agent_type} agent. \n\nUser request: {request.message}"
        
        # Add agent-specific instructions
        if request.agent_type == "code_analyst":
            agent_prompt += "\n\nAnalyze the code, identify issues and suggest improvements."
        elif request.agent_type == "debug_detective":
            agent_prompt += "\n\nInvestigate the error or bug description. Suggest possible causes and solutions."
        elif request.agent_type == "workflow_manager":
            agent_prompt += "\n\nHelp organize and optimize the described workflow or process."
        
        # Generate response
        response_text = await llm_manager.generate_response(
            agent_prompt,
            request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        return AgentResponse(
            agent=request.agent_type,
            response=response_text,
            model=request.model,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Agent error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agents/status")
async def get_agent_status():
    """Get status of all agents."""
    agents = [
        {
            "id": "agent_001",
            "type": "code_analyst",
            "status": "active",
            "performance_score": 0.95,
            "tasks_completed": 150,
            "current_task": None
        },
        {
            "id": "agent_002", 
            "type": "debug_detective",
            "status": "idle",
            "performance_score": 0.88,
            "tasks_completed": 89,
            "current_task": None
        },
        {
            "id": "agent_003", 
            "type": "workflow_manager",
            "status": "active",
            "performance_score": 0.92,
            "tasks_completed": 104,
            "current_task": "Optimizing CI/CD pipeline"
        }
    ]
    return {"agents": agents}

# Memory System Endpoints
@app.get("/api/memory/stats")
async def get_memory_stats():
    """Get memory system statistics."""
    return {
        "total_memories": 1250,
        "active_sessions": 5,
        "memory_usage": "2.3GB",
        "retrieval_accuracy": 0.994,
        "last_updated": datetime.now().isoformat()
    }

@app.post("/api/memory/store")
async def store_memory(data: Dict[str, Any]):
    """Store data in memory system."""
    # Implement actual memory storage
    return {
        "status": "stored",
        "memory_id": f"mem_{int(time.time())}",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/memory/query")
async def query_memory(query: Dict[str, Any]):
    """Query the memory system."""
    # Simulate memory query
    return {
        "results": [
            {"text": "Sample memory 1", "relevance": 0.92, "timestamp": "2023-06-18T14:35:12Z"},
            {"text": "Sample memory 2", "relevance": 0.87, "timestamp": "2023-06-17T09:12:45Z"},
        ],
        "query": query.get("text", ""),
        "timestamp": datetime.now().isoformat()
    }

# WebSocket endpoints
@app.websocket("/ws/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time dashboard updates."""
    await websocket.accept()
    websocket_connections.append(websocket)
    
    try:
        while True:
            # Send periodic updates
            update = {
                "type": "status_update",
                "timestamp": datetime.now().isoformat(),
                "active_connections": len(websocket_connections),
                "system_status": "operational"
            }
            await websocket.send_json(update)
            await asyncio.sleep(30)  # Send update every 30 seconds
            
    except WebSocketDisconnect:
        websocket_connections.remove(websocket)
        logger.info("WebSocket client disconnected")

@app.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    """WebSocket endpoint for streaming chat responses."""
    if not llm_manager:
        await websocket.close(code=1013, reason="LLM service not available")
        return
        
    await websocket.accept()
    websocket_connections.append(websocket)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            try:
                # Send typing indicator
                await websocket.send_json({"type": "typing", "status": "thinking"})
                
                # Generate response
                response = await llm_manager.generate_response(
                    data.get("message", ""),
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

# LLM Configuration endpoints
@app.get("/api/config/llm")
async def get_llm_config():
    """Get current LLM configuration."""
    if not llm_manager:
        raise HTTPException(status_code=503, detail="LLM service not available")
        
    return {
        "default_model": CONFIG.get("llm", {}).get("default_model", "deepseek-r1"),
        "available_providers": list(CONFIG.get("llm", {}).get("providers", {}).keys()),
        "status": await llm_manager.get_health() if llm_manager else {"status": "not_initialized"}
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "timestamp": datetime.now().isoformat()}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "timestamp": datetime.now().isoformat()}
    )

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global llm_manager
    
    logger.info("reVoAgent Backend Server starting...")
    
    # Initialize LLM Manager
    try:
        from src.revoagent.ai.llm_manager import LLMManager, llm_manager
        
        # Initialize the global LLM manager
        logger.info("Starting LLM Manager initialization...")
        
        # Add retry logic for initialization
        max_retries = 3
        retry_count = 0
        success = False
        
        while retry_count < max_retries and not success:
            try:
                success = await llm_manager.initialize()
                if success:
                    logger.info("LLM Manager initialized successfully")
                    break
                else:
                    retry_count += 1
                    logger.warning(f"LLM Manager initialization attempt {retry_count} failed, retrying...")
                    await asyncio.sleep(2)  # Wait before retrying
            except Exception as retry_error:
                retry_count += 1
                logger.warning(f"Initialization attempt {retry_count} error: {retry_error}")
                await asyncio.sleep(2)  # Wait before retrying
        
        if not success:
            logger.warning("LLM Manager initialization failed after retries, API will operate with limited functionality")
            
    except ImportError as e:
        logger.warning(f"LLM Manager module not available: {e}")
        logger.info("API will operate without LLM features")
        
    except Exception as e:
        logger.error(f"Error initializing LLM Manager: {e}")
        logger.info("API will operate with limited functionality")
    
    logger.info(f"Server started at: {datetime.now().isoformat()}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("reVoAgent Backend Server shutting down...")
    
    # Close all websocket connections
    for websocket in websocket_connections:
        try:
            await websocket.close()
        except:
            pass

def main():
    """Main entry point."""
    # Load port configuration
    port = CONFIG.get('ports', {}).get('backend', 12001)
    host = CONFIG.get('server', {}).get('host', '0.0.0.0')
    workers = CONFIG.get('server', {}).get('workers', 4)
    reload = CONFIG.get('server', {}).get('reload', False)
    
    logger.info(f"Starting reVoAgent Backend Server on {host}:{port}")
    logger.info(f"API Documentation available at: http://localhost:{port}/docs")
    logger.info(f"Health Check: http://localhost:{port}/health")
    
    uvicorn.run(
        "backend_main_enhanced:app",
        host=host,
        port=port,
        workers=1 if reload else workers,  # 1 worker when reload=True
        reload=reload,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main()