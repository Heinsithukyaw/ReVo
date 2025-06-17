"""
Metrics Collector Service

Focused service for collecting and tracking AI model performance metrics.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import psutil
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None

logger = logging.getLogger(__name__)


@dataclass
class ModelMetrics:
    """Metrics for a specific model."""
    model_id: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_response_time: float = 0.0
    total_tokens_generated: int = 0
    memory_usage_gb: float = 0.0
    gpu_memory_gb: float = 0.0
    last_used: Optional[datetime] = None
    error_rate: float = 0.0
    avg_response_time: float = 0.0
    tokens_per_second: float = 0.0
    recent_response_times: deque = field(default_factory=lambda: deque(maxlen=100))


@dataclass
class SystemMetrics:
    """System-wide metrics."""
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_used_gb: float = 0.0
    memory_total_gb: float = 0.0
    gpu_memory_used_gb: float = 0.0
    gpu_memory_total_gb: float = 0.0
    gpu_utilization: float = 0.0
    active_models: int = 0
    total_requests_per_minute: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


class MetricsCollector:
    """
    Focused service for collecting and tracking performance metrics.
    
    Responsibilities:
    - Track model performance metrics
    - Monitor system resource usage
    - Calculate performance statistics
    - Provide metrics for monitoring and alerting
    - Store historical metrics data
    """
    
    def __init__(self, retention_hours: int = 24):
        self.model_metrics: Dict[str, ModelMetrics] = {}
        self.system_metrics_history: deque = deque(maxlen=retention_hours * 60)  # 1 minute intervals
        self.request_timestamps: deque = deque(maxlen=10000)  # Last 10k requests
        self.retention_hours = retention_hours
        
    def record_request_start(self, model_id: str) -> str:
        """
        Record the start of a request.
        
        Args:
            model_id: ID of the model handling the request
            
        Returns:
            str: Request ID for tracking
        """
        request_id = f"{model_id}_{int(time.time() * 1000)}"
        
        if model_id not in self.model_metrics:
            self.model_metrics[model_id] = ModelMetrics(model_id=model_id)
        
        self.model_metrics[model_id].total_requests += 1
        self.request_timestamps.append(datetime.now())
        
        return request_id
    
    def record_request_completion(self, model_id: str, response_time: float, 
                                tokens_generated: int, success: bool = True, 
                                error: Optional[str] = None):
        """
        Record the completion of a request.
        
        Args:
            model_id: ID of the model that handled the request
            response_time: Time taken to generate response in seconds
            tokens_generated: Number of tokens generated
            success: Whether the request was successful
            error: Error message if request failed
        """
        if model_id not in self.model_metrics:
            self.model_metrics[model_id] = ModelMetrics(model_id=model_id)
        
        metrics = self.model_metrics[model_id]
        
        if success:
            metrics.successful_requests += 1
            metrics.total_response_time += response_time
            metrics.total_tokens_generated += tokens_generated
            metrics.recent_response_times.append(response_time)
        else:
            metrics.failed_requests += 1
            logger.warning(f"Request failed for model {model_id}: {error}")
        
        metrics.last_used = datetime.now()
        
        # Update calculated metrics
        self._update_calculated_metrics(model_id)
    
    def update_model_resource_usage(self, model_id: str, memory_gb: float, gpu_memory_gb: float):
        """
        Update resource usage metrics for a model.
        
        Args:
            model_id: ID of the model
            memory_gb: Memory usage in GB
            gpu_memory_gb: GPU memory usage in GB
        """
        if model_id not in self.model_metrics:
            self.model_metrics[model_id] = ModelMetrics(model_id=model_id)
        
        self.model_metrics[model_id].memory_usage_gb = memory_gb
        self.model_metrics[model_id].gpu_memory_gb = gpu_memory_gb
    
    def collect_system_metrics(self) -> SystemMetrics:
        """
        Collect current system metrics.
        
        Returns:
            SystemMetrics: Current system resource usage
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
        
        # Calculate requests per minute
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)
        recent_requests = sum(1 for ts in self.request_timestamps if ts > one_minute_ago)
        
        metrics = SystemMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used_gb=memory.used / (1024**3),
            memory_total_gb=memory.total / (1024**3),
            gpu_memory_used_gb=gpu_memory_used,
            gpu_memory_total_gb=gpu_memory_total,
            gpu_utilization=gpu_utilization,
            active_models=len(self.model_metrics),
            total_requests_per_minute=recent_requests,
            timestamp=now
        )
        
        # Store in history
        self.system_metrics_history.append(metrics)
        
        return metrics
    
    def get_model_metrics(self, model_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get metrics for a specific model or all models.
        
        Args:
            model_id: Optional specific model ID
            
        Returns:
            Dict containing model metrics
        """
        if model_id:
            if model_id in self.model_metrics:
                return self._format_model_metrics(self.model_metrics[model_id])
            else:
                return {}
        
        return {
            mid: self._format_model_metrics(metrics) 
            for mid, metrics in self.model_metrics.items()
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get a summary of overall performance metrics.
        
        Returns:
            Dict containing performance summary
        """
        total_requests = sum(m.total_requests for m in self.model_metrics.values())
        total_successful = sum(m.successful_requests for m in self.model_metrics.values())
        total_failed = sum(m.failed_requests for m in self.model_metrics.values())
        
        overall_error_rate = (total_failed / total_requests * 100) if total_requests > 0 else 0
        
        # Get current system metrics
        current_system = self.collect_system_metrics()
        
        # Calculate average response time across all models
        total_response_time = sum(m.total_response_time for m in self.model_metrics.values())
        avg_response_time = (total_response_time / total_successful) if total_successful > 0 else 0
        
        return {
            "total_requests": total_requests,
            "successful_requests": total_successful,
            "failed_requests": total_failed,
            "overall_error_rate": overall_error_rate,
            "average_response_time": avg_response_time,
            "active_models": len(self.model_metrics),
            "system_metrics": {
                "cpu_percent": current_system.cpu_percent,
                "memory_percent": current_system.memory_percent,
                "gpu_utilization": current_system.gpu_utilization,
                "requests_per_minute": current_system.total_requests_per_minute
            },
            "top_performing_models": self._get_top_performing_models(),
            "timestamp": datetime.now().isoformat()
        }
    
    def get_alerts(self) -> List[Dict[str, Any]]:
        """
        Get current performance alerts.
        
        Returns:
            List of alert dictionaries
        """
        alerts = []
        current_system = self.collect_system_metrics()
        
        # System resource alerts
        if current_system.memory_percent > 85:
            alerts.append({
                "type": "high_memory_usage",
                "severity": "warning",
                "message": f"Memory usage at {current_system.memory_percent:.1f}%",
                "timestamp": datetime.now().isoformat()
            })
        
        if current_system.cpu_percent > 90:
            alerts.append({
                "type": "high_cpu_usage", 
                "severity": "warning",
                "message": f"CPU usage at {current_system.cpu_percent:.1f}%",
                "timestamp": datetime.now().isoformat()
            })
        
        # Model performance alerts
        for model_id, metrics in self.model_metrics.items():
            if metrics.error_rate > 10:  # More than 10% error rate
                alerts.append({
                    "type": "high_error_rate",
                    "severity": "critical",
                    "message": f"Model {model_id} has {metrics.error_rate:.1f}% error rate",
                    "model_id": model_id,
                    "timestamp": datetime.now().isoformat()
                })
            
            if metrics.avg_response_time > 30:  # More than 30 seconds average
                alerts.append({
                    "type": "slow_response_time",
                    "severity": "warning", 
                    "message": f"Model {model_id} has {metrics.avg_response_time:.1f}s average response time",
                    "model_id": model_id,
                    "timestamp": datetime.now().isoformat()
                })
        
        return alerts
    
    def _update_calculated_metrics(self, model_id: str):
        """Update calculated metrics for a model."""
        metrics = self.model_metrics[model_id]
        
        # Error rate
        if metrics.total_requests > 0:
            metrics.error_rate = (metrics.failed_requests / metrics.total_requests) * 100
        
        # Average response time
        if metrics.successful_requests > 0:
            metrics.avg_response_time = metrics.total_response_time / metrics.successful_requests
        
        # Tokens per second
        if metrics.total_response_time > 0:
            metrics.tokens_per_second = metrics.total_tokens_generated / metrics.total_response_time
    
    def _format_model_metrics(self, metrics: ModelMetrics) -> Dict[str, Any]:
        """Format model metrics for output."""
        return {
            "model_id": metrics.model_id,
            "total_requests": metrics.total_requests,
            "successful_requests": metrics.successful_requests,
            "failed_requests": metrics.failed_requests,
            "error_rate": metrics.error_rate,
            "avg_response_time": metrics.avg_response_time,
            "tokens_per_second": metrics.tokens_per_second,
            "memory_usage_gb": metrics.memory_usage_gb,
            "gpu_memory_gb": metrics.gpu_memory_gb,
            "last_used": metrics.last_used.isoformat() if metrics.last_used else None,
            "total_tokens_generated": metrics.total_tokens_generated
        }
    
    def _get_top_performing_models(self, limit: int = 3) -> List[Dict[str, Any]]:
        """Get top performing models by tokens per second."""
        sorted_models = sorted(
            self.model_metrics.values(),
            key=lambda m: m.tokens_per_second,
            reverse=True
        )
        
        return [
            {
                "model_id": m.model_id,
                "tokens_per_second": m.tokens_per_second,
                "error_rate": m.error_rate,
                "avg_response_time": m.avg_response_time
            }
            for m in sorted_models[:limit]
        ]
    
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
    
    def cleanup_old_metrics(self):
        """Clean up old metrics data beyond retention period."""
        cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)
        
        # Clean up request timestamps
        while self.request_timestamps and self.request_timestamps[0] < cutoff_time:
            self.request_timestamps.popleft()
        
        # System metrics are automatically cleaned up by deque maxlen