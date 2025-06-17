"""reVoAgent Backend Application - Enterprise Ready with Authentication"""
import sys
import uuid
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uvicorn
import asyncio
import json
import random
import time

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import database and auth
from packages.core.database import get_db, init_database, User, Project, Execution, ChatSession, ChatMessage
from packages.core.auth import AuthService, get_current_user, get_current_active_user, get_current_user_optional
from packages.core.schemas import (
    UserCreate, UserResponse, LoginRequest, TokenResponse, RefreshTokenRequest,
    ProjectCreate, ProjectResponse, ProjectUpdate,
    ExecutionCreate, ExecutionResponse, ExecutionUpdate,
    ChatSessionCreate, ChatSessionResponse, ChatMessageCreate, ChatMessageResponse,
    AgentExecutionRequest, AgentExecutionResponse,
    DashboardStats, SystemHealth
)

# Import real agent implementations
from packages.agents.code_generator import CodeGeneratorAgent
from packages.agents.debugging_agent import DebuggingAgent
from packages.agents.testing_agent import TestingAgent
from packages.agents.documentation_agent import DocumentationAgent
from packages.agents.deploy_agent import DeployAgent
from packages.agents.browser_agent import BrowserAgent
from packages.agents.security_agent import SecurityAgent
from packages.core.config import AgentConfig
from packages.core.memory import MemoryManager

# Import real AI integration
from packages.core.ai_integration import SmartModelManager, RealToolManager, create_model_manager, create_tool_manager

# Initialize FastAPI app
app = FastAPI(
    title="reVoAgent Enterprise API", 
    version="2.0.0",
    description="Enterprise-Ready AI Development Platform with Authentication"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database and agents on startup."""
    init_database()
    print("✅ Database initialized")
    
    # Initialize agents with real AI integration
    global agents
    
    # Create smart model manager that auto-detects available providers
    model_manager = create_model_manager("auto")
    
    # Create real tool manager (with safety restrictions)
    tool_manager = create_tool_manager(use_real_tools=True)
    
    # Memory manager
    memory_manager = MemoryManager()
    
    agents = {
        "code-generator": CodeGeneratorAgent(
            agent_id="code-generator-001",
            config=AgentConfig(model="gpt-4", tools=["terminal", "file_manager"]),
            model_manager=model_manager,
            tool_manager=tool_manager,
            memory_manager=memory_manager
        ),
        "debug-agent": DebuggingAgent(
            agent_id="debug-agent-001",
            config=AgentConfig(model="gpt-4", tools=["terminal", "profiler", "log_analyzer"]),
            model_manager=model_manager,
            tool_manager=tool_manager,
            memory_manager=memory_manager
        ),
        "testing-agent": TestingAgent(
            agent_id="testing-agent-001",
            config=AgentConfig(model="gpt-4", tools=["pytest", "coverage", "terminal"]),
            model_manager=model_manager,
            tool_manager=tool_manager,
            memory_manager=memory_manager
        ),
        "documentation-agent": DocumentationAgent(
            agent_id="documentation-agent-001",
            config=AgentConfig(model="gpt-4", tools=["file_manager", "markdown_generator"]),
            model_manager=model_manager,
            tool_manager=tool_manager,
            memory_manager=memory_manager
        ),
        "deploy-agent": DeployAgent(
            agent_id="deploy-agent-001",
            config=AgentConfig(model="gpt-4", tools=["docker", "kubernetes", "terminal"]),
            model_manager=model_manager,
            tool_manager=tool_manager,
            memory_manager=memory_manager
        ),
        "browser-agent": BrowserAgent(
            agent_id="browser-agent-001",
            config=AgentConfig(model="gpt-4", tools=["selenium", "requests", "beautifulsoup"]),
            model_manager=model_manager,
            tool_manager=tool_manager,
            memory_manager=memory_manager
        ),
        "security-agent": SecurityAgent(
            agent_id="security-agent-001",
            config=AgentConfig(model="gpt-4", tools=["security_scanner", "vulnerability_checker"]),
            model_manager=model_manager,
            tool_manager=tool_manager,
            memory_manager=memory_manager
        )
    }
    print("✅ All agents initialized")

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                disconnected.append(connection)
        
        for connection in disconnected:
            self.disconnect(connection)

manager = ConnectionManager()

# Authentication endpoints
@app.post("/api/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    user = AuthService.create_user(
        db=db,
        email=user_data.email,
        username=user_data.username,
        password=user_data.password,
        full_name=user_data.full_name
    )
    return user

@app.post("/api/auth/login", response_model=TokenResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Login user and return JWT tokens."""
    user = AuthService.authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = AuthService.create_access_token(data={"sub": user.id})
    refresh_token = AuthService.create_refresh_token(data={"sub": user.id})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=30 * 60  # 30 minutes
    )

