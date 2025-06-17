"""
Enterprise Circuit Breaker Service
Implements resilience patterns for external dependencies
"""

import asyncio
import time
import logging
from typing import Dict, Any, Callable, Optional, Union, List
from enum import Enum
from dataclasses import dataclass, field
from functools import wraps
import json

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, requests fail fast
    HALF_OPEN = "half_open"  # Testing if service is back

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5          # Number of failures to open circuit
    recovery_timeout: int = 30          # Seconds before trying half-open
    success_threshold: int = 3          # Successes needed to close from half-open
    timeout: float = 10.0               # Request timeout in seconds
    expected_exception: type = Exception # Exception type that triggers circuit

@dataclass
class CircuitBreakerStats:
    """Circuit breaker statistics"""
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float = 0.0
    last_success_time: float = 0.0
    total_requests: int = 0
    total_failures: int = 0
    total_successes: int = 0
    state_changes: int = 0

class CircuitBreakerError(Exception):
    """Circuit breaker specific errors"""
    pass

class CircuitBreaker:
    """
    Circuit breaker implementation with exponential backoff
    """
    
    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.stats = CircuitBreakerStats()
        self._lock = asyncio.Lock()
        
        logger.info(f"🔧 Circuit breaker '{name}' initialized with config: {self.config}")
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection
        """
        async with self._lock:
            self.stats.total_requests += 1
            
            # Check if circuit should be opened
            if self._should_open_circuit():
                self._open_circuit()
            
            # Check if circuit should transition to half-open
            if self._should_attempt_reset():
                self._half_open_circuit()
            
            # Handle different circuit states
            if self.stats.state == CircuitState.OPEN:
                raise CircuitBreakerError(f"Circuit breaker '{self.name}' is OPEN")
            
            try:
                # Execute the function with timeout
                result = await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=self.config.timeout
                )
                
                # Record success
                await self._record_success()
                return result
                
            except asyncio.TimeoutError:
                await self._record_failure()
                raise CircuitBreakerError(f"Request timeout in circuit '{self.name}'")
            
            except self.config.expected_exception as e:
                await self._record_failure()
                raise CircuitBreakerError(f"Circuit breaker '{self.name}' caught expected exception: {str(e)}")
            
            except Exception as e:
                await self._record_failure()
                raise CircuitBreakerError(f"Circuit breaker '{self.name}' caught unexpected exception: {str(e)}")
    
    def _should_open_circuit(self) -> bool:
        """Check if circuit should be opened"""
        return (
            self.stats.state == CircuitState.CLOSED and
            self.stats.failure_count >= self.config.failure_threshold
        )
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt reset to half-open"""
        return (
            self.stats.state == CircuitState.OPEN and
            time.time() - self.stats.last_failure_time >= self.config.recovery_timeout
        )
    
    def _open_circuit(self):
        """Open the circuit"""
        if self.stats.state != CircuitState.OPEN:
            self.stats.state = CircuitState.OPEN
            self.stats.state_changes += 1
            logger.warning(f"🚨 Circuit breaker '{self.name}' OPENED after {self.stats.failure_count} failures")
    
    def _half_open_circuit(self):
        """Set circuit to half-open state"""
        if self.stats.state != CircuitState.HALF_OPEN:
            self.stats.state = CircuitState.HALF_OPEN
            self.stats.success_count = 0  # Reset success count for half-open test
            self.stats.state_changes += 1
            logger.info(f"🔄 Circuit breaker '{self.name}' set to HALF-OPEN for testing")
    
    def _close_circuit(self):
        """Close the circuit"""
        if self.stats.state != CircuitState.CLOSED:
            self.stats.state = CircuitState.CLOSED
            self.stats.failure_count = 0  # Reset failure count
            self.stats.state_changes += 1
            logger.info(f"✅ Circuit breaker '{self.name}' CLOSED - service recovered")
    
    async def _record_success(self):
        """Record a successful request"""
        self.stats.success_count += 1
        self.stats.total_successes += 1
        self.stats.last_success_time = time.time()
        
        # Reset failure count on success
        self.stats.failure_count = 0
        
        # Close circuit if enough successes in half-open state
        if (
            self.stats.state == CircuitState.HALF_OPEN and
            self.stats.success_count >= self.config.success_threshold
        ):
            self._close_circuit()
    
    async def _record_failure(self):
        """Record a failed request"""
        self.stats.failure_count += 1
        self.stats.total_failures += 1
        self.stats.last_failure_time = time.time()
        
        # Reset success count on failure
        self.stats.success_count = 0
        
        logger.warning(f"⚠️ Circuit breaker '{self.name}' recorded failure {self.stats.failure_count}/{self.config.failure_threshold}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        return {
            "name": self.name,
            "state": self.stats.state.value,
            "failure_count": self.stats.failure_count,
            "success_count": self.stats.success_count,
            "total_requests": self.stats.total_requests,
            "total_failures": self.stats.total_failures,
            "total_successes": self.stats.total_successes,
            "failure_rate": self.stats.total_failures / max(self.stats.total_requests, 1),
            "success_rate": self.stats.total_successes / max(self.stats.total_requests, 1),
            "state_changes": self.stats.state_changes,
            "last_failure_time": self.stats.last_failure_time,
            "last_success_time": self.stats.last_success_time,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "recovery_timeout": self.config.recovery_timeout,
                "success_threshold": self.config.success_threshold,
                "timeout": self.config.timeout
            }
        }
    
    def reset(self):
        """Reset circuit breaker to initial state"""
        self.stats = CircuitBreakerStats()
        logger.info(f"🔄 Circuit breaker '{self.name}' reset to initial state")

