#!/usr/bin/env python3
"""
API Routes for reVoAgent Backend
"""

from .ai_routes import router as ai_router
from .team_routes import router as team_router
from .monitoring_routes import router as monitoring_router
from .health_routes import router as health_router

__all__ = [
    'ai_router',
    'team_router', 
    'monitoring_router',
    'health_router'
]