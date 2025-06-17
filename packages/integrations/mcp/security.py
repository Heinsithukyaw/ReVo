"""
MCP Security Manager

Provides enterprise-grade security for MCP server interactions including:
- Multi-tenant access control
- Resource and tool permissions
- Audit logging
- Security policies
"""

import logging
import json
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import hashlib
import hmac

from .client import MCPServerConfig

logger = logging.getLogger(__name__)

class SecurityLevel(Enum):
    """Security levels for MCP operations"""
    PUBLIC = "public"           # No restrictions
    RESTRICTED = "restricted"   # Basic access control
    CONFIDENTIAL = "confidential"  # Strict access control
    SECRET = "secret"          # Maximum security

class PermissionType(Enum):
    """Types of permissions for MCP operations"""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"

@dataclass
class SecurityPolicy:
    """Security policy for MCP operations"""
    tenant_id: str
    server_name: str
    allowed_tools: Set[str]
    denied_tools: Set[str]
    allowed_resources: Set[str]
    denied_resources: Set[str]
    permissions: Set[PermissionType]
    security_level: SecurityLevel
    max_requests_per_minute: int = 100
    require_approval: bool = False
    audit_all_operations: bool = True

@dataclass
class SecurityContext:
    """Security context for an operation"""
    tenant_id: str
    user_id: Optional[str]
    session_id: str
    operation_type: str
    resource_path: Optional[str]
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class MCPSecurityManager:
    """
    Enterprise security manager for MCP operations
    
    Features:
    - Multi-tenant access control
    - Role-based permissions
    - Rate limiting
    - Audit logging
    - Security policy enforcement
    """
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.policies: Dict[str, SecurityPolicy] = {}
        self.rate_limits: Dict[str, List[datetime]] = {}
        self.audit_log: List[Dict[str, Any]] = []
        
        # Load security policies
        self._load_security_policies()
    
    def _load_security_policies(self):
        """Load security policies for the tenant"""
        try:
            # In production, this would load from a secure configuration store
            # For now, we'll create default policies
            
            default_policies = {
                "filesystem": SecurityPolicy(
                    tenant_id=self.tenant_id,
                    server_name="filesystem",
                    allowed_tools={"read_file", "write_file", "list_directory"},
                    denied_tools={"delete_file", "execute_file"},
                    allowed_resources={f"file://{self.tenant_id}/*"},
                    denied_resources={"file:///etc/*", "file:///root/*"},
                    permissions={PermissionType.READ, PermissionType.WRITE},
                    security_level=SecurityLevel.RESTRICTED,
                    max_requests_per_minute=50
                ),
                "sqlite": SecurityPolicy(
                    tenant_id=self.tenant_id,
                    server_name="sqlite",
                    allowed_tools={"query", "execute"},
                    denied_tools={"drop_table", "delete_database"},
                    allowed_resources={f"sqlite://{self.tenant_id}/*"},
                    denied_resources={"sqlite:///system/*"},
                    permissions={PermissionType.READ, PermissionType.WRITE},
                    security_level=SecurityLevel.CONFIDENTIAL,
                    max_requests_per_minute=30
                ),
                "github": SecurityPolicy(
                    tenant_id=self.tenant_id,
                    server_name="github",
                    allowed_tools={"get_repository", "list_files", "read_file"},
                    denied_tools={"delete_repository", "force_push"},
                    allowed_resources={"github://*/public/*"},
                    denied_resources={"github://*/private/*"},
                    permissions={PermissionType.READ},
                    security_level=SecurityLevel.RESTRICTED,
                    max_requests_per_minute=20
                ),
                "puppeteer": SecurityPolicy(
                    tenant_id=self.tenant_id,
                    server_name="puppeteer",
                    allowed_tools={"navigate", "screenshot", "get_content"},
                    denied_tools={"execute_script", "download_file"},
                    allowed_resources={"https://*", "http://localhost:*"},
                    denied_resources={"file://*", "ftp://*"},
                    permissions={PermissionType.READ},
                    security_level=SecurityLevel.RESTRICTED,
                    max_requests_per_minute=10
                )
            }
            
            self.policies.update(default_policies)
            
            logger.info(f"Loaded {len(self.policies)} security policies for tenant {self.tenant_id}")
            
        except Exception as e:
            logger.error(f"Failed to load security policies: {e}")
    
    async def validate_server_access(self, config: MCPServerConfig) -> bool:
        """
        Validate if tenant can access an MCP server
        
        Args:
            config: Server configuration
            
        Returns:
            bool: True if access is allowed
        """
        try:
            # Check if server is in allowed list
            if config.name not in self.policies:
                logger.warning(f"No security policy found for server {config.name}")
                return False
            
            policy = self.policies[config.name]
            
            # Check tenant isolation
            if policy.tenant_id != self.tenant_id:
                logger.warning(f"Tenant {self.tenant_id} cannot access server {config.name} (belongs to {policy.tenant_id})")
                return False
            
            # Check security level requirements
            if policy.security_level == SecurityLevel.SECRET:
                # Additional security checks for secret level
                if not await self._validate_secret_access(config):
                    return False
            
            # Log access attempt
            await self._log_security_event("server_access", {
                "server_name": config.name,
                "tenant_id": self.tenant_id,
                "allowed": True
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Server access validation failed: {e}")
            return False
    
    async def validate_tool_access(self, server_name: str, tool_name: str) -> bool:
        """
        Validate if tenant can access a specific tool
        
        Args:
            server_name: Name of the MCP server
            tool_name: Name of the tool
            
        Returns:
            bool: True if access is allowed
        """
        try:
            if server_name not in self.policies:
                return False
            
            policy = self.policies[server_name]
            
            # Check if tool is explicitly denied
            if tool_name in policy.denied_tools:
                logger.warning(f"Tool {tool_name} is denied for tenant {self.tenant_id}")
                return False
            
            # Check if tool is in allowed list (if allowed list is not empty)
            if policy.allowed_tools and tool_name not in policy.allowed_tools:
                logger.warning(f"Tool {tool_name} is not in allowed list for tenant {self.tenant_id}")
                return False
            
            # Check rate limiting
            if not await self._check_rate_limit(server_name, policy.max_requests_per_minute):
                logger.warning(f"Rate limit exceeded for server {server_name}")
                return False
            
            # Check if approval is required
            if policy.require_approval:
                if not await self._check_approval(server_name, tool_name):
                    logger.warning(f"Approval required for tool {tool_name}")
                    return False
            
            # Log tool access
            await self._log_security_event("tool_access", {
                "server_name": server_name,
                "tool_name": tool_name,
                "tenant_id": self.tenant_id,
                "allowed": True
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Tool access validation failed: {e}")
            return False
    
    async def validate_resource_access(self, server_name: str, resource_uri: str) -> bool:
        """
        Validate if tenant can access a specific resource
        
        Args:
            server_name: Name of the MCP server
            resource_uri: URI of the resource
            
        Returns:
            bool: True if access is allowed
        """
        try:
            if server_name not in self.policies:
                return False
            
            policy = self.policies[server_name]
            
            # Check if resource is explicitly denied
            for denied_pattern in policy.denied_resources:
                if self._matches_pattern(resource_uri, denied_pattern):
                    logger.warning(f"Resource {resource_uri} is denied for tenant {self.tenant_id}")
                    return False
            
            # Check if resource is in allowed list
            allowed = False
            for allowed_pattern in policy.allowed_resources:
                if self._matches_pattern(resource_uri, allowed_pattern):
                    allowed = True
                    break
            
            if not allowed:
                logger.warning(f"Resource {resource_uri} is not in allowed list for tenant {self.tenant_id}")
                return False
            
            # Log resource access
            await self._log_security_event("resource_access", {
                "server_name": server_name,
                "resource_uri": resource_uri,
                "tenant_id": self.tenant_id,
                "allowed": True
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Resource access validation failed: {e}")
            return False
    
    async def create_security_context(self, operation_type: str, **kwargs) -> SecurityContext:
        """Create security context for an operation"""
        return SecurityContext(
            tenant_id=self.tenant_id,
            user_id=kwargs.get("user_id"),
            session_id=kwargs.get("session_id", "unknown"),
            operation_type=operation_type,
            resource_path=kwargs.get("resource_path"),
            timestamp=datetime.now(),
            ip_address=kwargs.get("ip_address"),
            user_agent=kwargs.get("user_agent")
        )
    
    async def audit_operation(self, context: SecurityContext, operation_data: Dict[str, Any], result: Dict[str, Any]):
        """Audit an MCP operation"""
        try:
            audit_entry = {
                "timestamp": context.timestamp.isoformat(),
                "tenant_id": context.tenant_id,
                "user_id": context.user_id,
                "session_id": context.session_id,
                "operation_type": context.operation_type,
                "resource_path": context.resource_path,
                "ip_address": context.ip_address,
                "user_agent": context.user_agent,
                "operation_data": operation_data,
                "success": "error" not in result,
                "error": result.get("error"),
                "data_hash": self._hash_sensitive_data(operation_data)
            }
            
            self.audit_log.append(audit_entry)
            
            # In production, this would be sent to a secure audit logging system
            logger.info(f"Audit: {json.dumps(audit_entry)}")
            
        except Exception as e:
            logger.error(f"Failed to audit operation: {e}")
    
    async def get_security_summary(self) -> Dict[str, Any]:
        """Get security summary for the tenant"""
        return {
            "tenant_id": self.tenant_id,
            "policies_count": len(self.policies),
            "servers_accessible": list(self.policies.keys()),
            "audit_entries": len(self.audit_log),
            "security_level": "enterprise",
            "last_activity": datetime.now().isoformat()
        }
    
    # Private methods
    
    async def _validate_secret_access(self, config: MCPServerConfig) -> bool:
        """Additional validation for secret-level access"""
        # In production, this might check:
        # - Multi-factor authentication
        # - IP whitelist
        # - Time-based access windows
        # - Additional approvals
        
        logger.info(f"Secret-level access validation for {config.name}")
        return True  # Simplified for demo
    
    async def _check_rate_limit(self, server_name: str, max_requests: int) -> bool:
        """Check rate limiting for server access"""
        try:
            now = datetime.now()
            key = f"{self.tenant_id}:{server_name}"
            
            # Initialize if not exists
            if key not in self.rate_limits:
                self.rate_limits[key] = []
            
            # Clean old entries (older than 1 minute)
            self.rate_limits[key] = [
                timestamp for timestamp in self.rate_limits[key]
                if (now - timestamp).total_seconds() < 60
            ]
            
            # Check if under limit
            if len(self.rate_limits[key]) >= max_requests:
                return False
            
            # Add current request
            self.rate_limits[key].append(now)
            return True
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return False
    
    async def _check_approval(self, server_name: str, tool_name: str) -> bool:
        """Check if operation has required approval"""
        # In production, this would check an approval system
        # For demo, we'll allow all operations
        logger.info(f"Approval check for {server_name}.{tool_name}")
        return True
    
    def _matches_pattern(self, uri: str, pattern: str) -> bool:
        """Check if URI matches a pattern (supports wildcards)"""
        import fnmatch
        return fnmatch.fnmatch(uri, pattern)
    
    def _hash_sensitive_data(self, data: Dict[str, Any]) -> str:
        """Create hash of sensitive data for audit purposes"""
        try:
            # Remove or mask sensitive fields
            safe_data = {}
            for key, value in data.items():
                if key.lower() in ['password', 'token', 'key', 'secret']:
                    safe_data[key] = "[REDACTED]"
                else:
                    safe_data[key] = value
            
            # Create hash
            data_str = json.dumps(safe_data, sort_keys=True)
            return hashlib.sha256(data_str.encode()).hexdigest()[:16]
            
        except Exception as e:
            logger.error(f"Failed to hash data: {e}")
            return "hash_error"
    
    async def _log_security_event(self, event_type: str, event_data: Dict[str, Any]):
        """Log security events"""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "tenant_id": self.tenant_id,
                **event_data
            }
            
            # In production, this would go to a security monitoring system
            logger.info(f"Security Event: {json.dumps(log_entry)}")
            
        except Exception as e:
            logger.error(f"Failed to log security event: {e}")

class MCPSecurityAuditor:
    """Security auditor for MCP operations"""
    
    def __init__(self):
        self.audit_log: List[Dict[str, Any]] = []
    
    async def audit_server_connection(self, tenant_id: str, server_name: str, success: bool):
        """Audit server connection attempts"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "server_connection",
            "tenant_id": tenant_id,
            "server_name": server_name,
            "success": success
        }
        self.audit_log.append(entry)
        logger.info(f"Audit: {json.dumps(entry)}")
    
    async def audit_tool_execution(self, tenant_id: str, server_name: str, tool_name: str, success: bool):
        """Audit tool execution"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "tool_execution",
            "tenant_id": tenant_id,
            "server_name": server_name,
            "tool_name": tool_name,
            "success": success
        }
        self.audit_log.append(entry)
        logger.info(f"Audit: {json.dumps(entry)}")
    
    async def get_audit_report(self, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get audit report"""
        if tenant_id:
            return [entry for entry in self.audit_log if entry.get("tenant_id") == tenant_id]
        return self.audit_log

# Global security auditor
security_auditor = MCPSecurityAuditor()