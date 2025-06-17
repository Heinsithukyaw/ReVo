#!/usr/bin/env python3
"""
API Gateway for External Integration Resilience
Centralized gateway for all external API calls with rate limiting, retry logic, and monitoring
"""

import asyncio
import aiohttp
import json
import logging
import time
import hashlib
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import hmac
from collections import defaultdict, deque
import weakref

# Graceful Redis import
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)

class IntegrationType(Enum):
    """External integration types"""
    GITHUB = "github"
    SLACK = "slack"
    JIRA = "jira"
    OPENHANDS = "openhands"
    VLLM = "vllm"
    WEBHOOK = "webhook"
    CUSTOM = "custom"

class RequestMethod(Enum):
    """HTTP request methods"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"

class RetryStrategy(Enum):
    """Retry strategies for failed requests"""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_DELAY = "fixed_delay"
    IMMEDIATE = "immediate"
    NO_RETRY = "no_retry"

class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered

@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_limit: int = 10
    window_size: int = 60  # seconds
    
@dataclass
class RetryConfig:
    """Retry configuration"""
    max_attempts: int = 3
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    base_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    backoff_multiplier: float = 2.0
    jitter: bool = True

@dataclass
class TimeoutConfig:
    """Timeout configuration"""
    connect_timeout: float = 10.0  # seconds
    read_timeout: float = 30.0     # seconds
    total_timeout: float = 60.0    # seconds

@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5
    recovery_timeout: int = 60  # seconds
    success_threshold: int = 3  # for half-open state
    
@dataclass
class IntegrationConfig:
    """Configuration for external integration"""
    integration_type: IntegrationType
    base_url: str
    api_key: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    retry: RetryConfig = field(default_factory=RetryConfig)
    timeout: TimeoutConfig = field(default_factory=TimeoutConfig)
    circuit_breaker: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    cache_ttl: int = 3600  # seconds
    enable_logging: bool = True
    enable_metrics: bool = True

@dataclass
class APIRequest:
    """API request definition"""
    method: RequestMethod
    endpoint: str
    headers: Optional[Dict[str, str]] = None
    params: Optional[Dict[str, Any]] = None
    data: Optional[Union[Dict, str, bytes]] = None
    json_data: Optional[Dict[str, Any]] = None
    timeout_override: Optional[TimeoutConfig] = None
    retry_override: Optional[RetryConfig] = None
    cache_key: Optional[str] = None
    cache_ttl: Optional[int] = None

@dataclass
class APIResponse:
    """API response wrapper"""
    status_code: int
    headers: Dict[str, str]
    data: Any
    response_time: float
    cached: bool = False
    retry_count: int = 0
    integration_type: Optional[IntegrationType] = None
    endpoint: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.tokens = config.burst_limit
        self.last_update = time.time()
        self.request_times = deque()
        
    async def acquire(self) -> bool:
        """Acquire a token for rate limiting"""
        now = time.time()
        
        # Refill tokens based on time passed
        time_passed = now - self.last_update
        tokens_to_add = time_passed * (self.config.requests_per_minute / 60.0)
        self.tokens = min(self.config.burst_limit, self.tokens + tokens_to_add)
        self.last_update = now
        
        # Clean old request times
        cutoff_time = now - self.config.window_size
        while self.request_times and self.request_times[0] < cutoff_time:
            self.request_times.popleft()
            
        # Check rate limits
        if len(self.request_times) >= self.config.requests_per_minute:
            return False
            
        if self.tokens < 1:
            return False
            
        # Consume token and record request
        self.tokens -= 1
        self.request_times.append(now)
        return True
        
    def get_wait_time(self) -> float:
        """Get time to wait before next request"""
        if self.tokens >= 1:
            return 0.0
            
        # Calculate time until next token is available
        tokens_needed = 1 - self.tokens
        time_per_token = 60.0 / self.config.requests_per_minute
        return tokens_needed * time_per_token

class CircuitBreaker:
    """Circuit breaker for external service calls"""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
                self.success_count = 0
            else:
                raise Exception("Circuit breaker is OPEN - service unavailable")
                
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
            
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset"""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.config.recovery_timeout
        
    def _on_success(self):
        """Handle successful request"""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
        else:
            self.failure_count = 0
            
    def _on_failure(self):
        """Handle failed request"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitBreakerState.OPEN

class APIGateway:
    """Centralized API Gateway for external integrations"""
    
    def __init__(self, redis_url: Optional[str] = None):
        self.integrations: Dict[IntegrationType, IntegrationConfig] = {}
        self.rate_limiters: Dict[IntegrationType, RateLimiter] = {}
        self.circuit_breakers: Dict[IntegrationType, CircuitBreaker] = {}
        self.session: Optional[aiohttp.ClientSession] = None
        self.redis_client: Optional[redis.Redis] = None
        self.cache: Dict[str, Any] = {}  # In-memory fallback cache
        self.metrics: Dict[str, Any] = defaultdict(int)
        self.request_log: List[Dict[str, Any]] = []
        
        # Initialize Redis if available
        if REDIS_AVAILABLE and redis_url:
            try:
                self.redis_client = redis.from_url(redis_url)
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}")
                
    async def start(self):
        """Start the API Gateway"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=300)
            self.session = aiohttp.ClientSession(timeout=timeout)
            
        logger.info("API Gateway started successfully")
        
    async def stop(self):
        """Stop the API Gateway"""
        if self.session:
            await self.session.close()
            self.session = None
            
        if self.redis_client:
            await self.redis_client.close()
            
        logger.info("API Gateway stopped")
        
    def register_integration(self, config: IntegrationConfig):
        """Register an external integration"""
        self.integrations[config.integration_type] = config
        self.rate_limiters[config.integration_type] = RateLimiter(config.rate_limit)
        self.circuit_breakers[config.integration_type] = CircuitBreaker(config.circuit_breaker)
        
        logger.info(f"Registered integration: {config.integration_type.value}")
        
    async def make_request(
        self, 
        integration_type: IntegrationType, 
        request: APIRequest
    ) -> APIResponse:
        """Make an API request through the gateway"""
        if integration_type not in self.integrations:
            raise ValueError(f"Integration {integration_type.value} not registered")
            
        config = self.integrations[integration_type]
        start_time = time.time()
        
        # Check cache first
        cache_key = self._generate_cache_key(integration_type, request)
        cached_response = await self._get_cached_response(cache_key)
        if cached_response:
            return cached_response
            
        # Rate limiting
        rate_limiter = self.rate_limiters[integration_type]
        if not await rate_limiter.acquire():
            wait_time = rate_limiter.get_wait_time()
            raise Exception(f"Rate limit exceeded. Wait {wait_time:.2f} seconds")
            
        # Circuit breaker protection
        circuit_breaker = self.circuit_breakers[integration_type]
        
        try:
            response = await circuit_breaker.call(
                self._execute_request, 
                integration_type, 
                request, 
                config
            )
            
            # Cache successful responses
            if response.status_code < 400:
                await self._cache_response(cache_key, response, request.cache_ttl or config.cache_ttl)
                
            # Update metrics
            self._update_metrics(integration_type, response, time.time() - start_time)
            
            return response
            
        except Exception as e:
            self._update_metrics(integration_type, None, time.time() - start_time, error=str(e))
            raise e
            
    async def _execute_request(
        self, 
        integration_type: IntegrationType, 
        request: APIRequest, 
        config: IntegrationConfig
    ) -> APIResponse:
        """Execute the actual HTTP request with retry logic"""
        retry_config = request.retry_override or config.retry
        timeout_config = request.timeout_override or config.timeout
        
        last_exception = None
        
        for attempt in range(retry_config.max_attempts):
            try:
                # Build request parameters
                url = f"{config.base_url.rstrip('/')}/{request.endpoint.lstrip('/')}"
                headers = {**config.headers}
                if request.headers:
                    headers.update(request.headers)
                    
                # Set timeout
                timeout = aiohttp.ClientTimeout(
                    connect=timeout_config.connect_timeout,
                    sock_read=timeout_config.read_timeout,
                    total=timeout_config.total_timeout
                )
                
                # Make request
                start_time = time.time()
                async with self.session.request(
                    method=request.method.value,
                    url=url,
                    headers=headers,
                    params=request.params,
                    data=request.data,
                    json=request.json_data,
                    timeout=timeout
                ) as response:
                    response_data = await response.text()
                    try:
                        response_data = json.loads(response_data)
                    except json.JSONDecodeError:
                        pass  # Keep as text if not JSON
                        
                    api_response = APIResponse(
                        status_code=response.status,
                        headers=dict(response.headers),
                        data=response_data,
                        response_time=time.time() - start_time,
                        retry_count=attempt,
                        integration_type=integration_type,
                        endpoint=request.endpoint
                    )
                    
                    # Log request if enabled
                    if config.enable_logging:
                        self._log_request(integration_type, request, api_response)
                        
                    # Check if response indicates success
                    if response.status < 500:  # Don't retry client errors
                        return api_response
                        
                    # Server error - will retry
                    last_exception = Exception(f"Server error: {response.status}")
                    
            except Exception as e:
                last_exception = e
                
            # Calculate retry delay
            if attempt < retry_config.max_attempts - 1:
                delay = self._calculate_retry_delay(retry_config, attempt)
                await asyncio.sleep(delay)
                
        # All retries exhausted
        raise last_exception or Exception("Request failed after all retries")
        
    def _calculate_retry_delay(self, config: RetryConfig, attempt: int) -> float:
        """Calculate delay for retry attempt"""
        if config.strategy == RetryStrategy.NO_RETRY:
            return 0
        elif config.strategy == RetryStrategy.IMMEDIATE:
            return 0
        elif config.strategy == RetryStrategy.FIXED_DELAY:
            delay = config.base_delay
        elif config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = config.base_delay * (attempt + 1)
        elif config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = config.base_delay * (config.backoff_multiplier ** attempt)
        else:
            delay = config.base_delay
            
        # Apply jitter if enabled
        if config.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)  # 50-100% of calculated delay
            
        return min(delay, config.max_delay)
        
    def _generate_cache_key(self, integration_type: IntegrationType, request: APIRequest) -> str:
        """Generate cache key for request"""
        if request.cache_key:
            return f"{integration_type.value}:{request.cache_key}"
            
        # Generate key from request parameters
        key_parts = [
            integration_type.value,
            request.method.value,
            request.endpoint,
            str(request.params) if request.params else "",
            str(request.json_data) if request.json_data else ""
        ]
        
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
        
    async def _get_cached_response(self, cache_key: str) -> Optional[APIResponse]:
        """Get cached response"""
        try:
            if self.redis_client:
                cached_data = await self.redis_client.get(cache_key)
                if cached_data:
                    response_dict = json.loads(cached_data)
                    response = APIResponse(**response_dict)
                    response.cached = True
                    return response
        except Exception as e:
            logger.warning(f"Redis cache get failed: {e}")
            
        # Fallback to in-memory cache
        if cache_key in self.cache:
            cached_item = self.cache[cache_key]
            if cached_item['expires'] > time.time():
                response = APIResponse(**cached_item['data'])
                response.cached = True
                return response
            else:
                del self.cache[cache_key]
                
        return None
        
    async def _cache_response(self, cache_key: str, response: APIResponse, ttl: int):
        """Cache response"""
        response_dict = {
            'status_code': response.status_code,
            'headers': response.headers,
            'data': response.data,
            'response_time': response.response_time,
            'retry_count': response.retry_count,
            'integration_type': response.integration_type.value if response.integration_type else None,
            'endpoint': response.endpoint,
            'timestamp': response.timestamp.isoformat()
        }
        
        try:
            if self.redis_client:
                await self.redis_client.setex(
                    cache_key, 
                    ttl, 
                    json.dumps(response_dict, default=str)
                )
            else:
                # Fallback to in-memory cache
                self.cache[cache_key] = {
                    'data': response_dict,
                    'expires': time.time() + ttl
                }
        except Exception as e:
            logger.warning(f"Cache set failed: {e}")
            
    def _update_metrics(
        self, 
        integration_type: IntegrationType, 
        response: Optional[APIResponse], 
        duration: float,
        error: Optional[str] = None
    ):
        """Update request metrics"""
        prefix = f"{integration_type.value}"
        
        self.metrics[f"{prefix}_requests_total"] += 1
        self.metrics[f"{prefix}_request_duration_sum"] += duration
        
        if error:
            self.metrics[f"{prefix}_errors_total"] += 1
        elif response:
            if response.status_code >= 400:
                self.metrics[f"{prefix}_errors_total"] += 1
            else:
                self.metrics[f"{prefix}_success_total"] += 1
                
    def _log_request(
        self, 
        integration_type: IntegrationType, 
        request: APIRequest, 
        response: APIResponse
    ):
        """Log API request"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'integration_type': integration_type.value,
            'method': request.method.value,
            'endpoint': request.endpoint,
            'status_code': response.status_code,
            'response_time': response.response_time,
            'retry_count': response.retry_count,
            'cached': response.cached
        }
        
        self.request_log.append(log_entry)
        
        # Keep only last 1000 entries
        if len(self.request_log) > 1000:
            self.request_log = self.request_log[-1000:]
            
    async def get_integration_health(self, integration_type: IntegrationType) -> Dict[str, Any]:
        """Get health status for integration"""
        if integration_type not in self.integrations:
            return {"status": "not_registered"}
            
        circuit_breaker = self.circuit_breakers[integration_type]
        rate_limiter = self.rate_limiters[integration_type]
        
        prefix = f"{integration_type.value}"
        total_requests = self.metrics.get(f"{prefix}_requests_total", 0)
        total_errors = self.metrics.get(f"{prefix}_errors_total", 0)
        total_success = self.metrics.get(f"{prefix}_success_total", 0)
        total_duration = self.metrics.get(f"{prefix}_request_duration_sum", 0)
        
        error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
        avg_response_time = (total_duration / total_requests) if total_requests > 0 else 0
        
        return {
            "status": "healthy" if circuit_breaker.state == CircuitBreakerState.CLOSED else "unhealthy",
            "circuit_breaker_state": circuit_breaker.state.value,
            "failure_count": circuit_breaker.failure_count,
            "rate_limit_tokens": rate_limiter.tokens,
            "total_requests": total_requests,
            "total_errors": total_errors,
            "total_success": total_success,
            "error_rate_percent": round(error_rate, 2),
            "avg_response_time_ms": round(avg_response_time * 1000, 2)
        }
        
    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health"""
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "integrations": {}
        }
        
        unhealthy_count = 0
        for integration_type in self.integrations:
            integration_health = await self.get_integration_health(integration_type)
            health_data["integrations"][integration_type.value] = integration_health
            
            if integration_health["status"] != "healthy":
                unhealthy_count += 1
                
        if unhealthy_count > 0:
            health_data["status"] = "degraded" if unhealthy_count < len(self.integrations) else "unhealthy"
            
        return health_data

# Global API Gateway instance
_gateway_instance: Optional[APIGateway] = None

async def get_api_gateway(redis_url: Optional[str] = None) -> APIGateway:
    """Get or create the global API Gateway instance"""
    global _gateway_instance
    
    if _gateway_instance is None:
        _gateway_instance = APIGateway(redis_url)
        await _gateway_instance.start()
        
    return _gateway_instance

async def shutdown_api_gateway():
    """Shutdown the global API Gateway instance"""
    global _gateway_instance
    
    if _gateway_instance:
        await _gateway_instance.stop()
        _gateway_instance = None