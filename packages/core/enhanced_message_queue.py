"""
Enhanced Message Queue System for Phase 2 Multi-Agent Communication Optimization
Implements Redis-based message queuing with persistence, routing, and advanced features
"""

import asyncio
import json
import time
import logging
import uuid
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

# Handle Redis import gracefully
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

logger = logging.getLogger(__name__)

class MessagePriority(Enum):
    """Enhanced message priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5

class MessageStatus(Enum):
    """Message processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"
    DEAD_LETTER = "dead_letter"

class RoutingStrategy(Enum):
    """Message routing strategies"""
    DIRECT = "direct"           # Direct to specific agent
    ROUND_ROBIN = "round_robin" # Round-robin among available agents
    LEAST_BUSY = "least_busy"   # Route to least busy agent
    BROADCAST = "broadcast"     # Send to all agents of type
    TOPIC = "topic"            # Topic-based routing

@dataclass
class EnhancedMessage:
    """Enhanced message structure with advanced features"""
    id: str
    type: str
    sender: str
    recipient: str
    content: Dict[str, Any]
    priority: MessagePriority = MessagePriority.NORMAL
    routing_strategy: RoutingStrategy = RoutingStrategy.DIRECT
    topic: Optional[str] = None
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    ttl: Optional[int] = None  # Time to live in seconds
    retry_count: int = 0
    max_retries: int = 3
    status: MessageStatus = MessageStatus.PENDING
    created_at: datetime = None
    processed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}
        if not self.id:
            self.id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization"""
        data = asdict(self)
        data['priority'] = self.priority.value
        data['routing_strategy'] = self.routing_strategy.value
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        if self.processed_at:
            data['processed_at'] = self.processed_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnhancedMessage':
        """Create message from dictionary"""
        data['priority'] = MessagePriority(data['priority'])
        data['routing_strategy'] = RoutingStrategy(data['routing_strategy'])
        data['status'] = MessageStatus(data['status'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('processed_at'):
            data['processed_at'] = datetime.fromisoformat(data['processed_at'])
        return cls(**data)
    
    def is_expired(self) -> bool:
        """Check if message has expired"""
        if not self.ttl:
            return False
        return (datetime.now() - self.created_at).total_seconds() > self.ttl

@dataclass
class MessageBatch:
    """Batch of messages for efficient processing"""
    id: str
    messages: List[EnhancedMessage]
    batch_size: int
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class EnhancedMessageQueue:
    """
    Enhanced Redis-based message queue with advanced features:
    - Message persistence and reliability
    - Priority queuing
    - Message routing strategies
    - Batch processing
    - Dead letter queues
    - Message deduplication
    - Topic-based routing
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379", namespace: str = "revoagent"):
        self.redis_url = redis_url
        self.namespace = namespace
        self.redis_client: Optional[redis.Redis] = None
        self.message_handlers: Dict[str, Callable] = {}
        self.topic_subscribers: Dict[str, Set[str]] = {}
        self.agent_load: Dict[str, int] = {}  # Track agent load for routing
        self.round_robin_counters: Dict[str, int] = {}
        self.deduplication_cache: Set[str] = set()
        self.batch_processors: Dict[str, Callable] = {}
        
        # Queue names
        self.priority_queues = {
            MessagePriority.CRITICAL: f"{namespace}:queue:critical",
            MessagePriority.URGENT: f"{namespace}:queue:urgent", 
            MessagePriority.HIGH: f"{namespace}:queue:high",
            MessagePriority.NORMAL: f"{namespace}:queue:normal",
            MessagePriority.LOW: f"{namespace}:queue:low"
        }
        self.dead_letter_queue = f"{namespace}:queue:dead_letter"
        self.processing_queue = f"{namespace}:queue:processing"
        self.agent_queues_prefix = f"{namespace}:agent"
        self.topic_prefix = f"{namespace}:topic"
        
        # Metrics
        self.metrics = {
            "messages_sent": 0,
            "messages_received": 0,
            "messages_failed": 0,
            "messages_retried": 0,
            "messages_dead_lettered": 0,
            "batches_processed": 0
        }
    
    async def initialize(self):
        """Initialize Redis connection and setup"""
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            await self.redis_client.ping()
            logger.info("Enhanced message queue initialized successfully")
            
            # Setup cleanup task
            asyncio.create_task(self._cleanup_expired_messages())
            
        except Exception as e:
            logger.error(f"Failed to initialize message queue: {e}")
            raise
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
    
    @asynccontextmanager
    async def get_redis(self):
        """Context manager for Redis operations"""
        if not self.redis_client:
            await self.initialize()
        yield self.redis_client
    
    async def send_message(self, message: EnhancedMessage) -> bool:
        """Send message with enhanced routing and persistence"""
        try:
            # Check for duplicates
            if await self._is_duplicate(message):
                logger.debug(f"Duplicate message detected: {message.id}")
                return True
            
            # Route message based on strategy
            if message.routing_strategy == RoutingStrategy.DIRECT:
                success = await self._send_direct(message)
            elif message.routing_strategy == RoutingStrategy.ROUND_ROBIN:
                success = await self._send_round_robin(message)
            elif message.routing_strategy == RoutingStrategy.LEAST_BUSY:
                success = await self._send_least_busy(message)
            elif message.routing_strategy == RoutingStrategy.BROADCAST:
                success = await self._send_broadcast(message)
            elif message.routing_strategy == RoutingStrategy.TOPIC:
                success = await self._send_topic(message)
            else:
                success = await self._send_direct(message)
            
            if success:
                self.metrics["messages_sent"] += 1
                await self._add_to_deduplication_cache(message)
            else:
                self.metrics["messages_failed"] += 1
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to send message {message.id}: {e}")
            self.metrics["messages_failed"] += 1
            return False
    
    async def _send_direct(self, message: EnhancedMessage) -> bool:
        """Send message directly to specific agent"""
        async with self.get_redis() as redis_client:
            queue_name = f"{self.agent_queues_prefix}:{message.recipient}"
            priority_queue = self.priority_queues[message.priority]
            
            # Store message data
            message_data = json.dumps(message.to_dict())
            await redis_client.hset(f"{self.namespace}:messages", message.id, message_data)
            
            # Add to priority queue
            priority_score = self._get_priority_score(message)
            await redis_client.zadd(priority_queue, {message.id: priority_score})
            
            # Add to agent-specific queue
            await redis_client.lpush(queue_name, message.id)
            
            # Set TTL if specified
            if message.ttl:
                await redis_client.expire(f"{self.namespace}:messages:{message.id}", message.ttl)
            
            return True
    
    async def _send_round_robin(self, message: EnhancedMessage) -> bool:
        """Send message using round-robin strategy"""
        agent_type = message.recipient  # recipient is agent type for round-robin
        available_agents = await self._get_available_agents(agent_type)
        
        if not available_agents:
            logger.warning(f"No available agents for type: {agent_type}")
            return False
        
        # Get next agent in round-robin
        counter_key = f"rr:{agent_type}"
        current_counter = self.round_robin_counters.get(counter_key, 0)
        selected_agent = available_agents[current_counter % len(available_agents)]
        self.round_robin_counters[counter_key] = current_counter + 1
        
        # Update message recipient and send
        message.recipient = selected_agent
        return await self._send_direct(message)
    
    async def _send_least_busy(self, message: EnhancedMessage) -> bool:
        """Send message to least busy agent"""
        agent_type = message.recipient
        available_agents = await self._get_available_agents(agent_type)
        
        if not available_agents:
            return False
        
        # Find least busy agent
        least_busy_agent = min(available_agents, 
                              key=lambda agent: self.agent_load.get(agent, 0))
        
        message.recipient = least_busy_agent
        return await self._send_direct(message)
    
    async def _send_broadcast(self, message: EnhancedMessage) -> bool:
        """Send message to all agents of specified type"""
        agent_type = message.recipient
        available_agents = await self._get_available_agents(agent_type)
        
        success_count = 0
        for agent in available_agents:
            message_copy = EnhancedMessage(
                id=f"{message.id}_{agent}",
                type=message.type,
                sender=message.sender,
                recipient=agent,
                content=message.content.copy(),
                priority=message.priority,
                routing_strategy=RoutingStrategy.DIRECT,
                topic=message.topic,
                correlation_id=message.correlation_id,
                reply_to=message.reply_to,
                ttl=message.ttl,
                metadata=message.metadata.copy()
            )
            
            if await self._send_direct(message_copy):
                success_count += 1
        
        return success_count > 0
    
    async def _send_topic(self, message: EnhancedMessage) -> bool:
        """Send message using topic-based routing"""
        if not message.topic:
            logger.error("Topic routing requires message.topic to be set")
            return False
        
        subscribers = self.topic_subscribers.get(message.topic, set())
        if not subscribers:
            logger.warning(f"No subscribers for topic: {message.topic}")
            return False
        
        success_count = 0
        for subscriber in subscribers:
            message_copy = EnhancedMessage(
                id=f"{message.id}_{subscriber}",
                type=message.type,
                sender=message.sender,
                recipient=subscriber,
                content=message.content.copy(),
                priority=message.priority,
                routing_strategy=RoutingStrategy.DIRECT,
                topic=message.topic,
                correlation_id=message.correlation_id,
                reply_to=message.reply_to,
                ttl=message.ttl,
                metadata=message.metadata.copy()
            )
            
            if await self._send_direct(message_copy):
                success_count += 1
        
        return success_count > 0
    
    async def receive_message(self, agent_id: str, timeout: Optional[float] = None) -> Optional[EnhancedMessage]:
        """Receive message for specific agent with priority handling"""
        try:
            async with self.get_redis() as redis_client:
                queue_name = f"{self.agent_queues_prefix}:{agent_id}"
                
                # Try to get message from agent queue
                if timeout:
                    result = await redis_client.brpop(queue_name, timeout=timeout)
                else:
                    result = await redis_client.rpop(queue_name)
                
                if not result:
                    return None
                
                message_id = result[1] if isinstance(result, tuple) else result
                
                # Get message data
                message_data = await redis_client.hget(f"{self.namespace}:messages", message_id)
                if not message_data:
                    logger.warning(f"Message data not found for ID: {message_id}")
                    return None
                
                message = EnhancedMessage.from_dict(json.loads(message_data))
                
                # Check if message expired
                if message.is_expired():
                    await self._move_to_dead_letter(message, "expired")
                    return None
                
                # Mark as processing
                message.status = MessageStatus.PROCESSING
                message.processed_at = datetime.now()
                await redis_client.hset(f"{self.namespace}:messages", message_id, 
                                      json.dumps(message.to_dict()))
                
                # Update agent load
                self.agent_load[agent_id] = self.agent_load.get(agent_id, 0) + 1
                
                self.metrics["messages_received"] += 1
                return message
                
        except Exception as e:
            logger.error(f"Failed to receive message for {agent_id}: {e}")
            return None
    
    async def acknowledge_message(self, message: EnhancedMessage, success: bool = True) -> bool:
        """Acknowledge message processing completion"""
        try:
            async with self.get_redis() as redis_client:
                if success:
                    message.status = MessageStatus.COMPLETED
                    # Remove from processing, keep in history for a while
                    await redis_client.expire(f"{self.namespace}:messages:{message.id}", 3600)  # 1 hour
                else:
                    # Handle retry logic
                    if message.retry_count < message.max_retries:
                        message.retry_count += 1
                        message.status = MessageStatus.RETRY
                        # Re-queue for retry with exponential backoff
                        delay = min(300, 2 ** message.retry_count)  # Max 5 minutes
                        await asyncio.sleep(delay)
                        await self.send_message(message)
                        self.metrics["messages_retried"] += 1
                    else:
                        # Move to dead letter queue
                        await self._move_to_dead_letter(message, "max_retries_exceeded")
                
                # Update agent load
                if message.recipient in self.agent_load:
                    self.agent_load[message.recipient] = max(0, self.agent_load[message.recipient] - 1)
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to acknowledge message {message.id}: {e}")
            return False
    
    async def send_batch(self, messages: List[EnhancedMessage]) -> int:
        """Send batch of messages efficiently"""
        if not messages:
            return 0
        
        batch = MessageBatch(
            id=str(uuid.uuid4()),
            messages=messages,
            batch_size=len(messages)
        )
        
        success_count = 0
        async with self.get_redis() as redis_client:
            pipe = redis_client.pipeline()
            
            for message in messages:
                try:
                    # Batch Redis operations
                    message_data = json.dumps(message.to_dict())
                    pipe.hset(f"{self.namespace}:messages", message.id, message_data)
                    
                    queue_name = f"{self.agent_queues_prefix}:{message.recipient}"
                    pipe.lpush(queue_name, message.id)
                    
                    priority_queue = self.priority_queues[message.priority]
                    priority_score = self._get_priority_score(message)
                    pipe.zadd(priority_queue, {message.id: priority_score})
                    
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to prepare batch message {message.id}: {e}")
            
            # Execute batch
            await pipe.execute()
        
        self.metrics["messages_sent"] += success_count
        self.metrics["batches_processed"] += 1
        
        logger.info(f"Sent batch {batch.id}: {success_count}/{len(messages)} messages")
        return success_count
    
    async def subscribe_to_topic(self, agent_id: str, topic: str):
        """Subscribe agent to topic"""
        if topic not in self.topic_subscribers:
            self.topic_subscribers[topic] = set()
        self.topic_subscribers[topic].add(agent_id)
        logger.debug(f"Agent {agent_id} subscribed to topic {topic}")
    
    async def unsubscribe_from_topic(self, agent_id: str, topic: str):
        """Unsubscribe agent from topic"""
        if topic in self.topic_subscribers:
            self.topic_subscribers[topic].discard(agent_id)
            if not self.topic_subscribers[topic]:
                del self.topic_subscribers[topic]
        logger.debug(f"Agent {agent_id} unsubscribed from topic {topic}")
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get comprehensive queue statistics"""
        async with self.get_redis() as redis_client:
            stats = {
                "metrics": self.metrics.copy(),
                "queue_sizes": {},
                "agent_loads": self.agent_load.copy(),
                "topic_subscribers": {
                    topic: len(subscribers) 
                    for topic, subscribers in self.topic_subscribers.items()
                },
                "priority_queue_sizes": {}
            }
            
            # Get priority queue sizes
            for priority, queue_name in self.priority_queues.items():
                size = await redis_client.zcard(queue_name)
                stats["priority_queue_sizes"][priority.name] = size
            
            # Get dead letter queue size
            dead_letter_size = await redis_client.llen(self.dead_letter_queue)
            stats["dead_letter_queue_size"] = dead_letter_size
            
            return stats
    
    def _get_priority_score(self, message: EnhancedMessage) -> float:
        """Calculate priority score for message ordering"""
        base_score = message.priority.value * 1000
        time_score = time.time()  # Earlier messages get higher priority
        return base_score + time_score
    
    async def _get_available_agents(self, agent_type: str) -> List[str]:
        """Get list of available agents for given type"""
        # This would integrate with agent registry
        # For now, return mock data
        async with self.get_redis() as redis_client:
            pattern = f"{self.agent_queues_prefix}:{agent_type}:*"
            keys = await redis_client.keys(pattern)
            return [key.split(':')[-1] for key in keys]
    
    async def _is_duplicate(self, message: EnhancedMessage) -> bool:
        """Check if message is duplicate"""
        # Simple deduplication based on content hash
        content_hash = hash(json.dumps(message.content, sort_keys=True))
        dedup_key = f"{message.sender}:{message.type}:{content_hash}"
        
        if dedup_key in self.deduplication_cache:
            return True
        
        # Check Redis for longer-term deduplication
        async with self.get_redis() as redis_client:
            exists = await redis_client.exists(f"{self.namespace}:dedup:{dedup_key}")
            return bool(exists)
    
    async def _add_to_deduplication_cache(self, message: EnhancedMessage):
        """Add message to deduplication cache"""
        content_hash = hash(json.dumps(message.content, sort_keys=True))
        dedup_key = f"{message.sender}:{message.type}:{content_hash}"
        
        self.deduplication_cache.add(dedup_key)
        
        # Also store in Redis with TTL
        async with self.get_redis() as redis_client:
            await redis_client.setex(f"{self.namespace}:dedup:{dedup_key}", 3600, "1")  # 1 hour TTL
    
    async def _move_to_dead_letter(self, message: EnhancedMessage, reason: str):
        """Move message to dead letter queue"""
        message.status = MessageStatus.DEAD_LETTER
        message.metadata["dead_letter_reason"] = reason
        message.metadata["dead_letter_time"] = datetime.now().isoformat()
        
        async with self.get_redis() as redis_client:
            await redis_client.lpush(self.dead_letter_queue, json.dumps(message.to_dict()))
        
        self.metrics["messages_dead_lettered"] += 1
        logger.warning(f"Message {message.id} moved to dead letter queue: {reason}")
    
    async def _cleanup_expired_messages(self):
        """Background task to cleanup expired messages"""
        while True:
            try:
                async with self.get_redis() as redis_client:
                    # Clean up expired messages from priority queues
                    current_time = time.time()
                    for queue_name in self.priority_queues.values():
                        # Remove messages older than 1 hour from priority queues
                        await redis_client.zremrangebyscore(queue_name, 0, current_time - 3600)
                
                # Clean deduplication cache
                if len(self.deduplication_cache) > 10000:
                    self.deduplication_cache.clear()
                
                await asyncio.sleep(300)  # Run every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(60)

# Global message queue instance
message_queue = EnhancedMessageQueue()