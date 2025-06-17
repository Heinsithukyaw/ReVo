"""Tool manager for reVoAgent platform."""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Type

from ..core.config import Config
from .base import BaseTool
from .git_tool import GitTool
from .browser_tool import BrowserTool
from .editor_tool import EditorTool
from .terminal_tool import TerminalTool


class ToolManager:
    """
    Manages tools for the reVoAgent platform.
    
    Features:
    - Tool registration and discovery
    - Tool execution with sandboxing
    - Tool dependency management
    - Tool performance monitoring
    """
    
    def __init__(self, config: Config):
        """Initialize tool manager."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Tool registry
        self.tool_classes: Dict[str, Type[BaseTool]] = {}
        self.tool_instances: Dict[str, BaseTool] = {}
        
        # Tool execution statistics
        self.tool_stats: Dict[str, Dict[str, Any]] = {}
        
        # Security settings
        self.sandbox_enabled = config.security.sandbox_enabled
        self.allowed_tools = set()  # Can be configured per agent
    
    def initialize(self) -> None:
        """Initialize the tool manager."""
        self.logger.info("Initializing tool manager")
        
        # Register default tools
        self._register_default_tools()
        
        # Initialize tool instances
        self._initialize_tool_instances()
    
    def _register_default_tools(self) -> None:
        """Register default tool classes."""
        default_tools = {
            "git": GitTool,
            "browser": BrowserTool,
            "editor": EditorTool,
            "terminal": TerminalTool,
        }
        
        for tool_name, tool_class in default_tools.items():
            self.register_tool_class(tool_name, tool_class)
    
    def _initialize_tool_instances(self) -> None:
        """Initialize instances of registered tools."""
        for tool_name, tool_class in self.tool_classes.items():
            try:
                tool_instance = tool_class(
                    tool_name=tool_name,
                    config=self.config,
                    sandbox_enabled=self.sandbox_enabled
                )
                
                self.tool_instances[tool_name] = tool_instance
                self.tool_stats[tool_name] = {
                    "executions": 0,
                    "successes": 0,
                    "failures": 0,
                    "total_time": 0.0
                }
                
                self.logger.debug(f"Initialized tool: {tool_name}")
                
            except Exception as e:
                self.logger.error(f"Failed to initialize tool {tool_name}: {e}")
    
    def register_tool_class(self, tool_name: str, tool_class: Type[BaseTool]) -> None:
        """Register a tool class."""
        self.tool_classes[tool_name] = tool_class
        self.logger.debug(f"Registered tool class: {tool_name}")
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tools."""
        return list(self.tool_instances.keys())
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """Get a tool instance by name."""
        return self.tool_instances.get(tool_name)
    
    def is_tool_available(self, tool_name: str) -> bool:
        """Check if a tool is available."""
        return tool_name in self.tool_instances
    
    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        timeout: Optional[float] = None
    ) -> Any:
        """
        Execute a tool with the given parameters.
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Tool parameters
            timeout: Execution timeout in seconds
            
        Returns:
            Tool execution result
        """
        import time
        start_time = time.time()
        
        if tool_name not in self.tool_instances:
            raise ValueError(f"Tool not available: {tool_name}")
        
        tool = self.tool_instances[tool_name]
        
        try:
            self.logger.debug(f"Executing tool {tool_name} with parameters: {parameters}")
            
            # Update statistics
            self.tool_stats[tool_name]["executions"] += 1
            
            # Execute tool with timeout
            if timeout:
                result = await asyncio.wait_for(
                    tool.execute(parameters),
                    timeout=timeout
                )
            else:
                result = await tool.execute(parameters)
            
            # Update success statistics
            execution_time = time.time() - start_time
            self.tool_stats[tool_name]["successes"] += 1
            self.tool_stats[tool_name]["total_time"] += execution_time
            
            self.logger.debug(f"Tool {tool_name} executed successfully in {execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            # Update failure statistics
            execution_time = time.time() - start_time
            self.tool_stats[tool_name]["failures"] += 1
            self.tool_stats[tool_name]["total_time"] += execution_time
            
            self.logger.error(f"Tool {tool_name} execution failed: {e}")
            raise
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a tool."""
        if tool_name not in self.tool_instances:
            return None
        
        tool = self.tool_instances[tool_name]
        stats = self.tool_stats[tool_name]
        
        return {
            "name": tool_name,
            "description": tool.get_description(),
            "parameters": tool.get_parameters(),
            "capabilities": tool.get_capabilities(),
            "statistics": {
                **stats,
                "success_rate": stats["successes"] / max(stats["executions"], 1),
                "average_time": stats["total_time"] / max(stats["executions"], 1)
            }
        }
    
    def get_all_tools_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all tools."""
        return {
            tool_name: self.get_tool_info(tool_name)
            for tool_name in self.tool_instances.keys()
        }
    
    def validate_tool_parameters(self, tool_name: str, parameters: Dict[str, Any]) -> bool:
        """Validate parameters for a tool."""
        if tool_name not in self.tool_instances:
            return False
        
        tool = self.tool_instances[tool_name]
        return tool.validate_parameters(parameters)
    
    def get_tool_dependencies(self, tool_name: str) -> List[str]:
        """Get dependencies for a tool."""
        if tool_name not in self.tool_instances:
            return []
        
        tool = self.tool_instances[tool_name]
        return tool.get_dependencies()
    
    async def check_tool_health(self, tool_name: str) -> Dict[str, Any]:
        """Check the health status of a tool."""
        if tool_name not in self.tool_instances:
            return {"status": "not_found", "healthy": False}
        
        tool = self.tool_instances[tool_name]
        
        try:
            health_status = await tool.health_check()
            return {
                "status": "healthy" if health_status else "unhealthy",
                "healthy": health_status,
                "last_check": time.time()
            }
        except Exception as e:
            return {
                "status": "error",
                "healthy": False,
                "error": str(e),
                "last_check": time.time()
            }
    
    async def check_all_tools_health(self) -> Dict[str, Dict[str, Any]]:
        """Check health status of all tools."""
        health_results = {}
        
        for tool_name in self.tool_instances.keys():
            health_results[tool_name] = await self.check_tool_health(tool_name)
        
        return health_results
    
    def get_status(self) -> Dict[str, Any]:
        """Get overall tool manager status."""
        total_executions = sum(stats["executions"] for stats in self.tool_stats.values())
        total_successes = sum(stats["successes"] for stats in self.tool_stats.values())
        total_failures = sum(stats["failures"] for stats in self.tool_stats.values())
        
        return {
            "total_tools": len(self.tool_instances),
            "available_tools": list(self.tool_instances.keys()),
            "sandbox_enabled": self.sandbox_enabled,
            "statistics": {
                "total_executions": total_executions,
                "total_successes": total_successes,
                "total_failures": total_failures,
                "overall_success_rate": total_successes / max(total_executions, 1)
            },
            "tool_stats": self.tool_stats
        }
    
    async def install_tool_dependencies(self, tool_name: str) -> bool:
        """Install dependencies for a tool."""
        if tool_name not in self.tool_instances:
            return False
        
        tool = self.tool_instances[tool_name]
        
        try:
            success = await tool.install_dependencies()
            if success:
                self.logger.info(f"Successfully installed dependencies for tool {tool_name}")
            else:
                self.logger.warning(f"Failed to install dependencies for tool {tool_name}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error installing dependencies for tool {tool_name}: {e}")
            return False
    
    def cleanup(self) -> None:
        """Cleanup tool manager resources."""
        self.logger.info("Cleaning up tool manager")
        
        # Cleanup all tool instances
        for tool_name, tool in self.tool_instances.items():
            try:
                tool.cleanup()
            except Exception as e:
                self.logger.error(f"Error cleaning up tool {tool_name}: {e}")
        
        self.tool_instances.clear()
        self.logger.info("Tool manager cleanup complete")