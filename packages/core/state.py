"""State management for reVoAgent platform."""

import threading
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime


class AgentState(Enum):
    """Agent state enumeration."""
    IDLE = "idle"
    BUSY = "busy"
    WAITING = "waiting"
    ERROR = "error"
    PAUSED = "paused"
    STOPPED = "stopped"


class TaskState(Enum):
    """Task state enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentStateInfo:
    """Agent state information."""
    agent_id: str
    state: AgentState
    current_task: Optional[str] = None
    last_update: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskStateInfo:
    """Task state information."""
    task_id: str
    state: TaskState
    agent_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    progress: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class StateManager:
    """
    Manages the state of agents and tasks in the reVoAgent platform.
    
    Features:
    - Thread-safe state management
    - State transition validation
    - State history tracking
    - Event notifications
    - State persistence (optional)
    """
    
    def __init__(self):
        """Initialize state manager."""
        self.lock = threading.RLock()
        
        # State storage
        self.agent_states: Dict[str, AgentStateInfo] = {}
        self.task_states: Dict[str, TaskStateInfo] = {}
        
        # State history (limited to prevent memory growth)
        self.agent_history: Dict[str, List[AgentStateInfo]] = {}
        self.task_history: Dict[str, List[TaskStateInfo]] = {}
        self.max_history_size = 100
        
        # State change callbacks
        self.agent_state_callbacks: List[callable] = []
        self.task_state_callbacks: List[callable] = []
    
    def set_agent_state(
        self,
        agent_id: str,
        state: AgentState,
        current_task: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Set the state of an agent."""
        with self.lock:
            # Validate state transition
            current_state_info = self.agent_states.get(agent_id)
            if current_state_info and not self._is_valid_agent_transition(
                current_state_info.state, state
            ):
                raise ValueError(
                    f"Invalid state transition for agent {agent_id}: "
                    f"{current_state_info.state.value} -> {state.value}"
                )
            
            # Create new state info
            new_state_info = AgentStateInfo(
                agent_id=agent_id,
                state=state,
                current_task=current_task,
                last_update=datetime.now(),
                metadata=metadata or {}
            )
            
            # Store previous state in history
            if current_state_info:
                self._add_to_agent_history(agent_id, current_state_info)
            
            # Update current state
            self.agent_states[agent_id] = new_state_info
            
            # Notify callbacks
            self._notify_agent_state_change(agent_id, state, current_state_info)
    
    def get_agent_state(self, agent_id: str) -> Optional[AgentState]:
        """Get the current state of an agent."""
        with self.lock:
            state_info = self.agent_states.get(agent_id)
            return state_info.state if state_info else None
    
    def get_agent_state_info(self, agent_id: str) -> Optional[AgentStateInfo]:
        """Get detailed state information for an agent."""
        with self.lock:
            return self.agent_states.get(agent_id)
    
    def set_task_state(
        self,
        task_id: str,
        state: TaskState,
        agent_id: Optional[str] = None,
        progress: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Set the state of a task."""
        with self.lock:
            # Get current state info
            current_state_info = self.task_states.get(task_id)
            
            # Validate state transition
            if current_state_info and not self._is_valid_task_transition(
                current_state_info.state, state
            ):
                raise ValueError(
                    f"Invalid state transition for task {task_id}: "
                    f"{current_state_info.state.value} -> {state.value}"
                )
            
            # Create new state info
            now = datetime.now()
            new_state_info = TaskStateInfo(
                task_id=task_id,
                state=state,
                agent_id=agent_id or (current_state_info.agent_id if current_state_info else None),
                start_time=current_state_info.start_time if current_state_info else (
                    now if state == TaskState.RUNNING else None
                ),
                end_time=now if state in [TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED] else None,
                progress=progress if progress is not None else (
                    current_state_info.progress if current_state_info else 0.0
                ),
                metadata=metadata or (current_state_info.metadata if current_state_info else {})
            )
            
            # Store previous state in history
            if current_state_info:
                self._add_to_task_history(task_id, current_state_info)
            
            # Update current state
            self.task_states[task_id] = new_state_info
            
            # Notify callbacks
            self._notify_task_state_change(task_id, state, current_state_info)
    
    def get_task_state(self, task_id: str) -> Optional[TaskState]:
        """Get the current state of a task."""
        with self.lock:
            state_info = self.task_states.get(task_id)
            return state_info.state if state_info else None
    
    def get_task_state_info(self, task_id: str) -> Optional[TaskStateInfo]:
        """Get detailed state information for a task."""
        with self.lock:
            return self.task_states.get(task_id)
    
    def get_agents_by_state(self, state: AgentState) -> List[str]:
        """Get all agents in a specific state."""
        with self.lock:
            return [
                agent_id for agent_id, state_info in self.agent_states.items()
                if state_info.state == state
            ]
    
    def get_tasks_by_state(self, state: TaskState) -> List[str]:
        """Get all tasks in a specific state."""
        with self.lock:
            return [
                task_id for task_id, state_info in self.task_states.items()
                if state_info.state == state
            ]
    
    def get_agent_tasks(self, agent_id: str) -> List[str]:
        """Get all tasks assigned to an agent."""
        with self.lock:
            return [
                task_id for task_id, state_info in self.task_states.items()
                if state_info.agent_id == agent_id
            ]
    
    def remove_agent_state(self, agent_id: str) -> bool:
        """Remove an agent's state information."""
        with self.lock:
            if agent_id in self.agent_states:
                del self.agent_states[agent_id]
                return True
            return False
    
    def remove_task_state(self, task_id: str) -> bool:
        """Remove a task's state information."""
        with self.lock:
            if task_id in self.task_states:
                del self.task_states[task_id]
                return True
            return False
    
    def get_agent_history(self, agent_id: str) -> List[AgentStateInfo]:
        """Get state history for an agent."""
        with self.lock:
            return self.agent_history.get(agent_id, []).copy()
    
    def get_task_history(self, task_id: str) -> List[TaskStateInfo]:
        """Get state history for a task."""
        with self.lock:
            return self.task_history.get(task_id, []).copy()
    
    def register_agent_state_callback(self, callback: callable) -> None:
        """Register a callback for agent state changes."""
        self.agent_state_callbacks.append(callback)
    
    def register_task_state_callback(self, callback: callable) -> None:
        """Register a callback for task state changes."""
        self.task_state_callbacks.append(callback)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        with self.lock:
            agent_state_counts = {}
            for state in AgentState:
                agent_state_counts[state.value] = len(self.get_agents_by_state(state))
            
            task_state_counts = {}
            for state in TaskState:
                task_state_counts[state.value] = len(self.get_tasks_by_state(state))
            
            return {
                "agents": {
                    "total": len(self.agent_states),
                    "by_state": agent_state_counts
                },
                "tasks": {
                    "total": len(self.task_states),
                    "by_state": task_state_counts
                },
                "timestamp": datetime.now().isoformat()
            }
    
    def _is_valid_agent_transition(self, from_state: AgentState, to_state: AgentState) -> bool:
        """Validate agent state transitions."""
        # Define valid transitions
        valid_transitions = {
            AgentState.IDLE: [AgentState.BUSY, AgentState.PAUSED, AgentState.STOPPED],
            AgentState.BUSY: [AgentState.IDLE, AgentState.WAITING, AgentState.ERROR, AgentState.PAUSED],
            AgentState.WAITING: [AgentState.BUSY, AgentState.IDLE, AgentState.ERROR],
            AgentState.ERROR: [AgentState.IDLE, AgentState.STOPPED],
            AgentState.PAUSED: [AgentState.IDLE, AgentState.BUSY, AgentState.STOPPED],
            AgentState.STOPPED: [AgentState.IDLE]
        }
        
        return to_state in valid_transitions.get(from_state, [])
    
    def _is_valid_task_transition(self, from_state: TaskState, to_state: TaskState) -> bool:
        """Validate task state transitions."""
        # Define valid transitions
        valid_transitions = {
            TaskState.PENDING: [TaskState.RUNNING, TaskState.CANCELLED],
            TaskState.RUNNING: [TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED],
            TaskState.COMPLETED: [],  # Terminal state
            TaskState.FAILED: [],     # Terminal state
            TaskState.CANCELLED: []   # Terminal state
        }
        
        return to_state in valid_transitions.get(from_state, [])
    
    def _add_to_agent_history(self, agent_id: str, state_info: AgentStateInfo) -> None:
        """Add state info to agent history."""
        if agent_id not in self.agent_history:
            self.agent_history[agent_id] = []
        
        history = self.agent_history[agent_id]
        history.append(state_info)
        
        # Limit history size
        if len(history) > self.max_history_size:
            self.agent_history[agent_id] = history[-self.max_history_size:]
    
    def _add_to_task_history(self, task_id: str, state_info: TaskStateInfo) -> None:
        """Add state info to task history."""
        if task_id not in self.task_history:
            self.task_history[task_id] = []
        
        history = self.task_history[task_id]
        history.append(state_info)
        
        # Limit history size
        if len(history) > self.max_history_size:
            self.task_history[task_id] = history[-self.max_history_size:]
    
    def _notify_agent_state_change(
        self,
        agent_id: str,
        new_state: AgentState,
        previous_state_info: Optional[AgentStateInfo]
    ) -> None:
        """Notify callbacks of agent state changes."""
        for callback in self.agent_state_callbacks:
            try:
                callback(agent_id, new_state, previous_state_info)
            except Exception as e:
                # Log error but don't fail the state change
                print(f"Error in agent state callback: {e}")
    
    def _notify_task_state_change(
        self,
        task_id: str,
        new_state: TaskState,
        previous_state_info: Optional[TaskStateInfo]
    ) -> None:
        """Notify callbacks of task state changes."""
        for callback in self.task_state_callbacks:
            try:
                callback(task_id, new_state, previous_state_info)
            except Exception as e:
                # Log error but don't fail the state change
                print(f"Error in task state callback: {e}")