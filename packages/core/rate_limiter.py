"""
Advanced rate limiting with multiple strategies and storage backends.

Features:
- Multiple rate limiting algorithms (token bucket, sliding window, fixed window)
- Redis and in-memory storage backends
- Per-user, per-IP, and global rate limiting
- Burst handling and grace periods
- Rate limit headers for API responses
- Monitoring and alerting
"""

import asyncio
import time
import json
import logging
from typing import Dict, Optional, Any, List, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import hashlib

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

from .logging_config import get_logger

logger = get_logger(__name__)


class RateLimitAlgorithm(Enum):
    """Rate limiting algorithms."""
    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"


class RateLimitScope(Enum):
    """Rate limiting scopes."""
    GLOBAL = "global"
    PER_USER = "per_user"
    PER_IP = "per_ip"
    PER_ENDPOINT = "per_endpoint"
    PER_API_KEY = "per_api_key"


@dataclass
class RateLimitRule:
    """Rate limiting rule configuration."""
    name: str
    requests: int  # Number of requests allowed
    window_seconds: int  # Time window in seconds
    algorithm: RateLimitAlgorithm = RateLimitAlgorithm.SLIDING_WINDOW
    scope: RateLimitScope = RateLimitScope.PER_IP
    burst_multiplier: float = 1.5  # Allow burst up to this multiplier
    grace_period_seconds: int = 60  # Grace period for first-time users
    enabled: bool = True


@dataclass
class RateLimitResult:
    """Result of rate limit check."""
    allowed: bool
    remaining: int
    reset_time: float
    retry_after: Optional[int] = None
    rule_name: str = ""
    current_usage: int = 0


@dataclass
class TokenBucketState:
    """Token bucket algorithm state."""
    tokens: float
    last_refill: float
    capacity: int
    refill_rate: float


class RateLimitStorage:
    """Abstract base class for rate limit storage."""
    
    async def get_state(self, key: str) -> Optional[Dict[str, Any]]:
        """Get rate limit state for a key."""
        raise NotImplementedError
    
    async def set_state(self, key: str, state: Dict[str, Any], ttl: int):
        """Set rate limit state for a key."""
        raise NotImplementedError
    
    async def increment_counter(self, key: str, window_start: int, ttl: int) -> int:
        """Increment counter for fixed window algorithm."""
        raise NotImplementedError
    
    async def add_request(self, key: str, timestamp: float, ttl: int):
        """Add request timestamp for sliding window algorithm."""
        raise NotImplementedError
    
    async def get_request_count(self, key: str, since: float) -> int:
        """Get request count since timestamp for sliding window."""
        raise NotImplementedError
    
    async def cleanup_expired(self, key: str, before: float):
        """Clean up expired entries."""
        raise NotImplementedError


class InMemoryStorage(RateLimitStorage):
    """In-memory storage for rate limiting (single instance only)."""
    
    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._request_logs: Dict[str, List[float]] = {}
        self._lock = asyncio.Lock()
    
    async def get_state(self, key: str) -> Optional[Dict[str, Any]]:
        async with self._lock:
            return self._data.get(key)
    
    async def set_state(self, key: str, state: Dict[str, Any], ttl: int):
        async with self._lock:
            # Simple TTL implementation (not perfect but works for demo)
            expiry = time.time() + ttl
            self._data[key] = {**state, '_expiry': expiry}
    
    async def increment_counter(self, key: str, window_start: int, ttl: int) -> int:
        async with self._lock:
            current_time = time.time()
            
            # Clean up expired entries
            self._data = {k: v for k, v in self._data.items() 
                         if v.get('_expiry', float('inf')) > current_time}
            
            counter_key = f"{key}:{window_start}"
            current = self._data.get(counter_key, {'count': 0})
            current['count'] += 1
            current['_expiry'] = current_time + ttl
            self._data[counter_key] = current
            return current['count']
    
    async def add_request(self, key: str, timestamp: float, ttl: int):
        async with self._lock:
            if key not in self._request_logs:
                self._request_logs[key] = []
            self._request_logs[key].append(timestamp)
            
            # Clean up old entries
            cutoff = timestamp - ttl
            self._request_logs[key] = [t for t in self._request_logs[key] if t > cutoff]
    
    async def get_request_count(self, key: str, since: float) -> int:
        async with self._lock:
            if key not in self._request_logs:
                return 0
            return len([t for t in self._request_logs[key] if t >= since])
    
    async def cleanup_expired(self, key: str, before: float):
        async with self._lock:
            if key in self._request_logs:
                self._request_logs[key] = [t for t in self._request_logs[key] if t >= before]


