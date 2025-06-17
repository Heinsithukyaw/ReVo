"""
🔧 Base Engine Interface

Common interface and functionality for all engines in the Three-Engine Architecture.
Provides standardized methods, logging, and performance monitoring.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class EngineMetrics:
    """Performance metrics for an engine"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time_ms: float = 0.0
    last_request_time: Optional[datetime] = None
    uptime_seconds: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0

@dataclass
class EngineStatus:
    """Current status of an engine"""
    engine_name: str
    status: str  # "initializing", "active", "busy", "error", "shutdown"
    metrics: EngineMetrics
    capabilities: List[str]
    configuration: Dict[str, Any]
    last_health_check: datetime

class BaseEngine(ABC):
    """
    🔧 Base Engine Interface
    
    Abstract base class that all engines must implement.
    Provides common functionality for logging, metrics, and lifecycle management.
    """
    
    def __init__(self, engine_name: str, config: Dict[str, Any]):
        self.engine_name = engine_name
        self.config = config
        self.logger = logging.getLogger(f"revoagent.engines.{engine_name}")
        
        # Performance tracking
        self.metrics = EngineMetrics()
        self.start_time = time.time()
        self.status = "initializing"
        
        # Request tracking
        self.active_requests: Dict[str, Any] = {}
        self.request_history: List[Dict[str, Any]] = []
        
        self.logger.info(f"🔧 {engine_name} engine created")
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the engine.
        
        Returns:
            True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_engine_status(self) -> Dict[str, Any]:
        """
        Get current engine status and metrics.
        
        Returns:
            Dictionary containing engine status information
        """
        pass
    
    async def health_check(self) -> bool:
        """
        Perform health check on the engine.
        
        Returns:
            True if engine is healthy, False otherwise
        """
        try:
            status = await self.get_engine_status()
            return status.get('status') in ['active', 'busy']
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    def _start_request_tracking(self, request_id: str, request_data: Any) -> float:
        """Start tracking a request"""
        start_time = time.time()
        self.active_requests[request_id] = {
            'start_time': start_time,
            'data': request_data
        }
        return start_time
    
    def _end_request_tracking(self, request_id: str, success: bool, result: Any = None) -> float:
        """End tracking a request and update metrics"""
        if request_id not in self.active_requests:
            return 0.0
        
        request_info = self.active_requests.pop(request_id)
        duration = time.time() - request_info['start_time']
        duration_ms = duration * 1000
        
        # Update metrics
        self.metrics.total_requests += 1
        if success:
            self.metrics.successful_requests += 1
        else:
            self.metrics.failed_requests += 1
        
        # Update average response time
        if self.metrics.total_requests == 1:
            self.metrics.avg_response_time_ms = duration_ms
        else:
            self.metrics.avg_response_time_ms = (
                self.metrics.avg_response_time_ms * 0.9 + duration_ms * 0.1
            )
        
        self.metrics.last_request_time = datetime.now()
        
        # Add to history (keep last 100)
        self.request_history.append({
            'request_id': request_id,
            'duration_ms': duration_ms,
            'success': success,
            'timestamp': datetime.now(),
            'result_size': len(str(result)) if result else 0
        })
        
        if len(self.request_history) > 100:
            self.request_history = self.request_history[-100:]
        
        return duration_ms
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        uptime = time.time() - self.start_time
        success_rate = (
            self.metrics.successful_requests / self.metrics.total_requests * 100
            if self.metrics.total_requests > 0 else 0
        )
        
        return {
            'engine_name': self.engine_name,
            'uptime_seconds': uptime,
            'total_requests': self.metrics.total_requests,
            'success_rate_percent': round(success_rate, 2),
            'avg_response_time_ms': round(self.metrics.avg_response_time_ms, 2),
            'active_requests': len(self.active_requests),
            'status': self.status
        }
    
    async def shutdown(self) -> bool:
        """
        Shutdown the engine gracefully.
        
        Returns:
            True if shutdown successful, False otherwise
        """
        try:
            self.status = "shutdown"
            self.logger.info(f"🔧 {self.engine_name} engine shutdown")
            return True
        except Exception as e:
            self.logger.error(f"Shutdown failed: {e}")
            return False