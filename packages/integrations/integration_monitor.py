#!/usr/bin/env python3
"""
Integration Monitor for External Integration Resilience
Comprehensive monitoring, alerting, and health checking for external integrations
"""

import asyncio
import aiohttp
import json
import logging
import time
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import statistics

# Graceful Redis import
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class MetricType(Enum):
    """Metric types"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

@dataclass
class HealthCheck:
    """Health check configuration"""
    name: str
    endpoint: str
    method: str = "GET"
    timeout: float = 10.0
    interval: float = 60.0  # seconds
    expected_status: int = 200
    expected_response: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True

@dataclass
class AlertRule:
    """Alert rule configuration"""
    name: str
    metric_name: str
    condition: str  # e.g., "> 5", "< 0.95", "== 0"
    severity: AlertSeverity
    description: str
    cooldown: float = 300.0  # seconds
    enabled: bool = True

@dataclass
class Metric:
    """Metric data point"""
    name: str
    value: Union[int, float]
    metric_type: MetricType
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class Alert:
    """Alert instance"""
    id: str
    rule_name: str
    metric_name: str
    current_value: Union[int, float]
    threshold: str
    severity: AlertSeverity
    description: str
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolved_at: Optional[datetime] = None

@dataclass
class IntegrationStatus:
    """Integration status summary"""
    name: str
    status: HealthStatus
    last_check: datetime
    response_time: float
    error_rate: float
    success_rate: float
    total_requests: int
    failed_requests: int
    uptime_percentage: float
    alerts: List[Alert] = field(default_factory=list)

class MetricCollector:
    """Collects and stores metrics"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.metrics: Dict[str, List[Metric]] = defaultdict(list)
        self.max_metrics_per_name = 1000
        
    async def record_metric(self, metric: Metric):
        """Record a metric"""
        try:
            if self.redis_client:
                # Store in Redis with TTL
                key = f"metric:{metric.name}"
                metric_data = {
                    'value': metric.value,
                    'type': metric.metric_type.value,
                    'labels': metric.labels,
                    'timestamp': metric.timestamp.isoformat()
                }
                await self.redis_client.lpush(key, json.dumps(metric_data))
                await self.redis_client.ltrim(key, 0, self.max_metrics_per_name - 1)
                await self.redis_client.expire(key, 86400)  # 24 hours
            else:
                # Store in memory
                self.metrics[metric.name].append(metric)
                if len(self.metrics[metric.name]) > self.max_metrics_per_name:
                    self.metrics[metric.name] = self.metrics[metric.name][-self.max_metrics_per_name:]
                    
        except Exception as e:
            logger.error(f"Failed to record metric {metric.name}: {e}")
            
    async def get_metrics(self, metric_name: str, limit: int = 100) -> List[Metric]:
        """Get recent metrics"""
        try:
            if self.redis_client:
                key = f"metric:{metric_name}"
                metric_data_list = await self.redis_client.lrange(key, 0, limit - 1)
                metrics = []
                for metric_data in metric_data_list:
                    data = json.loads(metric_data)
                    metrics.append(Metric(
                        name=metric_name,
                        value=data['value'],
                        metric_type=MetricType(data['type']),
                        labels=data['labels'],
                        timestamp=datetime.fromisoformat(data['timestamp'])
                    ))
                return metrics
            else:
                return self.metrics.get(metric_name, [])[-limit:]
        except Exception as e:
            logger.error(f"Failed to get metrics for {metric_name}: {e}")
            return []
            
    async def get_metric_summary(self, metric_name: str, duration_minutes: int = 60) -> Dict[str, Any]:
        """Get metric summary for time period"""
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        metrics = await self.get_metrics(metric_name, 1000)
        
        # Filter by time
        recent_metrics = [m for m in metrics if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            return {
                "metric_name": metric_name,
                "count": 0,
                "duration_minutes": duration_minutes
            }
            
        values = [m.value for m in recent_metrics]
        
        return {
            "metric_name": metric_name,
            "count": len(values),
            "duration_minutes": duration_minutes,
            "min": min(values),
            "max": max(values),
            "avg": statistics.mean(values),
            "median": statistics.median(values),
            "latest": values[-1] if values else None,
            "timestamp": recent_metrics[-1].timestamp.isoformat() if recent_metrics else None
        }

class HealthChecker:
    """Performs health checks on integrations"""
    
    def __init__(self, session: aiohttp.ClientSession, metric_collector: MetricCollector):
        self.session = session
        self.metric_collector = metric_collector
        self.health_checks: Dict[str, HealthCheck] = {}
        self.check_tasks: Dict[str, asyncio.Task] = {}
        self.last_results: Dict[str, Dict[str, Any]] = {}
        
    def register_health_check(self, health_check: HealthCheck):
        """Register a health check"""
        self.health_checks[health_check.name] = health_check
        
        # Start periodic check
        if health_check.enabled:
            self._start_health_check(health_check)
            
        logger.info(f"Registered health check: {health_check.name}")
        
    def _start_health_check(self, health_check: HealthCheck):
        """Start periodic health check"""
        if health_check.name in self.check_tasks:
            self.check_tasks[health_check.name].cancel()
            
        task = asyncio.create_task(self._run_periodic_check(health_check))
        self.check_tasks[health_check.name] = task
        
    async def _run_periodic_check(self, health_check: HealthCheck):
        """Run periodic health check"""
        while True:
            try:
                await self.perform_health_check(health_check.name)
                await asyncio.sleep(health_check.interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error for {health_check.name}: {e}")
                await asyncio.sleep(health_check.interval)
                
    async def perform_health_check(self, check_name: str) -> Dict[str, Any]:
        """Perform a single health check"""
        if check_name not in self.health_checks:
            raise ValueError(f"Health check {check_name} not registered")
            
        health_check = self.health_checks[check_name]
        start_time = time.time()
        
        try:
            timeout = aiohttp.ClientTimeout(total=health_check.timeout)
            async with self.session.request(
                method=health_check.method,
                url=health_check.endpoint,
                headers=health_check.headers,
                timeout=timeout
            ) as response:
                response_time = time.time() - start_time
                response_text = await response.text()
                
                # Check status code
                status_ok = response.status == health_check.expected_status
                
                # Check response content if specified
                content_ok = True
                if health_check.expected_response:
                    content_ok = health_check.expected_response in response_text
                    
                is_healthy = status_ok and content_ok
                
                result = {
                    "name": check_name,
                    "status": HealthStatus.HEALTHY if is_healthy else HealthStatus.CRITICAL,
                    "response_time": response_time,
                    "status_code": response.status,
                    "expected_status": health_check.expected_status,
                    "content_check": content_ok,
                    "timestamp": datetime.now(),
                    "error": None
                }
                
                # Record metrics
                await self.metric_collector.record_metric(Metric(
                    name=f"health_check_response_time",
                    value=response_time,
                    metric_type=MetricType.GAUGE,
                    labels={"check_name": check_name}
                ))
                
                await self.metric_collector.record_metric(Metric(
                    name=f"health_check_status",
                    value=1 if is_healthy else 0,
                    metric_type=MetricType.GAUGE,
                    labels={"check_name": check_name}
                ))
                
                self.last_results[check_name] = result
                return result
                
        except Exception as e:
            response_time = time.time() - start_time
            result = {
                "name": check_name,
                "status": HealthStatus.CRITICAL,
                "response_time": response_time,
                "status_code": None,
                "expected_status": health_check.expected_status,
                "content_check": False,
                "timestamp": datetime.now(),
                "error": str(e)
            }
            
            # Record failure metrics
            await self.metric_collector.record_metric(Metric(
                name=f"health_check_response_time",
                value=response_time,
                metric_type=MetricType.GAUGE,
                labels={"check_name": check_name}
            ))
            
            await self.metric_collector.record_metric(Metric(
                name=f"health_check_status",
                value=0,
                metric_type=MetricType.GAUGE,
                labels={"check_name": check_name}
            ))
            
            self.last_results[check_name] = result
            return result
            
    async def get_all_health_results(self) -> Dict[str, Dict[str, Any]]:
        """Get all health check results"""
        return self.last_results.copy()
        
    async def stop_all_checks(self):
        """Stop all health checks"""
        for task in self.check_tasks.values():
            task.cancel()
            
        if self.check_tasks:
            await asyncio.gather(*self.check_tasks.values(), return_exceptions=True)
            
        self.check_tasks.clear()

class AlertManager:
    """Manages alerts and notifications"""
    
    def __init__(self, metric_collector: MetricCollector):
        self.metric_collector = metric_collector
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.last_alert_times: Dict[str, datetime] = {}
        self.alert_handlers: List[Callable[[Alert], Any]] = []
        
    def register_alert_rule(self, rule: AlertRule):
        """Register an alert rule"""
        self.alert_rules[rule.name] = rule
        logger.info(f"Registered alert rule: {rule.name}")
        
    def register_alert_handler(self, handler: Callable[[Alert], Any]):
        """Register alert handler"""
        self.alert_handlers.append(handler)
        
    async def check_alerts(self):
        """Check all alert rules"""
        for rule_name, rule in self.alert_rules.items():
            if not rule.enabled:
                continue
                
            try:
                await self._check_alert_rule(rule)
            except Exception as e:
                logger.error(f"Error checking alert rule {rule_name}: {e}")
                
    async def _check_alert_rule(self, rule: AlertRule):
        """Check a single alert rule"""
        # Get recent metric summary
        summary = await self.metric_collector.get_metric_summary(rule.metric_name, 5)
        
        if summary["count"] == 0:
            return  # No data to check
            
        current_value = summary["latest"]
        
        # Parse condition
        condition_met = self._evaluate_condition(current_value, rule.condition)
        
        alert_id = f"{rule.name}_{rule.metric_name}"
        
        if condition_met:
            # Check cooldown
            last_alert_time = self.last_alert_times.get(alert_id)
            if last_alert_time and (datetime.now() - last_alert_time).total_seconds() < rule.cooldown:
                return  # Still in cooldown
                
            # Create or update alert
            if alert_id not in self.active_alerts:
                alert = Alert(
                    id=alert_id,
                    rule_name=rule.name,
                    metric_name=rule.metric_name,
                    current_value=current_value,
                    threshold=rule.condition,
                    severity=rule.severity,
                    description=rule.description
                )
                
                self.active_alerts[alert_id] = alert
                self.alert_history.append(alert)
                self.last_alert_times[alert_id] = datetime.now()
                
                # Notify handlers
                for handler in self.alert_handlers:
                    try:
                        await handler(alert)
                    except Exception as e:
                        logger.error(f"Alert handler error: {e}")
                        
                logger.warning(f"Alert triggered: {rule.name} - {rule.description}")
                
        else:
            # Resolve alert if it exists
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.resolved = True
                alert.resolved_at = datetime.now()
                del self.active_alerts[alert_id]
                
                logger.info(f"Alert resolved: {rule.name}")
                
    def _evaluate_condition(self, value: Union[int, float], condition: str) -> bool:
        """Evaluate alert condition"""
        try:
            # Simple condition evaluation
            if condition.startswith(">"):
                threshold = float(condition[1:].strip())
                return value > threshold
            elif condition.startswith("<"):
                threshold = float(condition[1:].strip())
                return value < threshold
            elif condition.startswith(">="):
                threshold = float(condition[2:].strip())
                return value >= threshold
            elif condition.startswith("<="):
                threshold = float(condition[2:].strip())
                return value <= threshold
            elif condition.startswith("=="):
                threshold = float(condition[2:].strip())
                return value == threshold
            elif condition.startswith("!="):
                threshold = float(condition[2:].strip())
                return value != threshold
            else:
                logger.warning(f"Unknown condition format: {condition}")
                return False
        except Exception as e:
            logger.error(f"Error evaluating condition {condition}: {e}")
            return False
            
    async def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        return list(self.active_alerts.values())
        
    async def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Get alert history"""
        return self.alert_history[-limit:]

class IntegrationMonitor:
    """Main integration monitoring system"""
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_client: Optional[redis.Redis] = None
        self.session: Optional[aiohttp.ClientSession] = None
        self.metric_collector: Optional[MetricCollector] = None
        self.health_checker: Optional[HealthChecker] = None
        self.alert_manager: Optional[AlertManager] = None
        self.monitoring_task: Optional[asyncio.Task] = None
        self.running = False
        
        # Initialize Redis if available
        if REDIS_AVAILABLE and redis_url:
            try:
                self.redis_client = redis.from_url(redis_url)
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}")
                
    async def start(self):
        """Start the integration monitor"""
        # Initialize session
        self.session = aiohttp.ClientSession()
        
        # Initialize components
        self.metric_collector = MetricCollector(self.redis_client)
        self.health_checker = HealthChecker(self.session, self.metric_collector)
        self.alert_manager = AlertManager(self.metric_collector)
        
        # Start monitoring loop
        self.running = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info("Integration monitor started")
        
    async def stop(self):
        """Stop the integration monitor"""
        self.running = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            
        if self.health_checker:
            await self.health_checker.stop_all_checks()
            
        if self.session:
            await self.session.close()
            
        if self.redis_client:
            await self.redis_client.close()
            
        logger.info("Integration monitor stopped")
        
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Check alerts every 30 seconds
                await self.alert_manager.check_alerts()
                await asyncio.sleep(30)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(30)
                
    def register_health_check(self, health_check: HealthCheck):
        """Register health check"""
        if self.health_checker:
            self.health_checker.register_health_check(health_check)
            
    def register_alert_rule(self, rule: AlertRule):
        """Register alert rule"""
        if self.alert_manager:
            self.alert_manager.register_alert_rule(rule)
            
    def register_alert_handler(self, handler: Callable[[Alert], Any]):
        """Register alert handler"""
        if self.alert_manager:
            self.alert_manager.register_alert_handler(handler)
            
    async def record_metric(self, metric: Metric):
        """Record a metric"""
        if self.metric_collector:
            await self.metric_collector.record_metric(metric)
            
    async def get_integration_status(self, integration_name: str) -> IntegrationStatus:
        """Get status for specific integration"""
        if not self.health_checker or not self.metric_collector or not self.alert_manager:
            raise RuntimeError("Monitor not started")
            
        # Get health check result
        health_results = await self.health_checker.get_all_health_results()
        health_result = health_results.get(integration_name, {})
        
        # Get metrics
        response_time_summary = await self.metric_collector.get_metric_summary(
            f"integration_response_time", 60
        )
        error_rate_summary = await self.metric_collector.get_metric_summary(
            f"integration_error_rate", 60
        )
        
        # Get alerts
        active_alerts = await self.alert_manager.get_active_alerts()
        integration_alerts = [a for a in active_alerts if integration_name in a.metric_name]
        
        return IntegrationStatus(
            name=integration_name,
            status=health_result.get("status", HealthStatus.UNKNOWN),
            last_check=health_result.get("timestamp", datetime.now()),
            response_time=response_time_summary.get("avg", 0),
            error_rate=error_rate_summary.get("latest", 0),
            success_rate=100 - error_rate_summary.get("latest", 0),
            total_requests=response_time_summary.get("count", 0),
            failed_requests=int(response_time_summary.get("count", 0) * error_rate_summary.get("latest", 0) / 100),
            uptime_percentage=95.0,  # Calculate based on health checks
            alerts=integration_alerts
        )
        
    async def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        if not self.health_checker or not self.alert_manager:
            return {"status": "not_started"}
            
        health_results = await self.health_checker.get_all_health_results()
        active_alerts = await self.alert_manager.get_active_alerts()
        
        # Determine overall status
        overall_status = HealthStatus.HEALTHY
        critical_alerts = [a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]
        
        if critical_alerts:
            overall_status = HealthStatus.CRITICAL
        elif any(r.get("status") == HealthStatus.CRITICAL for r in health_results.values()):
            overall_status = HealthStatus.CRITICAL
        elif any(r.get("status") == HealthStatus.WARNING for r in health_results.values()):
            overall_status = HealthStatus.WARNING
            
        return {
            "status": overall_status.value,
            "timestamp": datetime.now().isoformat(),
            "health_checks": len(health_results),
            "active_alerts": len(active_alerts),
            "critical_alerts": len(critical_alerts),
            "integrations": list(health_results.keys())
        }

# Global monitor instance
_monitor_instance: Optional[IntegrationMonitor] = None

async def get_integration_monitor(redis_url: Optional[str] = None) -> IntegrationMonitor:
    """Get or create the global integration monitor instance"""
    global _monitor_instance
    
    if _monitor_instance is None:
        _monitor_instance = IntegrationMonitor(redis_url)
        await _monitor_instance.start()
        
    return _monitor_instance

async def shutdown_integration_monitor():
    """Shutdown the global integration monitor instance"""
    global _monitor_instance
    
    if _monitor_instance:
        await _monitor_instance.stop()
        _monitor_instance = None