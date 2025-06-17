#!/usr/bin/env python3
"""
Team Coordination Routes for reVoAgent Backend
"""

from fastapi import APIRouter, Depends, Request
from typing import Dict, Any

router = APIRouter()

@router.get("/status")
async def team_status(request: Request):
    """Get team coordination status"""
    try:
        team_coordinator = request.app.state.team_coordinator
        if team_coordinator:
            status = team_coordinator.get_team_status()
            return status
        else:
            return {"status": "not_initialized"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/agents")
async def list_agents():
    """List all agents"""
    return {
        "claude_agents": 30,
        "gemini_agents": 40,
        "openhands_agents": 30,
        "total": 100
    }