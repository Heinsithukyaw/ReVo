"""
Resource Manager - System Resource Optimization and Monitoring

Manages system resources, monitors performance, and optimizes resource allocation
for efficient agent and model execution.
"""

import asyncio
import logging
import psutil
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class ResourceType(Enum):
    """Types of system resources."""
    CPU = "cpu"
    MEMORY = "memory"
    GPU = "gpu"
    DISK = "disk"
    NETWORK = "network"


class ResourceStatus(Enum):
    """Resource status levels."""
    OPTIMAL = "optimal"
    WARNING = "warning"
    CRITICAL = "critical"
    UNAVAILABLE = "unavailable"


@dataclass
class ResourceMetrics:
    """Resource usage metrics."""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_available_gb: float
    disk_usage_percent: float
    disk_free_gb: float
    gpu_memory_percent: float = 0.0
    gpu_memory_free_gb: float = 0.0
    network_bytes_sent: int = 0
    network_bytes_recv: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "memory_available_gb": self.memory_available_gb,
            "disk_usage_percent": self.disk_usage_percent,
            "disk_free_gb": self.disk_free_gb,
            "gpu_memory_percent": self.gpu_memory_percent,
            "gpu_memory_free_gb": self.gpu_memory_free_gb,
            "network_bytes_sent": self.network_bytes_sent,
            "network_bytes_recv": self.network_bytes_recv
        }


@dataclass
class ResourceLimits:
    """Resource usage limits and thresholds."""
    max_cpu_percent: float = 80.0
    max_memory_percent: float = 85.0
    min_disk_free_gb: float = 5.0
    max_gpu_memory_percent: float = 90.0
    warning_cpu_percent: float = 70.0
    warning_memory_percent: float = 75.0
    warning_disk_free_gb: float = 10.0
    warning_gpu_memory_percent: float = 80.0


@dataclass
class ResourceAllocation:
    """Resource allocation for a specific task/agent."""
    task_id: str
    agent_id: str
    cpu_cores: Optional[int] = None
    memory_gb: Optional[float] = None
    gpu_memory_gb: Optional[float] = None
    priority: int = 5  # 1-10, higher is more important
    allocated_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None


