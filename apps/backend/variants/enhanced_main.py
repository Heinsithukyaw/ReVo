"""
Enhanced reVoAgent Backend Application
Part of reVoAgent Next Phase Implementation
Integrates: Enhanced WebSocket, Agent Coordination, and Monitoring
"""

import sys
import asyncio
import logging
import uuid
from pathlib import Path
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Optional
import uvicorn
from datetime import datetime

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import enhanced services
from .services.enhanced_websocket_manager import enhanced_websocket_manager
from .services.enhanced_agent_coordinator import enhanced_agent_coordinator, AgentStatus, TaskPriority
from .services.enhanced_monitoring_service import enhanced_monitoring_service

# Import existing services
from .engine_api import router as engine_router, initialize_engines, get_engine_coordinator
from .memory_api import get_memory_routers, initialize_memory_system
from .api.routes.ai_intelligence import router as ai_intelligence_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="reVoAgent Enhanced - Next Phase Implementation", 
    version="4.0.0",
    description="Enhanced Three-Engine AI Architecture with Real-time Communication, Agent Coordination, and Production Monitoring"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
system_state = {
    "startup_time": datetime.now(),
    "version": "4.0.0",
    "features": [
        "Enhanced WebSocket Communication",
        "Real-time Agent Coordination", 
        "Production Monitoring",
        "Three-Engine Architecture",
        "Memory Integration"
    ]
}

@app.on_event("startup")
async def startup_event():
    """Initialize all enhanced services"""
    try:
        logger.info("🚀 Starting reVoAgent Enhanced Backend...")
        
        # Initialize monitoring service first
        logger.info("📊 Initializing monitoring service...")
        enhanced_monitoring_service.websocket_manager = enhanced_websocket_manager
        await enhanced_monitoring_service.initialize()
        await enhanced_monitoring_service.start_monitoring()
        
        # Initialize agent coordinator
        logger.info("🤖 Initializing agent coordinator...")
        enhanced_agent_coordinator.websocket_manager = enhanced_websocket_manager
        await enhanced_agent_coordinator.start()
        
        # Start WebSocket heartbeat monitor
        logger.info("🔗 Starting WebSocket heartbeat monitor...")
        asyncio.create_task(enhanced_websocket_manager.start_heartbeat_monitor())
        
        # Initialize memory system
        logger.info("🧠 Initializing memory system...")
        memory_config = {
            "memory_config": {
                "enable_memory": True,
                "vector_db_provider": "lancedb",
                "graph_db_provider": "networkx",
                "memory_data_path": "./data/cognee_memory"
            }
        }
        await initialize_memory_system(memory_config)
        
        # Initialize three-engine architecture
        logger.info("⚡ Initializing three-engine architecture...")
        await initialize_engines()
        
        # Include routers
        app.include_router(engine_router)
        app.include_router(ai_intelligence_router)
        for router in get_memory_routers():
            app.include_router(router)
        
        # Register sample agents for demonstration
        await _register_sample_agents()
        
        logger.info("✅ reVoAgent Enhanced Backend started successfully!")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 Shutting down reVoAgent Enhanced Backend...")
    
    try:
        # Stop monitoring service
        await enhanced_monitoring_service.stop_monitoring()
        
        # Stop agent coordinator
        await enhanced_agent_coordinator.stop()
        
        # Cleanup WebSocket manager
        await enhanced_websocket_manager.cleanup()
        
        logger.info("✅ Shutdown complete")
        
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")

async def _register_sample_agents():
    """Register sample agents for demonstration"""
    sample_agents = [
        {
            "id": "code_generator_001",
            "name": "Code Generator Agent",
            "capabilities": ["code_generation", "refactoring", "optimization"],
            "max_concurrent": 3
        },
        {
            "id": "debug_detective_001", 
            "name": "Debug Detective Agent",
            "capabilities": ["debugging", "error_analysis", "troubleshooting"],
            "max_concurrent": 2
        },
        {
            "id": "testing_agent_001",
            "name": "Testing Agent",
            "capabilities": ["test_generation", "test_execution", "coverage_analysis"],
            "max_concurrent": 2
        },
        {
            "id": "documentation_agent_001",
            "name": "Documentation Agent", 
            "capabilities": ["documentation", "api_docs", "user_guides"],
            "max_concurrent": 1
        },
        {
            "id": "security_agent_001",
            "name": "Security Agent",
            "capabilities": ["security_analysis", "vulnerability_scan", "compliance"],
            "max_concurrent": 1
        }
    ]
    
    for agent_data in sample_agents:
        await enhanced_agent_coordinator.register_agent(
            agent_data["id"],
            agent_data["name"],
            agent_data["capabilities"],
            agent_data["max_concurrent"]
        )
        
        # Simulate agent heartbeat
        await enhanced_agent_coordinator.agent_heartbeat(agent_data["id"])

