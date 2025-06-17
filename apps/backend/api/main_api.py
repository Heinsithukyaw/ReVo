#!/usr/bin/env python3
"""
Refactored Main API for reVoAgent Backend
Clean, production-ready FastAPI application with proper service separation
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

# Import refactored services
from apps.backend.services.ai_service import ProductionAIService, create_production_ai_service
from apps.backend.services.ai_team_coordinator import AITeamCoordinator
from apps.backend.services.cost_optimizer import CostOptimizedRouter
from apps.backend.services.quality_gates import QualityGates
from apps.backend.services.monitoring_dashboard import AITeamMonitoring

# Import API routes
from .routes.ai_routes import router as ai_router
from .routes.team_routes import router as team_router
from .routes.monitoring_routes import router as monitoring_router
from .routes.health_routes import router as health_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RefactoredBackendApp:
    """
    Refactored Backend Application
    
    Clean separation of concerns:
    - AI Service: Model management and generation
    - Team Coordinator: 100-agent coordination
    - Cost Optimizer: 95% cost savings
    - Quality Gates: Multi-layer validation
    - Monitoring: Real-time performance tracking
    """
    
    def __init__(self):
        """Initialize the refactored backend"""
        self.app = FastAPI(
            title="reVoAgent Enterprise AI Platform",
            description="World's First Three-Engine AI Architecture with 100-Agent Coordination",
            version="2.0.0",
            docs_url="/api/docs",
            redoc_url="/api/redoc"
        )
        
        # Service instances
        self.ai_service: Optional[ProductionAIService] = None
        self.team_coordinator: Optional[AITeamCoordinator] = None
        self.cost_optimizer: Optional[CostOptimizedRouter] = None
        self.quality_gates: Optional[QualityGates] = None
        self.monitoring: Optional[AITeamMonitoring] = None
        
        # Setup middleware and routes
        self._setup_middleware()
        self._setup_routes()
        self._setup_event_handlers()
        
        logger.info("🚀 Refactored Backend Application initialized")
    
    def _setup_middleware(self):
        """Setup FastAPI middleware"""
        
        # CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Custom middleware for request logging
        @self.app.middleware("http")
        async def log_requests(request, call_next):
            start_time = asyncio.get_event_loop().time()
            response = await call_next(request)
            process_time = asyncio.get_event_loop().time() - start_time
            
            logger.info(f"📡 {request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
            return response
    
    def _setup_routes(self):
        """Setup API routes"""
        
        # Include route modules
        self.app.include_router(health_router, prefix="/api/health", tags=["Health"])
        self.app.include_router(ai_router, prefix="/api/ai", tags=["AI Services"])
        self.app.include_router(team_router, prefix="/api/team", tags=["Team Coordination"])
        self.app.include_router(monitoring_router, prefix="/api/monitoring", tags=["Monitoring"])
        
        # Root endpoint
        @self.app.get("/")
        async def root():
            return {
                "message": "reVoAgent Enterprise AI Platform",
                "version": "2.0.0",
                "status": "operational",
                "architecture": "three-engine",
                "agents": "100-agent-coordination",
                "cost_optimization": "95-percent-savings"
            }
        
        # API info endpoint
        @self.app.get("/api")
        async def api_info():
            return {
                "api_version": "2.0.0",
                "endpoints": {
                    "health": "/api/health",
                    "ai": "/api/ai",
                    "team": "/api/team",
                    "monitoring": "/api/monitoring"
                },
                "documentation": {
                    "swagger": "/api/docs",
                    "redoc": "/api/redoc"
                }
            }
    
    def _setup_event_handlers(self):
        """Setup application event handlers"""
        
        @self.app.on_event("startup")
        async def startup_event():
            """Initialize services on startup"""
            try:
                logger.info("🚀 Starting reVoAgent Backend Services...")
                
                # Initialize AI Service
                logger.info("🤖 Initializing AI Service...")
                self.ai_service = await create_production_ai_service()
                
                # Initialize Cost Optimizer
                logger.info("💰 Initializing Cost Optimizer...")
                self.cost_optimizer = CostOptimizedRouter()
                
                # Initialize Quality Gates
                logger.info("🛡️ Initializing Quality Gates...")
                self.quality_gates = QualityGates()
                
                # Initialize Team Coordinator
                logger.info("👥 Initializing Team Coordinator...")
                self.team_coordinator = AITeamCoordinator(self.ai_service)
                await self.team_coordinator.start_coordination()
                
                # Initialize Monitoring
                logger.info("📊 Initializing Monitoring Dashboard...")
                self.monitoring = AITeamMonitoring(
                    self.ai_service,
                    self.team_coordinator,
                    self.cost_optimizer
                )
                await self.monitoring.start_monitoring()
                
                # Store services in app state for dependency injection
                self.app.state.ai_service = self.ai_service
                self.app.state.team_coordinator = self.team_coordinator
                self.app.state.cost_optimizer = self.cost_optimizer
                self.app.state.quality_gates = self.quality_gates
                self.app.state.monitoring = self.monitoring
                
                logger.info("✅ All services initialized successfully!")
                logger.info("🎯 Backend ready for 100-agent coordination with 95% cost savings")
                
            except Exception as e:
                logger.error(f"❌ Failed to initialize services: {e}")
                raise
        
        @self.app.on_event("shutdown")
        async def shutdown_event():
            """Cleanup services on shutdown"""
            try:
                logger.info("🛑 Shutting down reVoAgent Backend Services...")
                
                # Shutdown services in reverse order
                if self.monitoring:
                    await self.monitoring.shutdown()
                
                if self.team_coordinator:
                    await self.team_coordinator.shutdown()
                
                if self.ai_service:
                    await self.ai_service.shutdown()
                
                logger.info("✅ All services shut down gracefully")
                
            except Exception as e:
                logger.error(f"❌ Error during shutdown: {e}")
    
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

# Factory function for creating the application
async def create_refactored_app() -> FastAPI:
    """Create and configure the refactored backend application"""
    
    backend_app = RefactoredBackendApp()
    app = backend_app.get_app()
    
    logger.info("🏗️ Refactored Backend Application created")
    return app

# Development server function
async def run_development_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the development server"""
    
    app = await create_refactored_app()
    
    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="info",
        reload=False,  # Disable reload for production-like behavior
        access_log=True
    )
    
    server = uvicorn.Server(config)
    
    logger.info(f"🚀 Starting development server on {host}:{port}")
    logger.info(f"📖 API Documentation: http://{host}:{port}/api/docs")
    logger.info(f"🔍 Health Check: http://{host}:{port}/api/health")
    
    await server.serve()

if __name__ == "__main__":
    # Run the development server
    asyncio.run(run_development_server())