"""
🚀 Enterprise API Manager - Complete Backend Infrastructure
Provides comprehensive RESTful API with OpenAPI documentation, middleware, and enterprise features.
"""

import asyncio
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import structlog
import uvicorn

from ..config.unified_config_manager import UnifiedConfigurationManager
from ..security.enterprise_security_manager import EnterpriseSecurityManager
from ..ai.intelligent_model_manager import IntelligentModelManager
from ..workflow.advanced_workflow_engine import AdvancedWorkflowEngine

logger = structlog.get_logger(__name__)

# Pydantic Models for API
class APIResponse(BaseModel):
    """Standard API response format"""
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

class AIGenerationRequest(BaseModel):
    """AI generation request model"""
    prompt: str = Field(..., min_length=1, max_length=10000)
    model_preference: Optional[str] = None
    max_tokens: Optional[int] = Field(default=1000, ge=1, le=4000)
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    context: Optional[Dict[str, Any]] = None

class WorkflowRequest(BaseModel):
    """Workflow creation request model"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []

class UserRegistrationRequest(BaseModel):
    """User registration request model"""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    password: str = Field(..., min_length=8)
    roles: List[str] = Field(default=['viewer'])

class LoginRequest(BaseModel):
    """User login request model"""
    username: str
    password: str

# Middleware for request tracking
class RequestTrackingMiddleware:
    """Middleware for tracking API requests and performance"""
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.request_count = 0
        self.response_times = []
    
    async def __call__(self, request: Request, call_next):
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        # Add request ID to headers
        request.state.request_id = request_id
        
        # Log request
        logger.info(
            "API request started",
            method=request.method,
            url=str(request.url),
            request_id=request_id,
            client_ip=request.client.host if request.client else None
        )
        
        try:
            response = await call_next(request)
            
            # Calculate response time
            response_time = time.time() - start_time
            self.response_times.append(response_time)
            self.request_count += 1
            
            # Add performance headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{response_time:.3f}s"
            
            # Log response
            logger.info(
                "API request completed",
                method=request.method,
                url=str(request.url),
                status_code=response.status_code,
                response_time=response_time,
                request_id=request_id
            )
            
            return response
            
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(
                "API request failed",
                method=request.method,
                url=str(request.url),
                error=str(e),
                response_time=response_time,
                request_id=request_id
            )
            raise

class EnterpriseAPIManager:
    """
    🚀 Enterprise API Manager
    
    Provides comprehensive RESTful API with:
    - OpenAPI documentation
    - Authentication and authorization
    - Rate limiting and security
    - Performance monitoring
    - Error handling and recovery
    """
    
    def __init__(self, config_manager: UnifiedConfigurationManager):
        self.config = config_manager
        self.security_manager = None
        self.ai_manager = None
        self.workflow_engine = None
        self.app = None
        self.security = HTTPBearer()
        
        logger.info("🚀 Enterprise API Manager initializing...")
    
    async def initialize(self):
        """Initialize all components"""
        try:
            # Initialize managers
            self.security_manager = EnterpriseSecurityManager(self.config)
            await self.security_manager.initialize()
            
            self.ai_manager = IntelligentModelManager(self.config)
            await self.ai_manager.initialize()
            
            self.workflow_engine = AdvancedWorkflowEngine(self.config)
            await self.workflow_engine.initialize()
            
            # Create FastAPI app
            self.app = await self._create_app()
            
            logger.info("✅ Enterprise API Manager initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Enterprise API Manager: {e}")
            raise
    
    async def _create_app(self) -> FastAPI:
        """Create and configure FastAPI application"""
        
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Startup
            logger.info("🚀 API Server starting up...")
            yield
            # Shutdown
            logger.info("🛑 API Server shutting down...")
        
        app = FastAPI(
            title="reVoAgent Enterprise API",
            description="Revolutionary AI Development Platform with Cost Optimization",
            version="2.0.0",
            docs_url="/docs",
            redoc_url="/redoc",
            openapi_url="/openapi.json",
            lifespan=lifespan
        )
        
        # Add middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        app.add_middleware(GZipMiddleware, minimum_size=1000)
        
        # Add custom middleware
        request_middleware = RequestTrackingMiddleware(app)
        app.middleware("http")(request_middleware)
        
        # Add routes
        self._add_routes(app)
        
        return app
    
    def _add_routes(self, app: FastAPI):
        """Add all API routes"""
        
        # Health check endpoint
        @app.get("/health", response_model=APIResponse)
        async def health_check():
            """Health check endpoint"""
            return APIResponse(
                message="API is healthy",
                data={
                    "status": "healthy",
                    "timestamp": datetime.utcnow().isoformat(),
                    "version": "2.0.0"
                }
            )
        
        # Authentication endpoints
        @app.post("/auth/register", response_model=APIResponse)
        async def register_user(request: UserRegistrationRequest):
            """Register a new user"""
            try:
                user_id = await self.security_manager.create_user(
                    username=request.username,
                    email=request.email,
                    password=request.password,
                    roles=request.roles
                )
                
                return APIResponse(
                    message="User registered successfully",
                    data={"user_id": user_id, "username": request.username}
                )
                
            except Exception as e:
                logger.error(f"Registration failed: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )
        
        @app.post("/auth/login", response_model=APIResponse)
        async def login_user(request: LoginRequest):
            """Authenticate user and return JWT token"""
            try:
                auth_result = await self.security_manager.authenticate_user(
                    request.username, request.password
                )
                
                if not auth_result["success"]:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid credentials"
                    )
                
                token = await self.security_manager.create_jwt_token(
                    auth_result["user_id"]
                )
                
                return APIResponse(
                    message="Login successful",
                    data={
                        "token": token,
                        "user_id": auth_result["user_id"],
                        "username": request.username
                    }
                )
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Login failed: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Login failed"
                )
        
        # AI endpoints
        @app.post("/ai/generate", response_model=APIResponse)
        async def generate_ai_content(
            request: AIGenerationRequest,
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ):
            """Generate AI content with intelligent model selection"""
            try:
                # Verify token and permissions
                user_info = await self._verify_token_and_permissions(
                    credentials.credentials, ["ai:generate"]
                )
                
                # Generate content
                result = await self.ai_manager.generate(
                    prompt=request.prompt,
                    model_preference=request.model_preference,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                    context=request.context
                )
                
                return APIResponse(
                    message="Content generated successfully",
                    data={
                        "content": result["content"],
                        "provider": result["provider"],
                        "quality_score": result["quality_score"],
                        "cost": result["cost"],
                        "generation_time": result.get("generation_time", 0)
                    }
                )
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"AI generation failed: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="AI generation failed"
                )
        
        @app.get("/ai/models", response_model=APIResponse)
        async def get_available_models(
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ):
            """Get list of available AI models"""
            try:
                await self._verify_token_and_permissions(
                    credentials.credentials, ["ai:read"]
                )
                
                models = await self.ai_manager.get_available_providers()
                stats = await self.ai_manager.get_performance_stats()
                
                return APIResponse(
                    message="Models retrieved successfully",
                    data={
                        "models": models,
                        "stats": stats
                    }
                )
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Failed to get models: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to retrieve models"
                )
        
        # Workflow endpoints
        @app.post("/workflows", response_model=APIResponse)
        async def create_workflow(
            request: WorkflowRequest,
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ):
            """Create a new workflow"""
            try:
                user_info = await self._verify_token_and_permissions(
                    credentials.credentials, ["workflow:create"]
                )
                
                workflow_id = await self.workflow_engine.create_workflow(
                    name=request.name,
                    description=request.description
                )
                
                # Add nodes and edges if provided
                for node in request.nodes:
                    await self.workflow_engine.add_node(
                        workflow_id, **node
                    )
                
                for edge in request.edges:
                    await self.workflow_engine.connect_nodes(
                        workflow_id, edge["from"], edge["to"]
                    )
                
                return APIResponse(
                    message="Workflow created successfully",
                    data={
                        "workflow_id": workflow_id,
                        "name": request.name,
                        "nodes_count": len(request.nodes),
                        "edges_count": len(request.edges)
                    }
                )
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Workflow creation failed: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Workflow creation failed"
                )
        
        @app.get("/workflows", response_model=APIResponse)
        async def list_workflows(
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ):
            """List all workflows"""
            try:
                await self._verify_token_and_permissions(
                    credentials.credentials, ["workflow:read"]
                )
                
                workflows = await self.workflow_engine.list_workflows()
                metrics = await self.workflow_engine.get_metrics()
                
                return APIResponse(
                    message="Workflows retrieved successfully",
                    data={
                        "workflows": workflows,
                        "metrics": metrics
                    }
                )
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Failed to list workflows: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to retrieve workflows"
                )
        
        @app.post("/workflows/{workflow_id}/execute", response_model=APIResponse)
        async def execute_workflow(
            workflow_id: str,
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ):
            """Execute a workflow"""
            try:
                await self._verify_token_and_permissions(
                    credentials.credentials, ["workflow:execute"]
                )
                
                execution_id = await self.workflow_engine.execute_workflow(
                    workflow_id
                )
                
                return APIResponse(
                    message="Workflow execution started",
                    data={
                        "execution_id": execution_id,
                        "workflow_id": workflow_id,
                        "status": "running"
                    }
                )
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Workflow execution failed: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Workflow execution failed"
                )
        
        # System endpoints
        @app.get("/system/metrics", response_model=APIResponse)
        async def get_system_metrics(
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ):
            """Get system performance metrics"""
            try:
                await self._verify_token_and_permissions(
                    credentials.credentials, ["system:monitor"]
                )
                
                # Collect metrics from all components
                ai_stats = await self.ai_manager.get_performance_stats()
                security_metrics = await self.security_manager.get_security_metrics()
                workflow_metrics = await self.workflow_engine.get_metrics()
                
                return APIResponse(
                    message="System metrics retrieved successfully",
                    data={
                        "ai": ai_stats,
                        "security": security_metrics,
                        "workflows": workflow_metrics,
                        "api": {
                            "total_requests": getattr(request_middleware, 'request_count', 0),
                            "avg_response_time": sum(getattr(request_middleware, 'response_times', [0])) / max(len(getattr(request_middleware, 'response_times', [1])), 1)
                        }
                    }
                )
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Failed to get system metrics: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to retrieve system metrics"
                )
    
    async def _verify_token_and_permissions(
        self, token: str, required_permissions: List[str]
    ) -> Dict[str, Any]:
        """Verify JWT token and check permissions"""
        try:
            # Verify token
            token_data = await self.security_manager.verify_jwt_token(token)
            if not token_data["valid"]:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token"
                )
            
            user_id = token_data["user_id"]
            
            # Check permissions
            for permission in required_permissions:
                if not await self.security_manager.check_permission(user_id, permission):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Insufficient permissions: {permission}"
                    )
            
            return {"user_id": user_id}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed"
            )
    
    async def start_server(self, host: str = "0.0.0.0", port: int = 8000):
        """Start the API server"""
        if not self.app:
            await self.initialize()
        
        logger.info(f"🚀 Starting Enterprise API Server on {host}:{port}")
        
        config = uvicorn.Config(
            app=self.app,
            host=host,
            port=port,
            log_level="info",
            access_log=True
        )
        
        server = uvicorn.Server(config)
        await server.serve()
    
    def get_app(self) -> FastAPI:
        """Get the FastAPI application instance"""
        return self.app
    
    async def get_api_metrics(self) -> Dict[str, Any]:
        """Get comprehensive API metrics"""
        try:
            return {
                "status": "healthy",
                "uptime": time.time(),
                "endpoints": len(self.app.routes) if self.app else 0,
                "components": {
                    "security": self.security_manager is not None,
                    "ai": self.ai_manager is not None,
                    "workflow": self.workflow_engine is not None
                }
            }
        except Exception as e:
            logger.error(f"Failed to get API metrics: {e}")
            return {"status": "error", "error": str(e)}

# Example usage
async def main():
    """Example usage of Enterprise API Manager"""
    from ..config.unified_config_manager import UnifiedConfigurationManager
    
    # Initialize configuration
    config = UnifiedConfigurationManager()
    await config.initialize()
    
    # Create and start API manager
    api_manager = EnterpriseAPIManager(config)
    await api_manager.initialize()
    
    # Start server
    await api_manager.start_server()

if __name__ == "__main__":
    asyncio.run(main())