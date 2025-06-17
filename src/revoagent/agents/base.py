"""Base agent class for reVoAgent platform."""

import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, TYPE_CHECKING
from datetime import datetime

from ..core.config import AgentConfig
from ..core.memory import MemoryManager, MemoryEntry
from ..core.state import AgentState

if TYPE_CHECKING:
    from ..models.manager import ModelManager
    from ..tools.manager import ToolManager


class BaseAgent(ABC):
    """
    Base class for all agents in the reVoAgent platform.
    
    Provides common functionality including:
    - Memory management
    - Tool integration
    - Model interaction
    - State management
    - Communication
    """
    
    def __init__(
        self,
        agent_id: str,
        config: AgentConfig,
        model_manager: "ModelManager",
        tool_manager: "ToolManager",
        memory_manager: MemoryManager,
        **kwargs
    ):
        """Initialize base agent."""
        self.agent_id = agent_id
        self.config = config
        self.model_manager = model_manager
        self.tool_manager = tool_manager
        self.memory_manager = memory_manager
        
        # Agent state
        self.state = AgentState.IDLE
        self.current_task: Optional[str] = None
        
        # Logging
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Performance tracking
        self.task_count = 0
        self.success_count = 0
        self.error_count = 0
        self.total_execution_time = 0.0
        
        # Initialize agent-specific components
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize agent-specific components. Override in subclasses."""
        pass
    
    @abstractmethod
    async def execute_task(self, task_description: str, parameters: Dict[str, Any]) -> Any:
        """
        Execute a task. Must be implemented by subclasses.
        
        Args:
            task_description: Natural language description of the task
            parameters: Task-specific parameters
            
        Returns:
            Task result
        """
        pass
    
    async def process_message(self, message_content: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Process a message using the agent's model.
        
        Args:
            message_content: The message to process
            context: Optional context information
            
        Returns:
            Agent's response
        """
        try:
            # Get recent memories for context
            recent_memories = self.memory_manager.get_recent_memories(self.agent_id, limit=5)
            memory_context = "\n".join([mem.content for mem in recent_memories])
            
            # Prepare prompt with context
            prompt = self._build_prompt(message_content, memory_context, context)
            
            # Get model response
            response = await self.model_manager.generate_response(
                model_name=self.config.model,
                prompt=prompt,
                max_tokens=self.config.max_iterations * 10  # Rough estimate
            )
            
            # Store interaction in memory
            await self._store_interaction(message_content, response)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return f"I encountered an error while processing your message: {str(e)}"
    
    def _build_prompt(
        self,
        message: str,
        memory_context: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build a prompt for the model including context and memory."""
        prompt_parts = [
            f"You are {self.__class__.__name__}, an AI agent specialized in {self.get_capabilities()}.",
            "",
            "Recent context from memory:",
            memory_context,
            "",
        ]
        
        if context:
            prompt_parts.extend([
                "Additional context:",
                str(context),
                ""
            ])
        
        prompt_parts.extend([
            "Current message:",
            message,
            "",
            "Please provide a helpful response:"
        ])
        
        return "\n".join(prompt_parts)
    
    async def _store_interaction(self, user_message: str, agent_response: str) -> None:
        """Store the interaction in memory."""
        # Store user message
        user_memory = MemoryEntry(
            id=f"{self.agent_id}_user_{uuid.uuid4()}",
            agent_id=self.agent_id,
            type="conversation",
            content=f"User: {user_message}",
            metadata={"role": "user"},
            timestamp=datetime.now(),
            importance=0.6
        )
        self.memory_manager.store_memory(user_memory)
        
        # Store agent response
        agent_memory = MemoryEntry(
            id=f"{self.agent_id}_agent_{uuid.uuid4()}",
            agent_id=self.agent_id,
            type="conversation",
            content=f"Agent: {agent_response}",
            metadata={"role": "agent"},
            timestamp=datetime.now(),
            importance=0.6
        )
        self.memory_manager.store_memory(agent_memory)
    
    async def use_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """
        Use a tool with the given parameters.
        
        Args:
            tool_name: Name of the tool to use
            parameters: Tool parameters
            
        Returns:
            Tool execution result
        """
        try:
            if tool_name not in self.config.tools:
                raise ValueError(f"Tool {tool_name} not available for this agent")
            
            result = await self.tool_manager.execute_tool(tool_name, parameters)
            
            # Store tool usage in memory
            tool_memory = MemoryEntry(
                id=f"{self.agent_id}_tool_{uuid.uuid4()}",
                agent_id=self.agent_id,
                type="tool_usage",
                content=f"Used tool {tool_name} with parameters {parameters}. Result: {result}",
                metadata={"tool": tool_name, "parameters": parameters},
                timestamp=datetime.now(),
                importance=0.7
            )
            self.memory_manager.store_memory(tool_memory)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error using tool {tool_name}: {e}")
            raise
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tools for this agent."""
        return self.config.tools.copy()
    
    def get_capabilities(self) -> str:
        """Get a description of the agent's capabilities. Override in subclasses."""
        return "general AI assistance"
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.__class__.__name__,
            "state": self.state.value,
            "current_task": self.current_task,
            "capabilities": self.get_capabilities(),
            "available_tools": self.get_available_tools(),
            "performance": {
                "task_count": self.task_count,
                "success_count": self.success_count,
                "error_count": self.error_count,
                "success_rate": self.success_count / max(self.task_count, 1),
                "average_execution_time": self.total_execution_time / max(self.task_count, 1)
            },
            "memory_stats": self.memory_manager.get_memory_stats(self.agent_id)
        }
    
    async def reflect_on_performance(self) -> str:
        """Reflect on recent performance and generate insights."""
        try:
            # Get recent task memories
            task_memories = self.memory_manager.retrieve_memories(
                agent_id=self.agent_id,
                memory_type="task",
                limit=10
            )
            
            if not task_memories:
                return "No recent tasks to reflect on."
            
            # Analyze performance
            performance_data = {
                "recent_tasks": len(task_memories),
                "success_rate": self.success_count / max(self.task_count, 1),
                "common_tools": self._get_common_tools_used(),
                "error_patterns": self._analyze_error_patterns()
            }
            
            # Generate reflection using model
            reflection_prompt = f"""
            Analyze my recent performance as {self.__class__.__name__}:
            
            Performance Data:
            {performance_data}
            
            Recent Task Memories:
            {[mem.content for mem in task_memories[:5]]}
            
            Please provide insights on:
            1. What I'm doing well
            2. Areas for improvement
            3. Patterns in my work
            4. Suggestions for optimization
            """
            
            reflection = await self.model_manager.generate_response(
                model_name=self.config.model,
                prompt=reflection_prompt,
                max_tokens=500
            )
            
            # Store reflection in memory
            reflection_memory = MemoryEntry(
                id=f"{self.agent_id}_reflection_{uuid.uuid4()}",
                agent_id=self.agent_id,
                type="reflection",
                content=reflection,
                metadata={"performance_data": performance_data},
                timestamp=datetime.now(),
                importance=0.8
            )
            self.memory_manager.store_memory(reflection_memory)
            
            return reflection
            
        except Exception as e:
            self.logger.error(f"Error during reflection: {e}")
            return f"Unable to reflect on performance: {str(e)}"
    
    def _get_common_tools_used(self) -> List[str]:
        """Get most commonly used tools from memory."""
        tool_memories = self.memory_manager.retrieve_memories(
            agent_id=self.agent_id,
            memory_type="tool_usage",
            limit=20
        )
        
        tool_counts = {}
        for memory in tool_memories:
            tool_name = memory.metadata.get("tool")
            if tool_name:
                tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1
        
        return sorted(tool_counts.keys(), key=lambda x: tool_counts[x], reverse=True)[:5]
    
    def _analyze_error_patterns(self) -> List[str]:
        """Analyze error patterns from memory."""
        # This is a simplified implementation
        # In a real system, you might use more sophisticated error analysis
        error_memories = self.memory_manager.search_memories(
            agent_id=self.agent_id,
            query="error",
            limit=10
        )
        
        error_patterns = []
        for memory in error_memories:
            if "error" in memory.content.lower():
                error_patterns.append(memory.content[:100] + "...")
        
        return error_patterns[:3]  # Return top 3 error patterns
    
    def cleanup(self) -> None:
        """Cleanup agent resources."""
        self.logger.info(f"Cleaning up agent {self.agent_id}")
        # Subclasses can override to add specific cleanup logic
    
    def __str__(self) -> str:
        """String representation of the agent."""
        return f"{self.__class__.__name__}(id={self.agent_id}, state={self.state.value})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the agent."""
        return (
            f"{self.__class__.__name__}("
            f"id={self.agent_id}, "
            f"state={self.state.value}, "
            f"model={self.config.model}, "
            f"tools={self.config.tools}"
            f")"
        )