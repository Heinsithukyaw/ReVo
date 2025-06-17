#!/usr/bin/env python3
"""
reVoAgent Consolidated Backend Server
Single entry point for all backend functionality
Consolidates: production_backend_server.py, simple_backend_server.py, and other variants
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

# Load port configuration
def load_port_config():
    """Load port configuration from config/ports.yaml"""
    try:
        import yaml
        with open('config/ports.yaml', 'r') as f:
            config = yaml.safe_load(f)
        return config['production']['backend']
    except Exception:
        return 12001  # Default fallback

# Initialize FastAPI app
app = FastAPI(
    title="reVoAgent Backend API",
    description="Consolidated backend server for reVoAgent platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer(auto_error=False)

# Data Models
class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    uptime: float
    services: Dict[str, str]

class ChatRequest(BaseModel):
    message: str
    model: Optional[str] = "deepseek-r1"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000

class ChatResponse(BaseModel):
    response: str
    model: str
    timestamp: str
    tokens_used: int

class AgentStatus(BaseModel):
    id: str
    type: str
    status: str
    current_task: Optional[str] = None
    performance_score: float
    tasks_completed: int

# Global state
start_time = time.time()
websocket_connections: List[WebSocket] = []

# Health Check Endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Comprehensive health check endpoint"""
    uptime = time.time() - start_time
    
    # Check service status
    services = {
        "api": "healthy",
        "database": "healthy",  # Add actual DB check
        "memory": "healthy",    # Add actual memory check
        "models": "healthy"     # Add actual model check
    }
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0",
        uptime=uptime,
        services=services
    )

@app.get("/health/ready")
async def readiness_check():
    """Kubernetes readiness probe"""
    return {"status": "ready", "timestamp": datetime.now().isoformat()}

@app.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe"""
    return {"status": "alive", "timestamp": datetime.now().isoformat()}

# API Endpoints
@app.get("/api/health")
async def api_health_check():
    """API health check endpoint"""
    return {
        "status": "healthy",
        "service": "reVoAgent API",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/api/models")
async def get_available_models():
    """Get list of available AI models"""
    models = [
        {
            "id": "deepseek-r1",
            "name": "DeepSeek R1",
            "type": "local",
            "status": "available",
            "cost_per_token": 0.0
        },
        {
            "id": "llama-3.1-70b",
            "name": "Llama 3.1 70B",
            "type": "local", 
            "status": "available",
            "cost_per_token": 0.0
        }
    ]
    return {"models": models}

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint with AI integration"""
    try:
        # Simulate AI response (replace with actual AI integration)
        response_text = f"AI Response to: {request.message}"
        
        return ChatResponse(
            response=response_text,
            model=request.model,
            timestamp=datetime.now().isoformat(),
            tokens_used=len(response_text.split())
        )
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/multi-agent")
async def multi_agent_chat(request: ChatRequest):
    """Multi-agent collaboration endpoint"""
    agents = ["code_analyst", "debug_detective", "workflow_manager"]
    responses = []
    
    for agent in agents:
        response = {
            "agent": agent,
            "response": f"{agent} response to: {request.message}",
            "timestamp": datetime.now().isoformat()
        }
        responses.append(response)
    
    return {"responses": responses}

@app.get("/api/agents/status")
async def get_agent_status():
    """Get status of all agents"""
    agents = [
        AgentStatus(
            id="agent_001",
            type="code_analyst",
            status="active",
            performance_score=0.95,
            tasks_completed=150
        ),
        AgentStatus(
            id="agent_002", 
            type="debug_detective",
            status="idle",
            performance_score=0.88,
            tasks_completed=89
        )
    ]
    return {"agents": agents}

# Memory System Endpoints
@app.get("/api/memory/stats")
async def get_memory_stats():
    """Get memory system statistics"""
    return {
        "total_memories": 1250,
        "active_sessions": 5,
        "memory_usage": "2.3GB",
        "retrieval_accuracy": 0.994,
        "last_updated": datetime.now().isoformat()
    }

@app.post("/api/memory/store")
async def store_memory(data: Dict[str, Any]):
    """Store data in memory system"""
    # Implement actual memory storage
    return {
        "status": "stored",
        "memory_id": f"mem_{int(time.time())}",
        "timestamp": datetime.now().isoformat()
    }

# WebSocket for real-time communication
@app.websocket("/ws/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time dashboard updates"""
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

# Integration Endpoints
@app.post("/api/integrations/github/repos/{owner}/{repo}/pulls")
async def create_github_pr(owner: str, repo: str, data: Dict[str, Any]):
    """Create GitHub pull request"""
    # Implement GitHub integration
    return {
        "status": "created",
        "pr_number": 123,
        "url": f"https://github.com/{owner}/{repo}/pull/123"
    }

@app.post("/api/integrations/slack/notify")
async def send_slack_notification(data: Dict[str, Any]):
    """Send Slack notification"""
    # Implement Slack integration
    return {
        "status": "sent",
        "channel": data.get("channel", "#general"),
        "timestamp": datetime.now().isoformat()
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "timestamp": datetime.now().isoformat()}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "timestamp": datetime.now().isoformat()}
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("reVoAgent Backend Server starting...")
    logger.info(f"Server started at: {datetime.now().isoformat()}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("reVoAgent Backend Server shutting down...")

def main():
    """Main entry point"""
    port = load_port_config()
    
    logger.info(f"Starting reVoAgent Backend Server on port {port}")
    logger.info("API Documentation available at: http://localhost:{port}/docs")
    
    uvicorn.run(
        "backend_main:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Set to True for development
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main()