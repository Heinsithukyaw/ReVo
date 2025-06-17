"""
Agent Registry Service for Phase 2 Multi-Agent Communication Optimization
Manages agent lifecycle, status tracking, load balancing, and coordination
"""

import asyncio
import json
import time
import logging
import uuid
from typing import Dict, List, Any, Optional, Set, Callable
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

class AgentStatus(Enum):
    """Agent status enumeration"""
    STARTING = "starting"
    IDLE = "idle"
    BUSY = "busy"
    OVERLOADED = "overloaded"
    ERROR = "error"
    MAINTENANCE = "maintenance"
    STOPPING = "stopping"
    OFFLINE = "offline"

class AgentCapability(Enum):
    """Agent capability types"""
    CODE_GENERATION = "code_generation"
    CODE_ANALYSIS = "code_analysis"
    DEBUGGING = "debugging"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    DEPLOYMENT = "deployment"
    SECURITY_AUDIT = "security_audit"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    ARCHITECTURE_DESIGN = "architecture_design"
    INTEGRATION = "integration"
    BROWSER_AUTOMATION = "browser_automation"
    MEMORY_MANAGEMENT = "memory_management"

class LoadBalancingStrategy(Enum):
    """Load balancing strategies"""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    LEAST_RESPONSE_TIME = "least_response_time"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    RESOURCE_BASED = "resource_based"

@dataclass
class AgentMetrics:
    """Agent performance metrics"""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    average_response_time: float = 0.0
    current_load: int = 0
    max_concurrent_tasks: int = 10
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    last_activity: Optional[datetime] = None
    uptime: float = 0.0
    
    def get_success_rate(self) -> float:
        """Calculate task success rate"""
        if self.total_tasks == 0:
            return 1.0
        return self.completed_tasks / self.total_tasks
    
    def get_load_percentage(self) -> float:
        """Calculate current load percentage"""
        return (self.current_load / self.max_concurrent_tasks) * 100
    
    def is_overloaded(self) -> bool:
        """Check if agent is overloaded"""
        return self.current_load >= self.max_concurrent_tasks

@dataclass
class AgentInfo:
    """Comprehensive agent information"""
    agent_id: str
    agent_type: str
    capabilities: List[AgentCapability]
    status: AgentStatus
    version: str
    host: str
    port: int
    endpoint: str
    weight: float = 1.0  # For weighted load balancing
    tags: Dict[str, str] = None
    config: Dict[str, Any] = None
    metrics: AgentMetrics = None
    registered_at: datetime = None
    last_heartbeat: datetime = None
    heartbeat_interval: int = 30  # seconds
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = {}
        if self.config is None:
            self.config = {}
        if self.metrics is None:
            self.metrics = AgentMetrics()
        if self.registered_at is None:
            self.registered_at = datetime.now()
        if self.last_heartbeat is None:
            self.last_heartbeat = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['capabilities'] = [cap.value for cap in self.capabilities]
        data['status'] = self.status.value
        data['registered_at'] = self.registered_at.isoformat()
        data['last_heartbeat'] = self.last_heartbeat.isoformat()
        if self.metrics.last_activity:
            data['metrics']['last_activity'] = self.metrics.last_activity.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentInfo':
        """Create from dictionary"""
        data['capabilities'] = [AgentCapability(cap) for cap in data['capabilities']]
        data['status'] = AgentStatus(data['status'])
        data['registered_at'] = datetime.fromisoformat(data['registered_at'])
        data['last_heartbeat'] = datetime.fromisoformat(data['last_heartbeat'])
        
        # Handle metrics
        metrics_data = data.get('metrics', {})
        if 'last_activity' in metrics_data and metrics_data['last_activity']:
            metrics_data['last_activity'] = datetime.fromisoformat(metrics_data['last_activity'])
        data['metrics'] = AgentMetrics(**metrics_data)
        
        return cls(**data)
    
    def is_healthy(self) -> bool:
        """Check if agent is healthy based on heartbeat"""
        if self.status == AgentStatus.OFFLINE:
            return False
        
        time_since_heartbeat = (datetime.now() - self.last_heartbeat).total_seconds()
        return time_since_heartbeat <= (self.heartbeat_interval * 2)  # Allow 2x interval
    
    def can_handle_task(self, required_capability: AgentCapability) -> bool:
        """Check if agent can handle a task with required capability"""
        return (
            required_capability in self.capabilities and
            self.status in [AgentStatus.IDLE, AgentStatus.BUSY] and
            not self.metrics.is_overloaded() and
            self.is_healthy()
        )

