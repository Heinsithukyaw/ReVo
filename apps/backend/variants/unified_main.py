"""
reVoAgent Unified Backend Service
Consolidates all backend implementations into a single, robust service
with clear selection strategy and graceful degradation
"""

import sys
import os
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from contextlib import asynccontextmanager

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# Import our new services
try:
    from services.websocket_service import (
        websocket_service, connect_websocket, disconnect_websocket, 
        handle_websocket_message, MessageType, send_to_user, send_to_room
    )
    from services.memory_service import (
        memory_service, initialize_memory_service, store_memory, 
        retrieve_memory, search_memory, MemoryType
    )
    SERVICES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Advanced services not available: {e}")
    SERVICES_AVAILABLE = False

# Import core components (with fallback for missing modules)
try:
    from .engine_api import router as engine_router, initialize_engines, get_engine_coordinator
except ImportError:
    print("Warning: Engine API not available, using fallback")
    engine_router = None
    initialize_engines = None
    get_engine_coordinator = None

try:
    from .memory_api import (
        get_memory_routers, initialize_memory_system, 
        memory_manager, get_memory_manager
    )
except ImportError:
    print("Warning: Memory API not available, using fallback")
    get_memory_routers = lambda: []
    initialize_memory_system = None
    memory_manager = None
    get_memory_manager = lambda: None

# Import services (with fallback)
try:
    from .services.ai_service import AIService
    from .services.ai_team_coordinator import AITeamCoordinator
    from .services.circuit_breaker_service import CircuitBreakerService
    from .services.cost_optimizer import CostOptimizer
    from .services.monitoring_dashboard import MonitoringDashboard
    from .services.quality_gates import QualityGates
except ImportError:
    print("Warning: Advanced services not available, using fallback")
    AIService = None
    AITeamCoordinator = None
    CircuitBreakerService = None
    CostOptimizer = None
    MonitoringDashboard = None
    QualityGates = None

# Import middleware (with fallback)
try:
    from .middleware.security_middleware import SecurityMiddleware
except ImportError:
    print("Warning: Security middleware not available, using fallback")
    SecurityMiddleware = None

# Import real agent implementations (with fallback)
try:
    from packages.agents.code_generator import CodeGeneratorAgent
    from packages.agents.debugging_agent import DebuggingAgent
    from packages.agents.testing_agent import TestingAgent
    from packages.agents.documentation_agent import DocumentationAgent
    from packages.agents.deploy_agent import DeployAgent
    from packages.agents.browser_agent import BrowserAgent
    from packages.agents.security_agent import SecurityAgent
    from packages.agents.performance_optimizer_agent import PerformanceOptimizerAgent
    from packages.agents.architecture_advisor_agent import ArchitectureAdvisorAgent
    from packages.core.config import AgentConfig
    from packages.core.memory import MemoryManager
except ImportError as e:
    print(f"Warning: Agent implementations not available: {e}")
    # Create mock agent classes
    class MockAgent:
        def __init__(self, config, memory_manager, model_manager, tool_manager, agent_id=None):
            self.config = config
            self.agent_id = agent_id or "mock_agent"
        
        def get_capabilities(self):
            return "Mock agent capabilities"
        
        async def execute_task(self, task_description, parameters):
            return {
                "status": "completed",
                "result": f"Mock execution of: {task_description}",
                "agent_id": self.agent_id
            }
    
    # Use mock agents as fallback
    CodeGeneratorAgent = MockAgent
    DebuggingAgent = MockAgent
    TestingAgent = MockAgent
    DocumentationAgent = MockAgent
    DeployAgent = MockAgent
    BrowserAgent = MockAgent
    SecurityAgent = MockAgent
    PerformanceOptimizerAgent = MockAgent
    ArchitectureAdvisorAgent = MockAgent
    
    # Mock config and memory classes
    class AgentConfig:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    class MemoryManager:
        pass

# Configuration and environment
import yaml
from pydantic import BaseModel
from datetime import datetime
import uuid
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ServiceConfig(BaseModel):
    """Service configuration model"""
    environment: str = "development"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 12001
    reload: bool = True
    
    # Feature flags
    enable_memory: bool = True
    enable_engines: bool = True
    enable_agents: bool = True
    enable_monitoring: bool = True
    enable_security: bool = True
    
    # Fallback options
    fallback_to_mock: bool = True
    graceful_degradation: bool = True
    
    # Performance settings
    max_concurrent_requests: int = 100
    request_timeout: int = 300
    
    # Memory settings
    memory_provider: str = "lancedb"
    memory_fallback: str = "in-memory"
    
    # Engine settings
    engine_provider: str = "local"
    engine_fallback: str = "mock"

