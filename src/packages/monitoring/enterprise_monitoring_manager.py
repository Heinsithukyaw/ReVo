"""
📊 Enterprise Monitoring Manager - Complete Observability Infrastructure
Provides comprehensive monitoring, logging, metrics, and alerting for enterprise deployments.
"""

import asyncio
import json
import time
import uuid
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from collections import defaultdict, deque

import structlog

logger = structlog.get_logger(__name__)

@dataclass
class MetricPoint:
    """Individual metric data point"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    tags: Dict[str, str] = None
    metadata: Dict[str, Any] = None

@dataclass
class Alert:
    """Alert configuration and state"""
    alert_id: str
    name: str
    condition: str
    threshold: float
    severity: str  # critical, warning, info
    enabled: bool = True
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0

@dataclass
class LogEntry:
    """Structured log entry"""
    timestamp: datetime
    level: str
    message: str
    component: str
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    metadata: Dict[str, Any] = None

class MetricsCollector:
    """Collects system and application metrics"""
    
    def __init__(self):
        self.metrics_buffer = deque(maxlen=10000)
        self.collection_interval = 30  # seconds
        self.running = False
        self.collection_thread = None
    
    def start_collection(self):
        """Start metrics collection"""
        self.running = True
        self.collection_thread = threading.Thread(target=self._collect_loop)
        self.collection_thread.daemon = True
        self.collection_thread.start()
        logger.info("📊 Metrics collection started")
    
    def stop_collection(self):
        """Stop metrics collection"""
        self.running = False
        if self.collection_thread:
            self.collection_thread.join()
        logger.info("📊 Metrics collection stopped")
    
    def _collect_loop(self):
        """Main collection loop"""
        while self.running:
            try:
                self._collect_system_metrics()
                time.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
    
    def _collect_system_metrics(self):
        """Collect system performance metrics"""
        timestamp = datetime.utcnow()
        
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        self.add_metric("system.cpu.usage", cpu_percent, "percent", timestamp)
        
        # Memory metrics
        memory = psutil.virtual_memory()
        self.add_metric("system.memory.usage", memory.percent, "percent", timestamp)
        self.add_metric("system.memory.available", memory.available, "bytes", timestamp)
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        self.add_metric("system.disk.usage", (disk.used / disk.total) * 100, "percent", timestamp)
        self.add_metric("system.disk.free", disk.free, "bytes", timestamp)
        
        # Network metrics (if available)
        try:
            network = psutil.net_io_counters()
            self.add_metric("system.network.bytes_sent", network.bytes_sent, "bytes", timestamp)
            self.add_metric("system.network.bytes_recv", network.bytes_recv, "bytes", timestamp)
        except:
            pass
    
    def add_metric(self, name: str, value: float, unit: str, timestamp: datetime = None, tags: Dict[str, str] = None):
        """Add a metric point"""
        metric = MetricPoint(
            name=name,
            value=value,
            unit=unit,
            timestamp=timestamp or datetime.utcnow(),
            tags=tags or {}
        )
        self.metrics_buffer.append(metric)
    
    def get_metrics(self, name_pattern: str = None, since: datetime = None) -> List[MetricPoint]:
        """Get metrics matching criteria"""
        metrics = list(self.metrics_buffer)
        
        if name_pattern:
            metrics = [m for m in metrics if name_pattern in m.name]
        
        if since:
            metrics = [m for m in metrics if m.timestamp >= since]
        
        return metrics

class AlertManager:
    """Manages alerts and notifications"""
    
    def __init__(self):
        self.alerts = {}
        self.alert_history = deque(maxlen=1000)
        self.notification_handlers = []
    
    def add_alert(self, alert: Alert):
        """Add an alert configuration"""
        self.alerts[alert.alert_id] = alert
        logger.info(f"🚨 Alert added: {alert.name}")
    
    def remove_alert(self, alert_id: str):
        """Remove an alert configuration"""
        if alert_id in self.alerts:
            del self.alerts[alert_id]
            logger.info(f"🚨 Alert removed: {alert_id}")
    
    def check_alerts(self, metrics: List[MetricPoint]):
        """Check metrics against alert conditions"""
        for alert in self.alerts.values():
            if not alert.enabled:
                continue
            
            try:
                if self._evaluate_alert_condition(alert, metrics):
                    self._trigger_alert(alert)
            except Exception as e:
                logger.error(f"Alert evaluation error for {alert.name}: {e}")
    
    def _evaluate_alert_condition(self, alert: Alert, metrics: List[MetricPoint]) -> bool:
        """Evaluate if alert condition is met"""
        # Simple threshold-based evaluation
        # In production, this could be more sophisticated
        relevant_metrics = [m for m in metrics if alert.condition in m.name]
        
        if not relevant_metrics:
            return False
        
        latest_metric = max(relevant_metrics, key=lambda m: m.timestamp)
        return latest_metric.value > alert.threshold
    
    def _trigger_alert(self, alert: Alert):
        """Trigger an alert"""
        alert.last_triggered = datetime.utcnow()
        alert.trigger_count += 1
        
        alert_event = {
            "alert_id": alert.alert_id,
            "name": alert.name,
            "severity": alert.severity,
            "triggered_at": alert.last_triggered,
            "trigger_count": alert.trigger_count
        }
        
        self.alert_history.append(alert_event)
        
        # Notify handlers
        for handler in self.notification_handlers:
            try:
                handler(alert_event)
            except Exception as e:
                logger.error(f"Notification handler error: {e}")
        
        logger.warning(f"🚨 Alert triggered: {alert.name} (severity: {alert.severity})")
    
    def add_notification_handler(self, handler: Callable):
        """Add a notification handler"""
        self.notification_handlers.append(handler)

class LogManager:
    """Manages structured logging"""
    
    def __init__(self):
        self.log_buffer = deque(maxlen=10000)
        self.log_handlers = []
    
    def log(self, level: str, message: str, component: str, user_id: str = None, 
            request_id: str = None, metadata: Dict[str, Any] = None):
        """Add a log entry"""
        entry = LogEntry(
            timestamp=datetime.utcnow(),
            level=level,
            message=message,
            component=component,
            user_id=user_id,
            request_id=request_id,
            metadata=metadata or {}
        )
        
        self.log_buffer.append(entry)
        
        # Send to handlers
        for handler in self.log_handlers:
            try:
                handler(entry)
            except Exception as e:
                logger.error(f"Log handler error: {e}")
    
    def add_log_handler(self, handler: Callable):
        """Add a log handler"""
        self.log_handlers.append(handler)
    
    def get_logs(self, level: str = None, component: str = None, 
                 since: datetime = None, limit: int = 100) -> List[LogEntry]:
        """Get logs matching criteria"""
        logs = list(self.log_buffer)
        
        if level:
            logs = [l for l in logs if l.level == level]
        
        if component:
            logs = [l for l in logs if l.component == component]
        
        if since:
            logs = [l for l in logs if l.timestamp >= since]
        
        # Sort by timestamp (newest first) and limit
        logs.sort(key=lambda l: l.timestamp, reverse=True)
        return logs[:limit]

class PerformanceTracker:
    """Tracks application performance metrics"""
    
    def __init__(self):
        self.request_times = defaultdict(list)
        self.error_counts = defaultdict(int)
        self.success_counts = defaultdict(int)
    
    def track_request(self, endpoint: str, duration: float, success: bool = True):
        """Track a request"""
        self.request_times[endpoint].append(duration)
        
        if success:
            self.success_counts[endpoint] += 1
        else:
            self.error_counts[endpoint] += 1
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        stats = {}
        
        for endpoint in self.request_times:
            times = self.request_times[endpoint]
            if times:
                stats[endpoint] = {
                    "avg_response_time": sum(times) / len(times),
                    "min_response_time": min(times),
                    "max_response_time": max(times),
                    "total_requests": len(times),
                    "success_count": self.success_counts[endpoint],
                    "error_count": self.error_counts[endpoint],
                    "success_rate": self.success_counts[endpoint] / (self.success_counts[endpoint] + self.error_counts[endpoint]) if (self.success_counts[endpoint] + self.error_counts[endpoint]) > 0 else 0
                }
        
        return stats

class EnterpriseMonitoringManager:
    """
    📊 Enterprise Monitoring Manager
    
    Provides comprehensive observability with:
    - Real-time metrics collection
    - Structured logging and log aggregation
    - Alert management and notifications
    - Performance tracking and analytics
    - System health monitoring
    - Custom dashboards and reporting
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()
        self.log_manager = LogManager()
        self.performance_tracker = PerformanceTracker()
        
        self.monitoring_enabled = True
        self.health_status = "healthy"
        self.start_time = datetime.utcnow()
        
        logger.info("📊 Enterprise Monitoring Manager initializing...")
    
    async def initialize(self):
        """Initialize monitoring system"""
        try:
            # Start metrics collection
            self.metrics_collector.start_collection()
            
            # Set up default alerts
            await self._setup_default_alerts()
            
            # Set up log handlers
            self._setup_log_handlers()
            
            # Set up notification handlers
            self._setup_notification_handlers()
            
            logger.info("✅ Enterprise Monitoring Manager initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize monitoring: {e}")
            raise
    
    async def _setup_default_alerts(self):
        """Set up default system alerts"""
        default_alerts = [
            Alert(
                alert_id="cpu_high",
                name="High CPU Usage",
                condition="system.cpu.usage",
                threshold=80.0,
                severity="warning"
            ),
            Alert(
                alert_id="memory_high",
                name="High Memory Usage",
                condition="system.memory.usage",
                threshold=85.0,
                severity="warning"
            ),
            Alert(
                alert_id="disk_full",
                name="Disk Space Low",
                condition="system.disk.usage",
                threshold=90.0,
                severity="critical"
            )
        ]
        
        for alert in default_alerts:
            self.alert_manager.add_alert(alert)
    
    def _setup_log_handlers(self):
        """Set up log handlers"""
        def console_log_handler(entry: LogEntry):
            """Console log handler"""
            print(f"[{entry.timestamp}] {entry.level.upper()} - {entry.component}: {entry.message}")
        
        self.log_manager.add_log_handler(console_log_handler)
    
    def _setup_notification_handlers(self):
        """Set up notification handlers"""
        def console_notification_handler(alert_event: Dict[str, Any]):
            """Console notification handler"""
            print(f"🚨 ALERT: {alert_event['name']} - Severity: {alert_event['severity']}")
        
        self.alert_manager.add_notification_handler(console_notification_handler)
    
    # Metrics methods
    def record_metric(self, name: str, value: float, unit: str = "count", tags: Dict[str, str] = None):
        """Record a custom metric"""
        self.metrics_collector.add_metric(name, value, unit, tags=tags)
    
    def get_metrics(self, name_pattern: str = None, since_minutes: int = 60) -> List[Dict[str, Any]]:
        """Get metrics data"""
        since = datetime.utcnow() - timedelta(minutes=since_minutes)
        metrics = self.metrics_collector.get_metrics(name_pattern, since)
        
        return [
            {
                "name": m.name,
                "value": m.value,
                "unit": m.unit,
                "timestamp": m.timestamp.isoformat(),
                "tags": m.tags
            }
            for m in metrics
        ]
    
    # Logging methods
    def log_info(self, message: str, component: str, **kwargs):
        """Log info message"""
        self.log_manager.log("INFO", message, component, **kwargs)
    
    def log_warning(self, message: str, component: str, **kwargs):
        """Log warning message"""
        self.log_manager.log("WARNING", message, component, **kwargs)
    
    def log_error(self, message: str, component: str, **kwargs):
        """Log error message"""
        self.log_manager.log("ERROR", message, component, **kwargs)
    
    def get_logs(self, **kwargs) -> List[Dict[str, Any]]:
        """Get log entries"""
        logs = self.log_manager.get_logs(**kwargs)
        
        return [
            {
                "timestamp": l.timestamp.isoformat(),
                "level": l.level,
                "message": l.message,
                "component": l.component,
                "user_id": l.user_id,
                "request_id": l.request_id,
                "metadata": l.metadata
            }
            for l in logs
        ]
    
    # Performance tracking
    def track_request_performance(self, endpoint: str, duration: float, success: bool = True):
        """Track request performance"""
        self.performance_tracker.track_request(endpoint, duration, success)
        
        # Also record as metric
        self.record_metric(f"api.request.duration", duration, "seconds", {"endpoint": endpoint})
        self.record_metric(f"api.request.count", 1, "count", {"endpoint": endpoint, "status": "success" if success else "error"})
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return self.performance_tracker.get_performance_stats()
    
    # Health monitoring
    async def check_system_health(self) -> Dict[str, Any]:
        """Check overall system health"""
        try:
            health_data = {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
                "components": {}
            }
            
            # Check system resources
            cpu_usage = psutil.cpu_percent()
            memory_usage = psutil.virtual_memory().percent
            disk_usage = psutil.disk_usage('/').used / psutil.disk_usage('/').total * 100
            
            health_data["components"]["system"] = {
                "status": "healthy" if cpu_usage < 90 and memory_usage < 90 and disk_usage < 95 else "degraded",
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
                "disk_usage": disk_usage
            }
            
            # Check recent alerts
            recent_alerts = [a for a in self.alert_manager.alert_history if 
                           (datetime.utcnow() - a["triggered_at"]).total_seconds() < 300]  # Last 5 minutes
            
            if recent_alerts:
                critical_alerts = [a for a in recent_alerts if a["severity"] == "critical"]
                if critical_alerts:
                    health_data["status"] = "critical"
                else:
                    health_data["status"] = "warning"
            
            health_data["recent_alerts"] = len(recent_alerts)
            
            return health_data
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    # Alert management
    def create_alert(self, name: str, condition: str, threshold: float, severity: str = "warning") -> str:
        """Create a new alert"""
        alert_id = str(uuid.uuid4())
        alert = Alert(
            alert_id=alert_id,
            name=name,
            condition=condition,
            threshold=threshold,
            severity=severity
        )
        
        self.alert_manager.add_alert(alert)
        return alert_id
    
    def get_alerts(self) -> List[Dict[str, Any]]:
        """Get all alerts"""
        return [
            {
                "alert_id": alert.alert_id,
                "name": alert.name,
                "condition": alert.condition,
                "threshold": alert.threshold,
                "severity": alert.severity,
                "enabled": alert.enabled,
                "last_triggered": alert.last_triggered.isoformat() if alert.last_triggered else None,
                "trigger_count": alert.trigger_count
            }
            for alert in self.alert_manager.alerts.values()
        ]
    
    # Dashboard data
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        try:
            # Get recent metrics
            metrics = self.get_metrics(since_minutes=60)
            
            # Get recent logs
            logs = self.get_logs(limit=50)
            
            # Get performance stats
            performance = self.get_performance_stats()
            
            # Get health status
            health = await self.check_system_health()
            
            # Get alerts
            alerts = self.get_alerts()
            
            return {
                "health": health,
                "metrics": metrics,
                "logs": logs,
                "performance": performance,
                "alerts": alerts,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get dashboard data: {e}")
            return {"error": str(e)}
    
    # Monitoring control
    def enable_monitoring(self):
        """Enable monitoring"""
        self.monitoring_enabled = True
        logger.info("📊 Monitoring enabled")
    
    def disable_monitoring(self):
        """Disable monitoring"""
        self.monitoring_enabled = False
        logger.info("📊 Monitoring disabled")
    
    async def shutdown(self):
        """Shutdown monitoring system"""
        try:
            self.metrics_collector.stop_collection()
            logger.info("📊 Enterprise Monitoring Manager shutdown complete")
        except Exception as e:
            logger.error(f"Error during monitoring shutdown: {e}")

# Example usage
async def main():
    """Example usage of Enterprise Monitoring Manager"""
    monitoring = EnterpriseMonitoringManager()
    await monitoring.initialize()
    
    # Record some metrics
    monitoring.record_metric("app.requests", 100, "count")
    monitoring.record_metric("app.response_time", 0.5, "seconds")
    
    # Log some events
    monitoring.log_info("Application started", "main")
    monitoring.log_warning("High memory usage detected", "system")
    
    # Track performance
    monitoring.track_request_performance("/api/generate", 1.2, True)
    
    # Get dashboard data
    dashboard = await monitoring.get_dashboard_data()
    print(f"Dashboard data: {json.dumps(dashboard, indent=2, default=str)}")
    
    # Wait a bit then shutdown
    await asyncio.sleep(5)
    await monitoring.shutdown()

if __name__ == "__main__":
    asyncio.run(main())