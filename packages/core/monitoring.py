"""
Production Monitoring and Alerting System

Features:
- Prometheus metrics collection
- Health check aggregation
- Alert management and notification
- Performance monitoring
- SLA tracking
- Custom dashboards support
"""

import asyncio
import time
import logging
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json
import os
from collections import defaultdict, deque

try:
    from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry, generate_latest
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    Counter = Histogram = Gauge = Info = CollectorRegistry = None

from .logging_config import get_logger

logger = get_logger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Alert status."""
    ACTIVE = "active"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"


@dataclass
class Alert:
    """Alert definition."""
    id: str
    name: str
    description: str
    severity: AlertSeverity
    status: AlertStatus = AlertStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthCheckResult:
    """Health check result."""
    service_name: str
    status: str  # healthy, degraded, unhealthy
    response_time: float
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class MetricDefinition:
    """Metric definition for monitoring."""
    name: str
    metric_type: str  # counter, histogram, gauge, info
    description: str
    labels: List[str] = field(default_factory=list)


class PrometheusMetrics:
    """Prometheus metrics collector."""
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        if not PROMETHEUS_AVAILABLE:
            logger.warning("Prometheus client not available. Install with: pip install prometheus-client")
            self.enabled = False
            return
        
        self.enabled = True
        self.registry = registry or CollectorRegistry()
        self.metrics = {}
        
        # Initialize core metrics
        self._initialize_core_metrics()
        
        logger.info("Prometheus metrics initialized")
    
    def _initialize_core_metrics(self):
        """Initialize core application metrics."""
        if not self.enabled:
            return
        
        # Request metrics
        self.metrics['http_requests_total'] = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status_code'],
            registry=self.registry
        )
        
        self.metrics['http_request_duration_seconds'] = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        # AI service metrics
        self.metrics['ai_requests_total'] = Counter(
            'ai_requests_total',
            'Total AI service requests',
            ['model', 'status'],
            registry=self.registry
        )
        
        self.metrics['ai_request_duration_seconds'] = Histogram(
            'ai_request_duration_seconds',
            'AI request duration in seconds',
            ['model'],
            registry=self.registry
        )
        
        self.metrics['ai_tokens_total'] = Counter(
            'ai_tokens_total',
            'Total AI tokens processed',
            ['model', 'type'],  # type: prompt, completion
            registry=self.registry
        )
        
        # Rate limiting metrics
        self.metrics['rate_limit_requests_total'] = Counter(
            'rate_limit_requests_total',
            'Total rate limit checks',
            ['rule', 'result'],  # result: allowed, blocked
            registry=self.registry
        )
        
        # Circuit breaker metrics
        self.metrics['circuit_breaker_state'] = Gauge(
            'circuit_breaker_state',
            'Circuit breaker state (0=closed, 1=open, 2=half-open)',
            ['circuit_name'],
            registry=self.registry
        )
        
        self.metrics['circuit_breaker_requests_total'] = Counter(
            'circuit_breaker_requests_total',
            'Total circuit breaker requests',
            ['circuit_name', 'result'],  # result: success, failure, rejected
            registry=self.registry
        )
        
        # Database metrics
        self.metrics['database_connections_active'] = Gauge(
            'database_connections_active',
            'Active database connections',
            registry=self.registry
        )
        
        self.metrics['database_query_duration_seconds'] = Histogram(
            'database_query_duration_seconds',
            'Database query duration in seconds',
            registry=self.registry
        )
        
        # System metrics
        self.metrics['system_memory_usage_bytes'] = Gauge(
            'system_memory_usage_bytes',
            'System memory usage in bytes',
            ['type'],  # type: used, available, total
            registry=self.registry
        )
        
        self.metrics['system_cpu_usage_percent'] = Gauge(
            'system_cpu_usage_percent',
            'System CPU usage percentage',
            registry=self.registry
        )
        
        # Application info
        self.metrics['application_info'] = Info(
            'application_info',
            'Application information',
            registry=self.registry
        )
        
        # Set application info
        self.metrics['application_info'].info({
            'version': '2.0.0',
            'name': 'reVoAgent',
            'environment': os.getenv('ENVIRONMENT', 'development')
        })
    
    def increment_counter(self, metric_name: str, labels: Dict[str, str] = None, value: float = 1):
        """Increment a counter metric."""
        if not self.enabled or metric_name not in self.metrics:
            return
        
        try:
            if labels:
                self.metrics[metric_name].labels(**labels).inc(value)
            else:
                self.metrics[metric_name].inc(value)
        except Exception as e:
            logger.error(f"Failed to increment counter {metric_name}: {e}")
    
    def observe_histogram(self, metric_name: str, value: float, labels: Dict[str, str] = None):
        """Observe a histogram metric."""
        if not self.enabled or metric_name not in self.metrics:
            return
        
        try:
            if labels:
                self.metrics[metric_name].labels(**labels).observe(value)
            else:
                self.metrics[metric_name].observe(value)
        except Exception as e:
            logger.error(f"Failed to observe histogram {metric_name}: {e}")
    
    def set_gauge(self, metric_name: str, value: float, labels: Dict[str, str] = None):
        """Set a gauge metric."""
        if not self.enabled or metric_name not in self.metrics:
            return
        
        try:
            if labels:
                self.metrics[metric_name].labels(**labels).set(value)
            else:
                self.metrics[metric_name].set(value)
        except Exception as e:
            logger.error(f"Failed to set gauge {metric_name}: {e}")
    
    def get_metrics(self) -> str:
        """Get metrics in Prometheus format."""
        if not self.enabled:
            return ""
        
        try:
            return generate_latest(self.registry).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to generate metrics: {e}")
            return ""


class HealthChecker:
    """Health check aggregator and manager."""
    
    def __init__(self):
        self.health_checks: Dict[str, Callable] = {}
        self.last_results: Dict[str, HealthCheckResult] = {}
        self.check_interval = 30  # seconds
        self.running = False
        self._task = None
        
        logger.info("Health checker initialized")
    
    def register_health_check(self, service_name: str, check_func: Callable):
        """Register a health check function."""
        self.health_checks[service_name] = check_func
        logger.info(f"Health check registered for {service_name}")
    
    async def run_health_check(self, service_name: str) -> HealthCheckResult:
        """Run a single health check."""
        if service_name not in self.health_checks:
            return HealthCheckResult(
                service_name=service_name,
                status="unknown",
                response_time=0.0,
                details={"error": "Health check not registered"}
            )
        
        start_time = time.time()
        try:
            check_func = self.health_checks[service_name]
            
            if asyncio.iscoroutinefunction(check_func):
                result = await check_func()
            else:
                result = check_func()
            
            response_time = time.time() - start_time
            
            if isinstance(result, dict):
                status = result.get('status', 'unknown')
                details = result
            else:
                status = 'healthy' if result else 'unhealthy'
                details = {'result': result}
            
            health_result = HealthCheckResult(
                service_name=service_name,
                status=status,
                response_time=response_time,
                details=details
            )
            
            self.last_results[service_name] = health_result
            return health_result
            
        except Exception as e:
            response_time = time.time() - start_time
            health_result = HealthCheckResult(
                service_name=service_name,
                status="unhealthy",
                response_time=response_time,
                details={"error": str(e)}
            )
            
            self.last_results[service_name] = health_result
            return health_result
    
    async def run_all_health_checks(self) -> Dict[str, HealthCheckResult]:
        """Run all registered health checks."""
        results = {}
        
        for service_name in self.health_checks:
            results[service_name] = await self.run_health_check(service_name)
        
        return results
    
    async def start_periodic_checks(self):
        """Start periodic health checks."""
        if self.running:
            return
        
        self.running = True
        self._task = asyncio.create_task(self._periodic_check_loop())
        logger.info("Periodic health checks started")
    
    async def stop_periodic_checks(self):
        """Stop periodic health checks."""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Periodic health checks stopped")
    
    async def _periodic_check_loop(self):
        """Periodic health check loop."""
        while self.running:
            try:
                await self.run_all_health_checks()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic health check: {e}")
                await asyncio.sleep(self.check_interval)
    
    def get_overall_status(self) -> str:
        """Get overall system health status."""
        if not self.last_results:
            return "unknown"
        
        statuses = [result.status for result in self.last_results.values()]
        
        if any(status == "unhealthy" for status in statuses):
            return "unhealthy"
        elif any(status == "degraded" for status in statuses):
            return "degraded"
        elif all(status == "healthy" for status in statuses):
            return "healthy"
        else:
            return "unknown"


class AlertManager:
    """Alert management and notification system."""
    
    def __init__(self):
        self.alerts: Dict[str, Alert] = {}
        self.alert_rules: List[Dict[str, Any]] = []
        self.notification_handlers: List[Callable] = []
        self.alert_history: deque = deque(maxlen=1000)
        
        logger.info("Alert manager initialized")
    
    def add_alert_rule(self, rule: Dict[str, Any]):
        """Add an alert rule."""
        required_fields = ['name', 'condition', 'severity']
        if not all(field in rule for field in required_fields):
            raise ValueError(f"Alert rule must contain: {required_fields}")
        
        self.alert_rules.append(rule)
        logger.info(f"Alert rule added: {rule['name']}")
    
    def add_notification_handler(self, handler: Callable):
        """Add a notification handler."""
        self.notification_handlers.append(handler)
        logger.info("Notification handler added")
    
    async def create_alert(self, alert_id: str, name: str, description: str, 
                          severity: AlertSeverity, metadata: Dict[str, Any] = None) -> Alert:
        """Create a new alert."""
        alert = Alert(
            id=alert_id,
            name=name,
            description=description,
            severity=severity,
            metadata=metadata or {}
        )
        
        self.alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        # Send notifications
        await self._send_notifications(alert)
        
        logger.warning(f"Alert created: {name} ({severity.value})", extra={
            'alert_id': alert_id,
            'severity': severity.value,
            'description': description
        })
        
        return alert
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert."""
        if alert_id not in self.alerts:
            return False
        
        alert = self.alerts[alert_id]
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.now()
        
        # Send resolution notification
        await self._send_notifications(alert)
        
        logger.info(f"Alert resolved: {alert.name}", extra={
            'alert_id': alert_id
        })
        
        return True
    
    async def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        if alert_id not in self.alerts:
            return False
        
        alert = self.alerts[alert_id]
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.now()
        
        logger.info(f"Alert acknowledged: {alert.name}", extra={
            'alert_id': alert_id
        })
        
        return True
    
    async def evaluate_alert_rules(self, metrics: Dict[str, Any]):
        """Evaluate alert rules against current metrics."""
        for rule in self.alert_rules:
            try:
                await self._evaluate_rule(rule, metrics)
            except Exception as e:
                logger.error(f"Error evaluating alert rule {rule['name']}: {e}")
    
    async def _evaluate_rule(self, rule: Dict[str, Any], metrics: Dict[str, Any]):
        """Evaluate a single alert rule."""
        condition = rule['condition']
        alert_id = f"rule_{rule['name']}"
        
        # Simple condition evaluation (extend as needed)
        triggered = False
        
        if condition['type'] == 'threshold':
            metric_value = self._get_metric_value(metrics, condition['metric'])
            threshold = condition['threshold']
            operator = condition.get('operator', '>')
            
            if operator == '>' and metric_value > threshold:
                triggered = True
            elif operator == '<' and metric_value < threshold:
                triggered = True
            elif operator == '>=' and metric_value >= threshold:
                triggered = True
            elif operator == '<=' and metric_value <= threshold:
                triggered = True
            elif operator == '==' and metric_value == threshold:
                triggered = True
        
        # Handle alert state
        if triggered and alert_id not in self.alerts:
            # Create new alert
            await self.create_alert(
                alert_id=alert_id,
                name=rule['name'],
                description=rule.get('description', f"Alert rule {rule['name']} triggered"),
                severity=AlertSeverity(rule['severity']),
                metadata={'rule': rule, 'metric_value': metric_value}
            )
        elif not triggered and alert_id in self.alerts:
            # Resolve existing alert
            await self.resolve_alert(alert_id)
    
    def _get_metric_value(self, metrics: Dict[str, Any], metric_path: str) -> float:
        """Get metric value from nested dictionary."""
        keys = metric_path.split('.')
        value = metrics
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return 0.0
        
        return float(value) if isinstance(value, (int, float)) else 0.0
    
    async def _send_notifications(self, alert: Alert):
        """Send alert notifications."""
        for handler in self.notification_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(alert)
                else:
                    handler(alert)
            except Exception as e:
                logger.error(f"Notification handler failed: {e}")
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        return [alert for alert in self.alerts.values() if alert.status == AlertStatus.ACTIVE]
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert summary statistics."""
        active_alerts = self.get_active_alerts()
        
        severity_counts = defaultdict(int)
        for alert in active_alerts:
            severity_counts[alert.severity.value] += 1
        
        return {
            'total_active': len(active_alerts),
            'by_severity': dict(severity_counts),
            'total_rules': len(self.alert_rules),
            'total_history': len(self.alert_history)
        }


class MonitoringSystem:
    """Main monitoring system coordinator."""
    
    def __init__(self):
        self.metrics = PrometheusMetrics()
        self.health_checker = HealthChecker()
        self.alert_manager = AlertManager()
        self.running = False
        self._monitoring_task = None
        
        # Setup default alert rules
        self._setup_default_alert_rules()
        
        logger.info("Monitoring system initialized")
    
    def _setup_default_alert_rules(self):
        """Setup default alert rules."""
        default_rules = [
            {
                'name': 'high_error_rate',
                'description': 'High error rate detected',
                'condition': {
                    'type': 'threshold',
                    'metric': 'error_rate',
                    'operator': '>',
                    'threshold': 0.05  # 5% error rate
                },
                'severity': 'warning'
            },
            {
                'name': 'high_response_time',
                'description': 'High response time detected',
                'condition': {
                    'type': 'threshold',
                    'metric': 'avg_response_time',
                    'operator': '>',
                    'threshold': 5.0  # 5 seconds
                },
                'severity': 'warning'
            },
            {
                'name': 'service_down',
                'description': 'Service is down',
                'condition': {
                    'type': 'threshold',
                    'metric': 'health_score',
                    'operator': '<',
                    'threshold': 0.5
                },
                'severity': 'critical'
            }
        ]
        
        for rule in default_rules:
            self.alert_manager.add_alert_rule(rule)
    
    async def start_monitoring(self):
        """Start the monitoring system."""
        if self.running:
            return
        
        self.running = True
        
        # Start health checks
        await self.health_checker.start_periodic_checks()
        
        # Start monitoring loop
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info("Monitoring system started")
    
    async def stop_monitoring(self):
        """Stop the monitoring system."""
        self.running = False
        
        # Stop health checks
        await self.health_checker.stop_periodic_checks()
        
        # Stop monitoring loop
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Monitoring system stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.running:
            try:
                # Collect metrics
                metrics = await self._collect_metrics()
                
                # Evaluate alert rules
                await self.alert_manager.evaluate_alert_rules(metrics)
                
                # Update Prometheus metrics
                self._update_prometheus_metrics(metrics)
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(10)
    
    async def _collect_metrics(self) -> Dict[str, Any]:
        """Collect system metrics."""
        metrics = {
            'timestamp': time.time(),
            'health_checks': {},
            'system': {},
            'application': {}
        }
        
        # Collect health check results
        health_results = await self.health_checker.run_all_health_checks()
        for service_name, result in health_results.items():
            metrics['health_checks'][service_name] = {
                'status': result.status,
                'response_time': result.response_time,
                'details': result.details
            }
        
        # Calculate health score
        healthy_count = sum(1 for result in health_results.values() if result.status == 'healthy')
        total_count = len(health_results)
        metrics['health_score'] = healthy_count / max(1, total_count)
        
        # Collect system metrics
        try:
            import psutil
            metrics['system'] = {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent
            }
        except ImportError:
            metrics['system'] = {'error': 'psutil not available'}
        
        return metrics
    
    def _update_prometheus_metrics(self, metrics: Dict[str, Any]):
        """Update Prometheus metrics."""
        if not self.metrics.enabled:
            return
        
        # Update system metrics
        if 'system' in metrics and 'error' not in metrics['system']:
            self.metrics.set_gauge('system_cpu_usage_percent', metrics['system']['cpu_percent'])
            
            # Convert memory percentage to bytes (approximate)
            try:
                import psutil
                memory_info = psutil.virtual_memory()
                self.metrics.set_gauge('system_memory_usage_bytes', memory_info.used, {'type': 'used'})
                self.metrics.set_gauge('system_memory_usage_bytes', memory_info.available, {'type': 'available'})
                self.metrics.set_gauge('system_memory_usage_bytes', memory_info.total, {'type': 'total'})
            except ImportError:
                pass
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get overall monitoring status."""
        return {
            'running': self.running,
            'health_checker': {
                'registered_checks': len(self.health_checker.health_checks),
                'last_check_count': len(self.health_checker.last_results),
                'overall_status': self.health_checker.get_overall_status()
            },
            'alert_manager': self.alert_manager.get_alert_summary(),
            'metrics': {
                'prometheus_enabled': self.metrics.enabled,
                'metrics_count': len(self.metrics.metrics) if self.metrics.enabled else 0
            }
        }


