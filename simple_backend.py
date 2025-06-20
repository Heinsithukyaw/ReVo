#!/usr/bin/env python3
"""
Simple Backend Server for reVoAgent

A simplified version of the backend server for testing connectivity.
"""

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime
import logging
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("simple_backend")

# Create FastAPI app
app = FastAPI(title="reVoAgent Simple Backend")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Websocket connections
active_connections = []

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "uptime": 0,
        "services": {
            "api": "healthy",
            "llm": "template_mode"
        }
    }

@app.get("/api/models")
async def get_models():
    """Get available models."""
    return {
        "models": [
            {
                "id": "template-model",
                "name": "Template Model",
                "provider": "template",
                "source": "template",
                "status": "available"
            }
        ]
    }

@app.post("/api/chat")
async def chat(message: dict):
    """Basic chat endpoint."""
    user_message = message.get("message", "")
    return {
        "response": f"Template response to: {user_message}",
        "model": "template-model",
        "timestamp": datetime.now().isoformat(),
        "tokens_used": len(user_message.split())
    }

@app.get("/api/llm/status")
async def llm_status():
    """LLM status endpoint."""
    return {
        "status": "template_mode",
        "models_count": 1,
        "models": [
            {
                "id": "template-model",
                "name": "Template Model",
                "provider": "template",
                "source": "template",
                "status": "available"
            }
        ],
        "fallback_system": False,
        "timestamp": datetime.now().isoformat()
    }

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for chat."""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "system_status": "ready",
            "timestamp": datetime.now().isoformat()
        })
        
        while True:
            data = await websocket.receive_json()
            user_message = data.get("message", "")
            
            # Send typing indicator
            await websocket.send_json({
                "type": "typing",
                "status": "thinking"
            })
            
            # Simulate processing time
            await asyncio.sleep(1)
            
            # Send response
            await websocket.send_json({
                "type": "response",
                "response": f"Template response to: {user_message}",
                "model": "template-model",
                "timestamp": datetime.now().isoformat()
            })
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)

if __name__ == "__main__":
    logger.info("Starting reVoAgent Simple Backend on port 12001")
    uvicorn.run(app, host="0.0.0.0", port=12001)