class CircuitBreakerRegistry:
    """
    Registry for managing multiple circuit breakers
    """
    
    def __init__(self):
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._lock = asyncio.Lock()
    
    async def get_circuit_breaker(self, name: str, config: CircuitBreakerConfig = None) -> CircuitBreaker:
        """Get or create a circuit breaker"""
        async with self._lock:
            if name not in self._circuit_breakers:
                self._circuit_breakers[name] = CircuitBreaker(name, config)
                logger.info(f"📝 Created new circuit breaker: {name}")
            
            return self._circuit_breakers[name]
    
    async def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all circuit breakers"""
        stats = {}
        async with self._lock:
            for name, circuit_breaker in self._circuit_breakers.items():
                stats[name] = circuit_breaker.get_stats()
        
        return stats
    
    async def reset_all(self):
        """Reset all circuit breakers"""
        async with self._lock:
            for circuit_breaker in self._circuit_breakers.values():
                circuit_breaker.reset()
        
        logger.info("🔄 All circuit breakers reset")
    
    async def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary of all circuit breakers"""
        all_stats = await self.get_all_stats()
        
        total_circuits = len(all_stats)
        open_circuits = sum(1 for stats in all_stats.values() if stats["state"] == "open")
        half_open_circuits = sum(1 for stats in all_stats.values() if stats["state"] == "half_open")
        closed_circuits = sum(1 for stats in all_stats.values() if stats["state"] == "closed")
        
        overall_health = "healthy" if open_circuits == 0 else "degraded" if open_circuits < total_circuits else "critical"
        
        return {
            "overall_health": overall_health,
            "total_circuits": total_circuits,
            "open_circuits": open_circuits,
            "half_open_circuits": half_open_circuits,
            "closed_circuits": closed_circuits,
            "circuit_details": all_stats
        }

# Global circuit breaker registry
circuit_registry = CircuitBreakerRegistry()

