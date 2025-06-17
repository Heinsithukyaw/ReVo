"""
reVoAgent Enterprise API
Main FastAPI application with integrated LLM orchestrator and enterprise features
"""
import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field
import uvicorn

# Import enterprise packages
from packages.core.config import get_settings, Settings
from packages.models.llm_orchestrator import (
    get_llm_orchestrator, 
    initialize_llm_orchestrator,
    GenerationResult
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Request/Response Models
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    model: Optional[str] = Field(None, description="Specific model to use")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(2048, ge=1, le=4096)
    stream: Optional[bool] = Field(False, description="Stream response")

class ChatResponse(BaseModel):
    response: str
    model: str
    response_time: float
    tokens_used: int
    cost: float
    metadata: Dict[str, Any]

class HealthResponse(BaseModel):
    status: str
    timestamp: int
    services: Dict[str, Any]
    version: str

class ModelStatusResponse(BaseModel):
    orchestrator: Dict[str, Any]
    models: Dict[str, Any]

# Global state
app_state = {
    "startup_time": time.time(),
    "request_count": 0,
    "total_response_time": 0.0
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("🚀 Starting reVoAgent Enterprise API...")
    
    settings = get_settings()
    
    # Initialize LLM orchestrator
    try:
        await initialize_llm_orchestrator(settings.llm)
        logger.info("✅ LLM Orchestrator initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize LLM Orchestrator: {e}")
        raise
    
    # Initialize other services
    app_state["startup_time"] = time.time()
    logger.info("✅ reVoAgent Enterprise API ready")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down reVoAgent Enterprise API...")
    orchestrator = get_llm_orchestrator()
    await orchestrator.cleanup()
    logger.info("✅ Cleanup complete")

# Create FastAPI application
def create_app() -> FastAPI:
    settings = get_settings()
    
    app = FastAPI(
        title="reVoAgent Enterprise API",
        description="Enterprise-grade AI agent platform with three-engine architecture",
        version="2.0.0",
        lifespan=lifespan,
        openapi_url=f"{settings.api_prefix}/openapi.json",
        docs_url=f"{settings.api_prefix}/docs",
        redoc_url=f"{settings.api_prefix}/redoc"
    )
    
    # Add middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.security.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.security.allowed_hosts
    )
    
    return app

app = create_app()

# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    logger.warning(f"Validation error: {exc}")
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "details": exc.errors(),
            "timestamp": int(time.time())
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "timestamp": int(time.time())
        }
    )

# Middleware for request tracking
@app.middleware("http")
async def track_requests(request, call_next):
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Track metrics
    process_time = time.time() - start_time
    app_state["request_count"] += 1
    app_state["total_response_time"] += process_time
    
    # Add headers
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-Request-ID"] = str(app_state["request_count"])
    
    return response

# Health Check Endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Comprehensive health check"""
    settings = get_settings()
    orchestrator = get_llm_orchestrator()
    
    try:
        # Check LLM orchestrator health
        model_health = await orchestrator.health_check()
        
        # Get model status
        model_status = await orchestrator.get_model_status()
        
        # Calculate uptime
        uptime = time.time() - app_state["startup_time"]
        
        # Calculate average response time
        avg_response_time = 0.0
        if app_state["request_count"] > 0:
            avg_response_time = app_state["total_response_time"] / app_state["request_count"]
        
        health_data = {
            "status": "healthy",
            "timestamp": int(time.time()),
            "services": {
                "api": {
                    "status": "healthy",
                    "uptime": f"{uptime:.2f}s",
                    "requests": app_state["request_count"],
                    "avg_response_time": f"{avg_response_time:.3f}s"
                },
                "llm_orchestrator": {
                    "status": "healthy" if any(model_health.values()) else "unhealthy",
                    "models": model_health,
                    "primary_model": model_status["orchestrator"]["current_model"],
                    "total_requests": model_status["orchestrator"]["request_count"]
                }
            },
            "version": "2.0.0"
        }
        
        return health_data
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

# Chat Endpoint
@app.post(f"{get_settings().api_prefix}/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    """Chat with the AI agent using enterprise LLM orchestrator"""
    try:
        orchestrator = get_llm_orchestrator()
        
        # Generate response
        generation_kwargs = {
            "temperature": request.temperature,
            "max_tokens": request.max_tokens
        }
        
        if request.model:
            # Try to switch to specific model
            if not await orchestrator.switch_model(request.model):
                logger.warning(f"Failed to switch to model {request.model}, using fallback")
        
        result: GenerationResult = await orchestrator.generate(
            request.message,
            **generation_kwargs
        )
        
        return ChatResponse(
            response=result.response,
            model=result.model,
            response_time=result.response_time,
            tokens_used=result.tokens_used,
            cost=result.cost,
            metadata=result.metadata
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Chat processing failed: {str(e)}"
        )

# Model Management Endpoints
@app.get(f"{get_settings().api_prefix}/models/status", response_model=ModelStatusResponse)
async def get_model_status():
    """Get status of all LLM models"""
    try:
        orchestrator = get_llm_orchestrator()
        status = await orchestrator.get_model_status()
        return ModelStatusResponse(**status)
    except Exception as e:
        logger.error(f"Error getting model status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get model status")

@app.post(f"{get_settings().api_prefix}/models/switch")
async def switch_model(model_name: str):
    """Switch to a specific model"""
    try:
        orchestrator = get_llm_orchestrator()
        success = await orchestrator.switch_model(model_name)
        
        if success:
            return {"message": f"Switched to model: {model_name}"}
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to switch to model: {model_name}"
            )
    except Exception as e:
        logger.error(f"Error switching model: {e}")
        raise HTTPException(status_code=500, detail="Model switch failed")

# System Information Endpoints
@app.get(f"{get_settings().api_prefix}/system/info")
async def get_system_info():
    """Get system information"""
    settings = get_settings()
    
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "api_prefix": settings.api_prefix,
        "ports": {
            "backend": settings.backend_port,
            "frontend": settings.frontend_port,
            "memory": settings.memory_port,
            "engine": settings.engine_port
        },
        "features": {
            "three_engines": settings.three_engine.enable_three_engines,
            "memory_system": settings.memory.enable_memory_system,
            "local_models": settings.llm.use_local_models,
            "monitoring": settings.monitoring.enable_metrics
        }
    }

@app.get(f"{get_settings().api_prefix}/system/metrics")
async def get_metrics():
    """Get application metrics"""
    uptime = time.time() - app_state["startup_time"]
    avg_response_time = 0.0
    
    if app_state["request_count"] > 0:
        avg_response_time = app_state["total_response_time"] / app_state["request_count"]
    
    return {
        "uptime": uptime,
        "requests_total": app_state["request_count"],
        "avg_response_time": avg_response_time,
        "total_response_time": app_state["total_response_time"]
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    settings = get_settings()
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "environment": settings.environment,
        "docs": f"{settings.api_prefix}/docs",
        "health": "/health",
        "timestamp": int(time.time())
    }

# Development server
if __name__ == "__main__":
    settings = get_settings()
    
    uvicorn.run(
        "main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=settings.debug,
        log_level="info",
        access_log=True
    )
