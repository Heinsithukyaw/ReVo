"""
Enhanced Monitoring Service
Part of reVoAgent Next Phase Implementation
"""

import asyncio
import json
import logging
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import deque
from dataclasses import dataclass, asdict

# Redis functionality disabled for compatibility
REDIS_AVAILABLE = False
aioredis = None

logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, int]
    timestamp: datetime

@dataclass
class ApplicationMetrics:
    response_times: List[float]
    error_rates: List[float]
    throughput: int
    active_connections: int
    timestamp: datetime

@dataclass
class Alert:
    id: str
    severity: str  # 'info', 'warning', 'critical'
    title: str
    description: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None

class EnhancedMonitoringService:
    def __init__(self, websocket_manager=None, redis_url: str = "redis://localhost:6379"):
        self.websocket_manager = websocket_manager
        self.redis_url = redis_url
        self.redis = None
        
        # Metrics history
        self.metrics_history = {
            'response_times': deque(maxlen=100),
            'error_rates': deque(maxlen=24),  # 24 hours
            'cpu_usage': deque(maxlen=60),    # 60 minutes
            'memory_usage': deque(maxlen=60),
            'disk_usage': deque(maxlen=60),
            'throughput': deque(maxlen=60),
            'network_io': deque(maxlen=60)
        }
        
        # Alert thresholds
        self.alert_thresholds = {
            'cpu_usage': {'warning': 70, 'critical': 85},
            'memory_usage': {'warning': 75, 'critical': 90},
            'disk_usage': {'warning': 80, 'critical': 95},
            'response_time': {'warning': 3000, 'critical': 5000},  # ms
            'error_rate': {'warning': 3, 'critical': 5},  # %
            'throughput_drop': {'warning': 50, 'critical': 75}  # % drop
        }
        
        # State
        self.running = False
        self.alerts: Dict[str, Alert] = {}
        self.baseline_metrics = {}
        self.last_metrics = {}
        
        # Tasks
        self.monitoring_tasks = []

    async def initialize(self):
        """Initialize monitoring service"""
        if REDIS_AVAILABLE:
            try:
                self.redis = await aioredis.from_url(self.redis_url)
                logger.info("Redis connection established for monitoring")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}. Continuing without Redis.")
                self.redis = None
        else:
            logger.info("Redis not available. Continuing without Redis caching.")
            self.redis = None
        
        # Establish baseline metrics
        await self._establish_baseline()

    async def start_monitoring(self):
        """Start continuous monitoring"""
        if self.running:
            return
            
        self.running = True
        logger.info("Starting enhanced monitoring service")
        
        # Start monitoring tasks
        self.monitoring_tasks = [
            asyncio.create_task(self._collect_system_metrics()),
            asyncio.create_task(self._collect_application_metrics()),
            asyncio.create_task(self._check_alerts()),
            asyncio.create_task(self._cleanup_old_data()),
            asyncio.create_task(self._broadcast_metrics())
        ]

    async def stop_monitoring(self):
        """Stop monitoring"""
        self.running = False
        
        # Cancel all monitoring tasks
        for task in self.monitoring_tasks:
            task.cancel()
            
        try:
            await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"Error stopping monitoring tasks: {e}")
        
        if self.redis:
            await self.redis.close()
            
        logger.info("Enhanced monitoring service stopped")

    async def _establish_baseline(self):
        """Establish baseline metrics for comparison"""
        try:
            # Collect initial metrics
            cpu_samples = []
            memory_samples = []
            
            for _ in range(5):
                cpu_samples.append(psutil.cpu_percent(interval=1))
                memory_samples.append(psutil.virtual_memory().percent)
                await asyncio.sleep(1)
            
            self.baseline_metrics = {
                'cpu_usage': sum(cpu_samples) / len(cpu_samples),
                'memory_usage': sum(memory_samples) / len(memory_samples),
                'established_at': datetime.now()
            }
            
            logger.info(f"Baseline metrics established: {self.baseline_metrics}")
            
        except Exception as e:
            logger.error(f"Failed to establish baseline metrics: {e}")

    async def _collect_system_metrics(self):
        """Collect system-level metrics"""
        while self.running:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                self.metrics_history['cpu_usage'].append(cpu_percent)
                
                # Memory usage
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                self.metrics_history['memory_usage'].append(memory_percent)
                
                # Disk usage
                disk = psutil.disk_usage('/')
                disk_percent = (disk.used / disk.total) * 100
                self.metrics_history['disk_usage'].append(disk_percent)
                
                # Network I/O
                network = psutil.net_io_counters()
                network_data = {
                    'bytes_sent': network.bytes_sent,
                    'bytes_received': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_received': network.packets_recv
                }
                self.metrics_history['network_io'].append(network_data)
                
                # Create metrics object
                metrics = SystemMetrics(
                    cpu_usage=cpu_percent,
                    memory_usage=memory_percent,
                    disk_usage=disk_percent,
                    network_io=network_data,
                    timestamp=datetime.now()
                )
                
                # Store in Redis if available
                if self.redis:
                    await self.redis.setex(
                        'system_metrics', 
                        300,  # 5 minutes TTL
                        json.dumps(asdict(metrics), default=str)
                    )
                
                self.last_metrics['system'] = metrics
                
                # Check for system alerts
                await self._check_system_alerts(metrics)
                
            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}")
                
            await asyncio.sleep(60)  # Collect every minute

    async def _collect_application_metrics(self):
        """Collect application-specific metrics"""
        while self.running:
            try:
                # Calculate throughput from recent requests
                current_time = datetime.now()
                minute_ago = current_time - timedelta(minutes=1)
                
                # This would typically query your application's request logs
                throughput = await self._calculate_throughput(minute_ago, current_time)
                self.metrics_history['throughput'].append(throughput)
                
                # Calculate error rates for different time periods
                error_rates = await self._calculate_error_rates()
                
                # Get active connections (if websocket manager is available)
                active_connections = 0
                if self.websocket_manager:
                    active_connections = len(self.websocket_manager.active_connections)
                
                # Create application metrics
                app_metrics = ApplicationMetrics(
                    response_times=list(self.metrics_history['response_times']),
                    error_rates=error_rates,
                    throughput=throughput,
                    active_connections=active_connections,
                    timestamp=current_time
                )
                
                self.last_metrics['application'] = app_metrics
                
                # Check for application alerts
                await self._check_application_alerts(app_metrics)
                
            except Exception as e:
                logger.error(f"Error collecting application metrics: {e}")
                
            await asyncio.sleep(60)  # Collect every minute

    async def _calculate_throughput(self, start_time: datetime, end_time: datetime) -> int:
        """Calculate requests per minute"""
        # This would typically query your request logs or metrics store
        # For demo purposes, return a simulated value based on active connections
        if self.websocket_manager:
            base_throughput = len(self.websocket_manager.active_connections) * 10
            # Add some randomness
            import random
            return max(0, base_throughput + random.randint(-20, 50))
        else:
            import random
            return random.randint(50, 200)

    async def _calculate_error_rates(self) -> List[float]:
        """Calculate error rates for different time periods"""
        # This would typically query your error logs
        # For demo purposes, return simulated values
        import random
        
        # Simulate error rates that increase under load
        base_error_rate = 0.5
        if self.websocket_manager:
            connection_load = len(self.websocket_manager.active_connections)
            load_factor = min(connection_load / 100, 2.0)  # Max 2x increase
            base_error_rate *= (1 + load_factor)
        
        return [
            max(0, base_error_rate + random.uniform(-0.3, 0.8)),  # Last hour
            max(0, base_error_rate + random.uniform(-0.2, 0.6)),  # Last 6 hours
            max(0, base_error_rate + random.uniform(-0.1, 0.4)),  # Last 24 hours
            max(0, base_error_rate + random.uniform(-0.1, 0.2))   # Last week
        ]

    async def record_response_time(self, response_time: float):
        """Record a response time measurement"""
        self.metrics_history['response_times'].append(response_time)
        
        # Check for response time alerts
        if response_time > self.alert_thresholds['response_time']['critical']:
            await self._create_alert(
                'critical',
                'Critical Response Time',
                f'Response time of {response_time:.0f}ms exceeds critical threshold'
            )
        elif response_time > self.alert_thresholds['response_time']['warning']:
            await self._create_alert(
                'warning',
                'High Response Time',
                f'Response time of {response_time:.0f}ms exceeds warning threshold'
            )

    async def record_error(self, error_type: str, error_message: str):
        """Record an error occurrence"""
        error_data = {
            'type': error_type,
            'message': error_message,
            'timestamp': datetime.now().isoformat()
        }
        
        # Store in Redis if available
        if self.redis:
            await self.redis.lpush('errors', json.dumps(error_data))
            await self.redis.ltrim('errors', 0, 999)  # Keep last 1000 errors

    async def _check_system_alerts(self, metrics: SystemMetrics):
        """Check system metrics against alert thresholds"""
        alerts_to_create = []
        
        # CPU usage alerts
        if metrics.cpu_usage > self.alert_thresholds['cpu_usage']['critical']:
            alerts_to_create.append({
                'severity': 'critical',
                'title': 'Critical CPU Usage',
                'description': f'CPU usage at {metrics.cpu_usage:.1f}%'
            })
        elif metrics.cpu_usage > self.alert_thresholds['cpu_usage']['warning']:
            alerts_to_create.append({
                'severity': 'warning',
                'title': 'High CPU Usage',
                'description': f'CPU usage at {metrics.cpu_usage:.1f}%'
            })
            
        # Memory usage alerts
        if metrics.memory_usage > self.alert_thresholds['memory_usage']['critical']:
            alerts_to_create.append({
                'severity': 'critical',
                'title': 'Critical Memory Usage',
                'description': f'Memory usage at {metrics.memory_usage:.1f}%'
            })
        elif metrics.memory_usage > self.alert_thresholds['memory_usage']['warning']:
            alerts_to_create.append({
                'severity': 'warning',
                'title': 'High Memory Usage',
                'description': f'Memory usage at {metrics.memory_usage:.1f}%'
            })
            
        # Disk usage alerts
        if metrics.disk_usage > self.alert_thresholds['disk_usage']['critical']:
            alerts_to_create.append({
                'severity': 'critical',
                'title': 'Critical Disk Usage',
                'description': f'Disk usage at {metrics.disk_usage:.1f}%'
            })
        elif metrics.disk_usage > self.alert_thresholds['disk_usage']['warning']:
            alerts_to_create.append({
                'severity': 'warning',
                'title': 'High Disk Usage',
                'description': f'Disk usage at {metrics.disk_usage:.1f}%'
            })
            
        # Create alerts
        for alert_data in alerts_to_create:
            await self._create_alert(
                alert_data['severity'],
                alert_data['title'],
                alert_data['description']
            )

    async def _check_application_alerts(self, metrics: ApplicationMetrics):
        """Check application metrics against alert thresholds"""
        # Check error rates
        if metrics.error_rates:
            current_error_rate = metrics.error_rates[0]  # Most recent
            
            if current_error_rate > self.alert_thresholds['error_rate']['critical']:
                await self._create_alert(
                    'critical',
                    'Critical Error Rate',
                    f'Error rate at {current_error_rate:.1f}%'
                )
            elif current_error_rate > self.alert_thresholds['error_rate']['warning']:
                await self._create_alert(
                    'warning',
                    'High Error Rate',
                    f'Error rate at {current_error_rate:.1f}%'
                )
        
        # Check throughput drops
        if len(self.metrics_history['throughput']) > 5:
            recent_throughput = list(self.metrics_history['throughput'])[-5:]
            avg_recent = sum(recent_throughput) / len(recent_throughput)
            
            if self.baseline_metrics and 'throughput' in self.baseline_metrics:
                baseline_throughput = self.baseline_metrics['throughput']
                drop_percentage = ((baseline_throughput - avg_recent) / baseline_throughput) * 100
                
                if drop_percentage > self.alert_thresholds['throughput_drop']['critical']:
                    await self._create_alert(
                        'critical',
                        'Critical Throughput Drop',
                        f'Throughput dropped by {drop_percentage:.1f}%'
                    )
                elif drop_percentage > self.alert_thresholds['throughput_drop']['warning']:
                    await self._create_alert(
                        'warning',
                        'Throughput Drop',
                        f'Throughput dropped by {drop_percentage:.1f}%'
                    )

    async def _create_alert(self, severity: str, title: str, description: str):
        """Create and broadcast an alert"""
        # Check if similar alert already exists and is not resolved
        alert_key = f"{severity}_{title}"
        
        if alert_key in self.alerts and not self.alerts[alert_key].resolved:
            return  # Don't create duplicate alerts
        
        alert = Alert(
            id=alert_key,
            severity=severity,
            title=title,
            description=description,
            timestamp=datetime.now()
        )
        
        self.alerts[alert_key] = alert
        
        # Store alert in Redis
        if self.redis:
            await self.redis.lpush('alerts', json.dumps(asdict(alert), default=str))
            await self.redis.ltrim('alerts', 0, 99)  # Keep last 100 alerts
            
        # Broadcast to WebSocket clients
        if self.websocket_manager:
            await self.websocket_manager.broadcast_to_channel(
                'system_alerts',
                {
                    'channel': 'system_alerts',
                    'payload': asdict(alert, dict_factory=lambda x: {k: v.isoformat() if isinstance(v, datetime) else v for k, v in x})
                }
            )
        
        logger.warning(f"Alert created: [{severity.upper()}] {title} - {description}")

    async def resolve_alert(self, alert_id: str):
        """Resolve an alert"""
        if alert_id in self.alerts:
            self.alerts[alert_id].resolved = True
            self.alerts[alert_id].resolved_at = datetime.now()
            
            # Broadcast resolution
            if self.websocket_manager:
                await self.websocket_manager.broadcast_to_channel(
                    'alert_resolved',
                    {
                        'channel': 'alert_resolved',
                        'payload': {'alert_id': alert_id, 'resolved_at': datetime.now().isoformat()}
                    }
                )

    async def _check_alerts(self):
        """Periodic alert checking and auto-resolution"""
        while self.running:
            try:
                current_time = datetime.now()
                
                # Auto-resolve old alerts (older than 1 hour)
                for alert_id, alert in list(self.alerts.items()):
                    if not alert.resolved and (current_time - alert.timestamp).total_seconds() > 3600:
                        await self.resolve_alert(alert_id)
                        logger.info(f"Auto-resolved old alert: {alert_id}")
                
                # Check for system-wide issues
                await self._check_system_health()
                
            except Exception as e:
                logger.error(f"Error in alert checking: {e}")
                
            await asyncio.sleep(300)  # Check every 5 minutes

    async def _check_system_health(self):
        """Check overall system health"""
        if not self.last_metrics:
            return
            
        health_issues = []
        
        # Check if we have recent metrics
        if 'system' in self.last_metrics:
            system_metrics = self.last_metrics['system']
            time_since_update = (datetime.now() - system_metrics.timestamp).total_seconds()
            
            if time_since_update > 300:  # 5 minutes
                health_issues.append("System metrics are stale")
        
        # Check if we have active monitoring
        if not self.running:
            health_issues.append("Monitoring service is not running")
        
        # Check critical resource usage
        if 'system' in self.last_metrics:
            system_metrics = self.last_metrics['system']
            
            critical_resources = []
            if system_metrics.cpu_usage > 90:
                critical_resources.append(f"CPU: {system_metrics.cpu_usage:.1f}%")
            if system_metrics.memory_usage > 95:
                critical_resources.append(f"Memory: {system_metrics.memory_usage:.1f}%")
            if system_metrics.disk_usage > 98:
                critical_resources.append(f"Disk: {system_metrics.disk_usage:.1f}%")
            
            if critical_resources:
                health_issues.append(f"Critical resource usage: {', '.join(critical_resources)}")
        
        # Create system health alert if issues found
        if health_issues:
            await self._create_alert(
                'critical',
                'System Health Issues',
                f"Multiple issues detected: {'; '.join(health_issues)}"
            )

    async def _broadcast_metrics(self):
        """Broadcast current metrics to WebSocket clients"""
        while self.running:
            try:
                if self.websocket_manager and self.last_metrics:
                    # Combine system and application metrics
                    combined_metrics = {}
                    
                    if 'system' in self.last_metrics:
                        system_metrics = self.last_metrics['system']
                        combined_metrics.update({
                            'cpu_usage': system_metrics.cpu_usage,
                            'memory_usage': system_metrics.memory_usage,
                            'disk_usage': system_metrics.disk_usage,
                            'network_io': system_metrics.network_io
                        })
                    
                    if 'application' in self.last_metrics:
                        app_metrics = self.last_metrics['application']
                        combined_metrics.update({
                            'response_times': app_metrics.response_times[-20:],  # Last 20 measurements
                            'error_rates': app_metrics.error_rates,
                            'throughput': app_metrics.throughput,
                            'active_connections': app_metrics.active_connections
                        })
                    
                    combined_metrics['timestamp'] = datetime.now().isoformat()
                    
                    await self.websocket_manager.broadcast_to_channel(
                        'system_metrics',
                        {
                            'channel': 'system_metrics',
                            'payload': combined_metrics
                        }
                    )
                
            except Exception as e:
                logger.error(f"Error broadcasting metrics: {e}")
                
            await asyncio.sleep(30)  # Broadcast every 30 seconds

    async def _cleanup_old_data(self):
        """Clean up old metrics and alerts"""
        while self.running:
            try:
                # Clean up old alerts (older than 24 hours)
                cutoff_time = datetime.now() - timedelta(hours=24)
                old_alerts = [
                    alert_id for alert_id, alert in self.alerts.items()
                    if alert.timestamp < cutoff_time
                ]
                
                for alert_id in old_alerts:
                    del self.alerts[alert_id]
                
                if old_alerts:
                    logger.info(f"Cleaned up {len(old_alerts)} old alerts")
                
                # Clean up Redis data if available
                if self.redis:
                    # Clean up old errors
                    await self.redis.ltrim('errors', 0, 999)
                    await self.redis.ltrim('alerts', 0, 99)
                
            except Exception as e:
                logger.error(f"Error in cleanup: {e}")
                
            await asyncio.sleep(3600)  # Clean up every hour

    async def get_current_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        if self.redis:
            try:
                cached_metrics = await self.redis.get('system_metrics')
                if cached_metrics:
                    return json.loads(cached_metrics)
            except Exception as e:
                logger.error(f"Error retrieving cached metrics: {e}")
                
        # Fallback to real-time collection
        try:
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            return {
                'cpu_usage': cpu_percent,
                'memory_usage': memory.percent,
                'disk_usage': (disk.used / disk.total) * 100,
                'network_io': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_received': network.bytes_recv
                },
                'response_times': list(self.metrics_history['response_times']),
                'error_rates': await self._calculate_error_rates(),
                'throughput': list(self.metrics_history['throughput'])[-1] if self.metrics_history['throughput'] else 0,
                'active_connections': len(self.websocket_manager.active_connections) if self.websocket_manager else 0,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error collecting real-time metrics: {e}")
            return {}

    async def get_alerts(self, include_resolved: bool = False) -> List[Dict[str, Any]]:
        """Get current alerts"""
        alerts = []
        for alert in self.alerts.values():
            if include_resolved or not alert.resolved:
                alerts.append(asdict(alert, dict_factory=lambda x: {k: v.isoformat() if isinstance(v, datetime) else v for k, v in x}))
        
        return sorted(alerts, key=lambda x: x['timestamp'], reverse=True)

    def get_health_status(self) -> Dict[str, Any]:
        """Get overall system health status"""
        if not self.last_metrics:
            return {'status': 'unknown', 'message': 'No metrics available'}
        
        issues = []
        warnings = []
        
        # Check system metrics
        if 'system' in self.last_metrics:
            system_metrics = self.last_metrics['system']
            
            if system_metrics.cpu_usage > 85:
                issues.append(f"High CPU usage: {system_metrics.cpu_usage:.1f}%")
            elif system_metrics.cpu_usage > 70:
                warnings.append(f"Elevated CPU usage: {system_metrics.cpu_usage:.1f}%")
            
            if system_metrics.memory_usage > 90:
                issues.append(f"High memory usage: {system_metrics.memory_usage:.1f}%")
            elif system_metrics.memory_usage > 75:
                warnings.append(f"Elevated memory usage: {system_metrics.memory_usage:.1f}%")
            
            if system_metrics.disk_usage > 95:
                issues.append(f"High disk usage: {system_metrics.disk_usage:.1f}%")
            elif system_metrics.disk_usage > 80:
                warnings.append(f"Elevated disk usage: {system_metrics.disk_usage:.1f}%")
        
        # Check active alerts
        active_alerts = [alert for alert in self.alerts.values() if not alert.resolved]
        critical_alerts = [alert for alert in active_alerts if alert.severity == 'critical']
        
        if critical_alerts:
            issues.extend([f"Critical alert: {alert.title}" for alert in critical_alerts[:3]])
        
        # Determine overall status
        if issues:
            status = 'critical'
            message = f"{len(issues)} critical issues detected"
        elif warnings:
            status = 'warning'
            message = f"{len(warnings)} warnings detected"
        else:
            status = 'healthy'
            message = 'All systems operating normally'
        
        return {
            'status': status,
            'message': message,
            'issues': issues,
            'warnings': warnings,
            'active_alerts': len(active_alerts),
            'last_update': datetime.now().isoformat()
        }

# Global instance
enhanced_monitoring_service = EnhancedMonitoringService()