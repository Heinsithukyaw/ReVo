#!/usr/bin/env python3
"""
Multi-Agent Chat API Endpoints
FastAPI endpoints for real-time multi-agent chat functionality
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import asyncio
import json
import logging
from datetime import datetime

# Import our multi-agent chat system
try:
    from packages.chat.realtime_multi_agent_chat import RealTimeMultiAgentChat, MultiAgentChatWebSocketServer
except ImportError:
    # Fallback for development
    class RealTimeMultiAgentChat:
        async def start_realtime_session(self, user_id, initial_message, collaboration_pattern="comprehensive_swarm"):
            return "mock_session_id"
        
        async def process_realtime_message(self, session_id, message, user_id):
            return {"status": "processed"}
        
        async def get_session_state(self, session_id):
            return {"session_id": session_id, "status": "active"}
        
        async def end_session(self, session_id):
            return {"status": "ended"}

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/v1/chat/multi-agent", tags=["Multi-Agent Chat"])

# Initialize chat system
chat_system = RealTimeMultiAgentChat()
websocket_server = None

# Pydantic models
class StartSessionRequest(BaseModel):
    user_id: str
    initial_message: str
    collaboration_pattern: str = "comprehensive_swarm"

class SendMessageRequest(BaseModel):
    session_id: str
    message: str
    user_id: str

class SessionResponse(BaseModel):
    session_id: str
    status: str
    message: str

class SessionStateResponse(BaseModel):
    session_id: str
    user_id: str
    created_at: str
    status: str
    collaboration_pattern: str
    message_history: List[Dict[str, Any]]
    agent_states: Dict[str, Any]
    shared_context: Dict[str, Any]

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected for session {session_id}")
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket disconnected for session {session_id}")
    
    async def send_personal_message(self, message: str, session_id: str):
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Error sending message to {session_id}: {e}")
                self.disconnect(session_id)

manager = ConnectionManager()

# API Endpoints

@router.post("/start", response_model=SessionResponse)
async def start_multi_agent_session(request: StartSessionRequest):
    """Start a new multi-agent chat session"""
    try:
        session_id = await chat_system.start_realtime_session(
            user_id=request.user_id,
            initial_message=request.initial_message,
            collaboration_pattern=request.collaboration_pattern
        )
        
        return SessionResponse(
            session_id=session_id,
            status="started",
            message=f"Multi-agent session started with pattern: {request.collaboration_pattern}"
        )
    
    except Exception as e:
        logger.error(f"Error starting session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start session: {str(e)}")

@router.post("/message")
async def send_message(request: SendMessageRequest):
    """Send a message to an existing multi-agent session"""
    try:
        await chat_system.process_realtime_message(
            session_id=request.session_id,
            message=request.message,
            user_id=request.user_id
        )
        
        return {"status": "message_sent", "session_id": request.session_id}
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")

@router.get("/session/{session_id}", response_model=SessionStateResponse)
async def get_session_state(session_id: str):
    """Get the current state of a multi-agent session"""
    try:
        session_state = await chat_system.get_session_state(session_id)
        
        return SessionStateResponse(
            session_id=session_state["session_id"] if "session_id" in session_state else session_id,
            user_id=session_state.get("user_id", "unknown"),
            created_at=session_state.get("created_at", datetime.now().isoformat()),
            status=session_state.get("status", "unknown"),
            collaboration_pattern=session_state.get("collaboration_pattern", "unknown"),
            message_history=session_state.get("message_history", []),
            agent_states=session_state.get("agent_states", {}),
            shared_context=session_state.get("shared_context", {})
        )
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting session state: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get session state: {str(e)}")

@router.delete("/session/{session_id}")
async def end_session(session_id: str):
    """End a multi-agent chat session"""
    try:
        await chat_system.end_session(session_id)
        
        # Disconnect WebSocket if connected
        manager.disconnect(session_id)
        
        return {"status": "session_ended", "session_id": session_id}
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error ending session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to end session: {str(e)}")

@router.get("/patterns")
async def get_collaboration_patterns():
    """Get available collaboration patterns"""
    patterns = [
        {
            "name": "code_review_swarm",
            "display_name": "Code Review Swarm",
            "description": "Parallel analysis by code analyst and debug detective",
            "agents": ["code_analyst", "debug_detective"],
            "pattern": "parallel_analysis",
            "best_for": ["code review", "quality analysis", "security audit"]
        },
        {
            "name": "debugging_cascade",
            "display_name": "Debugging Cascade",
            "description": "Sequential analysis for complex debugging",
            "agents": ["debug_detective", "code_analyst", "workflow_manager"],
            "pattern": "sequential_cascade",
            "best_for": ["bug investigation", "root cause analysis", "troubleshooting"]
        },
        {
            "name": "workflow_orchestration",
            "display_name": "Workflow Orchestration",
            "description": "Iterative collaboration for workflow optimization",
            "agents": ["workflow_manager", "code_analyst"],
            "pattern": "iterative_collaboration",
            "best_for": ["process automation", "workflow design", "optimization"]
        },
        {
            "name": "comprehensive_swarm",
            "display_name": "Comprehensive Swarm",
            "description": "Full multi-agent swarm intelligence",
            "agents": ["code_analyst", "debug_detective", "workflow_manager", "coordinator"],
            "pattern": "swarm_intelligence",
            "best_for": ["complex analysis", "comprehensive solutions", "strategic planning"]
        }
    ]
    
    return {"patterns": patterns}

@router.get("/health")
async def health_check():
    """Health check endpoint for multi-agent chat service"""
    return {
        "status": "healthy",
        "service": "multi-agent-chat",
        "timestamp": datetime.now().isoformat(),
        "active_sessions": len(chat_system.active_sessions) if hasattr(chat_system, 'active_sessions') else 0
    }

# WebSocket endpoint for real-time communication
@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time multi-agent chat"""
    await manager.connect(websocket, session_id)
    
    # Register with chat system
    await chat_system.register_websocket_client(websocket, session_id)
    
    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                
                if message_data.get("type") == "message":
                    # Process message through chat system
                    await chat_system.process_realtime_message(
                        session_id=session_id,
                        message=message_data.get("content", ""),
                        user_id=message_data.get("user_id", "anonymous")
                    )
                
                elif message_data.get("type") == "ping":
                    # Respond to ping
                    await websocket.send_text(json.dumps({"type": "pong"}))
                
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
            
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"Processing error: {str(e)}"
                }))
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
    
    finally:
        # Clean up
        manager.disconnect(session_id)
        await chat_system.unregister_websocket_client(session_id)

