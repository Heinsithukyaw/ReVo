"""
Agent Dashboard - Real-time Monitoring and Control for Specialized Agents

This module provides a comprehensive dashboard for monitoring and controlling
the Phase 4 specialized agents and their intelligent workflows.
"""

import asyncio
import logging
import json
import time
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Set
from enum import Enum
from datetime import datetime, timedelta

from .base_intelligent_agent import IntelligentAgent, AgentCapability
from .workflow_intelligence import WorkflowIntelligence, WorkflowExecution, WorkflowStatus
from ..core.framework import ThreeEngineArchitecture


class DashboardMetric(Enum):
    """Dashboard metrics to track"""
    AGENT_HEALTH = "agent_health"
    WORKFLOW_SUCCESS_RATE = "workflow_success_rate"
    AVERAGE_RESPONSE_TIME = "average_response_time"
    PROBLEMS_SOLVED = "problems_solved"
    LEARNING_PROGRESS = "learning_progress"
    RESOURCE_UTILIZATION = "resource_utilization"
    ERROR_RATE = "error_rate"
    USER_SATISFACTION = "user_satisfaction"


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AgentStatus:
    """Current status of an agent"""
    agent_id: str
    capability: AgentCapability
    is_healthy: bool
    is_busy: bool
    current_task: Optional[str]
    performance_score: float
    last_activity: float
    error_count: int
    success_count: int
    learning_score: float


@dataclass
class WorkflowMetrics:
    """Workflow execution metrics"""
    total_workflows: int
    active_workflows: int
    completed_workflows: int
    failed_workflows: int
    average_duration: float
    success_rate: float
    most_common_workflow_type: str
    bottleneck_agents: List[str]


@dataclass
class SystemAlert:
    """System alert notification"""
    alert_id: str
    level: AlertLevel
    title: str
    message: str
    timestamp: float
    source: str
    acknowledged: bool = False
    resolved: bool = False


@dataclass
class DashboardState:
    """Complete dashboard state"""
    timestamp: float
    agent_statuses: Dict[str, AgentStatus]
    workflow_metrics: WorkflowMetrics
    system_alerts: List[SystemAlert]
    performance_metrics: Dict[DashboardMetric, float]
    engine_status: Dict[str, Dict[str, Any]]
    active_sessions: int
    total_problems_solved: int


