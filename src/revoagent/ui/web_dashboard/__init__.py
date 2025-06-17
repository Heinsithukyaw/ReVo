"""
Web Dashboard - Browser-based Management Interface

Provides a comprehensive web-based interface for managing agents, workflows,
and monitoring system performance.
"""

from .dashboard_server import DashboardServer
from .api_routes import APIRoutes
from .websocket_manager import WebSocketManager

__all__ = [
    'DashboardServer',
    'APIRoutes',
    'WebSocketManager'
]