#!/usr/bin/env python3
"""
Health Check Routes for reVoAgent Backend
"""

from fastapi import APIRouter, Depends, Request
from typing import Dict, Any
import asyncio
from datetime import datetime

router = APIRouter()

@router.get("/")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "reVoAgent Backend",
        "version": "2.0.0"
    }

@router.get("/detailed")
async def detailed_health_check(request: Request):
    """Detailed health check with service status"""
    
    try:
        # Check if services are available
        services_status = {}
        
        # Check AI Service
        try:
            ai_service = request.app.state.ai_service
            if ai_service:
                cost_summary = ai_service.get_cost_summary()
                services_status["ai_service"] = {
                    "status": "healthy",
                    "total_requests": cost_summary["total_requests"],
                    "local_usage": f"{cost_summary['local_usage_percentage']:.1%}"
                }
            else:
                services_status["ai_service"] = {"status": "not_initialized"}
        except Exception as e:
            services_status["ai_service"] = {"status": "error", "error": str(e)}
        
        # Check Team Coordinator
        try:
            team_coordinator = request.app.state.team_coordinator
            if team_coordinator:
                team_status = team_coordinator.get_team_status()
                services_status["team_coordinator"] = {
                    "status": "healthy",
                    "total_agents": team_status["team_metrics"]["total_agents"],
                    "active_agents": team_status["team_metrics"]["active_agents"],
                    "tasks_completed": team_status["team_metrics"]["tasks_completed_today"]
                }
            else:
                services_status["team_coordinator"] = {"status": "not_initialized"}
        except Exception as e:
            services_status["team_coordinator"] = {"status": "error", "error": str(e)}
        
        # Check Cost Optimizer
        try:
            cost_optimizer = request.app.state.cost_optimizer
            if cost_optimizer:
                cost_summary = cost_optimizer.get_cost_summary()
                services_status["cost_optimizer"] = {
                    "status": "healthy",
                    "savings_percentage": f"{cost_summary['savings_analysis']['savings_percentage']:.1%}",
                    "local_usage": f"{cost_summary['routing_performance']['local_usage_percentage']:.1%}"
                }
            else:
                services_status["cost_optimizer"] = {"status": "not_initialized"}
        except Exception as e:
            services_status["cost_optimizer"] = {"status": "error", "error": str(e)}
        
        # Check Quality Gates
        try:
            quality_gates = request.app.state.quality_gates
            if quality_gates:
                services_status["quality_gates"] = {
                    "status": "healthy",
                    "available_gates": len(quality_gates.gates),
                    "minimum_score": quality_gates.thresholds["minimum_score"]
                }
            else:
                services_status["quality_gates"] = {"status": "not_initialized"}
        except Exception as e:
            services_status["quality_gates"] = {"status": "error", "error": str(e)}
        
        # Check Monitoring
        try:
            monitoring = request.app.state.monitoring
            if monitoring:
                dashboard_data = monitoring.get_real_time_dashboard()
                services_status["monitoring"] = {
                    "status": "healthy",
                    "efficiency_score": f"{dashboard_data['system_health']['efficiency_score']:.2f}",
                    "active_alerts": len(dashboard_data['active_alerts'])
                }
            else:
                services_status["monitoring"] = {"status": "not_initialized"}
        except Exception as e:
            services_status["monitoring"] = {"status": "error", "error": str(e)}
        
        # Determine overall health
        healthy_services = sum(1 for service in services_status.values() if service.get("status") == "healthy")
        total_services = len(services_status)
        overall_health = "healthy" if healthy_services == total_services else "degraded"
        
        return {
            "status": overall_health,
            "timestamp": datetime.now().isoformat(),
            "service": "reVoAgent Backend",
            "version": "2.0.0",
            "services": services_status,
            "summary": {
                "healthy_services": healthy_services,
                "total_services": total_services,
                "health_percentage": f"{(healthy_services/total_services)*100:.1f}%"
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@router.get("/readiness")
async def readiness_check(request: Request):
    """Kubernetes readiness probe endpoint"""
    
    try:
        # Check if critical services are ready
        ai_service = getattr(request.app.state, 'ai_service', None)
        team_coordinator = getattr(request.app.state, 'team_coordinator', None)
        
        if ai_service and team_coordinator:
            return {"status": "ready", "timestamp": datetime.now().isoformat()}
        else:
            return {"status": "not_ready", "timestamp": datetime.now().isoformat()}
            
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/liveness")
async def liveness_check():
    """Kubernetes liveness probe endpoint"""
    
    try:
        # Simple liveness check - if we can respond, we're alive
        return {"status": "alive", "timestamp": datetime.now().isoformat()}
        
    except Exception as e:
        return {"status": "error", "error": str(e)}