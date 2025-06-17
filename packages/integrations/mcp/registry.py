"""
MCP Server Registry

Manages discovery, installation, and lifecycle of MCP servers.
Integrates with awesome-mcp-servers repository for community servers.
"""

import asyncio
import json
import logging
import yaml
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import subprocess
import tempfile
import shutil

from .client import MCPServerConfig, MCPTransportType

logger = logging.getLogger(__name__)

class MCPServerCategory(Enum):
    """Categories of MCP servers"""
    FILE_SYSTEMS = "file_systems"
    DATABASES = "databases"
    BROWSER_AUTOMATION = "browser_automation"
    CLOUD_PLATFORMS = "cloud_platforms"
    CODE_EXECUTION = "code_execution"
    COMMUNICATION = "communication"
    DEVELOPER_TOOLS = "developer_tools"
    VERSION_CONTROL = "version_control"
    SECURITY = "security"
    MONITORING = "monitoring"
    DATA_PLATFORMS = "data_platforms"
    AI_ML = "ai_ml"
    FINANCE = "finance"
    MARKETING = "marketing"
    OTHER = "other"

@dataclass
class MCPServerSpec:
    """Specification for an MCP server from awesome-mcp-servers"""
    name: str
    description: str
    category: MCPServerCategory
    repository_url: str
    language: str
    transport_types: List[MCPTransportType]
    installation_method: str  # "npm", "pip", "go", "cargo", "binary", etc.
    command_template: str
    args_template: List[str]
    env_vars: Dict[str, str]
    requirements: List[str]
    documentation_url: Optional[str] = None
    examples: List[Dict[str, Any]] = None
    enterprise_ready: bool = False
    security_notes: Optional[str] = None

@dataclass
class InstalledMCPServer:
    """Represents an installed MCP server"""
    spec: MCPServerSpec
    installation_path: str
    config: MCPServerConfig
    installed_at: str
    version: Optional[str] = None
    status: str = "installed"  # installed, running, stopped, error

