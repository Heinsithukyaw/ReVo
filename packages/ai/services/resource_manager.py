"""
Resource Manager Service

Focused service for managing system resources and optimizing performance.
"""

import asyncio
import logging
import psutil
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None
import gc
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import threading

logger = logging.getLogger(__name__)


@dataclass
class ResourceLimits:
    """Resource limits configuration."""
    max_memory_percent: float = 85.0
    max_gpu_memory_percent: float = 90.0
    max_cpu_percent: float = 90.0
    min_free_memory_gb: float = 2.0
    model_memory_limit_gb: float = 16.0


@dataclass
class ResourceUsage:
    """Current resource usage snapshot."""
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_available_gb: float
    gpu_memory_used_gb: float
    gpu_memory_total_gb: float
    gpu_utilization: float
    timestamp: datetime


class ResourceManager:
    """
    Focused service for system resource management and optimization.
    
    Responsibilities:
    - Monitor system resource usage
    - Enforce resource limits
    - Optimize memory usage
    - Manage GPU resources
    - Implement resource-based scaling
    - Provide resource cleanup
    """
    
    def __init__(self, limits: Optional[ResourceLimits] = None):
        self.limits = limits or ResourceLimits()
        self.resource_history: List[ResourceUsage] = []
        self.cleanup_callbacks: List[callable] = []
        self.lock = threading.Lock()
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
        
    async def start_monitoring(self, interval_seconds: int = 30):
        """
        Start continuous resource monitoring.
        
        Args:
            interval_seconds: Monitoring interval in seconds
        """
        if self._monitoring:
            logger.warning("Resource monitoring already started")
            return
        
        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop(interval_seconds))
        logger.info(f"Started resource monitoring with {interval_seconds}s interval")
    
    async def stop_monitoring(self):
        """Stop resource monitoring."""
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped resource monitoring")
    
    async def _monitor_loop(self, interval_seconds: int):
        """Main monitoring loop."""
        while self._monitoring:
            try:
                usage = self.get_current_usage()
                self._store_usage_history(usage)
                
                # Check for resource violations
                await self._check_resource_limits(usage)
                
                await asyncio.sleep(interval_seconds)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in resource monitoring: {e}")
                await asyncio.sleep(interval_seconds)
    
    def get_current_usage(self) -> ResourceUsage:
        """
        Get current system resource usage.
        
        Returns:
            ResourceUsage: Current resource usage snapshot
        """
        # CPU and memory
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # GPU metrics
        gpu_memory_used = 0.0
        gpu_memory_total = 0.0
        gpu_utilization = 0.0
        
        if TORCH_AVAILABLE and torch.cuda.is_available():
            gpu_memory_used = torch.cuda.memory_allocated() / (1024**3)
            gpu_memory_total = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            gpu_utilization = self._get_gpu_utilization()
        
        return ResourceUsage(
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used_gb=memory.used / (1024**3),
            memory_available_gb=memory.available / (1024**3),
            gpu_memory_used_gb=gpu_memory_used,
            gpu_memory_total_gb=gpu_memory_total,
            gpu_utilization=gpu_utilization,
            timestamp=datetime.now()
        )
    
    async def check_resource_availability(self, required_memory_gb: float = 0.0, 
                                        required_gpu_memory_gb: float = 0.0) -> Tuple[bool, str]:
        """
        Check if sufficient resources are available for an operation.
        
        Args:
            required_memory_gb: Required system memory in GB
            required_gpu_memory_gb: Required GPU memory in GB
            
        Returns:
            Tuple[bool, str]: (availability, reason if not available)
        """
        usage = self.get_current_usage()
        
        # Check system memory
        if required_memory_gb > 0:
            available_memory = usage.memory_available_gb
            if available_memory < required_memory_gb:
                return False, f"Insufficient memory: need {required_memory_gb}GB, have {available_memory:.1f}GB"
            
            # Check if operation would exceed memory limit
            projected_usage = ((usage.memory_used_gb + required_memory_gb) / 
                             (usage.memory_used_gb + usage.memory_available_gb)) * 100
            if projected_usage > self.limits.max_memory_percent:
                return False, f"Operation would exceed memory limit: {projected_usage:.1f}% > {self.limits.max_memory_percent}%"
        
        # Check GPU memory
        if required_gpu_memory_gb > 0 and torch.cuda.is_available():
            available_gpu_memory = usage.gpu_memory_total_gb - usage.gpu_memory_used_gb
            if available_gpu_memory < required_gpu_memory_gb:
                return False, f"Insufficient GPU memory: need {required_gpu_memory_gb}GB, have {available_gpu_memory:.1f}GB"
            
            # Check if operation would exceed GPU memory limit
            projected_gpu_usage = ((usage.gpu_memory_used_gb + required_gpu_memory_gb) / 
                                 usage.gpu_memory_total_gb) * 100
            if projected_gpu_usage > self.limits.max_gpu_memory_percent:
                return False, f"Operation would exceed GPU memory limit: {projected_gpu_usage:.1f}% > {self.limits.max_gpu_memory_percent}%"
        
        return True, "Resources available"
    
    async def optimize_memory_usage(self) -> Dict[str, Any]:
        """
        Optimize system memory usage by cleaning up resources.
        
        Returns:
            Dict containing optimization results
        """
        logger.info("Starting memory optimization")
        
        usage_before = self.get_current_usage()
        
        optimization_results = {
            "before": {
                "memory_percent": usage_before.memory_percent,
                "memory_used_gb": usage_before.memory_used_gb,
                "gpu_memory_used_gb": usage_before.gpu_memory_used_gb
            },
            "actions_taken": [],
            "memory_freed_gb": 0.0,
            "gpu_memory_freed_gb": 0.0
        }
        
        # Run cleanup callbacks
        for callback in self.cleanup_callbacks:
            try:
                await callback()
                optimization_results["actions_taken"].append(f"Executed cleanup callback: {callback.__name__}")
            except Exception as e:
                logger.error(f"Cleanup callback failed: {e}")
        
        # Force garbage collection
        gc.collect()
        optimization_results["actions_taken"].append("Forced garbage collection")
        
        # Clear GPU cache if available
        if TORCH_AVAILABLE and torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
            optimization_results["actions_taken"].append("Cleared GPU cache")
        
        # Get usage after optimization
        usage_after = self.get_current_usage()
        
        optimization_results["after"] = {
            "memory_percent": usage_after.memory_percent,
            "memory_used_gb": usage_after.memory_used_gb,
            "gpu_memory_used_gb": usage_after.gpu_memory_used_gb
        }
        
        optimization_results["memory_freed_gb"] = usage_before.memory_used_gb - usage_after.memory_used_gb
        optimization_results["gpu_memory_freed_gb"] = usage_before.gpu_memory_used_gb - usage_after.gpu_memory_used_gb
        
        logger.info(f"Memory optimization completed: freed {optimization_results['memory_freed_gb']:.2f}GB system memory, "
                   f"{optimization_results['gpu_memory_freed_gb']:.2f}GB GPU memory")
        
        return optimization_results
    
    async def _check_resource_limits(self, usage: ResourceUsage):
        """Check if resource usage exceeds limits and take action."""
        actions_taken = []
        
        # Check memory limit
        if usage.memory_percent > self.limits.max_memory_percent:
            logger.warning(f"Memory usage {usage.memory_percent:.1f}% exceeds limit {self.limits.max_memory_percent}%")
            await self.optimize_memory_usage()
            actions_taken.append("memory_optimization")
        
        # Check available memory
        if usage.memory_available_gb < self.limits.min_free_memory_gb:
            logger.warning(f"Available memory {usage.memory_available_gb:.1f}GB below minimum {self.limits.min_free_memory_gb}GB")
            await self.optimize_memory_usage()
            actions_taken.append("low_memory_cleanup")
        
        # Check GPU memory limit
        if TORCH_AVAILABLE and torch.cuda.is_available() and usage.gpu_memory_total_gb > 0:
            gpu_usage_percent = (usage.gpu_memory_used_gb / usage.gpu_memory_total_gb) * 100
            if gpu_usage_percent > self.limits.max_gpu_memory_percent:
                logger.warning(f"GPU memory usage {gpu_usage_percent:.1f}% exceeds limit {self.limits.max_gpu_memory_percent}%")
                torch.cuda.empty_cache()
                actions_taken.append("gpu_cache_clear")
        
        # Check CPU usage
        if usage.cpu_percent > self.limits.max_cpu_percent:
            logger.warning(f"CPU usage {usage.cpu_percent:.1f}% exceeds limit {self.limits.max_cpu_percent}%")
            # Could implement CPU throttling or load balancing here
            actions_taken.append("cpu_warning")
        
        if actions_taken:
            logger.info(f"Resource limit actions taken: {actions_taken}")
    
    def _store_usage_history(self, usage: ResourceUsage):
        """Store usage in history with cleanup of old entries."""
        with self.lock:
            self.resource_history.append(usage)
            
            # Keep only last 24 hours of data (assuming 30s intervals = 2880 entries)
            max_entries = 2880
            if len(self.resource_history) > max_entries:
                self.resource_history = self.resource_history[-max_entries:]
    
    def get_resource_trends(self, hours: int = 1) -> Dict[str, Any]:
        """
        Get resource usage trends over specified time period.
        
        Args:
            hours: Number of hours to analyze
            
        Returns:
            Dict containing trend analysis
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self.lock:
            recent_usage = [u for u in self.resource_history if u.timestamp > cutoff_time]
        
        if not recent_usage:
            return {"error": "No recent usage data available"}
        
        # Calculate trends
        memory_values = [u.memory_percent for u in recent_usage]
        cpu_values = [u.cpu_percent for u in recent_usage]
        gpu_memory_values = [u.gpu_memory_used_gb for u in recent_usage if u.gpu_memory_total_gb > 0]
        
        return {
            "time_period_hours": hours,
            "data_points": len(recent_usage),
            "memory": {
                "avg_percent": sum(memory_values) / len(memory_values),
                "max_percent": max(memory_values),
                "min_percent": min(memory_values),
                "trend": "increasing" if memory_values[-1] > memory_values[0] else "decreasing"
            },
            "cpu": {
                "avg_percent": sum(cpu_values) / len(cpu_values),
                "max_percent": max(cpu_values),
                "min_percent": min(cpu_values),
                "trend": "increasing" if cpu_values[-1] > cpu_values[0] else "decreasing"
            },
            "gpu_memory": {
                "avg_gb": sum(gpu_memory_values) / len(gpu_memory_values) if gpu_memory_values else 0,
                "max_gb": max(gpu_memory_values) if gpu_memory_values else 0,
                "min_gb": min(gpu_memory_values) if gpu_memory_values else 0,
                "trend": "increasing" if gpu_memory_values and gpu_memory_values[-1] > gpu_memory_values[0] else "decreasing"
            }
        }
    
    def register_cleanup_callback(self, callback: callable):
        """
        Register a cleanup callback to be called during optimization.
        
        Args:
            callback: Async function to call for cleanup
        """
        self.cleanup_callbacks.append(callback)
        logger.info(f"Registered cleanup callback: {callback.__name__}")
    
    def _get_gpu_utilization(self) -> float:
        """Get GPU utilization percentage."""
        try:
            import nvidia_ml_py as nvml
            nvml.nvmlInit()
            handle = nvml.nvmlDeviceGetHandleByIndex(0)
            util = nvml.nvmlDeviceGetUtilizationRates(handle)
            return util.gpu
        except Exception:
            return 0.0
    
    def get_resource_summary(self) -> Dict[str, Any]:
        """Get comprehensive resource summary."""
        current_usage = self.get_current_usage()
        trends = self.get_resource_trends(hours=1)
        
        return {
            "current_usage": {
                "cpu_percent": current_usage.cpu_percent,
                "memory_percent": current_usage.memory_percent,
                "memory_used_gb": current_usage.memory_used_gb,
                "memory_available_gb": current_usage.memory_available_gb,
                "gpu_memory_used_gb": current_usage.gpu_memory_used_gb,
                "gpu_memory_total_gb": current_usage.gpu_memory_total_gb,
                "gpu_utilization": current_usage.gpu_utilization
            },
            "limits": {
                "max_memory_percent": self.limits.max_memory_percent,
                "max_gpu_memory_percent": self.limits.max_gpu_memory_percent,
                "max_cpu_percent": self.limits.max_cpu_percent,
                "min_free_memory_gb": self.limits.min_free_memory_gb
            },
            "trends": trends,
            "monitoring_active": self._monitoring,
            "cleanup_callbacks_registered": len(self.cleanup_callbacks),
            "timestamp": datetime.now().isoformat()
        }