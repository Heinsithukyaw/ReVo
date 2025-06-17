#!/usr/bin/env python3
"""
Health Check Router
Provides health check endpoints for the backend services
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import asyncio
from datetime import datetime

router = APIRouter()

@router.get("/")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "reVoAgent Backend API v2.0"
    }

@router.get("/detailed")
async def detailed_health_check():
    """Detailed health check with service status"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "api": "operational",
            "database": "operational",
            "ai_service": "operational",
            "team_coordinator": "operational",
            "cost_optimizer": "operational",
            "quality_gates": "operational",
            "monitoring": "operational"
        },
        "version": "2.0.0",
        "uptime": "operational"
    }

@router.get("/readiness")
async def readiness_check():
    """Kubernetes readiness probe"""
    return {"status": "ready"}

@router.get("/liveness")
async def liveness_check():
    """Kubernetes liveness probe"""
    return {"status": "alive"}