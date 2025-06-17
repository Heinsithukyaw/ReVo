"""
MCP (Model Context Protocol) Integration Package

This package provides enterprise-grade MCP integration for reVoAgent,
enabling seamless connection to hundreds of external tools and services.

Key Components:
- MCPClient: Core client for MCP server communication
- MCPRegistry: Server discovery and management
- MCPSecurity: Multi-tenant security and access control
- Protocol implementations: stdio, SSE, WebSocket transports
"""

from .client import MCPClient
from .registry import MCPServerRegistry
from .security import MCPSecurityManager

__version__ = "1.0.0"
__all__ = ["MCPClient", "MCPServerRegistry", "MCPSecurityManager"]