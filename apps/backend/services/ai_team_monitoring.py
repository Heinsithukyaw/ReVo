#!/usr/bin/env python3
"""
AI Team Monitoring Dashboard for reVoAgent
Real-time performance monitoring for 100-agent team
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

from .ai_team_coordinator import AITeamCoordinator, AgentType, TaskStatus
from .cost_optimizer import CostOptimizedRouter
from .quality_gates import QualityGates

logger = logging.getLogger(__name__)

@dataclass
class TeamPerformanceMetrics:
    """Team performance metrics"""
    timestamp: datetime
    total_agents: int
    active_agents: int
    tasks_completed_today: int
    tasks_in_progress: int
    average_completion_time: float
    team_efficiency: float
    cost_per_feature: float
    quality_score: float
    agent_utilization: float
    
    # Agent type breakdown
    claude_metrics: Dict[str, Any] = field(default_factory=dict)
    gemini_metrics: Dict[str, Any] = field(default_factory=dict)
    openhands_metrics: Dict[str, Any] = field(default_factory=dict)
    
    # Cost metrics
    daily_cost: float = 0.0
    cost_savings: float = 0.0
    local_usage_ratio: float = 0.0

@dataclass
class DailyTeamReport:
    """Daily team performance report"""
    date: datetime
    total_features_completed: int
    average_quality_score: float
    cost_savings_vs_cloud: float
    agent_efficiency: float
    top_performing_agents: List[str]
    issues_identified: List[str]
    recommendations: List[str]

class AITeamMonitoring:
    """
    Real-time AI team performance monitoring system
    
    Features:
    - Real-time metrics collection
    - Performance trend analysis
    - Cost optimization tracking
    - Quality monitoring
    - Agent efficiency analysis
    - Automated reporting
    """
    
    def __init__(self, coordinator: AITeamCoordinator, cost_optimizer: CostOptimizedRouter, quality_gates: QualityGates):
        """Initialize the monitoring system"""
        self.coordinator = coordinator
        self.cost_optimizer = cost_optimizer
        self.quality_gates = quality_gates
        
        # Performance metrics storage
        self.metrics_history: List[TeamPerformanceMetrics] = []
        self.daily_reports: List[DailyTeamReport] = []
        
        # Real-time metrics
        self.current_metrics = {
            "tasks_completed_per_day": {},
            "code_quality_scores": {},
            "cost_per_feature": {},
            "agent_utilization": {},
            "response_times": {},
            "error_rates": {}
        }
        
        # Performance targets
        self.targets = {
            "development_velocity": 5.0,  # features per day per agent
            "cost_efficiency": 0.95,      # 95% cost savings
            "quality_score": 0.90,        # 90% quality score
            "team_coordination": 0.95,    # 95% coordination success
            "system_stability": 0.995,    # 99.5% uptime
            "ai_model_efficiency": 0.70   # 70% local model usage
        }
        
        # Monitoring tasks
        self.monitoring_tasks = []
        
        logger.info("📊 AI Team Monitoring system initialized")
        logger.info(f"🎯 Performance targets: {self.targets}")
    
    async def start_monitoring(self):
        """Start real-time monitoring"""
        try:
            self.monitoring_tasks = [
                asyncio.create_task(self._collect_real_time_metrics()),
                asyncio.create_task(self._analyze_performance_trends()),
                asyncio.create_task(self._monitor_cost_efficiency()),
                asyncio.create_task(self._track_quality_metrics()),
                asyncio.create_task(self._generate_alerts()),
                asyncio.create_task(self._create_daily_reports())
            ]
            
            logger.info("🚀 AI Team Monitoring started")
            
        except Exception as e:
            logger.error(f"❌ Failed to start monitoring: {e}")
            raise
    
    async def _collect_real_time_metrics(self):
        """Collect real-time performance metrics"""
        while True:
            try:
                await asyncio.sleep(60)  # Collect every minute
                
                # Get current team status
                team_status = self.coordinator.get_team_status()
                cost_summary = self.cost_optimizer.get_cost_summary()
                quality_summary = self.quality_gates.get_validation_summary()
                
                # Calculate current metrics
                current_time = datetime.now()
                
                metrics = TeamPerformanceMetrics(
                    timestamp=current_time,
                    total_agents=team_status["team_metrics"]["total_agents"],
                    active_agents=team_status["team_metrics"]["active_agents"],
                    tasks_completed_today=team_status["team_metrics"]["tasks_completed_today"],
                    tasks_in_progress=team_status["team_metrics"]["tasks_in_progress"],
                    average_completion_time=team_status["team_metrics"].get("average_completion_time", 0.0),
                    team_efficiency=team_status["team_metrics"].get("team_efficiency", 0.0),
                    cost_per_feature=cost_summary.get("cost_per_task", 0.0),
                    quality_score=quality_summary["validation_stats"]["average_quality_score"] / 100.0,
                    agent_utilization=self._calculate_agent_utilization(team_status),
                    claude_metrics=team_status["agent_summary"]["claude_agents"],
                    gemini_metrics=team_status["agent_summary"]["gemini_agents"],
                    openhands_metrics=team_status["agent_summary"]["openhands_agents"],
                    daily_cost=cost_summary.get("daily_cost", 0.0),
                    cost_savings=cost_summary.get("cost_savings", 0.0),
                    local_usage_ratio=cost_summary.get("local_usage_percentage", 0.0)
                )
                
                # Store metrics
                self.metrics_history.append(metrics)
                
                # Keep only last 24 hours of minute-level data
                cutoff_time = current_time - timedelta(hours=24)
                self.metrics_history = [
                    m for m in self.metrics_history 
                    if m.timestamp > cutoff_time
                ]
                
                # Update current metrics
                await self._update_current_metrics(metrics)
                
            except Exception as e:
                logger.error(f"❌ Metrics collection error: {e}")
                await asyncio.sleep(5)
    
    def _calculate_agent_utilization(self, team_status: Dict[str, Any]) -> float:
        """Calculate overall agent utilization"""
        total_agents = team_status["team_metrics"]["total_agents"]
        active_agents = team_status["team_metrics"]["active_agents"]
        
        if total_agents == 0:
            return 0.0
        
        # Calculate based on active agents and current workload
        utilization = active_agents / total_agents
        
        # Adjust for current workload
        tasks_in_progress = team_status["team_metrics"]["tasks_in_progress"]
        if tasks_in_progress > 0:
            utilization = min(utilization * 1.2, 1.0)  # Boost for active work
        
        return utilization
    
    async def _update_current_metrics(self, metrics: TeamPerformanceMetrics):
        """Update current metrics tracking"""
        today = metrics.timestamp.date()
        
        # Update daily metrics
        if today not in self.current_metrics["tasks_completed_per_day"]:
            self.current_metrics["tasks_completed_per_day"][today] = 0
        
        self.current_metrics["tasks_completed_per_day"][today] = metrics.tasks_completed_today
        self.current_metrics["code_quality_scores"][today] = metrics.quality_score
        self.current_metrics["cost_per_feature"][today] = metrics.cost_per_feature
        self.current_metrics["agent_utilization"][today] = metrics.agent_utilization
    
    async def _analyze_performance_trends(self):
        """Analyze performance trends and patterns"""
        while True:
            try:
                await asyncio.sleep(300)  # Analyze every 5 minutes
                
                if len(self.metrics_history) < 10:
                    continue
                
                # Get recent metrics
                recent_metrics = self.metrics_history[-10:]
                
                # Analyze trends
                trends = await self._calculate_trends(recent_metrics)
                
                # Log significant trends
                for metric, trend in trends.items():
                    if abs(trend) > 0.1:  # 10% change
                        direction = "📈" if trend > 0 else "📉"
                        logger.info(f"{direction} {metric}: {trend:+.1%} trend")
                
            except Exception as e:
                logger.error(f"❌ Trend analysis error: {e}")
                await asyncio.sleep(60)
    
    async def _calculate_trends(self, metrics: List[TeamPerformanceMetrics]) -> Dict[str, float]:
        """Calculate performance trends"""
        if len(metrics) < 2:
            return {}
        
        # Calculate trends for key metrics
        trends = {}
        
        # Team efficiency trend
        efficiency_values = [m.team_efficiency for m in metrics]
        trends["team_efficiency"] = self._calculate_trend(efficiency_values)
        
        # Quality score trend
        quality_values = [m.quality_score for m in metrics]
        trends["quality_score"] = self._calculate_trend(quality_values)
        
        # Cost efficiency trend
        cost_values = [m.cost_per_feature for m in metrics if m.cost_per_feature > 0]
        if cost_values:
            trends["cost_efficiency"] = -self._calculate_trend(cost_values)  # Lower cost is better
        
        # Agent utilization trend
        utilization_values = [m.agent_utilization for m in metrics]
        trends["agent_utilization"] = self._calculate_trend(utilization_values)
        
        return trends
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend as percentage change"""
        if len(values) < 2:
            return 0.0
        
        # Simple linear trend calculation
        x = np.arange(len(values))
        y = np.array(values)
        
        if np.std(y) == 0:
            return 0.0
        
        # Calculate correlation coefficient as trend indicator
        correlation = np.corrcoef(x, y)[0, 1]
        
        # Convert to percentage change
        if not np.isnan(correlation):
            return correlation * (y[-1] - y[0]) / y[0] if y[0] != 0 else 0.0
        
        return 0.0
    
    async def _monitor_cost_efficiency(self):
        """Monitor cost efficiency and savings"""
        while True:
            try:
                await asyncio.sleep(600)  # Check every 10 minutes
                
                cost_summary = self.cost_optimizer.get_cost_summary()
                
                # Check if we're meeting cost targets
                savings_target = self.targets["cost_efficiency"]
                actual_savings = cost_summary.get("savings_vs_target", {}).get("actual_savings", 0.0)
                
                if actual_savings < savings_target * 0.9:  # 90% of target
                    logger.warning(f"💸 Cost savings below target: {actual_savings:.1%} vs {savings_target:.1%}")
                
                # Check local model usage
                local_usage = cost_summary.get("local_usage_percentage", 0.0)
                local_target = self.targets["ai_model_efficiency"]
                
                if local_usage < local_target * 0.9:
                    logger.warning(f"🤖 Local model usage below target: {local_usage:.1%} vs {local_target:.1%}")
                
            except Exception as e:
                logger.error(f"❌ Cost monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _track_quality_metrics(self):
        """Track code quality metrics"""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                quality_summary = self.quality_gates.get_validation_summary()
                
                # Check quality targets
                success_rate = quality_summary.get("success_rate", 0.0)
                quality_target = self.targets["quality_score"]
                
                if success_rate < quality_target * 0.9:
                    logger.warning(f"🔍 Quality score below target: {success_rate:.1%} vs {quality_target:.1%}")
                
                # Identify top performing agents
                top_agents = quality_summary.get("top_performing_agents", [])
                if top_agents:
                    logger.info(f"🏆 Top performing agents: {[agent[0] for agent in top_agents[:3]]}")
                
            except Exception as e:
                logger.error(f"❌ Quality monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _generate_alerts(self):
        """Generate alerts for performance issues"""
        while True:
            try:
                await asyncio.sleep(180)  # Check every 3 minutes
                
                if not self.metrics_history:
                    continue
                
                latest_metrics = self.metrics_history[-1]
                
                # Check for performance issues
                alerts = []
                
                # Low agent utilization
                if latest_metrics.agent_utilization < 0.5:
                    alerts.append("🚨 Low agent utilization detected")
                
                # High error rate (if available)
                if latest_metrics.team_efficiency < 0.7:
                    alerts.append("🚨 Low team efficiency detected")
                
                # Quality issues
                if latest_metrics.quality_score < 0.8:
                    alerts.append("🚨 Quality score below threshold")
                
                # Cost overruns
                if latest_metrics.daily_cost > 100:  # Daily budget
                    alerts.append("🚨 Daily cost budget exceeded")
                
                # Log alerts
                for alert in alerts:
                    logger.warning(alert)
                
            except Exception as e:
                logger.error(f"❌ Alert generation error: {e}")
                await asyncio.sleep(60)
    
    async def _create_daily_reports(self):
        """Create daily performance reports"""
        while True:
            try:
                # Wait until end of day or start of new day
                now = datetime.now()
                next_report_time = now.replace(hour=23, minute=59, second=0, microsecond=0)
                
                if now > next_report_time:
                    next_report_time += timedelta(days=1)
                
                sleep_seconds = (next_report_time - now).total_seconds()
                await asyncio.sleep(sleep_seconds)
                
                # Generate daily report
                report = await self.daily_team_report()
                self.daily_reports.append(report)
                
                # Keep only last 30 days
                cutoff_date = datetime.now() - timedelta(days=30)
                self.daily_reports = [
                    r for r in self.daily_reports 
                    if r.date > cutoff_date
                ]
                
                logger.info(f"📊 Daily report generated: {report.total_features_completed} features completed")
                
            except Exception as e:
                logger.error(f"❌ Daily report error: {e}")
                await asyncio.sleep(3600)  # Retry in 1 hour
    
    async def daily_team_report(self) -> DailyTeamReport:
        """Generate daily team performance report"""
        today = datetime.now().date()
        
        # Get today's metrics
        today_metrics = [
            m for m in self.metrics_history 
            if m.timestamp.date() == today
        ]
        
        if not today_metrics:
            # Return empty report if no data
            return DailyTeamReport(
                date=datetime.now(),
                total_features_completed=0,
                average_quality_score=0.0,
                cost_savings_vs_cloud=0.0,
                agent_efficiency=0.0,
                top_performing_agents=[],
                issues_identified=[],
                recommendations=[]
            )
        
        # Calculate daily aggregates
        latest_metrics = today_metrics[-1]
        
        # Get cost and quality summaries
        cost_summary = self.cost_optimizer.get_cost_summary()
        quality_summary = self.quality_gates.get_validation_summary()
        
        # Calculate metrics
        total_features = latest_metrics.tasks_completed_today
        avg_quality = latest_metrics.quality_score
        cost_savings = cost_summary.get("savings_vs_target", {}).get("actual_savings", 0.0)
        agent_efficiency = latest_metrics.team_efficiency
        
        # Get top performing agents
        top_agents = [
            agent[0] for agent in quality_summary.get("top_performing_agents", [])[:5]
        ]
        
        # Identify issues
        issues = []
        if avg_quality < self.targets["quality_score"]:
            issues.append(f"Quality score below target: {avg_quality:.1%}")
        
        if cost_savings < self.targets["cost_efficiency"]:
            issues.append(f"Cost savings below target: {cost_savings:.1%}")
        
        if agent_efficiency < 0.8:
            issues.append(f"Team efficiency below optimal: {agent_efficiency:.1%}")
        
        # Generate recommendations
        recommendations = []
        if issues:
            if avg_quality < self.targets["quality_score"]:
                recommendations.append("Increase code review frequency and quality gate enforcement")
            
            if cost_savings < self.targets["cost_efficiency"]:
                recommendations.append("Increase local model usage and optimize cloud routing")
            
            if agent_efficiency < 0.8:
                recommendations.append("Review task allocation and agent workload distribution")
        else:
            recommendations.append("Team performance is meeting all targets - maintain current practices")
        
        return DailyTeamReport(
            date=datetime.now(),
            total_features_completed=total_features,
            average_quality_score=avg_quality,
            cost_savings_vs_cloud=cost_savings,
            agent_efficiency=agent_efficiency,
            top_performing_agents=top_agents,
            issues_identified=issues,
            recommendations=recommendations
        )
    
    async def get_real_time_dashboard(self) -> Dict[str, Any]:
        """Get real-time dashboard data"""
        if not self.metrics_history:
            return {"error": "No metrics available"}
        
        latest_metrics = self.metrics_history[-1]
        cost_summary = self.cost_optimizer.get_cost_summary()
        quality_summary = self.quality_gates.get_validation_summary()
        
        # Calculate performance vs targets
        performance_vs_targets = {}
        for metric, target in self.targets.items():
            if metric == "development_velocity":
                current = latest_metrics.tasks_completed_today / max(latest_metrics.active_agents, 1)
                performance_vs_targets[metric] = {
                    "current": current,
                    "target": target,
                    "percentage": (current / target) if target > 0 else 0.0
                }
            elif metric == "cost_efficiency":
                current = cost_summary.get("savings_vs_target", {}).get("actual_savings", 0.0)
                performance_vs_targets[metric] = {
                    "current": current,
                    "target": target,
                    "percentage": (current / target) if target > 0 else 0.0
                }
            elif metric == "quality_score":
                current = latest_metrics.quality_score
                performance_vs_targets[metric] = {
                    "current": current,
                    "target": target,
                    "percentage": (current / target) if target > 0 else 0.0
                }
        
        # Get recent trends
        recent_trends = await self._get_recent_trends()
        
        return {
            "timestamp": latest_metrics.timestamp.isoformat(),
            "team_overview": {
                "total_agents": latest_metrics.total_agents,
                "active_agents": latest_metrics.active_agents,
                "agent_utilization": latest_metrics.agent_utilization,
                "tasks_completed_today": latest_metrics.tasks_completed_today,
                "tasks_in_progress": latest_metrics.tasks_in_progress
            },
            "performance_metrics": {
                "team_efficiency": latest_metrics.team_efficiency,
                "average_completion_time": latest_metrics.average_completion_time,
                "quality_score": latest_metrics.quality_score,
                "cost_per_feature": latest_metrics.cost_per_feature
            },
            "cost_metrics": {
                "daily_cost": latest_metrics.daily_cost,
                "cost_savings": latest_metrics.cost_savings,
                "local_usage_ratio": latest_metrics.local_usage_ratio,
                "budget_status": cost_summary.get("budget_status", {})
            },
            "agent_breakdown": {
                "claude_agents": latest_metrics.claude_metrics,
                "gemini_agents": latest_metrics.gemini_metrics,
                "openhands_agents": latest_metrics.openhands_metrics
            },
            "performance_vs_targets": performance_vs_targets,
            "recent_trends": recent_trends,
            "quality_summary": quality_summary
        }
    
    async def _get_recent_trends(self) -> Dict[str, Any]:
        """Get recent performance trends"""
        if len(self.metrics_history) < 10:
            return {}
        
        recent_metrics = self.metrics_history[-10:]
        trends = await self._calculate_trends(recent_metrics)
        
        return {
            "trend_period": "last_10_measurements",
            "trends": trends
        }
    
    async def shutdown(self):
        """Gracefully shutdown monitoring"""
        logger.info("🛑 Shutting down AI Team Monitoring...")
        
        # Cancel monitoring tasks
        for task in self.monitoring_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
        
        logger.info("✅ AI Team Monitoring shutdown complete")

# Daily success metrics configuration
DAILY_SUCCESS_METRICS = {
    "development_velocity": "features_per_day_per_agent",
    "cost_efficiency": "cost_per_feature_vs_baseline",
    "quality_score": "automated_quality_score",
    "team_coordination": "inter_agent_collaboration_success_rate",
    "system_stability": "uptime_percentage",
    "ai_model_efficiency": "local_vs_cloud_usage_ratio"
}

# Success targets
SUCCESS_TARGETS = {
    "development_velocity": 5.0,  # 5x faster than traditional teams
    "cost_efficiency": 0.80,     # 80% savings vs full cloud deployment  
    "quality_score": 0.90,       # >90% automated quality checks passing
    "system_stability": 0.995,   # >99.5% uptime
    "ai_model_efficiency": 0.70  # 70% local model usage
}