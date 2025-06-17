#!/usr/bin/env python3
"""
Modern FastAPI Backend with Async Patterns and WebSocket Support
Integrates with Three-Engine Architecture and Phase 4 Specialized Agents
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
import uvicorn

# Phase 4 Imports
from revoagent.core.framework import ThreeEngineArchitecture
from src.revoagent.specialized_agents import (
    WorkflowIntelligence, AgentDashboard, CodeAnalysisAgent, 
    DebugDetectiveAgent, ArchitectureAdvisorAgent, PerformanceOptimizerAgent,
    SecurityAuditorAgent, AgentCapability
)
from src.revoagent.specialized_agents.integration_framework import IntegrationFramework


# Pydantic Models
class EngineStatus(BaseModel):
    type: str
    status: str = Field(..., pattern="^(healthy|warning|error)$")
    is_active: bool
    performance: float = Field(..., ge=0, le=1)
    last_activity: datetime
    metrics: Dict[str, float]
    specific_metrics: Dict[str, Any]


class SystemMetrics(BaseModel):
    total_tasks: int
    active_sessions: int
    success_rate: float = Field(..., ge=0, le=1)
    uptime: int


class Alert(BaseModel):
    id: str
    level: str = Field(..., pattern="^(info|warning|error)$")
    message: str
    timestamp: datetime


class DashboardData(BaseModel):
    engines: List[EngineStatus]
    system_metrics: SystemMetrics
    alerts: List[Alert]


class WorkflowRequest(BaseModel):
    description: str
    context: Dict[str, Any] = Field(default_factory=dict)
    preferences: Dict[str, Any] = Field(default_factory=dict)


class WorkflowResponse(BaseModel):
    workflow_id: str
    status: str
    steps: int
    estimated_duration: Optional[float] = None


class AgentRequest(BaseModel):
    agent_capability: str
    task_description: str
    context: Dict[str, Any] = Field(default_factory=dict)


class AgentResponse(BaseModel):
    agent_id: str
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None


# Global state
class AppState:
    def __init__(self):
        self.engines: Optional[ThreeEngineArchitecture] = None
        self.workflow_intelligence: Optional[WorkflowIntelligence] = None
        self.dashboard: Optional[AgentDashboard] = None
        self.integration_framework: Optional[IntegrationFramework] = None
        self.websocket_connections: List[WebSocket] = []
        self.background_tasks: List[asyncio.Task] = []
        self.is_initialized = False


app_state = AppState()


# Application lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle"""
    # Startup
    logging.info("🚀 Starting reVoAgent Modern Backend...")
    
    try:
        # Initialize Three-Engine Architecture
        app_state.engines = ThreeEngineArchitecture()
        if not await app_state.engines.initialize():
            raise Exception("Failed to initialize Three-Engine Architecture")
        
        # Initialize Workflow Intelligence
        app_state.workflow_intelligence = WorkflowIntelligence(app_state.engines)
        if not await app_state.workflow_intelligence.initialize():
            raise Exception("Failed to initialize Workflow Intelligence")
        
        # Initialize Agent Dashboard
        app_state.dashboard = AgentDashboard(app_state.engines, app_state.workflow_intelligence)
        if not await app_state.dashboard.initialize():
            raise Exception("Failed to initialize Agent Dashboard")
        
        # Initialize Integration Framework
        app_state.integration_framework = IntegrationFramework()
        if not await app_state.integration_framework.initialize():
            raise Exception("Failed to initialize Integration Framework")
        
        # Start background tasks
        app_state.background_tasks.append(
            asyncio.create_task(dashboard_broadcast_task())
        )
        
        app_state.is_initialized = True
        logging.info("✅ reVoAgent Backend initialized successfully")
        
        yield
        
    except Exception as e:
        logging.error(f"❌ Failed to initialize backend: {e}")
        raise
    
    finally:
        # Shutdown
        logging.info("🛑 Shutting down reVoAgent Backend...")
        
        # Cancel background tasks
        for task in app_state.background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # Close WebSocket connections
        for ws in app_state.websocket_connections:
            try:
                await ws.close()
            except:
                pass
        
        # Cleanup components
        if app_state.dashboard:
            await app_state.dashboard.stop_monitoring()
        
        if app_state.integration_framework:
            await app_state.integration_framework.shutdown()
        
        logging.info("✅ Backend shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="reVoAgent Modern Backend",
    description="Advanced AI Development Platform with Three-Engine Architecture",
    version="3.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files (conditional mounting)
import os
if os.path.exists("frontend/dist"):
    app.mount("/static", StaticFiles(directory="frontend/dist"), name="static")


# Background tasks
async def dashboard_broadcast_task():
    """Background task to broadcast dashboard updates"""
    while True:
        try:
            if app_state.is_initialized and app_state.websocket_connections:
                dashboard_data = await get_dashboard_data()
                message = json.dumps(dashboard_data.dict(), default=str)
                
                # Broadcast to all connected clients
                disconnected = []
                for ws in app_state.websocket_connections:
                    try:
                        await ws.send_text(message)
                    except:
                        disconnected.append(ws)
                
                # Remove disconnected clients
                for ws in disconnected:
                    app_state.websocket_connections.remove(ws)
            
            await asyncio.sleep(2)  # Update every 2 seconds
            
        except Exception as e:
            logging.error(f"Dashboard broadcast error: {e}")
            await asyncio.sleep(5)


# Helper functions
async def get_dashboard_data() -> DashboardData:
    """Get current dashboard data"""
    if not app_state.dashboard:
        raise HTTPException(status_code=503, detail="Dashboard not initialized")
    
    state = await app_state.dashboard.get_dashboard_state()
    
    # Convert to API model
    engines = []
    for agent_id, status in state.agent_statuses.items():
        engines.append(EngineStatus(
            type=status.capability.value,
            status="healthy" if status.is_healthy else "error",
            is_active=not status.is_busy,
            performance=status.performance_score,
            last_activity=datetime.fromtimestamp(status.last_activity),
            metrics={
                "response_time": 100.0,  # Mock data
                "throughput": 85.0,
                "accuracy": 99.2,
                "utilization": 72.0
            },
            specific_metrics={
                "problems_solved": status.success_count,
                "error_count": status.error_count,
                "learning_score": status.learning_score
            }
        ))
    
    system_metrics = SystemMetrics(
        total_tasks=state.total_problems_solved,
        active_sessions=state.active_sessions,
        success_rate=state.workflow_metrics.success_rate,
        uptime=int(time.time() - 1000)  # Mock uptime
    )
    
    alerts = [
        Alert(
            id=alert.alert_id,
            level=alert.level.value,
            message=alert.message,
            timestamp=datetime.fromtimestamp(alert.timestamp)
        )
        for alert in await app_state.dashboard.get_system_alerts()
    ]
    
    return DashboardData(
        engines=engines,
        system_metrics=system_metrics,
        alerts=alerts
    )


# API Routes

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the React frontend"""
    try:
        with open("frontend/dist/index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse("""
        <html>
            <body>
                <h1>🤖 reVoAgent Backend</h1>
                <p>Frontend not built. Run: <code>cd frontend && npm run build</code></p>
                <p><a href="/docs">API Documentation</a></p>
            </body>
        </html>
        """)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy" if app_state.is_initialized else "initializing",
        "timestamp": datetime.now().isoformat(),
        "version": "3.0.0",
        "engines_initialized": app_state.engines is not None,
        "dashboard_active": app_state.dashboard is not None
    }


@app.get("/api/dashboard", response_model=DashboardData)
async def get_dashboard():
    """Get current dashboard data"""
    return await get_dashboard_data()


@app.post("/api/workflows", response_model=WorkflowResponse)
async def create_workflow(request: WorkflowRequest, background_tasks: BackgroundTasks):
    """Create and execute an intelligent workflow"""
    if not app_state.workflow_intelligence:
        raise HTTPException(status_code=503, detail="Workflow Intelligence not initialized")
    
    try:
        # Create workflow
        workflow_def = await app_state.workflow_intelligence.create_intelligent_workflow(
            problem_description=request.description,
            context=request.context,
            preferences=request.preferences
        )
        
        # Execute workflow in background
        background_tasks.add_task(
            execute_workflow_background,
            workflow_def.workflow_id,
            request.context
        )
        
        return WorkflowResponse(
            workflow_id=workflow_def.workflow_id,
            status="created",
            steps=len(workflow_def.steps),
            estimated_duration=3600.0  # Mock estimation
        )
        
    except Exception as e:
        logging.error(f"Workflow creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def execute_workflow_background(workflow_id: str, context: Dict[str, Any]):
    """Execute workflow in background"""
    try:
        execution = await app_state.workflow_intelligence.execute_workflow(
            workflow_id, context
        )
        logging.info(f"Workflow {workflow_id} completed with status: {execution.status}")
    except Exception as e:
        logging.error(f"Workflow {workflow_id} execution failed: {e}")


@app.get("/api/workflows/{workflow_id}")
async def get_workflow_status(workflow_id: str):
    """Get workflow execution status"""
    if not app_state.workflow_intelligence:
        raise HTTPException(status_code=503, detail="Workflow Intelligence not initialized")
    
    # Check active executions
    for execution in app_state.workflow_intelligence.active_executions.values():
        if execution.workflow_id == workflow_id:
            return {
                "workflow_id": workflow_id,
                "execution_id": execution.execution_id,
                "status": execution.status.value,
                "current_step": execution.current_step,
                "completed_steps": len(execution.completed_steps),
                "total_steps": len(app_state.workflow_intelligence.workflow_definitions[workflow_id].steps)
            }
    
    raise HTTPException(status_code=404, detail="Workflow not found")


@app.post("/api/agents/{capability}/execute", response_model=AgentResponse)
async def execute_agent_task(capability: str, request: AgentRequest):
    """Execute a task with a specific agent"""
    if not app_state.workflow_intelligence:
        raise HTTPException(status_code=503, detail="Workflow Intelligence not initialized")
    
    try:
        # Map capability string to enum
        agent_capability = AgentCapability(capability)
        agent = app_state.workflow_intelligence.agents.get(agent_capability)
        
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {capability} not found")
        
        # Create and execute task
        from src.revoagent.specialized_agents import Problem, ProblemComplexity
        
        problem = Problem(
            description=request.task_description,
            context=request.context,
            complexity=ProblemComplexity.MODERATE
        )
        
        # Execute task
        analysis = await agent.analyze_problem(problem)
        solutions = await agent.generate_solution(analysis)
        
        task_id = f"task_{int(time.time())}"
        
        return AgentResponse(
            agent_id=agent.agent_id,
            task_id=task_id,
            status="completed",
            result={
                "analysis": {
                    "problem_type": analysis.problem_type,
                    "complexity": analysis.complexity_assessment.value,
                    "confidence": analysis.confidence_score
                },
                "solutions": [
                    {
                        "approach": solution.approach,
                        "confidence": solution.confidence_score,
                        "effort": solution.estimated_effort
                    }
                    for solution in solutions[:3]  # Return top 3 solutions
                ]
            }
        )
        
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid agent capability: {capability}")
    except Exception as e:
        logging.error(f"Agent task execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agents")
async def list_agents():
    """List all available agents"""
    if not app_state.workflow_intelligence:
        raise HTTPException(status_code=503, detail="Workflow Intelligence not initialized")
    
    agents = []
    for capability, agent in app_state.workflow_intelligence.agents.items():
        agents.append({
            "capability": capability.value,
            "agent_id": agent.agent_id,
            "specialization": agent.specialization,
            "is_healthy": agent.is_initialized,
            "performance_metrics": agent.performance_metrics
        })
    
    return {"agents": agents}


@app.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """WebSocket endpoint for real-time dashboard updates"""
    await websocket.accept()
    app_state.websocket_connections.append(websocket)
    
    try:
        # Send initial data
        if app_state.is_initialized:
            dashboard_data = await get_dashboard_data()
            await websocket.send_text(json.dumps(dashboard_data.dict(), default=str))
        
        # Keep connection alive
        while True:
            try:
                # Wait for client messages (ping/pong)
                await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.ping()
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
    finally:
        if websocket in app_state.websocket_connections:
            app_state.websocket_connections.remove(websocket)


@app.post("/api/integrations/github")
async def create_github_integration(config: Dict[str, Any]):
    """Create GitHub integration"""
    if not app_state.integration_framework:
        raise HTTPException(status_code=503, detail="Integration Framework not initialized")
    
    try:
        integration_id = await app_state.integration_framework.create_github_integration(config)
        return {"integration_id": integration_id, "status": "created"}
    except Exception as e:
        logging.error(f"GitHub integration creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/integrations/status")
async def get_integrations_status():
    """Get status of all integrations"""
    if not app_state.integration_framework:
        raise HTTPException(status_code=503, detail="Integration Framework not initialized")
    
    status = await app_state.integration_framework.get_integration_status()
    return {"integrations": status}


async def create_app():
    """Create and return the FastAPI app instance"""
    return app


# Development server
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=12001,
        reload=True,
        ws_ping_interval=20,
        ws_ping_timeout=10
    )