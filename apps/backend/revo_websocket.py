"""
ReVo AI WebSocket Endpoint
Real-time communication endpoint for the ReVo AI Chat Interface
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.security import HTTPBearer
import jwt

# Import core components
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "packages"))

from core.revo_orchestrator import ReVoOrchestrator, MessageType
from core.auth import verify_jwt_token
from core.workflow_engine import WorkflowEngine
from engines.perfect_recall_engine import PerfectRecallEngine
from engines.creative_engine import CreativeEngine
from engines.parallel_mind_engine import ParallelMindEngine

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()


class ConnectionManager:
    """Manages WebSocket connections for the ReVo AI Chat Interface."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_sessions: Dict[str, Dict[str, Any]] = {}
        self.orchestrators: Dict[str, ReVoOrchestrator] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str, user_id: str):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        self.user_sessions[session_id] = {
            "user_id": user_id,
            "connected_at": time.time(),
            "last_activity": time.time()
        }
        
        # Initialize orchestrator for this session
        await self._initialize_orchestrator(session_id, user_id)
        
        logger.info(f"WebSocket connection established for session {session_id}")
    
    def disconnect(self, session_id: str):
        """Remove a WebSocket connection."""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if session_id in self.user_sessions:
            del self.user_sessions[session_id]
        if session_id in self.orchestrators:
            del self.orchestrators[session_id]
        
        logger.info(f"WebSocket connection closed for session {session_id}")
    
    async def send_personal_message(self, message: Dict[str, Any], session_id: str):
        """Send a message to a specific session."""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            try:
                await websocket.send_text(json.dumps(message))
                self.user_sessions[session_id]["last_activity"] = time.time()
            except Exception as e:
                logger.error(f"Error sending message to session {session_id}: {e}")
                # Connection might be broken, remove it
                self.disconnect(session_id)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast a message to all connected sessions."""
        disconnected_sessions = []
        
        for session_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(message))
                self.user_sessions[session_id]["last_activity"] = time.time()
            except Exception as e:
                logger.error(f"Error broadcasting to session {session_id}: {e}")
                disconnected_sessions.append(session_id)
        
        # Clean up disconnected sessions
        for session_id in disconnected_sessions:
            self.disconnect(session_id)
    
    async def _initialize_orchestrator(self, session_id: str, user_id: str):
        """Initialize ReVo Orchestrator for a session."""
        try:
            # Initialize LLM client with multi-provider fallback
            from ai.llm_config import create_llm_client_from_env
            llm_client = create_llm_client_from_env()
            
            # Initialize engines (these would be actual instances in production)
            perfect_recall_engine = None  # PerfectRecallEngine()
            creative_engine = None  # CreativeEngine()
            parallel_mind_engine = None  # ParallelMindEngine()
            workflow_engine = None  # WorkflowEngine()
            
            # Create orchestrator with real LLM client
            orchestrator = ReVoOrchestrator(
                workflow_engine=workflow_engine,
                perfect_recall_engine=perfect_recall_engine,
                creative_engine=creative_engine,
                parallel_mind_engine=parallel_mind_engine,
                llm_client=llm_client
            )
            
            # Set WebSocket callback
            async def websocket_callback(message: Dict[str, Any]):
                await self.send_personal_message(message, session_id)
            
            orchestrator.set_websocket_callback(websocket_callback)
            
            # Store orchestrator
            self.orchestrators[session_id] = orchestrator
            
            # Send welcome message
            await self.send_personal_message({
                "type": "message",
                "data": {
                    "id": f"welcome_{int(time.time() * 1000)}",
                    "sender": "revo",
                    "content": "Welcome to ReVo AI! I'm ready to help you with development tasks. Type a message or use '/' for commands.",
                    "timestamp": time.time(),
                    "message_type": "success"
                }
            }, session_id)
            
        except Exception as e:
            logger.error(f"Error initializing orchestrator for session {session_id}: {e}")
    
    async def handle_message(self, message_data: Dict[str, Any], session_id: str):
        """Handle incoming message from a session."""
        try:
            # Update last activity
            if session_id in self.user_sessions:
                self.user_sessions[session_id]["last_activity"] = time.time()
            
            # Get orchestrator for this session
            orchestrator = self.orchestrators.get(session_id)
            if not orchestrator:
                await self.send_personal_message({
                    "type": "error",
                    "data": {"message": "Session not properly initialized"}
                }, session_id)
                return
            
            # Handle the message
            await orchestrator.handle_message(message_data, session_id)
            
        except Exception as e:
            logger.error(f"Error handling message for session {session_id}: {e}")
            await self.send_personal_message({
                "type": "error",
                "data": {"message": f"Error processing message: {str(e)}"}
            }, session_id)
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about active sessions."""
        current_time = time.time()
        active_count = len(self.active_connections)
        
        session_durations = []
        for session_data in self.user_sessions.values():
            duration = current_time - session_data["connected_at"]
            session_durations.append(duration)
        
        avg_duration = sum(session_durations) / len(session_durations) if session_durations else 0
        
        return {
            "active_sessions": active_count,
            "total_sessions": len(self.user_sessions),
            "average_session_duration": avg_duration,
            "oldest_session": max(session_durations) if session_durations else 0
        }