# Enhanced WebSocket endpoint
@app.websocket("/ws/{connection_id}")
async def websocket_endpoint(websocket: WebSocket, connection_id: str):
    """Enhanced WebSocket endpoint with full message handling"""
    success = await enhanced_websocket_manager.connect(websocket, connection_id)
    
    if not success:
        await websocket.close(code=1011, reason="Connection failed")
        return
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            
            # Handle message through enhanced manager
            await enhanced_websocket_manager.handle_message(connection_id, data)
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket client {connection_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for {connection_id}: {e}")
    finally:
        await enhanced_websocket_manager.disconnect(connection_id)

# Enhanced API Endpoints

@app.get("/health")
async def health_check():
    """Enhanced health check with detailed system status"""
    try:
        # Get monitoring health status
        monitoring_health = enhanced_monitoring_service.get_health_status()
        
        # Get agent coordinator overview
        agent_overview = await enhanced_agent_coordinator.get_system_overview()
        
        # Get WebSocket connection stats
        ws_stats = enhanced_websocket_manager.get_connection_stats()
        
        # Get current metrics
        current_metrics = await enhanced_monitoring_service.get_current_metrics()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": system_state["version"],
            "uptime_seconds": (datetime.now() - system_state["startup_time"]).total_seconds(),
            "monitoring": monitoring_health,
            "agents": agent_overview,
            "websockets": {
                "total_connections": ws_stats["total_connections"],
                "total_subscriptions": ws_stats["total_subscriptions"],
                "active_channels": len(ws_stats["channels"])
            },
            "system_metrics": current_metrics
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.get("/api/system/overview")
async def get_system_overview():
    """Get comprehensive system overview"""
    try:
        return {
            "agents": await enhanced_agent_coordinator.get_system_overview(),
            "monitoring": enhanced_monitoring_service.get_health_status(),
            "websockets": enhanced_websocket_manager.get_connection_stats(),
            "metrics": await enhanced_monitoring_service.get_current_metrics(),
            "alerts": await enhanced_monitoring_service.get_alerts(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting system overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agents")
async def list_agents():
    """List all registered agents"""
    try:
        agents = []
        for agent_id, agent in enhanced_agent_coordinator.agents.items():
            agent_data = await enhanced_agent_coordinator.get_agent_details(agent_id)
            if agent_data:
                agents.append(agent_data)
        
        return {"agents": agents}
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agents/{agent_id}")
async def get_agent_details(agent_id: str):
    """Get detailed information about a specific agent"""
    try:
        agent_data = await enhanced_agent_coordinator.get_agent_details(agent_id)
        if not agent_data:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        return agent_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agents/{agent_id}/tasks")
async def submit_agent_task(
    agent_id: str,
    task_data: Dict[str, Any]
):
    """Submit a task to a specific agent"""
    try:
        task_type = task_data.get("task_type", "general")
        description = task_data.get("description", "")
        parameters = task_data.get("parameters", {})
        priority = TaskPriority[task_data.get("priority", "MEDIUM").upper()]
        
        if not description:
            raise HTTPException(status_code=400, detail="Task description is required")
        
        # Check if agent exists
        if agent_id not in enhanced_agent_coordinator.agents:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        task_id = await enhanced_agent_coordinator.submit_task(
            task_type=task_type,
            description=description,
            parameters=parameters,
            priority=priority,
            preferred_agent=agent_id
        )
        
        return {
            "task_id": task_id,
            "agent_id": agent_id,
            "status": "submitted",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tasks")
async def submit_task(task_data: Dict[str, Any]):
    """Submit a task to the best available agent"""
    try:
        task_type = task_data.get("task_type", "general")
        description = task_data.get("description", "")
        parameters = task_data.get("parameters", {})
        priority = TaskPriority[task_data.get("priority", "MEDIUM").upper()]
        required_capabilities = task_data.get("required_capabilities", [])
        
        if not description:
            raise HTTPException(status_code=400, detail="Task description is required")
        
        task_id = await enhanced_agent_coordinator.submit_task(
            task_type=task_type,
            description=description,
            parameters=parameters,
            priority=priority,
            required_capabilities=required_capabilities
        )
        
        return {
            "task_id": task_id,
            "status": "submitted",
            "timestamp": datetime.now().isoformat()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/monitoring/metrics")
async def get_monitoring_metrics():
    """Get current monitoring metrics"""
    try:
        return await enhanced_monitoring_service.get_current_metrics()
    except Exception as e:
        logger.error(f"Error getting monitoring metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/monitoring/alerts")
async def get_alerts(include_resolved: bool = False):
    """Get current alerts"""
    try:
        alerts = await enhanced_monitoring_service.get_alerts(include_resolved)
        return {"alerts": alerts}
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/monitoring/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """Resolve an alert"""
    try:
        await enhanced_monitoring_service.resolve_alert(alert_id)
        return {"status": "resolved", "alert_id": alert_id}
    except Exception as e:
        logger.error(f"Error resolving alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/monitoring/response-time")
async def record_response_time(data: Dict[str, Any]):
    """Record a response time measurement"""
    try:
        response_time = data.get("response_time")
        if response_time is None:
            raise HTTPException(status_code=400, detail="response_time is required")
        
        await enhanced_monitoring_service.record_response_time(response_time)
        return {"status": "recorded"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording response time: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/websockets/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics"""
    try:
        return enhanced_websocket_manager.get_connection_stats()
    except Exception as e:
        logger.error(f"Error getting WebSocket stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Middleware to record response times
@app.middleware("http")
async def record_response_time_middleware(request, call_next):
    start_time = datetime.now()
    response = await call_next(request)
    end_time = datetime.now()
    
    response_time = (end_time - start_time).total_seconds() * 1000  # Convert to milliseconds
    
    # Record response time for monitoring
    try:
        await enhanced_monitoring_service.record_response_time(response_time)
    except Exception as e:
        logger.error(f"Error recording response time in middleware: {e}")
    
    # Add response time header
    response.headers["X-Response-Time"] = f"{response_time:.2f}ms"
    
    return response

if __name__ == "__main__":
    uvicorn.run(
        "enhanced_main:app",
        host="0.0.0.0",
        port=12000,
        reload=False,
        log_level="info"
    )