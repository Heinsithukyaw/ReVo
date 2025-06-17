"""
Enhanced reVoAgent Backend with Phase 1 Critical Hotspot Improvements
Includes: Circuit Breakers, Health Checks, Performance Monitoring, Caching, Rate Limiting
"""

import asyncio
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv
import redis
try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
except ImportError:
    # Fallback if prometheus_client is not available
    class MockMetric:
        def labels(self, **kwargs): return self
        def inc(self): pass
        def set(self, value): pass
    
    Counter = Histogram = Gauge = lambda *args, **kwargs: MockMetric()
    generate_latest = lambda: "# Prometheus metrics not available"
    CONTENT_TYPE_LATEST = "text/plain"

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import our middleware and utilities
try:
    from middleware.circuit_breaker import (
        CircuitBreakerConfig, 
        get_circuit_breaker, 
        circuit_breaker,
        get_all_circuit_breaker_stats
    )
    from middleware.health_checks import health_checker
    from middleware.performance import (
        performance_monitor,
        cache_manager,
        rate_limiter,
        performance_middleware,
        cache_response,
        rate_limit,
        compress_response
    )
except ImportError as e:
    logger.warning(f"Could not import middleware: {e}")
    # Create mock implementations
    class MockCircuitBreaker:
        def __init__(self, *args, **kwargs): pass
        async def call(self, func, *args, **kwargs): 
            return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
        def get_stats(self): return {}
    
    class MockHealthChecker:
        async def comprehensive_health_check(self): 
            return {"status": "unknown", "services": {}, "summary": {}}
    
    class MockPerformanceMonitor:
        def record_request(self, *args, **kwargs): pass
        def get_metrics(self): return {}
    
    CircuitBreakerConfig = lambda *args, **kwargs: None
    get_circuit_breaker = lambda *args, **kwargs: MockCircuitBreaker()
    get_all_circuit_breaker_stats = lambda: {}
    health_checker = MockHealthChecker()
    performance_monitor = MockPerformanceMonitor()
    
    # Mock decorators
    def cache_response(*args, **kwargs):
        def decorator(func): return func
        return decorator
    
    def rate_limit(*args, **kwargs):
        def decorator(func): return func
        return decorator
    
    def compress_response(*args, **kwargs):
        def decorator(func): return func
        return decorator
    
    async def performance_middleware(request, call_next):
        return await call_next(request)

# Import enhanced model manager
try:
    from packages.ai.enhanced_local_model_manager import (
        EnhancedLocalModelManager, 
        GenerationRequest, 
        ModelProvider
    )
except ImportError:
    logger.warning("Could not import enhanced model manager, using fallback")
    EnhancedLocalModelManager = None

