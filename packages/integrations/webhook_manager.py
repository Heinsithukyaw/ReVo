#!/usr/bin/env python3
"""
Webhook Manager for External Integration Resilience
Centralized webhook handling with signature verification, retry mechanisms, and event queuing
"""

import asyncio
import aiohttp
import json
import logging
import time
import hashlib
import hmac
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import uuid
import base64

# Graceful Redis import
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)

class WebhookEventType(Enum):
    """Webhook event types"""
    GITHUB_PUSH = "github.push"
    GITHUB_PR = "github.pull_request"
    GITHUB_ISSUE = "github.issues"
    GITHUB_RELEASE = "github.release"
    SLACK_MESSAGE = "slack.message"
    SLACK_MENTION = "slack.app_mention"
    SLACK_REACTION = "slack.reaction_added"
    JIRA_ISSUE = "jira.issue"
    JIRA_COMMENT = "jira.comment"
    CUSTOM = "custom"

class WebhookStatus(Enum):
    """Webhook processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    DEAD_LETTER = "dead_letter"

class SignatureAlgorithm(Enum):
    """Webhook signature algorithms"""
    SHA1 = "sha1"
    SHA256 = "sha256"
    HMAC_SHA1 = "hmac-sha1"
    HMAC_SHA256 = "hmac-sha256"

@dataclass
class WebhookConfig:
    """Webhook configuration"""
    event_type: WebhookEventType
    endpoint: str
    secret: Optional[str] = None
    signature_algorithm: SignatureAlgorithm = SignatureAlgorithm.HMAC_SHA256
    signature_header: str = "X-Hub-Signature-256"
    max_retries: int = 3
    retry_delay: float = 5.0  # seconds
    retry_backoff: float = 2.0
    timeout: float = 30.0  # seconds
    rate_limit: int = 100  # requests per minute
    enable_queue: bool = True
    queue_size: int = 1000
    dead_letter_threshold: int = 5

@dataclass
class WebhookEvent:
    """Webhook event data"""
    id: str
    event_type: WebhookEventType
    source: str  # e.g., "github", "slack"
    headers: Dict[str, str]
    payload: Dict[str, Any]
    signature: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    status: WebhookStatus = WebhookStatus.PENDING
    retry_count: int = 0
    last_error: Optional[str] = None
    processing_time: Optional[float] = None

@dataclass
class WebhookHandler:
    """Webhook event handler"""
    event_type: WebhookEventType
    handler_func: Callable[[WebhookEvent], Any]
    async_handler: bool = True
    priority: int = 0  # Higher priority handlers run first

class WebhookRateLimiter:
    """Rate limiter for webhook processing"""
    
    def __init__(self, requests_per_minute: int = 100):
        self.requests_per_minute = requests_per_minute
        self.request_times = deque()
        
    async def acquire(self) -> bool:
        """Acquire permission to process webhook"""
        now = time.time()
        cutoff_time = now - 60  # 1 minute window
        
        # Remove old requests
        while self.request_times and self.request_times[0] < cutoff_time:
            self.request_times.popleft()
            
        # Check if under limit
        if len(self.request_times) >= self.requests_per_minute:
            return False
            
        self.request_times.append(now)
        return True
        
    def get_wait_time(self) -> float:
        """Get time to wait before next request"""
        if len(self.request_times) < self.requests_per_minute:
            return 0.0
            
        oldest_request = self.request_times[0]
        return max(0, 60 - (time.time() - oldest_request))

class WebhookQueue:
    """Queue for webhook events"""
    
    def __init__(self, max_size: int = 1000, redis_client: Optional[redis.Redis] = None):
        self.max_size = max_size
        self.redis_client = redis_client
        self.local_queue = asyncio.Queue(maxsize=max_size)
        self.dead_letter_queue = asyncio.Queue()
        
    async def enqueue(self, event: WebhookEvent) -> bool:
        """Add event to queue"""
        try:
            if self.redis_client:
                # Use Redis for persistent queue
                event_data = {
                    'id': event.id,
                    'event_type': event.event_type.value,
                    'source': event.source,
                    'headers': event.headers,
                    'payload': event.payload,
                    'signature': event.signature,
                    'timestamp': event.timestamp.isoformat(),
                    'status': event.status.value,
                    'retry_count': event.retry_count,
                    'last_error': event.last_error
                }
                await self.redis_client.lpush("webhook_queue", json.dumps(event_data))
                return True
            else:
                # Use local queue
                self.local_queue.put_nowait(event)
                return True
        except Exception as e:
            logger.error(f"Failed to enqueue webhook event: {e}")
            return False
            
    async def dequeue(self) -> Optional[WebhookEvent]:
        """Get next event from queue"""
        try:
            if self.redis_client:
                # Get from Redis queue
                event_data = await self.redis_client.brpop("webhook_queue", timeout=1)
                if event_data:
                    event_dict = json.loads(event_data[1])
                    return WebhookEvent(
                        id=event_dict['id'],
                        event_type=WebhookEventType(event_dict['event_type']),
                        source=event_dict['source'],
                        headers=event_dict['headers'],
                        payload=event_dict['payload'],
                        signature=event_dict.get('signature'),
                        timestamp=datetime.fromisoformat(event_dict['timestamp']),
                        status=WebhookStatus(event_dict['status']),
                        retry_count=event_dict['retry_count'],
                        last_error=event_dict.get('last_error')
                    )
            else:
                # Get from local queue
                try:
                    return await asyncio.wait_for(self.local_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    return None
        except Exception as e:
            logger.error(f"Failed to dequeue webhook event: {e}")
            return None
            
    async def move_to_dead_letter(self, event: WebhookEvent):
        """Move event to dead letter queue"""
        event.status = WebhookStatus.DEAD_LETTER
        try:
            if self.redis_client:
                event_data = {
                    'id': event.id,
                    'event_type': event.event_type.value,
                    'source': event.source,
                    'headers': event.headers,
                    'payload': event.payload,
                    'signature': event.signature,
                    'timestamp': event.timestamp.isoformat(),
                    'status': event.status.value,
                    'retry_count': event.retry_count,
                    'last_error': event.last_error
                }
                await self.redis_client.lpush("webhook_dead_letter", json.dumps(event_data))
            else:
                await self.dead_letter_queue.put(event)
        except Exception as e:
            logger.error(f"Failed to move event to dead letter queue: {e}")
            
    async def get_queue_size(self) -> int:
        """Get current queue size"""
        try:
            if self.redis_client:
                return await self.redis_client.llen("webhook_queue")
            else:
                return self.local_queue.qsize()
        except Exception:
            return 0

class WebhookManager:
    """Centralized webhook manager"""
    
    def __init__(self, redis_url: Optional[str] = None):
        self.configs: Dict[WebhookEventType, WebhookConfig] = {}
        self.handlers: Dict[WebhookEventType, List[WebhookHandler]] = defaultdict(list)
        self.rate_limiters: Dict[WebhookEventType, WebhookRateLimiter] = {}
        self.redis_client: Optional[redis.Redis] = None
        self.queue: Optional[WebhookQueue] = None
        self.metrics: Dict[str, Any] = defaultdict(int)
        self.processing_tasks: List[asyncio.Task] = []
        self.running = False
        
        # Initialize Redis if available
        if REDIS_AVAILABLE and redis_url:
            try:
                self.redis_client = redis.from_url(redis_url)
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}")
                
    async def start(self, num_workers: int = 3):
        """Start the webhook manager"""
        self.queue = WebhookQueue(redis_client=self.redis_client)
        self.running = True
        
        # Start processing workers
        for i in range(num_workers):
            task = asyncio.create_task(self._process_webhooks())
            self.processing_tasks.append(task)
            
        logger.info(f"Webhook manager started with {num_workers} workers")
        
    async def stop(self):
        """Stop the webhook manager"""
        self.running = False
        
        # Cancel processing tasks
        for task in self.processing_tasks:
            task.cancel()
            
        # Wait for tasks to complete
        if self.processing_tasks:
            await asyncio.gather(*self.processing_tasks, return_exceptions=True)
            
        if self.redis_client:
            await self.redis_client.close()
            
        logger.info("Webhook manager stopped")
        
    def register_webhook(self, config: WebhookConfig):
        """Register webhook configuration"""
        self.configs[config.event_type] = config
        self.rate_limiters[config.event_type] = WebhookRateLimiter(config.rate_limit)
        
        logger.info(f"Registered webhook: {config.event_type.value}")
        
    def register_handler(self, handler: WebhookHandler):
        """Register webhook event handler"""
        self.handlers[handler.event_type].append(handler)
        
        # Sort handlers by priority (higher priority first)
        self.handlers[handler.event_type].sort(key=lambda h: h.priority, reverse=True)
        
        logger.info(f"Registered handler for: {handler.event_type.value}")
        
    async def receive_webhook(
        self, 
        event_type: WebhookEventType,
        source: str,
        headers: Dict[str, str],
        payload: Dict[str, Any],
        signature: Optional[str] = None
    ) -> str:
        """Receive and process webhook"""
        event_id = str(uuid.uuid4())
        
        # Create webhook event
        event = WebhookEvent(
            id=event_id,
            event_type=event_type,
            source=source,
            headers=headers,
            payload=payload,
            signature=signature
        )
        
        # Verify signature if configured
        if event_type in self.configs:
            config = self.configs[event_type]
            if config.secret and not self._verify_signature(event, config):
                self.metrics[f"{event_type.value}_signature_failures"] += 1
                raise ValueError("Invalid webhook signature")
                
        # Add to queue if enabled
        if event_type in self.configs and self.configs[event_type].enable_queue:
            if await self.queue.enqueue(event):
                self.metrics[f"{event_type.value}_queued"] += 1
                logger.info(f"Webhook event queued: {event_id}")
            else:
                self.metrics[f"{event_type.value}_queue_failures"] += 1
                raise Exception("Failed to queue webhook event")
        else:
            # Process immediately
            await self._process_event(event)
            
        return event_id
        
    def _verify_signature(self, event: WebhookEvent, config: WebhookConfig) -> bool:
        """Verify webhook signature"""
        if not event.signature or not config.secret:
            return False
            
        payload_bytes = json.dumps(event.payload, separators=(',', ':')).encode('utf-8')
        
        if config.signature_algorithm == SignatureAlgorithm.HMAC_SHA256:
            expected_signature = hmac.new(
                config.secret.encode('utf-8'),
                payload_bytes,
                hashlib.sha256
            ).hexdigest()
            expected_signature = f"sha256={expected_signature}"
        elif config.signature_algorithm == SignatureAlgorithm.HMAC_SHA1:
            expected_signature = hmac.new(
                config.secret.encode('utf-8'),
                payload_bytes,
                hashlib.sha1
            ).hexdigest()
            expected_signature = f"sha1={expected_signature}"
        else:
            logger.warning(f"Unsupported signature algorithm: {config.signature_algorithm}")
            return False
            
        return hmac.compare_digest(event.signature, expected_signature)
        
    async def _process_webhooks(self):
        """Process webhooks from queue"""
        while self.running:
            try:
                event = await self.queue.dequeue()
                if event:
                    await self._process_event(event)
            except Exception as e:
                logger.error(f"Error processing webhook: {e}")
                await asyncio.sleep(1)
                
    async def _process_event(self, event: WebhookEvent):
        """Process a single webhook event"""
        start_time = time.time()
        event.status = WebhookStatus.PROCESSING
        
        try:
            # Check rate limiting
            if event.event_type in self.rate_limiters:
                rate_limiter = self.rate_limiters[event.event_type]
                if not await rate_limiter.acquire():
                    wait_time = rate_limiter.get_wait_time()
                    await asyncio.sleep(wait_time)
                    
            # Get handlers for event type
            handlers = self.handlers.get(event.event_type, [])
            if not handlers:
                logger.warning(f"No handlers registered for event type: {event.event_type.value}")
                event.status = WebhookStatus.COMPLETED
                return
                
            # Execute handlers
            for handler in handlers:
                try:
                    if handler.async_handler:
                        await handler.handler_func(event)
                    else:
                        handler.handler_func(event)
                except Exception as e:
                    logger.error(f"Handler error for {event.event_type.value}: {e}")
                    event.last_error = str(e)
                    event.status = WebhookStatus.FAILED
                    
                    # Check if we should retry
                    config = self.configs.get(event.event_type)
                    if config and event.retry_count < config.max_retries:
                        await self._schedule_retry(event, config)
                        return
                    elif config and event.retry_count >= config.dead_letter_threshold:
                        await self.queue.move_to_dead_letter(event)
                        return
                        
            event.status = WebhookStatus.COMPLETED
            event.processing_time = time.time() - start_time
            
            # Update metrics
            self.metrics[f"{event.event_type.value}_processed"] += 1
            self.metrics[f"{event.event_type.value}_processing_time_sum"] += event.processing_time
            
            logger.info(f"Webhook processed successfully: {event.id}")
            
        except Exception as e:
            event.status = WebhookStatus.FAILED
            event.last_error = str(e)
            event.processing_time = time.time() - start_time
            
            self.metrics[f"{event.event_type.value}_failures"] += 1
            logger.error(f"Failed to process webhook {event.id}: {e}")
            
    async def _schedule_retry(self, event: WebhookEvent, config: WebhookConfig):
        """Schedule webhook retry"""
        event.retry_count += 1
        event.status = WebhookStatus.RETRYING
        
        # Calculate retry delay with exponential backoff
        delay = config.retry_delay * (config.retry_backoff ** (event.retry_count - 1))
        
        logger.info(f"Scheduling retry {event.retry_count} for webhook {event.id} in {delay}s")
        
        # Schedule retry
        asyncio.create_task(self._retry_after_delay(event, delay))
        
    async def _retry_after_delay(self, event: WebhookEvent, delay: float):
        """Retry webhook after delay"""
        await asyncio.sleep(delay)
        event.status = WebhookStatus.PENDING
        await self.queue.enqueue(event)
        
    async def get_webhook_stats(self, event_type: Optional[WebhookEventType] = None) -> Dict[str, Any]:
        """Get webhook processing statistics"""
        if event_type:
            prefix = event_type.value
            processed = self.metrics.get(f"{prefix}_processed", 0)
            failures = self.metrics.get(f"{prefix}_failures", 0)
            processing_time_sum = self.metrics.get(f"{prefix}_processing_time_sum", 0)
            
            return {
                "event_type": event_type.value,
                "processed": processed,
                "failures": failures,
                "success_rate": (processed / (processed + failures) * 100) if (processed + failures) > 0 else 0,
                "avg_processing_time": (processing_time_sum / processed) if processed > 0 else 0,
                "queue_size": await self.queue.get_queue_size() if self.queue else 0
            }
        else:
            # Return stats for all event types
            stats = {}
            for event_type in self.configs:
                stats[event_type.value] = await self.get_webhook_stats(event_type)
                
            return {
                "total_stats": stats,
                "queue_size": await self.queue.get_queue_size() if self.queue else 0
            }
            
    async def get_health_status(self) -> Dict[str, Any]:
        """Get webhook manager health status"""
        total_processed = sum(self.metrics.get(f"{et.value}_processed", 0) for et in self.configs)
        total_failures = sum(self.metrics.get(f"{et.value}_failures", 0) for et in self.configs)
        
        success_rate = (total_processed / (total_processed + total_failures) * 100) if (total_processed + total_failures) > 0 else 100
        
        return {
            "status": "healthy" if success_rate >= 95 else "degraded" if success_rate >= 80 else "unhealthy",
            "running": self.running,
            "workers": len(self.processing_tasks),
            "total_processed": total_processed,
            "total_failures": total_failures,
            "success_rate": round(success_rate, 2),
            "queue_size": await self.queue.get_queue_size() if self.queue else 0,
            "registered_webhooks": len(self.configs),
            "registered_handlers": sum(len(handlers) for handlers in self.handlers.values())
        }

# Global webhook manager instance
_webhook_manager_instance: Optional[WebhookManager] = None

async def get_webhook_manager(redis_url: Optional[str] = None) -> WebhookManager:
    """Get or create the global webhook manager instance"""
    global _webhook_manager_instance
    
    if _webhook_manager_instance is None:
        _webhook_manager_instance = WebhookManager(redis_url)
        await _webhook_manager_instance.start()
        
    return _webhook_manager_instance

async def shutdown_webhook_manager():
    """Shutdown the global webhook manager instance"""
    global _webhook_manager_instance
    
    if _webhook_manager_instance:
        await _webhook_manager_instance.stop()
        _webhook_manager_instance = None