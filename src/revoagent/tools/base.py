"""Base tool class for reVoAgent platform."""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

from ..core.config import Config


class BaseTool(ABC):
    """
    Base class for all tools in the reVoAgent platform.
    
    Provides common functionality including:
    - Parameter validation
    - Dependency management
    - Health checking
    - Sandboxing support
    """
    
    def __init__(self, tool_name: str, config: Config, sandbox_enabled: bool = True):
        """Initialize base tool."""
        self.tool_name = tool_name
        self.config = config
        self.sandbox_enabled = sandbox_enabled
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Tool state
        self.is_initialized = False
        self.dependencies_installed = False
        
        # Initialize tool-specific components
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize tool-specific components. Override in subclasses."""
        self.is_initialized = True
    
    @abstractmethod
    async def execute(self, parameters: Dict[str, Any]) -> Any:
        """
        Execute the tool with given parameters. Must be implemented by subclasses.
        
        Args:
            parameters: Tool-specific parameters
            
        Returns:
            Tool execution result
        """
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Get a description of what this tool does."""
        pass
    
    @abstractmethod
    def get_parameters(self) -> Dict[str, Any]:
        """
        Get the parameter schema for this tool.
        
        Returns:
            Dictionary describing expected parameters
        """
        pass
    
    def get_capabilities(self) -> List[str]:
        """Get a list of capabilities this tool provides."""
        return ["basic_execution"]
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """
        Validate parameters for this tool.
        
        Args:
            parameters: Parameters to validate
            
        Returns:
            True if parameters are valid, False otherwise
        """
        try:
            required_params = self.get_parameters().get("required", [])
            
            # Check if all required parameters are present
            for param in required_params:
                if param not in parameters:
                    self.logger.error(f"Missing required parameter: {param}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating parameters: {e}")
            return False
    
    def get_dependencies(self) -> List[str]:
        """Get list of dependencies required by this tool."""
        return []
    
    async def install_dependencies(self) -> bool:
        """Install dependencies required by this tool."""
        dependencies = self.get_dependencies()
        
        if not dependencies:
            self.dependencies_installed = True
            return True
        
        try:
            self.logger.info(f"Installing dependencies for {self.tool_name}: {dependencies}")
            
            # Install each dependency
            for dependency in dependencies:
                success = await self._install_dependency(dependency)
                if not success:
                    self.logger.error(f"Failed to install dependency: {dependency}")
                    return False
            
            self.dependencies_installed = True
            self.logger.info(f"Successfully installed all dependencies for {self.tool_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error installing dependencies for {self.tool_name}: {e}")
            return False
    
    async def _install_dependency(self, dependency: str) -> bool:
        """Install a single dependency."""
        try:
            # This is a simplified implementation
            # In practice, you might want to use different package managers
            # or check if the dependency is already installed
            
            process = await asyncio.create_subprocess_exec(
                "pip", "install", dependency,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                self.logger.debug(f"Successfully installed dependency: {dependency}")
                return True
            else:
                self.logger.error(f"Failed to install dependency {dependency}: {stderr.decode()}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error installing dependency {dependency}: {e}")
            return False
    
    async def health_check(self) -> bool:
        """
        Perform a health check for this tool.
        
        Returns:
            True if tool is healthy, False otherwise
        """
        try:
            # Basic health check - ensure tool is initialized
            if not self.is_initialized:
                return False
            
            # Check dependencies if required
            dependencies = self.get_dependencies()
            if dependencies and not self.dependencies_installed:
                return False
            
            # Tool-specific health checks can be implemented in subclasses
            return await self._tool_specific_health_check()
            
        except Exception as e:
            self.logger.error(f"Health check failed for {self.tool_name}: {e}")
            return False
    
    async def _tool_specific_health_check(self) -> bool:
        """Tool-specific health check. Override in subclasses."""
        return True
    
    def _apply_sandbox_restrictions(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Apply sandbox restrictions to parameters."""
        if not self.sandbox_enabled:
            return parameters
        
        # Basic sandbox restrictions
        restricted_params = parameters.copy()
        
        # Remove potentially dangerous parameters
        dangerous_keys = ["rm", "delete", "format", "sudo", "admin"]
        for key in list(restricted_params.keys()):
            if any(dangerous in key.lower() for dangerous in dangerous_keys):
                self.logger.warning(f"Removing potentially dangerous parameter: {key}")
                del restricted_params[key]
        
        # Apply file system restrictions
        if "path" in restricted_params:
            path = str(restricted_params["path"])
            if self._is_path_restricted(path):
                self.logger.warning(f"Restricting access to path: {path}")
                restricted_params["path"] = self._get_safe_path(path)
        
        return restricted_params
    
    def _is_path_restricted(self, path: str) -> bool:
        """Check if a path is restricted in sandbox mode."""
        if not self.sandbox_enabled:
            return False
        
        restricted_paths = [
            "/etc", "/bin", "/sbin", "/usr/bin", "/usr/sbin",
            "/root", "/home", "/var", "/tmp"
        ]
        
        return any(path.startswith(restricted) for restricted in restricted_paths)
    
    def _get_safe_path(self, path: str) -> str:
        """Get a safe alternative path for sandbox mode."""
        # Redirect to a safe sandbox directory
        sandbox_dir = self.config.platform.temp_dir
        return f"{sandbox_dir}/sandbox/{path.lstrip('/')}"
    
    async def _execute_with_timeout(
        self,
        coro,
        timeout: Optional[float] = None
    ) -> Any:
        """Execute a coroutine with timeout."""
        if timeout:
            return await asyncio.wait_for(coro, timeout=timeout)
        else:
            return await coro
    
    def cleanup(self) -> None:
        """Cleanup tool resources. Override in subclasses if needed."""
        self.logger.debug(f"Cleaning up tool: {self.tool_name}")
    
    def __str__(self) -> str:
        """String representation of the tool."""
        return f"{self.__class__.__name__}(name={self.tool_name})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the tool."""
        return (
            f"{self.__class__.__name__}("
            f"name={self.tool_name}, "
            f"initialized={self.is_initialized}, "
            f"sandbox_enabled={self.sandbox_enabled}"
            f")"
        )