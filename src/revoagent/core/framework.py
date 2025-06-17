"""Core agent framework for reVoAgent platform."""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Type
from dataclasses import dataclass
from enum import Enum

from .config import Config, get_config
from .memory import MemoryManager
from .state import StateManager, AgentState
from .communication import CommunicationManager
from ..agents.base import BaseAgent
from ..model_layer.local_models import LocalModelManager as ModelManager
from ..tools.manager import ToolManager


class FrameworkStatus(Enum):
    """Framework status enumeration."""
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class TaskRequest:
    """Task request structure."""
    id: str
    type: str
    description: str
    agent_type: str
    parameters: Dict[str, Any]
    priority: int = 1
    timeout: Optional[int] = None


@dataclass
class TaskResult:
    """Task result structure."""
    task_id: str
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = None


class AgentFramework:
    """
    Core agent framework that manages agents, models, tools, and workflows.
    
    This is the central orchestrator that coordinates all platform components
    following the architectural blueprint.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the agent framework."""
        self.config = config or get_config()
        self.status = FrameworkStatus.INITIALIZING
        
        # Core managers
        self.memory_manager = MemoryManager()
        self.state_manager = StateManager()
        self.communication_manager = CommunicationManager()
        self.model_manager = ModelManager(self.config)
        self.tool_manager = ToolManager(self.config)
        
        # Agent registry
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_classes: Dict[str, Type[BaseAgent]] = {}
        
        # Task management
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.active_tasks: Dict[str, asyncio.Task] = {}
        
        # Logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self._initialize_components()
    
    def _initialize_components(self) -> None:
        """Initialize all framework components."""
        try:
            # Initialize model manager
            self.model_manager.initialize()
            
            # Initialize tool manager
            self.tool_manager.initialize()
            
            # Register default agent types
            self._register_default_agents()
            
            # Create configured agents
            self._create_configured_agents()
            
            self.status = FrameworkStatus.READY
            self.logger.info("Agent framework initialized successfully")
            
        except Exception as e:
            self.status = FrameworkStatus.ERROR
            self.logger.error(f"Failed to initialize framework: {e}")
            raise
    
    def _register_default_agents(self) -> None:
        """Register default agent types."""
        from ..agents.code_generator import CodeGeneratorAgent
        from ..agents.browser_agent import BrowserAgent
        from ..agents.debugging_agent import DebuggingAgent
        from ..agents.testing_agent import TestingAgent
        
        self.register_agent_class("code_generator", CodeGeneratorAgent)
        self.register_agent_class("browser_agent", BrowserAgent)
        self.register_agent_class("debugging_agent", DebuggingAgent)
        self.register_agent_class("testing_agent", TestingAgent)
    
    def _create_configured_agents(self) -> None:
        """Create agents based on configuration."""
        for agent_name, agent_config in self.config.agents.items():
            if agent_config.enabled:
                try:
                    agent = self.create_agent(agent_name, agent_name)
                    self.logger.info(f"Created agent: {agent_name}")
                except Exception as e:
                    self.logger.error(f"Failed to create agent {agent_name}: {e}")
    
    def register_agent_class(self, agent_type: str, agent_class: Type[BaseAgent]) -> None:
        """Register an agent class for the given type."""
        self.agent_classes[agent_type] = agent_class
        self.logger.debug(f"Registered agent class: {agent_type}")
    
    def create_agent(self, agent_id: str, agent_type: str, **kwargs) -> BaseAgent:
        """Create a new agent instance."""
        if agent_type not in self.agent_classes:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        agent_class = self.agent_classes[agent_type]
        agent_config = self.config.get_agent_config(agent_type)
        
        if not agent_config:
            raise ValueError(f"No configuration found for agent type: {agent_type}")
        
        # Create agent with framework dependencies
        agent = agent_class(
            agent_id=agent_id,
            config=agent_config,
            model_manager=self.model_manager,
            tool_manager=self.tool_manager,
            memory_manager=self.memory_manager,
            **kwargs
        )
        
        self.agents[agent_id] = agent
        self.state_manager.set_agent_state(agent_id, AgentState.IDLE)
        
        return agent
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get an agent by ID."""
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[str]:
        """List all registered agent IDs."""
        return list(self.agents.keys())
    
    def remove_agent(self, agent_id: str) -> bool:
        """Remove an agent from the framework."""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            agent.cleanup()
            del self.agents[agent_id]
            self.state_manager.remove_agent_state(agent_id)
            return True
        return False
    
    async def submit_task(self, task: TaskRequest) -> str:
        """Submit a task for execution."""
        await self.task_queue.put(task)
        self.logger.info(f"Task submitted: {task.id}")
        return task.id
    
    async def execute_task(self, task: TaskRequest) -> TaskResult:
        """Execute a single task."""
        import time
        start_time = time.time()
        
        try:
            # Get or create agent for the task
            agent = self.get_agent(task.agent_type)
            if not agent:
                agent = self.create_agent(f"{task.agent_type}_temp", task.agent_type)
            
            # Set agent state to busy
            self.state_manager.set_agent_state(agent.agent_id, AgentState.BUSY)
            
            # Execute the task
            result = await agent.execute_task(task.description, task.parameters)
            
            # Set agent state back to idle
            self.state_manager.set_agent_state(agent.agent_id, AgentState.IDLE)
            
            execution_time = time.time() - start_time
            
            return TaskResult(
                task_id=task.id,
                success=True,
                result=result,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Task execution failed: {e}")
            
            return TaskResult(
                task_id=task.id,
                success=False,
                result=None,
                error=str(e),
                execution_time=execution_time
            )
    
    async def start_task_processor(self) -> None:
        """Start the task processing loop."""
        self.status = FrameworkStatus.RUNNING
        self.logger.info("Starting task processor")
        
        while self.status == FrameworkStatus.RUNNING:
            try:
                # Get task from queue with timeout
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                
                # Create task coroutine
                task_coro = self.execute_task(task)
                
                # Start task execution
                task_handle = asyncio.create_task(task_coro)
                self.active_tasks[task.id] = task_handle
                
                # Clean up completed tasks
                completed_tasks = [
                    task_id for task_id, task_handle in self.active_tasks.items()
                    if task_handle.done()
                ]
                for task_id in completed_tasks:
                    del self.active_tasks[task_id]
                
            except asyncio.TimeoutError:
                # No tasks in queue, continue
                continue
            except Exception as e:
                self.logger.error(f"Error in task processor: {e}")
    
    async def stop_task_processor(self) -> None:
        """Stop the task processing loop."""
        self.status = FrameworkStatus.STOPPED
        
        # Cancel all active tasks
        for task_handle in self.active_tasks.values():
            task_handle.cancel()
        
        # Wait for tasks to complete
        if self.active_tasks:
            await asyncio.gather(*self.active_tasks.values(), return_exceptions=True)
        
        self.active_tasks.clear()
        self.logger.info("Task processor stopped")
    
    def get_framework_status(self) -> Dict[str, Any]:
        """Get current framework status."""
        return {
            "status": self.status.value,
            "agents": {
                agent_id: {
                    "type": agent.__class__.__name__,
                    "state": self.state_manager.get_agent_state(agent_id).value
                }
                for agent_id, agent in self.agents.items()
            },
            "active_tasks": len(self.active_tasks),
            "queue_size": self.task_queue.qsize(),
            "models": self.model_manager.get_status(),
            "tools": self.tool_manager.get_status()
        }
    
    async def shutdown(self) -> None:
        """Shutdown the framework gracefully."""
        self.logger.info("Shutting down agent framework")
        
        # Stop task processor
        await self.stop_task_processor()
        
        # Cleanup all agents
        for agent in self.agents.values():
            agent.cleanup()
        
        # Cleanup managers
        self.model_manager.cleanup()
        self.tool_manager.cleanup()
        
        self.status = FrameworkStatus.STOPPED
        self.logger.info("Agent framework shutdown complete")


class ThreeEngineArchitecture:
    """
    Three-Engine Architecture for reVoAgent
    Provides a unified interface for the three core engines:
    - Perfect Recall Engine (Memory & Context)
    - Parallel Mind Engine (Multi-Worker Processing)
    - Creative Engine (Solution Generation)
    """
    
    def __init__(self):
        self.is_initialized = False
        self.engines = {}
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self) -> bool:
        """Initialize the Three-Engine Architecture"""
        try:
            self.logger.info("Initializing Three-Engine Architecture...")
            
            # Initialize engines (placeholder implementation)
            self.engines = {
                "perfect_recall": {"status": "active", "type": "memory"},
                "parallel_mind": {"status": "active", "type": "processing"},
                "creative_engine": {"status": "active", "type": "generation"}
            }
            
            self.is_initialized = True
            self.logger.info("Three-Engine Architecture initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Three-Engine Architecture: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get the status of all engines"""
        return {
            "initialized": self.is_initialized,
            "engines": self.engines
        }