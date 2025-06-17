"""
Phase 2 Integration Layer - Multi-Agent Communication Optimization
Integrates enhanced message queue, agent registry, coordination, and memory systems
"""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import uuid

from .enhanced_message_queue import EnhancedMessageQueue, EnhancedMessage, MessagePriority, RoutingStrategy
from .agent_registry import AgentRegistry, AgentInfo, AgentCapability, AgentStatus, LoadBalancingStrategy
from .agent_coordinator import AgentCoordinator, Task, Workflow, WorkflowType, CollaborationPattern
from ..memory.enhanced_memory_coordinator import EnhancedMemoryCoordinator, LockType

logger = logging.getLogger(__name__)

class Phase2System:
    """
    Integrated Phase 2 Multi-Agent Communication Optimization System
    
    Provides unified interface for:
    - Enhanced message queuing with persistence and routing
    - Agent registry with load balancing and health monitoring
    - Agent coordination with workflow orchestration
    - Memory coordination with conflict resolution and synchronization
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379", namespace: str = "revoagent"):
        self.redis_url = redis_url
        self.namespace = namespace
        
        # Core components
        self.message_queue = EnhancedMessageQueue(redis_url, namespace)
        self.agent_registry = AgentRegistry(redis_url, namespace)
        self.memory_coordinator = EnhancedMemoryCoordinator(redis_url, namespace)
        self.agent_coordinator = None  # Will be initialized after message_queue and agent_registry
        
        # System state
        self.initialized = False
        self.running = False
        
        # Event handlers
        self.system_handlers: Dict[str, List[Callable]] = {
            "system_started": [],
            "system_stopped": [],
            "agent_communication": [],
            "workflow_execution": [],
            "memory_operation": [],
            "system_error": []
        }
        
        # Performance metrics
        self.system_metrics = {
            "uptime": 0.0,
            "total_messages": 0,
            "total_workflows": 0,
            "total_memory_operations": 0,
            "system_errors": 0
        }
        
        self.start_time: Optional[datetime] = None
    
    async def initialize(self) -> bool:
        """Initialize all Phase 2 components"""
        try:
            logger.info("🚀 Initializing Phase 2 Multi-Agent Communication System...")
            
            # Initialize core components
            await self.message_queue.initialize()
            logger.info("✅ Message queue initialized")
            
            await self.agent_registry.initialize()
            logger.info("✅ Agent registry initialized")
            
            await self.memory_coordinator.initialize()
            logger.info("✅ Memory coordinator initialized")
            
            # Initialize agent coordinator with dependencies
            from .agent_coordinator import get_coordinator
            self.agent_coordinator = get_coordinator(self.message_queue, self.agent_registry)
            await self.agent_coordinator.initialize()
            logger.info("✅ Agent coordinator initialized")
            
            # Setup inter-component communication
            await self._setup_component_integration()
            
            # Start system monitoring
            asyncio.create_task(self._system_monitor())
            
            self.initialized = True
            self.start_time = datetime.now()
            
            await self._trigger_event("system_started", {"timestamp": self.start_time})
            
            logger.info("🎉 Phase 2 system initialization complete!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Phase 2 system: {e}")
            await self._trigger_event("system_error", {"error": str(e), "phase": "initialization"})
            return False
    
    async def start(self) -> bool:
        """Start the Phase 2 system"""
        if not self.initialized:
            success = await self.initialize()
            if not success:
                return False
        
        try:
            self.running = True
            logger.info("🟢 Phase 2 system started and running")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start Phase 2 system: {e}")
            return False
    
    async def stop(self) -> bool:
        """Stop the Phase 2 system gracefully"""
        try:
            logger.info("🛑 Stopping Phase 2 system...")
            
            self.running = False
            
            # Close components
            await self.message_queue.close()
            await self.agent_registry.close()
            await self.memory_coordinator.close()
            
            await self._trigger_event("system_stopped", {"timestamp": datetime.now()})
            
            logger.info("✅ Phase 2 system stopped gracefully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error stopping Phase 2 system: {e}")
            return False
    
    # Agent Management Interface
    async def register_agent(
        self, 
        agent_id: str,
        agent_type: str,
        capabilities: List[AgentCapability],
        host: str = "localhost",
        port: int = 8000,
        endpoint: str = "/",
        config: Dict[str, Any] = None
    ) -> bool:
        """Register a new agent in the system"""
        try:
            agent_info = AgentInfo(
                agent_id=agent_id,
                agent_type=agent_type,
                capabilities=capabilities,
                status=AgentStatus.STARTING,
                version="1.0.0",
                host=host,
                port=port,
                endpoint=endpoint,
                config=config or {}
            )
            
            # Register with agent registry
            success = await self.agent_registry.register_agent(agent_info)
            if success:
                # Register with message queue
                self.message_queue.register_agent(agent_id)
                
                # Update status to idle
                await self.agent_registry.update_agent_status(agent_id, AgentStatus.IDLE)
                
                logger.info(f"✅ Agent registered: {agent_id} ({agent_type})")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to register agent {agent_id}: {e}")
            return False
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent from the system"""
        try:
            # Unregister from components
            await self.agent_registry.unregister_agent(agent_id)
            self.message_queue.unregister_agent(agent_id)
            
            logger.info(f"✅ Agent unregistered: {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to unregister agent {agent_id}: {e}")
            return False
    
    async def send_message_to_agent(
        self, 
        sender: str,
        recipient: str,
        message_type: str,
        content: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        routing_strategy: RoutingStrategy = RoutingStrategy.DIRECT
    ) -> bool:
        """Send message to specific agent"""
        try:
            message = EnhancedMessage(
                id=str(uuid.uuid4()),
                type=message_type,
                sender=sender,
                recipient=recipient,
                content=content,
                priority=priority,
                routing_strategy=routing_strategy
            )
            
            success = await self.message_queue.send_message(message)
            if success:
                self.system_metrics["total_messages"] += 1
                await self._trigger_event("agent_communication", {
                    "sender": sender,
                    "recipient": recipient,
                    "type": message_type
                })
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Failed to send message from {sender} to {recipient}: {e}")
            return False
    
    async def broadcast_message(
        self,
        sender: str,
        agent_type: str,
        message_type: str,
        content: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> int:
        """Broadcast message to all agents of specific type"""
        try:
            message = EnhancedMessage(
                id=str(uuid.uuid4()),
                type=message_type,
                sender=sender,
                recipient=agent_type,
                content=content,
                priority=priority,
                routing_strategy=RoutingStrategy.BROADCAST
            )
            
            success = await self.message_queue.send_message(message)
            if success:
                agents = await self.agent_registry.get_agents_by_type(agent_type)
                self.system_metrics["total_messages"] += len(agents)
                return len(agents)
            
            return 0
            
        except Exception as e:
            logger.error(f"❌ Failed to broadcast message: {e}")
            return 0
    
    # Workflow Management Interface
    async def execute_workflow(
        self,
        workflow_name: str,
        tasks: List[Dict[str, Any]],
        workflow_type: WorkflowType = WorkflowType.SEQUENTIAL,
        collaboration_pattern: CollaborationPattern = CollaborationPattern.MASTER_WORKER
    ) -> str:
        """Execute a multi-agent workflow"""
        try:
            # Convert task dictionaries to Task objects
            task_objects = []
            for task_data in tasks:
                task = Task(
                    id=task_data.get("id", str(uuid.uuid4())),
                    type=task_data["type"],
                    description=task_data["description"],
                    parameters=task_data.get("parameters", {}),
                    required_capability=AgentCapability(task_data["capability"]) if "capability" in task_data else None,
                    agent_type=task_data.get("agent_type"),
                    priority=MessagePriority(task_data.get("priority", MessagePriority.NORMAL.value)),
                    timeout=task_data.get("timeout", 300),
                    dependencies=task_data.get("dependencies", [])
                )
                task_objects.append(task)
            
            # Create workflow
            workflow = Workflow(
                id=str(uuid.uuid4()),
                name=workflow_name,
                description=f"Multi-agent workflow: {workflow_name}",
                tasks=task_objects,
                workflow_type=workflow_type,
                collaboration_pattern=collaboration_pattern
            )
            
            # Execute workflow
            workflow_id = await self.agent_coordinator.execute_workflow(workflow)
            
            self.system_metrics["total_workflows"] += 1
            await self._trigger_event("workflow_execution", {
                "workflow_id": workflow_id,
                "name": workflow_name,
                "task_count": len(tasks)
            })
            
            logger.info(f"✅ Workflow started: {workflow_name} ({workflow_id})")
            return workflow_id
            
        except Exception as e:
            logger.error(f"❌ Failed to execute workflow {workflow_name}: {e}")
            raise
    
    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow execution status"""
        try:
            if workflow_id in self.agent_coordinator.workflows:
                workflow = self.agent_coordinator.workflows[workflow_id]
                return {
                    "id": workflow.id,
                    "name": workflow.name,
                    "status": workflow.status.value,
                    "progress": workflow.get_progress(),
                    "task_count": len(workflow.tasks),
                    "completed_tasks": sum(1 for task in workflow.tasks if task.status.value == "completed"),
                    "failed_tasks": sum(1 for task in workflow.tasks if task.status.value == "failed"),
                    "created_at": workflow.created_at.isoformat(),
                    "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
                    "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None
                }
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get workflow status {workflow_id}: {e}")
            return None
    
    # Memory Management Interface
    async def read_shared_memory(self, key: str, agent_id: str) -> Optional[Any]:
        """Read from shared memory"""
        try:
            entry = await self.memory_coordinator.read_memory(key, agent_id)
            if entry:
                self.system_metrics["total_memory_operations"] += 1
                await self._trigger_event("memory_operation", {
                    "operation": "read",
                    "key": key,
                    "agent_id": agent_id
                })
                return entry.value
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to read memory {key}: {e}")
            return None
    
    async def write_shared_memory(
        self, 
        key: str, 
        value: Any, 
        agent_id: str,
        acquire_lock: bool = True
    ) -> bool:
        """Write to shared memory with optional locking"""
        try:
            lock_id = None
            
            if acquire_lock:
                lock_id = await self.memory_coordinator.acquire_lock(
                    key, agent_id, LockType.EXCLUSIVE
                )
                if not lock_id:
                    logger.warning(f"Failed to acquire lock for memory write: {key}")
                    return False
            
            try:
                success = await self.memory_coordinator.write_memory(
                    key, value, agent_id, lock_id
                )
                
                if success:
                    self.system_metrics["total_memory_operations"] += 1
                    await self._trigger_event("memory_operation", {
                        "operation": "write",
                        "key": key,
                        "agent_id": agent_id
                    })
                
                return success
                
            finally:
                if lock_id:
                    await self.memory_coordinator.release_lock(lock_id)
            
        except Exception as e:
            logger.error(f"❌ Failed to write memory {key}: {e}")
            return False
    
    async def acquire_memory_lock(
        self, 
        key: str, 
        agent_id: str, 
        lock_type: LockType = LockType.EXCLUSIVE,
        timeout: int = 300
    ) -> Optional[str]:
        """Acquire memory lock"""
        try:
            lock_id = await self.memory_coordinator.acquire_lock(
                key, agent_id, lock_type, timeout
            )
            
            if lock_id:
                await self._trigger_event("memory_operation", {
                    "operation": "lock_acquired",
                    "key": key,
                    "agent_id": agent_id,
                    "lock_type": lock_type.value
                })
            
            return lock_id
            
        except Exception as e:
            logger.error(f"❌ Failed to acquire memory lock {key}: {e}")
            return None
    
    async def release_memory_lock(self, lock_id: str) -> bool:
        """Release memory lock"""
        try:
            success = await self.memory_coordinator.release_lock(lock_id)
            
            if success:
                await self._trigger_event("memory_operation", {
                    "operation": "lock_released",
                    "lock_id": lock_id
                })
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Failed to release memory lock {lock_id}: {e}")
            return False
    
    # System Monitoring Interface
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        try:
            # Update uptime
            if self.start_time:
                self.system_metrics["uptime"] = (datetime.now() - self.start_time).total_seconds()
            
            # Get component statistics
            message_stats = await self.message_queue.get_queue_stats()
            registry_stats = await self.agent_registry.get_registry_stats()
            coordination_stats = await self.agent_coordinator.get_coordination_stats()
            memory_stats = await self.memory_coordinator.get_memory_stats()
            
            return {
                "system": {
                    "status": "running" if self.running else "stopped",
                    "initialized": self.initialized,
                    "uptime": self.system_metrics["uptime"],
                    "start_time": self.start_time.isoformat() if self.start_time else None
                },
                "metrics": self.system_metrics.copy(),
                "components": {
                    "message_queue": message_stats,
                    "agent_registry": registry_stats,
                    "coordination": coordination_stats,
                    "memory": memory_stats
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get system status: {e}")
            return {"error": str(e)}
    
    async def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get specific agent status"""
        try:
            agent = await self.agent_registry.get_agent(agent_id)
            if agent:
                return {
                    "agent_id": agent.agent_id,
                    "agent_type": agent.agent_type,
                    "status": agent.status.value,
                    "capabilities": [cap.value for cap in agent.capabilities],
                    "metrics": {
                        "current_load": agent.metrics.current_load,
                        "total_tasks": agent.metrics.total_tasks,
                        "success_rate": agent.metrics.get_success_rate(),
                        "average_response_time": agent.metrics.average_response_time,
                        "uptime": agent.metrics.uptime
                    },
                    "last_heartbeat": agent.last_heartbeat.isoformat(),
                    "is_healthy": agent.is_healthy()
                }
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get agent status {agent_id}: {e}")
            return None
    
    # Event Handling
    async def add_event_handler(self, event_type: str, handler: Callable):
        """Add system event handler"""
        if event_type in self.system_handlers:
            self.system_handlers[event_type].append(handler)
    
    async def _trigger_event(self, event_type: str, data: Dict[str, Any]):
        """Trigger system event handlers"""
        if event_type in self.system_handlers:
            for handler in self.system_handlers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(data)
                    else:
                        handler(data)
                except Exception as e:
                    logger.error(f"Error in event handler {event_type}: {e}")
                    self.system_metrics["system_errors"] += 1
    
    async def _setup_component_integration(self):
        """Setup integration between components"""
        # Setup message handling for coordination
        async def handle_task_completion(message):
            if message.type == "task_completion":
                task_id = message.correlation_id
                result = message.content.get("result")
                success = message.content.get("success", True)
                
                await self.agent_coordinator.handle_task_completion(task_id, result, success)
        
        # Register message handlers
        self.message_queue.register_message_handler("coordinator", handle_task_completion)
        
        # Setup agent registry event handlers
        async def on_agent_failed(agent_info, extra_data):
            logger.warning(f"Agent failed: {agent_info.agent_id}")
            # Could implement automatic failover here
        
        await self.agent_registry.add_event_handler("agent_failed", on_agent_failed)
    
    async def _system_monitor(self):
        """Background system monitoring"""
        while True:
            try:
                if not self.running:
                    break
                
                # Monitor system health
                status = await self.get_system_status()
                
                # Check for issues and trigger alerts if needed
                # This could be expanded with more sophisticated monitoring
                
                await asyncio.sleep(60)  # Monitor every minute
                
            except Exception as e:
                logger.error(f"Error in system monitor: {e}")
                self.system_metrics["system_errors"] += 1
                await asyncio.sleep(60)

# Global Phase 2 system instance
phase2_system = Phase2System()

async def get_phase2_system() -> Phase2System:
    """Get the global Phase 2 system instance"""
    if not phase2_system.initialized:
        await phase2_system.initialize()
    return phase2_system