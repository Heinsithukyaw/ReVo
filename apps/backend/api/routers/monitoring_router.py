#!/usr/bin/env python3
"""
Monitoring Router
Provides real-time monitoring and analytics endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, Any, Optional
import sys
from pathlib import Path

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from apps.backend.services.ai_team_monitoring import AITeamMonitoring
from apps.backend.services.cost_optimizer import CostOptimizedRouter
from apps.backend.services.quality_gates import QualityGates

router = APIRouter()

async def get_monitoring(request: Request) -> AITeamMonitoring:
    """Get monitoring service from app state"""
    return request.app.state.monitoring

async def get_cost_optimizer(request: Request) -> CostOptimizedRouter:
    """Get cost optimizer from app state"""
    return request.app.state.cost_optimizer

async def get_quality_gates(request: Request) -> QualityGates:
    """Get quality gates from app state"""
    return request.app.state.quality_gates

@router.get("/dashboard")
async def get_dashboard(monitoring: AITeamMonitoring = Depends(get_monitoring)):
    """Get real-time monitoring dashboard data"""
    try:
        return await monitoring.get_real_time_dashboard()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/daily-report")
async def get_daily_report(monitoring: AITeamMonitoring = Depends(get_monitoring)):
    """Get daily team performance report"""
    try:
        report = await monitoring.daily_team_report()
        return {
            "date": report.date.isoformat(),
            "total_features_completed": report.total_features_completed,
            "average_quality_score": report.average_quality_score,
            "cost_savings_vs_cloud": report.cost_savings_vs_cloud,
            "agent_efficiency": report.agent_efficiency,
            "top_performing_agents": report.top_performing_agents,
            "issues_identified": report.issues_identified,
            "recommendations": report.recommendations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cost-optimization")
async def get_cost_optimization_status(cost_optimizer: CostOptimizedRouter = Depends(get_cost_optimizer)):
    """Get cost optimization status and metrics"""
    try:
        return cost_optimizer.get_cost_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/quality-metrics")
async def get_quality_metrics(quality_gates: QualityGates = Depends(get_quality_gates)):
    """Get quality validation metrics"""
    try:
        return quality_gates.get_validation_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance-trends")
async def get_performance_trends(monitoring: AITeamMonitoring = Depends(get_monitoring)):
    """Get performance trends analysis"""
    try:
        if not monitoring.metrics_history:
            return {"error": "No metrics history available"}
        
        # Get recent trends
        recent_trends = await monitoring._get_recent_trends()
        
        # Get historical data
        history_data = []
        for metric in monitoring.metrics_history[-24:]:  # Last 24 data points
            history_data.append({
                "timestamp": metric.timestamp.isoformat(),
                "team_efficiency": metric.team_efficiency,
                "quality_score": metric.quality_score,
                "agent_utilization": metric.agent_utilization,
                "cost_per_feature": metric.cost_per_feature,
                "tasks_completed": metric.tasks_completed_today
            })
        
        return {
            "recent_trends": recent_trends,
            "historical_data": history_data,
            "data_points": len(history_data)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts")
async def get_current_alerts(monitoring: AITeamMonitoring = Depends(get_monitoring)):
    """Get current system alerts"""
    try:
        if not monitoring.metrics_history:
            return {"alerts": [], "status": "no_data"}
        
        latest_metrics = monitoring.metrics_history[-1]
        alerts = []
        
        # Check for alert conditions
        if latest_metrics.agent_utilization < 0.5:
            alerts.append({
                "type": "warning",
                "message": "Low agent utilization detected",
                "value": latest_metrics.agent_utilization,
                "threshold": 0.5
            })
        
        if latest_metrics.team_efficiency < 0.7:
            alerts.append({
                "type": "warning", 
                "message": "Low team efficiency detected",
                "value": latest_metrics.team_efficiency,
                "threshold": 0.7
            })
        
        if latest_metrics.quality_score < 0.8:
            alerts.append({
                "type": "error",
                "message": "Quality score below threshold",
                "value": latest_metrics.quality_score,
                "threshold": 0.8
            })
        
        if latest_metrics.daily_cost > 100:
            alerts.append({
                "type": "error",
                "message": "Daily cost budget exceeded",
                "value": latest_metrics.daily_cost,
                "threshold": 100
            })
        
        return {
            "alerts": alerts,
            "alert_count": len(alerts),
            "status": "critical" if any(a["type"] == "error" for a in alerts) else "warning" if alerts else "healthy"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/summary")
async def get_metrics_summary(monitoring: AITeamMonitoring = Depends(get_monitoring)):
    """Get comprehensive metrics summary"""
    try:
        dashboard_data = await monitoring.get_real_time_dashboard()
        
        return {
            "current_performance": dashboard_data.get("performance_metrics", {}),
            "cost_efficiency": dashboard_data.get("cost_metrics", {}),
            "team_status": dashboard_data.get("team_overview", {}),
            "targets_vs_actual": dashboard_data.get("performance_vs_targets", {}),
            "timestamp": dashboard_data.get("timestamp")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))