class UnifiedBackendService:
    """Unified backend service with graceful degradation and fallback mechanisms"""
    
    def __init__(self, config: ServiceConfig):
        self.config = config
        self.app = FastAPI(
            title="reVoAgent - Unified Backend Service",
            version="3.0.0",
            description="Revolutionary Three-Engine Foundation with 20+ Memory-Enabled Agents",
            docs_url="/docs" if config.debug else None,
            redoc_url="/redoc" if config.debug else None
        )
        
        # Service components
        self.ai_service: Optional[AIService] = None
        self.team_coordinator: Optional[AITeamCoordinator] = None
        self.circuit_breaker: Optional[CircuitBreakerService] = None
        self.cost_optimizer: Optional[CostOptimizer] = None
        self.monitoring: Optional[MonitoringDashboard] = None
        self.quality_gates: Optional[QualityGates] = None
        
        # Agent registry
        self.agents: Dict[str, Any] = {}
        
        # Service status
        self.service_status = {
            "memory": "initializing",
            "engines": "initializing", 
            "agents": "initializing",
            "monitoring": "initializing",
            "security": "initializing"
        }
        
        # Initialize app
        self._setup_middleware()
        self._setup_routes()
    
    def _setup_middleware(self):
        """Setup middleware with security and CORS"""
        
        # CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Security middleware
        if self.config.enable_security and SecurityMiddleware:
            try:
                security_middleware = SecurityMiddleware()
                self.app.middleware("http")(security_middleware.process_request)
                logger.info("✅ Security middleware enabled")
            except Exception as e:
                logger.warning(f"⚠️ Security middleware failed to load: {e}")
                if not self.config.graceful_degradation:
                    raise
        elif self.config.enable_security:
            logger.warning("⚠️ Security middleware not available, continuing without it")
    
    def _setup_routes(self):
        """Setup all routes and endpoints"""
        
        # Health check endpoint
        @self.app.get("/health")
        async def health_check():
            health_data = {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "services": self.service_status,
                "version": "3.0.0"
            }
            
            # Add unified services status
            if SERVICES_AVAILABLE:
                health_data["unified_services"] = {
                    "websocket": websocket_service.get_stats(),
                    "memory": memory_service.get_stats()
                }
            
            return health_data
        
        # Service status endpoint
        @self.app.get("/status")
        async def service_status():
            return {
                "backend": "running",
                "services": self.service_status,
                "config": {
                    "environment": self.config.environment,
                    "debug": self.config.debug,
                    "features": {
                        "memory": self.config.enable_memory,
                        "engines": self.config.enable_engines,
                        "agents": self.config.enable_agents,
                        "monitoring": self.config.enable_monitoring,
                        "security": self.config.enable_security
                    }
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # WebSocket endpoint for real-time communication
        @self.app.websocket("/ws/dashboard")
        async def websocket_endpoint(websocket: WebSocket):
            await self._handle_websocket(websocket)
    
    async def _handle_websocket(self, websocket: WebSocket):
        """Handle WebSocket connections with room support"""
        await websocket.accept()
        client_id = str(uuid.uuid4())
        
        try:
            logger.info(f"WebSocket client {client_id} connected")
            
            # Send initial status
            await websocket.send_json({
                "type": "connection_established",
                "client_id": client_id,
                "timestamp": datetime.utcnow().isoformat(),
                "services": self.service_status
            })
            
            # Handle messages
            while True:
                try:
                    data = await websocket.receive_json()
                    await self._process_websocket_message(websocket, client_id, data)
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"WebSocket error for client {client_id}: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    })
        
        except WebSocketDisconnect:
            logger.info(f"WebSocket client {client_id} disconnected")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            logger.info(f"WebSocket connection closed for client {client_id}")
    
    async def _process_websocket_message(self, websocket: WebSocket, client_id: str, data: dict):
        """Process incoming WebSocket messages"""
        message_type = data.get("type")
        
        if message_type == "ping":
            await websocket.send_json({
                "type": "pong",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        elif message_type == "get_status":
            await websocket.send_json({
                "type": "status_update",
                "services": self.service_status,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        elif message_type == "agent_request":
            await self._handle_agent_request(websocket, client_id, data)
        
        else:
            logger.warning(f"Unknown message type: {message_type}")
    
    async def _handle_agent_request(self, websocket: WebSocket, client_id: str, data: dict):
        """Handle agent execution requests via WebSocket"""
        try:
            agent_type = data.get("agent_type")
            task_description = data.get("task_description", "")
            parameters = data.get("parameters", {})
            
            if agent_type not in self.agents:
                await websocket.send_json({
                    "type": "agent_error",
                    "error": f"Agent type '{agent_type}' not found",
                    "timestamp": datetime.utcnow().isoformat()
                })
                return
            
            # Execute agent task
            agent = self.agents[agent_type]
            result = await agent.execute_task(task_description, parameters)
            
            await websocket.send_json({
                "type": "agent_result",
                "agent_type": agent_type,
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Agent request error: {e}")
            await websocket.send_json({
                "type": "agent_error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def initialize_services(self):
        """Initialize all services with graceful degradation"""
        logger.info("🚀 Initializing reVoAgent Unified Backend Services...")
        
        # Initialize memory system
        if self.config.enable_memory:
            await self._initialize_memory()
        
        # Initialize three engines
        if self.config.enable_engines:
            await self._initialize_engines()
        
        # Initialize agents
        if self.config.enable_agents:
            await self._initialize_agents()
        
        # Initialize monitoring
        if self.config.enable_monitoring:
            await self._initialize_monitoring()
        
        # Initialize new unified services
        if SERVICES_AVAILABLE:
            await self._initialize_unified_services()
        
        # Register routers
        await self._register_routers()
        
        logger.info("✅ All services initialized successfully")
    
    async def _initialize_memory(self):
        """Initialize memory system with fallback"""
        try:
            logger.info("Initializing memory system...")
            
            if initialize_memory_system:
                memory_config = {
                    "memory_config": {
                        "enable_memory": True,
                        "vector_db_provider": self.config.memory_provider,
                        "graph_db_provider": "networkx",
                        "memory_data_path": "./data/cognee_memory"
                    }
                }
                
                await initialize_memory_system(memory_config)
                self.service_status["memory"] = "active"
                logger.info("✅ Memory system initialized successfully")
            else:
                logger.warning("⚠️ Memory system not available, using fallback")
                self.service_status["memory"] = "fallback"
            
        except Exception as e:
            logger.error(f"❌ Memory system initialization failed: {e}")
            
            if self.config.graceful_degradation:
                logger.warning("⚠️ Falling back to in-memory storage")
                self.service_status["memory"] = "fallback"
            else:
                self.service_status["memory"] = "failed"
                raise
    
    async def _initialize_engines(self):
        """Initialize three engines with fallback"""
        try:
            logger.info("Initializing three-engine architecture...")
            
            if initialize_engines:
                await initialize_engines()
                self.service_status["engines"] = "active"
                logger.info("✅ Three-engine architecture initialized successfully")
            else:
                logger.warning("⚠️ Engine system not available, using fallback")
                self.service_status["engines"] = "fallback"
            
        except Exception as e:
            logger.error(f"❌ Engine initialization failed: {e}")
            
            if self.config.graceful_degradation:
                logger.warning("⚠️ Falling back to mock engines")
                self.service_status["engines"] = "fallback"
            else:
                self.service_status["engines"] = "failed"
                raise
    
    async def _initialize_agents(self):
        """Initialize all agents with fallback"""
        try:
            logger.info("Initializing specialized agents...")
            
            # Mock managers for fallback (create inline if not available)
            try:
                from .main import MockModelManager, MockToolManager
            except ImportError:
                # Create mock managers inline
                class MockModelManager:
                    async def generate_response(self, prompt: str, model_name: str = None, **kwargs):
                        return f"Mock response for: {prompt[:50]}..."
                
                class MockToolManager:
                    async def execute_tool(self, tool_name: str, parameters: dict = None, **kwargs):
                        return f"Mock execution of {tool_name} with {parameters}"
            
            model_manager = MockModelManager()
            tool_manager = MockToolManager()
            memory_manager = get_memory_manager() if self.service_status["memory"] == "active" else None
            
            # Agent configurations
            agent_configs = {
                "code_generator": {"name": "Code Generator", "capabilities": "code generation"},
                "debugging": {"name": "Debug Agent", "capabilities": "debugging and error analysis"},
                "testing": {"name": "Testing Agent", "capabilities": "test generation and execution"},
                "documentation": {"name": "Documentation Agent", "capabilities": "documentation generation"},
                "deploy": {"name": "Deploy Agent", "capabilities": "deployment automation"},
                "browser": {"name": "Browser Agent", "capabilities": "web automation"},
                "security": {"name": "Security Agent", "capabilities": "security analysis"},
                "performance": {"name": "Performance Agent", "capabilities": "performance optimization"},
                "architecture": {"name": "Architecture Agent", "capabilities": "architecture advice"}
            }
            
            # Initialize agents
            for agent_type, config in agent_configs.items():
                try:
                    agent_config = AgentConfig(**config)
                    
                    if agent_type == "code_generator":
                        agent = CodeGeneratorAgent(agent_config, memory_manager, model_manager, tool_manager)
                    elif agent_type == "debugging":
                        agent = DebuggingAgent(agent_config, memory_manager, model_manager, tool_manager)
                    elif agent_type == "testing":
                        agent = TestingAgent(agent_config, memory_manager, model_manager, tool_manager)
                    elif agent_type == "documentation":
                        agent = DocumentationAgent(agent_config, memory_manager, model_manager, tool_manager)
                    elif agent_type == "deploy":
                        agent = DeployAgent(agent_config, memory_manager, model_manager, tool_manager)
                    elif agent_type == "browser":
                        agent = BrowserAgent(agent_config, memory_manager, model_manager, tool_manager)
                    elif agent_type == "security":
                        agent = SecurityAgent(agent_config, memory_manager, model_manager, tool_manager)
                    elif agent_type == "performance":
                        agent = PerformanceOptimizerAgent(agent_config, memory_manager, model_manager, tool_manager)
                    elif agent_type == "architecture":
                        agent = ArchitectureAdvisorAgent(agent_config, memory_manager, model_manager, tool_manager)
                    else:
                        continue
                    
                    self.agents[agent_type] = agent
                    logger.info(f"✅ {config['name']} initialized")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Failed to initialize {config['name']}: {e}")
                    if not self.config.graceful_degradation:
                        raise
            
            self.service_status["agents"] = "active" if self.agents else "fallback"
            logger.info(f"✅ Initialized {len(self.agents)} agents successfully")
            
        except Exception as e:
            logger.error(f"❌ Agent initialization failed: {e}")
            self.service_status["agents"] = "failed"
            if not self.config.graceful_degradation:
                raise
    
    async def _initialize_monitoring(self):
        """Initialize monitoring services"""
        try:
            logger.info("Initializing monitoring services...")
            
            # Initialize monitoring components if available
            if MonitoringDashboard:
                self.monitoring = MonitoringDashboard()
            if CircuitBreakerService:
                self.circuit_breaker = CircuitBreakerService()
            if CostOptimizer:
                self.cost_optimizer = CostOptimizer()
            if QualityGates:
                self.quality_gates = QualityGates()
            
            self.service_status["monitoring"] = "active" if any([
                MonitoringDashboard, CircuitBreakerService, CostOptimizer, QualityGates
            ]) else "fallback"
            
            logger.info("✅ Monitoring services initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Monitoring initialization failed: {e}")
            self.service_status["monitoring"] = "fallback"
            if not self.config.graceful_degradation:
                raise
    
    async def _initialize_unified_services(self):
        """Initialize unified WebSocket and Memory services"""
        try:
            logger.info("Initializing unified services...")
            
            # Initialize memory service
            memory_config = {
                "sqlite": {"db_path": "data/memory.db"},
                "in_memory": {"max_entries": 10000}
            }
            await initialize_memory_service(memory_config)
            logger.info("✅ Unified memory service initialized")
            
            # WebSocket service is initialized automatically
            logger.info("✅ Unified WebSocket service initialized")
            
        except Exception as e:
            logger.error(f"❌ Unified services initialization failed: {e}")
            if not self.config.graceful_degradation:
                raise
    
    async def _register_routers(self):
        """Register all API routers"""
        try:
            # Include engine router if engines are active and available
            if self.service_status["engines"] in ["active", "fallback"] and engine_router:
                self.app.include_router(engine_router, prefix="/api/engines", tags=["engines"])
                logger.info("✅ Engine API routes registered")
            
            # Include memory routers if memory is active and available
            if self.service_status["memory"] in ["active", "fallback"] and get_memory_routers:
                for router in get_memory_routers():
                    self.app.include_router(router, prefix="/api/memory", tags=["memory"])
                logger.info("✅ Memory API routes registered")
            
            # Add agent endpoints
            if self.service_status["agents"] in ["active", "fallback"]:
                self._register_agent_routes()
                logger.info("✅ Agent API routes registered")
            
            # Add WebSocket and memory endpoints
            if SERVICES_AVAILABLE:
                self._register_websocket_routes()
                self._register_memory_routes()
                logger.info("✅ WebSocket and Memory API routes registered")
            
        except Exception as e:
            logger.error(f"❌ Router registration failed: {e}")
            if not self.config.graceful_degradation:
                raise
    
    def _register_websocket_routes(self):
        """Register WebSocket routes"""
        
        @self.app.websocket("/ws/{user_id}")
        async def websocket_endpoint(websocket: WebSocket, user_id: str):
            """Main WebSocket endpoint"""
            connection_id = None
            try:
                connection_id = await connect_websocket(websocket, user_id)
                
                while True:
                    data = await websocket.receive_text()
                    await handle_websocket_message(connection_id, data)
                    
            except WebSocketDisconnect:
                if connection_id:
                    await disconnect_websocket(connection_id)
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                if connection_id:
                    await disconnect_websocket(connection_id)
        
        @self.app.get("/api/websocket/stats")
        async def get_websocket_stats():
            """Get WebSocket service statistics"""
            return websocket_service.get_stats()
    
    def _register_memory_routes(self):
        """Register memory API routes"""
        
        @self.app.post("/api/memory/store")
        async def store_memory_entry(request_data: dict):
            """Store a memory entry"""
            try:
                memory_type_enum = MemoryType(request_data["memory_type"])
                entry_id = await store_memory(
                    memory_type_enum, 
                    request_data["content"], 
                    request_data.get("metadata"),
                    request_data.get("user_id"),
                    request_data.get("session_id"),
                    request_data.get("agent_id")
                )
                return {"entry_id": entry_id, "status": "stored"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/memory/{entry_id}")
        async def get_memory_entry(entry_id: str):
            """Retrieve a memory entry"""
            entry = await retrieve_memory(entry_id)
            if entry:
                return entry.to_dict()
            raise HTTPException(status_code=404, detail="Memory entry not found")
        
        @self.app.get("/api/memory/search/")
        async def search_memory_entries(
            query: str,
            memory_type: str = None,
            limit: int = 10
        ):
            """Search memory entries"""
            memory_type_enum = MemoryType(memory_type) if memory_type else None
            results = await search_memory(query, memory_type_enum, limit)
            return {
                "results": [entry.to_dict() for entry in results],
                "count": len(results)
            }
        
        @self.app.get("/api/memory/service/stats")
        async def get_memory_stats():
            """Get memory service statistics"""
            return memory_service.get_stats()

    def _register_agent_routes(self):
        """Register agent-specific routes"""
        
        @self.app.get("/api/agents")
        async def list_agents():
            """List all available agents"""
            return {
                "agents": [
                    {
                        "id": agent_id,
                        "name": agent.config.name if hasattr(agent, 'config') else agent_id,
                        "capabilities": agent.get_capabilities() if hasattr(agent, 'get_capabilities') else "Unknown",
                        "status": "active"
                    }
                    for agent_id, agent in self.agents.items()
                ],
                "total": len(self.agents),
                "timestamp": datetime.utcnow().isoformat()
            }
        
        @self.app.post("/api/agents/{agent_id}/execute")
        async def execute_agent_task(agent_id: str, task_data: dict):
            """Execute a task with a specific agent"""
            if agent_id not in self.agents:
                raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
            
            try:
                agent = self.agents[agent_id]
                task_description = task_data.get("task_description", "")
                parameters = task_data.get("parameters", {})
                
                result = await agent.execute_task(task_description, parameters)
                
                return {
                    "agent_id": agent_id,
                    "task_description": task_description,
                    "result": result,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Agent execution error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

def load_config() -> ServiceConfig:
    """Load configuration from file or environment"""
    config_path = os.getenv("REVOAGENT_CONFIG", "config/environments/development.yaml")
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Extract server config
            server_config = config_data.get("server", {})
            
            return ServiceConfig(
                environment=config_data.get("environment", "development"),
                debug=config_data.get("debug", True),
                host=server_config.get("host", "0.0.0.0"),
                port=server_config.get("port", 12001),
                reload=server_config.get("reload", True),
                enable_memory=config_data.get("memory", {}).get("enable_memory", True),
                enable_engines=config_data.get("engines", {}).get("perfect_recall", {}).get("enabled", True),
                enable_agents=config_data.get("agents", {}).get("max_concurrent", 0) > 0,
                enable_monitoring=True,
                enable_security=True
            )
        except Exception as e:
            logger.warning(f"Failed to load config from {config_path}: {e}")
    
    # Default configuration
    return ServiceConfig()

# Create global service instance
config = load_config()
service = UnifiedBackendService(config)

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await service.initialize_services()
    yield
    # Shutdown
    logger.info("🛑 Shutting down reVoAgent Unified Backend...")

# Update app with lifespan
service.app.router.lifespan_context = lifespan

# Export the app
app = service.app

if __name__ == "__main__":
    logger.info(f"🚀 Starting reVoAgent Unified Backend on {config.host}:{config.port}")
    
    uvicorn.run(
        "unified_main:app",
        host=config.host,
        port=config.port,
        reload=config.reload,
        log_level="info" if config.debug else "warning"
    )