def circuit_breaker(name: str, config: CircuitBreakerConfig = None):
    """
    Decorator for applying circuit breaker to async functions
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            circuit = await circuit_registry.get_circuit_breaker(name, config)
            return await circuit.call(func, *args, **kwargs)
        
        return wrapper
    return decorator

class ExternalAPIService:
    """
    Service for making external API calls with circuit breaker protection
    """
    
    def __init__(self):
        self.session = None
        
    async def initialize(self):
        """Initialize HTTP session"""
        import aiohttp
        self.session = aiohttp.ClientSession()
        logger.info("🌐 External API service initialized")
    
    @circuit_breaker("openai_api", CircuitBreakerConfig(failure_threshold=3, recovery_timeout=60))
    async def call_openai_api(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Call OpenAI API with circuit breaker protection"""
        if not self.session:
            await self.initialize()
        
        try:
            async with self.session.post(
                "https://api.openai.com/v1/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {payload.get('api_key', '')}"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"✅ OpenAI API call successful: {response.status}")
                    return result
                else:
                    error_text = await response.text()
                    raise Exception(f"OpenAI API error {response.status}: {error_text}")
        
        except Exception as e:
            logger.error(f"❌ OpenAI API call failed: {str(e)}")
            # Fallback to local model
            return await self._fallback_to_local_model(payload)
    
    @circuit_breaker("anthropic_api", CircuitBreakerConfig(failure_threshold=3, recovery_timeout=60))
    async def call_anthropic_api(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Call Anthropic API with circuit breaker protection"""
        if not self.session:
            await self.initialize()
        
        try:
            async with self.session.post(
                "https://api.anthropic.com/v1/messages",
                json=payload,
                headers={"x-api-key": payload.get('api_key', '')}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"✅ Anthropic API call successful: {response.status}")
                    return result
                else:
                    error_text = await response.text()
                    raise Exception(f"Anthropic API error {response.status}: {error_text}")
        
        except Exception as e:
            logger.error(f"❌ Anthropic API call failed: {str(e)}")
            return await self._fallback_to_local_model(payload)
    
    @circuit_breaker("database", CircuitBreakerConfig(failure_threshold=5, recovery_timeout=30))
    async def query_database(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Query database with circuit breaker protection"""
        try:
            # Simulate database query
            await asyncio.sleep(0.1)  # Simulate query time
            
            # Simulate occasional failures for testing
            import random
            if random.random() < 0.05:  # 5% failure rate
                raise Exception("Database connection timeout")
            
            logger.info(f"✅ Database query successful: {query[:50]}...")
            return [{"result": "success", "query": query}]
        
        except Exception as e:
            logger.error(f"❌ Database query failed: {str(e)}")
            raise
    
    async def _fallback_to_local_model(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback to local AI model when external APIs fail"""
        logger.info("🔄 Falling back to local AI model")
        
        # Simulate local model processing
        await asyncio.sleep(0.5)
        
        return {
            "choices": [{
                "message": {
                    "content": "This response was generated by local fallback model due to external API unavailability."
                }
            }],
            "model": "deepseek-r1-local-fallback",
            "usage": {"total_tokens": 20},
            "fallback": True
        }
    
    async def get_circuit_breaker_status(self) -> Dict[str, Any]:
        """Get status of all circuit breakers"""
        return await circuit_registry.get_health_summary()
    
    async def shutdown(self):
        """Shutdown the service"""
        if self.session:
            await self.session.close()
        logger.info("🛑 External API service shut down")

class RetryWithExponentialBackoff:
    """
    Retry mechanism with exponential backoff
    """
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry and exponential backoff"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            
            except Exception as e:
                last_exception = e
                
                if attempt == self.max_retries:
                    logger.error(f"❌ All {self.max_retries + 1} attempts failed. Last error: {str(e)}")
                    raise e
                
                # Calculate delay with exponential backoff
                delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                
                logger.warning(f"⚠️ Attempt {attempt + 1} failed: {str(e)}. Retrying in {delay:.2f}s...")
                await asyncio.sleep(delay)
        
        # This should never be reached, but just in case
        raise last_exception

# Convenience function for creating retry decorator
def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
    """Decorator for retry with exponential backoff"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            retry_handler = RetryWithExponentialBackoff(max_retries, base_delay, max_delay)
            return await retry_handler.execute(func, *args, **kwargs)
        
        return wrapper
    return decorator

# Example usage combining circuit breaker and retry
class ResilientExternalService:
    """
    Example service combining circuit breaker and retry patterns
    """
    
    @circuit_breaker("external_service", CircuitBreakerConfig(failure_threshold=5, recovery_timeout=60))
    @retry_with_backoff(max_retries=3, base_delay=1.0, max_delay=30.0)
    async def call_external_service(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Call external service with both circuit breaker and retry protection"""
        # Simulate external service call
        import random
        
        if random.random() < 0.3:  # 30% failure rate for testing
            raise Exception("External service temporarily unavailable")
        
        await asyncio.sleep(0.2)  # Simulate processing time
        
        return {
            "status": "success",
            "data": data,
            "timestamp": time.time()
        }

if __name__ == "__main__":
    # Example usage
    async def test_circuit_breaker():
        service = ExternalAPIService()
        await service.initialize()
        
        # Test circuit breaker functionality
        for i in range(10):
            try:
                result = await service.call_openai_api({
                    "model": "gpt-4",
                    "messages": [{"role": "user", "content": f"Test message {i}"}]
                })
                print(f"Request {i}: Success")
            except CircuitBreakerError as e:
                print(f"Request {i}: Circuit breaker error - {e}")
            except Exception as e:
                print(f"Request {i}: Other error - {e}")
            
            await asyncio.sleep(1)
        
        # Print circuit breaker stats
        stats = await service.get_circuit_breaker_status()
        print(f"\nCircuit Breaker Status: {json.dumps(stats, indent=2)}")
        
        await service.shutdown()
    
    asyncio.run(test_circuit_breaker())