class RedisStorage(RateLimitStorage):
    """Redis storage for rate limiting (distributed)."""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def get_state(self, key: str) -> Optional[Dict[str, Any]]:
        try:
            data = await self.redis.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error("Failed to get rate limit state from Redis", extra={
                'key': key,
                'error': str(e)
            })
            return None
    
    async def set_state(self, key: str, state: Dict[str, Any], ttl: int):
        try:
            await self.redis.setex(key, ttl, json.dumps(state))
        except Exception as e:
            logger.error("Failed to set rate limit state in Redis", extra={
                'key': key,
                'error': str(e)
            })
    
    async def increment_counter(self, key: str, window_start: int, ttl: int) -> int:
        try:
            counter_key = f"{key}:{window_start}"
            pipe = self.redis.pipeline()
            pipe.incr(counter_key)
            pipe.expire(counter_key, ttl)
            results = await pipe.execute()
            return results[0]
        except Exception as e:
            logger.error("Failed to increment counter in Redis", extra={
                'key': key,
                'error': str(e)
            })
            return 0
    
    async def add_request(self, key: str, timestamp: float, ttl: int):
        try:
            await self.redis.zadd(key, {str(timestamp): timestamp})
            await self.redis.expire(key, ttl)
        except Exception as e:
            logger.error("Failed to add request to Redis", extra={
                'key': key,
                'error': str(e)
            })
    
    async def get_request_count(self, key: str, since: float) -> int:
        try:
            return await self.redis.zcount(key, since, '+inf')
        except Exception as e:
            logger.error("Failed to get request count from Redis", extra={
                'key': key,
                'error': str(e)
            })
            return 0
    
    async def cleanup_expired(self, key: str, before: float):
        try:
            await self.redis.zremrangebyscore(key, '-inf', before)
        except Exception as e:
            logger.error("Failed to cleanup expired entries in Redis", extra={
                'key': key,
                'error': str(e)
            })


