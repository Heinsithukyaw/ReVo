"""
Agent Coordination Framework for Phase 2 Multi-Agent Communication Optimization
Orchestrates agent collaboration, workflow execution, and task distribution
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, List, Any, Optional, Callable, Union, Set
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import time

from .enhanced_message_queue import EnhancedMessageQueue, EnhancedMessage, MessagePriority, RoutingStrategy
from .agent_registry import AgentRegistry, AgentInfo, AgentCapability, AgentStatus, LoadBalancingStrategy

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

class WorkflowType(Enum):
    """Workflow execution types"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    PIPELINE = "pipeline"
    MAP_REDUCE = "map_reduce"

class CollaborationPattern(Enum):
    """Agent collaboration patterns"""
    MASTER_WORKER = "master_worker"
    PEER_TO_PEER = "peer_to_peer"
    HIERARCHICAL = "hierarchical"
    PIPELINE = "pipeline"
    CONSENSUS = "consensus"

@dataclass
class Task:
    """Individual task definition"""
    id: str
    type: str
    description: str
    parameters: Dict[str, Any]
    required_capability: Optional[AgentCapability] = None
    agent_type: Optional[str] = None
    priority: MessagePriority = MessagePriority.NORMAL
    timeout: int = 300  # seconds
    retry_count: int = 0
    max_retries: int = 3
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    dependencies: List[str] = None  # Task IDs this task depends on
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.dependencies is None:
            self.dependencies = []
        if not self.id:
            self.id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['priority'] = self.priority.value
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        if self.started_at:
            data['started_at'] = self.started_at.isoformat()
        if self.completed_at:
            data['completed_at'] = self.completed_at.isoformat()
        if self.required_capability:
            data['required_capability'] = self.required_capability.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create from dictionary"""
        data['priority'] = MessagePriority(data['priority'])
        data['status'] = TaskStatus(data['status'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('started_at'):
            data['started_at'] = datetime.fromisoformat(data['started_at'])
        if data.get('completed_at'):
            data['completed_at'] = datetime.fromisoformat(data['completed_at'])
        if data.get('required_capability'):
            data['required_capability'] = AgentCapability(data['required_capability'])
        return cls(**data)
    
    def is_ready(self, completed_tasks: Set[str]) -> bool:
        """Check if task is ready to execute (all dependencies completed)"""
        return all(dep_id in completed_tasks for dep_id in self.dependencies)
    
    def get_execution_time(self) -> Optional[float]:
        """Get task execution time in seconds"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

@dataclass
class Workflow:
    """Workflow definition and execution state"""
    id: str
    name: str
    description: str
    tasks: List[Task]
    workflow_type: WorkflowType
    collaboration_pattern: CollaborationPattern
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    timeout: int = 3600  # seconds
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}
        if not self.id:
            self.id = str(uuid.uuid4())
    
    def get_ready_tasks(self) -> List[Task]:
        """Get tasks that are ready to execute"""
        completed_task_ids = {
            task.id for task in self.tasks 
            if task.status == TaskStatus.COMPLETED
        }
        
        return [
            task for task in self.tasks
            if task.status == TaskStatus.PENDING and task.is_ready(completed_task_ids)
        ]
    
    def get_progress(self) -> float:
        """Get workflow completion progress (0.0 to 1.0)"""
        if not self.tasks:
            return 1.0
        
        completed = sum(1 for task in self.tasks if task.status == TaskStatus.COMPLETED)
        return completed / len(self.tasks)
    
    def is_completed(self) -> bool:
        """Check if workflow is completed"""
        return all(task.status == TaskStatus.COMPLETED for task in self.tasks)
    
    def has_failed(self) -> bool:
        """Check if workflow has failed"""
        return any(task.status == TaskStatus.FAILED for task in self.tasks)

