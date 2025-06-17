#!/usr/bin/env python3
"""
Real-time Team Performance Monitoring Dashboard for reVoAgent
Monitors 100+ AI agents with comprehensive metrics and alerts
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json
import numpy as np
from pathlib import Path
import sys

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from apps.backend.services.ai_team_coordinator import AITeamCoordinator
from apps.backend.services.ai_service import ProductionAIService
from apps.backend.services.cost_optimizer import CostOptimizedRouter

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics for monitoring"""
    timestamp: datetime
    tasks_completed_per_day: Dict[str, int]
    code_quality_scores: Dict[str, float]
    cost_per_feature: Dict[str, float]
    agent_utilization: Dict[str, float]
    response_times: Dict[str, float]
    error_rates: Dict[str, float]
    throughput: float
    efficiency_score: float

@dataclass
class AlertRule:
    """Alert rule configuration"""
    name: str
    metric: str
    threshold: float
    operator: str  # 'gt', 'lt', 'eq'
    severity: str  # 'critical', 'warning', 'info'
    enabled: bool = True
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0

class AITeamMonitoring:
    """
    Real-time AI team performance monitoring system
    
    Features:
    - Real-time metrics collection
    - Performance trend analysis
    - Cost optimization tracking
    - Quality score monitoring
    - Alert system for anomalies
    - Team efficiency calculations
    """
    
    def __init__(self, ai_service: ProductionAIService, team_coordinator: AITeamCoordinator, cost_optimizer: CostOptimizedRouter):
        """Initialize the monitoring system"""
        self.ai_service = ai_service
        self.team_coordinator = team_coordinator
        self.cost_optimizer = cost_optimizer
        
        # Metrics storage
        self.metrics_history: List[PerformanceMetrics] = []
        self.current_metrics = {
            "tasks_completed_per_day": {},
            "code_quality_scores": {},
            "cost_per_feature": {},
            "agent_utilization": {},
            "response_times": {},
            "error_rates": {},
            "throughput": 0.0,
            "efficiency_score": 0.0
        }
        
        # Alert system
        self.alert_rules = self._initialize_alert_rules()
        self.active_alerts: List[Dict[str, Any]] = []
        
        # Performance targets
        self.targets = {
            "development_velocity": 5.0,  # 5x faster than traditional teams
            "cost_efficiency": 0.8,      # 80% savings vs full cloud
            "quality_score": 0.9,        # >90% quality checks passing
            "team_coordination": 0.95,   # >95% coordination success
            "system_stability": 0.995,   # >99.5% uptime
            "ai_model_efficiency": 0.7   # 70% local vs cloud usage
        }
        
        # Monitoring tasks
        self.monitoring_tasks = []
        
        logger.info("📊 AI Team Monitoring Dashboard initialized")
        logger.info(f"🎯 Performance targets: {self.targets}")
    
    def _initialize_alert_rules(self) -> List[AlertRule]:
        """Initialize alert rules for monitoring"""
        return [
            AlertRule(
                name="Low Quality Score",
                metric="quality_score",
                threshold=0.8,
                operator="lt",
                severity="warning"
            ),
            AlertRule(
                name="High Cost Per Feature",
                metric="cost_per_feature",
                threshold=10.0,
                operator="gt",
                severity="warning"
            ),
            AlertRule(
                name="Low Agent Utilization",
                metric="agent_utilization",
                threshold=0.5,
                operator="lt",
                severity="info"
            ),
            AlertRule(
                name="High Error Rate",
                metric="error_rate",
                threshold=0.1,
                operator="gt",
                severity="critical"
            ),
            AlertRule(
                name="Low Throughput",
                metric="throughput",
                threshold=10.0,
                operator="lt",
                severity="warning"
            ),
            AlertRule(
                name="System Instability",
                metric="system_stability",
                threshold=0.99,
                operator="lt",
                severity="critical"
            )
        ]
    
    async def start_monitoring(self):
        """Start the monitoring system"""
        try:
            # Start monitoring tasks
            self.monitoring_tasks = [
                asyncio.create_task(self._collect_metrics()),
                asyncio.create_task(self._process_alerts()),
                asyncio.create_task(self._generate_reports()),
                asyncio.create_task(self._trend_analysis())
            ]
            
            logger.info("🚀 AI Team Monitoring started")
            
        except Exception as e:
            logger.error(f"❌ Failed to start monitoring: {e}")
            raise
    
    async def _collect_metrics(self):
        """Background task to collect performance metrics"""
        while True:
            try:
                await asyncio.sleep(60)  # Collect every minute
                
                # Collect metrics from all services
                team_status = self.team_coordinator.get_team_status()
                ai_performance = self.ai_service.get_performance_summary()
                cost_summary = self.cost_optimizer.get_cost_summary()
                
                # Calculate derived metrics
                current_time = datetime.now()
                
                # Tasks completed per day by agent type
                tasks_per_day = {
                    "claude": team_status["agent_status"]["claude_agents"]["completed_today"],
                    "gemini": team_status["agent_status"]["gemini_agents"]["completed_today"],
                    "openhands": team_status["agent_status"]["openhands_agents"]["completed_today"],
                    "total": sum([
                        team_status["agent_status"]["claude_agents"]["completed_today"],
                        team_status["agent_status"]["gemini_agents"]["completed_today"],
                        team_status["agent_status"]["openhands_agents"]["completed_today"]
                    ])
                }
                
                # Quality scores (mock data for now - would come from quality gates)
                quality_scores = {
                    "overall": np.random.normal(0.9, 0.05),  # Mock: 90% ± 5%
                    "code_generation": np.random.normal(0.88, 0.06),
                    "architecture": np.random.normal(0.92, 0.04),
                    "testing": np.random.normal(0.85, 0.07)
                }
                
                # Cost per feature
                total_cost = cost_summary["cost_metrics"]["total_cost"]
                total_features = tasks_per_day["total"]
                cost_per_feature = {
                    "average": total_cost / max(total_features, 1),
                    "claude": total_cost * 0.4 / max(tasks_per_day["claude"], 1),
                    "gemini": total_cost * 0.3 / max(tasks_per_day["gemini"], 1),
                    "openhands": total_cost * 0.3 / max(tasks_per_day["openhands"], 1)
                }
                
                # Agent utilization
                agent_utilization = {
                    "claude": team_status["agent_status"]["claude_agents"]["active"] / team_status["agent_status"]["claude_agents"]["total"],
                    "gemini": team_status["agent_status"]["gemini_agents"]["active"] / team_status["agent_status"]["gemini_agents"]["total"],
                    "openhands": team_status["agent_status"]["openhands_agents"]["active"] / team_status["agent_status"]["openhands_agents"]["total"],
                    "overall": (team_status["agent_status"]["claude_agents"]["active"] + 
                              team_status["agent_status"]["gemini_agents"]["active"] + 
                              team_status["agent_status"]["openhands_agents"]["active"]) / 100  # Total 100 agents
                }
                
                # Response times (mock data - would come from actual measurements)
                response_times = {
                    "claude": np.random.normal(2.5, 0.5),  # 2.5s ± 0.5s
                    "gemini": np.random.normal(1.8, 0.3),  # 1.8s ± 0.3s
                    "openhands": np.random.normal(3.2, 0.7),  # 3.2s ± 0.7s
                    "average": np.random.normal(2.5, 0.4)
                }
                
                # Error rates
                total_requests = ai_performance["total_requests"]
                failed_requests = ai_performance["failed_requests"]
                error_rates = {
                    "overall": failed_requests / max(total_requests, 1),
                    "claude": np.random.normal(0.02, 0.01),  # 2% ± 1%
                    "gemini": np.random.normal(0.015, 0.008),  # 1.5% ± 0.8%
                    "openhands": np.random.normal(0.025, 0.012)  # 2.5% ± 1.2%
                }
                
                # Throughput (tasks per hour)
                throughput = tasks_per_day["total"] / 24.0  # Convert daily to hourly
                
                # Efficiency score
                efficiency_score = self._calculate_efficiency_score(
                    tasks_per_day, quality_scores, cost_per_feature, agent_utilization
                )
                
                # Update current metrics
                self.current_metrics.update({
                    "tasks_completed_per_day": tasks_per_day,
                    "code_quality_scores": quality_scores,
                    "cost_per_feature": cost_per_feature,
                    "agent_utilization": agent_utilization,
                    "response_times": response_times,
                    "error_rates": error_rates,
                    "throughput": throughput,
                    "efficiency_score": efficiency_score
                })
                
                # Store in history
                metrics = PerformanceMetrics(
                    timestamp=current_time,
                    tasks_completed_per_day=tasks_per_day,
                    code_quality_scores=quality_scores,
                    cost_per_feature=cost_per_feature,
                    agent_utilization=agent_utilization,
                    response_times=response_times,
                    error_rates=error_rates,
                    throughput=throughput,
                    efficiency_score=efficiency_score
                )
                
                self.metrics_history.append(metrics)
                
                # Keep only last 24 hours of metrics
                cutoff_time = current_time - timedelta(hours=24)
                self.metrics_history = [m for m in self.metrics_history if m.timestamp > cutoff_time]
                
                logger.debug(f"📊 Metrics collected - Efficiency: {efficiency_score:.2f}, Throughput: {throughput:.1f}/hr")
                
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(5)
    
    def _calculate_efficiency_score(self, tasks: Dict, quality: Dict, cost: Dict, utilization: Dict) -> float:
        """Calculate overall team efficiency score"""
        
        # Weighted efficiency calculation
        weights = {
            "task_completion": 0.3,
            "quality": 0.25,
            "cost_efficiency": 0.25,
            "utilization": 0.2
        }
        
        # Task completion score (normalized against target)
        task_score = min(1.0, tasks["total"] / 50)  # Target: 50 tasks/day
        
        # Quality score
        quality_score = quality["overall"]
        
        # Cost efficiency score (lower cost = higher score)
        avg_cost = cost["average"]
        cost_score = max(0.0, 1.0 - (avg_cost / 5.0))  # Target: <$5 per feature
        
        # Utilization score
        utilization_score = utilization["overall"]
        
        # Calculate weighted efficiency
        efficiency = (
            task_score * weights["task_completion"] +
            quality_score * weights["quality"] +
            cost_score * weights["cost_efficiency"] +
            utilization_score * weights["utilization"]
        )
        
        return min(1.0, efficiency)
    
    async def _process_alerts(self):
        """Background task to process alerts"""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                current_time = datetime.now()
                
                for rule in self.alert_rules:
                    if not rule.enabled:
                        continue
                    
                    # Get metric value
                    metric_value = self._get_metric_value(rule.metric)
                    
                    if metric_value is None:
                        continue
                    
                    # Check threshold
                    triggered = False
                    if rule.operator == "gt" and metric_value > rule.threshold:
                        triggered = True
                    elif rule.operator == "lt" and metric_value < rule.threshold:
                        triggered = True
                    elif rule.operator == "eq" and abs(metric_value - rule.threshold) < 0.01:
                        triggered = True
                    
                    if triggered:
                        # Check if we should trigger (avoid spam)
                        if rule.last_triggered is None or (current_time - rule.last_triggered).total_seconds() > 300:  # 5 minutes
                            alert = {
                                "rule_name": rule.name,
                                "metric": rule.metric,
                                "value": metric_value,
                                "threshold": rule.threshold,
                                "severity": rule.severity,
                                "timestamp": current_time,
                                "message": f"{rule.name}: {rule.metric} = {metric_value:.3f} (threshold: {rule.threshold})"
                            }
                            
                            self.active_alerts.append(alert)
                            rule.last_triggered = current_time
                            rule.trigger_count += 1
                            
                            logger.warning(f"🚨 ALERT: {alert['message']}")
                
                # Clean up old alerts (keep last 100)
                self.active_alerts = self.active_alerts[-100:]
                
            except Exception as e:
                logger.error(f"Alert processing error: {e}")
                await asyncio.sleep(10)
    
    def _get_metric_value(self, metric_name: str) -> Optional[float]:
        """Get current value for a metric"""
        
        metric_map = {
            "quality_score": lambda: self.current_metrics["code_quality_scores"]["overall"],
            "cost_per_feature": lambda: self.current_metrics["cost_per_feature"]["average"],
            "agent_utilization": lambda: self.current_metrics["agent_utilization"]["overall"],
            "error_rate": lambda: self.current_metrics["error_rates"]["overall"],
            "throughput": lambda: self.current_metrics["throughput"],
            "system_stability": lambda: 1.0 - self.current_metrics["error_rates"]["overall"],  # Derived metric
            "efficiency_score": lambda: self.current_metrics["efficiency_score"]
        }
        
        try:
            if metric_name in metric_map:
                return metric_map[metric_name]()
            return None
        except (KeyError, TypeError):
            return None
    
    async def _generate_reports(self):
        """Background task to generate periodic reports"""
        while True:
            try:
                await asyncio.sleep(3600)  # Generate hourly reports
                
                report = await self.daily_team_report()
                logger.info(f"📈 Hourly Report: {json.dumps(report, indent=2)}")
                
            except Exception as e:
                logger.error(f"Report generation error: {e}")
                await asyncio.sleep(300)
    
    async def _trend_analysis(self):
        """Background task to analyze performance trends"""
        while True:
            try:
                await asyncio.sleep(1800)  # Analyze every 30 minutes
                
                if len(self.metrics_history) < 10:  # Need at least 10 data points
                    await asyncio.sleep(300)
                    continue
                
                trends = self._calculate_trends()
                logger.info(f"📊 Trend Analysis: {json.dumps(trends, indent=2)}")
                
            except Exception as e:
                logger.error(f"Trend analysis error: {e}")
                await asyncio.sleep(300)
    
    def _calculate_trends(self) -> Dict[str, Any]:
        """Calculate performance trends"""
        
        if len(self.metrics_history) < 2:
            return {"error": "Insufficient data for trend analysis"}
        
        # Get recent metrics (last hour)
        recent_metrics = self.metrics_history[-60:]  # Last 60 minutes
        
        # Calculate trends for key metrics
        efficiency_scores = [m.efficiency_score for m in recent_metrics]
        throughput_values = [m.throughput for m in recent_metrics]
        quality_scores = [m.code_quality_scores["overall"] for m in recent_metrics]
        
        trends = {
            "efficiency_trend": self._calculate_trend(efficiency_scores),
            "throughput_trend": self._calculate_trend(throughput_values),
            "quality_trend": self._calculate_trend(quality_scores),
            "data_points": len(recent_metrics),
            "time_range": "last_hour"
        }
        
        return trends
    
    def _calculate_trend(self, values: List[float]) -> Dict[str, Any]:
        """Calculate trend for a series of values"""
        
        if len(values) < 2:
            return {"direction": "unknown", "change": 0.0}
        
        # Simple linear trend calculation
        x = np.arange(len(values))
        y = np.array(values)
        
        # Calculate slope
        slope = np.polyfit(x, y, 1)[0]
        
        # Calculate percentage change
        start_value = values[0]
        end_value = values[-1]
        percent_change = ((end_value - start_value) / start_value) * 100 if start_value != 0 else 0
        
        # Determine direction
        if slope > 0.001:
            direction = "improving"
        elif slope < -0.001:
            direction = "declining"
        else:
            direction = "stable"
        
        return {
            "direction": direction,
            "slope": slope,
            "percent_change": percent_change,
            "current_value": end_value,
            "previous_value": start_value
        }
    
    async def daily_team_report(self) -> Dict[str, Any]:
        """Generate comprehensive daily team report"""
        
        current_time = datetime.now()
        
        # Get current metrics
        team_status = self.team_coordinator.get_team_status()
        cost_summary = self.cost_optimizer.get_cost_summary()
        
        # Calculate performance vs targets
        performance_vs_targets = {}
        for target_name, target_value in self.targets.items():
            current_value = self._get_target_current_value(target_name)
            if current_value is not None:
                performance_vs_targets[target_name] = {
                    "target": target_value,
                    "current": current_value,
                    "achievement": current_value / target_value if target_value > 0 else 0,
                    "status": "✅" if current_value >= target_value else "⚠️"
                }
        
        # Calculate team efficiency
        total_features_completed = sum(self.current_metrics["tasks_completed_per_day"].values())
        average_quality_score = np.mean(list(self.current_metrics["code_quality_scores"].values()))
        cost_savings_vs_cloud = cost_summary["savings_analysis"]["savings_percentage"]
        agent_efficiency = self.current_metrics["agent_utilization"]["overall"]
        
        report = {
            "timestamp": current_time.isoformat(),
            "summary": {
                "total_features_completed": total_features_completed,
                "average_quality_score": average_quality_score,
                "cost_savings_vs_cloud": cost_savings_vs_cloud,
                "agent_efficiency": agent_efficiency,
                "overall_efficiency": self.current_metrics["efficiency_score"]
            },
            "team_performance": {
                "claude_agents": {
                    "completed_today": team_status["agent_status"]["claude_agents"]["completed_today"],
                    "utilization": self.current_metrics["agent_utilization"]["claude"],
                    "avg_response_time": self.current_metrics["response_times"]["claude"],
                    "error_rate": self.current_metrics["error_rates"]["claude"]
                },
                "gemini_agents": {
                    "completed_today": team_status["agent_status"]["gemini_agents"]["completed_today"],
                    "utilization": self.current_metrics["agent_utilization"]["gemini"],
                    "avg_response_time": self.current_metrics["response_times"]["gemini"],
                    "error_rate": self.current_metrics["error_rates"]["gemini"]
                },
                "openhands_agents": {
                    "completed_today": team_status["agent_status"]["openhands_agents"]["completed_today"],
                    "utilization": self.current_metrics["agent_utilization"]["openhands"],
                    "avg_response_time": self.current_metrics["response_times"]["openhands"],
                    "error_rate": self.current_metrics["error_rates"]["openhands"]
                }
            },
            "cost_analysis": cost_summary,
            "quality_metrics": self.current_metrics["code_quality_scores"],
            "performance_vs_targets": performance_vs_targets,
            "active_alerts": len(self.active_alerts),
            "system_health": "healthy" if self.current_metrics["efficiency_score"] > 0.8 else "needs_attention"
        }
        
        return report
    
    def _get_target_current_value(self, target_name: str) -> Optional[float]:
        """Get current value for a performance target"""
        
        target_map = {
            "development_velocity": lambda: self.current_metrics["tasks_completed_per_day"]["total"] / 10,  # Normalize to traditional baseline
            "cost_efficiency": lambda: self.cost_optimizer.get_cost_summary()["savings_analysis"]["savings_percentage"],
            "quality_score": lambda: self.current_metrics["code_quality_scores"]["overall"],
            "team_coordination": lambda: 1.0 - self.current_metrics["error_rates"]["overall"],  # Inverse of error rate
            "system_stability": lambda: 1.0 - self.current_metrics["error_rates"]["overall"],
            "ai_model_efficiency": lambda: self.cost_optimizer.get_cost_summary()["routing_performance"]["local_usage_percentage"]
        }
        
        try:
            if target_name in target_map:
                return target_map[target_name]()
            return None
        except (KeyError, TypeError, ZeroDivisionError):
            return None
    
    def get_real_time_dashboard(self) -> Dict[str, Any]:
        """Get real-time dashboard data"""
        
        return {
            "current_metrics": self.current_metrics,
            "active_alerts": self.active_alerts[-10:],  # Last 10 alerts
            "team_status": self.team_coordinator.get_team_status(),
            "cost_summary": self.cost_optimizer.get_cost_summary(),
            "performance_targets": self.targets,
            "system_health": {
                "efficiency_score": self.current_metrics["efficiency_score"],
                "throughput": self.current_metrics["throughput"],
                "quality_score": self.current_metrics["code_quality_scores"]["overall"],
                "cost_per_feature": self.current_metrics["cost_per_feature"]["average"],
                "agent_utilization": self.current_metrics["agent_utilization"]["overall"]
            },
            "trends": self._calculate_trends() if len(self.metrics_history) > 10 else None
        }
    
    def add_alert_rule(self, rule: AlertRule):
        """Add a new alert rule"""
        self.alert_rules.append(rule)
        logger.info(f"🚨 Added alert rule: {rule.name}")
    
    def update_targets(self, new_targets: Dict[str, float]):
        """Update performance targets"""
        self.targets.update(new_targets)
        logger.info(f"🎯 Updated targets: {new_targets}")
    
    async def shutdown(self):
        """Gracefully shutdown the monitoring system"""
        logger.info("🛑 Shutting down AI Team Monitoring...")
        
        # Cancel monitoring tasks
        for task in self.monitoring_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
        
        logger.info("✅ AI Team Monitoring shutdown complete")

# Daily success metrics as defined in the plan
DAILY_SUCCESS_METRICS = {
    "development_velocity": "features_per_day_per_agent",
    "cost_efficiency": "cost_per_feature_vs_baseline", 
    "quality_score": "automated_quality_score",
    "team_coordination": "inter_agent_collaboration_success_rate",
    "system_stability": "uptime_percentage",
    "ai_model_efficiency": "local_vs_cloud_usage_ratio"
}

# Success targets as defined in the plan
SUCCESS_TARGETS = {
    "development_velocity": 5.0,  # 5x faster than traditional teams
    "cost_efficiency": 0.8,      # 80% savings vs full cloud deployment  
    "quality_score": 0.9,        # >90% automated quality checks passing
    "system_stability": 0.995,   # >99.5% uptime
    "ai_model_efficiency": 0.7   # 70% local vs cloud usage ratio
}