"""
Phase 4 Monitoring System - Comprehensive Monitoring & Continuous Improvement

Unified monitoring system that integrates all Phase 4 components:
- System Metrics Collection
- Application Metrics & Tracing
- Performance Profiling
- Alert Management
- Load Testing
- Continuous Optimization
- Health Dashboard
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json
import aiofiles
from pathlib import Path

from .system_metrics import SystemMetricsCollector, get_system_metrics_collector
from .application_metrics import ApplicationMetricsCollector, get_app_metrics_collector
from .performance_profiler import PerformanceProfiler, get_performance_profiler
from .alert_manager import AlertManager, get_alert_manager, NotificationChannel
from .load_tester import LoadTester, get_load_tester, LoadTestConfig, LoadTestType
from .continuous_optimizer import ContinuousOptimizer, get_continuous_optimizer
from .health_dashboard import HealthDashboard, get_health_dashboard

logger = logging.getLogger(__name__)

@dataclass
class Phase4Config:
    """Phase 4 monitoring system configuration"""
    system_metrics_interval: float = 30.0
    app_metrics_retention_hours: int = 72
    performance_profile_interval: float = 300.0
    alert_check_interval: float = 30.0
    optimization_analysis_interval: float = 300.0
    dashboard_update_interval: float = 30.0
    load_testing_enabled: bool = True
    auto_optimization_enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)

@dataclass
class MonitoringStatus:
    """Overall monitoring system status"""
    is_running: bool
    start_time: datetime
    components_status: Dict[str, str]
    total_metrics_collected: int
    active_alerts: int
    optimization_recommendations: int
    last_health_check: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['start_time'] = self.start_time.isoformat()
        data['last_health_check'] = self.last_health_check.isoformat()
        return data

class Phase4MonitoringSystem:
    """
    Comprehensive Phase 4 monitoring system that orchestrates all monitoring components
    """
    
    def __init__(self, config: Optional[Phase4Config] = None):
        self.config = config or Phase4Config()
        self.storage_path = Path("monitoring/phase4")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Component instances
        self.system_metrics: Optional[SystemMetricsCollector] = None
        self.app_metrics: Optional[ApplicationMetricsCollector] = None
        self.performance_profiler: Optional[PerformanceProfiler] = None
        self.alert_manager: Optional[AlertManager] = None
        self.load_tester: Optional[LoadTester] = None
        self.continuous_optimizer: Optional[ContinuousOptimizer] = None
        self.health_dashboard: Optional[HealthDashboard] = None
        
        # System state
        self.is_running = False
        self.start_time: Optional[datetime] = None
        self.component_tasks: List[asyncio.Task] = []
        
        # Integration state
        self.metric_providers_registered = False
        self.alert_rules_configured = False
        self.optimization_enabled = False
        
        logger.info("Phase4MonitoringSystem initialized")
    
    async def initialize(self):
        """Initialize all monitoring components"""
        try:
            logger.info("Initializing Phase 4 monitoring components...")
            
            # Initialize components
            self.system_metrics = await get_system_metrics_collector()
            self.app_metrics = await get_app_metrics_collector()
            self.performance_profiler = await get_performance_profiler()
            self.alert_manager = await get_alert_manager()
            self.load_tester = await get_load_tester()
            self.continuous_optimizer = await get_continuous_optimizer()
            self.health_dashboard = await get_health_dashboard()
            
            # Configure component integration
            await self._setup_component_integration()
            
            # Configure alert notifications
            await self._setup_alert_notifications()
            
            # Setup default load tests
            await self._setup_default_load_tests()
            
            logger.info("Phase 4 monitoring components initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing Phase 4 monitoring system: {e}")
            raise
    
    async def _setup_component_integration(self):
        """Setup integration between monitoring components"""
        try:
            # Register metric providers for alert manager
            self.alert_manager.add_metric_provider(self._get_system_metrics_for_alerts)
            self.alert_manager.add_metric_provider(self._get_app_metrics_for_alerts)
            
            # Register metric providers for continuous optimizer
            self.continuous_optimizer.add_metric_provider(self._get_system_metrics_for_optimization)
            self.continuous_optimizer.add_metric_provider(self._get_app_metrics_for_optimization)
            
            # Register metric providers for health dashboard
            self.health_dashboard.add_metric_provider("system_metrics", self._get_system_metrics_for_dashboard)
            self.health_dashboard.add_metric_provider("app_metrics", self._get_app_metrics_for_dashboard)
            
            self.metric_providers_registered = True
            logger.info("Component integration setup completed")
            
        except Exception as e:
            logger.error(f"Error setting up component integration: {e}")
            raise
    
    async def _setup_alert_notifications(self):
        """Setup alert notification channels"""
        try:
            # Configure Slack notifications (if webhook URL is available)
            slack_config = {
                'webhook_url': 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'  # Replace with actual URL
            }
            self.alert_manager.configure_notification_channel(NotificationChannel.SLACK, slack_config)
            
            # Configure email notifications
            email_config = {
                'smtp_server': 'localhost',
                'smtp_port': 587,
                'username': 'monitoring@revoagent.com',
                'password': 'your_password',
                'from_email': 'monitoring@revoagent.com',
                'to_emails': ['admin@revoagent.com', 'ops@revoagent.com']
            }
            self.alert_manager.configure_notification_channel(NotificationChannel.EMAIL, email_config)
            
            # Configure webhook notifications
            webhook_config = {
                'url': 'http://localhost:8000/api/v1/webhooks/alerts'
            }
            self.alert_manager.configure_notification_channel(NotificationChannel.WEBHOOK, webhook_config)
            
            self.alert_rules_configured = True
            logger.info("Alert notification channels configured")
            
        except Exception as e:
            logger.error(f"Error setting up alert notifications: {e}")
    
    async def _setup_default_load_tests(self):
        """Setup default load test configurations"""
        try:
            if not self.config.load_testing_enabled:
                return
            
            # Schedule periodic load tests
            asyncio.create_task(self._periodic_load_testing())
            
            logger.info("Default load tests configured")
            
        except Exception as e:
            logger.error(f"Error setting up default load tests: {e}")
    
    async def start(self):
        """Start the comprehensive monitoring system"""
        if self.is_running:
            logger.warning("Phase 4 monitoring system already running")
            return
        
        try:
            # Initialize if not already done
            if not self.system_metrics:
                await self.initialize()
            
            self.is_running = True
            self.start_time = datetime.now()
            
            logger.info("Starting Phase 4 comprehensive monitoring system...")
            
            # Start all components
            await self._start_all_components()
            
            # Start integration tasks
            await self._start_integration_tasks()
            
            logger.info("Phase 4 monitoring system started successfully")
            
        except Exception as e:
            logger.error(f"Error starting Phase 4 monitoring system: {e}")
            self.is_running = False
            raise
    
    async def _start_all_components(self):
        """Start all monitoring components"""
        try:
            # Start system metrics collection
            await self.system_metrics.start_collection()
            
            # Start performance profiling
            await self.performance_profiler.start_profiling()
            
            # Start alert manager
            await self.alert_manager.start()
            
            # Start continuous optimizer
            await self.continuous_optimizer.start()
            
            # Start health dashboard
            await self.health_dashboard.start()
            
            logger.info("All monitoring components started")
            
        except Exception as e:
            logger.error(f"Error starting monitoring components: {e}")
            raise
    
    async def _start_integration_tasks(self):
        """Start integration and coordination tasks"""
        try:
            # Start application metrics aggregation
            task1 = asyncio.create_task(self._app_metrics_aggregation_loop())
            self.component_tasks.append(task1)
            
            # Start system health monitoring
            task2 = asyncio.create_task(self._system_health_monitoring_loop())
            self.component_tasks.append(task2)
            
            # Start optimization automation (if enabled)
            if self.config.auto_optimization_enabled:
                task3 = asyncio.create_task(self._auto_optimization_loop())
                self.component_tasks.append(task3)
            
            # Start monitoring data persistence
            task4 = asyncio.create_task(self._data_persistence_loop())
            self.component_tasks.append(task4)
            
            logger.info("Integration tasks started")
            
        except Exception as e:
            logger.error(f"Error starting integration tasks: {e}")
            raise
    
    async def stop(self):
        """Stop the comprehensive monitoring system"""
        if not self.is_running:
            logger.warning("Phase 4 monitoring system not running")
            return
        
        try:
            logger.info("Stopping Phase 4 monitoring system...")
            
            self.is_running = False
            
            # Cancel integration tasks
            for task in self.component_tasks:
                task.cancel()
            
            # Stop all components
            await self._stop_all_components()
            
            logger.info("Phase 4 monitoring system stopped")
            
        except Exception as e:
            logger.error(f"Error stopping Phase 4 monitoring system: {e}")
    
    async def _stop_all_components(self):
        """Stop all monitoring components"""
        try:
            if self.system_metrics:
                await self.system_metrics.stop_collection()
            
            if self.performance_profiler:
                await self.performance_profiler.stop_profiling()
            
            if self.alert_manager:
                await self.alert_manager.stop()
            
            if self.continuous_optimizer:
                await self.continuous_optimizer.stop()
            
            if self.health_dashboard:
                await self.health_dashboard.stop()
            
            logger.info("All monitoring components stopped")
            
        except Exception as e:
            logger.error(f"Error stopping monitoring components: {e}")
    
    async def _app_metrics_aggregation_loop(self):
        """Application metrics aggregation loop"""
        while self.is_running:
            try:
                await self.app_metrics.aggregate_metrics()
                await asyncio.sleep(60)  # Aggregate every minute
            except Exception as e:
                logger.error(f"Error in app metrics aggregation: {e}")
                await asyncio.sleep(10)
    
    async def _system_health_monitoring_loop(self):
        """System health monitoring loop"""
        while self.is_running:
            try:
                # Perform comprehensive health check
                health_status = await self._perform_health_check()
                
                # Log health status
                if health_status['overall_status'] != 'healthy':
                    logger.warning(f"System health check: {health_status['overall_status']}")
                
                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                logger.error(f"Error in system health monitoring: {e}")
                await asyncio.sleep(30)
    
    async def _auto_optimization_loop(self):
        """Automatic optimization implementation loop"""
        while self.is_running:
            try:
                # Get high-priority recommendations
                recommendations = self.continuous_optimizer.get_recommendations(
                    priority=None,  # All priorities
                    status=None     # All statuses
                )
                
                # Auto-implement low-risk optimizations
                for rec in recommendations:
                    if (rec.priority.value in ['medium', 'low'] and 
                        rec.status.value == 'pending' and
                        'low risk' in rec.implementation_effort.lower()):
                        
                        logger.info(f"Auto-implementing optimization: {rec.title}")
                        await self.continuous_optimizer.implement_recommendation(
                            rec.id, 
                            "Auto-implemented by Phase 4 monitoring system"
                        )
                
                await asyncio.sleep(3600)  # Check every hour
            except Exception as e:
                logger.error(f"Error in auto-optimization: {e}")
                await asyncio.sleep(300)
    
    async def _data_persistence_loop(self):
        """Data persistence and cleanup loop"""
        while self.is_running:
            try:
                # Save monitoring status
                await self._save_monitoring_status()
                
                # Cleanup old data
                await self._cleanup_old_monitoring_data()
                
                await asyncio.sleep(1800)  # Every 30 minutes
            except Exception as e:
                logger.error(f"Error in data persistence: {e}")
                await asyncio.sleep(300)
    
    async def _periodic_load_testing(self):
        """Periodic load testing execution"""
        while self.is_running:
            try:
                if not self.config.load_testing_enabled:
                    await asyncio.sleep(3600)
                    continue
                
                # Run daily smoke test
                smoke_config = LoadTestConfig(
                    name="Daily Smoke Test",
                    test_type=LoadTestType.SMOKE,
                    target_url="http://localhost:8000/health",
                    duration_seconds=60,
                    concurrent_users=5
                )
                
                test_id = await self.load_tester.run_load_test(smoke_config)
                logger.info(f"Started daily smoke test: {test_id}")
                
                # Wait 24 hours for next test
                await asyncio.sleep(86400)
                
            except Exception as e:
                logger.error(f"Error in periodic load testing: {e}")
                await asyncio.sleep(3600)
    
    async def _get_system_metrics_for_alerts(self) -> Dict[str, float]:
        """Get system metrics for alert evaluation"""
        try:
            current_metrics = self.system_metrics.get_current_metrics()
            if not current_metrics:
                return {}
            
            return {
                'cpu_percent': current_metrics.cpu_percent,
                'memory_percent': current_metrics.memory_percent,
                'disk_percent': current_metrics.disk_percent
            }
        except Exception as e:
            logger.error(f"Error getting system metrics for alerts: {e}")
            return {}
    
    async def _get_app_metrics_for_alerts(self) -> Dict[str, float]:
        """Get application metrics for alert evaluation"""
        try:
            api_performance = self.app_metrics.get_api_performance()
            if api_performance.get('status') == 'no_data':
                return {}
            
            return {
                'error_rate': api_performance.get('overall_error_rate', 0),
                'avg_response_time_ms': api_performance.get('avg_response_time_ms', 0)
            }
        except Exception as e:
            logger.error(f"Error getting app metrics for alerts: {e}")
            return {}
    
    async def _get_system_metrics_for_optimization(self) -> Dict[str, float]:
        """Get system metrics for optimization analysis"""
        return await self._get_system_metrics_for_alerts()
    
    async def _get_app_metrics_for_optimization(self) -> Dict[str, float]:
        """Get application metrics for optimization analysis"""
        return await self._get_app_metrics_for_alerts()
    
    async def _get_system_metrics_for_dashboard(self) -> Dict[str, float]:
        """Get system metrics for dashboard display"""
        return await self._get_system_metrics_for_alerts()
    
    async def _get_app_metrics_for_dashboard(self) -> Dict[str, float]:
        """Get application metrics for dashboard display"""
        return await self._get_app_metrics_for_alerts()
    
    async def _perform_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive system health check"""
        try:
            health_status = {
                'overall_status': 'healthy',
                'components': {},
                'timestamp': datetime.now().isoformat()
            }
            
            # Check system metrics
            system_metrics = self.system_metrics.get_current_metrics()
            if system_metrics:
                if system_metrics.cpu_percent > 90 or system_metrics.memory_percent > 90:
                    health_status['overall_status'] = 'critical'
                elif system_metrics.cpu_percent > 75 or system_metrics.memory_percent > 80:
                    health_status['overall_status'] = 'warning'
                
                health_status['components']['system_metrics'] = {
                    'status': 'healthy' if system_metrics.cpu_percent < 75 else 'warning',
                    'cpu_percent': system_metrics.cpu_percent,
                    'memory_percent': system_metrics.memory_percent
                }
            
            # Check application metrics
            app_summary = self.app_metrics.get_metrics_summary()
            health_status['components']['app_metrics'] = {
                'status': 'healthy',
                'active_traces': app_summary.get('active_traces_count', 0),
                'business_metrics': app_summary.get('business_metrics_count', 0)
            }
            
            # Check alert manager
            alert_summary = self.alert_manager.get_alert_summary()
            critical_alerts = alert_summary.get('alerts_by_severity', {}).get('critical', 0)
            health_status['components']['alert_manager'] = {
                'status': 'critical' if critical_alerts > 0 else 'healthy',
                'active_alerts': alert_summary.get('active_alerts', 0),
                'critical_alerts': critical_alerts
            }
            
            # Update overall status based on components
            if any(comp.get('status') == 'critical' for comp in health_status['components'].values()):
                health_status['overall_status'] = 'critical'
            elif any(comp.get('status') == 'warning' for comp in health_status['components'].values()):
                if health_status['overall_status'] == 'healthy':
                    health_status['overall_status'] = 'warning'
            
            return health_status
            
        except Exception as e:
            logger.error(f"Error performing health check: {e}")
            return {
                'overall_status': 'unknown',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _save_monitoring_status(self):
        """Save current monitoring status"""
        try:
            status = await self.get_monitoring_status()
            
            status_file = self.storage_path / f"monitoring_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            async with aiofiles.open(status_file, 'w') as f:
                await f.write(json.dumps(status.to_dict(), indent=2))
                
        except Exception as e:
            logger.error(f"Error saving monitoring status: {e}")
    
    async def _cleanup_old_monitoring_data(self):
        """Cleanup old monitoring data files"""
        try:
            cutoff_time = datetime.now() - timedelta(days=7)  # Keep 7 days
            
            for file_path in self.storage_path.glob("monitoring_status_*.json"):
                try:
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_time:
                        file_path.unlink()
                except Exception as e:
                    logger.warning(f"Error cleaning up file {file_path}: {e}")
                    
        except Exception as e:
            logger.error(f"Error cleaning up old monitoring data: {e}")
    
    async def get_monitoring_status(self) -> MonitoringStatus:
        """Get comprehensive monitoring system status"""
        try:
            # Get component statuses
            components_status = {}
            
            if self.system_metrics:
                components_status['system_metrics'] = 'running' if self.system_metrics.is_collecting else 'stopped'
            
            if self.performance_profiler:
                components_status['performance_profiler'] = 'running' if self.performance_profiler.is_profiling else 'stopped'
            
            if self.alert_manager:
                components_status['alert_manager'] = 'running' if self.alert_manager.is_running else 'stopped'
            
            if self.continuous_optimizer:
                components_status['continuous_optimizer'] = 'running' if self.continuous_optimizer.is_running else 'stopped'
            
            if self.health_dashboard:
                components_status['health_dashboard'] = 'running' if self.health_dashboard.is_running else 'stopped'
            
            # Count metrics and alerts
            total_metrics = 0
            if self.system_metrics:
                total_metrics += len(self.system_metrics.metrics_history)
            if self.app_metrics:
                total_metrics += self.app_metrics.get_metrics_summary().get('business_metrics_count', 0)
            
            active_alerts = 0
            optimization_recommendations = 0
            if self.alert_manager:
                active_alerts = self.alert_manager.get_alert_summary().get('active_alerts', 0)
            if self.continuous_optimizer:
                optimization_recommendations = len(self.continuous_optimizer.get_recommendations())
            
            return MonitoringStatus(
                is_running=self.is_running,
                start_time=self.start_time or datetime.now(),
                components_status=components_status,
                total_metrics_collected=total_metrics,
                active_alerts=active_alerts,
                optimization_recommendations=optimization_recommendations,
                last_health_check=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error getting monitoring status: {e}")
            return MonitoringStatus(
                is_running=False,
                start_time=datetime.now(),
                components_status={'error': str(e)},
                total_metrics_collected=0,
                active_alerts=0,
                optimization_recommendations=0,
                last_health_check=datetime.now()
            )
    
    def get_system_summary(self) -> Dict[str, Any]:
        """Get comprehensive system summary"""
        try:
            summary = {
                'phase4_monitoring': {
                    'is_running': self.is_running,
                    'start_time': self.start_time.isoformat() if self.start_time else None,
                    'config': self.config.to_dict()
                }
            }
            
            # Add component summaries
            if self.system_metrics:
                summary['system_metrics'] = self.system_metrics.get_metrics_summary()
            
            if self.app_metrics:
                summary['app_metrics'] = self.app_metrics.get_metrics_summary()
            
            if self.performance_profiler:
                summary['performance_profiler'] = self.performance_profiler.get_performance_summary()
            
            if self.alert_manager:
                summary['alert_manager'] = self.alert_manager.get_alert_summary()
            
            if self.load_tester:
                summary['load_tester'] = self.load_tester.get_load_test_summary()
            
            if self.continuous_optimizer:
                summary['continuous_optimizer'] = self.continuous_optimizer.get_optimization_summary()
            
            if self.health_dashboard:
                summary['health_dashboard'] = self.health_dashboard.get_dashboard_summary()
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting system summary: {e}")
            return {'error': str(e)}

# Global instance
_phase4_monitoring_system = None

async def get_phase4_monitoring_system(config: Optional[Phase4Config] = None) -> Phase4MonitoringSystem:
    """Get or create global Phase 4 monitoring system instance"""
    global _phase4_monitoring_system
    if _phase4_monitoring_system is None:
        _phase4_monitoring_system = Phase4MonitoringSystem(config)
    return _phase4_monitoring_system