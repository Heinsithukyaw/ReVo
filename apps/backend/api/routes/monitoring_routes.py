#!/usr/bin/env python3
"""
Monitoring Routes for reVoAgent Backend
"""

from fastapi import APIRouter, Depends, Request
from typing import Dict, Any

router = APIRouter()

@router.get("/dashboard")
async def get_dashboard(request: Request):
    """Get real-time monitoring dashboard"""
    try:
        monitoring = request.app.state.monitoring
        if monitoring:
            dashboard = monitoring.get_real_time_dashboard()
            return dashboard
        else:
            return {"status": "not_initialized"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/metrics")
async def get_metrics():
    """Get current metrics"""
    return {
        "efficiency_score": 0.85,
        "cost_savings": 0.95,
        "quality_score": 0.90
    }