# Metrics endpoint
@router.get("/metrics")
async def get_metrics():
    """Get multi-agent chat metrics"""
    try:
        active_sessions = len(chat_system.active_sessions) if hasattr(chat_system, 'active_sessions') else 0
        connected_clients = len(manager.active_connections)
        
        return {
            "active_sessions": active_sessions,
            "connected_websockets": connected_clients,
            "total_agents": 4,  # code_analyst, debug_detective, workflow_manager, coordinator
            "collaboration_patterns": 4,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")

# Session management endpoints
@router.get("/sessions")
async def list_active_sessions():
    """List all active multi-agent sessions"""
    try:
        if hasattr(chat_system, 'active_sessions'):
            sessions = []
            for session_id, session_data in chat_system.active_sessions.items():
                sessions.append({
                    "session_id": session_id,
                    "user_id": session_data.get("user_id", "unknown"),
                    "status": session_data.get("status", "unknown"),
                    "created_at": session_data.get("created_at", "unknown"),
                    "collaboration_pattern": session_data.get("collaboration_pattern", "unknown"),
                    "message_count": len(session_data.get("message_history", []))
                })
            
            return {"sessions": sessions, "total": len(sessions)}
        else:
            return {"sessions": [], "total": 0}
    
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")

# Initialize WebSocket server (called from main application)
async def initialize_websocket_server():
    """Initialize the WebSocket server for multi-agent chat"""
    global websocket_server
    try:
        websocket_server = MultiAgentChatWebSocketServer(chat_system)
        server = await websocket_server.start_server(host="0.0.0.0", port=8765)
        logger.info("Multi-Agent Chat WebSocket server initialized on port 8765")
        return server
    except Exception as e:
        logger.error(f"Failed to initialize WebSocket server: {e}")
        return None

# Export router and initialization function
__all__ = ["router", "initialize_websocket_server", "chat_system"]