# Global connection manager
manager = ConnectionManager()


async def verify_websocket_token(token: str) -> Dict[str, Any]:
    """Verify JWT token for WebSocket authentication."""
    try:
        # This would use your actual JWT verification logic
        # For now, return a mock user
        return {
            "user_id": "user_123",
            "username": "developer",
            "permissions": ["chat", "execute", "create_projects"]
        }
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")


async def websocket_endpoint(websocket: WebSocket, token: Optional[str] = None):
    """
    WebSocket endpoint for ReVo AI Chat Interface.
    
    Args:
        websocket: WebSocket connection
        token: JWT authentication token (query parameter)
    """
    session_id = None
    
    try:
        # Verify authentication
        if not token:
            await websocket.close(code=1008, reason="Authentication token required")
            return
        
        user_data = await verify_websocket_token(token)
        user_id = user_data["user_id"]
        
        # Generate session ID
        session_id = f"{user_id}_{int(time.time() * 1000)}"
        
        # Accept connection
        await manager.connect(websocket, session_id, user_id)
        
        # Send connection confirmation
        await manager.send_personal_message({
            "type": "status",
            "data": {
                "status": "connected",
                "session_id": session_id,
                "user_id": user_id,
                "timestamp": time.time()
            }
        }, session_id)
        
        # Message handling loop
        while True:
            try:
                # Receive message
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Validate message structure
                if not isinstance(message_data, dict):
                    await manager.send_personal_message({
                        "type": "error",
                        "data": {"message": "Invalid message format"}
                    }, session_id)
                    continue
                
                # Handle different message types
                message_type = message_data.get("type", "message")
                
                if message_type == "ping":
                    # Respond to ping with pong
                    await manager.send_personal_message({
                        "type": "pong",
                        "data": {"timestamp": time.time()}
                    }, session_id)
                
                elif message_type == "message":
                    # Handle chat message
                    await manager.handle_message(message_data.get("data", {}), session_id)
                
                elif message_type == "status_request":
                    # Send session status
                    stats = manager.get_session_stats()
                    await manager.send_personal_message({
                        "type": "status",
                        "data": {
                            "session_stats": stats,
                            "session_id": session_id,
                            "timestamp": time.time()
                        }
                    }, session_id)
                
                else:
                    await manager.send_personal_message({
                        "type": "error",
                        "data": {"message": f"Unknown message type: {message_type}"}
                    }, session_id)
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for session {session_id}")
                break
            
            except json.JSONDecodeError:
                await manager.send_personal_message({
                    "type": "error",
                    "data": {"message": "Invalid JSON format"}
                }, session_id)
            
            except Exception as e:
                logger.error(f"Error in message loop for session {session_id}: {e}")
                await manager.send_personal_message({
                    "type": "error",
                    "data": {"message": f"Internal error: {str(e)}"}
                }, session_id)
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        if session_id:
            await manager.send_personal_message({
                "type": "error",
                "data": {"message": f"Connection error: {str(e)}"}
            }, session_id)
    
    finally:
        # Clean up connection
        if session_id:
            manager.disconnect(session_id)


# Health check endpoint for WebSocket service
async def websocket_health():
    """Health check for WebSocket service."""
    stats = manager.get_session_stats()
    return {
        "status": "healthy",
        "service": "revo_websocket",
        "timestamp": time.time(),
        "stats": stats
    }


# Broadcast endpoint for system messages
async def broadcast_system_message(message: str, message_type: str = "system"):
    """Broadcast a system message to all connected sessions."""
    await manager.broadcast({
        "type": "message",
        "data": {
            "id": f"system_{int(time.time() * 1000)}",
            "sender": "system",
            "content": message,
            "timestamp": time.time(),
            "message_type": message_type
        }
    })
    
    return {"status": "broadcasted", "message": message}


# Session management endpoints
async def get_active_sessions():
    """Get information about active sessions."""
    stats = manager.get_session_stats()
    sessions = []
    
    for session_id, session_data in manager.user_sessions.items():
        sessions.append({
            "session_id": session_id,
            "user_id": session_data["user_id"],
            "connected_at": session_data["connected_at"],
            "last_activity": session_data["last_activity"],
            "duration": time.time() - session_data["connected_at"]
        })
    
    return {
        "stats": stats,
        "sessions": sessions
    }


async def disconnect_session(session_id: str):
    """Forcefully disconnect a session."""
    if session_id in manager.active_connections:
        websocket = manager.active_connections[session_id]
        await websocket.close(code=1000, reason="Disconnected by admin")
        manager.disconnect(session_id)
        return {"status": "disconnected", "session_id": session_id}
    else:
        return {"status": "not_found", "session_id": session_id}