# Global monitoring system instance
_monitoring_system: Optional[MonitoringSystem] = None


def get_monitoring_system() -> MonitoringSystem:
    """Get the global monitoring system instance."""
    global _monitoring_system
    if _monitoring_system is None:
        _monitoring_system = MonitoringSystem()
    return _monitoring_system


# Notification handlers
async def console_notification_handler(alert: Alert):
    """Console notification handler."""
    status_emoji = {
        AlertStatus.ACTIVE: "🚨",
        AlertStatus.RESOLVED: "✅",
        AlertStatus.ACKNOWLEDGED: "👀"
    }
    
    severity_emoji = {
        AlertSeverity.INFO: "ℹ️",
        AlertSeverity.WARNING: "⚠️",
        AlertSeverity.ERROR: "❌",
        AlertSeverity.CRITICAL: "🔥"
    }
    
    emoji = status_emoji.get(alert.status, "❓")
    severity = severity_emoji.get(alert.severity, "❓")
    
    print(f"{emoji} {severity} [{alert.status.value.upper()}] {alert.name}")
    print(f"   Description: {alert.description}")
    print(f"   Created: {alert.created_at}")
    if alert.resolved_at:
        print(f"   Resolved: {alert.resolved_at}")


def slack_notification_handler(alert: Alert):
    """Slack notification handler (placeholder)."""
    # Implement Slack webhook integration
    logger.info(f"Slack notification: {alert.name} ({alert.severity.value})")


def email_notification_handler(alert: Alert):
    """Email notification handler (placeholder)."""
    # Implement email notification
    logger.info(f"Email notification: {alert.name} ({alert.severity.value})")