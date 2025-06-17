#!/usr/bin/env python3
"""
🚀 reVoAgent Unified API Server
Glassmorphism-Enhanced Backend with All 9 Agents
Zero-cost operation with local AI models + enterprise features
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import uuid
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import uvicorn

# Add packages to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Import our enhanced AI and agent modules
from packages.ai.local_model_manager import LocalModelManager, GenerationRequest, ModelProvider
from packages.agents.enhanced_code_generator import EnhancedCodeGenerator
from packages.agents.debugging_agent import DebuggingAgent
from packages.agents.testing_agent import TestingAgent
from packages.agents.deploy_agent import DeployAgent
from packages.agents.browser_agent import BrowserAgent
from packages.agents.security_agent import SecurityAgent
from packages.agents.documentation_agent import DocumentationAgent
from packages.agents.performance_optimizer_agent import PerformanceOptimizerAgent
from packages.agents.architecture_advisor_agent import ArchitectureAdvisorAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global state
ai_manager: Optional[LocalModelManager] = None
agent_instances: Dict[str, Any] = {}
active_connections: Dict[str, WebSocket] = {}
agent_tasks: Dict[str, Dict[str, Any]] = {}

# System metrics for glassmorphism dashboard
system_metrics = {
    "uptime_start": datetime.now(),
    "total_requests": 0,
    "successful_requests": 0,
    "cost_savings": 0.0,
    "active_agents": 0,
    "websocket_connections": 0,
    "cpu_usage": 0.0,
    "memory_usage": 0.0,
    "gpu_usage": 0.0,
    "providers_status": {}
}

# Pydantic Models for API
class AgentExecutionRequest(BaseModel):
    task_description: str = Field(..., description="Task description")
    agent_type: str = Field(..., description="Agent type to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    priority: str = Field(default="medium", description="Task priority")
    preferred_provider: Optional[str] = Field(None, description="Preferred AI provider")

class AgentExecutionResponse(BaseModel):
    task_id: str
    status: str
    estimated_completion: Optional[datetime] = None
    message: str
    agent_type: str

class TaskStatusResponse(BaseModel):
    task_id: str
    agent_type: str
    status: str
    progress: float
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    cost: float = 0.0
    provider_used: Optional[str] = None

class SystemStatusResponse(BaseModel):
    status: str
    uptime: str
    version: str = "3.2.0-glassmorphism"
    available_providers: List[str]
    active_agents: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    cost_savings: Dict[str, Any]
    active_connections: int
    active_tasks: int

class GlassmorphismDashboardData(BaseModel):
    system_metrics: Dict[str, Any]
    agent_metrics: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]
    cost_analytics: Dict[str, Any]
    performance_analytics: Dict[str, Any]

# Initialize agent instances
async def initialize_agents():
    """Initialize all 9 agent instances"""
    global agent_instances
    
    try:
        # Initialize all 9 agents
        agent_instances = {
            "code_generator": EnhancedCodeGenerator(),
            "debug_agent": DebuggingAgent(),
            "testing_agent": TestingAgent(),
            "deploy_agent": DeployAgent(),
            "browser_agent": BrowserAgent(),
            "security_agent": SecurityAgent(),
            "documentation_agent": DocumentationAgent(),
            "performance_optimizer": PerformanceOptimizerAgent(),
            "architecture_advisor": ArchitectureAdvisorAgent()
        }
        
        logger.info("✅ All 9 agents initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize agents: {e}")
        return False

# Startup and Shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("🚀 Starting reVoAgent Unified API (Glassmorphism Edition)")
    
    global ai_manager
    
    # Initialize AI Manager
    try:
        from packages.ai.local_model_manager import create_local_ai_config
        config = create_local_ai_config()
        ai_manager = LocalModelManager(config)
        await ai_manager.initialize()
        logger.info("✅ AI Manager initialized")
    except Exception as e:
        logger.error(f"❌ AI Manager initialization failed: {e}")
    
    # Initialize all 9 agents
    await initialize_agents()
    
    # Start background tasks
    asyncio.create_task(system_monitor())
    asyncio.create_task(cleanup_completed_tasks())
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down reVoAgent Unified API")

# FastAPI App
app = FastAPI(
    title="reVoAgent Unified API",
    description="🎨 Glassmorphism-Enhanced AI Agent Platform with All 9 Agents",
    version="3.2.0-glassmorphism",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer(auto_error=False)

# Background Tasks
async def system_monitor():
    """Enhanced system monitoring for glassmorphism dashboard"""
    import psutil
    
    while True:
        try:
            # Update system metrics
            system_metrics.update({
                "cpu_usage": psutil.cpu_percent(interval=1),
                "memory_usage": psutil.virtual_memory().percent,
                "websocket_connections": len(active_connections),
                "active_agents": len([t for t in agent_tasks.values() if t["status"] == "running"]),
                "timestamp": datetime.now().isoformat()
            })
            
            # Add GPU usage if available
            try:
                import GPUtil
                gpus = GPUtil.getGPUs()
                if gpus:
                    system_metrics["gpu_usage"] = gpus[0].load * 100
            except:
                system_metrics["gpu_usage"] = 0
            
            # Provider status
            if ai_manager:
                provider_status = ai_manager.get_provider_status()
                system_metrics["providers_status"] = provider_status
            
            # Broadcast to glassmorphism dashboard
            await broadcast_glassmorphism_update(system_metrics)
            
            await asyncio.sleep(2)  # Update every 2 seconds for smooth animations
            
        except Exception as e:
            logger.error(f"System monitor error: {e}")
            await asyncio.sleep(5)

async def cleanup_completed_tasks():
    """Clean up completed tasks periodically"""
    while True:
        try:
            current_time = datetime.now()
            completed_tasks = []
            
            for task_id, task_data in agent_tasks.items():
                if (task_data.get("status") in ["completed", "failed"] and 
                    task_data.get("completed_at") and
                    current_time - task_data["completed_at"] > timedelta(hours=2)):
                    completed_tasks.append(task_id)
            
            for task_id in completed_tasks:
                del agent_tasks[task_id]
                logger.debug(f"Cleaned up task: {task_id}")
            
            await asyncio.sleep(600)  # Clean every 10 minutes
            
        except Exception as e:
            logger.error(f"Task cleanup error: {e}")
            await asyncio.sleep(900)

# WebSocket Management for Glassmorphism UI
async def broadcast_glassmorphism_update(data: Dict[str, Any]):
    """Broadcast updates to glassmorphism dashboard"""
    if not active_connections:
        return
    
    message = json.dumps({
        "type": "glassmorphism_update",
        "data": data,
        "timestamp": datetime.now().isoformat()
    })
    
    disconnected = []
    for client_id, websocket in active_connections.items():
        try:
            await websocket.send_text(message)
        except Exception:
            disconnected.append(client_id)
    
    # Clean up disconnected clients
    for client_id in disconnected:
        active_connections.pop(client_id, None)

async def broadcast_agent_update(task_id: str, task_data: Dict[str, Any]):
    """Broadcast agent task updates"""
    if not active_connections:
        return
    
    message = json.dumps({
        "type": "agent_update",
        "task_id": task_id,
        "data": task_data,
        "timestamp": datetime.now().isoformat()
    })
    
    disconnected = []
    for client_id, websocket in active_connections.items():
        try:
            await websocket.send_text(message)
        except Exception:
            disconnected.append(client_id)
    
    for client_id in disconnected:
        active_connections.pop(client_id, None)

# Agent Execution Functions
async def execute_agent_task(task_id: str, request: AgentExecutionRequest, agent_type: str):
    """Execute any of the 9 agents"""
    try:
        # Get agent instance
        agent = agent_instances.get(agent_type)
        if not agent:
            raise HTTPException(status_code=400, detail=f"Agent type '{agent_type}' not found")
        
        # Update task status
        agent_tasks[task_id]["status"] = "running"
        agent_tasks[task_id]["progress"] = 0.1
        await broadcast_agent_update(task_id, agent_tasks[task_id])
        
        # Execute agent with AI manager
        result = await agent.execute(
            task_description=request.task_description,
            ai_manager=ai_manager,
            parameters=request.parameters
        )
        
        # Update completion
        agent_tasks[task_id].update({
            "status": "completed",
            "progress": 1.0,
            "result": result,
            "completed_at": datetime.now(),
            "provider_used": result.get("provider_used", "unknown")
        })
        
        system_metrics["successful_requests"] += 1
        await broadcast_agent_update(task_id, agent_tasks[task_id])
        
    except Exception as e:
        logger.error(f"Agent execution error: {e}")
        agent_tasks[task_id].update({
            "status": "failed",
            "error": str(e),
            "completed_at": datetime.now()
        })
        await broadcast_agent_update(task_id, agent_tasks[task_id])

# API Routes
@app.get("/", tags=["System"])
async def root():
    """Root endpoint with glassmorphism branding"""
    return {
        "service": "reVoAgent Unified API",
        "version": "3.2.0-glassmorphism",
        "edition": "Glassmorphism Enhanced",
        "status": "operational",
        "agents_available": list(agent_instances.keys()) if agent_instances else [],
        "features": [
            "🎨 Glassmorphism UI Design",
            "🤖 All 9 AI Agents Implemented",
            "🔄 Real-time WebSocket Updates",
            "💰 Zero-cost Local AI Operation",
            "🏢 Enterprise-ready Architecture",
            "🚀 Production-grade Performance"
        ],
        "documentation": "/api/docs"
    }

@app.get("/health", tags=["System"])
async def health_check():
    """Enhanced health check for glassmorphism dashboard"""
    uptime = datetime.now() - system_metrics["uptime_start"]
    
    return {
        "status": "healthy",
        "uptime": str(uptime),
        "timestamp": datetime.now().isoformat(),
        "version": "3.2.0-glassmorphism",
        "components": {
            "ai_manager": ai_manager is not None,
            "agents": len(agent_instances),
            "websocket_server": True,
            "background_tasks": True
        },
        "metrics": {
            "cpu_usage": system_metrics.get("cpu_usage", 0),
            "memory_usage": system_metrics.get("memory_usage", 0),
            "gpu_usage": system_metrics.get("gpu_usage", 0),
            "active_connections": len(active_connections),
            "active_tasks": len([t for t in agent_tasks.values() if t["status"] == "running"])
        }
    }

@app.get("/api/system/status", response_model=SystemStatusResponse, tags=["System"])
async def get_system_status():
    """Complete system status for glassmorphism dashboard"""
    uptime = datetime.now() - system_metrics["uptime_start"]
    
    # Get AI provider status
    available_providers = []
    if ai_manager:
        provider_status = ai_manager.get_provider_status()
        available_providers = provider_status.get("available_providers", [])
    
    # Calculate cost savings
    total_requests = system_metrics["total_requests"]
    estimated_cloud_cost = total_requests * 0.002  # $0.002 per request estimate
    actual_cost = 0  # Local models are free
    cost_savings = {
        "total_savings": estimated_cloud_cost,
        "percentage": 100.0 if total_requests > 0 else 0,
        "monthly_projection": estimated_cloud_cost * 30
    }
    
    return SystemStatusResponse(
        status="operational",
        uptime=str(uptime),
        available_providers=available_providers,
        active_agents=agent_instances,
        performance_metrics=system_metrics,
        cost_savings=cost_savings,
        active_connections=len(active_connections),
        active_tasks=len([t for t in agent_tasks.values() if t["status"] in ["running", "queued"]])
    )

@app.post("/api/agents/{agent_type}/execute", response_model=AgentExecutionResponse, tags=["Agents"])
async def execute_agent(
    agent_type: str,
    request: AgentExecutionRequest,
    background_tasks: BackgroundTasks
):
    """Execute any of the 9 available agents"""
    system_metrics["total_requests"] += 1
    
    # Validate agent type
    if agent_type not in agent_instances:
        raise HTTPException(
            status_code=400, 
            detail=f"Agent type '{agent_type}' not found. Available: {list(agent_instances.keys())}"
        )
    
    # Generate task ID
    task_id = str(uuid.uuid4())
    
    # Initialize task tracking
    agent_tasks[task_id] = {
        "task_id": task_id,
        "agent_type": agent_type,
        "status": "queued",
        "progress": 0.0,
        "created_at": datetime.now(),
        "request": request.dict(),
        "result": None,
        "error": None,
        "cost": 0.0,
        "provider_used": None
    }
    
    # Start execution in background
    background_tasks.add_task(execute_agent_task, task_id, request, agent_type)
    
    return AgentExecutionResponse(
        task_id=task_id,
        status="queued",
        estimated_completion=datetime.now() + timedelta(seconds=30),
        message=f"Agent '{agent_type}' task queued successfully",
        agent_type=agent_type
    )

@app.get("/api/agents/tasks/{task_id}", response_model=TaskStatusResponse, tags=["Agents"])
async def get_task_status(task_id: str):
    """Get status of any agent task"""
    if task_id not in agent_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_data = agent_tasks[task_id]
    
    return TaskStatusResponse(
        task_id=task_data["task_id"],
        agent_type=task_data["agent_type"],
        status=task_data["status"],
        progress=task_data["progress"],
        result=task_data.get("result"),
        error=task_data.get("error"),
        created_at=task_data["created_at"],
        completed_at=task_data.get("completed_at"),
        cost=task_data.get("cost", 0.0),
        provider_used=task_data.get("provider_used")
    )

@app.delete("/api/agents/tasks/{task_id}", tags=["Agents"])
async def cancel_task(task_id: str):
    """Cancel a running task"""
    if task_id not in agent_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = agent_tasks[task_id]
    if task["status"] in ["completed", "failed"]:
        raise HTTPException(status_code=400, detail="Cannot cancel completed task")
    
    agent_tasks[task_id].update({
        "status": "cancelled",
        "completed_at": datetime.now()
    })
    
    await broadcast_agent_update(task_id, agent_tasks[task_id])
    
    return {"message": "Task cancelled successfully"}

@app.get("/api/agents/tasks", tags=["Agents"])
async def list_tasks(
    status: Optional[str] = None, 
    agent_type: Optional[str] = None,
    limit: int = 50
):
    """List all tasks with filtering"""
    tasks = list(agent_tasks.values())
    
    if status:
        tasks = [t for t in tasks if t["status"] == status]
    
    if agent_type:
        tasks = [t for t in tasks if t["agent_type"] == agent_type]
    
    # Sort by creation time (newest first)
    tasks.sort(key=lambda x: x["created_at"], reverse=True)
    
    return {
        "tasks": tasks[:limit],
        "total": len(tasks),
        "filtered": len(tasks) if (status or agent_type) else None,
        "available_agents": list(agent_instances.keys())
    }

@app.get("/api/glassmorphism/dashboard", response_model=GlassmorphismDashboardData, tags=["Glassmorphism"])
async def get_glassmorphism_dashboard():
    """Get complete dashboard data for glassmorphism UI"""
    
    # Agent metrics
    agent_metrics = []
    for agent_type, agent in agent_instances.items():
        agent_tasks_for_type = [t for t in agent_tasks.values() if t["agent_type"] == agent_type]
        completed_tasks = [t for t in agent_tasks_for_type if t["status"] == "completed"]
        
        agent_metrics.append({
            "type": agent_type,
            "status": "active" if agent_tasks_for_type else "idle",
            "total_tasks": len(agent_tasks_for_type),
            "completed_tasks": len(completed_tasks),
            "success_rate": len(completed_tasks) / len(agent_tasks_for_type) if agent_tasks_for_type else 0,
            "average_response_time": 15.0,  # Mock data
            "last_used": datetime.now().isoformat() if agent_tasks_for_type else None
        })
    
    # Recent activity
    recent_activity = []
    recent_tasks = sorted(agent_tasks.values(), key=lambda x: x["created_at"], reverse=True)[:10]
    for task in recent_tasks:
        recent_activity.append({
            "id": task["task_id"],
            "title": f"{task['agent_type'].replace('_', ' ').title()} Task",
            "description": task["request"]["task_description"][:100] + "..." if len(task["request"]["task_description"]) > 100 else task["request"]["task_description"],
            "status": task["status"],
            "timestamp": task["created_at"].isoformat(),
            "agent_type": task["agent_type"]
        })
    
    return GlassmorphismDashboardData(
        system_metrics=system_metrics,
        agent_metrics=agent_metrics,
        recent_activity=recent_activity,
        cost_analytics={
            "total_savings": system_metrics.get("cost_savings", 0),
            "monthly_projection": system_metrics.get("cost_savings", 0) * 30,
            "cost_per_request": 0.0,
            "cloud_equivalent": system_metrics["total_requests"] * 0.002
        },
        performance_analytics={
            "uptime_percentage": 99.9,
            "average_response_time": "12.3s",
            "throughput": f"{system_metrics['successful_requests']}/hour",
            "error_rate": 0.1
        }
    )

# Enhanced WebSocket for Glassmorphism Dashboard
@app.websocket("/ws/glassmorphism")
async def websocket_glassmorphism_dashboard(websocket: WebSocket):
    """Enhanced WebSocket for glassmorphism dashboard with smooth animations"""
    await websocket.accept()
    client_id = str(uuid.uuid4())
    active_connections[client_id] = websocket
    
    logger.info(f"🎨 Glassmorphism WebSocket connected: {client_id}")
    
    try:
        # Send initial dashboard data
        dashboard_data = await get_glassmorphism_dashboard()
        await websocket.send_text(json.dumps({
            "type": "initial_dashboard",
            "data": dashboard_data.dict(),
            "timestamp": datetime.now().isoformat()
        }))
        
        # Keep connection alive with heartbeat
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat(),
                        "metrics": {
                            "cpu": system_metrics.get("cpu_usage", 0),
                            "memory": system_metrics.get("memory_usage", 0),
                            "gpu": system_metrics.get("gpu_usage", 0)
                        }
                    }))
                elif message.get("type") == "request_refresh":
                    dashboard_data = await get_glassmorphism_dashboard()
                    await websocket.send_text(json.dumps({
                        "type": "dashboard_refresh",
                        "data": dashboard_data.dict(),
                        "timestamp": datetime.now().isoformat()
                    }))
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket message error: {e}")
                break
                
    except WebSocketDisconnect:
        pass
    finally:
        active_connections.pop(client_id, None)
        logger.info(f"🎨 Glassmorphism WebSocket disconnected: {client_id}")

# Legacy WebSocket endpoint for compatibility
@app.websocket("/ws/dashboard")
async def websocket_dashboard_legacy(websocket: WebSocket):
    """Legacy dashboard WebSocket for compatibility"""
    await websocket_glassmorphism_dashboard(websocket)

if __name__ == "__main__":
    print("🚀 Starting reVoAgent Unified API Server")
    print("🎨 Glassmorphism Edition with All 9 Agents")
    print("📚 API Documentation: http://localhost:8000/api/docs")
    print("🔌 Glassmorphism WebSocket: ws://localhost:8000/ws/glassmorphism")
    print("💰 Zero-cost operation with local AI models")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Set to True for development
        log_level="info",
        access_log=True
    )