class AgentCoordinator:
    """
    Central coordinator for multi-agent collaboration and workflow execution
    
    Features:
    - Task distribution and load balancing
    - Workflow orchestration
    - Agent collaboration patterns
    - Timeout and retry handling
    - Performance monitoring
    - Fault tolerance and recovery
    """
    
    def __init__(self, message_queue: EnhancedMessageQueue, agent_registry: AgentRegistry):
        self.message_queue = message_queue
        self.agent_registry = agent_registry
        
        # Active workflows and tasks
        self.workflows: Dict[str, Workflow] = {}
        self.tasks: Dict[str, Task] = {}
        self.task_assignments: Dict[str, str] = {}  # task_id -> agent_id
        
        # Coordination state
        self.active_collaborations: Dict[str, Dict[str, Any]] = {}
        self.agent_timeouts: Dict[str, datetime] = {}
        
        # Performance tracking
        self.coordination_metrics = {
            "workflows_executed": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "average_task_time": 0.0,
            "agent_utilization": {},
            "collaboration_success_rate": 0.0
        }
        
        # Event handlers
        self.workflow_handlers: Dict[str, List[Callable]] = {
            "workflow_started": [],
            "workflow_completed": [],
            "workflow_failed": [],
            "task_assigned": [],
            "task_completed": [],
            "task_failed": [],
            "collaboration_started": [],
            "collaboration_completed": []
        }
    
    async def initialize(self):
        """Initialize coordinator"""
        # Start background tasks
        asyncio.create_task(self._workflow_monitor())
        asyncio.create_task(self._timeout_monitor())
        asyncio.create_task(self._metrics_collector())
        
        logger.info("Agent coordinator initialized")
    
    async def execute_workflow(self, workflow: Workflow) -> str:
        """Execute a workflow"""
        try:
            workflow.status = TaskStatus.IN_PROGRESS
            workflow.started_at = datetime.now()
            
            # Store workflow
            self.workflows[workflow.id] = workflow
            
            # Trigger workflow started event
            await self._trigger_event("workflow_started", workflow)
            
            # Execute based on workflow type
            if workflow.workflow_type == WorkflowType.SEQUENTIAL:
                await self._execute_sequential_workflow(workflow)
            elif workflow.workflow_type == WorkflowType.PARALLEL:
                await self._execute_parallel_workflow(workflow)
            elif workflow.workflow_type == WorkflowType.CONDITIONAL:
                await self._execute_conditional_workflow(workflow)
            elif workflow.workflow_type == WorkflowType.PIPELINE:
                await self._execute_pipeline_workflow(workflow)
            elif workflow.workflow_type == WorkflowType.MAP_REDUCE:
                await self._execute_map_reduce_workflow(workflow)
            
            self.coordination_metrics["workflows_executed"] += 1
            logger.info(f"Workflow {workflow.id} execution started")
            
            return workflow.id
            
        except Exception as e:
            workflow.status = TaskStatus.FAILED
            logger.error(f"Failed to execute workflow {workflow.id}: {e}")
            await self._trigger_event("workflow_failed", workflow, {"error": str(e)})
            raise
    
    async def assign_task(
        self, 
        task: Task, 
        strategy: LoadBalancingStrategy = LoadBalancingStrategy.LEAST_CONNECTIONS
    ) -> Optional[str]:
        """Assign task to best available agent"""
        try:
            # Find suitable agent
            agent = await self.agent_registry.select_agent(
                capability=task.required_capability,
                agent_type=task.agent_type,
                strategy=strategy
            )
            
            if not agent:
                logger.warning(f"No available agent for task {task.id}")
                return None
            
            # Assign task
            task.assigned_agent = agent.agent_id
            task.status = TaskStatus.ASSIGNED
            task.started_at = datetime.now()
            
            # Store task
            self.tasks[task.id] = task
            self.task_assignments[task.id] = agent.agent_id
            
            # Send task to agent
            message = EnhancedMessage(
                id=str(uuid.uuid4()),
                type="task_assignment",
                sender="coordinator",
                recipient=agent.agent_id,
                content={
                    "task": task.to_dict(),
                    "timeout": task.timeout
                },
                priority=task.priority,
                correlation_id=task.id,
                reply_to="coordinator"
            )
            
            success = await self.message_queue.send_message(message)
            if success:
                # Set timeout
                timeout_time = datetime.now() + timedelta(seconds=task.timeout)
                self.agent_timeouts[task.id] = timeout_time
                
                # Update agent load
                agent.metrics.current_load += 1
                await self.agent_registry.update_agent_status(
                    agent.agent_id, 
                    AgentStatus.BUSY if agent.metrics.current_load > 0 else AgentStatus.IDLE,
                    agent.metrics
                )
                
                await self._trigger_event("task_assigned", task, {"agent": agent})
                logger.info(f"Task {task.id} assigned to agent {agent.agent_id}")
                
                return agent.agent_id
            else:
                task.status = TaskStatus.FAILED
                task.error = "Failed to send task to agent"
                return None
                
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            logger.error(f"Failed to assign task {task.id}: {e}")
            return None
    
    async def handle_task_completion(self, task_id: str, result: Any, success: bool = True):
        """Handle task completion from agent"""
        try:
            if task_id not in self.tasks:
                logger.warning(f"Unknown task completion: {task_id}")
                return
            
            task = self.tasks[task_id]
            agent_id = self.task_assignments.get(task_id)
            
            if success:
                task.status = TaskStatus.COMPLETED
                task.result = result
                task.completed_at = datetime.now()
                
                self.coordination_metrics["tasks_completed"] += 1
                
                # Update average task time
                execution_time = task.get_execution_time()
                if execution_time:
                    current_avg = self.coordination_metrics["average_task_time"]
                    total_tasks = self.coordination_metrics["tasks_completed"]
                    self.coordination_metrics["average_task_time"] = (
                        (current_avg * (total_tasks - 1) + execution_time) / total_tasks
                    )
                
                await self._trigger_event("task_completed", task, {"result": result})
                logger.info(f"Task {task_id} completed successfully")
                
            else:
                task.status = TaskStatus.FAILED
                task.error = str(result) if result else "Task failed"
                task.completed_at = datetime.now()
                
                self.coordination_metrics["tasks_failed"] += 1
                
                # Handle retry logic
                if task.retry_count < task.max_retries:
                    task.retry_count += 1
                    task.status = TaskStatus.PENDING
                    task.assigned_agent = None
                    task.started_at = None
                    task.completed_at = None
                    
                    # Re-assign task
                    await self.assign_task(task)
                    logger.info(f"Task {task_id} retrying ({task.retry_count}/{task.max_retries})")
                else:
                    await self._trigger_event("task_failed", task, {"error": task.error})
                    logger.error(f"Task {task_id} failed permanently: {task.error}")
            
            # Update agent load
            if agent_id:
                agent = await self.agent_registry.get_agent(agent_id)
                if agent:
                    agent.metrics.current_load = max(0, agent.metrics.current_load - 1)
                    await self.agent_registry.update_agent_status(
                        agent_id,
                        AgentStatus.IDLE if agent.metrics.current_load == 0 else AgentStatus.BUSY,
                        agent.metrics
                    )
            
            # Remove timeout
            if task_id in self.agent_timeouts:
                del self.agent_timeouts[task_id]
            
            # Check if workflow is completed
            await self._check_workflow_completion(task)
            
        except Exception as e:
            logger.error(f"Error handling task completion {task_id}: {e}")
    
    async def start_collaboration(
        self, 
        collaboration_id: str,
        agents: List[str],
        pattern: CollaborationPattern,
        context: Dict[str, Any]
    ) -> bool:
        """Start agent collaboration"""
        try:
            collaboration = {
                "id": collaboration_id,
                "agents": agents,
                "pattern": pattern,
                "context": context,
                "started_at": datetime.now(),
                "status": "active"
            }
            
            self.active_collaborations[collaboration_id] = collaboration
            
            # Notify agents about collaboration
            for agent_id in agents:
                message = EnhancedMessage(
                    id=str(uuid.uuid4()),
                    type="collaboration_invite",
                    sender="coordinator",
                    recipient=agent_id,
                    content={
                        "collaboration_id": collaboration_id,
                        "pattern": pattern.value,
                        "participants": agents,
                        "context": context
                    },
                    priority=MessagePriority.HIGH
                )
                
                await self.message_queue.send_message(message)
            
            await self._trigger_event("collaboration_started", collaboration)
            logger.info(f"Collaboration {collaboration_id} started with {len(agents)} agents")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start collaboration {collaboration_id}: {e}")
            return False
    
    async def end_collaboration(self, collaboration_id: str, result: Any = None):
        """End agent collaboration"""
        try:
            if collaboration_id not in self.active_collaborations:
                return
            
            collaboration = self.active_collaborations[collaboration_id]
            collaboration["status"] = "completed"
            collaboration["completed_at"] = datetime.now()
            collaboration["result"] = result
            
            # Notify agents
            for agent_id in collaboration["agents"]:
                message = EnhancedMessage(
                    id=str(uuid.uuid4()),
                    type="collaboration_end",
                    sender="coordinator",
                    recipient=agent_id,
                    content={
                        "collaboration_id": collaboration_id,
                        "result": result
                    },
                    priority=MessagePriority.NORMAL
                )
                
                await self.message_queue.send_message(message)
            
            await self._trigger_event("collaboration_completed", collaboration)
            del self.active_collaborations[collaboration_id]
            
            logger.info(f"Collaboration {collaboration_id} completed")
            
        except Exception as e:
            logger.error(f"Failed to end collaboration {collaboration_id}: {e}")
    
    async def get_coordination_stats(self) -> Dict[str, Any]:
        """Get coordination statistics"""
        active_workflows = len([w for w in self.workflows.values() if w.status == TaskStatus.IN_PROGRESS])
        active_tasks = len([t for t in self.tasks.values() if t.status in [TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS]])
        
        return {
            "coordination_metrics": self.coordination_metrics.copy(),
            "active_workflows": active_workflows,
            "active_tasks": active_tasks,
            "active_collaborations": len(self.active_collaborations),
            "total_workflows": len(self.workflows),
            "total_tasks": len(self.tasks),
            "workflow_success_rate": self._calculate_workflow_success_rate(),
            "task_success_rate": self._calculate_task_success_rate()
        }
    
    def _calculate_workflow_success_rate(self) -> float:
        """Calculate workflow success rate"""
        completed_workflows = [w for w in self.workflows.values() if w.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]]
        if not completed_workflows:
            return 1.0
        
        successful = sum(1 for w in completed_workflows if w.status == TaskStatus.COMPLETED)
        return successful / len(completed_workflows)
    
    def _calculate_task_success_rate(self) -> float:
        """Calculate task success rate"""
        completed_tasks = [t for t in self.tasks.values() if t.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]]
        if not completed_tasks:
            return 1.0
        
        successful = sum(1 for t in completed_tasks if t.status == TaskStatus.COMPLETED)
        return successful / len(completed_tasks)
    
    async def _execute_sequential_workflow(self, workflow: Workflow):
        """Execute workflow tasks sequentially"""
        for task in workflow.tasks:
            if workflow.status == TaskStatus.CANCELLED:
                break
            
            await self.assign_task(task)
            
            # Wait for task completion
            while task.status in [TaskStatus.PENDING, TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS]:
                await asyncio.sleep(1)
            
            if task.status == TaskStatus.FAILED:
                workflow.status = TaskStatus.FAILED
                break
    
    async def _execute_parallel_workflow(self, workflow: Workflow):
        """Execute workflow tasks in parallel"""
        # Assign all tasks
        assignment_tasks = []
        for task in workflow.tasks:
            assignment_tasks.append(self.assign_task(task))
        
        await asyncio.gather(*assignment_tasks)
    
    async def _execute_conditional_workflow(self, workflow: Workflow):
        """Execute workflow with conditional logic"""
        # This would implement conditional execution based on task results
        # For now, execute sequentially with condition checking
        await self._execute_sequential_workflow(workflow)
    
    async def _execute_pipeline_workflow(self, workflow: Workflow):
        """Execute workflow as a pipeline"""
        # Execute tasks based on dependencies
        completed_tasks = set()
        
        while len(completed_tasks) < len(workflow.tasks):
            ready_tasks = [
                task for task in workflow.tasks
                if task.status == TaskStatus.PENDING and task.is_ready(completed_tasks)
            ]
            
            if not ready_tasks:
                # Check for deadlock or completion
                if all(task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED] for task in workflow.tasks):
                    break
                await asyncio.sleep(1)
                continue
            
            # Assign ready tasks
            for task in ready_tasks:
                await self.assign_task(task)
            
            # Wait for at least one task to complete
            while not any(task.id in completed_tasks for task in ready_tasks):
                for task in ready_tasks:
                    if task.status == TaskStatus.COMPLETED:
                        completed_tasks.add(task.id)
                    elif task.status == TaskStatus.FAILED:
                        workflow.status = TaskStatus.FAILED
                        return
                
                await asyncio.sleep(1)
    
    async def _execute_map_reduce_workflow(self, workflow: Workflow):
        """Execute workflow using map-reduce pattern"""
        # Separate map and reduce tasks
        map_tasks = [task for task in workflow.tasks if task.type.startswith("map_")]
        reduce_tasks = [task for task in workflow.tasks if task.type.startswith("reduce_")]
        
        # Execute map tasks in parallel
        for task in map_tasks:
            await self.assign_task(task)
        
        # Wait for all map tasks to complete
        while any(task.status in [TaskStatus.PENDING, TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS] for task in map_tasks):
            await asyncio.sleep(1)
        
        # Execute reduce tasks
        for task in reduce_tasks:
            await self.assign_task(task)
    
    async def _check_workflow_completion(self, completed_task: Task):
        """Check if any workflows are completed"""
        for workflow in self.workflows.values():
            if workflow.status != TaskStatus.IN_PROGRESS:
                continue
            
            if completed_task.id not in [task.id for task in workflow.tasks]:
                continue
            
            if workflow.is_completed():
                workflow.status = TaskStatus.COMPLETED
                workflow.completed_at = datetime.now()
                await self._trigger_event("workflow_completed", workflow)
                logger.info(f"Workflow {workflow.id} completed")
            elif workflow.has_failed():
                workflow.status = TaskStatus.FAILED
                workflow.completed_at = datetime.now()
                await self._trigger_event("workflow_failed", workflow)
                logger.error(f"Workflow {workflow.id} failed")
    
    async def _workflow_monitor(self):
        """Monitor workflow execution"""
        while True:
            try:
                current_time = datetime.now()
                
                for workflow in self.workflows.values():
                    if workflow.status != TaskStatus.IN_PROGRESS:
                        continue
                    
                    # Check workflow timeout
                    if workflow.started_at:
                        elapsed = (current_time - workflow.started_at).total_seconds()
                        if elapsed > workflow.timeout:
                            workflow.status = TaskStatus.TIMEOUT
                            workflow.completed_at = current_time
                            await self._trigger_event("workflow_failed", workflow, {"reason": "timeout"})
                            logger.warning(f"Workflow {workflow.id} timed out")
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in workflow monitor: {e}")
                await asyncio.sleep(60)
    
    async def _timeout_monitor(self):
        """Monitor task timeouts"""
        while True:
            try:
                current_time = datetime.now()
                timed_out_tasks = []
                
                for task_id, timeout_time in self.agent_timeouts.items():
                    if current_time > timeout_time:
                        timed_out_tasks.append(task_id)
                
                for task_id in timed_out_tasks:
                    if task_id in self.tasks:
                        task = self.tasks[task_id]
                        task.status = TaskStatus.TIMEOUT
                        task.completed_at = current_time
                        task.error = "Task timeout"
                        
                        await self.handle_task_completion(task_id, None, False)
                        logger.warning(f"Task {task_id} timed out")
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in timeout monitor: {e}")
                await asyncio.sleep(60)
    
    async def _metrics_collector(self):
        """Collect coordination metrics"""
        while True:
            try:
                # Update agent utilization metrics
                agents = await self.agent_registry.get_agents_by_type("")  # Get all agents
                for agent in agents:
                    utilization = agent.metrics.get_load_percentage()
                    self.coordination_metrics["agent_utilization"][agent.agent_id] = utilization
                
                # Update collaboration success rate
                if self.active_collaborations:
                    # This would be calculated based on collaboration outcomes
                    pass
                
                await asyncio.sleep(60)  # Collect every minute
                
            except Exception as e:
                logger.error(f"Error in metrics collector: {e}")
                await asyncio.sleep(60)
    
    async def add_event_handler(self, event_type: str, handler: Callable):
        """Add event handler"""
        if event_type in self.workflow_handlers:
            self.workflow_handlers[event_type].append(handler)
    
    async def _trigger_event(self, event_type: str, data: Any, extra_data: Dict[str, Any] = None):
        """Trigger event handlers"""
        if event_type in self.workflow_handlers:
            for handler in self.workflow_handlers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(data, extra_data)
                    else:
                        handler(data, extra_data)
                except Exception as e:
                    logger.error(f"Error in event handler {event_type}: {e}")

# Global coordinator instance
agent_coordinator = None

def get_coordinator(message_queue: EnhancedMessageQueue, agent_registry: AgentRegistry) -> AgentCoordinator:
    """Get or create global coordinator instance"""
    global agent_coordinator
    if agent_coordinator is None:
        agent_coordinator = AgentCoordinator(message_queue, agent_registry)
    return agent_coordinator