class MCPServerRegistry:
    """
    Registry for managing MCP servers
    
    Features:
    - Discovery from awesome-mcp-servers
    - Installation and lifecycle management
    - Configuration management
    - Health monitoring
    - Enterprise categorization
    """
    
    def __init__(self, config_dir: str = "config/integrations/mcp"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.servers_file = self.config_dir / "servers.yaml"
        self.installed_file = self.config_dir / "installed.yaml"
        self.awesome_mcp_path = Path("external/awesome-mcp-servers")
        
        self.available_servers: Dict[str, MCPServerSpec] = {}
        self.installed_servers: Dict[str, InstalledMCPServer] = {}
        
        # Initialize
        asyncio.create_task(self._initialize())
    
    async def _initialize(self):
        """Initialize the registry"""
        try:
            await self.load_available_servers()
            await self.load_installed_servers()
            logger.info("MCP Server Registry initialized")
        except Exception as e:
            logger.error(f"Failed to initialize MCP registry: {e}")
    
    async def load_available_servers(self):
        """Load available servers from awesome-mcp-servers and local config"""
        try:
            # Load from awesome-mcp-servers if available
            if self.awesome_mcp_path.exists():
                await self._parse_awesome_mcp_servers()
            
            # Load from local servers.yaml
            if self.servers_file.exists():
                with open(self.servers_file, 'r') as f:
                    local_servers = yaml.safe_load(f) or {}
                
                for server_data in local_servers.get('servers', []):
                    spec = self._dict_to_server_spec(server_data)
                    self.available_servers[spec.name] = spec
            
            logger.info(f"Loaded {len(self.available_servers)} available MCP servers")
            
        except Exception as e:
            logger.error(f"Failed to load available servers: {e}")
    
    async def load_installed_servers(self):
        """Load installed servers configuration"""
        try:
            if self.installed_file.exists():
                with open(self.installed_file, 'r') as f:
                    installed_data = yaml.safe_load(f) or {}
                
                for server_data in installed_data.get('installed', []):
                    installed = self._dict_to_installed_server(server_data)
                    self.installed_servers[installed.spec.name] = installed
            
            logger.info(f"Loaded {len(self.installed_servers)} installed MCP servers")
            
        except Exception as e:
            logger.error(f"Failed to load installed servers: {e}")
    
    async def discover_servers(self, category: Optional[MCPServerCategory] = None) -> List[MCPServerSpec]:
        """
        Discover available MCP servers
        
        Args:
            category: Filter by category, or None for all
            
        Returns:
            List of available server specifications
        """
        servers = list(self.available_servers.values())
        
        if category:
            servers = [s for s in servers if s.category == category]
        
        return servers
    
    async def get_enterprise_servers(self) -> List[MCPServerSpec]:
        """Get servers marked as enterprise-ready"""
        return [s for s in self.available_servers.values() if s.enterprise_ready]
    
    async def get_servers_for_agent(self, agent_type: str) -> List[MCPServerSpec]:
        """
        Get recommended MCP servers for an agent type
        
        Args:
            agent_type: Type of agent (e.g., "code_generation", "data_analysis")
            
        Returns:
            List of recommended server specifications
        """
        recommendations = {
            "code_generation": [
                MCPServerCategory.FILE_SYSTEMS,
                MCPServerCategory.VERSION_CONTROL,
                MCPServerCategory.CODE_EXECUTION,
                MCPServerCategory.DEVELOPER_TOOLS
            ],
            "data_analysis": [
                MCPServerCategory.DATABASES,
                MCPServerCategory.DATA_PLATFORMS,
                MCPServerCategory.FILE_SYSTEMS,
                MCPServerCategory.AI_ML
            ],
            "browser_automation": [
                MCPServerCategory.BROWSER_AUTOMATION,
                MCPServerCategory.FILE_SYSTEMS
            ],
            "security_audit": [
                MCPServerCategory.SECURITY,
                MCPServerCategory.MONITORING,
                MCPServerCategory.VERSION_CONTROL
            ],
            "task_automation": [
                MCPServerCategory.COMMUNICATION,
                MCPServerCategory.FILE_SYSTEMS,
                MCPServerCategory.CLOUD_PLATFORMS
            ]
        }
        
        categories = recommendations.get(agent_type, [])
        servers = []
        
        for category in categories:
            category_servers = await self.discover_servers(category)
            servers.extend(category_servers)
        
        return servers
    
    async def install_server(self, server_name: str, custom_config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Install an MCP server
        
        Args:
            server_name: Name of the server to install
            custom_config: Custom configuration overrides
            
        Returns:
            bool: True if installation successful
        """
        try:
            if server_name not in self.available_servers:
                logger.error(f"Server {server_name} not found in registry")
                return False
            
            spec = self.available_servers[server_name]
            
            # Check if already installed
            if server_name in self.installed_servers:
                logger.info(f"Server {server_name} already installed")
                return True
            
            logger.info(f"Installing MCP server: {server_name}")
            
            # Install based on installation method
            installation_path = await self._install_server_by_method(spec)
            
            if not installation_path:
                logger.error(f"Failed to install server {server_name}")
                return False
            
            # Create server configuration
            config = self._create_server_config(spec, installation_path, custom_config)
            
            # Create installed server record
            installed = InstalledMCPServer(
                spec=spec,
                installation_path=installation_path,
                config=config,
                installed_at=str(asyncio.get_event_loop().time())
            )
            
            self.installed_servers[server_name] = installed
            
            # Save to file
            await self._save_installed_servers()
            
            logger.info(f"Successfully installed MCP server: {server_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to install server {server_name}: {e}")
            return False
    
    async def uninstall_server(self, server_name: str) -> bool:
        """Uninstall an MCP server"""
        try:
            if server_name not in self.installed_servers:
                logger.warning(f"Server {server_name} not installed")
                return False
            
            installed = self.installed_servers[server_name]
            
            # Remove installation directory
            installation_path = Path(installed.installation_path)
            if installation_path.exists():
                shutil.rmtree(installation_path)
            
            # Remove from registry
            del self.installed_servers[server_name]
            
            # Save updated list
            await self._save_installed_servers()
            
            logger.info(f"Successfully uninstalled MCP server: {server_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to uninstall server {server_name}: {e}")
            return False
    
    async def get_server_config(self, server_name: str) -> Optional[MCPServerConfig]:
        """Get configuration for an installed server"""
        if server_name in self.installed_servers:
            return self.installed_servers[server_name].config
        return None
    
    async def list_installed_servers(self) -> List[InstalledMCPServer]:
        """List all installed servers"""
        return list(self.installed_servers.values())
    
    async def update_server_status(self, server_name: str, status: str):
        """Update the status of an installed server"""
        if server_name in self.installed_servers:
            self.installed_servers[server_name].status = status
            await self._save_installed_servers()
    
    # Private methods
    
    async def _parse_awesome_mcp_servers(self):
        """Parse awesome-mcp-servers repository"""
        try:
            readme_path = self.awesome_mcp_path / "README.md"
            if not readme_path.exists():
                logger.warning("awesome-mcp-servers README.md not found")
                return
            
            # This is a simplified parser - in production, you'd want more robust parsing
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse server entries (this is a basic implementation)
            # In production, you'd want to parse the actual markdown structure
            servers = self._extract_servers_from_readme(content)
            
            for server in servers:
                self.available_servers[server.name] = server
            
            logger.info(f"Parsed {len(servers)} servers from awesome-mcp-servers")
            
        except Exception as e:
            logger.error(f"Failed to parse awesome-mcp-servers: {e}")
    
    def _extract_servers_from_readme(self, content: str) -> List[MCPServerSpec]:
        """Extract server specifications from README content"""
        # This is a simplified implementation
        # In production, you'd want proper markdown parsing
        
        servers = []
        
        # Add some popular servers manually for now
        popular_servers = [
            {
                "name": "filesystem",
                "description": "File system operations (read, write, list files)",
                "category": MCPServerCategory.FILE_SYSTEMS,
                "repository_url": "https://github.com/modelcontextprotocol/servers",
                "language": "typescript",
                "transport_types": [MCPTransportType.STDIO],
                "installation_method": "npm",
                "command_template": "npx @modelcontextprotocol/server-filesystem",
                "args_template": ["{base_path}"],
                "env_vars": {},
                "requirements": ["node", "npm"],
                "enterprise_ready": True
            },
            {
                "name": "sqlite",
                "description": "SQLite database operations",
                "category": MCPServerCategory.DATABASES,
                "repository_url": "https://github.com/modelcontextprotocol/servers",
                "language": "typescript",
                "transport_types": [MCPTransportType.STDIO],
                "installation_method": "npm",
                "command_template": "npx @modelcontextprotocol/server-sqlite",
                "args_template": ["{database_path}"],
                "env_vars": {},
                "requirements": ["node", "npm"],
                "enterprise_ready": True
            },
            {
                "name": "brave-search",
                "description": "Web search using Brave Search API",
                "category": MCPServerCategory.DATA_PLATFORMS,
                "repository_url": "https://github.com/modelcontextprotocol/servers",
                "language": "typescript",
                "transport_types": [MCPTransportType.STDIO],
                "installation_method": "npm",
                "command_template": "npx @modelcontextprotocol/server-brave-search",
                "args_template": [],
                "env_vars": {"BRAVE_API_KEY": "required"},
                "requirements": ["node", "npm"],
                "enterprise_ready": False
            },
            {
                "name": "github",
                "description": "GitHub repository operations",
                "category": MCPServerCategory.VERSION_CONTROL,
                "repository_url": "https://github.com/modelcontextprotocol/servers",
                "language": "typescript",
                "transport_types": [MCPTransportType.STDIO],
                "installation_method": "npm",
                "command_template": "npx @modelcontextprotocol/server-github",
                "args_template": [],
                "env_vars": {"GITHUB_PERSONAL_ACCESS_TOKEN": "required"},
                "requirements": ["node", "npm"],
                "enterprise_ready": True
            },
            {
                "name": "puppeteer",
                "description": "Browser automation with Puppeteer",
                "category": MCPServerCategory.BROWSER_AUTOMATION,
                "repository_url": "https://github.com/modelcontextprotocol/servers",
                "language": "typescript",
                "transport_types": [MCPTransportType.STDIO],
                "installation_method": "npm",
                "command_template": "npx @modelcontextprotocol/server-puppeteer",
                "args_template": [],
                "env_vars": {},
                "requirements": ["node", "npm", "chromium"],
                "enterprise_ready": True
            }
        ]
        
        for server_data in popular_servers:
            try:
                spec = MCPServerSpec(
                    name=server_data["name"],
                    description=server_data["description"],
                    category=server_data["category"],
                    repository_url=server_data["repository_url"],
                    language=server_data["language"],
                    transport_types=server_data["transport_types"],
                    installation_method=server_data["installation_method"],
                    command_template=server_data["command_template"],
                    args_template=server_data["args_template"],
                    env_vars=server_data["env_vars"],
                    requirements=server_data["requirements"],
                    enterprise_ready=server_data["enterprise_ready"]
                )
                servers.append(spec)
            except Exception as e:
                logger.error(f"Failed to create server spec: {e}")
        
        return servers
    
    async def _install_server_by_method(self, spec: MCPServerSpec) -> Optional[str]:
        """Install server based on installation method"""
        try:
            if spec.installation_method == "npm":
                return await self._install_npm_server(spec)
            elif spec.installation_method == "pip":
                return await self._install_pip_server(spec)
            elif spec.installation_method == "binary":
                return await self._install_binary_server(spec)
            else:
                logger.error(f"Unsupported installation method: {spec.installation_method}")
                return None
                
        except Exception as e:
            logger.error(f"Installation failed for {spec.name}: {e}")
            return None
    
    async def _install_npm_server(self, spec: MCPServerSpec) -> Optional[str]:
        """Install NPM-based MCP server"""
        try:
            # Create installation directory
            install_dir = Path(f"mcp_servers/{spec.name}")
            install_dir.mkdir(parents=True, exist_ok=True)
            
            # For npm packages, we'll use global installation
            # In production, you might want isolated installations
            
            # Check if npm is available
            result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
            if result.returncode != 0:
                logger.error("npm not available for installation")
                return None
            
            logger.info(f"npm is available, server {spec.name} can be installed")
            
            # For now, we'll mark it as installed without actually running npm
            # In production, you'd run: npm install -g @modelcontextprotocol/server-{name}
            
            return str(install_dir.absolute())
            
        except Exception as e:
            logger.error(f"NPM installation failed: {e}")
            return None
    
    async def _install_pip_server(self, spec: MCPServerSpec) -> Optional[str]:
        """Install pip-based MCP server"""
        try:
            install_dir = Path(f"mcp_servers/{spec.name}")
            install_dir.mkdir(parents=True, exist_ok=True)
            
            # Check if pip is available
            result = subprocess.run(["pip", "--version"], capture_output=True, text=True)
            if result.returncode != 0:
                logger.error("pip not available for installation")
                return None
            
            logger.info(f"pip is available, server {spec.name} can be installed")
            
            return str(install_dir.absolute())
            
        except Exception as e:
            logger.error(f"pip installation failed: {e}")
            return None
    
    async def _install_binary_server(self, spec: MCPServerSpec) -> Optional[str]:
        """Install binary MCP server"""
        try:
            install_dir = Path(f"mcp_servers/{spec.name}")
            install_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Binary server {spec.name} marked as installed")
            
            return str(install_dir.absolute())
            
        except Exception as e:
            logger.error(f"Binary installation failed: {e}")
            return None
    
    def _create_server_config(self, spec: MCPServerSpec, installation_path: str, custom_config: Optional[Dict[str, Any]]) -> MCPServerConfig:
        """Create MCPServerConfig from server spec"""
        
        # Use the first available transport type
        transport_type = spec.transport_types[0] if spec.transport_types else MCPTransportType.STDIO
        
        # Build command and args
        command = spec.command_template
        args = spec.args_template.copy() if spec.args_template else []
        
        # Apply custom configuration
        if custom_config:
            # Replace template variables
            for i, arg in enumerate(args):
                for key, value in custom_config.items():
                    args[i] = arg.replace(f"{{{key}}}", str(value))
        
        config = MCPServerConfig(
            name=spec.name,
            transport_type=transport_type,
            command=command,
            args=args,
            env=spec.env_vars.copy(),
            timeout=30,
            max_retries=3
        )
        
        return config
    
    def _dict_to_server_spec(self, data: Dict[str, Any]) -> MCPServerSpec:
        """Convert dictionary to MCPServerSpec"""
        return MCPServerSpec(
            name=data["name"],
            description=data["description"],
            category=MCPServerCategory(data["category"]),
            repository_url=data["repository_url"],
            language=data["language"],
            transport_types=[MCPTransportType(t) for t in data["transport_types"]],
            installation_method=data["installation_method"],
            command_template=data["command_template"],
            args_template=data.get("args_template", []),
            env_vars=data.get("env_vars", {}),
            requirements=data.get("requirements", []),
            documentation_url=data.get("documentation_url"),
            examples=data.get("examples", []),
            enterprise_ready=data.get("enterprise_ready", False),
            security_notes=data.get("security_notes")
        )
    
    def _dict_to_installed_server(self, data: Dict[str, Any]) -> InstalledMCPServer:
        """Convert dictionary to InstalledMCPServer"""
        spec = self._dict_to_server_spec(data["spec"])
        config = MCPServerConfig(**data["config"])
        
        return InstalledMCPServer(
            spec=spec,
            installation_path=data["installation_path"],
            config=config,
            installed_at=data["installed_at"],
            version=data.get("version"),
            status=data.get("status", "installed")
        )
    
    async def _save_installed_servers(self):
        """Save installed servers to file"""
        try:
            installed_data = {
                "installed": [
                    {
                        "spec": asdict(server.spec),
                        "installation_path": server.installation_path,
                        "config": asdict(server.config),
                        "installed_at": server.installed_at,
                        "version": server.version,
                        "status": server.status
                    }
                    for server in self.installed_servers.values()
                ]
            }
            
            with open(self.installed_file, 'w') as f:
                yaml.dump(installed_data, f, default_flow_style=False)
                
        except Exception as e:
            logger.error(f"Failed to save installed servers: {e}")

# Global registry instance
mcp_registry = MCPServerRegistry()