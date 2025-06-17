#!/usr/bin/env python3
"""
Multi-Agent Chat Orchestrator Entrypoint
Production-ready entrypoint for the Multi-Agent Chat system
"""

import asyncio
import logging
import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Add paths
sys.path.append('/app/src')
sys.path.append('/app/packages')

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import components
try:
    from packages.chat.realtime_multi_agent_chat import RealTimeMultiAgentChat, MultiAgentChatWebSocketServer
    from src.revoagent.api.multi_agent_chat_endpoints import router, initialize_websocket_server
except ImportError as e:
    logger.error(f"Failed to import Multi-Agent Chat components: {e}")
    sys.exit(1)

# Initialize FastAPI app
app = FastAPI(
    title="Multi-Agent Chat Orchestrator",
    description="Real-time Multi-Agent Chat System for reVoAgent",
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

# Include the multi-agent chat router
app.include_router(router)

# Global variables
chat_system = None
websocket_server = None

@app.on_event("startup")
async def startup_event():
    """Initialize the chat system on startup"""
    global chat_system, websocket_server
    
    try:
        # Initialize chat system
        chat_system = RealTimeMultiAgentChat()
        logger.info("Multi-Agent Chat System initialized")
        
        # Initialize WebSocket server if enabled
        if os.getenv('WEBSOCKET_ENABLED', 'true').lower() == 'true':
            websocket_server = await initialize_websocket_server()
            logger.info("WebSocket server initialized")
        
        logger.info("Multi-Agent Chat Orchestrator started successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize chat system: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global websocket_server
    
    try:
        if websocket_server:
            websocket_server.close()
            await websocket_server.wait_closed()
            logger.info("WebSocket server closed")
        
        logger.info("Multi-Agent Chat Orchestrator shutdown complete")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Multi-Agent Chat Orchestrator",
        "version": "1.0.0",
        "status": "running",
        "websocket_enabled": os.getenv('WEBSOCKET_ENABLED', 'true').lower() == 'true',
        "endpoints": {
            "start_session": "/api/v1/chat/multi-agent/start",
            "send_message": "/api/v1/chat/multi-agent/message", 
            "get_session": "/api/v1/chat/multi-agent/session/{session_id}",
            "websocket": "/api/v1/chat/multi-agent/ws/{session_id}",
            "patterns": "/api/v1/chat/multi-agent/patterns",
            "health": "/api/v1/chat/multi-agent/health"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "multi_agent_chat",
        "version": "1.0.0",
        "websocket_enabled": os.getenv('WEBSOCKET_ENABLED', 'true').lower() == 'true',
        "active_sessions": len(chat_system.active_sessions) if chat_system and hasattr(chat_system, 'active_sessions') else 0
    }

@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    if chat_system is None:
        return {"status": "not_ready", "reason": "Chat system not initialized"}, 503
    
    return {
        "status": "ready",
        "service": "multi_agent_chat",
        "capabilities": [
            "real_time_collaboration",
            "multi_agent_coordination",
            "websocket_communication",
            "pattern_based_collaboration"
        ]
    }

def main():
    """Main function to start the orchestrator"""
    logger.info("Starting Multi-Agent Chat Orchestrator...")
    
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