#!/usr/bin/env python3
"""
Code Analyst Agent Entrypoint
Production-ready entrypoint for the Code Analyst Agent
"""

import asyncio
import logging
import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

# Add paths
sys.path.append('/app/src')
sys.path.append('/app/packages')

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import agent
try:
    from packages.agents.code_analysis_agent import EnhancedCodeAnalysisAgent
except ImportError as e:
    logger.error(f"Failed to import Code Analysis Agent: {e}")
    sys.exit(1)

# Metrics
REQUEST_COUNT = Counter('code_analyst_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('code_analyst_request_duration_seconds', 'Request duration')
ANALYSIS_COUNT = Counter('code_analyst_analyses_total', 'Total code analyses', ['language', 'status'])

# Initialize FastAPI app
app = FastAPI(
    title="Code Analyst Agent",
    description="Enhanced Code Analysis Agent for reVoAgent",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agent
agent = None

@app.on_event("startup")
async def startup_event():
    """Initialize the agent on startup"""
    global agent
    try:
        agent = EnhancedCodeAnalysisAgent()
        logger.info("Code Analyst Agent initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}")
        raise

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agent_type": "code_analyst",
        "agent_id": os.getenv('AGENT_ID', 'unknown'),
        "version": "1.0.0"
    }

@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not ready")
    
    return {
        "status": "ready",
        "agent_type": "code_analyst",
        "capabilities": [
            "code_review",
            "architecture_analysis", 
            "performance_optimization",
            "security_analysis",
            "best_practices",
            "refactoring"
        ]
    }

@app.post("/analyze")
async def analyze_code(request: dict):
    """Analyze code endpoint"""
    REQUEST_COUNT.labels(method='POST', endpoint='/analyze').inc()
    
    with REQUEST_DURATION.time():
        try:
            code = request.get('code', '')
            language = request.get('language', 'python')
            context = request.get('context', {})
            
            if not code:
                raise HTTPException(status_code=400, detail="Code is required")
            
            # Perform analysis
            result = await agent.analyze_code(code, context)
            
            ANALYSIS_COUNT.labels(language=language, status='success').inc()
            
            return {
                "status": "success",
                "analysis": result,
                "agent_id": os.getenv('AGENT_ID', 'unknown'),
                "timestamp": asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            ANALYSIS_COUNT.labels(language=language, status='error').inc()
            logger.error(f"Analysis error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/review")
async def review_code(request: dict):
    """Code review endpoint"""
    REQUEST_COUNT.labels(method='POST', endpoint='/review').inc()
    
    with REQUEST_DURATION.time():
        try:
            code = request.get('code', '')
            context = request.get('context', {})
            
            if not code:
                raise HTTPException(status_code=400, detail="Code is required")
            
            # Perform review
            result = await agent.review_code(code, context)
            
            return {
                "status": "success",
                "review": result,
                "agent_id": os.getenv('AGENT_ID', 'unknown'),
                "timestamp": asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            logger.error(f"Review error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    if not os.getenv('METRICS_ENABLED', 'false').lower() == 'true':
        raise HTTPException(status_code=404, detail="Metrics not enabled")
    
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/capabilities")
async def get_capabilities():
    """Get agent capabilities"""
    return {
        "agent_type": "code_analyst",
        "specializations": [
            "code_review",
            "architecture_analysis",
            "performance_optimization", 
            "security_analysis",
            "best_practices",
            "refactoring"
        ],
        "supported_languages": [
            "python",
            "javascript",
            "typescript",
            "java",
            "go",
            "rust",
            "cpp",
            "c"
        ],
        "triggers": [
            "analyze",
            "review", 
            "optimize",
            "refactor",
            "architecture",
            "performance",
            "security",
            "code quality"
        ]
    }

def main():
    """Main function to start the agent"""
    logger.info("Starting Code Analyst Agent...")
    
    # Configuration
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', '8000'))
    workers = int(os.getenv('WORKERS', '1'))
    
    # Start the server
    uvicorn.run(
        app,
        host=host,
        port=port,
        workers=workers,
        log_level=os.getenv('LOG_LEVEL', 'info').lower(),
        access_log=True
    )

if __name__ == "__main__":
    main()