"""
Health Dashboard for Phase 4 Comprehensive Monitoring

Provides comprehensive system health dashboards with real-time metrics,
performance visualization, and system status overview.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """System health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class ComponentType(Enum):
    """Types of system components"""
    API = "api"
    DATABASE = "database"
    CACHE = "cache"
    QUEUE = "queue"
    STORAGE = "storage"
    EXTERNAL_SERVICE = "external_service"
    MEMORY_ENGINE = "memory_engine"
    AI_ENGINE = "ai_engine"

@dataclass
class ComponentHealth:
    """Health status of a system component"""
    name: str
    component_type: ComponentType
    status: HealthStatus
    response_time_ms: Optional[float]
    error_rate: float
    uptime_percentage: float
    last_check: datetime
    details: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['component_type'] = self.component_type.value
        data['status'] = self.status.value
        data['last_check'] = self.last_check.isoformat()
        return data

@dataclass
class SystemMetricsSummary:
    """Summary of system metrics"""
    cpu_usage_percent: float
    memory_usage_percent: float
    disk_usage_percent: float
    network_io_mbps: float
    active_connections: int
    request_rate_per_second: float
    error_rate_percent: float
    avg_response_time_ms: float
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

@dataclass
class DashboardWidget:
    """Dashboard widget configuration"""
    id: str
    title: str
    widget_type: str
    data_source: str
    config: Dict[str, Any]
    position: Dict[str, int]  # x, y, width, height
    refresh_interval: int  # seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)

