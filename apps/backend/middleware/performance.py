"""
Performance Optimization Middleware for reVoAgent
Includes caching, compression, rate limiting, and performance monitoring
"""

import asyncio
import time
import gzip
import json
from typing import Dict, Any, Optional, Callable
from functools import wraps
import redis
import logging
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import hashlib
from dataclasses import dataclass, field
from collections import defaultdict, deque
import threading

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics tracking"""
    request_count: int = 0
    total_response_time: float = 0.0
    min_response_time: float = float('inf')
    max_response_time: float = 0.0
    error_count: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    recent_response_times: deque = field(default_factory=lambda: deque(maxlen=100))

class PerformanceMonitor:
    """
    Performance monitoring and optimization system
    """
    
    def __init__(self):
        self.metrics = defaultdict(PerformanceMetrics)
        self.redis_client = None
        self._lock = threading.Lock()
        self._initialize_redis()
    
    def _initialize_redis(self):
        """Initialize Redis for caching"""
        try:
            import os
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            logger.info("Redis cache initialized successfully")
        except Exception as e:
            logger.warning(f"Could not initialize Redis cache: {e}")
    
    def record_request(self, endpoint: str, response_time: float, success: bool = True):
        """Record request metrics"""
        with self._lock:
            metrics = self.metrics[endpoint]
            metrics.request_count += 1
            metrics.total_response_time += response_time
            metrics.min_response_time = min(metrics.min_response_time, response_time)
            metrics.max_response_time = max(metrics.max_response_time, response_time)
            metrics.recent_response_times.append(response_time)
            
            if not success:
                metrics.error_count += 1
    
    def record_cache_hit(self, endpoint: str):
        """Record cache hit"""
        with self._lock:
            self.metrics[endpoint].cache_hits += 1
    
    def record_cache_miss(self, endpoint: str):
        """Record cache miss"""
        with self._lock:
            self.metrics[endpoint].cache_misses += 1
    
    def get_metrics(self, endpoint: str = None) -> Dict[str, Any]:
        """Get performance metrics"""
        with self._lock:
            if endpoint:
                metrics = self.metrics[endpoint]
                avg_response_time = (
                    metrics.total_response_time / metrics.request_count 
                    if metrics.request_count > 0 else 0
                )
                
                recent_avg = (
                    sum(metrics.recent_response_times) / len(metrics.recent_response_times)
                    if metrics.recent_response_times else 0
                )
                
                cache_hit_rate = (
                    metrics.cache_hits / (metrics.cache_hits + metrics.cache_misses)
                    if (metrics.cache_hits + metrics.cache_misses) > 0 else 0
                )
                
                return {
                    "endpoint": endpoint,
                    "request_count": metrics.request_count,
                    "avg_response_time": avg_response_time,
                    "min_response_time": metrics.min_response_time if metrics.min_response_time != float('inf') else 0,
                    "max_response_time": metrics.max_response_time,
                    "recent_avg_response_time": recent_avg,
                    "error_count": metrics.error_count,
                    "error_rate": metrics.error_count / metrics.request_count if metrics.request_count > 0 else 0,
                    "cache_hits": metrics.cache_hits,
                    "cache_misses": metrics.cache_misses,
                    "cache_hit_rate": cache_hit_rate
                }
            else:
                # Return all metrics
                return {
                    endpoint: self.get_metrics(endpoint)
                    for endpoint in self.metrics.keys()
                }

class CacheManager:
    """
    Redis-based caching system with TTL and compression
    """
    
    def __init__(self, redis_client: redis.Redis = None):
        self.redis_client = redis_client
        self.default_ttl = 3600  # 1 hour
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.redis_client:
            return None
        
        try:
            cached_data = self.redis_client.get(key)
            if cached_data:
                # Try to decompress if it's compressed
                try:
                    decompressed = gzip.decompress(cached_data.encode('latin1'))
                    return json.loads(decompressed.decode())
                except:
                    # Fallback to regular JSON
                    return json.loads(cached_data)
            return None
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache with optional compression"""
        if not self.redis_client:
            return False
        
        try:
            json_data = json.dumps(value)
            
            # Compress if data is large
            if len(json_data) > 1024:  # 1KB threshold
                compressed = gzip.compress(json_data.encode())
                data_to_store = compressed.decode('latin1')
            else:
                data_to_store = json_data
            
            ttl = ttl or self.default_ttl
            return self.redis_client.setex(key, ttl, data_to_store)
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        if not self.redis_client:
            return False
        
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.warning(f"Cache delete error: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        if not self.redis_client:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Cache clear pattern error: {e}")
            return 0