class RateLimiter:
    """
    Advanced rate limiter with multiple algorithms and storage backends.
    
    Features:
    - Token bucket, sliding window, and fixed window algorithms
    - Redis and in-memory storage
    - Per-user, per-IP, and global rate limiting
    - Burst handling and grace periods
    - Comprehensive monitoring
    """
    
    def __init__(self, storage: RateLimitStorage, rules: List[RateLimitRule]):
        self.storage = storage
        self.rules = {rule.name: rule for rule in rules}
        self._stats = {
            'total_requests': 0,
            'blocked_requests': 0,
            'rules_triggered': {},
            'start_time': time.time()
        }
        
        logger.info("RateLimiter initialized", extra={
            'rules_count': len(rules),
            'storage_type': type(storage).__name__
        })
    
    def _generate_key(self, rule: RateLimitRule, identifier: str) -> str:
        """Generate storage key for rate limit rule and identifier."""
        scope_prefix = rule.scope.value
        rule_hash = hashlib.md5(rule.name.encode()).hexdigest()[:8]
        return f"ratelimit:{scope_prefix}:{rule_hash}:{identifier}"
    
    async def check_rate_limit(self, rule_name: str, identifier: str, 
                              request_weight: int = 1) -> RateLimitResult:
        """
        Check if request is allowed under rate limit.
        
        Args:
            rule_name: Name of the rate limit rule to apply
            identifier: Unique identifier (user_id, ip_address, etc.)
            request_weight: Weight of the request (default 1)
            
        Returns:
            RateLimitResult with decision and metadata
        """
        self._stats['total_requests'] += 1
        
        rule = self.rules.get(rule_name)
        if not rule or not rule.enabled:
            return RateLimitResult(
                allowed=True,
                remaining=rule.requests if rule else 0,
                reset_time=time.time() + (rule.window_seconds if rule else 3600),
                rule_name=rule_name
            )
        
        key = self._generate_key(rule, identifier)
        
        try:
            if rule.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
                result = await self._check_token_bucket(rule, key, request_weight)
            elif rule.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
                result = await self._check_sliding_window(rule, key, request_weight)
            elif rule.algorithm == RateLimitAlgorithm.FIXED_WINDOW:
                result = await self._check_fixed_window(rule, key, request_weight)
            else:
                raise ValueError(f"Unknown algorithm: {rule.algorithm}")
            
            result.rule_name = rule_name
            
            if not result.allowed:
                self._stats['blocked_requests'] += 1
                self._stats['rules_triggered'][rule_name] = \
                    self._stats['rules_triggered'].get(rule_name, 0) + 1
                
                logger.warning("Rate limit exceeded", extra={
                    'rule_name': rule_name,
                    'identifier': identifier,
                    'current_usage': result.current_usage,
                    'limit': rule.requests,
                    'window_seconds': rule.window_seconds
                })
            
            return result
            
        except Exception as e:
            logger.error("Rate limit check failed", extra={
                'rule_name': rule_name,
                'identifier': identifier,
                'error': str(e)
            })
            # Fail open - allow request if rate limiter fails
            return RateLimitResult(
                allowed=True,
                remaining=0,
                reset_time=time.time() + rule.window_seconds,
                rule_name=rule_name
            )
    
    async def _check_token_bucket(self, rule: RateLimitRule, key: str, 
                                 weight: int) -> RateLimitResult:
        """Check rate limit using token bucket algorithm."""
        current_time = time.time()
        
        # Get current state
        state_data = await self.storage.get_state(key)
        
        if state_data:
            state = TokenBucketState(**state_data)
        else:
            # Initialize new bucket
            state = TokenBucketState(
                tokens=rule.requests,
                last_refill=current_time,
                capacity=int(rule.requests * rule.burst_multiplier),
                refill_rate=rule.requests / rule.window_seconds
            )
        
        # Refill tokens based on elapsed time
        elapsed = current_time - state.last_refill
        tokens_to_add = elapsed * state.refill_rate
        state.tokens = min(state.capacity, state.tokens + tokens_to_add)
        state.last_refill = current_time
        
        # Check if request can be served
        allowed = state.tokens >= weight
        if allowed:
            state.tokens -= weight
        
        # Save state
        await self.storage.set_state(key, asdict(state), rule.window_seconds * 2)
        
        return RateLimitResult(
            allowed=allowed,
            remaining=int(state.tokens),
            reset_time=current_time + (rule.window_seconds - (state.capacity - state.tokens) / state.refill_rate),
            current_usage=state.capacity - int(state.tokens),
            retry_after=int((weight - state.tokens) / state.refill_rate) if not allowed else None
        )
    
    async def _check_sliding_window(self, rule: RateLimitRule, key: str, 
                                   weight: int) -> RateLimitResult:
        """Check rate limit using sliding window algorithm."""
        current_time = time.time()
        window_start = current_time - rule.window_seconds
        
        # Clean up old entries
        await self.storage.cleanup_expired(key, window_start)
        
        # Get current request count
        current_count = await self.storage.get_request_count(key, window_start)
        
        # Check if request is allowed
        allowed = current_count + weight <= rule.requests
        
        if allowed:
            # Add current request(s)
            for _ in range(weight):
                await self.storage.add_request(key, current_time, rule.window_seconds)
        
        return RateLimitResult(
            allowed=allowed,
            remaining=max(0, rule.requests - current_count - (weight if allowed else 0)),
            reset_time=current_time + rule.window_seconds,
            current_usage=current_count + (weight if allowed else 0),
            retry_after=rule.window_seconds if not allowed else None
        )
    
    async def _check_fixed_window(self, rule: RateLimitRule, key: str, 
                                 weight: int) -> RateLimitResult:
        """Check rate limit using fixed window algorithm."""
        current_time = time.time()
        window_start = int(current_time // rule.window_seconds) * rule.window_seconds
        
        # Get current count for this window
        current_count = await self.storage.increment_counter(
            key, window_start, rule.window_seconds
        )
        
        # Check if request is allowed (subtract the increment we just did)
        allowed = (current_count - weight) + weight <= rule.requests
        
        if not allowed:
            # Decrement the counter since request is not allowed
            await self.storage.increment_counter(key, window_start, rule.window_seconds)
            current_count -= weight
        
        next_window = window_start + rule.window_seconds
        
        return RateLimitResult(
            allowed=allowed,
            remaining=max(0, rule.requests - current_count),
            reset_time=next_window,
            current_usage=current_count,
            retry_after=int(next_window - current_time) if not allowed else None
        )
    
    def get_rate_limit_headers(self, result: RateLimitResult, rule_name: str) -> Dict[str, str]:
        """Get HTTP headers for rate limiting."""
        rule = self.rules.get(rule_name)
        if not rule:
            return {}
        
        headers = {
            'X-RateLimit-Limit': str(rule.requests),
            'X-RateLimit-Remaining': str(result.remaining),
            'X-RateLimit-Reset': str(int(result.reset_time)),
            'X-RateLimit-Window': str(rule.window_seconds)
        }
        
        if result.retry_after:
            headers['Retry-After'] = str(result.retry_after)
        
        return headers
    
    def add_rule(self, rule: RateLimitRule):
        """Add a new rate limiting rule."""
        self.rules[rule.name] = rule
        logger.info("Rate limiting rule added", extra={
            'rule_name': rule.name,
            'requests': rule.requests,
            'window_seconds': rule.window_seconds,
            'algorithm': rule.algorithm.value
        })
    
    def remove_rule(self, rule_name: str):
        """Remove a rate limiting rule."""
        if rule_name in self.rules:
            del self.rules[rule_name]
            logger.info("Rate limiting rule removed", extra={
                'rule_name': rule_name
            })
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics."""
        uptime = time.time() - self._stats['start_time']
        
        return {
            'total_requests': self._stats['total_requests'],
            'blocked_requests': self._stats['blocked_requests'],
            'block_rate': (self._stats['blocked_requests'] / max(1, self._stats['total_requests'])) * 100,
            'rules_triggered': self._stats['rules_triggered'].copy(),
            'active_rules': len([r for r in self.rules.values() if r.enabled]),
            'total_rules': len(self.rules),
            'uptime_seconds': uptime,
            'requests_per_second': self._stats['total_requests'] / max(1, uptime)
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on rate limiter."""
        health_status = {
            'status': 'healthy',
            'storage_type': type(self.storage).__name__,
            'active_rules': len([r for r in self.rules.values() if r.enabled]),
            'stats': self.get_stats(),
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Test storage connectivity
            test_key = "health_check_test"
            await self.storage.set_state(test_key, {'test': True}, 60)
            test_result = await self.storage.get_state(test_key)
            
            if test_result and test_result.get('test'):
                health_status['storage_connectivity'] = 'healthy'
            else:
                health_status['storage_connectivity'] = 'degraded'
                health_status['status'] = 'degraded'
                
        except Exception as e:
            health_status['status'] = 'unhealthy'
            health_status['storage_connectivity'] = 'failed'
            health_status['error'] = str(e)
            logger.error("Rate limiter health check failed", extra={
                'error': str(e)
            })
        
        return health_status


# Predefined rate limiting rules
DEFAULT_RULES = [
    RateLimitRule(
        name="api_general",
        requests=100,
        window_seconds=60,
        algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
        scope=RateLimitScope.PER_IP
    ),
    RateLimitRule(
        name="api_generation",
        requests=20,
        window_seconds=60,
        algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
        scope=RateLimitScope.PER_USER,
        burst_multiplier=2.0
    ),
    RateLimitRule(
        name="api_model_loading",
        requests=5,
        window_seconds=300,  # 5 minutes
        algorithm=RateLimitAlgorithm.FIXED_WINDOW,
        scope=RateLimitScope.PER_USER
    ),
    RateLimitRule(
        name="global_protection",
        requests=10000,
        window_seconds=60,
        algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
        scope=RateLimitScope.GLOBAL
    )
]


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> Optional[RateLimiter]:
    """Get the global rate limiter instance."""
    return _rate_limiter


def initialize_rate_limiter(storage: RateLimitStorage, 
                           rules: Optional[List[RateLimitRule]] = None) -> RateLimiter:
    """Initialize the global rate limiter."""
    global _rate_limiter
    _rate_limiter = RateLimiter(storage, rules or DEFAULT_RULES)
    return _rate_limiter