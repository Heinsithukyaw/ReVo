#!/usr/bin/env python3
"""
Simplified FastAPI Backend for Testing Critical Fixes
Demonstrates that the port configuration and basic functionality work
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic Models
class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    port: int

class DashboardData(BaseModel):
    message: str
    timestamp: str
    active_connections: int

# Global state
class AppState:
    def __init__(self):
        self.websocket_connections: List[WebSocket] = []
        self.start_time = time.time()

app_state = AppState()

# Create FastAPI app
app = FastAPI(
    title="reVoAgent Simplified Backend",
    description="Testing Critical Fixes - Port Configuration and Basic Functionality",
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

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with basic info"""
    return HTMLResponse("""
    <html>
        <head>
            <title>reVoAgent Backend</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .status { color: #28a745; font-weight: bold; }
                .info { background: #e9ecef; padding: 15px; border-radius: 5px; margin: 15px 0; }
                .success { color: #28a745; }
                .port { color: #007bff; font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🤖 reVoAgent Backend</h1>
                <p class="status">✅ Backend is running successfully!</p>
                
                <div class="info">
                    <h3>Critical Fixes Implemented:</h3>
                    <ul>
                        <li class="success">✅ Port Configuration: Running on port <span class="port">12001</span></li>
                        <li class="success">✅ CORS Configuration: Allows frontend connections</li>
                        <li class="success">✅ WebSocket Support: Real-time communication enabled</li>
                        <li class="success">✅ Health Check: Monitoring endpoint available</li>
                    </ul>
                </div>
                
                <div class="info">
                    <h3>Available Endpoints:</h3>
                    <ul>
                        <li><a href="/health">/health</a> - Health check</li>
                        <li><a href="/docs">/docs</a> - API Documentation</li>
                        <li><a href="/api/dashboard">/api/dashboard</a> - Dashboard data</li>
                        <li><strong>/ws/dashboard</strong> - WebSocket endpoint</li>
                    </ul>
                </div>
                
                <p><strong>Frontend URL:</strong> <a href="http://localhost:12000">http://localhost:12000</a></p>
                <p><strong>Backend URL:</strong> <a href="http://localhost:12001">http://localhost:12001</a></p>
            </div>
        </body>
    </html>
    """)

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0",
        port=12001
    )

@app.get("/api/dashboard", response_model=DashboardData)
async def get_dashboard():
    """Get dashboard data"""
    return DashboardData(
        message="Dashboard data from simplified backend",
        timestamp=datetime.now().isoformat(),
        active_connections=len(app_state.websocket_connections)
    )

@app.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """WebSocket endpoint for real-time dashboard updates"""
    await websocket.accept()
    app_state.websocket_connections.append(websocket)
    logger.info(f"WebSocket connected. Total connections: {len(app_state.websocket_connections)}")
    
    try:
        # Send initial data
        initial_data = {
            "type": "connection",
            "message": "Connected to reVoAgent backend",
            "timestamp": datetime.now().isoformat(),
            "port": 12001
        }
        await websocket.send_text(json.dumps(initial_data))
        
        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for client messages
                data = await websocket.receive_text()
                logger.info(f"Received WebSocket message: {data}")
                
                # Echo back with timestamp
                response = {
                    "type": "echo",
                    "original_message": data,
                    "timestamp": datetime.now().isoformat(),
                    "active_connections": len(app_state.websocket_connections)
                }
                await websocket.send_text(json.dumps(response))
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
                
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in app_state.websocket_connections:
            app_state.websocket_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(app_state.websocket_connections)}")

# Background task to broadcast periodic updates
async def broadcast_updates():
    """Send periodic updates to all connected WebSocket clients"""
    while True:
        if app_state.websocket_connections:
            update_data = {
                "type": "update",
                "message": "Periodic update from backend",
                "timestamp": datetime.now().isoformat(),
                "uptime": int(time.time() - app_state.start_time),
                "active_connections": len(app_state.websocket_connections)
            }
            
            # Send to all connected clients
            disconnected = []
            for websocket in app_state.websocket_connections:
                try:
                    await websocket.send_text(json.dumps(update_data))
                except:
                    disconnected.append(websocket)
            
            # Remove disconnected clients
            for websocket in disconnected:
                app_state.websocket_connections.remove(websocket)
        
        await asyncio.sleep(10)  # Send update every 10 seconds

@app.on_event("startup")
async def startup_event():
    """Application startup"""
    logger.info("🚀 reVoAgent Simplified Backend starting...")
    logger.info("✅ Critical fixes implemented:")
    logger.info("   - Port configuration: 12001")
    logger.info("   - CORS enabled for frontend")
    logger.info("   - WebSocket support enabled")
    logger.info("   - Health check endpoint available")
    
    # Start background task
    asyncio.create_task(broadcast_updates())

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown"""
    logger.info("🛑 reVoAgent Backend shutting down...")
    
    # Close all WebSocket connections
    for websocket in app_state.websocket_connections:
        try:
            await websocket.close()
        except:
            pass

if __name__ == "__main__":
    logger.info("Starting reVoAgent Backend on port 12001...")
    uvicorn.run(
        "simple_main:app",
        host="0.0.0.0",
        port=12001,
        reload=True,
        ws_ping_interval=20,
        ws_ping_timeout=10
    )