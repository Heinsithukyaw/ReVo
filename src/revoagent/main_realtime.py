#!/usr/bin/env python3
"""
🚀 reVoAgent Real-Time Application

Main FastAPI application with real-time WebSocket communication for the
Three-Engine Architecture, providing live monitoring and task execution.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from revoagent.engines.perfect_recall import PerfectRecallEngine
from revoagent.engines.parallel_mind.worker_manager import WorkerManager
from revoagent.engines.creative_engine import CreativeEngine
from revoagent.engines.engine_coordinator import EngineCoordinator
from revoagent.api.websocket_endpoints import (
    router as websocket_router,
    initialize_websocket_system,
    shutdown_websocket_system
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ReVoAgentRealTimeApp:
    """Main application class for reVoAgent with real-time capabilities"""
    
    def __init__(self):
        self.app = FastAPI(
            title="🎯 reVoAgent Three-Engine Architecture",
            description="Revolutionary AI-powered development platform with real-time monitoring",
            version="2.0.0",
            docs_url="/api/docs",
            redoc_url="/api/redoc"
        )
        
        self.engines: Dict[str, Any] = {}
        self.setup_middleware()
        self.setup_routes()
        
    def setup_middleware(self):
        """Setup FastAPI middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def setup_routes(self):
        """Setup API routes"""
        
        # Include WebSocket router
        self.app.include_router(websocket_router)
        
        @self.app.on_event("startup")
        async def startup_event():
            """Initialize engines and WebSocket system on startup"""
            await self.initialize_engines()
            await initialize_websocket_system(self.engines)
            logger.info("🚀 reVoAgent Real-Time Application started successfully")
        
        @self.app.on_event("shutdown")
        async def shutdown_event():
            """Cleanup on shutdown"""
            await shutdown_websocket_system()
            await self.shutdown_engines()
            logger.info("🛑 reVoAgent Real-Time Application shutdown complete")
        
        @self.app.get("/", response_class=HTMLResponse)
        async def root():
            """Serve main dashboard"""
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>🎯 reVoAgent Three-Engine Architecture</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body { 
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        margin: 0; padding: 40px; background: #0f172a; color: #e2e8f0;
                        line-height: 1.6;
                    }
                    .container { max-width: 1200px; margin: 0 auto; }
                    .header { text-align: center; margin-bottom: 60px; }
                    .title { font-size: 3rem; font-weight: bold; margin-bottom: 20px; 
                             background: linear-gradient(135deg, #3b82f6, #8b5cf6, #ec4899);
                             -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
                    .subtitle { font-size: 1.2rem; color: #94a3b8; margin-bottom: 40px; }
                    .features { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 30px; margin-bottom: 60px; }
                    .feature { background: #1e293b; padding: 30px; border-radius: 12px; border: 1px solid #334155; }
                    .feature-icon { font-size: 2rem; margin-bottom: 15px; }
                    .feature-title { font-size: 1.3rem; font-weight: 600; margin-bottom: 10px; }
                    .feature-desc { color: #94a3b8; }
                    .links { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
                    .link { display: block; background: #1e293b; padding: 20px; border-radius: 8px; 
                            text-decoration: none; color: #e2e8f0; border: 1px solid #334155;
                            transition: all 0.2s; }
                    .link:hover { border-color: #3b82f6; background: #1e40af20; }
                    .link-title { font-weight: 600; margin-bottom: 5px; }
                    .link-desc { color: #94a3b8; font-size: 0.9rem; }
                    .status { display: inline-flex; align-items: center; gap: 8px; 
                             background: #059669; color: white; padding: 6px 12px; 
                             border-radius: 20px; font-size: 0.9rem; font-weight: 500; }
                    .status-dot { width: 8px; height: 8px; background: #10b981; border-radius: 50%; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1 class="title">🎯 reVoAgent</h1>
                        <p class="subtitle">Revolutionary Three-Engine Architecture for AI-Powered Development</p>
                        <div class="status">
                            <div class="status-dot"></div>
                            Real-Time System Active
                        </div>
                    </div>
                    
                    <div class="features">
                        <div class="feature">
                            <div class="feature-icon">🔵</div>
                            <h3 class="feature-title">Perfect Recall Engine</h3>
                            <p class="feature-desc">Sub-100ms context retrieval with intelligent memory management and semantic search capabilities.</p>
                        </div>
                        <div class="feature">
                            <div class="feature-icon">🟣</div>
                            <h3 class="feature-title">Parallel Mind Engine</h3>
                            <p class="feature-desc">Auto-scaling worker management (4-16 workers) with intelligent task distribution and load balancing.</p>
                        </div>
                        <div class="feature">
                            <div class="feature-icon">🩷</div>
                            <h3 class="feature-title">Creative Engine</h3>
                            <p class="feature-desc">Generate 3-5 innovative solutions using multiple creativity techniques and adaptive learning.</p>
                        </div>
                        <div class="feature">
                            <div class="feature-icon">🔄</div>
                            <h3 class="feature-title">Engine Coordinator</h3>
                            <p class="feature-desc">Orchestrate complex workflows across engines with sequential, parallel, and adaptive strategies.</p>
                        </div>
                    </div>
                    
                    <div class="links">
                        <a href="/ws/dashboard" class="link">
                            <div class="link-title">📊 Live Dashboard</div>
                            <div class="link-desc">Real-time engine monitoring with WebSocket updates</div>
                        </a>
                        <a href="/api/docs" class="link">
                            <div class="link-title">📚 API Documentation</div>
                            <div class="link-desc">Interactive API documentation and testing</div>
                        </a>
                        <a href="/ws/status" class="link">
                            <div class="link-title">🔌 WebSocket Status</div>
                            <div class="link-desc">Real-time system status and connection info</div>
                        </a>
                        <a href="/ws/metrics" class="link">
                            <div class="link-title">📈 Performance Metrics</div>
                            <div class="link-desc">Live engine performance and health metrics</div>
                        </a>
                    </div>
                </div>
            </body>
            </html>
            """
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            engine_health = {}
            
            for engine_name, engine in self.engines.items():
                try:
                    if hasattr(engine, 'get_engine_status'):
                        status = await engine.get_engine_status()
                        engine_health[engine_name] = {
                            "status": "healthy",
                            "details": status
                        }
                    else:
                        engine_health[engine_name] = {"status": "healthy", "details": "no status method"}
                except Exception as e:
                    engine_health[engine_name] = {"status": "unhealthy", "error": str(e)}
            
            overall_healthy = all(
                engine["status"] == "healthy" 
                for engine in engine_health.values()
            )
            
            return {
                "status": "healthy" if overall_healthy else "degraded",
                "timestamp": asyncio.get_event_loop().time(),
                "engines": engine_health,
                "version": "2.0.0"
            }
        
        @self.app.get("/api/engines")
        async def list_engines():
            """List all available engines"""
            engine_info = {}
            
            for engine_name, engine in self.engines.items():
                try:
                    if hasattr(engine, 'get_engine_status'):
                        status = await engine.get_engine_status()
                    else:
                        status = {"status": "active", "message": "Engine running"}
                    
                    engine_info[engine_name] = {
                        "name": engine_name,
                        "type": engine.__class__.__name__,
                        "status": status,
                        "capabilities": self._get_engine_capabilities(engine_name)
                    }
                except Exception as e:
                    engine_info[engine_name] = {
                        "name": engine_name,
                        "type": engine.__class__.__name__,
                        "status": {"status": "error", "error": str(e)},
                        "capabilities": []
                    }
            
            return {
                "engines": engine_info,
                "total_engines": len(engine_info),
                "healthy_engines": len([e for e in engine_info.values() if e["status"].get("status") == "active"])
            }
        
        @self.app.post("/api/engines/{engine_name}/execute")
        async def execute_engine_task(engine_name: str, task_data: Dict[str, Any]):
            """Execute a task on a specific engine"""
            if engine_name not in self.engines:
                raise HTTPException(status_code=404, detail=f"Engine '{engine_name}' not found")
            
            engine = self.engines[engine_name]
            
            try:
                # Route to appropriate engine method based on task type
                result = await self._execute_engine_task(engine_name, engine, task_data)
                
                return {
                    "success": True,
                    "engine": engine_name,
                    "task_id": task_data.get("task_id", "unknown"),
                    "result": result
                }
                
            except Exception as e:
                logger.error(f"Error executing task on {engine_name}: {e}")
                raise HTTPException(status_code=500, detail=f"Task execution failed: {str(e)}")
    
    async def initialize_engines(self):
        """Initialize all engines"""
        logger.info("🔧 Initializing Three-Engine Architecture...")
        
        try:
            # Initialize Perfect Recall Engine
            self.engines['perfect_recall'] = PerfectRecallEngine({
                'redis_url': os.getenv('REDIS_URL', 'redis://localhost:6379')
            })
            await self.engines['perfect_recall'].initialize()
            logger.info("🔵 Perfect Recall Engine initialized")
            
            # Initialize Parallel Mind Engine
            self.engines['parallel_mind'] = WorkerManager(min_workers=4, max_workers=16)
            await self.engines['parallel_mind'].start()
            logger.info("🟣 Parallel Mind Engine initialized")
            
            # Initialize Creative Engine
            self.engines['creative'] = CreativeEngine({})
            await self.engines['creative'].initialize()
            logger.info("🩷 Creative Engine initialized")
            
            # Initialize Engine Coordinator
            self.engines['coordinator'] = EngineCoordinator({
                'perfect_recall': {'redis_url': os.getenv('REDIS_URL', 'redis://localhost:6379')},
                'parallel_mind': {'min_workers': 4, 'max_workers': 16},
                'creative': {}
            })
            await self.engines['coordinator'].initialize()
            logger.info("🔄 Engine Coordinator initialized")
            
            logger.info("✅ All engines initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Engine initialization failed: {e}")
            raise
    
    async def shutdown_engines(self):
        """Shutdown all engines"""
        logger.info("🛑 Shutting down engines...")
        
        for engine_name, engine in self.engines.items():
            try:
                if hasattr(engine, 'shutdown'):
                    await engine.shutdown()
                logger.info(f"✅ {engine_name} shutdown complete")
            except Exception as e:
                logger.error(f"❌ Error shutting down {engine_name}: {e}")
    
    def _get_engine_capabilities(self, engine_name: str) -> List[str]:
        """Get capabilities for an engine"""
        capabilities_map = {
            'perfect_recall': ['store_context', 'retrieve_context', 'memory_management'],
            'parallel_mind': ['parallel_processing', 'auto_scaling', 'task_distribution'],
            'creative': ['solution_generation', 'innovation_scoring', 'adaptive_learning'],
            'coordinator': ['multi_engine_workflows', 'strategy_coordination', 'result_synthesis']
        }
        return capabilities_map.get(engine_name, [])
    
    async def _execute_engine_task(self, engine_name: str, engine: Any, task_data: Dict[str, Any]) -> Any:
        """Execute a task on a specific engine"""
        task_type = task_data.get('task_type', 'unknown')
        inputs = task_data.get('inputs', {})
        
        if engine_name == 'perfect_recall':
            if task_type == 'store_context':
                return await engine.store_context(
                    content=inputs.get('content', ''),
                    context_type=inputs.get('context_type', 'general'),
                    session_id=inputs.get('session_id', 'default')
                )
            elif task_type == 'retrieve_context':
                from revoagent.engines.perfect_recall.engine import RecallRequest
                request = RecallRequest(
                    query=inputs.get('query', ''),
                    limit=inputs.get('limit', 10),
                    session_id=inputs.get('session_id')
                )
                return await engine.retrieve_fast(request)
        
        elif engine_name == 'parallel_mind':
            if task_type == 'parallel_analysis':
                # Submit analysis task
                task_id = await engine.submit_task(
                    self._analyze_code,
                    inputs.get('code', ''),
                    inputs.get('analysis_types', 'all')
                )
                return {"task_id": task_id, "status": "submitted"}
        
        elif engine_name == 'creative':
            if task_type == 'generate_solutions':
                from revoagent.engines.creative_engine.engine import CreativeRequest
                request = CreativeRequest(
                    problem_statement=inputs.get('problem', ''),
                    domain=inputs.get('domain', 'general'),
                    constraints=inputs.get('constraints', '').split('\n') if inputs.get('constraints') else [],
                    innovation_level=inputs.get('innovation_level', 0.7)
                )
                return await engine.generate_creative_solutions(request)
        
        elif engine_name == 'coordinator':
            if task_type == 'multi_engine_workflow':
                from revoagent.engines.engine_coordinator import CoordinatedRequest, TaskComplexity, EngineType
                
                # Map workflow type to engines
                engine_mapping = {
                    'debugging': [EngineType.PERFECT_RECALL, EngineType.PARALLEL_MIND],
                    'code_generation': [EngineType.CREATIVE, EngineType.PERFECT_RECALL],
                    'analysis': [EngineType.PARALLEL_MIND, EngineType.PERFECT_RECALL],
                    'optimization': [EngineType.CREATIVE, EngineType.PARALLEL_MIND]
                }
                
                workflow_type = inputs.get('workflow_type', 'debugging')
                required_engines = engine_mapping.get(workflow_type, [EngineType.PERFECT_RECALL])
                
                request = CoordinatedRequest(
                    task_id=task_data.get('task_id', f"coord_{int(asyncio.get_event_loop().time())}"),
                    task_type=workflow_type,
                    description=f"Coordinated {workflow_type} workflow",
                    input_data={'query': inputs.get('input_data', '')},
                    complexity=TaskComplexity.MODERATE,
                    required_engines=required_engines,
                    coordination_strategy=inputs.get('coordination_strategy', 'adaptive')
                )
                
                return await engine.execute_coordinated_task(request)
        
        return {"message": f"Task type '{task_type}' not implemented for engine '{engine_name}'"}
    
    def _analyze_code(self, code: str, analysis_types: str) -> Dict[str, Any]:
        """Simple code analysis function for parallel processing"""
        import ast
        import time
        
        start_time = time.time()
        results = {
            "analysis_types": analysis_types,
            "code_length": len(code),
            "line_count": len(code.split('\n'))
        }
        
        try:
            tree = ast.parse(code)
            results["syntax_valid"] = True
            results["functions"] = len([node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)])
            results["classes"] = len([node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)])
        except SyntaxError as e:
            results["syntax_valid"] = False
            results["syntax_error"] = str(e)
        
        results["analysis_time"] = time.time() - start_time
        return results

def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    app_instance = ReVoAgentRealTimeApp()
    return app_instance.app

# Create the app instance
app = create_app()

async def main():
    """Main entry point for running the application"""
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True,
        reload=False  # Set to True for development
    )
    
    server = uvicorn.Server(config)
    
    try:
        logger.info("🚀 Starting reVoAgent Real-Time Application...")
        await server.serve()
    except KeyboardInterrupt:
        logger.info("🛑 Application stopped by user")
    except Exception as e:
        logger.error(f"❌ Application error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())