@app.post("/api/auth/refresh", response_model=TokenResponse)
async def refresh_token(refresh_data: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refresh access token using refresh token."""
    payload = AuthService.verify_token(refresh_data.refresh_token)
    
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    access_token = AuthService.create_access_token(data={"sub": user.id})
    new_refresh_token = AuthService.create_refresh_token(data={"sub": user.id})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=30 * 60
    )

@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information."""
    return current_user

# Project endpoints
@app.post("/api/projects", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new project."""
    project = Project(
        name=project_data.name,
        description=project_data.description,
        owner_id=current_user.id,
        settings=project_data.settings or {}
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

@app.get("/api/projects", response_model=List[ProjectResponse])
async def get_projects(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's projects."""
    projects = db.query(Project).filter(Project.owner_id == current_user.id).all()
    return projects

@app.get("/api/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific project."""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

# Agent execution endpoints
@app.post("/api/agents/{agent_type}/execute", response_model=AgentExecutionResponse)
async def execute_agent(
    agent_type: str,
    request: AgentExecutionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Execute an agent task."""
    if agent_type not in agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Create execution record
    execution = Execution(
        user_id=current_user.id,
        project_id=request.project_id,
        agent_type=agent_type,
        task_description=request.task_description,
        parameters=request.parameters or {},
        status="running"
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)
    
    try:
        # Execute agent task
        start_time = time.time()
        agent = agents[agent_type]
        result = await agent.execute_task(request.task_description, request.parameters or {})
        execution_time = int((time.time() - start_time) * 1000)
        
        # Update execution record
        execution.status = "completed"
        execution.result = result
        execution.execution_time = execution_time
        execution.completed_at = datetime.utcnow()
        db.commit()
        
        # Broadcast update via WebSocket
        await manager.broadcast(json.dumps({
            "type": "execution_completed",
            "execution_id": execution.id,
            "agent_type": agent_type,
            "status": "completed"
        }))
        
        return AgentExecutionResponse(
            execution_id=execution.id,
            status="completed",
            result=result,
            execution_time=execution_time
        )
        
    except Exception as e:
        # Update execution record with error
        execution.status = "failed"
        execution.error_message = str(e)
        execution.completed_at = datetime.utcnow()
        db.commit()
        
        return AgentExecutionResponse(
            execution_id=execution.id,
            status="failed",
            error_message=str(e)
        )

@app.get("/api/executions", response_model=List[ExecutionResponse])
async def get_executions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0
):
    """Get user's execution history."""
    executions = db.query(Execution).filter(
        Execution.user_id == current_user.id
    ).order_by(Execution.created_at.desc()).offset(offset).limit(limit).all()
    return executions

@app.get("/api/executions/{execution_id}", response_model=ExecutionResponse)
async def get_execution(
    execution_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific execution."""
    execution = db.query(Execution).filter(
        Execution.id == execution_id,
        Execution.user_id == current_user.id
    ).first()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution

# Dashboard endpoints
@app.get("/api/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics."""
    total_executions = db.query(Execution).filter(Execution.user_id == current_user.id).count()
    successful_executions = db.query(Execution).filter(
        Execution.user_id == current_user.id,
        Execution.status == "completed"
    ).count()
    failed_executions = db.query(Execution).filter(
        Execution.user_id == current_user.id,
        Execution.status == "failed"
    ).count()
    total_projects = db.query(Project).filter(Project.owner_id == current_user.id).count()
    active_sessions = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id,
        ChatSession.is_active == True
    ).count()
    
    return DashboardStats(
        total_executions=total_executions,
        successful_executions=successful_executions,
        failed_executions=failed_executions,
        total_projects=total_projects,
        active_sessions=active_sessions
    )

@app.get("/api/system/health", response_model=SystemHealth)
async def get_system_health():
    """Get system health status."""
    import psutil
    
    return SystemHealth(
        status="healthy",
        uptime="2 days, 14 hours",
        memory_usage=psutil.virtual_memory().percent,
        cpu_usage=psutil.cpu_percent(),
        active_connections=len(manager.active_connections)
    )

# Public endpoints (no auth required)
@app.get("/api/agents")
async def get_agents():
    """Get available agents."""
    return {
        "agents": [
            {
                "type": agent_type,
                "name": agent_type.replace("-", " ").title(),
                "capabilities": agent.get_capabilities(),
                "status": "active"
            }
            for agent_type, agent in agents.items()
        ]
    }

# WebSocket endpoint
@app.websocket("/ws/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time dashboard updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Send periodic updates
            await asyncio.sleep(5)
            await websocket.send_text(json.dumps({
                "type": "heartbeat",
                "timestamp": datetime.utcnow().isoformat(),
                "active_connections": len(manager.active_connections)
            }))
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    uvicorn.run(
        "main_with_auth:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )