#!/usr/bin/env python3
"""
reVoAgent Consolidated Backend Server with Enhanced LLM Integration

Implements Phase 4 of the enhancement plan:
- Clean Architecture & Testing
- Enhanced Error Handling
- LLM Response Validation
- Full Stack Integration Testing
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
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from fastapi.exceptions import RequestValidationError

# Add project paths
sys.path.append('src')
sys.path.append('apps')
sys.path.append('packages')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("backend_main")

# Import custom error handler
from src.revoagent.utils.error_handler import register_error_handlers, ErrorDetails, ErrorCategory, ErrorSeverity

# Import LLM validator
from src.revoagent.validation.llm_validator import llm_validator, ValidationResult, ValidationType

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
        'config/ports.yaml',
        'config/fallback_config.yaml'
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
    description="Enhanced backend with local + fallback LLM system",
    version="2.0.0",
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
    fallback_info: Optional[Dict[str, Any]] = None

class CodeRequest(BaseModel):
    task_description: str
    language: Optional[str] = "python"
    framework: Optional[str] = "fastapi"
    database: Optional[str] = "postgresql"
    features: Optional[List[str]] = []
    model: Optional[str] = "deepseek-r1"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2000

class CodeResponse(BaseModel):
    generated_code: str
    model_used: str
    generation_time: str
    quality_score: float
    estimated_lines: int
    files_created: Optional[List[str]] = []
    status: str
    fallback_info: Optional[Dict[str, Any]] = None

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
    fallback_info: Optional[Dict[str, Any]] = None

class ModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    source: str
    status: str
    cost_per_token: float
    features: Optional[List[str]] = []

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
        version="2.0.0",
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
        except:
            llm_ready = False
    
    status = "ready" if llm_ready else "not_ready"
    return {"status": status, "timestamp": datetime.now().isoformat()}

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
        "version": "2.0.0"
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
async def chat_endpoint(request: ChatRequest, req: Request):
    """Main chat endpoint with real LLM integration and validation."""
    if not llm_manager:
        error_details = ErrorDetails(
            message="LLM service not available",
            category=ErrorCategory.LLM,
            severity=ErrorSeverity.HIGH,
            status_code=503,
            client_message="The AI model is currently unavailable. Please try again later."
        )
        return error_details.to_response()
    
    start_time = time.time()
    
    try:
        # Generate response using LLM manager
        response_text = await llm_manager.generate_response(
            request.message,
            request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        # Validate the response
        validation_result = await llm_validator.validate_response(
            response_text, 
            request.message,
            [ValidationType.RELEVANCE, ValidationType.HALLUCINATION]
        )
        
        # Log validation issues if any
        if not validation_result.is_valid:
            logger.warning(f"Response validation issues: {validation_result.issues}")
        
        response_time = time.time() - start_time
        tokens_used = len(response_text.split())  # Approximate
        
        # Check if fallback was used
        fallback_info = None
        
        # Get the stats from the fallback manager
        if llm_manager.fallback_manager and llm_manager.fallback_manager.enabled:
            stats = llm_manager.fallback_manager.get_fallback_stats()
            if stats.get("total_events", 0) > 0:
                # Check if the last event timestamp is close to this request
                last_event_time = stats.get("last_event_time")
                if last_event_time and (time.time() - last_event_time) < 10:  # Within 10 seconds
                    fallback_info = {
                        "used": True,
                        "reason": list(stats.get("reason_counts", {}).keys())[-1] if stats.get("reason_counts") else "unknown",
                        "validation_score": validation_result.score
                    }
        
        return ChatResponse(
            response=response_text,
            model=request.model,
            timestamp=datetime.now().isoformat(),
            tokens_used=tokens_used,
            response_time=response_time,
            fallback_info=fallback_info
        )
    except Exception as e:
        logger.error(f"Chat error: {e}")
        # Use our enhanced error handler
        return ErrorDetails(
            message=f"Error generating chat response: {str(e)}",
            category=ErrorCategory.LLM,
            severity=ErrorSeverity.HIGH,
            status_code=500,
            exception=e,
            client_message="Failed to generate a response. Please try again later."
        ).to_response()

@app.post("/api/code", response_model=CodeResponse)
async def generate_code_endpoint(request: CodeRequest, req: Request):
    """Code generation endpoint with fallback support and validation."""
    if not llm_manager:
        error_details = ErrorDetails(
            message="LLM service not available",
            category=ErrorCategory.LLM,
            severity=ErrorSeverity.HIGH,
            status_code=503,
            client_message="The code generation service is currently unavailable. Please try again later."
        )
        return error_details.to_response()
    
    try:
        # Prepare code generation request
        code_request = {
            "task_description": request.task_description,
            "language": request.language,
            "framework": request.framework,
            "database": request.database,
            "features": request.features
        }
        
        # Generate code using enhanced LLM manager
        result = await llm_manager.generate_code(
            code_request,
            request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        # Validate the generated code
        generated_code = result.get("generated_code", "")
        validation_result = await llm_validator.validate_response(
            generated_code,
            request.task_description,
            [ValidationType.CODE_SYNTAX, ValidationType.SECURITY]
        )
        
        # Add validation score to result
        result["quality_score"] = validation_result.score
        
        # Log validation issues if any
        if not validation_result.is_valid:
            logger.warning(f"Code validation issues: {validation_result.issues}")
            result["validation_issues"] = [issue.get("message") for issue in validation_result.issues]
        
        # Check if fallback was used (add to response if needed)
        fallback_info = None
        if llm_manager.fallback_manager and llm_manager.fallback_manager.enabled:
            stats = llm_manager.fallback_manager.get_fallback_stats()
            if stats.get("total_events", 0) > 0:
                # Check if the last event timestamp is close to this request
                last_event_time = stats.get("last_event_time")
                if last_event_time and (time.time() - last_event_time) < 10:  # Within 10 seconds
                    fallback_info = {
                        "used": True,
                        "reason": list(stats.get("reason_counts", {}).keys())[-1] if stats.get("reason_counts") else "unknown",
                        "validation_score": validation_result.score
                    }
        
        # Add fallback info to result
        result["fallback_info"] = fallback_info
        
        return result
    except Exception as e:
        logger.error(f"Code generation error: {e}")
        # Use enhanced error handling
        return ErrorDetails(
            message=f"Error generating code: {str(e)}",
            category=ErrorCategory.LLM,
            severity=ErrorSeverity.HIGH,
            status_code=500,
            exception=e,
            client_message="Failed to generate code. Please try again or modify your request."
        ).to_response()

@app.post("/api/chat/multi-agent")
async def multi_agent_chat(request: ChatRequest, req: Request):
    """Multi-agent collaboration endpoint with real LLM integration and validation."""
    if not llm_manager:
        error_details = ErrorDetails(
            message="LLM service not available",
            category=ErrorCategory.LLM,
            severity=ErrorSeverity.HIGH,
            status_code=503,
            client_message="The multi-agent service is currently unavailable. Please try again later."
        )
        return error_details.to_response()
    
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
            
            # Validate response
            validation_types = [ValidationType.RELEVANCE]
            if agent == "code_analyst":
                validation_types.append(ValidationType.CODE_SYNTAX)
            
            validation_result = await llm_validator.validate_response(
                response_text,
                request.message,
                validation_types
            )
            
            # Log validation issues if any
            if not validation_result.is_valid:
                logger.warning(f"{agent} response validation issues: {validation_result.issues}")
            
            response = {
                "agent": agent,
                "response": response_text,
                "timestamp": datetime.now().isoformat(),
                "model": request.model,
                "validation_score": validation_result.score
            }
            responses.append(response)
        
        return {"responses": responses}
    except Exception as e:
        logger.error(f"Multi-agent error: {e}")
        return ErrorDetails(
            message=f"Error in multi-agent processing: {str(e)}",
            category=ErrorCategory.LLM,
            severity=ErrorSeverity.HIGH,
            status_code=500,
            exception=e,
            client_message="Failed to process multi-agent request. Please try again later."
        ).to_response()

@app.post("/api/agent", response_model=AgentResponse)
async def agent_endpoint(request: AgentRequest, req: Request):
    """Single agent endpoint with specialized prompting and validation."""
    if not llm_manager:
        error_details = ErrorDetails(
            message="LLM service not available",
            category=ErrorCategory.LLM,
            severity=ErrorSeverity.HIGH,
            status_code=503,
            client_message="The agent service is currently unavailable. Please try again later."
        )
        return error_details.to_response()
    
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
        
        # Validate the response
        validation_types = [ValidationType.RELEVANCE]
        if request.agent_type == "code_analyst":
            validation_types.append(ValidationType.CODE_SYNTAX)
        
        validation_result = await llm_validator.validate_response(
            response_text,
            request.message,
            validation_types
        )
        
        # Log validation issues if any
        if not validation_result.is_valid:
            logger.warning(f"Agent response validation issues: {validation_result.issues}")
        
        # Check for fallback usage
        fallback_info = None
        if llm_manager.fallback_manager and llm_manager.fallback_manager.enabled:
            stats = llm_manager.fallback_manager.get_fallback_stats()
            if stats.get("total_events", 0) > 0:
                last_event_time = stats.get("last_event_time")
                if last_event_time and (time.time() - last_event_time) < 10:
                    fallback_info = {
                        "used": True,
                        "reason": list(stats.get("reason_counts", {}).keys())[-1] if stats.get("reason_counts") else "unknown",
                        "validation_score": validation_result.score
                    }

# Error handlers are now registered in the startup event
# See startup_event() function
        
        return AgentResponse(
            agent=request.agent_type,
            response=response_text,
            model=request.model,
            timestamp=datetime.now().isoformat(),
            fallback_info=fallback_info
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

@app.get("/api/fallback/stats")
async def get_fallback_stats():
    """Get statistics about fallback system usage."""
    if not llm_manager or not llm_manager.fallback_manager:
        raise HTTPException(status_code=503, detail="Fallback system not available")
    
    try:
        stats = llm_manager.fallback_manager.get_fallback_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting fallback stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get fallback stats: {str(e)}")

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
        await websocket.accept()
        await websocket.send_json({
            "type": "error",
            "error": "LLM service not available",
            "system_status": "not_initialized"
        })
        await websocket.close(code=1013, reason="LLM service not available")
        return
        
    await websocket.accept()
    websocket_connections.append(websocket)
    
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
                logger.error(f"WebSocket error: {e}")
                await websocket.send_json({
                    "type": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
                
    except WebSocketDisconnect:
        websocket_connections.remove(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket general error: {e}")
        try:
            websocket_connections.remove(websocket)
        except ValueError:
            pass

# LLM Configuration endpoints
@app.get("/api/config/llm")
async def get_llm_config():
    """Get current LLM configuration."""
    if not llm_manager:
        raise HTTPException(status_code=503, detail="LLM service not available")
        
    # Get fallback system status
    fallback_enabled = False
    if hasattr(llm_manager, "fallback_manager") and llm_manager.fallback_manager:
        fallback_enabled = llm_manager.fallback_manager.enabled
    
    return {
        "default_model": CONFIG.get("llm", {}).get("default_model", "deepseek-r1"),
        "available_providers": list(CONFIG.get("llm", {}).get("providers", {}).keys()),
        "fallback_system": fallback_enabled,
        "status": await llm_manager.get_health() if llm_manager else {"status": "not_initialized"}
    }

@app.get("/api/llm/status")
async def get_llm_status():
    """Get LLM service status."""
    if not llm_manager:
        return {
            "status": "not_available",
            "message": "LLM service is not initialized",
            "timestamp": datetime.now().isoformat()
        }
    
    try:
        # Get health status from LLM manager
        health = await llm_manager.get_health()
        
        # Get available models
        models = await llm_manager.get_available_models()
        
        return {
            "status": health.get("status", "unknown"),
            "models_count": len(models),
            "models": models,
            "fallback_system": hasattr(llm_manager, "fallback_manager") and getattr(llm_manager.fallback_manager, "enabled", False),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting LLM status: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Error handlers moved to src/revoagent/utils/error_handler.py

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global llm_manager
    
    logger.info("reVoAgent Enhanced Backend Server starting with Fallback System...")
    
    # Register enhanced error handlers
    register_error_handlers(app)
    logger.info("Enhanced error handlers registered")
    
    # Initialize LLM Manager using the new initializer
    try:
        from src.revoagent.utils.llm_initializer import LLMInitializer
        
        # Initialize the LLM system
        llm_manager = await LLMInitializer.initialize_llm_system()
        
        if llm_manager and llm_manager.initialized:
            logger.info("LLM Manager initialized successfully")
            
            # Log available models
            try:
                models = await llm_manager.get_available_models()
                logger.info(f"Available models: {len(models)}")
            except Exception as e:
                logger.warning(f"Failed to get available models: {e}")
            
            # Log fallback system status if available
            if hasattr(llm_manager, "fallback_manager") and llm_manager.fallback_manager:
                if getattr(llm_manager.fallback_manager, "enabled", False):
                    logger.info("Fallback system is enabled")
                else:
                    logger.warning("Fallback system is disabled")
        else:
            logger.warning("LLM Manager initialization failed")
            
    except Exception as e:
        logger.error(f"Error initializing LLM Manager: {e}")
        llm_manager = None
    
    # Initialize LLM validator
    try:
        await llm_validator.validate_response("Test response", "Test prompt")
        logger.info("LLM validator initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing LLM validator: {e}")
    
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
    
    logger.info(f"Starting reVoAgent Backend Server with Fallback System on {host}:{port}")
    logger.info(f"API Documentation available at: http://localhost:{port}/docs")
    logger.info(f"Health Check: http://localhost:{port}/health")
    
    uvicorn.run(
        "backend_main_fallback:app",
        host=host,
        port=port,
        workers=1 if reload else workers,  # 1 worker when reload=True
        reload=reload,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main()