# Prometheus metrics
REQUEST_COUNT = Counter('revoagent_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('revoagent_request_duration_seconds', 'Request duration', ['method', 'endpoint'])
ACTIVE_CONNECTIONS = Gauge('revoagent_active_connections', 'Active WebSocket connections')
CIRCUIT_BREAKER_STATE = Gauge('revoagent_circuit_breaker_state', 'Circuit breaker state', ['name'])

app = FastAPI(
    title="reVoAgent Enhanced Backend",
    description="Production-ready backend with resilience patterns and monitoring",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add performance monitoring middleware
app.middleware("http")(performance_middleware)

# Global instances
model_manager: Optional[EnhancedLocalModelManager] = None
redis_client: Optional[redis.Redis] = None
active_websockets = set()

class ChatRequest(BaseModel):
    content: str
    system_prompt: Optional[str] = None
    max_tokens: int = 1024
    temperature: float = 0.7

class ChatResponse(BaseModel):
    content: str
    provider: str
    tokens_used: int
    generation_time: float

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    services: Dict[str, Any]
    summary: Dict[str, Any]

@app.on_event("startup")
async def startup_event():
    """Initialize the application with enhanced startup sequence"""
    global model_manager, redis_client
    
    logger.info("🚀 Starting reVoAgent Enhanced Backend v2.0.0...")
    
    # Initialize Redis
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        redis_client = redis.from_url(redis_url, decode_responses=True)
        redis_client.ping()
        logger.info("✅ Redis connection established")
    except Exception as e:
        logger.warning(f"⚠️ Redis connection failed: {e}")
    
    # Initialize model manager with circuit breaker
    if EnhancedLocalModelManager:
        config = {
            "openai_api_key": os.getenv("OPENAI_API_KEY"),
            "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
        }
        
        try:
            model_manager = EnhancedLocalModelManager(config)
            await model_manager.initialize_with_fallback()
            logger.info("✅ AI model manager initialized")
        except Exception as e:
            logger.error(f"❌ Model manager initialization failed: {e}")
    
    logger.info("✅ Backend initialization complete")

@app.on_event("shutdown")
async def shutdown_event():
    """Graceful shutdown"""
    logger.info("🛑 Shutting down reVoAgent Backend...")
    
    # Close WebSocket connections
    for websocket in active_websockets.copy():
        try:
            await websocket.close()
        except:
            pass
    
    # Close Redis connection
    if redis_client:
        redis_client.close()
    
    logger.info("✅ Shutdown complete")

@app.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe - basic health check"""
    return {"status": "alive", "timestamp": datetime.now().isoformat()}

@app.get("/health/ready")
async def readiness_check():
    """Kubernetes readiness probe - dependency health check"""
    try:
        # Quick checks for critical dependencies
        checks = {
            "redis": False,
            "ai_models": False
        }
        
        # Check Redis
        if redis_client:
            try:
                redis_client.ping()
                checks["redis"] = True
            except:
                pass
        
        # Check AI models
        if model_manager:
            checks["ai_models"] = True
        
        # Determine readiness
        ready = all(checks.values())
        status_code = 200 if ready else 503
        
        return JSONResponse(
            status_code=status_code,
            content={
                "status": "ready" if ready else "not_ready",
                "checks": checks,
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@app.get("/health", response_model=HealthResponse)
async def comprehensive_health_check():
    """Comprehensive health check with detailed system status"""
    try:
        health_data = await health_checker.comprehensive_health_check()
        
        # Add circuit breaker stats
        cb_stats = await get_all_circuit_breaker_stats()
        health_data["circuit_breakers"] = cb_stats
        
        # Add performance metrics
        perf_metrics = performance_monitor.get_metrics()
        health_data["performance"] = perf_metrics
        
        # Update Prometheus metrics
        for name, stats in cb_stats.items():
            state_value = {"closed": 0, "open": 1, "half_open": 0.5}.get(stats["state"], -1)
            CIRCUIT_BREAKER_STATE.labels(name=name).set(state_value)
        
        return health_data
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/api/chat", response_model=ChatResponse)
@rate_limit(requests_per_minute=100)  # Rate limiting
@cache_response(ttl=300, key_prefix="chat")  # 5-minute cache for similar requests
@compress_response()  # Response compression
async def chat_endpoint(request: ChatRequest, http_request: Request):
    """Enhanced chat endpoint with circuit breaker protection"""
    
    # Circuit breaker for AI model calls
    ai_circuit_breaker = get_circuit_breaker(
        "ai_models",
        CircuitBreakerConfig(failure_threshold=3, timeout=30.0)
    )
    
    try:
        if not model_manager:
            raise HTTPException(status_code=503, detail="AI models not available")
        
        # Create generation request
        gen_request = GenerationRequest(
            prompt=request.content,
            system_prompt=request.system_prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        # Generate response with circuit breaker protection
        async def generate_with_model():
            return await model_manager.generate(gen_request)
        
        response = await ai_circuit_breaker.call(generate_with_model)
        
        # Update metrics
        REQUEST_COUNT.labels(
            method=http_request.method,
            endpoint="/api/chat",
            status="success"
        ).inc()
        
        return ChatResponse(
            content=response.content,
            provider=response.provider.value,
            tokens_used=response.tokens_used,
            generation_time=response.generation_time
        )
        
    except Exception as e:
        REQUEST_COUNT.labels(
            method=http_request.method,
            endpoint="/api/chat",
            status="error"
        ).inc()
        
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/models")
@cache_response(ttl=60, key_prefix="models")  # 1-minute cache
async def list_models():
    """List available AI models with caching"""
    if not model_manager:
        return {"models": [], "status": "not_initialized"}
    
    try:
        health = await model_manager.health_check()
        return {
            "models": health.get("available_providers", []),
            "status": health["status"],
            "resources": health.get("resources", {}),
            "cached_at": datetime.now().isoformat()
        }
    except Exception as e:
        return {"models": [], "status": f"error: {str(e)}"}

@app.get("/api/performance")
async def get_performance_metrics():
    """Get detailed performance metrics"""
    try:
        metrics = performance_monitor.get_metrics()
        cb_stats = await get_all_circuit_breaker_stats()
        
        return {
            "performance_metrics": metrics,
            "circuit_breakers": cb_stats,
            "active_websockets": len(active_websockets),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """Enhanced WebSocket endpoint with connection management"""
    await websocket.accept()
    active_websockets.add(websocket)
    ACTIVE_CONNECTIONS.set(len(active_websockets))
    
    # Circuit breaker for WebSocket AI calls
    ws_circuit_breaker = get_circuit_breaker(
        "websocket_ai",
        CircuitBreakerConfig(failure_threshold=5, timeout=60.0)
    )
    
    try:
        while True:
            # Receive message with timeout
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=30.0)
            except asyncio.TimeoutError:
                await websocket.send_json({
                    "type": "ping",
                    "timestamp": datetime.now().isoformat()
                })
                continue
            
            if not model_manager:
                await websocket.send_json({
                    "error": "AI models not available",
                    "type": "error"
                })
                continue
            
            # Process chat request with circuit breaker
            try:
                async def ws_generate():
                    gen_request = GenerationRequest(
                        prompt=data.get("content", ""),
                        system_prompt=data.get("system_prompt"),
                        max_tokens=data.get("max_tokens", 1024),
                        temperature=data.get("temperature", 0.7)
                    )
                    return await model_manager.generate(gen_request)
                
                response = await ws_circuit_breaker.call(ws_generate)
                
                await websocket.send_json({
                    "content": response.content,
                    "provider": response.provider.value,
                    "tokens_used": response.tokens_used,
                    "generation_time": response.generation_time,
                    "type": "response",
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                await websocket.send_json({
                    "error": str(e),
                    "type": "error",
                    "timestamp": datetime.now().isoformat()
                })
                
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        active_websockets.discard(websocket)
        ACTIVE_CONNECTIONS.set(len(active_websockets))

@app.get("/api/admin/cache/clear")
async def clear_cache(pattern: str = "*"):
    """Admin endpoint to clear cache"""
    try:
        cleared = await cache_manager.clear_pattern(f"*{pattern}*")
        return {"cleared_keys": cleared, "pattern": pattern}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/circuit-breaker/{name}/reset")
async def reset_circuit_breaker(name: str):
    """Admin endpoint to reset circuit breaker"""
    try:
        cb = get_circuit_breaker(name)
        await cb.reset()
        return {"message": f"Circuit breaker {name} reset successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Production-ready server configuration
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=12001,
        reload=False,
        log_level="info",
        access_log=True,
        workers=1,  # Single worker for now, can be increased
        loop="uvloop",  # High-performance event loop
        http="httptools",  # High-performance HTTP parser
        limit_concurrency=1000,
        limit_max_requests=10000,
        timeout_keep_alive=30
    )