class RateLimiter:
    """
    Token bucket rate limiter
    """
    
    def __init__(self, redis_client: redis.Redis = None):
        self.redis_client = redis_client
        self.local_buckets = {}  # Fallback for when Redis is unavailable
        self._lock = threading.Lock()
    
    async def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """Check if request is allowed under rate limit"""
        current_time = int(time.time())
        
        if self.redis_client:
            return await self._redis_rate_limit(key, limit, window, current_time)
        else:
            return self._local_rate_limit(key, limit, window, current_time)
    
    async def _redis_rate_limit(self, key: str, limit: int, window: int, current_time: int) -> bool:
        """Redis-based rate limiting"""
        try:
            pipe = self.redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, current_time - window)
            pipe.zcard(key)
            pipe.zadd(key, {str(current_time): current_time})
            pipe.expire(key, window)
            results = pipe.execute()
            
            current_requests = results[1]
            return current_requests < limit
        except Exception as e:
            logger.warning(f"Redis rate limit error: {e}")
            return True  # Allow request if Redis fails
    
    def _local_rate_limit(self, key: str, limit: int, window: int, current_time: int) -> bool:
        """Local memory-based rate limiting (fallback)"""
        with self._lock:
            if key not in self.local_buckets:
                self.local_buckets[key] = deque()
            
            bucket = self.local_buckets[key]
            
            # Remove old entries
            while bucket and bucket[0] <= current_time - window:
                bucket.popleft()
            
            # Check if under limit
            if len(bucket) < limit:
                bucket.append(current_time)
                return True
            
            return False

# Global instances
performance_monitor = PerformanceMonitor()
cache_manager = CacheManager(performance_monitor.redis_client)
rate_limiter = RateLimiter(performance_monitor.redis_client)

def cache_response(ttl: int = 3600, key_prefix: str = "api"):
    """Decorator for caching API responses"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache_manager._generate_key(key_prefix, func.__name__, *args, **kwargs)
            
            # Try to get from cache
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                performance_monitor.record_cache_hit(func.__name__)
                return cached_result
            
            # Execute function
            performance_monitor.record_cache_miss(func.__name__)
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            
            # Cache result
            await cache_manager.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator

def rate_limit(requests_per_minute: int = 60):
    """Decorator for rate limiting"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract identifier (could be IP, user ID, etc.)
            identifier = "global"  # Default identifier
            
            # Check if first arg is a Request object
            if args and hasattr(args[0], 'client'):
                identifier = args[0].client.host
            
            rate_key = f"rate_limit:{func.__name__}:{identifier}"
            
            if not await rate_limiter.is_allowed(rate_key, requests_per_minute, 60):
                from fastapi import HTTPException
                raise HTTPException(status_code=429, detail="Rate limit exceeded")
            
            return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
        return wrapper
    return decorator

async def performance_middleware(request: Request, call_next):
    """FastAPI middleware for performance monitoring"""
    start_time = time.time()
    endpoint = f"{request.method} {request.url.path}"
    
    try:
        response = await call_next(request)
        response_time = time.time() - start_time
        
        # Record metrics
        performance_monitor.record_request(endpoint, response_time, True)
        
        # Add performance headers
        response.headers["X-Response-Time"] = f"{response_time:.3f}s"
        
        return response
        
    except Exception as e:
        response_time = time.time() - start_time
        performance_monitor.record_request(endpoint, response_time, False)
        raise

def compress_response(min_size: int = 1024):
    """Decorator for response compression"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            
            # If result is a Response object, try to compress
            if isinstance(result, Response):
                content = result.body
                if len(content) > min_size:
                    compressed = gzip.compress(content)
                    if len(compressed) < len(content):
                        result.body = compressed
                        result.headers["Content-Encoding"] = "gzip"
                        result.headers["Content-Length"] = str(len(compressed))
            
            return result
        return wrapper
    return decorator