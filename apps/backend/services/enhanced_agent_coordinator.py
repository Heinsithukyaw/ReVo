"""
Enhanced Agent Coordinator Service
Part of reVoAgent Next Phase Implementation
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class AgentStatus(Enum):
    IDLE = "idle"
    PROCESSING = "processing"
    ERROR = "error"
    OFFLINE = "offline"

class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class AgentMetrics:
    tasks_completed: int = 0
    average_response_time: float = 0.0
    success_rate: float = 100.0
    last_activity: Optional[datetime] = None
    error_count: int = 0
    total_execution_time: float = 0.0

@dataclass
class AgentState:
    id: str
    name: str
    status: AgentStatus
    current_task: Optional[str] = None
    metrics: AgentMetrics = None
    capabilities: List[str] = None
    load_percentage: float = 0.0
    max_concurrent_tasks: int = 1
    current_task_count: int = 0
    last_heartbeat: Optional[datetime] = None

    def __post_init__(self):
        if self.metrics is None:
            self.metrics = AgentMetrics()

@dataclass
class AgentTask:
    id: str
    agent_id: str
    task_type: str
    description: str
    parameters: Dict[str, Any]
    priority: TaskPriority
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "queued"  # queued, running, completed, failed
    result: Optional[Any] = None
    error: Optional[str] = None

class EnhancedAgentCoordinator:
    def __init__(self, websocket_manager=None):
        self.agents: Dict[str, AgentState] = {}
        self.tasks: Dict[str, AgentTask] = {}
        self.task_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.websocket_manager = websocket_manager
        self.performance_thresholds = {
            'max_response_time': 5000,  # ms
            'min_success_rate': 85,     # %
            'max_error_rate': 10,       # %
            'max_load_percentage': 80   # %
        }
        self.running = False
        self.task_processor_task = None

    async def start(self):
        """Start the agent coordinator"""
        self.running = True
        self.task_processor_task = asyncio.create_task(self._process_task_queue())
        logger.info("Enhanced Agent Coordinator started")

    async def stop(self):
        """Stop the agent coordinator"""
        self.running = False
        if self.task_processor_task:
            self.task_processor_task.cancel()
            try:
                await self.task_processor_task
            except asyncio.CancelledError:
                pass
        logger.info("Enhanced Agent Coordinator stopped")

    async def register_agent(self, agent_id: str, agent_name: str, 
                           capabilities: List[str], max_concurrent_tasks: int = 1):
        """Register a new agent with the coordinator"""
        self.agents[agent_id] = AgentState(
            id=agent_id,
            name=agent_name,
            status=AgentStatus.IDLE,
            capabilities=capabilities,
            max_concurrent_tasks=max_concurrent_tasks,
            last_heartbeat=datetime.now()
        )
        
        logger.info(f"Agent registered: {agent_id} ({agent_name}) with capabilities: {capabilities}")
        await self._broadcast_agent_update(agent_id)

    async def unregister_agent(self, agent_id: str):
        """Unregister an agent"""
        if agent_id in self.agents:
            # Cancel any running tasks for this agent
            agent_tasks = [task for task in self.tasks.values() 
                          if task.agent_id == agent_id and task.status in ["queued", "running"]]
            
            for task in agent_tasks:
                task.status = "failed"
                task.error = "Agent unregistered"
                task.completed_at = datetime.now()
            
            del self.agents[agent_id]
            logger.info(f"Agent unregistered: {agent_id}")
            
            # Broadcast agent removal
            if self.websocket_manager:
                await self.websocket_manager.broadcast_to_channel(
                    'agent_removed',
                    {
                        'channel': 'agent_removed',
                        'payload': {'agent_id': agent_id}
                    }
                )

    async def update_agent_status(self, agent_id: str, status: AgentStatus, 
                                current_task: Optional[str] = None):
        """Update agent status and broadcast to clients"""
        if agent_id not in self.agents:
            logger.warning(f"Attempted to update status for unknown agent: {agent_id}")
            return False
            
        agent = self.agents[agent_id]
        agent.status = status
        agent.current_task = current_task
        agent.last_heartbeat = datetime.now()
        
        # Update load percentage based on current tasks
        agent.load_percentage = (agent.current_task_count / agent.max_concurrent_tasks) * 100
        
        await self._broadcast_agent_update(agent_id)
        return True

    async def agent_heartbeat(self, agent_id: str, metrics: Optional[Dict[str, Any]] = None):
        """Process agent heartbeat with optional metrics"""
        if agent_id not in self.agents:
            return False
            
        agent = self.agents[agent_id]
        agent.last_heartbeat = datetime.now()
        
        # Update metrics if provided
        if metrics:
            if 'tasks_completed' in metrics:
                agent.metrics.tasks_completed = metrics['tasks_completed']
            if 'average_response_time' in metrics:
                agent.metrics.average_response_time = metrics['average_response_time']
            if 'success_rate' in metrics:
                agent.metrics.success_rate = metrics['success_rate']
            if 'error_count' in metrics:
                agent.metrics.error_count = metrics['error_count']
        
        # Check if agent should be marked as offline
        if agent.status == AgentStatus.OFFLINE:
            agent.status = AgentStatus.IDLE
            
        await self._broadcast_agent_update(agent_id)
        return True

    async def submit_task(self, task_type: str, description: str, 
                         parameters: Dict[str, Any] = None,
                         priority: TaskPriority = TaskPriority.MEDIUM,
                         required_capabilities: List[str] = None,
                         preferred_agent: Optional[str] = None) -> str:
        """Submit a task to the coordination system"""
        
        if parameters is None:
            parameters = {}
        if required_capabilities is None:
            required_capabilities = []
            
        task_id = str(uuid.uuid4())
        
        # Find the best agent for this task
        agent_id = await self._find_best_agent(required_capabilities, preferred_agent)
        
        if not agent_id:
            raise ValueError("No suitable agent available for this task")
        
        task = AgentTask(
            id=task_id,
            agent_id=agent_id,
            task_type=task_type,
            description=description,
            parameters=parameters,
            priority=priority,
            created_at=datetime.now()
        )
        
        self.tasks[task_id] = task
        
        # Add to priority queue
        await self.task_queue.put((priority.value, task))
        
        logger.info(f"Task submitted: {task_id} -> Agent {agent_id} ({task_type})")
        
        # Broadcast task submission
        if self.websocket_manager:
            await self.websocket_manager.broadcast_to_channel(
                'task_submitted',
                {
                    'channel': 'task_submitted',
                    'payload': {
                        'task_id': task_id,
                        'agent_id': agent_id,
                        'task_type': task_type,
                        'description': description,
                        'priority': priority.name,
                        'status': 'queued'
                    }
                }
            )
        
        return task_id

    async def _find_best_agent(self, required_capabilities: List[str], 
                              preferred_agent: Optional[str] = None) -> Optional[str]:
        """Find the best available agent for a task"""
        
        # If preferred agent is specified and available, use it
        if preferred_agent and preferred_agent in self.agents:
            agent = self.agents[preferred_agent]
            if (agent.status in [AgentStatus.IDLE, AgentStatus.PROCESSING] and
                agent.current_task_count < agent.max_concurrent_tasks and
                all(cap in agent.capabilities for cap in required_capabilities)):
                return preferred_agent
        
        # Find all suitable agents
        suitable_agents = []
        for agent_id, agent in self.agents.items():
            if (agent.status in [AgentStatus.IDLE, AgentStatus.PROCESSING] and
                agent.current_task_count < agent.max_concurrent_tasks and
                all(cap in agent.capabilities for cap in required_capabilities)):
                suitable_agents.append((agent_id, agent))
        
        if not suitable_agents:
            return None
        
        # Sort by performance and load
        suitable_agents.sort(key=lambda x: (
            x[1].load_percentage,
            x[1].metrics.average_response_time,
            -x[1].metrics.success_rate
        ))
        
        return suitable_agents[0][0]

    async def _process_task_queue(self):
        """Process tasks from the queue"""
        while self.running:
            try:
                # Get next task from priority queue
                priority, task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                
                # Check if agent is still available
                agent_id = task.agent_id
                if agent_id not in self.agents:
                    task.status = "failed"
                    task.error = "Agent no longer available"
                    task.completed_at = datetime.now()
                    continue
                
                agent = self.agents[agent_id]
                
                # Check if agent can handle the task
                if agent.current_task_count >= agent.max_concurrent_tasks:
                    # Re-queue the task
                    await self.task_queue.put((priority, task))
                    await asyncio.sleep(0.1)
                    continue
                
                # Start task execution
                await self._execute_task(task)
                
            except asyncio.TimeoutError:
                # No tasks in queue, continue
                continue
            except Exception as e:
                logger.error(f"Error processing task queue: {e}")
                await asyncio.sleep(1)

    async def _execute_task(self, task: AgentTask):
        """Execute a task on the assigned agent"""
        agent = self.agents[task.agent_id]
        
        # Update task status
        task.status = "running"
        task.started_at = datetime.now()
        
        # Update agent status
        agent.current_task_count += 1
        agent.current_task = task.description
        if agent.status == AgentStatus.IDLE:
            agent.status = AgentStatus.PROCESSING
        
        await self._broadcast_agent_update(task.agent_id)
        await self._broadcast_task_update(task.id)
        
        try:
            # Simulate task execution (replace with actual agent execution)
            execution_time = await self._simulate_task_execution(task)
            
            # Task completed successfully
            task.status = "completed"
            task.completed_at = datetime.now()
            task.result = {
                "success": True,
                "execution_time": execution_time,
                "message": f"Task {task.task_type} completed successfully"
            }
            
            # Update agent metrics
            await self._update_agent_metrics(task.agent_id, execution_time, True)
            
        except Exception as e:
            # Task failed
            task.status = "failed"
            task.completed_at = datetime.now()
            task.error = str(e)
            
            # Update agent metrics
            await self._update_agent_metrics(task.agent_id, 0, False)
            
            logger.error(f"Task {task.id} failed: {e}")
        
        finally:
            # Update agent status
            agent.current_task_count -= 1
            if agent.current_task_count == 0:
                agent.status = AgentStatus.IDLE
                agent.current_task = None
            
            await self._broadcast_agent_update(task.agent_id)
            await self._broadcast_task_update(task.id)

    async def _simulate_task_execution(self, task: AgentTask) -> float:
        """Simulate task execution (replace with actual agent execution)"""
        # Simulate variable execution time based on task type
        base_time = {
            'code_generation': 2.0,
            'debugging': 1.5,
            'testing': 3.0,
            'documentation': 1.0,
            'analysis': 2.5
        }.get(task.task_type, 1.0)
        
        # Add some randomness
        import random
        execution_time = base_time + random.uniform(0.5, 2.0)
        
        await asyncio.sleep(execution_time)
        
        # Simulate occasional failures
        if random.random() < 0.05:  # 5% failure rate
            raise Exception("Simulated task failure")
        
        return execution_time

    async def _update_agent_metrics(self, agent_id: str, execution_time: float, success: bool):
        """Update agent performance metrics"""
        if agent_id not in self.agents:
            return
            
        agent = self.agents[agent_id]
        metrics = agent.metrics
        
        # Update task count
        metrics.tasks_completed += 1
        metrics.last_activity = datetime.now()
        
        if success:
            # Update average response time
            metrics.total_execution_time += execution_time
            metrics.average_response_time = (metrics.total_execution_time / metrics.tasks_completed) * 1000  # Convert to ms
        else:
            metrics.error_count += 1
            
        # Calculate success rate
        metrics.success_rate = ((metrics.tasks_completed - metrics.error_count) / metrics.tasks_completed) * 100
        
        # Check performance thresholds
        await self._check_performance_thresholds(agent_id)

    async def _check_performance_thresholds(self, agent_id: str):
        """Check if agent performance meets thresholds"""
        agent = self.agents[agent_id]
        metrics = agent.metrics
        
        alerts = []
        
        if metrics.average_response_time > self.performance_thresholds['max_response_time']:
            alerts.append(f"High response time: {metrics.average_response_time:.0f}ms")
            
        if metrics.success_rate < self.performance_thresholds['min_success_rate']:
            alerts.append(f"Low success rate: {metrics.success_rate:.1f}%")
            
        error_rate = (metrics.error_count / metrics.tasks_completed * 100) if metrics.tasks_completed > 0 else 0
        if error_rate > self.performance_thresholds['max_error_rate']:
            alerts.append(f"High error rate: {error_rate:.1f}%")
            
        if agent.load_percentage > self.performance_thresholds['max_load_percentage']:
            alerts.append(f"High load: {agent.load_percentage:.1f}%")
            
        if alerts:
            await self._send_performance_alert(agent_id, alerts)

    async def _send_performance_alert(self, agent_id: str, alerts: List[str]):
        """Send performance alert to monitoring systems"""
        if not self.websocket_manager:
            return
            
        agent = self.agents[agent_id]
        alert_data = {
            'agent_id': agent_id,
            'agent_name': agent.name,
            'alerts': alerts,
            'timestamp': datetime.now().isoformat(),
            'metrics': asdict(agent.metrics)
        }
        
        await self.websocket_manager.broadcast_to_channel(
            'performance_alert',
            {
                'channel': 'performance_alert',
                'payload': alert_data
            }
        )

    async def _broadcast_agent_update(self, agent_id: str):
        """Broadcast agent status update to all connected clients"""
        if not self.websocket_manager or agent_id not in self.agents:
            return
            
        agent = self.agents[agent_id]
        agent_data = asdict(agent)
        
        # Convert datetime objects to ISO strings
        if agent_data['metrics']['last_activity']:
            agent_data['metrics']['last_activity'] = agent_data['metrics']['last_activity'].isoformat()
        if agent_data['last_heartbeat']:
            agent_data['last_heartbeat'] = agent_data['last_heartbeat'].isoformat()
            
        # Convert enum to string
        agent_data['status'] = agent.status.value
        
        await self.websocket_manager.broadcast_to_channel(
            'agent_status',
            {
                'channel': 'agent_status',
                'payload': agent_data
            }
        )

    async def _broadcast_task_update(self, task_id: str):
        """Broadcast task status update to all connected clients"""
        if not self.websocket_manager or task_id not in self.tasks:
            return
            
        task = self.tasks[task_id]
        task_data = asdict(task)
        
        # Convert datetime objects to ISO strings
        task_data['created_at'] = task.created_at.isoformat()
        if task.started_at:
            task_data['started_at'] = task.started_at.isoformat()
        if task.completed_at:
            task_data['completed_at'] = task.completed_at.isoformat()
            
        # Convert enum to string
        task_data['priority'] = task.priority.name
        
        await self.websocket_manager.broadcast_to_channel(
            'task_completion',
            {
                'channel': 'task_completion',
                'payload': task_data
            }
        )

    async def get_system_overview(self) -> Dict[str, Any]:
        """Get overall system status and metrics"""
        total_agents = len(self.agents)
        active_agents = len([a for a in self.agents.values() if a.status != AgentStatus.OFFLINE])
        processing_agents = len([a for a in self.agents.values() if a.status == AgentStatus.PROCESSING])
        
        if total_agents > 0:
            avg_response_time = sum(a.metrics.average_response_time for a in self.agents.values()) / total_agents
            avg_success_rate = sum(a.metrics.success_rate for a in self.agents.values()) / total_agents
            total_tasks = sum(a.metrics.tasks_completed for a in self.agents.values())
        else:
            avg_response_time = 0
            avg_success_rate = 0
            total_tasks = 0
        
        # Task statistics
        queued_tasks = len([t for t in self.tasks.values() if t.status == "queued"])
        running_tasks = len([t for t in self.tasks.values() if t.status == "running"])
        completed_tasks = len([t for t in self.tasks.values() if t.status == "completed"])
        failed_tasks = len([t for t in self.tasks.values() if t.status == "failed"])
        
        return {
            'total_agents': total_agents,
            'active_agents': active_agents,
            'processing_agents': processing_agents,
            'offline_agents': total_agents - active_agents,
            'system_metrics': {
                'average_response_time': avg_response_time,
                'average_success_rate': avg_success_rate,
                'total_tasks_completed': total_tasks
            },
            'task_statistics': {
                'queued': queued_tasks,
                'running': running_tasks,
                'completed': completed_tasks,
                'failed': failed_tasks,
                'total': len(self.tasks)
            },
            'system_health': self._calculate_system_health()
        }

    def _calculate_system_health(self) -> str:
        """Calculate overall system health"""
        if not self.agents:
            return 'unknown'
            
        offline_agents = len([a for a in self.agents.values() if a.status == AgentStatus.OFFLINE])
        error_agents = len([a for a in self.agents.values() if a.status == AgentStatus.ERROR])
        
        if offline_agents > len(self.agents) * 0.5:
            return 'critical'
        elif error_agents > 0 or offline_agents > 0:
            return 'degraded'
        
        # Check performance metrics
        poor_performance_agents = len([
            a for a in self.agents.values() 
            if (a.metrics.success_rate < self.performance_thresholds['min_success_rate'] or
                a.metrics.average_response_time > self.performance_thresholds['max_response_time'])
        ])
        
        if poor_performance_agents > len(self.agents) * 0.3:
            return 'degraded'
            
        return 'healthy'

    async def get_agent_details(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific agent"""
        if agent_id not in self.agents:
            return None
            
        agent = self.agents[agent_id]
        agent_data = asdict(agent)
        
        # Convert datetime objects to ISO strings
        if agent_data['metrics']['last_activity']:
            agent_data['metrics']['last_activity'] = agent_data['metrics']['last_activity'].isoformat()
        if agent_data['last_heartbeat']:
            agent_data['last_heartbeat'] = agent_data['last_heartbeat'].isoformat()
            
        # Convert enum to string
        agent_data['status'] = agent.status.value
        
        # Add recent tasks
        recent_tasks = [
            asdict(task) for task in self.tasks.values() 
            if task.agent_id == agent_id
        ][-10:]  # Last 10 tasks
        
        # Convert datetime objects in tasks
        for task_data in recent_tasks:
            task_data['created_at'] = task_data['created_at']
            if task_data['started_at']:
                task_data['started_at'] = task_data['started_at']
            if task_data['completed_at']:
                task_data['completed_at'] = task_data['completed_at']
            task_data['priority'] = task_data['priority']
        
        agent_data['recent_tasks'] = recent_tasks
        
        return agent_data

    async def cleanup_old_tasks(self, max_age_hours: int = 24):
        """Clean up old completed/failed tasks"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        old_tasks = [
            task_id for task_id, task in self.tasks.items()
            if (task.status in ["completed", "failed"] and 
                task.completed_at and task.completed_at < cutoff_time)
        ]
        
        for task_id in old_tasks:
            del self.tasks[task_id]
            
        if old_tasks:
            logger.info(f"Cleaned up {len(old_tasks)} old tasks")

    async def check_agent_health(self):
        """Check agent health and mark offline agents"""
        now = datetime.now()
        timeout_threshold = timedelta(minutes=5)  # 5 minutes without heartbeat
        
        for agent_id, agent in self.agents.items():
            if agent.last_heartbeat and (now - agent.last_heartbeat) > timeout_threshold:
                if agent.status != AgentStatus.OFFLINE:
                    logger.warning(f"Agent {agent_id} marked as offline (no heartbeat for {now - agent.last_heartbeat})")
                    agent.status = AgentStatus.OFFLINE
                    agent.current_task = None
                    agent.current_task_count = 0
                    await self._broadcast_agent_update(agent_id)

# Global instance
enhanced_agent_coordinator = EnhancedAgentCoordinator()