class ResourceMonitor:
    """Monitors system resource usage."""
    
    def __init__(self, 
                 collection_interval: float = 5.0,
                 history_size: int = 1000):
        self.collection_interval = collection_interval
        self.history_size = history_size
        self.metrics_history: List[ResourceMetrics] = []
        self.is_monitoring = False
        self.monitor_task: Optional[asyncio.Task] = None
        
        # Callbacks
        self.on_metrics_collected: Optional[Callable[[ResourceMetrics], None]] = None
        self.on_threshold_exceeded: Optional[Callable[[ResourceType, float], None]] = None
    
    async def start_monitoring(self):
        """Start resource monitoring."""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Resource monitoring started")
    
    async def stop_monitoring(self):
        """Stop resource monitoring."""
        self.is_monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
            self.monitor_task = None
        logger.info("Resource monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.is_monitoring:
            try:
                metrics = await self._collect_metrics()
                self.metrics_history.append(metrics)
                
                # Maintain history size
                if len(self.metrics_history) > self.history_size:
                    self.metrics_history.pop(0)
                
                # Trigger callback
                if self.on_metrics_collected:
                    self.on_metrics_collected(metrics)
                
                await asyncio.sleep(self.collection_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.collection_interval)
    
    async def _collect_metrics(self) -> ResourceMetrics:
        """Collect current resource metrics."""
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory metrics
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_available_gb = memory.available / (1024**3)
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        disk_usage_percent = (disk.used / disk.total) * 100
        disk_free_gb = disk.free / (1024**3)
        
        # Network metrics
        network = psutil.net_io_counters()
        network_bytes_sent = network.bytes_sent
        network_bytes_recv = network.bytes_recv
        
        # GPU metrics (if available)
        gpu_memory_percent = 0.0
        gpu_memory_free_gb = 0.0
        
        try:
            import torch
            if torch.cuda.is_available():
                gpu_memory_total = torch.cuda.get_device_properties(0).total_memory
                gpu_memory_allocated = torch.cuda.memory_allocated(0)
                gpu_memory_percent = (gpu_memory_allocated / gpu_memory_total) * 100
                gpu_memory_free_gb = (gpu_memory_total - gpu_memory_allocated) / (1024**3)
        except ImportError:
            pass
        
        return ResourceMetrics(
            timestamp=time.time(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_available_gb=memory_available_gb,
            disk_usage_percent=disk_usage_percent,
            disk_free_gb=disk_free_gb,
            gpu_memory_percent=gpu_memory_percent,
            gpu_memory_free_gb=gpu_memory_free_gb,
            network_bytes_sent=network_bytes_sent,
            network_bytes_recv=network_bytes_recv
        )
    
    def get_current_metrics(self) -> Optional[ResourceMetrics]:
        """Get the most recent metrics."""
        return self.metrics_history[-1] if self.metrics_history else None
    
    def get_metrics_history(self, 
                          duration_minutes: Optional[int] = None) -> List[ResourceMetrics]:
        """Get metrics history for a specific duration."""
        if not duration_minutes:
            return self.metrics_history.copy()
        
        cutoff_time = time.time() - (duration_minutes * 60)
        return [m for m in self.metrics_history if m.timestamp >= cutoff_time]
    
    def get_average_metrics(self, 
                          duration_minutes: int = 10) -> Optional[ResourceMetrics]:
        """Get average metrics over a duration."""
        metrics = self.get_metrics_history(duration_minutes)
        if not metrics:
            return None
        
        return ResourceMetrics(
            timestamp=time.time(),
            cpu_percent=sum(m.cpu_percent for m in metrics) / len(metrics),
            memory_percent=sum(m.memory_percent for m in metrics) / len(metrics),
            memory_available_gb=sum(m.memory_available_gb for m in metrics) / len(metrics),
            disk_usage_percent=sum(m.disk_usage_percent for m in metrics) / len(metrics),
            disk_free_gb=sum(m.disk_free_gb for m in metrics) / len(metrics),
            gpu_memory_percent=sum(m.gpu_memory_percent for m in metrics) / len(metrics),
            gpu_memory_free_gb=sum(m.gpu_memory_free_gb for m in metrics) / len(metrics),
            network_bytes_sent=sum(m.network_bytes_sent for m in metrics) / len(metrics),
            network_bytes_recv=sum(m.network_bytes_recv for m in metrics) / len(metrics)
        )


class ResourceManager:
    """Manages system resources and optimizes allocation."""
    
    def __init__(self, 
                 limits: Optional[ResourceLimits] = None,
                 storage_path: Optional[Path] = None):
        self.limits = limits or ResourceLimits()
        self.storage_path = storage_path or Path("resources")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.monitor = ResourceMonitor()
        self.allocations: Dict[str, ResourceAllocation] = {}
        self.resource_locks: Dict[ResourceType, asyncio.Lock] = {
            resource_type: asyncio.Lock() for resource_type in ResourceType
        }
        
        # Setup monitoring callbacks
        self.monitor.on_metrics_collected = self._on_metrics_collected
        self.monitor.on_threshold_exceeded = self._on_threshold_exceeded
        
        # Optimization settings
        self.auto_optimization_enabled = True
        self.optimization_interval = 60.0  # seconds
        self.optimization_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the resource manager."""
        await self.monitor.start_monitoring()
        
        if self.auto_optimization_enabled:
            self.optimization_task = asyncio.create_task(self._optimization_loop())
        
        logger.info("Resource manager started")
    
    async def stop(self):
        """Stop the resource manager."""
        await self.monitor.stop_monitoring()
        
        if self.optimization_task:
            self.optimization_task.cancel()
            try:
                await self.optimization_task
            except asyncio.CancelledError:
                pass
            self.optimization_task = None
        
        logger.info("Resource manager stopped")
    
    async def allocate_resources(self, 
                               task_id: str,
                               agent_id: str,
                               cpu_cores: Optional[int] = None,
                               memory_gb: Optional[float] = None,
                               gpu_memory_gb: Optional[float] = None,
                               priority: int = 5,
                               timeout: Optional[float] = None) -> bool:
        """Allocate resources for a task."""
        try:
            # Check if resources are available
            if not await self._check_resource_availability(cpu_cores, memory_gb, gpu_memory_gb):
                logger.warning(f"Insufficient resources for task {task_id}")
                return False
            
            # Create allocation
            allocation = ResourceAllocation(
                task_id=task_id,
                agent_id=agent_id,
                cpu_cores=cpu_cores,
                memory_gb=memory_gb,
                gpu_memory_gb=gpu_memory_gb,
                priority=priority,
                expires_at=time.time() + timeout if timeout else None
            )
            
            # Store allocation
            self.allocations[task_id] = allocation
            
            # Apply resource limits if possible
            await self._apply_resource_limits(allocation)
            
            logger.info(f"Resources allocated for task {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error allocating resources for task {task_id}: {e}")
            return False
    
    async def release_resources(self, task_id: str):
        """Release resources for a task."""
        if task_id in self.allocations:
            allocation = self.allocations[task_id]
            
            # Remove resource limits
            await self._remove_resource_limits(allocation)
            
            # Remove allocation
            del self.allocations[task_id]
            
            logger.info(f"Resources released for task {task_id}")
    
    async def get_resource_status(self) -> Dict[str, Any]:
        """Get current resource status."""
        metrics = self.monitor.get_current_metrics()
        if not metrics:
            return {"status": "unavailable"}
        
        # Determine status levels
        cpu_status = self._get_status_level(metrics.cpu_percent, 
                                          self.limits.warning_cpu_percent,
                                          self.limits.max_cpu_percent)
        
        memory_status = self._get_status_level(metrics.memory_percent,
                                             self.limits.warning_memory_percent,
                                             self.limits.max_memory_percent)
        
        disk_status = self._get_status_level(100 - (metrics.disk_free_gb / 100 * 100),
                                           100 - self.limits.warning_disk_free_gb,
                                           100 - self.limits.min_disk_free_gb)
        
        gpu_status = self._get_status_level(metrics.gpu_memory_percent,
                                          self.limits.warning_gpu_memory_percent,
                                          self.limits.max_gpu_memory_percent)
        
        # Overall status
        statuses = [cpu_status, memory_status, disk_status, gpu_status]
        if ResourceStatus.CRITICAL in statuses:
            overall_status = ResourceStatus.CRITICAL
        elif ResourceStatus.WARNING in statuses:
            overall_status = ResourceStatus.WARNING
        else:
            overall_status = ResourceStatus.OPTIMAL
        
        return {
            "overall_status": overall_status.value,
            "cpu_status": cpu_status.value,
            "memory_status": memory_status.value,
            "disk_status": disk_status.value,
            "gpu_status": gpu_status.value,
            "metrics": metrics.to_dict(),
            "active_allocations": len(self.allocations),
            "limits": {
                "max_cpu_percent": self.limits.max_cpu_percent,
                "max_memory_percent": self.limits.max_memory_percent,
                "min_disk_free_gb": self.limits.min_disk_free_gb,
                "max_gpu_memory_percent": self.limits.max_gpu_memory_percent
            }
        }
    
    async def optimize_resources(self):
        """Optimize resource allocation."""
        try:
            # Clean up expired allocations
            await self._cleanup_expired_allocations()
            
            # Rebalance allocations based on priority
            await self._rebalance_allocations()
            
            # Suggest optimizations
            suggestions = await self._generate_optimization_suggestions()
            
            logger.info(f"Resource optimization completed. Suggestions: {len(suggestions)}")
            return suggestions
            
        except Exception as e:
            logger.error(f"Error during resource optimization: {e}")
            return []
    
    async def get_resource_recommendations(self, 
                                         task_type: str,
                                         complexity: str = "medium") -> Dict[str, Any]:
        """Get resource recommendations for a task type."""
        # Base recommendations by task type
        base_recommendations = {
            "code_generation": {
                "low": {"cpu_cores": 2, "memory_gb": 4, "gpu_memory_gb": 2},
                "medium": {"cpu_cores": 4, "memory_gb": 8, "gpu_memory_gb": 4},
                "high": {"cpu_cores": 8, "memory_gb": 16, "gpu_memory_gb": 8}
            },
            "debugging": {
                "low": {"cpu_cores": 1, "memory_gb": 2, "gpu_memory_gb": 1},
                "medium": {"cpu_cores": 2, "memory_gb": 4, "gpu_memory_gb": 2},
                "high": {"cpu_cores": 4, "memory_gb": 8, "gpu_memory_gb": 4}
            },
            "testing": {
                "low": {"cpu_cores": 2, "memory_gb": 4, "gpu_memory_gb": 1},
                "medium": {"cpu_cores": 4, "memory_gb": 8, "gpu_memory_gb": 2},
                "high": {"cpu_cores": 6, "memory_gb": 12, "gpu_memory_gb": 4}
            },
            "deployment": {
                "low": {"cpu_cores": 1, "memory_gb": 2, "gpu_memory_gb": 0},
                "medium": {"cpu_cores": 2, "memory_gb": 4, "gpu_memory_gb": 0},
                "high": {"cpu_cores": 4, "memory_gb": 8, "gpu_memory_gb": 0}
            }
        }
        
        # Get base recommendation
        base_rec = base_recommendations.get(task_type, {}).get(complexity, {
            "cpu_cores": 2, "memory_gb": 4, "gpu_memory_gb": 2
        })
        
        # Adjust based on current resource availability
        current_metrics = self.monitor.get_current_metrics()
        if current_metrics:
            # Reduce recommendations if resources are constrained
            if current_metrics.memory_percent > 70:
                base_rec["memory_gb"] = max(1, base_rec["memory_gb"] * 0.7)
            
            if current_metrics.cpu_percent > 70:
                base_rec["cpu_cores"] = max(1, int(base_rec["cpu_cores"] * 0.7))
            
            if current_metrics.gpu_memory_percent > 70:
                base_rec["gpu_memory_gb"] = max(0, base_rec["gpu_memory_gb"] * 0.7)
        
        return {
            "task_type": task_type,
            "complexity": complexity,
            "recommended": base_rec,
            "available": await self._get_available_resources(),
            "can_allocate": await self._check_resource_availability(
                base_rec["cpu_cores"],
                base_rec["memory_gb"],
                base_rec["gpu_memory_gb"]
            )
        }
    
    async def _check_resource_availability(self,
                                         cpu_cores: Optional[int],
                                         memory_gb: Optional[float],
                                         gpu_memory_gb: Optional[float]) -> bool:
        """Check if requested resources are available."""
        current_metrics = self.monitor.get_current_metrics()
        if not current_metrics:
            return False
        
        # Check CPU availability
        if cpu_cores:
            total_cores = psutil.cpu_count()
            if cpu_cores > total_cores:
                return False
        
        # Check memory availability
        if memory_gb:
            if memory_gb > current_metrics.memory_available_gb:
                return False
        
        # Check GPU memory availability
        if gpu_memory_gb:
            if gpu_memory_gb > current_metrics.gpu_memory_free_gb:
                return False
        
        return True
    
    async def _get_available_resources(self) -> Dict[str, Any]:
        """Get currently available resources."""
        current_metrics = self.monitor.get_current_metrics()
        if not current_metrics:
            return {}
        
        return {
            "cpu_cores_total": psutil.cpu_count(),
            "cpu_percent_used": current_metrics.cpu_percent,
            "memory_total_gb": psutil.virtual_memory().total / (1024**3),
            "memory_available_gb": current_metrics.memory_available_gb,
            "disk_free_gb": current_metrics.disk_free_gb,
            "gpu_memory_free_gb": current_metrics.gpu_memory_free_gb
        }
    
    def _get_status_level(self, current: float, warning: float, critical: float) -> ResourceStatus:
        """Get status level based on thresholds."""
        if current >= critical:
            return ResourceStatus.CRITICAL
        elif current >= warning:
            return ResourceStatus.WARNING
        else:
            return ResourceStatus.OPTIMAL
    
    async def _apply_resource_limits(self, allocation: ResourceAllocation):
        """Apply resource limits for an allocation."""
        # This would integrate with cgroups or similar on Linux
        # For now, just log the allocation
        logger.info(f"Applied resource limits for task {allocation.task_id}")
    
    async def _remove_resource_limits(self, allocation: ResourceAllocation):
        """Remove resource limits for an allocation."""
        logger.info(f"Removed resource limits for task {allocation.task_id}")
    
    async def _cleanup_expired_allocations(self):
        """Clean up expired resource allocations."""
        current_time = time.time()
        expired_tasks = []
        
        for task_id, allocation in self.allocations.items():
            if allocation.expires_at and current_time > allocation.expires_at:
                expired_tasks.append(task_id)
        
        for task_id in expired_tasks:
            await self.release_resources(task_id)
            logger.info(f"Cleaned up expired allocation for task {task_id}")
    
    async def _rebalance_allocations(self):
        """Rebalance resource allocations based on priority."""
        # Sort allocations by priority
        sorted_allocations = sorted(
            self.allocations.values(),
            key=lambda a: a.priority,
            reverse=True
        )
        
        # Implement rebalancing logic here
        logger.debug(f"Rebalanced {len(sorted_allocations)} allocations")
    
    async def _generate_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """Generate resource optimization suggestions."""
        suggestions = []
        current_metrics = self.monitor.get_current_metrics()
        
        if not current_metrics:
            return suggestions
        
        # High CPU usage suggestion
        if current_metrics.cpu_percent > self.limits.warning_cpu_percent:
            suggestions.append({
                "type": "cpu_optimization",
                "severity": "warning" if current_metrics.cpu_percent < self.limits.max_cpu_percent else "critical",
                "message": f"CPU usage is {current_metrics.cpu_percent:.1f}%. Consider reducing concurrent tasks.",
                "action": "reduce_concurrent_tasks"
            })
        
        # High memory usage suggestion
        if current_metrics.memory_percent > self.limits.warning_memory_percent:
            suggestions.append({
                "type": "memory_optimization",
                "severity": "warning" if current_metrics.memory_percent < self.limits.max_memory_percent else "critical",
                "message": f"Memory usage is {current_metrics.memory_percent:.1f}%. Consider using model quantization.",
                "action": "enable_quantization"
            })
        
        # Low disk space suggestion
        if current_metrics.disk_free_gb < self.limits.warning_disk_free_gb:
            suggestions.append({
                "type": "disk_optimization",
                "severity": "warning" if current_metrics.disk_free_gb > self.limits.min_disk_free_gb else "critical",
                "message": f"Only {current_metrics.disk_free_gb:.1f}GB disk space remaining. Consider cleanup.",
                "action": "cleanup_cache"
            })
        
        return suggestions
    
    async def _optimization_loop(self):
        """Main optimization loop."""
        while True:
            try:
                await self.optimize_resources()
                await asyncio.sleep(self.optimization_interval)
            except Exception as e:
                logger.error(f"Error in optimization loop: {e}")
                await asyncio.sleep(self.optimization_interval)
    
    def _on_metrics_collected(self, metrics: ResourceMetrics):
        """Handle metrics collection."""
        # Check for threshold violations
        if metrics.cpu_percent > self.limits.max_cpu_percent:
            if self.monitor.on_threshold_exceeded:
                self.monitor.on_threshold_exceeded(ResourceType.CPU, metrics.cpu_percent)
        
        if metrics.memory_percent > self.limits.max_memory_percent:
            if self.monitor.on_threshold_exceeded:
                self.monitor.on_threshold_exceeded(ResourceType.MEMORY, metrics.memory_percent)
    
    def _on_threshold_exceeded(self, resource_type: ResourceType, value: float):
        """Handle threshold exceeded events."""
        logger.warning(f"Resource threshold exceeded: {resource_type.value} = {value}")
    
    async def get_allocation_info(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get allocation information for a task."""
        allocation = self.allocations.get(task_id)
        if not allocation:
            return None
        
        return {
            "task_id": allocation.task_id,
            "agent_id": allocation.agent_id,
            "cpu_cores": allocation.cpu_cores,
            "memory_gb": allocation.memory_gb,
            "gpu_memory_gb": allocation.gpu_memory_gb,
            "priority": allocation.priority,
            "allocated_at": allocation.allocated_at,
            "expires_at": allocation.expires_at
        }
    
    async def list_allocations(self) -> List[Dict[str, Any]]:
        """List all current allocations."""
        return [
            await self.get_allocation_info(task_id)
            for task_id in self.allocations.keys()
        ]