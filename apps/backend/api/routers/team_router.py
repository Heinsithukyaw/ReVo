#!/usr/bin/env python3
"""
Team Coordination Router
Handles AI team coordination and task management
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import sys
from pathlib import Path

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from apps.backend.services.ai_team_coordinator import AITeamCoordinator, TaskType, TaskPriority

router = APIRouter()

class EpicRequest(BaseModel):
    """Epic coordination request"""
    title: str
    description: str
    requirements: List[str] = []
    priority: str = "medium"
    estimated_complexity: int = 5

class TaskResponse(BaseModel):
    """Task response model"""
    task_id: str
    title: str
    description: str
    task_type: str
    priority: str
    assigned_agent: Optional[str] = None
    status: str

async def get_team_coordinator(request: Request) -> AITeamCoordinator:
    """Get team coordinator from app state"""
    return request.app.state.team_coordinator

@router.post("/coordinate-epic")
async def coordinate_epic(
    epic: EpicRequest,
    coordinator: AITeamCoordinator = Depends(get_team_coordinator)
):
    """Coordinate a development epic across AI agents"""
    try:
        # Convert to internal epic format
        epic_data = {
            "title": epic.title,
            "description": epic.description,
            "requirements": epic.requirements,
            "priority": epic.priority,
            "estimated_complexity": epic.estimated_complexity
        }
        
        # Coordinate the epic
        tasks = await coordinator.coordinate_development_task(epic_data)
        
        # Convert tasks to response format
        task_responses = [
            TaskResponse(
                task_id=task.task_id,
                title=task.title,
                description=task.description,
                task_type=task.task_type.value,
                priority=task.priority.value,
                assigned_agent=task.assigned_agent,
                status=task.status.value
            )
            for task in tasks
        ]
        
        return {
            "epic_id": f"epic_{epic.title.lower().replace(' ', '_')}",
            "tasks_created": len(tasks),
            "tasks": task_responses
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_team_status(coordinator: AITeamCoordinator = Depends(get_team_coordinator)):
    """Get current team status and metrics"""
    try:
        return coordinator.get_team_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents")
async def get_agent_summary(coordinator: AITeamCoordinator = Depends(get_team_coordinator)):
    """Get summary of all AI agents"""
    try:
        team_status = coordinator.get_team_status()
        return {
            "total_agents": team_status["team_metrics"]["total_agents"],
            "active_agents": team_status["team_metrics"]["active_agents"],
            "agent_breakdown": team_status["agent_summary"],
            "specializations": {
                "claude_agents": ["code_generation", "code_review", "documentation"],
                "gemini_agents": ["architecture_analysis", "performance_optimization", "security_scanning"],
                "openhands_agents": ["testing", "deployment_automation", "integration_testing"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tasks/active")
async def get_active_tasks(coordinator: AITeamCoordinator = Depends(get_team_coordinator)):
    """Get currently active tasks"""
    try:
        # Get active tasks from coordinator
        active_tasks = []
        for task_id, task in coordinator.active_tasks.items():
            active_tasks.append({
                "task_id": task.task_id,
                "title": task.title,
                "description": task.description,
                "task_type": task.task_type.value,
                "priority": task.priority.value,
                "assigned_agent": task.assigned_agent,
                "status": task.status.value,
                "created_at": task.created_at.isoformat(),
                "assigned_at": task.assigned_at.isoformat() if task.assigned_at else None,
                "started_at": task.started_at.isoformat() if task.started_at else None
            })
        
        return {
            "active_tasks": active_tasks,
            "total_active": len(active_tasks)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tasks/completed")
async def get_completed_tasks(coordinator: AITeamCoordinator = Depends(get_team_coordinator)):
    """Get completed tasks"""
    try:
        # Get completed tasks from coordinator
        completed_tasks = []
        for task_id, task in coordinator.completed_tasks.items():
            completed_tasks.append({
                "task_id": task.task_id,
                "title": task.title,
                "description": task.description,
                "task_type": task.task_type.value,
                "priority": task.priority.value,
                "assigned_agent": task.assigned_agent,
                "status": task.status.value,
                "created_at": task.created_at.isoformat(),
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "result": task.result
            })
        
        return {
            "completed_tasks": completed_tasks,
            "total_completed": len(completed_tasks)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))