#!/usr/bin/env python3
"""
Refactored Backend API Main Entry Point
Clean, modular FastAPI application with proper service separation
"""

import sys
import asyncio
import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
import uvicorn

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Import security middleware
from ..middleware.security_middleware import (
    SecurityHeadersMiddleware,
    CORSSecurityMiddleware,
    RateLimitingMiddleware
)

# Import service modules
from ..services.ai_service import ProductionAIService, create_production_ai_service, GenerationRequest
from ..services.ai_team_coordinator import AITeamCoordinator
from ..services.cost_optimizer import CostOptimizedRouter
from ..services.quality_gates import QualityGates
from ..services.ai_team_monitoring import AITeamMonitoring

# Import API routers
from .routers.ai_router import router as ai_router
from .routers.team_router import router as team_router
from .routers.monitoring_router import router as monitoring_router
from .routers.health_router import router as health_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackendApplication:
    """
    Refactored Backend Application
    
    Clean separation of concerns:
    - AI Service: Model management and generation
    - Team Coordinator: Agent coordination and task management
    - Cost Optimizer: Cost optimization and routing
    - Quality Gates: Code quality validation
    - Monitoring: Performance monitoring and analytics
    """
    
    def __init__(self):
        """Initialize the backend application"""
        self.app = FastAPI(
            title="reVoAgent Backend API",
            description="Enterprise AI Development Platform - Refactored Backend",
            version="2.0.0",
            docs_url="/docs",
            redoc_url="/redoc"
        )
        
        # Service instances
        self.ai_service: Optional[ProductionAIService] = None
        self.team_coordinator: Optional[AITeamCoordinator] = None
        self.cost_optimizer: Optional[CostOptimizedRouter] = None
        self.quality_gates: Optional[QualityGates] = None
        self.monitoring: Optional[AITeamMonitoring] = None
        
        # Setup application
        self._setup_middleware()
        self._setup_routes()
        self._setup_event_handlers()
        
        logger.info("🚀 Backend Application initialized")
    
    def _setup_middleware(self):
        """Setup FastAPI middleware with enterprise security"""
        
        # 1. Security Headers Middleware (Applied first for all responses)
        self.app.add_middleware(SecurityHeadersMiddleware)
        
        # 2. Rate Limiting Middleware
        self.app.add_middleware(
            RateLimitingMiddleware,
            requests_per_minute=100  # Configurable rate limit
        )
        
        # 3. Secure CORS Middleware (replaces default CORS)
        self.app.add_middleware(
            CORSSecurityMiddleware,
            allowed_origins=[
                "http://localhost:12000",  # Frontend development
                "https://app.revoagent.dev",  # Production frontend
                "http://localhost:3000",  # Alternative frontend port
            ],
            allowed_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        )
        
        # 4. Request logging and performance monitoring
        @self.app.middleware("http")
        async def log_requests_and_monitor(request, call_next):
            start_time = asyncio.get_event_loop().time()
            
            # Log incoming request
            logger.info(f"📡 {request.method} {request.url.path} - Client: {request.client.host if request.client else 'unknown'}")
            
            try:
                response = await call_next(request)
                process_time = asyncio.get_event_loop().time() - start_time
                
                # Log response with performance metrics
                logger.info(f"✅ {request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
                
                # Add performance headers
                response.headers["X-Response-Time"] = f"{process_time:.3f}s"
                response.headers["X-Request-ID"] = str(id(request))
                
                return response
                
            except Exception as e:
                process_time = asyncio.get_event_loop().time() - start_time
                logger.error(f"❌ {request.method} {request.url.path} - Error: {str(e)} - {process_time:.3f}s")
                raise
    
    def _setup_routes(self):
        """Setup API routes"""
        
        # Include API routers
        self.app.include_router(health_router, prefix="/api/v1/health", tags=["health"])
        self.app.include_router(ai_router, prefix="/api/v1/ai", tags=["ai"])
        self.app.include_router(team_router, prefix="/api/v1/team", tags=["team"])
        self.app.include_router(monitoring_router, prefix="/api/v1/monitoring", tags=["monitoring"])
        
        # Root endpoint
        @self.app.get("/")
        async def root():
            return {
                "message": "reVoAgent Backend API v2.0",
                "status": "operational",
                "features": [
                    "Enhanced AI Model Manager",
                    "100-Agent Team Coordination",
                    "Cost Optimization (95% savings)",
                    "Quality Gates System",
                    "Real-time Monitoring"
                ]
            }
        
        # Service status endpoint
        @self.app.get("/api/v1/status")
        async def get_status():
            """Get comprehensive service status"""
            return {
                "services": {
                    "ai_service": "operational" if self.ai_service else "not_initialized",
                    "team_coordinator": "operational" if self.team_coordinator else "not_initialized",
                    "cost_optimizer": "operational" if self.cost_optimizer else "not_initialized",
                    "quality_gates": "operational" if self.quality_gates else "not_initialized",
                    "monitoring": "operational" if self.monitoring else "not_initialized"
                },
                "timestamp": asyncio.get_event_loop().time()
            }
    
    def _setup_event_handlers(self):
        """Setup application event handlers"""
        
        @self.app.on_event("startup")
        async def startup_event():
            """Initialize services on startup"""
            logger.info("🚀 Starting reVoAgent Backend Services...")
            
            try:
                # Initialize services in dependency order
                await self._initialize_services()
                logger.info("✅ All services initialized successfully")
                
            except Exception as e:
                logger.error(f"❌ Service initialization failed: {e}")
                raise
        
        @self.app.on_event("shutdown")
        async def shutdown_event():
            """Cleanup services on shutdown"""
            logger.info("🛑 Shutting down reVoAgent Backend Services...")
            
            try:
                await self._shutdown_services()
                logger.info("✅ All services shut down successfully")
                
            except Exception as e:
                logger.error(f"❌ Service shutdown error: {e}")
    
    async def _initialize_services(self):
        """Initialize all backend services"""
        
        # 1. Initialize AI Service (Enhanced Model Manager)
        logger.info("🤖 Initializing AI Service...")
        self.ai_service = await create_production_ai_service()
        
        # 2. Initialize Cost Optimizer
        logger.info("💰 Initializing Cost Optimizer...")
        self.cost_optimizer = CostOptimizedRouter()
        
        # 3. Initialize Quality Gates
        logger.info("🛡️ Initializing Quality Gates...")
        self.quality_gates = QualityGates()
        
        # 4. Initialize Team Coordinator
        logger.info("👥 Initializing Team Coordinator...")
        self.team_coordinator = AITeamCoordinator(self.ai_service)
        await self.team_coordinator.start_coordination()
        
        # 5. Initialize Monitoring
        logger.info("📊 Initializing Monitoring...")
        self.monitoring = AITeamMonitoring(
            self.team_coordinator,
            self.cost_optimizer,
            self.quality_gates
        )
        await self.monitoring.start_monitoring()
        
        # Store services in app state for dependency injection
        self.app.state.ai_service = self.ai_service
        self.app.state.team_coordinator = self.team_coordinator
        self.app.state.cost_optimizer = self.cost_optimizer
        self.app.state.quality_gates = self.quality_gates
        self.app.state.monitoring = self.monitoring
    
    async def _shutdown_services(self):
        """Shutdown all services gracefully"""
        
        if self.monitoring:
            await self.monitoring.shutdown()
        
        if self.team_coordinator:
            await self.team_coordinator.shutdown()
        
        if self.ai_service:
            await self.ai_service.shutdown()
    
    def get_app(self) -> FastAPI:
        """Get the FastAPI application instance"""
        return self.app

# Dependency injection functions
async def get_ai_service(request) -> ProductionAIService:
    """Get AI service instance"""
    return request.app.state.ai_service

async def get_team_coordinator(request) -> AITeamCoordinator:
    """Get team coordinator instance"""
    return request.app.state.team_coordinator

async def get_cost_optimizer(request) -> CostOptimizedRouter:
    """Get cost optimizer instance"""
    return request.app.state.cost_optimizer

async def get_quality_gates(request) -> QualityGates:
    """Get quality gates instance"""
    return request.app.state.quality_gates

async def get_monitoring(request) -> AITeamMonitoring:
    """Get monitoring instance"""
    return request.app.state.monitoring

# Create application instance
backend_app = BackendApplication()
app = backend_app.get_app()

# Main entry point
async def create_app() -> FastAPI:
    """Create and return the FastAPI application"""
    return app

if __name__ == "__main__":
    # Development server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )