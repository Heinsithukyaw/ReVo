"""
System Metrics Collector for Phase 4 Comprehensive Monitoring

Collects system-level metrics including CPU, memory, disk usage, network I/O,
and service-specific resource consumption.
"""

import asyncio
import psutil
import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json
import aiofiles
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """System metrics data structure"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float
    network_bytes_sent: int
    network_bytes_recv: int
    load_average: List[float]
    process_count: int
    open_files: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

@dataclass
class ServiceMetrics:
    """Service-specific metrics"""
    service_name: str
    pid: int
    cpu_percent: float
    memory_percent: float
    memory_rss_mb: float
    memory_vms_mb: float
    num_threads: int
    num_fds: int
    status: str
    create_time: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['create_time'] = self.create_time.isoformat()
        return data

class SystemMetricsCollector:
    """
    Comprehensive system metrics collector with service-specific monitoring
    """
    
    def __init__(self, 
                 collection_interval: float = 30.0,
                 retention_hours: int = 24,
                 storage_path: str = "monitoring/metrics"):
        self.collection_interval = collection_interval
        self.retention_hours = retention_hours
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.is_collecting = False
        self.metrics_history: List[SystemMetrics] = []
        self.service_metrics_history: Dict[str, List[ServiceMetrics]] = {}
        
        # Service monitoring configuration
        self.monitored_services = {
            'revoagent-api': ['python', 'uvicorn', 'fastapi'],
            'revoagent-backend': ['python', 'backend'],
            'revoagent-frontend': ['node', 'npm', 'vite'],
            'revoagent-memory': ['python', 'memory'],
            'redis': ['redis-server'],
            'postgres': ['postgres'],
            'nginx': ['nginx']
        }
        
        logger.info(f"SystemMetricsCollector initialized with {collection_interval}s interval")
    
    async def start_collection(self):
        """Start continuous metrics collection"""
        if self.is_collecting:
            logger.warning("Metrics collection already running")
            return
        
        self.is_collecting = True
        logger.info("Starting system metrics collection")
        
        try:
            while self.is_collecting:
                await self._collect_metrics()
                await asyncio.sleep(self.collection_interval)
        except Exception as e:
            logger.error(f"Error in metrics collection: {e}")
            self.is_collecting = False
    
    async def stop_collection(self):
        """Stop metrics collection"""
        self.is_collecting = False
        logger.info("Stopped system metrics collection")
    
    async def _collect_metrics(self):
        """Collect system and service metrics"""
        try:
            # Collect system metrics
            system_metrics = await self._collect_system_metrics()
            self.metrics_history.append(system_metrics)
            
            # Collect service metrics
            service_metrics = await self._collect_service_metrics()
            for service_name, metrics in service_metrics.items():
                if service_name not in self.service_metrics_history:
                    self.service_metrics_history[service_name] = []
                self.service_metrics_history[service_name].append(metrics)
            
            # Clean old metrics
            await self._cleanup_old_metrics()
            
            # Save metrics to storage
            await self._save_metrics(system_metrics, service_metrics)
            
            logger.debug(f"Collected metrics at {system_metrics.timestamp}")
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
    
    async def _collect_system_metrics(self) -> SystemMetrics:
        """Collect system-level metrics"""
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory metrics
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_gb = memory.used / (1024**3)
        memory_total_gb = memory.total / (1024**3)
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        disk_used_gb = disk.used / (1024**3)
        disk_total_gb = disk.total / (1024**3)
        
        # Network metrics
        network = psutil.net_io_counters()
        network_bytes_sent = network.bytes_sent
        network_bytes_recv = network.bytes_recv
        
        # Load average
        load_average = list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else [0.0, 0.0, 0.0]
        
        # Process metrics
        process_count = len(psutil.pids())
        
        # Open files count
        try:
            open_files = len(psutil.Process().open_files())
        except:
            open_files = 0
        
        return SystemMetrics(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_used_gb=memory_used_gb,
            memory_total_gb=memory_total_gb,
            disk_percent=disk_percent,
            disk_used_gb=disk_used_gb,
            disk_total_gb=disk_total_gb,
            network_bytes_sent=network_bytes_sent,
            network_bytes_recv=network_bytes_recv,
            load_average=load_average,
            process_count=process_count,
            open_files=open_files
        )
    
    async def _collect_service_metrics(self) -> Dict[str, ServiceMetrics]:
        """Collect service-specific metrics"""
        service_metrics = {}
        
        for service_name, process_names in self.monitored_services.items():
            try:
                process = await self._find_service_process(process_names)
                if process:
                    metrics = await self._get_process_metrics(service_name, process)
                    service_metrics[service_name] = metrics
            except Exception as e:
                logger.warning(f"Could not collect metrics for {service_name}: {e}")
        
        return service_metrics
    
    async def _find_service_process(self, process_names: List[str]) -> Optional[psutil.Process]:
        """Find process by name patterns"""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                proc_info = proc.info
                proc_name = proc_info['name'].lower()
                cmdline = ' '.join(proc_info['cmdline']).lower() if proc_info['cmdline'] else ''
                
                for pattern in process_names:
                    if pattern.lower() in proc_name or pattern.lower() in cmdline:
                        return proc
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return None
    
    async def _get_process_metrics(self, service_name: str, process: psutil.Process) -> ServiceMetrics:
        """Get metrics for a specific process"""
        try:
            with process.oneshot():
                memory_info = process.memory_info()
                
                return ServiceMetrics(
                    service_name=service_name,
                    pid=process.pid,
                    cpu_percent=process.cpu_percent(),
                    memory_percent=process.memory_percent(),
                    memory_rss_mb=memory_info.rss / (1024**2),
                    memory_vms_mb=memory_info.vms / (1024**2),
                    num_threads=process.num_threads(),
                    num_fds=process.num_fds() if hasattr(process, 'num_fds') else 0,
                    status=process.status(),
                    create_time=datetime.fromtimestamp(process.create_time())
                )
        except Exception as e:
            logger.error(f"Error getting process metrics for {service_name}: {e}")
            raise
    
    async def _cleanup_old_metrics(self):
        """Remove metrics older than retention period"""
        cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)
        
        # Clean system metrics
        self.metrics_history = [
            m for m in self.metrics_history 
            if m.timestamp > cutoff_time
        ]
        
        # Clean service metrics
        for service_name in self.service_metrics_history:
            self.service_metrics_history[service_name] = [
                m for m in self.service_metrics_history[service_name]
                if m.create_time > cutoff_time
            ]
    
    async def _save_metrics(self, system_metrics: SystemMetrics, service_metrics: Dict[str, ServiceMetrics]):
        """Save metrics to persistent storage"""
        try:
            timestamp_str = system_metrics.timestamp.strftime("%Y%m%d_%H%M%S")
            
            # Save system metrics
            system_file = self.storage_path / f"system_metrics_{timestamp_str}.json"
            async with aiofiles.open(system_file, 'w') as f:
                await f.write(json.dumps(system_metrics.to_dict(), indent=2))
            
            # Save service metrics
            if service_metrics:
                service_file = self.storage_path / f"service_metrics_{timestamp_str}.json"
                service_data = {name: metrics.to_dict() for name, metrics in service_metrics.items()}
                async with aiofiles.open(service_file, 'w') as f:
                    await f.write(json.dumps(service_data, indent=2))
            
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")
    
    def get_current_metrics(self) -> Optional[SystemMetrics]:
        """Get the most recent system metrics"""
        return self.metrics_history[-1] if self.metrics_history else None
    
    def get_service_metrics(self, service_name: str) -> List[ServiceMetrics]:
        """Get metrics for a specific service"""
        return self.service_metrics_history.get(service_name, [])
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of collected metrics"""
        if not self.metrics_history:
            return {"status": "no_data"}
        
        recent_metrics = self.metrics_history[-10:]  # Last 10 measurements
        
        return {
            "status": "active" if self.is_collecting else "stopped",
            "collection_interval": self.collection_interval,
            "total_measurements": len(self.metrics_history),
            "retention_hours": self.retention_hours,
            "current_metrics": self.get_current_metrics().to_dict() if self.get_current_metrics() else None,
            "average_cpu": sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics),
            "average_memory": sum(m.memory_percent for m in recent_metrics) / len(recent_metrics),
            "monitored_services": list(self.service_metrics_history.keys()),
            "service_count": len(self.service_metrics_history)
        }
    
    async def get_performance_trends(self, hours: int = 1) -> Dict[str, Any]:
        """Analyze performance trends over specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [m for m in self.metrics_history if m.timestamp > cutoff_time]
        
        if not recent_metrics:
            return {"status": "insufficient_data"}
        
        # Calculate trends
        cpu_values = [m.cpu_percent for m in recent_metrics]
        memory_values = [m.memory_percent for m in recent_metrics]
        
        return {
            "time_period_hours": hours,
            "measurements_count": len(recent_metrics),
            "cpu_trend": {
                "min": min(cpu_values),
                "max": max(cpu_values),
                "avg": sum(cpu_values) / len(cpu_values),
                "current": cpu_values[-1] if cpu_values else 0
            },
            "memory_trend": {
                "min": min(memory_values),
                "max": max(memory_values),
                "avg": sum(memory_values) / len(memory_values),
                "current": memory_values[-1] if memory_values else 0
            },
            "alerts": await self._generate_performance_alerts(recent_metrics)
        }
    
    async def _generate_performance_alerts(self, metrics: List[SystemMetrics]) -> List[Dict[str, Any]]:
        """Generate performance alerts based on metrics"""
        alerts = []
        
        if not metrics:
            return alerts
        
        latest = metrics[-1]
        
        # CPU alerts
        if latest.cpu_percent > 90:
            alerts.append({
                "type": "critical",
                "metric": "cpu",
                "value": latest.cpu_percent,
                "threshold": 90,
                "message": f"Critical CPU usage: {latest.cpu_percent:.1f}%"
            })
        elif latest.cpu_percent > 75:
            alerts.append({
                "type": "warning",
                "metric": "cpu",
                "value": latest.cpu_percent,
                "threshold": 75,
                "message": f"High CPU usage: {latest.cpu_percent:.1f}%"
            })
        
        # Memory alerts
        if latest.memory_percent > 90:
            alerts.append({
                "type": "critical",
                "metric": "memory",
                "value": latest.memory_percent,
                "threshold": 90,
                "message": f"Critical memory usage: {latest.memory_percent:.1f}%"
            })
        elif latest.memory_percent > 80:
            alerts.append({
                "type": "warning",
                "metric": "memory",
                "value": latest.memory_percent,
                "threshold": 80,
                "message": f"High memory usage: {latest.memory_percent:.1f}%"
            })
        
        # Disk alerts
        if latest.disk_percent > 95:
            alerts.append({
                "type": "critical",
                "metric": "disk",
                "value": latest.disk_percent,
                "threshold": 95,
                "message": f"Critical disk usage: {latest.disk_percent:.1f}%"
            })
        elif latest.disk_percent > 85:
            alerts.append({
                "type": "warning",
                "metric": "disk",
                "value": latest.disk_percent,
                "threshold": 85,
                "message": f"High disk usage: {latest.disk_percent:.1f}%"
            })
        
        return alerts

# Global instance
_system_metrics_collector = None

async def get_system_metrics_collector() -> SystemMetricsCollector:
    """Get or create global system metrics collector instance"""
    global _system_metrics_collector
    if _system_metrics_collector is None:
        _system_metrics_collector = SystemMetricsCollector()
    return _system_metrics_collector