class HealthDashboard:
    """
    Comprehensive health dashboard providing real-time system monitoring,
    performance visualization, and health status overview
    """
    
    def __init__(self,
                 update_interval: float = 30.0,
                 history_retention_hours: int = 24):
        self.update_interval = update_interval
        self.history_retention_hours = history_retention_hours
        
        # Dashboard state
        self.component_health: Dict[str, ComponentHealth] = {}
        self.system_metrics_history: List[SystemMetricsSummary] = []
        self.dashboard_widgets: Dict[str, DashboardWidget] = {}
        
        # Data providers
        self.metric_providers: Dict[str, Any] = {}
        self.health_checkers: Dict[str, Any] = {}
        
        # Dashboard configuration
        self.is_running = False
        self.last_update = datetime.now()
        
        # Initialize default widgets
        self._setup_default_widgets()
        
        # Initialize default components
        self._setup_default_components()
        
        logger.info("HealthDashboard initialized")
    
    def _setup_default_widgets(self):
        """Setup default dashboard widgets"""
        default_widgets = [
            DashboardWidget(
                id="system_overview",
                title="System Overview",
                widget_type="metrics_grid",
                data_source="system_metrics",
                config={
                    "metrics": ["cpu_usage_percent", "memory_usage_percent", "disk_usage_percent"],
                    "thresholds": {"warning": 75, "critical": 90}
                },
                position={"x": 0, "y": 0, "width": 6, "height": 4},
                refresh_interval=30
            ),
            DashboardWidget(
                id="api_performance",
                title="API Performance",
                widget_type="line_chart",
                data_source="api_metrics",
                config={
                    "metrics": ["avg_response_time_ms", "request_rate_per_second"],
                    "time_range": "1h"
                },
                position={"x": 6, "y": 0, "width": 6, "height": 4},
                refresh_interval=30
            ),
            DashboardWidget(
                id="error_rates",
                title="Error Rates",
                widget_type="bar_chart",
                data_source="error_metrics",
                config={
                    "metrics": ["error_rate_percent"],
                    "breakdown": "by_endpoint"
                },
                position={"x": 0, "y": 4, "width": 4, "height": 3},
                refresh_interval=60
            ),
            DashboardWidget(
                id="component_health",
                title="Component Health",
                widget_type="status_grid",
                data_source="component_health",
                config={
                    "show_details": True,
                    "group_by": "component_type"
                },
                position={"x": 4, "y": 4, "width": 4, "height": 3},
                refresh_interval=30
            ),
            DashboardWidget(
                id="active_alerts",
                title="Active Alerts",
                widget_type="alert_list",
                data_source="alerts",
                config={
                    "max_items": 10,
                    "severity_filter": ["warning", "critical"]
                },
                position={"x": 8, "y": 4, "width": 4, "height": 3},
                refresh_interval=15
            ),
            DashboardWidget(
                id="performance_trends",
                title="Performance Trends",
                widget_type="trend_chart",
                data_source="performance_trends",
                config={
                    "metrics": ["avg_response_time_ms", "throughput_rps"],
                    "time_range": "24h"
                },
                position={"x": 0, "y": 7, "width": 8, "height": 4},
                refresh_interval=300
            ),
            DashboardWidget(
                id="optimization_recommendations",
                title="Optimization Recommendations",
                widget_type="recommendation_list",
                data_source="optimization_recommendations",
                config={
                    "max_items": 5,
                    "priority_filter": ["high", "critical"]
                },
                position={"x": 8, "y": 7, "width": 4, "height": 4},
                refresh_interval=300
            )
        ]
        
        for widget in default_widgets:
            self.dashboard_widgets[widget.id] = widget
    
    def _setup_default_components(self):
        """Setup default system components for health monitoring"""
        default_components = [
            {
                "name": "api_gateway",
                "component_type": ComponentType.API,
                "health_check_url": "http://localhost:8000/health"
            },
            {
                "name": "backend_api",
                "component_type": ComponentType.API,
                "health_check_url": "http://localhost:8001/health"
            },
            {
                "name": "memory_engine",
                "component_type": ComponentType.MEMORY_ENGINE,
                "health_check_url": "http://localhost:8002/health"
            },
            {
                "name": "postgres_db",
                "component_type": ComponentType.DATABASE,
                "health_check_function": "check_postgres_health"
            },
            {
                "name": "redis_cache",
                "component_type": ComponentType.CACHE,
                "health_check_function": "check_redis_health"
            }
        ]
        
        for component in default_components:
            self.component_health[component["name"]] = ComponentHealth(
                name=component["name"],
                component_type=component["component_type"],
                status=HealthStatus.UNKNOWN,
                response_time_ms=None,
                error_rate=0.0,
                uptime_percentage=100.0,
                last_check=datetime.now(),
                details={}
            )
    
    async def start(self):
        """Start health dashboard monitoring"""
        if self.is_running:
            logger.warning("HealthDashboard already running")
            return
        
        self.is_running = True
        logger.info("Starting HealthDashboard")
        
        # Start background update task
        asyncio.create_task(self._dashboard_update_loop())
    
    async def stop(self):
        """Stop health dashboard monitoring"""
        self.is_running = False
        logger.info("Stopped HealthDashboard")
    
    async def _dashboard_update_loop(self):
        """Main dashboard update loop"""
        while self.is_running:
            try:
                await self._update_dashboard_data()
                await asyncio.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"Error in dashboard update loop: {e}")
                await asyncio.sleep(10)
    
    async def _update_dashboard_data(self):
        """Update all dashboard data"""
        try:
            # Update component health
            await self._update_component_health()
            
            # Update system metrics
            await self._update_system_metrics()
            
            # Clean old data
            await self._cleanup_old_data()
            
            self.last_update = datetime.now()
            logger.debug("Updated dashboard data")
            
        except Exception as e:
            logger.error(f"Error updating dashboard data: {e}")
    
    async def _update_component_health(self):
        """Update health status of all components"""
        for component_name, component in self.component_health.items():
            try:
                health_status = await self._check_component_health(component_name)
                if health_status:
                    self.component_health[component_name] = health_status
            except Exception as e:
                logger.error(f"Error checking health for {component_name}: {e}")
                # Mark as unknown on error
                self.component_health[component_name].status = HealthStatus.UNKNOWN
                self.component_health[component_name].last_check = datetime.now()
    
    async def _check_component_health(self, component_name: str) -> Optional[ComponentHealth]:
        """Check health of a specific component"""
        try:
            if component_name in self.health_checkers:
                checker = self.health_checkers[component_name]
                return await checker()
            
            # Default health check (placeholder)
            component = self.component_health[component_name]
            
            # Simulate health check
            import random
            status = random.choice([HealthStatus.HEALTHY, HealthStatus.WARNING, HealthStatus.CRITICAL])
            response_time = random.uniform(10, 500)  # 10-500ms
            error_rate = random.uniform(0, 0.1)  # 0-10%
            
            return ComponentHealth(
                name=component_name,
                component_type=component.component_type,
                status=status,
                response_time_ms=response_time,
                error_rate=error_rate,
                uptime_percentage=random.uniform(95, 100),
                last_check=datetime.now(),
                details={
                    "last_error": None if status == HealthStatus.HEALTHY else "Simulated error",
                    "version": "1.0.0",
                    "connections": random.randint(1, 100)
                }
            )
            
        except Exception as e:
            logger.error(f"Error in health check for {component_name}: {e}")
            return None
    
    async def _update_system_metrics(self):
        """Update system-level metrics"""
        try:
            # Collect metrics from providers
            metrics = {}
            for provider_name, provider in self.metric_providers.items():
                try:
                    provider_metrics = await provider()
                    if isinstance(provider_metrics, dict):
                        metrics.update(provider_metrics)
                except Exception as e:
                    logger.warning(f"Error getting metrics from {provider_name}: {e}")
            
            # Create system metrics summary
            summary = SystemMetricsSummary(
                cpu_usage_percent=metrics.get('cpu_percent', 0),
                memory_usage_percent=metrics.get('memory_percent', 0),
                disk_usage_percent=metrics.get('disk_percent', 0),
                network_io_mbps=metrics.get('network_io_mbps', 0),
                active_connections=metrics.get('active_connections', 0),
                request_rate_per_second=metrics.get('request_rate_per_second', 0),
                error_rate_percent=metrics.get('error_rate', 0) * 100,
                avg_response_time_ms=metrics.get('avg_response_time_ms', 0),
                timestamp=datetime.now()
            )
            
            self.system_metrics_history.append(summary)
            
        except Exception as e:
            logger.error(f"Error updating system metrics: {e}")
    
    async def _cleanup_old_data(self):
        """Clean up old dashboard data"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=self.history_retention_hours)
            
            # Clean system metrics history
            self.system_metrics_history = [
                metrics for metrics in self.system_metrics_history
                if metrics.timestamp > cutoff_time
            ]
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
    
    def add_metric_provider(self, name: str, provider):
        """Add a metric provider"""
        self.metric_providers[name] = provider
        logger.info(f"Added metric provider: {name}")
    
    def add_health_checker(self, component_name: str, checker):
        """Add a health checker for a component"""
        self.health_checkers[component_name] = checker
        logger.info(f"Added health checker for: {component_name}")
    
    def add_widget(self, widget: DashboardWidget):
        """Add a custom widget to the dashboard"""
        self.dashboard_widgets[widget.id] = widget
        logger.info(f"Added dashboard widget: {widget.title}")
    
    def remove_widget(self, widget_id: str):
        """Remove a widget from the dashboard"""
        if widget_id in self.dashboard_widgets:
            del self.dashboard_widgets[widget_id]
            logger.info(f"Removed dashboard widget: {widget_id}")
    
    def get_dashboard_config(self) -> Dict[str, Any]:
        """Get complete dashboard configuration"""
        return {
            "widgets": {wid: widget.to_dict() for wid, widget in self.dashboard_widgets.items()},
            "update_interval": self.update_interval,
            "last_update": self.last_update.isoformat(),
            "is_running": self.is_running
        }
    
    def get_system_overview(self) -> Dict[str, Any]:
        """Get system overview data"""
        # Calculate overall system health
        component_statuses = [comp.status for comp in self.component_health.values()]
        
        if HealthStatus.CRITICAL in component_statuses:
            overall_status = HealthStatus.CRITICAL
        elif HealthStatus.WARNING in component_statuses:
            overall_status = HealthStatus.WARNING
        elif HealthStatus.UNKNOWN in component_statuses:
            overall_status = HealthStatus.WARNING
        else:
            overall_status = HealthStatus.HEALTHY
        
        # Get latest metrics
        latest_metrics = self.system_metrics_history[-1] if self.system_metrics_history else None
        
        return {
            "overall_status": overall_status.value,
            "total_components": len(self.component_health),
            "healthy_components": len([c for c in self.component_health.values() if c.status == HealthStatus.HEALTHY]),
            "warning_components": len([c for c in self.component_health.values() if c.status == HealthStatus.WARNING]),
            "critical_components": len([c for c in self.component_health.values() if c.status == HealthStatus.CRITICAL]),
            "latest_metrics": latest_metrics.to_dict() if latest_metrics else None,
            "last_update": self.last_update.isoformat()
        }
    
    def get_component_health_data(self) -> Dict[str, Any]:
        """Get component health data for dashboard"""
        return {
            "components": {name: comp.to_dict() for name, comp in self.component_health.items()},
            "summary": {
                "total": len(self.component_health),
                "healthy": len([c for c in self.component_health.values() if c.status == HealthStatus.HEALTHY]),
                "warning": len([c for c in self.component_health.values() if c.status == HealthStatus.WARNING]),
                "critical": len([c for c in self.component_health.values() if c.status == HealthStatus.CRITICAL]),
                "unknown": len([c for c in self.component_health.values() if c.status == HealthStatus.UNKNOWN])
            }
        }
    
    def get_metrics_data(self, time_range_hours: int = 1) -> Dict[str, Any]:
        """Get metrics data for specified time range"""
        cutoff_time = datetime.now() - timedelta(hours=time_range_hours)
        
        filtered_metrics = [
            metrics for metrics in self.system_metrics_history
            if metrics.timestamp > cutoff_time
        ]
        
        if not filtered_metrics:
            return {"status": "no_data"}
        
        return {
            "time_range_hours": time_range_hours,
            "data_points": len(filtered_metrics),
            "metrics": [metrics.to_dict() for metrics in filtered_metrics],
            "summary": {
                "avg_cpu": sum(m.cpu_usage_percent for m in filtered_metrics) / len(filtered_metrics),
                "avg_memory": sum(m.memory_usage_percent for m in filtered_metrics) / len(filtered_metrics),
                "avg_response_time": sum(m.avg_response_time_ms for m in filtered_metrics) / len(filtered_metrics),
                "avg_error_rate": sum(m.error_rate_percent for m in filtered_metrics) / len(filtered_metrics)
            }
        }
    
    def get_widget_data(self, widget_id: str) -> Dict[str, Any]:
        """Get data for a specific widget"""
        if widget_id not in self.dashboard_widgets:
            return {"error": "Widget not found"}
        
        widget = self.dashboard_widgets[widget_id]
        
        # Route to appropriate data source
        if widget.data_source == "system_metrics":
            return self.get_metrics_data(1)  # Last hour
        elif widget.data_source == "component_health":
            return self.get_component_health_data()
        elif widget.data_source == "api_metrics":
            return self._get_api_metrics_data()
        elif widget.data_source == "error_metrics":
            return self._get_error_metrics_data()
        elif widget.data_source == "alerts":
            return self._get_alerts_data()
        elif widget.data_source == "performance_trends":
            return self._get_performance_trends_data()
        elif widget.data_source == "optimization_recommendations":
            return self._get_optimization_recommendations_data()
        else:
            return {"error": "Unknown data source"}
    
    def _get_api_metrics_data(self) -> Dict[str, Any]:
        """Get API metrics data"""
        # Placeholder - would integrate with actual API metrics
        return {
            "endpoints": [
                {"path": "/api/v1/agents", "avg_response_time": 150, "request_rate": 45},
                {"path": "/api/v1/memory", "avg_response_time": 200, "request_rate": 30},
                {"path": "/api/v1/health", "avg_response_time": 50, "request_rate": 10}
            ]
        }
    
    def _get_error_metrics_data(self) -> Dict[str, Any]:
        """Get error metrics data"""
        # Placeholder - would integrate with actual error metrics
        return {
            "error_rates": [
                {"endpoint": "/api/v1/agents", "error_rate": 0.02},
                {"endpoint": "/api/v1/memory", "error_rate": 0.01},
                {"endpoint": "/api/v1/health", "error_rate": 0.0}
            ]
        }
    
    def _get_alerts_data(self) -> Dict[str, Any]:
        """Get alerts data"""
        # Placeholder - would integrate with actual alert manager
        return {
            "active_alerts": [
                {"id": "alert1", "severity": "warning", "title": "High CPU Usage", "timestamp": datetime.now().isoformat()},
                {"id": "alert2", "severity": "critical", "title": "Database Connection Error", "timestamp": datetime.now().isoformat()}
            ]
        }
    
    def _get_performance_trends_data(self) -> Dict[str, Any]:
        """Get performance trends data"""
        # Placeholder - would integrate with actual performance trends
        return {
            "trends": [
                {"metric": "response_time", "direction": "improving", "change_percent": -15.5},
                {"metric": "throughput", "direction": "stable", "change_percent": 2.1},
                {"metric": "error_rate", "direction": "degrading", "change_percent": 25.0}
            ]
        }
    
    def _get_optimization_recommendations_data(self) -> Dict[str, Any]:
        """Get optimization recommendations data"""
        # Placeholder - would integrate with actual optimization recommendations
        return {
            "recommendations": [
                {"id": "opt1", "title": "Optimize Database Queries", "priority": "high", "estimated_impact": "30% performance improvement"},
                {"id": "opt2", "title": "Implement Response Caching", "priority": "medium", "estimated_impact": "20% response time reduction"}
            ]
        }
    
    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get dashboard summary"""
        return {
            "is_running": self.is_running,
            "last_update": self.last_update.isoformat(),
            "update_interval": self.update_interval,
            "total_widgets": len(self.dashboard_widgets),
            "total_components": len(self.component_health),
            "metrics_history_points": len(self.system_metrics_history),
            "metric_providers": len(self.metric_providers),
            "health_checkers": len(self.health_checkers)
        }

# Global instance
_health_dashboard = None

async def get_health_dashboard() -> HealthDashboard:
    """Get or create global health dashboard instance"""
    global _health_dashboard
    if _health_dashboard is None:
        _health_dashboard = HealthDashboard()
    return _health_dashboard