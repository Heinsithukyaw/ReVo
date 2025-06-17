#!/usr/bin/env python3
"""
Simple test script to start the dashboard server for testing frontend UI
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="reVoAgent Dashboard Test",
    description="Test server for reVoAgent Dashboard",
    version="1.0.0"
)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files directory
static_dir = Path(__file__).parent / "src" / "revoagent" / "ui" / "web_dashboard" / "static"

# Mount built React assets
dist_dir = static_dir / "dist"
if dist_dir.exists():
    # Mount the assets directory
    assets_dir = dist_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
    
    # Mount the entire dist directory for other static files
    app.mount("/dist", StaticFiles(directory=str(dist_dir)), name="dist")

# Mount static files (fallback)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/")
async def dashboard():
    """Serve the main dashboard."""
    # Force serve React build
    react_build_file = static_dir / "dist" / "index.html"
    if react_build_file.exists():
        logger.info(f"Serving React build from: {react_build_file}")
        return FileResponse(str(react_build_file), media_type="text/html")
    else:
        logger.error(f"React build not found at: {react_build_file}")
        return {"error": "React build not found", "path": str(react_build_file)}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "reVoAgent Dashboard Test",
        "version": "1.0.0"
    }

# Mock API endpoints for testing
@app.get("/api/v1/dashboard/stats")
async def get_dashboard_stats():
    return {
        "active_agents": 3,
        "running_workflows": 2,
        "tasks_completed": 591,
        "models_loaded": 3,
        "success_rate": 98.5,
        "api_cost": 0,
        "uptime": "99.9%",
        "response_time": 847
    }

@app.get("/api/v1/agents")
async def get_agents():
    return {
        "agents": [
            {
                "id": "code-generator",
                "name": "Enhanced Code Generator",
                "status": "active",
                "type": "code_generation",
                "performance": 95.2
            },
            {
                "id": "debug-agent",
                "name": "Debug Agent",
                "status": "active",
                "type": "debugging",
                "performance": 92.8
            },
            {
                "id": "testing-agent",
                "name": "Testing Agent",
                "status": "idle",
                "type": "testing",
                "performance": 89.5
            }
        ]
    }

@app.get("/api/v1/workflows")
async def get_workflows():
    return {
        "workflows": [
            {
                "id": "workflow-1",
                "name": "Full Stack Development",
                "status": "running",
                "progress": 75,
                "agents": ["code-generator", "testing-agent"]
            },
            {
                "id": "workflow-2",
                "name": "Bug Fix Pipeline",
                "status": "running",
                "progress": 45,
                "agents": ["debug-agent", "testing-agent"]
            }
        ]
    }

@app.get("/api/v1/models")
async def get_models():
    return {
        "models": [
            {
                "id": "deepseek-r1",
                "name": "DeepSeek R1",
                "status": "loaded",
                "type": "reasoning",
                "performance": 98.5
            },
            {
                "id": "codellama-70b",
                "name": "CodeLlama 70B",
                "status": "available",
                "type": "code_generation",
                "performance": 94.2
            },
            {
                "id": "mistral-7b",
                "name": "Mistral 7B",
                "status": "available",
                "type": "general",
                "performance": 87.3
            }
        ]
    }

@app.get("/api/v1/system/metrics")
async def get_system_metrics():
    return {
        "cpu_usage": {"value": 45.2, "unit": "%", "status": "normal"},
        "memory_usage": {"value": 68.7, "unit": "%", "status": "normal"},
        "gpu_usage": {"value": 23.1, "unit": "%", "status": "normal"},
        "disk_usage": {"value": 34.5, "unit": "%", "status": "normal"}
    }

@app.get("/api/v1/integrations/status")
async def get_integration_status():
    return {
        "integrations": [
            {"name": "OpenHands", "status": "connected", "health": "healthy"},
            {"name": "vLLM Server", "status": "connected", "health": "healthy"},
            {"name": "Docker", "status": "connected", "health": "healthy"},
            {"name": "All-Hands", "status": "connected", "health": "healthy"},
            {"name": "Monitoring", "status": "connected", "health": "healthy"}
        ]
    }

@app.get("/api/v1/activity/recent")
async def get_recent_activity():
    return {
        "activities": [
            {
                "id": "1",
                "type": "code_generation",
                "description": "Generated React component for dashboard",
                "timestamp": "2025-06-07T19:30:00Z",
                "agent": "code-generator",
                "status": "completed"
            },
            {
                "id": "2",
                "type": "debugging",
                "description": "Fixed API endpoint routing issue",
                "timestamp": "2025-06-07T19:25:00Z",
                "agent": "debug-agent",
                "status": "completed"
            },
            {
                "id": "3",
                "type": "testing",
                "description": "Running integration tests",
                "timestamp": "2025-06-07T19:20:00Z",
                "agent": "testing-agent",
                "status": "running"
            }
        ]
    }

if __name__ == "__main__":
    logger.info("Starting reVoAgent Dashboard Test Server...")
    logger.info(f"Static directory: {static_dir}")
    logger.info(f"React build exists: {(static_dir / 'dist' / 'index.html').exists()}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=12000,
        log_level="info"
    )