"""
Circuit Breaker Pattern Implementation for reVoAgent
Provides resilience for external API calls and service dependencies
"""

import asyncio
import time
from enum import Enum
from typing import Callable, Any, Optional, Dict
from dataclasses import dataclass, field
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, failing fast
    HALF_OPEN = "half_open"  # Testing if service is back

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5  # Number of failures before opening
    timeout: float = 30.0       # Seconds to wait before trying again
    success_threshold: int = 3   # Successes needed to close from half-open
    window_size: int = 60       # Time window for failure counting (seconds)

@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker monitoring"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    state_changes: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    failures_in_window: list = field(default_factory=list)

class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open"""
    pass

class CircuitBreaker:
    """
    Circuit Breaker implementation for resilient service calls
    """
    
    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.stats = CircuitBreakerStats()
        self._lock = asyncio.Lock()
        self._consecutive_successes = 0
        
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function with circuit breaker protection
        """
        async with self._lock:
            # Check if we should fail fast
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    logger.info(f"Circuit breaker {self.name} moved to HALF_OPEN")
                else:
                    self.stats.total_requests += 1
                    raise CircuitBreakerError(f"Circuit breaker {self.name} is OPEN")
        
        # Attempt the call
        self.stats.total_requests += 1
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            await self._on_success()
            return result
            
        except Exception as e:
            await self._on_failure(e)
            raise
    
    async def _on_success(self):
        """Handle successful call"""
        async with self._lock:
            self.stats.successful_requests += 1
            self.stats.last_success_time = time.time()
            self._consecutive_successes += 1
            
            if self.state == CircuitState.HALF_OPEN:
                if self._consecutive_successes >= self.config.success_threshold:
                    self.state = CircuitState.CLOSED
                    self.stats.state_changes += 1
                    self._consecutive_successes = 0
                    logger.info(f"Circuit breaker {self.name} moved to CLOSED")
    
    async def _on_failure(self, exception: Exception):
        """Handle failed call"""
        async with self._lock:
            self.stats.failed_requests += 1
            current_time = time.time()
            self.stats.last_failure_time = current_time
            self._consecutive_successes = 0
            
            # Add failure to window
            self.stats.failures_in_window.append(current_time)
            self._clean_failure_window()
            
            # Check if we should open the circuit
            if (self.state == CircuitState.CLOSED and 
                len(self.stats.failures_in_window) >= self.config.failure_threshold):
                self.state = CircuitState.OPEN
                self.stats.state_changes += 1
                logger.warning(f"Circuit breaker {self.name} moved to OPEN due to {len(self.stats.failures_in_window)} failures")
            
            elif self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                self.stats.state_changes += 1
                logger.warning(f"Circuit breaker {self.name} moved back to OPEN from HALF_OPEN")
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.stats.last_failure_time is None:
            return True
        return time.time() - self.stats.last_failure_time >= self.config.timeout
    
    def _clean_failure_window(self):
        """Remove old failures from the window"""
        current_time = time.time()
        window_start = current_time - self.config.window_size
        self.stats.failures_in_window = [
            failure_time for failure_time in self.stats.failures_in_window
            if failure_time >= window_start
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        return {
            "name": self.name,
            "state": self.state.value,
            "total_requests": self.stats.total_requests,
            "successful_requests": self.stats.successful_requests,
            "failed_requests": self.stats.failed_requests,
            "success_rate": (
                self.stats.successful_requests / self.stats.total_requests 
                if self.stats.total_requests > 0 else 0
            ),
            "failures_in_window": len(self.stats.failures_in_window),
            "state_changes": self.stats.state_changes,
            "last_failure_time": self.stats.last_failure_time,
            "last_success_time": self.stats.last_success_time,
        }
    
    async def reset(self):
        """Manually reset the circuit breaker"""
        async with self._lock:
            self.state = CircuitState.CLOSED
            self.stats.failures_in_window.clear()
            self._consecutive_successes = 0
            self.stats.state_changes += 1
            logger.info(f"Circuit breaker {self.name} manually reset to CLOSED")

# Global circuit breaker registry
_circuit_breakers: Dict[str, CircuitBreaker] = {}

def get_circuit_breaker(name: str, config: CircuitBreakerConfig = None) -> CircuitBreaker:
    """Get or create a circuit breaker"""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name, config)
    return _circuit_breakers[name]

def circuit_breaker(name: str, config: CircuitBreakerConfig = None):
    """Decorator for circuit breaker protection"""
    def decorator(func):
        cb = get_circuit_breaker(name, config)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await cb.call(func, *args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return asyncio.run(cb.call(func, *args, **kwargs))
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

async def get_all_circuit_breaker_stats() -> Dict[str, Dict[str, Any]]:
    """Get statistics for all circuit breakers"""
    return {name: cb.get_stats() for name, cb in _circuit_breakers.items()}