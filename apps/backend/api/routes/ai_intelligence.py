"""
AI Intelligence API Routes
Part of reVoAgent Phase 5: Advanced Intelligence & Automation
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import sys
from pathlib import Path

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from packages.ai.predictive_analytics_engine import (
    predictive_analytics_engine, 
    PerformanceMetrics, 
    WorkloadProfile,
    PredictionType
)
from packages.ai.intelligent_autoscaler import (
    intelligent_autoscaler,
    SystemMetrics,
    AutoScalingConfig
)
from packages.ai.anomaly_detection_engine import (
    anomaly_detection_engine,
    TrendData
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Intelligence"])

# Pydantic models for API
class PerformanceMetricsRequest(BaseModel):
    agent_id: str
    task_type: str
    success_rate: float
    avg_response_time: float
    resource_usage: float
    context: Dict[str, Any] = {}

class WorkloadProfileRequest(BaseModel):
    concurrent_tasks: int
    task_complexity: float
    resource_requirements: Dict[str, float]
    time_constraints: float
    priority_level: int

class PredictionRequest(BaseModel):
    task_type: str
    agent_id: str
    context: Dict[str, Any] = {}

class ResponseTimePredictionRequest(BaseModel):
    task_complexity: float
    system_load: float

class SystemMetricsRequest(BaseModel):
    metrics: Dict[str, float]

class AutoScalingConfigRequest(BaseModel):
    min_instances: int
    max_instances: int
    target_cpu_utilization: float
    target_memory_utilization: float
    scale_up_cooldown: int
    scale_down_cooldown: int

@router.post("/predictive/add-performance-data")
async def add_performance_data(request: PerformanceMetricsRequest):
    """Add performance data for ML training"""
    try:
        metrics = PerformanceMetrics(
            agent_id=request.agent_id,
            task_type=request.task_type,
            success_rate=request.success_rate,
            avg_response_time=request.avg_response_time,
            resource_usage=request.resource_usage,
            timestamp=datetime.now(),
            context=request.context
        )
        
        await predictive_analytics_engine.add_performance_data(metrics)
        
        return {
            "status": "success",
            "message": "Performance data added successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to add performance data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predictive/predict-performance")
async def predict_agent_performance(request: PredictionRequest):
    """Predict agent performance for a specific task"""
    try:
        prediction = await predictive_analytics_engine.predict_agent_performance(
            request.task_type, request.agent_id, request.context
        )
        
        return {
            "prediction_type": prediction.prediction_type.value,
            "predicted_value": prediction.predicted_value,
            "confidence": prediction.confidence,
            "timestamp": prediction.timestamp.isoformat(),
            "features_used": prediction.features_used,
            "model_version": prediction.model_version,
            "metadata": prediction.metadata
        }
        
    except Exception as e:
        logger.error(f"Performance prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predictive/predict-response-time")
async def predict_response_time(request: ResponseTimePredictionRequest):
    """Predict response time based on task complexity and system load"""
    try:
        prediction = await predictive_analytics_engine.predict_response_time(
            request.task_complexity, request.system_load
        )
        
        return {
            "predicted_response_time": prediction.predicted_value,
            "confidence": prediction.confidence,
            "timestamp": prediction.timestamp.isoformat(),
            "features_used": prediction.features_used,
            "metadata": prediction.metadata
        }
        
    except Exception as e:
        logger.error(f"Response time prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predictive/recommend-configuration")
async def recommend_optimal_configuration(request: WorkloadProfileRequest):
    """Get AI-powered system configuration recommendation"""
    try:
        workload = WorkloadProfile(
            concurrent_tasks=request.concurrent_tasks,
            task_complexity=request.task_complexity,
            resource_requirements=request.resource_requirements,
            time_constraints=request.time_constraints,
            priority_level=request.priority_level
        )
        
        config = await predictive_analytics_engine.recommend_optimal_configuration(workload)
        
        return {
            "agent_count": config.agent_count,
            "resource_allocation": config.resource_allocation,
            "timeout_settings": config.timeout_settings,
            "optimization_params": config.optimization_params,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Configuration recommendation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/predictive/analytics")
async def get_predictive_analytics():
    """Get analytics about predictive engine performance"""
    try:
        analytics = await predictive_analytics_engine.get_prediction_analytics()
        return analytics
        
    except Exception as e:
        logger.error(f"Failed to get predictive analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/autoscaling/analyze-load")
async def analyze_system_load():
    """Analyze current system load and get scaling recommendation"""
    try:
        decision = await intelligent_autoscaler.analyze_system_load()
        
        return {
            "direction": decision.direction.value,
            "target_instances": decision.target_instances,
            "current_instances": decision.current_instances,
            "confidence": decision.confidence,
            "triggers": [t.value for t in decision.triggers],
            "reasoning": decision.reasoning,
            "estimated_impact": decision.estimated_impact,
            "timestamp": decision.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"System load analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/autoscaling/execute-scaling")
async def execute_auto_scaling(background_tasks: BackgroundTasks):
    """Execute auto-scaling based on current analysis"""
    try:
        # Get scaling decision
        decision = await intelligent_autoscaler.analyze_system_load()
        
        # Execute scaling in background
        background_tasks.add_task(intelligent_autoscaler.auto_scale_agents, decision)
        
        return {
            "status": "scaling_initiated",
            "decision": {
                "direction": decision.direction.value,
                "target_instances": decision.target_instances,
                "current_instances": decision.current_instances,
                "reasoning": decision.reasoning
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Auto-scaling execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/autoscaling/metrics")
async def get_system_metrics():
    """Get current system metrics"""
    try:
        metrics = await intelligent_autoscaler.collect_system_metrics()
        
        return {
            "cpu_usage": metrics.cpu_usage,
            "memory_usage": metrics.memory_usage,
            "disk_usage": metrics.disk_usage,
            "network_io": metrics.network_io,
            "active_connections": metrics.active_connections,
            "queue_length": metrics.queue_length,
            "response_time": metrics.response_time,
            "error_rate": metrics.error_rate,
            "timestamp": metrics.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/autoscaling/configure")
async def configure_autoscaling(request: AutoScalingConfigRequest):
    """Configure auto-scaling parameters"""
    try:
        # Update autoscaler configuration
        intelligent_autoscaler.config.min_instances = request.min_instances
        intelligent_autoscaler.config.max_instances = request.max_instances
        intelligent_autoscaler.config.target_cpu_utilization = request.target_cpu_utilization
        intelligent_autoscaler.config.target_memory_utilization = request.target_memory_utilization
        intelligent_autoscaler.config.scale_up_cooldown = request.scale_up_cooldown
        intelligent_autoscaler.config.scale_down_cooldown = request.scale_down_cooldown
        
        return {
            "status": "success",
            "message": "Auto-scaling configuration updated",
            "config": {
                "min_instances": request.min_instances,
                "max_instances": request.max_instances,
                "target_cpu_utilization": request.target_cpu_utilization,
                "target_memory_utilization": request.target_memory_utilization,
                "scale_up_cooldown": request.scale_up_cooldown,
                "scale_down_cooldown": request.scale_down_cooldown
            }
        }
        
    except Exception as e:
        logger.error(f"Auto-scaling configuration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/autoscaling/analytics")
async def get_autoscaling_analytics():
    """Get analytics about auto-scaling performance"""
    try:
        analytics = await intelligent_autoscaler.get_scaling_analytics()
        return analytics
        
    except Exception as e:
        logger.error(f"Failed to get auto-scaling analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/anomaly/detect")
async def detect_anomalies(request: SystemMetricsRequest):
    """Detect anomalies in system metrics"""
    try:
        anomalies = await anomaly_detection_engine.detect_performance_anomalies(request.metrics)
        
        return {
            "anomalies_detected": len(anomalies),
            "anomalies": [
                {
                    "id": a.id,
                    "type": a.type.value,
                    "severity": a.severity.value,
                    "metric": a.metric,
                    "value": a.value,
                    "expected_value": a.expected_value,
                    "deviation": a.deviation,
                    "confidence": a.confidence,
                    "description": a.description,
                    "suggested_actions": a.suggested_actions,
                    "timestamp": a.timestamp.isoformat()
                }
                for a in anomalies
            ],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Anomaly detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/anomaly/predict-issues")
async def predict_potential_issues():
    """Predict potential issues based on trend analysis"""
    try:
        # Use current trend data
        predicted_issues = await anomaly_detection_engine.predict_potential_issues(
            anomaly_detection_engine.trend_data
        )
        
        return {
            "issues_predicted": len(predicted_issues),
            "predicted_issues": [
                {
                    "id": p.id,
                    "issue_type": p.issue_type,
                    "probability": p.probability,
                    "estimated_time": p.estimated_time.isoformat(),
                    "impact_level": p.impact_level,
                    "description": p.description,
                    "prevention_actions": p.prevention_actions,
                    "monitoring_metrics": p.monitoring_metrics
                }
                for p in predicted_issues
            ],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Issue prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/anomaly/analytics")
async def get_anomaly_analytics():
    """Get analytics about anomaly detection performance"""
    try:
        analytics = await anomaly_detection_engine.get_anomaly_analytics()
        return analytics
        
    except Exception as e:
        logger.error(f"Failed to get anomaly analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/intelligence/dashboard")
async def get_intelligence_dashboard():
    """Get comprehensive AI intelligence dashboard data"""
    try:
        # Collect data from all AI systems
        predictive_analytics = await predictive_analytics_engine.get_prediction_analytics()
        autoscaling_analytics = await intelligent_autoscaler.get_scaling_analytics()
        anomaly_analytics = await anomaly_detection_engine.get_anomaly_analytics()
        
        # Get current system state
        current_metrics = await intelligent_autoscaler.collect_system_metrics()
        scaling_decision = await intelligent_autoscaler.analyze_system_load()
        
        return {
            "overview": {
                "timestamp": datetime.now().isoformat(),
                "ai_systems_active": 3,
                "total_predictions": predictive_analytics.get("total_predictions", 0),
                "total_scaling_actions": autoscaling_analytics.get("total_scaling_actions", 0),
                "total_anomalies": anomaly_analytics.get("total_anomalies", 0)
            },
            "current_state": {
                "system_metrics": {
                    "cpu_usage": current_metrics.cpu_usage,
                    "memory_usage": current_metrics.memory_usage,
                    "response_time": current_metrics.response_time,
                    "error_rate": current_metrics.error_rate
                },
                "scaling_recommendation": {
                    "direction": scaling_decision.direction.value,
                    "confidence": scaling_decision.confidence,
                    "reasoning": scaling_decision.reasoning
                },
                "current_instances": autoscaling_analytics.get("current_instances", 1)
            },
            "predictive_analytics": predictive_analytics,
            "autoscaling_analytics": autoscaling_analytics,
            "anomaly_analytics": anomaly_analytics
        }
        
    except Exception as e:
        logger.error(f"Failed to get intelligence dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/intelligence/simulate-workload")
async def simulate_workload_scenario(request: WorkloadProfileRequest):
    """Simulate a workload scenario and get AI recommendations"""
    try:
        workload = WorkloadProfile(
            concurrent_tasks=request.concurrent_tasks,
            task_complexity=request.task_complexity,
            resource_requirements=request.resource_requirements,
            time_constraints=request.time_constraints,
            priority_level=request.priority_level
        )
        
        # Get configuration recommendation
        config = await predictive_analytics_engine.recommend_optimal_configuration(workload)
        
        # Simulate metrics for this workload
        simulated_metrics = {
            "cpu_usage": min(90, workload.concurrent_tasks * workload.task_complexity * 5),
            "memory_usage": min(85, workload.concurrent_tasks * 3 + workload.task_complexity * 2),
            "response_time": workload.task_complexity * (1 + workload.concurrent_tasks / 10),
            "error_rate": max(0, (workload.concurrent_tasks - 20) * 0.1)
        }
        
        # Detect potential anomalies
        anomalies = await anomaly_detection_engine.detect_performance_anomalies(simulated_metrics)
        
        return {
            "workload_profile": {
                "concurrent_tasks": workload.concurrent_tasks,
                "task_complexity": workload.task_complexity,
                "priority_level": workload.priority_level
            },
            "recommended_configuration": {
                "agent_count": config.agent_count,
                "resource_allocation": config.resource_allocation,
                "timeout_settings": config.timeout_settings
            },
            "predicted_metrics": simulated_metrics,
            "potential_anomalies": len(anomalies),
            "recommendations": [
                f"Deploy {config.agent_count} agent instances",
                f"Allocate {config.resource_allocation.get('cpu', 2)} CPU cores",
                f"Set task timeout to {config.timeout_settings.get('task_timeout', 300)} seconds"
            ],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Workload simulation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))