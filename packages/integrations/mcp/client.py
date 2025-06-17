"""
Enterprise MCP Client Implementation

Provides robust, multi-tenant MCP client with security, monitoring,
and enterprise features for reVoAgent platform.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

class MCPTransportType(Enum):
    """Supported MCP transport types"""
    STDIO = "stdio"
    SSE = "sse" 
    WEBSOCKET = "websocket"

@dataclass
class MCPServerConfig:
    """Configuration for an MCP server connection"""
    name: str
    transport_type: MCPTransportType
    command: Optional[str] = None  # For stdio transport
    url: Optional[str] = None      # For SSE/WebSocket transport
    args: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None
    timeout: int = 30
    max_retries: int = 3
    tenant_id: Optional[str] = None
    security_config: Optional[Dict[str, Any]] = None

@dataclass
class MCPTool:
    """Represents an MCP tool"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    server_name: str

@dataclass
class MCPResource:
    """Represents an MCP resource"""
    uri: str
    name: str
    description: Optional[str] = None
    mime_type: Optional[str] = None
    server_name: Optional[str] = None

class MCPClient:
    """
    Enterprise-grade MCP client with multi-tenant support
    
    Features:
    - Multi-tenant isolation
    - Security and access control
    - Connection pooling and management
    - Health monitoring
    - Audit logging
    """
    
    def __init__(self, tenant_id: Optional[str] = None):
        self.tenant_id = tenant_id or "default"
        self.servers: Dict[str, Any] = {}
        self.connections: Dict[str, Any] = {}
        self.tools_cache: Dict[str, List[MCPTool]] = {}
        self.resources_cache: Dict[str, List[MCPResource]] = {}
        self.session_id = str(uuid.uuid4())
        
        # Import security manager
        from .security import MCPSecurityManager
        self.security_manager = MCPSecurityManager(self.tenant_id)
        
        logger.info(f"MCPClient initialized for tenant: {self.tenant_id}, session: {self.session_id}")
    
    async def connect_server(self, config: MCPServerConfig) -> bool:
        """
        Connect to an MCP server with security validation
        
        Args:
            config: Server configuration
            
        Returns:
            bool: True if connection successful
        """
        try:
            # Security validation
            if not await self.security_manager.validate_server_access(config):
                logger.warning(f"Access denied to server {config.name} for tenant {self.tenant_id}")
                return False
            
            # Check if already connected
            if config.name in self.connections:
                logger.info(f"Server {config.name} already connected")
                return True
            
            # Store server config
            self.servers[config.name] = config
            
            # Create connection based on transport type
            if config.transport_type == MCPTransportType.STDIO:
                connection = await self._create_stdio_connection(config)
            elif config.transport_type == MCPTransportType.SSE:
                connection = await self._create_sse_connection(config)
            elif config.transport_type == MCPTransportType.WEBSOCKET:
                connection = await self._create_websocket_connection(config)
            else:
                raise ValueError(f"Unsupported transport type: {config.transport_type}")
            
            if connection:
                self.connections[config.name] = connection
                
                # Initialize server (handshake)
                await self._initialize_server(config.name)
                
                # Cache tools and resources
                await self._refresh_server_capabilities(config.name)
                
                logger.info(f"Successfully connected to MCP server: {config.name}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to connect to server {config.name}: {e}")
            return False
    
    async def disconnect_server(self, server_name: str) -> bool:
        """Disconnect from an MCP server"""
        try:
            if server_name in self.connections:
                connection = self.connections[server_name]
                await self._close_connection(connection)
                del self.connections[server_name]
                
                # Clear caches
                self.tools_cache.pop(server_name, None)
                self.resources_cache.pop(server_name, None)
                
                logger.info(f"Disconnected from MCP server: {server_name}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to disconnect from server {server_name}: {e}")
            return False
    
    async def list_tools(self, server_name: Optional[str] = None) -> List[MCPTool]:
        """
        List available tools from a specific server or all servers
        
        Args:
            server_name: Specific server name, or None for all servers
            
        Returns:
            List of available tools
        """
        if server_name:
            return self.tools_cache.get(server_name, [])
        
        # Return tools from all connected servers
        all_tools = []
        for tools in self.tools_cache.values():
            all_tools.extend(tools)
        
        return all_tools
    
    async def list_resources(self, server_name: Optional[str] = None) -> List[MCPResource]:
        """List available resources from a specific server or all servers"""
        if server_name:
            return self.resources_cache.get(server_name, [])
        
        # Return resources from all connected servers
        all_resources = []
        for resources in self.resources_cache.values():
            all_resources.extend(resources)
        
        return all_resources
    
    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a tool on an MCP server
        
        Args:
            server_name: Name of the MCP server
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        try:
            # Validate access
            if not await self.security_manager.validate_tool_access(server_name, tool_name):
                raise PermissionError(f"Access denied to tool {tool_name} on server {server_name}")
            
            # Check connection
            if server_name not in self.connections:
                raise ConnectionError(f"Not connected to server: {server_name}")
            
            # Validate tool exists
            tools = await self.list_tools(server_name)
            tool = next((t for t in tools if t.name == tool_name), None)
            if not tool:
                raise ValueError(f"Tool {tool_name} not found on server {server_name}")
            
            # Execute tool
            connection = self.connections[server_name]
            request = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments or {}
                }
            }
            
            result = await self._send_request(connection, request)
            
            # Log tool usage for audit
            await self._log_tool_usage(server_name, tool_name, arguments, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Tool execution failed: {server_name}.{tool_name} - {e}")
            raise
    
    async def read_resource(self, server_name: str, uri: str) -> Dict[str, Any]:
        """Read a resource from an MCP server"""
        try:
            # Validate access
            if not await self.security_manager.validate_resource_access(server_name, uri):
                raise PermissionError(f"Access denied to resource {uri} on server {server_name}")
            
            # Check connection
            if server_name not in self.connections:
                raise ConnectionError(f"Not connected to server: {server_name}")
            
            connection = self.connections[server_name]
            request = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "resources/read",
                "params": {
                    "uri": uri
                }
            }
            
            result = await self._send_request(connection, request)
            
            # Log resource access for audit
            await self._log_resource_access(server_name, uri, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Resource read failed: {server_name}:{uri} - {e}")
            raise
    
    async def get_server_status(self, server_name: str) -> Dict[str, Any]:
        """Get status of an MCP server"""
        try:
            if server_name not in self.connections:
                return {"status": "disconnected", "server": server_name}
            
            connection = self.connections[server_name]
            
            # Send ping to check health
            request = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "ping"
            }
            
            start_time = datetime.now()
            result = await self._send_request(connection, request)
            response_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "status": "connected",
                "server": server_name,
                "response_time_ms": response_time * 1000,
                "tools_count": len(self.tools_cache.get(server_name, [])),
                "resources_count": len(self.resources_cache.get(server_name, [])),
                "last_ping": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "server": server_name,
                "error": str(e)
            }
    
    async def refresh_capabilities(self, server_name: Optional[str] = None):
        """Refresh cached tools and resources for servers"""
        if server_name:
            await self._refresh_server_capabilities(server_name)
        else:
            for name in self.connections.keys():
                await self._refresh_server_capabilities(name)
    
    # Private methods for connection management
    
    async def _create_stdio_connection(self, config: MCPServerConfig):
        """Create stdio-based MCP connection"""
        try:
            from .protocols.stdio import StdioMCPConnection
            connection = StdioMCPConnection(config)
            await connection.connect()
            return connection
        except ImportError:
            # Fallback implementation
            logger.warning("StdioMCPConnection not available, using mock")
            return MockMCPConnection(config)
    
    async def _create_sse_connection(self, config: MCPServerConfig):
        """Create SSE-based MCP connection"""
        try:
            from .protocols.sse import SSEMCPConnection
            connection = SSEMCPConnection(config)
            await connection.connect()
            return connection
        except ImportError:
            logger.warning("SSEMCPConnection not available, using mock")
            return MockMCPConnection(config)
    
    async def _create_websocket_connection(self, config: MCPServerConfig):
        """Create WebSocket-based MCP connection"""
        try:
            from .protocols.websocket import WebSocketMCPConnection
            connection = WebSocketMCPConnection(config)
            await connection.connect()
            return connection
        except ImportError:
            logger.warning("WebSocketMCPConnection not available, using mock")
            return MockMCPConnection(config)
    
    async def _initialize_server(self, server_name: str):
        """Initialize MCP server with handshake"""
        connection = self.connections[server_name]
        
        # Send initialize request
        request = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "resources": {}
                },
                "clientInfo": {
                    "name": "reVoAgent",
                    "version": "2.0.0"
                }
            }
        }
        
        result = await self._send_request(connection, request)
        logger.info(f"Server {server_name} initialized: {result}")
    
    async def _refresh_server_capabilities(self, server_name: str):
        """Refresh tools and resources cache for a server"""
        try:
            connection = self.connections[server_name]
            
            # Get tools
            tools_request = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "tools/list"
            }
            
            tools_result = await self._send_request(connection, tools_request)
            tools = []
            
            if "result" in tools_result and "tools" in tools_result["result"]:
                for tool_data in tools_result["result"]["tools"]:
                    tool = MCPTool(
                        name=tool_data["name"],
                        description=tool_data.get("description", ""),
                        input_schema=tool_data.get("inputSchema", {}),
                        server_name=server_name
                    )
                    tools.append(tool)
            
            self.tools_cache[server_name] = tools
            
            # Get resources
            resources_request = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "resources/list"
            }
            
            resources_result = await self._send_request(connection, resources_request)
            resources = []
            
            if "result" in resources_result and "resources" in resources_result["result"]:
                for resource_data in resources_result["result"]["resources"]:
                    resource = MCPResource(
                        uri=resource_data["uri"],
                        name=resource_data.get("name", ""),
                        description=resource_data.get("description"),
                        mime_type=resource_data.get("mimeType"),
                        server_name=server_name
                    )
                    resources.append(resource)
            
            self.resources_cache[server_name] = resources
            
            logger.info(f"Refreshed capabilities for {server_name}: {len(tools)} tools, {len(resources)} resources")
            
        except Exception as e:
            logger.error(f"Failed to refresh capabilities for {server_name}: {e}")
    
    async def _send_request(self, connection, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send request to MCP server and get response"""
        try:
            return await connection.send_request(request)
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise
    
    async def _close_connection(self, connection):
        """Close MCP connection"""
        try:
            await connection.close()
        except Exception as e:
            logger.error(f"Error closing connection: {e}")
    
    async def _log_tool_usage(self, server_name: str, tool_name: str, arguments: Dict[str, Any], result: Dict[str, Any]):
        """Log tool usage for audit purposes"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "tenant_id": self.tenant_id,
            "session_id": self.session_id,
            "action": "tool_call",
            "server_name": server_name,
            "tool_name": tool_name,
            "arguments": arguments,
            "success": "error" not in result
        }
        
        # In production, this would go to a proper audit log
        logger.info(f"Tool usage: {json.dumps(log_entry)}")
    
    async def _log_resource_access(self, server_name: str, uri: str, result: Dict[str, Any]):
        """Log resource access for audit purposes"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "tenant_id": self.tenant_id,
            "session_id": self.session_id,
            "action": "resource_read",
            "server_name": server_name,
            "resource_uri": uri,
            "success": "error" not in result
        }
        
        logger.info(f"Resource access: {json.dumps(log_entry)}")

class MockMCPConnection:
    """Mock MCP connection for testing and fallback"""
    
    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.connected = False
    
    async def connect(self):
        """Mock connect"""
        self.connected = True
        logger.info(f"Mock connection established to {self.config.name}")
    
    async def send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Mock request handling"""
        method = request.get("method", "")
        
        if method == "initialize":
            return {
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}, "resources": {}},
                    "serverInfo": {"name": f"Mock {self.config.name}", "version": "1.0.0"}
                }
            }
        elif method == "tools/list":
            return {
                "result": {
                    "tools": [
                        {
                            "name": "mock_tool",
                            "description": "A mock tool for testing",
                            "inputSchema": {"type": "object", "properties": {}}
                        }
                    ]
                }
            }
        elif method == "resources/list":
            return {
                "result": {
                    "resources": [
                        {
                            "uri": f"mock://{self.config.name}/resource",
                            "name": "Mock Resource",
                            "description": "A mock resource for testing"
                        }
                    ]
                }
            }
        elif method == "tools/call":
            return {
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Mock result from {self.config.name}"
                        }
                    ]
                }
            }
        elif method == "resources/read":
            return {
                "result": {
                    "contents": [
                        {
                            "uri": request["params"]["uri"],
                            "mimeType": "text/plain",
                            "text": "Mock resource content"
                        }
                    ]
                }
            }
        elif method == "ping":
            return {"result": "pong"}
        
        return {"error": {"code": -32601, "message": "Method not found"}}
    
    async def close(self):
        """Mock close"""
        self.connected = False
        logger.info(f"Mock connection closed to {self.config.name}")