"""
🌐 API Module for reVoAgent

FastAPI-based API endpoints for the Three-Engine Architecture,
including REST APIs and WebSocket endpoints for real-time communication.
"""

from .websocket_endpoints import router as websocket_router, initialize_websocket_system, shutdown_websocket_system

__all__ = [
    'websocket_router',
    'initialize_websocket_system', 
    'shutdown_websocket_system'
]