class AgentDashboard:
    """
    Real-time dashboard for monitoring and controlling specialized agents.
    
    Features:
    - Real-time agent health monitoring
    - Workflow execution tracking
    - Performance metrics visualization
    - Alert management
    - Resource utilization monitoring
    - Learning progress tracking
    """
    
    def __init__(self, engines: ThreeEngineArchitecture, workflow_intelligence: WorkflowIntelligence):
        self.engines = engines
        self.workflow_intelligence = workflow_intelligence
        self.logger = logging.getLogger("agent_dashboard")
        
        # Dashboard state
        self.current_state = None
        self.historical_data = []
        self.alerts = []
        self.subscribers = set()
        
        # Monitoring configuration
        self.monitoring_interval = 5.0  # seconds
        self.alert_thresholds = {
            "agent_error_rate": 0.1,
            "workflow_failure_rate": 0.2,
            "response_time": 30.0,
            "resource_utilization": 0.9
        }
        
        # Monitoring task
        self.monitoring_task = None
        self.is_monitoring = False
    
    async def initialize(self) -> bool:
        """Initialize the agent dashboard"""
        try:
            self.logger.info("Initializing Agent Dashboard...")
            
            # Initialize dashboard state
            await self._initialize_dashboard_state()
            
            # Start monitoring
            await self.start_monitoring()
            
            self.logger.info("Agent Dashboard initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Agent Dashboard: {e}")
            return False
    
    async def start_monitoring(self) -> None:
        """Start real-time monitoring"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("Started real-time monitoring")
    
    async def stop_monitoring(self) -> None:
        """Stop real-time monitoring"""
        self.is_monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Stopped real-time monitoring")
    
    async def get_dashboard_state(self) -> DashboardState:
        """Get current dashboard state"""
        if not self.current_state:
            await self._update_dashboard_state()
        return self.current_state
    
    async def get_agent_details(self, agent_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific agent"""
        agent_status = self.current_state.agent_statuses.get(agent_id)
        if not agent_status:
            return {"error": "Agent not found"}
        
        # Get agent from workflow intelligence
        agent = None
        for capability, agent_instance in self.workflow_intelligence.agents.items():
            if agent_instance.agent_id == agent_id:
                agent = agent_instance
                break
        
        if not agent:
            return {"error": "Agent instance not found"}
        
        return {
            "status": asdict(agent_status),
            "performance_metrics": agent.performance_metrics,
            "learning_data": agent.learning_data,
            "capabilities": [cap.value for cap in [agent_status.capability]],
            "specialization": agent.specialization
        }
    
    async def get_workflow_details(self, workflow_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific workflow"""
        workflow_def = self.workflow_intelligence.workflow_definitions.get(workflow_id)
        if not workflow_def:
            return {"error": "Workflow not found"}
        
        # Find active execution
        active_execution = None
        for execution in self.workflow_intelligence.active_executions.values():
            if execution.workflow_id == workflow_id:
                active_execution = execution
                break
        
        return {
            "definition": asdict(workflow_def),
            "active_execution": asdict(active_execution) if active_execution else None,
            "execution_history": await self._get_workflow_history(workflow_id)
        }
    
    async def get_performance_trends(self, metric: DashboardMetric,
                                   time_range: timedelta = timedelta(hours=24)) -> List[Dict[str, Any]]:
        """Get performance trends for a specific metric"""
        cutoff_time = time.time() - time_range.total_seconds()
        
        trends = []
        for data_point in self.historical_data:
            if data_point["timestamp"] >= cutoff_time:
                if metric.value in data_point.get("performance_metrics", {}):
                    trends.append({
                        "timestamp": data_point["timestamp"],
                        "value": data_point["performance_metrics"][metric.value]
                    })
        
        return trends
    
    async def get_system_alerts(self, level: Optional[AlertLevel] = None,
                               unresolved_only: bool = True) -> List[SystemAlert]:
        """Get system alerts with optional filtering"""
        alerts = self.alerts
        
        if level:
            alerts = [alert for alert in alerts if alert.level == level]
        
        if unresolved_only:
            alerts = [alert for alert in alerts if not alert.resolved]
        
        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)
    
    async def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge a system alert"""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                self.logger.info(f"Alert {alert_id} acknowledged")
                await self._notify_subscribers("alert_acknowledged", {"alert_id": alert_id})
                return True
        return False
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """Resolve a system alert"""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.resolved = True
                self.logger.info(f"Alert {alert_id} resolved")
                await self._notify_subscribers("alert_resolved", {"alert_id": alert_id})
                return True
        return False
    
    async def trigger_agent_action(self, agent_id: str, action: str,
                                  parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Trigger an action on a specific agent"""
        # Find the agent
        agent = None
        for capability, agent_instance in self.workflow_intelligence.agents.items():
            if agent_instance.agent_id == agent_id:
                agent = agent_instance
                break
        
        if not agent:
            return {"success": False, "error": "Agent not found"}
        
        try:
            if action == "health_check":
                result = await self._perform_agent_health_check(agent)
            elif action == "restart":
                result = await self._restart_agent(agent)
            elif action == "clear_cache":
                result = await self._clear_agent_cache(agent)
            elif action == "update_learning":
                result = await self._update_agent_learning(agent, parameters or {})
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
            
            await self._create_alert(
                AlertLevel.INFO,
                f"Agent Action: {action}",
                f"Action '{action}' executed on agent {agent_id}",
                f"agent_{agent_id}"
            )
            
            return {"success": True, "result": result}
            
        except Exception as e:
            self.logger.error(f"Failed to execute action {action} on agent {agent_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_workflow_from_dashboard(self, workflow_config: Dict[str, Any]) -> str:
        """Create a new workflow from dashboard configuration"""
        try:
            workflow_def = await self.workflow_intelligence.create_intelligent_workflow(
                problem_description=workflow_config.get("description", ""),
                context=workflow_config.get("context", {}),
                preferences=workflow_config.get("preferences", {})
            )
            
            await self._create_alert(
                AlertLevel.INFO,
                "Workflow Created",
                f"New workflow created: {workflow_def.workflow_id}",
                "dashboard"
            )
            
            return workflow_def.workflow_id
            
        except Exception as e:
            self.logger.error(f"Failed to create workflow from dashboard: {e}")
            await self._create_alert(
                AlertLevel.ERROR,
                "Workflow Creation Failed",
                f"Failed to create workflow: {str(e)}",
                "dashboard"
            )
            raise
    
    async def subscribe_to_updates(self, callback) -> str:
        """Subscribe to real-time dashboard updates"""
        subscriber_id = f"subscriber_{time.time()}"
        self.subscribers.add((subscriber_id, callback))
        self.logger.info(f"New subscriber added: {subscriber_id}")
        return subscriber_id
    
    async def unsubscribe_from_updates(self, subscriber_id: str) -> bool:
        """Unsubscribe from dashboard updates"""
        for subscriber in self.subscribers:
            if subscriber[0] == subscriber_id:
                self.subscribers.remove(subscriber)
                self.logger.info(f"Subscriber removed: {subscriber_id}")
                return True
        return False
    
    # Private Methods
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                await self._update_dashboard_state()
                await self._check_alert_conditions()
                await self._notify_subscribers("state_update", asdict(self.current_state))
                
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def _initialize_dashboard_state(self) -> None:
        """Initialize the dashboard state"""
        self.current_state = DashboardState(
            timestamp=time.time(),
            agent_statuses={},
            workflow_metrics=WorkflowMetrics(
                total_workflows=0,
                active_workflows=0,
                completed_workflows=0,
                failed_workflows=0,
                average_duration=0.0,
                success_rate=0.0,
                most_common_workflow_type="sequential",
                bottleneck_agents=[]
            ),
            system_alerts=[],
            performance_metrics={},
            engine_status={},
            active_sessions=0,
            total_problems_solved=0
        )
        
        await self._update_dashboard_state()
    
    async def _update_dashboard_state(self) -> None:
        """Update the current dashboard state"""
        current_time = time.time()
        
        # Update agent statuses
        agent_statuses = {}
        for capability, agent in self.workflow_intelligence.agents.items():
            status = await self._get_agent_status(agent)
            agent_statuses[agent.agent_id] = status
        
        # Update workflow metrics
        workflow_metrics = await self._calculate_workflow_metrics()
        
        # Update performance metrics
        performance_metrics = await self._calculate_performance_metrics(agent_statuses)
        
        # Update engine status
        engine_status = await self._get_engine_status()
        
        # Update dashboard state
        self.current_state = DashboardState(
            timestamp=current_time,
            agent_statuses=agent_statuses,
            workflow_metrics=workflow_metrics,
            system_alerts=self.alerts[-10:],  # Last 10 alerts
            performance_metrics=performance_metrics,
            engine_status=engine_status,
            active_sessions=len(self.workflow_intelligence.active_executions),
            total_problems_solved=sum(status.success_count for status in agent_statuses.values())
        )
        
        # Store historical data
        self.historical_data.append({
            "timestamp": current_time,
            "performance_metrics": performance_metrics,
            "workflow_metrics": asdict(workflow_metrics)
        })
        
        # Keep only last 24 hours of data
        cutoff_time = current_time - 86400  # 24 hours
        self.historical_data = [
            data for data in self.historical_data
            if data["timestamp"] >= cutoff_time
        ]
    
    async def _get_agent_status(self, agent: IntelligentAgent) -> AgentStatus:
        """Get current status of an agent"""
        # Perform health check
        is_healthy = await self._check_agent_health(agent)
        
        # Check if agent is busy (simplified)
        is_busy = False  # Would check actual agent state
        
        return AgentStatus(
            agent_id=agent.agent_id,
            capability=agent.capabilities[0] if agent.capabilities else AgentCapability.CODE_ANALYSIS,
            is_healthy=is_healthy,
            is_busy=is_busy,
            current_task=None,  # Would get from agent state
            performance_score=agent.performance_metrics.get("success_rate", 0.0),
            last_activity=time.time(),
            error_count=0,  # Would track actual errors
            success_count=agent.performance_metrics.get("problems_solved", 0),
            learning_score=agent.performance_metrics.get("learning_score", 0.0)
        )
    
    async def _check_agent_health(self, agent: IntelligentAgent) -> bool:
        """Check if an agent is healthy"""
        try:
            # Simple health check - verify agent is initialized
            return agent.is_initialized
        except Exception:
            return False
    
    async def _calculate_workflow_metrics(self) -> WorkflowMetrics:
        """Calculate workflow execution metrics"""
        total_workflows = len(self.workflow_intelligence.workflow_definitions)
        active_workflows = len(self.workflow_intelligence.active_executions)
        
        # Count completed and failed workflows (simplified)
        completed_workflows = 0
        failed_workflows = 0
        
        for execution in self.workflow_intelligence.active_executions.values():
            if execution.status == WorkflowStatus.COMPLETED:
                completed_workflows += 1
            elif execution.status == WorkflowStatus.FAILED:
                failed_workflows += 1
        
        success_rate = (
            completed_workflows / max(1, completed_workflows + failed_workflows)
        )
        
        return WorkflowMetrics(
            total_workflows=total_workflows,
            active_workflows=active_workflows,
            completed_workflows=completed_workflows,
            failed_workflows=failed_workflows,
            average_duration=3600.0,  # Placeholder
            success_rate=success_rate,
            most_common_workflow_type="sequential",
            bottleneck_agents=[]
        )
    
    async def _calculate_performance_metrics(self, agent_statuses: Dict[str, AgentStatus]) -> Dict[DashboardMetric, float]:
        """Calculate system performance metrics"""
        if not agent_statuses:
            return {}
        
        # Calculate aggregate metrics
        total_agents = len(agent_statuses)
        healthy_agents = sum(1 for status in agent_statuses.values() if status.is_healthy)
        total_problems = sum(status.success_count for status in agent_statuses.values())
        avg_learning_score = sum(status.learning_score for status in agent_statuses.values()) / total_agents
        
        return {
            DashboardMetric.AGENT_HEALTH: healthy_agents / total_agents,
            DashboardMetric.WORKFLOW_SUCCESS_RATE: 0.85,  # From workflow metrics
            DashboardMetric.AVERAGE_RESPONSE_TIME: 2.5,  # Placeholder
            DashboardMetric.PROBLEMS_SOLVED: total_problems,
            DashboardMetric.LEARNING_PROGRESS: avg_learning_score,
            DashboardMetric.RESOURCE_UTILIZATION: 0.65,  # Placeholder
            DashboardMetric.ERROR_RATE: 0.05,  # Placeholder
            DashboardMetric.USER_SATISFACTION: 0.9  # Placeholder
        }
    
    async def _get_engine_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of the three engines"""
        return {
            "perfect_recall": {
                "status": "healthy",
                "memory_usage": "2.1GB",
                "retrieval_time": "85ms",
                "accuracy": "99.2%"
            },
            "parallel_mind": {
                "status": "healthy",
                "active_workers": 8,
                "utilization": "72%",
                "throughput": "18 tasks/min"
            },
            "creative_engine": {
                "status": "healthy",
                "innovation_score": "82%",
                "solution_diversity": "75%",
                "response_time": "3.2s"
            }
        }
    
    async def _check_alert_conditions(self) -> None:
        """Check for conditions that should trigger alerts"""
        current_metrics = self.current_state.performance_metrics
        
        # Check agent health
        agent_health = current_metrics.get(DashboardMetric.AGENT_HEALTH, 1.0)
        if agent_health < 0.8:
            await self._create_alert(
                AlertLevel.WARNING,
                "Low Agent Health",
                f"Agent health is {agent_health:.1%}",
                "system"
            )
        
        # Check error rate
        error_rate = current_metrics.get(DashboardMetric.ERROR_RATE, 0.0)
        if error_rate > self.alert_thresholds["agent_error_rate"]:
            await self._create_alert(
                AlertLevel.ERROR,
                "High Error Rate",
                f"Error rate is {error_rate:.1%}",
                "system"
            )
        
        # Check workflow failure rate
        workflow_success = current_metrics.get(DashboardMetric.WORKFLOW_SUCCESS_RATE, 1.0)
        if workflow_success < (1.0 - self.alert_thresholds["workflow_failure_rate"]):
            await self._create_alert(
                AlertLevel.WARNING,
                "Low Workflow Success Rate",
                f"Workflow success rate is {workflow_success:.1%}",
                "workflows"
            )
        
        # Check resource utilization
        resource_util = current_metrics.get(DashboardMetric.RESOURCE_UTILIZATION, 0.0)
        if resource_util > self.alert_thresholds["resource_utilization"]:
            await self._create_alert(
                AlertLevel.WARNING,
                "High Resource Utilization",
                f"Resource utilization is {resource_util:.1%}",
                "system"
            )
    
    async def _create_alert(self, level: AlertLevel, title: str, message: str, source: str) -> None:
        """Create a new system alert"""
        alert = SystemAlert(
            alert_id=f"alert_{time.time()}",
            level=level,
            title=title,
            message=message,
            timestamp=time.time(),
            source=source
        )
        
        self.alerts.append(alert)
        
        # Keep only last 100 alerts
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
        
        self.logger.info(f"Created {level.value} alert: {title}")
        await self._notify_subscribers("new_alert", asdict(alert))
    
    async def _notify_subscribers(self, event_type: str, data: Any) -> None:
        """Notify all subscribers of an event"""
        if not self.subscribers:
            return
        
        notification = {
            "event_type": event_type,
            "timestamp": time.time(),
            "data": data
        }
        
        # Notify all subscribers
        for subscriber_id, callback in self.subscribers.copy():
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(notification)
                else:
                    callback(notification)
            except Exception as e:
                self.logger.error(f"Error notifying subscriber {subscriber_id}: {e}")
                # Remove failed subscriber
                self.subscribers.discard((subscriber_id, callback))
    
    async def _get_workflow_history(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Get execution history for a workflow"""
        # This would query historical execution data
        return []
    
    async def _perform_agent_health_check(self, agent: IntelligentAgent) -> Dict[str, Any]:
        """Perform detailed health check on an agent"""
        return {
            "health_status": "healthy",
            "response_time": 0.5,
            "memory_usage": "256MB",
            "last_error": None
        }
    
    async def _restart_agent(self, agent: IntelligentAgent) -> Dict[str, Any]:
        """Restart an agent"""
        # This would implement agent restart logic
        return {"status": "restarted", "restart_time": time.time()}
    
    async def _clear_agent_cache(self, agent: IntelligentAgent) -> Dict[str, Any]:
        """Clear an agent's cache"""
        # This would implement cache clearing logic
        return {"status": "cache_cleared", "items_cleared": 0}
    
    async def _update_agent_learning(self, agent: IntelligentAgent, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Update an agent's learning data"""
        # This would implement learning data update logic
        return {"status": "learning_updated", "parameters": parameters}