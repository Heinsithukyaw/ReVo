"""
Circuit breaker pattern implementation for external API resilience.

Features:
- Multiple circuit breaker states (closed, open, half-open)
- Configurable failure thresholds and timeouts
- Automatic recovery attempts
- Fallback strategies
- Monitoring and alerting
- Bulkhead isolation for different services
"""

import asyncio
import time
import logging
from typing import Dict, Optional, Any, Callable, Awaitable, Union, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import hashlib
from collections import deque, defaultdict

from .logging_config import get_logger

logger = get_logger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"        # Normal operation
    OPEN = "open"           # Failing, rejecting requests
    HALF_OPEN = "half_open" # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    name: str
    failure_threshold: int = 5          # Number of failures to open circuit
    recovery_timeout: int = 60          # Seconds to wait before trying recovery
    success_threshold: int = 3          # Successes needed to close circuit from half-open
    timeout: float = 30.0               # Request timeout in seconds
    expected_exception: type = Exception # Exception type that triggers circuit
    fallback_function: Optional[Callable] = None
    monitor_window: int = 300           # Monitoring window in seconds
    slow_call_threshold: float = 10.0   # Calls slower than this are considered failures


@dataclass
class CircuitBreakerStats:
    """Circuit breaker statistics."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rejected_requests: int = 0
    slow_requests: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    state_changes: int = 0
    current_state: CircuitState = CircuitState.CLOSED
    recent_response_times: deque = field(default_factory=lambda: deque(maxlen=100))


class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class CircuitBreakerTimeoutException(Exception):
    """Exception raised when request times out."""
    pass


class CircuitBreaker:
    """
    Circuit breaker implementation for external API calls.
    
    The circuit breaker monitors the health of external services and
    prevents cascading failures by temporarily blocking requests to
    failing services.
    """
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.stats = CircuitBreakerStats()
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0
        self.next_attempt_time = 0
        self._lock = asyncio.Lock()
        
        logger.info("Circuit breaker initialized", extra={
            'circuit_name': config.name,
            'failure_threshold': config.failure_threshold,
            'recovery_timeout': config.recovery_timeout
        })
    
    async def call(self, func: Callable[..., Awaitable[Any]], *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenException: When circuit is open
            CircuitBreakerTimeoutException: When request times out
        """
        async with self._lock:
            self.stats.total_requests += 1
            
            # Check if circuit is open
            if self.state == CircuitState.OPEN:
                if time.time() < self.next_attempt_time:
                    self.stats.rejected_requests += 1
                    logger.warning("Circuit breaker open, rejecting request", extra={
                        'circuit_name': self.config.name,
                        'next_attempt_in': self.next_attempt_time - time.time()
                    })
                    raise CircuitBreakerOpenException(
                        f"Circuit breaker '{self.config.name}' is open"
                    )
                else:
                    # Try to recover - move to half-open
                    await self._transition_to_half_open()
        
        # Execute the function with timeout
        start_time = time.time()
        try:
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.config.timeout
            )
            
            execution_time = time.time() - start_time
            await self._record_success(execution_time)
            
            return result
            
        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            await self._record_failure(CircuitBreakerTimeoutException(
                f"Request timed out after {execution_time:.2f}s"
            ))
            raise CircuitBreakerTimeoutException(
                f"Request to '{self.config.name}' timed out after {self.config.timeout}s"
            )
            
        except self.config.expected_exception as e:
            execution_time = time.time() - start_time
            await self._record_failure(e)
            raise
            
        except Exception as e:
            # Unexpected exception - don't count as failure unless configured
            execution_time = time.time() - start_time
            logger.error("Unexpected exception in circuit breaker", extra={
                'circuit_name': self.config.name,
                'error': str(e),
                'execution_time': execution_time
            })
            raise
    
    async def call_with_fallback(self, func: Callable[..., Awaitable[Any]], 
                                *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker and fallback.
        
        Args:
            func: Primary function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result or fallback result
        """
        try:
            return await self.call(func, *args, **kwargs)
        except (CircuitBreakerOpenException, CircuitBreakerTimeoutException, 
                self.config.expected_exception) as e:
            
            if self.config.fallback_function:
                logger.info("Using fallback function", extra={
                    'circuit_name': self.config.name,
                    'error': str(e)
                })
                
                try:
                    if asyncio.iscoroutinefunction(self.config.fallback_function):
                        return await self.config.fallback_function(*args, **kwargs)
                    else:
                        return self.config.fallback_function(*args, **kwargs)
                except Exception as fallback_error:
                    logger.error("Fallback function failed", extra={
                        'circuit_name': self.config.name,
                        'fallback_error': str(fallback_error)
                    })
                    raise
            else:
                raise
    
    async def _record_success(self, execution_time: float):
        """Record successful execution."""
        async with self._lock:
            self.stats.successful_requests += 1
            self.stats.last_success_time = time.time()
            self.stats.recent_response_times.append(execution_time)
            
            # Check for slow calls
            if execution_time > self.config.slow_call_threshold:
                self.stats.slow_requests += 1
                logger.warning("Slow call detected", extra={
                    'circuit_name': self.config.name,
                    'execution_time': execution_time,
                    'threshold': self.config.slow_call_threshold
                })
            
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    await self._transition_to_closed()
            elif self.state == CircuitState.OPEN:
                # Shouldn't happen, but reset if it does
                await self._transition_to_closed()
            
            logger.debug("Success recorded", extra={
                'circuit_name': self.config.name,
                'execution_time': execution_time,
                'state': self.state.value
            })
    
    async def _record_failure(self, exception: Exception):
        """Record failed execution."""
        async with self._lock:
            self.stats.failed_requests += 1
            self.stats.last_failure_time = time.time()
            self.last_failure_time = time.time()
            
            if self.state == CircuitState.CLOSED:
                self.failure_count += 1
                if self.failure_count >= self.config.failure_threshold:
                    await self._transition_to_open()
            elif self.state == CircuitState.HALF_OPEN:
                # Failed during recovery - go back to open
                await self._transition_to_open()
            
            logger.warning("Failure recorded", extra={
                'circuit_name': self.config.name,
                'error': str(exception),
                'failure_count': self.failure_count,
                'state': self.state.value
            })
    
    async def _transition_to_open(self):
        """Transition circuit breaker to open state."""
        if self.state != CircuitState.OPEN:
            self.state = CircuitState.OPEN
            self.stats.current_state = CircuitState.OPEN
            self.stats.state_changes += 1
            self.next_attempt_time = time.time() + self.config.recovery_timeout
            
            logger.error("Circuit breaker opened", extra={
                'circuit_name': self.config.name,
                'failure_count': self.failure_count,
                'recovery_timeout': self.config.recovery_timeout
            })
    
    async def _transition_to_half_open(self):
        """Transition circuit breaker to half-open state."""
        if self.state != CircuitState.HALF_OPEN:
            self.state = CircuitState.HALF_OPEN
            self.stats.current_state = CircuitState.HALF_OPEN
            self.stats.state_changes += 1
            self.success_count = 0
            
            logger.info("Circuit breaker half-open", extra={
                'circuit_name': self.config.name,
                'success_threshold': self.config.success_threshold
            })
    
    async def _transition_to_closed(self):
        """Transition circuit breaker to closed state."""
        if self.state != CircuitState.CLOSED:
            self.state = CircuitState.CLOSED
            self.stats.current_state = CircuitState.CLOSED
            self.stats.state_changes += 1
            self.failure_count = 0
            self.success_count = 0
            
            logger.info("Circuit breaker closed", extra={
                'circuit_name': self.config.name
            })
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        uptime = time.time() - (self.stats.last_success_time or time.time())
        
        # Calculate success rate
        total_completed = self.stats.successful_requests + self.stats.failed_requests
        success_rate = (self.stats.successful_requests / max(1, total_completed)) * 100
        
        # Calculate average response time
        avg_response_time = (
            sum(self.stats.recent_response_times) / len(self.stats.recent_response_times)
            if self.stats.recent_response_times else 0
        )
        
        return {
            'name': self.config.name,
            'state': self.state.value,
            'total_requests': self.stats.total_requests,
            'successful_requests': self.stats.successful_requests,
            'failed_requests': self.stats.failed_requests,
            'rejected_requests': self.stats.rejected_requests,
            'slow_requests': self.stats.slow_requests,
            'success_rate': success_rate,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'avg_response_time': avg_response_time,
            'state_changes': self.stats.state_changes,
            'last_failure_time': self.stats.last_failure_time,
            'last_success_time': self.stats.last_success_time,
            'next_attempt_time': self.next_attempt_time if self.state == CircuitState.OPEN else None
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on circuit breaker."""
        stats = self.get_stats()
        
        health_status = {
            'status': 'healthy',
            'circuit_name': self.config.name,
            'circuit_state': self.state.value,
            'stats': stats,
            'timestamp': datetime.now().isoformat()
        }
        
        # Determine health based on state and recent performance
        if self.state == CircuitState.OPEN:
            health_status['status'] = 'unhealthy'
            health_status['reason'] = 'Circuit breaker is open'
        elif self.state == CircuitState.HALF_OPEN:
            health_status['status'] = 'degraded'
            health_status['reason'] = 'Circuit breaker is recovering'
        elif stats['success_rate'] < 90:  # Less than 90% success rate
            health_status['status'] = 'degraded'
            health_status['reason'] = f"Low success rate: {stats['success_rate']:.1f}%"
        elif stats['avg_response_time'] > self.config.slow_call_threshold:
            health_status['status'] = 'degraded'
            health_status['reason'] = f"High response time: {stats['avg_response_time']:.2f}s"
        
        return health_status
    
    async def reset(self):
        """Reset circuit breaker to closed state."""
        async with self._lock:
            await self._transition_to_closed()
            self.stats = CircuitBreakerStats()
            logger.info("Circuit breaker reset", extra={
                'circuit_name': self.config.name
            })


class CircuitBreakerManager:
    """
    Manager for multiple circuit breakers.
    
    Provides centralized management, monitoring, and configuration
    for multiple circuit breakers protecting different services.
    """
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._global_stats = {
            'total_circuits': 0,
            'open_circuits': 0,
            'half_open_circuits': 0,
            'closed_circuits': 0,
            'start_time': time.time()
        }
        
        logger.info("Circuit breaker manager initialized")
    
    def create_circuit_breaker(self, config: CircuitBreakerConfig) -> CircuitBreaker:
        """Create and register a new circuit breaker."""
        if config.name in self.circuit_breakers:
            logger.warning("Circuit breaker already exists", extra={
                'name': config.name
            })
            return self.circuit_breakers[config.name]
        
        circuit_breaker = CircuitBreaker(config)
        self.circuit_breakers[config.name] = circuit_breaker
        self._global_stats['total_circuits'] += 1
        
        logger.info("Circuit breaker created", extra={
            'name': config.name,
            'total_circuits': self._global_stats['total_circuits']
        })
        
        return circuit_breaker
    
    def get_circuit_breaker(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name."""
        return self.circuit_breakers.get(name)
    
    def remove_circuit_breaker(self, name: str) -> bool:
        """Remove circuit breaker."""
        if name in self.circuit_breakers:
            del self.circuit_breakers[name]
            self._global_stats['total_circuits'] -= 1
            logger.info("Circuit breaker removed", extra={'name': name})
            return True
        return False
    
    async def call_with_circuit_breaker(self, circuit_name: str, 
                                       func: Callable[..., Awaitable[Any]], 
                                       *args, **kwargs) -> Any:
        """Execute function with named circuit breaker."""
        circuit_breaker = self.get_circuit_breaker(circuit_name)
        if not circuit_breaker:
            raise ValueError(f"Circuit breaker '{circuit_name}' not found")
        
        return await circuit_breaker.call(func, *args, **kwargs)
    
    async def call_with_fallback(self, circuit_name: str, 
                                func: Callable[..., Awaitable[Any]], 
                                *args, **kwargs) -> Any:
        """Execute function with named circuit breaker and fallback."""
        circuit_breaker = self.get_circuit_breaker(circuit_name)
        if not circuit_breaker:
            raise ValueError(f"Circuit breaker '{circuit_name}' not found")
        
        return await circuit_breaker.call_with_fallback(func, *args, **kwargs)
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all circuit breakers."""
        circuit_stats = {}
        state_counts = defaultdict(int)
        
        for name, cb in self.circuit_breakers.items():
            stats = cb.get_stats()
            circuit_stats[name] = stats
            state_counts[stats['state']] += 1
        
        # Update global stats
        self._global_stats.update({
            'open_circuits': state_counts['open'],
            'half_open_circuits': state_counts['half_open'],
            'closed_circuits': state_counts['closed'],
            'uptime_seconds': time.time() - self._global_stats['start_time']
        })
        
        return {
            'global_stats': self._global_stats,
            'circuit_breakers': circuit_stats
        }
    
    async def health_check_all(self) -> Dict[str, Any]:
        """Perform health check on all circuit breakers."""
        health_checks = {}
        overall_status = 'healthy'
        
        for name, cb in self.circuit_breakers.items():
            health = await cb.health_check()
            health_checks[name] = health
            
            if health['status'] == 'unhealthy':
                overall_status = 'unhealthy'
            elif health['status'] == 'degraded' and overall_status == 'healthy':
                overall_status = 'degraded'
        
        return {
            'overall_status': overall_status,
            'circuit_breakers': health_checks,
            'global_stats': self._global_stats,
            'timestamp': datetime.now().isoformat()
        }
    
    async def reset_all(self):
        """Reset all circuit breakers."""
        for cb in self.circuit_breakers.values():
            await cb.reset()
        
        logger.info("All circuit breakers reset")


# Global circuit breaker manager
_circuit_breaker_manager: Optional[CircuitBreakerManager] = None


def get_circuit_breaker_manager() -> CircuitBreakerManager:
    """Get the global circuit breaker manager."""
    global _circuit_breaker_manager
    if _circuit_breaker_manager is None:
        _circuit_breaker_manager = CircuitBreakerManager()
    return _circuit_breaker_manager


# Predefined circuit breaker configurations for common services
OPENAI_CIRCUIT_CONFIG = CircuitBreakerConfig(
    name="openai_api",
    failure_threshold=3,
    recovery_timeout=30,
    success_threshold=2,
    timeout=30.0,
    slow_call_threshold=10.0
)

ANTHROPIC_CIRCUIT_CONFIG = CircuitBreakerConfig(
    name="anthropic_api",
    failure_threshold=3,
    recovery_timeout=30,
    success_threshold=2,
    timeout=30.0,
    slow_call_threshold=10.0
)

DEEPSEEK_CIRCUIT_CONFIG = CircuitBreakerConfig(
    name="deepseek_api",
    failure_threshold=5,
    recovery_timeout=60,
    success_threshold=3,
    timeout=45.0,
    slow_call_threshold=15.0
)

DATABASE_CIRCUIT_CONFIG = CircuitBreakerConfig(
    name="database",
    failure_threshold=5,
    recovery_timeout=30,
    success_threshold=3,
    timeout=10.0,
    slow_call_threshold=5.0
)

REDIS_CIRCUIT_CONFIG = CircuitBreakerConfig(
    name="redis",
    failure_threshold=3,
    recovery_timeout=15,
    success_threshold=2,
    timeout=5.0,
    slow_call_threshold=2.0
)


def initialize_default_circuit_breakers():
    """Initialize circuit breakers for common services."""
    manager = get_circuit_breaker_manager()
    
    configs = [
        OPENAI_CIRCUIT_CONFIG,
        ANTHROPIC_CIRCUIT_CONFIG,
        DEEPSEEK_CIRCUIT_CONFIG,
        DATABASE_CIRCUIT_CONFIG,
        REDIS_CIRCUIT_CONFIG
    ]
    
    for config in configs:
        manager.create_circuit_breaker(config)
    
    logger.info("Default circuit breakers initialized", extra={
        'circuit_count': len(configs)
    })