class AgentRegistry:
    """
    Centralized agent registry for managing agent lifecycle and coordination
    
    Features:
    - Agent registration and discovery
    - Health monitoring and heartbeat tracking
    - Load balancing and task routing
    - Performance metrics collection
    - Agent capability matching
    - Automatic failover and recovery
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379", namespace: str = "revoagent"):
        self.redis_url = redis_url
        self.namespace = namespace
        self.redis_client: Optional[redis.Redis] = None
        
        # In-memory caches for performance
        self.agents: Dict[str, AgentInfo] = {}
        self.capability_index: Dict[AgentCapability, Set[str]] = {}
        self.type_index: Dict[str, Set[str]] = {}
        self.load_balancers: Dict[str, Callable] = {}
        
        # Round-robin counters
        self.round_robin_counters: Dict[str, int] = {}
        
        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {
            "agent_registered": [],
            "agent_unregistered": [],
            "agent_status_changed": [],
            "agent_failed": [],
            "agent_recovered": []
        }
        
        # Registry statistics
        self.stats = {
            "total_agents": 0,
            "active_agents": 0,
            "failed_agents": 0,
            "total_registrations": 0,
            "total_heartbeats": 0,
            "load_balancing_requests": 0
        }
        
        # Redis keys
        self.agents_key = f"{namespace}:agents"
        self.capabilities_key = f"{namespace}:capabilities"
        self.types_key = f"{namespace}:types"
        self.metrics_key = f"{namespace}:metrics"
    
    async def initialize(self):
        """Initialize registry and load existing agents"""
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            await self.redis_client.ping()
            
            # Load existing agents from Redis
            await self._load_agents_from_redis()
            
            # Start background tasks
            asyncio.create_task(self._health_monitor())
            asyncio.create_task(self._metrics_collector())
            
            logger.info("Agent registry initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize agent registry: {e}")
            raise
    
    async def close(self):
        """Close registry and cleanup"""
        if self.redis_client:
            await self.redis_client.close()
    
    @asynccontextmanager
    async def get_redis(self):
        """Context manager for Redis operations"""
        if not self.redis_client:
            await self.initialize()
        yield self.redis_client
    
    async def register_agent(self, agent_info: AgentInfo) -> bool:
        """Register a new agent"""
        try:
            # Validate agent info
            if not agent_info.agent_id or not agent_info.agent_type:
                raise ValueError("Agent ID and type are required")
            
            # Store in memory
            self.agents[agent_info.agent_id] = agent_info
            
            # Update indexes
            self._update_capability_index(agent_info.agent_id, agent_info.capabilities)
            self._update_type_index(agent_info.agent_id, agent_info.agent_type)
            
            # Store in Redis
            async with self.get_redis() as redis_client:
                await redis_client.hset(
                    self.agents_key, 
                    agent_info.agent_id, 
                    json.dumps(agent_info.to_dict())
                )
                
                # Update capability index in Redis
                for capability in agent_info.capabilities:
                    await redis_client.sadd(
                        f"{self.capabilities_key}:{capability.value}",
                        agent_info.agent_id
                    )
                
                # Update type index in Redis
                await redis_client.sadd(
                    f"{self.types_key}:{agent_info.agent_type}",
                    agent_info.agent_id
                )
            
            # Update statistics
            self.stats["total_agents"] += 1
            self.stats["active_agents"] += 1
            self.stats["total_registrations"] += 1
            
            # Trigger event
            await self._trigger_event("agent_registered", agent_info)
            
            logger.info(f"Agent registered: {agent_info.agent_id} ({agent_info.agent_type})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register agent {agent_info.agent_id}: {e}")
            return False
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent"""
        try:
            if agent_id not in self.agents:
                logger.warning(f"Agent not found for unregistration: {agent_id}")
                return False
            
            agent_info = self.agents[agent_id]
            
            # Remove from memory
            del self.agents[agent_id]
            
            # Update indexes
            self._remove_from_capability_index(agent_id, agent_info.capabilities)
            self._remove_from_type_index(agent_id, agent_info.agent_type)
            
            # Remove from Redis
            async with self.get_redis() as redis_client:
                await redis_client.hdel(self.agents_key, agent_id)
                
                # Remove from capability indexes
                for capability in agent_info.capabilities:
                    await redis_client.srem(
                        f"{self.capabilities_key}:{capability.value}",
                        agent_id
                    )
                
                # Remove from type index
                await redis_client.srem(
                    f"{self.types_key}:{agent_info.agent_type}",
                    agent_id
                )
            
            # Update statistics
            self.stats["total_agents"] -= 1
            self.stats["active_agents"] -= 1
            
            # Trigger event
            await self._trigger_event("agent_unregistered", agent_info)
            
            logger.info(f"Agent unregistered: {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister agent {agent_id}: {e}")
            return False
    
    async def update_agent_status(self, agent_id: str, status: AgentStatus, metrics: Optional[AgentMetrics] = None) -> bool:
        """Update agent status and metrics"""
        try:
            if agent_id not in self.agents:
                logger.warning(f"Agent not found for status update: {agent_id}")
                return False
            
            agent_info = self.agents[agent_id]
            old_status = agent_info.status
            
            # Update status and heartbeat
            agent_info.status = status
            agent_info.last_heartbeat = datetime.now()
            
            # Update metrics if provided
            if metrics:
                agent_info.metrics = metrics
                agent_info.metrics.last_activity = datetime.now()
            
            # Store in Redis
            async with self.get_redis() as redis_client:
                await redis_client.hset(
                    self.agents_key,
                    agent_id,
                    json.dumps(agent_info.to_dict())
                )
            
            # Update statistics
            self.stats["total_heartbeats"] += 1
            
            # Trigger status change event
            if old_status != status:
                await self._trigger_event("agent_status_changed", agent_info, {
                    "old_status": old_status,
                    "new_status": status
                })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update agent status {agent_id}: {e}")
            return False
    
    async def heartbeat(self, agent_id: str, metrics: Optional[AgentMetrics] = None) -> bool:
        """Process agent heartbeat"""
        if agent_id not in self.agents:
            return False
        
        agent_info = self.agents[agent_id]
        
        # If agent was offline, mark as recovered
        if agent_info.status == AgentStatus.OFFLINE:
            await self._trigger_event("agent_recovered", agent_info)
            agent_info.status = AgentStatus.IDLE
        
        return await self.update_agent_status(agent_id, agent_info.status, metrics)
    
    async def get_agent(self, agent_id: str) -> Optional[AgentInfo]:
        """Get agent information"""
        return self.agents.get(agent_id)
    
    async def get_agents_by_capability(self, capability: AgentCapability) -> List[AgentInfo]:
        """Get all agents with specific capability"""
        agent_ids = self.capability_index.get(capability, set())
        return [self.agents[agent_id] for agent_id in agent_ids if agent_id in self.agents]
    
    async def get_agents_by_type(self, agent_type: str) -> List[AgentInfo]:
        """Get all agents of specific type"""
        agent_ids = self.type_index.get(agent_type, set())
        return [self.agents[agent_id] for agent_id in agent_ids if agent_id in self.agents]
    
    async def get_available_agents(self, capability: Optional[AgentCapability] = None, agent_type: Optional[str] = None) -> List[AgentInfo]:
        """Get available agents matching criteria"""
        candidates = list(self.agents.values())
        
        # Filter by capability
        if capability:
            candidates = [agent for agent in candidates if agent.can_handle_task(capability)]
        
        # Filter by type
        if agent_type:
            candidates = [agent for agent in candidates if agent.agent_type == agent_type]
        
        # Filter by availability
        available = [
            agent for agent in candidates
            if agent.status in [AgentStatus.IDLE, AgentStatus.BUSY] and
               not agent.metrics.is_overloaded() and
               agent.is_healthy()
        ]
        
        return available
    
    async def select_agent(
        self, 
        capability: Optional[AgentCapability] = None,
        agent_type: Optional[str] = None,
        strategy: LoadBalancingStrategy = LoadBalancingStrategy.LEAST_CONNECTIONS
    ) -> Optional[AgentInfo]:
        """Select best agent using specified load balancing strategy"""
        
        available_agents = await self.get_available_agents(capability, agent_type)
        if not available_agents:
            return None
        
        self.stats["load_balancing_requests"] += 1
        
        if strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._select_round_robin(available_agents, capability or agent_type)
        elif strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return self._select_least_connections(available_agents)
        elif strategy == LoadBalancingStrategy.LEAST_RESPONSE_TIME:
            return self._select_least_response_time(available_agents)
        elif strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
            return self._select_weighted_round_robin(available_agents)
        elif strategy == LoadBalancingStrategy.RESOURCE_BASED:
            return self._select_resource_based(available_agents)
        else:
            return available_agents[0]  # Default to first available
    
    def _select_round_robin(self, agents: List[AgentInfo], key: str) -> AgentInfo:
        """Round-robin selection"""
        counter = self.round_robin_counters.get(key, 0)
        selected = agents[counter % len(agents)]
        self.round_robin_counters[key] = counter + 1
        return selected
    
    def _select_least_connections(self, agents: List[AgentInfo]) -> AgentInfo:
        """Select agent with least current load"""
        return min(agents, key=lambda agent: agent.metrics.current_load)
    
    def _select_least_response_time(self, agents: List[AgentInfo]) -> AgentInfo:
        """Select agent with best response time"""
        return min(agents, key=lambda agent: agent.metrics.average_response_time)
    
    def _select_weighted_round_robin(self, agents: List[AgentInfo]) -> AgentInfo:
        """Weighted round-robin based on agent weights"""
        # Simple weighted selection based on weight
        total_weight = sum(agent.weight for agent in agents)
        if total_weight == 0:
            return agents[0]
        
        # For simplicity, select based on weight ratio
        # In production, implement proper weighted round-robin
        weights = [agent.weight / total_weight for agent in agents]
        import random
        return random.choices(agents, weights=weights)[0]
    
    def _select_resource_based(self, agents: List[AgentInfo]) -> AgentInfo:
        """Select based on resource utilization"""
        def resource_score(agent: AgentInfo) -> float:
            # Lower score is better
            load_factor = agent.metrics.get_load_percentage() / 100
            cpu_factor = agent.metrics.cpu_usage / 100
            memory_factor = agent.metrics.memory_usage / 100
            return load_factor + cpu_factor + memory_factor
        
        return min(agents, key=resource_score)
    
    async def get_registry_stats(self) -> Dict[str, Any]:
        """Get comprehensive registry statistics"""
        healthy_agents = sum(1 for agent in self.agents.values() if agent.is_healthy())
        
        capability_stats = {}
        for capability in AgentCapability:
            agents_with_cap = len(self.capability_index.get(capability, set()))
            capability_stats[capability.value] = agents_with_cap
        
        type_stats = {}
        for agent_type, agent_ids in self.type_index.items():
            type_stats[agent_type] = len(agent_ids)
        
        return {
            "registry_stats": self.stats.copy(),
            "agent_counts": {
                "total": len(self.agents),
                "healthy": healthy_agents,
                "unhealthy": len(self.agents) - healthy_agents
            },
            "capability_distribution": capability_stats,
            "type_distribution": type_stats,
            "load_balancing": {
                "round_robin_counters": self.round_robin_counters.copy()
            }
        }
    
    async def add_event_handler(self, event_type: str, handler: Callable):
        """Add event handler"""
        if event_type in self.event_handlers:
            self.event_handlers[event_type].append(handler)
    
    async def _trigger_event(self, event_type: str, agent_info: AgentInfo, extra_data: Dict[str, Any] = None):
        """Trigger event handlers"""
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(agent_info, extra_data)
                    else:
                        handler(agent_info, extra_data)
                except Exception as e:
                    logger.error(f"Error in event handler {event_type}: {e}")
    
    def _update_capability_index(self, agent_id: str, capabilities: List[AgentCapability]):
        """Update capability index"""
        for capability in capabilities:
            if capability not in self.capability_index:
                self.capability_index[capability] = set()
            self.capability_index[capability].add(agent_id)
    
    def _remove_from_capability_index(self, agent_id: str, capabilities: List[AgentCapability]):
        """Remove from capability index"""
        for capability in capabilities:
            if capability in self.capability_index:
                self.capability_index[capability].discard(agent_id)
                if not self.capability_index[capability]:
                    del self.capability_index[capability]
    
    def _update_type_index(self, agent_id: str, agent_type: str):
        """Update type index"""
        if agent_type not in self.type_index:
            self.type_index[agent_type] = set()
        self.type_index[agent_type].add(agent_id)
    
    def _remove_from_type_index(self, agent_id: str, agent_type: str):
        """Remove from type index"""
        if agent_type in self.type_index:
            self.type_index[agent_type].discard(agent_id)
            if not self.type_index[agent_type]:
                del self.type_index[agent_type]
    
    async def _load_agents_from_redis(self):
        """Load existing agents from Redis"""
        try:
            async with self.get_redis() as redis_client:
                agents_data = await redis_client.hgetall(self.agents_key)
                
                for agent_id, agent_json in agents_data.items():
                    try:
                        agent_info = AgentInfo.from_dict(json.loads(agent_json))
                        self.agents[agent_id] = agent_info
                        self._update_capability_index(agent_id, agent_info.capabilities)
                        self._update_type_index(agent_id, agent_info.agent_type)
                    except Exception as e:
                        logger.error(f"Failed to load agent {agent_id}: {e}")
                
                logger.info(f"Loaded {len(self.agents)} agents from Redis")
                
        except Exception as e:
            logger.error(f"Failed to load agents from Redis: {e}")
    
    async def _health_monitor(self):
        """Background health monitoring task"""
        while True:
            try:
                current_time = datetime.now()
                failed_agents = []
                
                for agent_id, agent_info in self.agents.items():
                    if not agent_info.is_healthy() and agent_info.status != AgentStatus.OFFLINE:
                        # Mark as offline
                        agent_info.status = AgentStatus.OFFLINE
                        failed_agents.append(agent_info)
                        
                        # Update in Redis
                        async with self.get_redis() as redis_client:
                            await redis_client.hset(
                                self.agents_key,
                                agent_id,
                                json.dumps(agent_info.to_dict())
                            )
                
                # Trigger failure events
                for agent_info in failed_agents:
                    await self._trigger_event("agent_failed", agent_info)
                    self.stats["failed_agents"] += 1
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in health monitor: {e}")
                await asyncio.sleep(60)
    
    async def _metrics_collector(self):
        """Background metrics collection task"""
        while True:
            try:
                # Collect and store registry metrics
                stats = await self.get_registry_stats()
                
                async with self.get_redis() as redis_client:
                    await redis_client.hset(
                        self.metrics_key,
                        "registry_stats",
                        json.dumps(stats)
                    )
                
                await asyncio.sleep(60)  # Collect every minute
                
            except Exception as e:
                logger.error(f"Error in metrics collector: {e}")
                await asyncio.sleep(60)

# Global agent registry instance
agent_registry = AgentRegistry()