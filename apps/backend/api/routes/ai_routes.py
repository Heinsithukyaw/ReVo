#!/usr/bin/env python3
"""
AI Service Routes for reVoAgent Backend
"""

from fastapi import APIRouter, Depends, Request
from typing import Dict, Any

router = APIRouter()

@router.get("/status")
async def ai_status(request: Request):
    """Get AI service status"""
    try:
        ai_service = request.app.state.ai_service
        if ai_service:
            performance = ai_service.get_performance_summary()
            return {
                "status": "operational",
                "performance": performance
            }
        else:
            return {"status": "not_initialized"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/models")
async def list_models():
    """List available AI models"""
    return {
        "local_models": ["deepseek_r1", "llama_local"],
        "cloud_models": ["claude-3-sonnet", "gemini-pro", "gpt-4"]
    }