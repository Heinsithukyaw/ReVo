#!/usr/bin/env python3
"""
Enterprise Security Manager for reVoAgent
Comprehensive security framework with JWT, RBAC, rate limiting, and audit logging

This module implements enterprise-grade security features including:
- JWT authentication and authorization
- Role-based access control (RBAC)
- Rate limiting and API protection
- Security audit logging
- Encryption and data protection
- Session management
- API key management
"""

import asyncio
import jwt
import hashlib
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List, Set, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict, deque
import json
import bcrypt
from cryptography.fernet import Fernet
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserRole(Enum):
    """User roles for RBAC system"""
    ADMIN = "admin"
    DEVELOPER = "developer"
    ANALYST = "analyst"
    VIEWER = "viewer"
    API_USER = "api_user"
    GUEST = "guest"

class Permission(Enum):
    """System permissions"""
    # AI Operations
    AI_GENERATE = "ai:generate"
    AI_CONFIGURE = "ai:configure"
    AI_MONITOR = "ai:monitor"
    
    # Data Operations
    DATA_READ = "data:read"
    DATA_WRITE = "data:write"
    DATA_DELETE = "data:delete"
    DATA_EXPORT = "data:export"
    
    # System Operations
    SYSTEM_ADMIN = "system:admin"
    SYSTEM_CONFIG = "system:config"
    SYSTEM_MONITOR = "system:monitor"
    
    # User Management
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_VIEW = "user:view"

class SecurityEvent(Enum):
    """Security event types for audit logging"""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    PERMISSION_DENIED = "permission_denied"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    API_KEY_CREATED = "api_key_created"
    API_KEY_REVOKED = "api_key_revoked"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    DATA_ACCESS = "data_access"
    CONFIGURATION_CHANGE = "configuration_change"
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"

@dataclass
class User:
    """User entity with security attributes"""
    user_id: str
    username: str
    email: str
    password_hash: str
    roles: Set[UserRole]
    permissions: Set[Permission] = field(default_factory=set)
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    account_locked_until: Optional[datetime] = None
    api_keys: List[str] = field(default_factory=list)
    session_tokens: Set[str] = field(default_factory=set)

@dataclass
class SecurityAuditLog:
    """Security audit log entry"""
    event_id: str
    event_type: SecurityEvent
    user_id: Optional[str]
    ip_address: str
    user_agent: str
    timestamp: datetime
    details: Dict[str, Any]
    risk_level: str = "low"  # low, medium, high, critical

@dataclass
class RateLimitRule:
    """Rate limiting rule configuration"""
    endpoint: str
    max_requests: int
    time_window: int  # seconds
    burst_allowance: int = 0
    block_duration: int = 300  # seconds

@dataclass
class APIKey:
    """API key entity"""
    key_id: str
    key_hash: str
    user_id: str
    name: str
    permissions: Set[Permission]
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    is_active: bool = True

class EnterpriseSecurityManager:
    """
    Enterprise Security Manager
    
    Provides comprehensive security features for the reVoAgent platform:
    - JWT authentication and session management
    - Role-based access control (RBAC)
    - Rate limiting and API protection
    - Security audit logging
    - Encryption and data protection
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the Enterprise Security Manager"""
        self.config = config
        self.jwt_secret = config.get("jwt_secret", self._generate_secret())
        self.jwt_algorithm = config.get("jwt_algorithm", "HS256")
        self.jwt_expiry_hours = config.get("jwt_expiry_hours", 24)
        self.encryption_key = config.get("encryption_key", Fernet.generate_key())
        self.fernet = Fernet(self.encryption_key)
        
        # Security settings
        self.max_login_attempts = config.get("max_login_attempts", 5)
        self.account_lockout_duration = config.get("account_lockout_duration", 1800)  # 30 minutes
        self.password_min_length = config.get("password_min_length", 12)
        self.require_password_complexity = config.get("require_password_complexity", True)
        
        # Storage
        self.users: Dict[str, User] = {}
        self.api_keys: Dict[str, APIKey] = {}
        self.audit_logs: deque = deque(maxlen=10000)
        self.rate_limit_data: Dict[str, Dict] = defaultdict(dict)
        self.blocked_ips: Dict[str, datetime] = {}
        
        # Rate limiting rules
        self.rate_limit_rules: List[RateLimitRule] = [
            RateLimitRule("/api/ai/generate", 100, 3600, 10, 300),  # 100/hour, 10 burst
            RateLimitRule("/api/auth/login", 10, 900, 2, 900),      # 10/15min, 2 burst
            RateLimitRule("/api/data/export", 5, 3600, 1, 1800),   # 5/hour, 1 burst
            RateLimitRule("/api/admin/*", 50, 3600, 5, 600),       # 50/hour, 5 burst
        ]
        
        # Role permissions mapping
        self.role_permissions = {
            UserRole.ADMIN: {
                Permission.AI_GENERATE, Permission.AI_CONFIGURE, Permission.AI_MONITOR,
                Permission.DATA_READ, Permission.DATA_WRITE, Permission.DATA_DELETE, Permission.DATA_EXPORT,
                Permission.SYSTEM_ADMIN, Permission.SYSTEM_CONFIG, Permission.SYSTEM_MONITOR,
                Permission.USER_CREATE, Permission.USER_UPDATE, Permission.USER_DELETE, Permission.USER_VIEW
            },
            UserRole.DEVELOPER: {
                Permission.AI_GENERATE, Permission.AI_CONFIGURE, Permission.AI_MONITOR,
                Permission.DATA_READ, Permission.DATA_WRITE, Permission.DATA_EXPORT,
                Permission.SYSTEM_MONITOR, Permission.USER_VIEW
            },
            UserRole.ANALYST: {
                Permission.AI_GENERATE, Permission.AI_MONITOR,
                Permission.DATA_READ, Permission.DATA_EXPORT,
                Permission.SYSTEM_MONITOR
            },
            UserRole.VIEWER: {
                Permission.AI_MONITOR, Permission.DATA_READ, Permission.SYSTEM_MONITOR
            },
            UserRole.API_USER: {
                Permission.AI_GENERATE, Permission.DATA_READ
            },
            UserRole.GUEST: {
                Permission.DATA_READ
            }
        }
        
        logger.info("🛡️ Enterprise Security Manager initialized")
        logger.info(f"🔐 JWT expiry: {self.jwt_expiry_hours} hours")
        logger.info(f"🚫 Max login attempts: {self.max_login_attempts}")
        logger.info(f"⏰ Account lockout duration: {self.account_lockout_duration} seconds")

    def _generate_secret(self) -> str:
        """Generate a secure random secret"""
        return secrets.token_urlsafe(32)

    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

    def _validate_password_strength(self, password: str) -> bool:
        """Validate password meets security requirements"""
        if len(password) < self.password_min_length:
            return False
        
        if not self.require_password_complexity:
            return True
        
        # Check complexity requirements
        has_upper = bool(re.search(r'[A-Z]', password))
        has_lower = bool(re.search(r'[a-z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
        
        return has_upper and has_lower and has_digit and has_special

    async def create_user(self, username: str, email: str, password: str, 
                         roles: Set[UserRole], user_id: Optional[str] = None) -> User:
        """Create a new user with security validation"""
        
        # Validate password strength
        if not self._validate_password_strength(password):
            raise ValueError(f"Password must be at least {self.password_min_length} characters with uppercase, lowercase, digit, and special character")
        
        # Check if user already exists
        if any(u.username == username or u.email == email for u in self.users.values()):
            raise ValueError("User with this username or email already exists")
        
        # Generate user ID if not provided
        if not user_id:
            user_id = f"user_{secrets.token_urlsafe(8)}"
        
        # Hash password
        password_hash = self._hash_password(password)
        
        # Calculate permissions from roles
        permissions = set()
        for role in roles:
            permissions.update(self.role_permissions.get(role, set()))
        
        # Create user
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            password_hash=password_hash,
            roles=roles,
            permissions=permissions
        )
        
        self.users[user_id] = user
        
        # Log security event
        await self._log_security_event(
            SecurityEvent.USER_CREATE,
            user_id=user_id,
            ip_address="system",
            user_agent="system",
            details={"username": username, "email": email, "roles": [r.value for r in roles]}
        )
        
        logger.info(f"👤 User created: {username} ({user_id}) with roles: {[r.value for r in roles]}")
        return user

    async def authenticate_user(self, username: str, password: str, 
                              ip_address: str, user_agent: str) -> Optional[str]:
        """Authenticate user and return JWT token"""
        
        # Find user by username or email
        user = None
        for u in self.users.values():
            if u.username == username or u.email == username:
                user = u
                break
        
        if not user:
            await self._log_security_event(
                SecurityEvent.LOGIN_FAILURE,
                user_id=None,
                ip_address=ip_address,
                user_agent=user_agent,
                details={"username": username, "reason": "user_not_found"}
            )
            return None
        
        # Check if account is locked
        if user.account_locked_until and user.account_locked_until > datetime.now(timezone.utc):
            await self._log_security_event(
                SecurityEvent.LOGIN_FAILURE,
                user_id=user.user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                details={"username": username, "reason": "account_locked"}
            )
            return None
        
        # Check if account is active
        if not user.is_active:
            await self._log_security_event(
                SecurityEvent.LOGIN_FAILURE,
                user_id=user.user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                details={"username": username, "reason": "account_inactive"}
            )
            return None
        
        # Verify password
        if not self._verify_password(password, user.password_hash):
            user.failed_login_attempts += 1
            
            # Lock account if too many failed attempts
            if user.failed_login_attempts >= self.max_login_attempts:
                user.account_locked_until = datetime.now(timezone.utc) + timedelta(seconds=self.account_lockout_duration)
                logger.warning(f"🔒 Account locked for user {username} due to failed login attempts")
            
            await self._log_security_event(
                SecurityEvent.LOGIN_FAILURE,
                user_id=user.user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                details={"username": username, "reason": "invalid_password", "failed_attempts": user.failed_login_attempts}
            )
            return None
        
        # Successful authentication
        user.failed_login_attempts = 0
        user.account_locked_until = None
        user.last_login = datetime.now(timezone.utc)
        
        # Generate JWT token
        token = self._generate_jwt_token(user)
        user.session_tokens.add(token)
        
        await self._log_security_event(
            SecurityEvent.LOGIN_SUCCESS,
            user_id=user.user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details={"username": username}
        )
        
        logger.info(f"✅ User authenticated: {username} ({user.user_id})")
        return token

    def _generate_jwt_token(self, user: User) -> str:
        """Generate JWT token for authenticated user"""
        payload = {
            "user_id": user.user_id,
            "username": user.username,
            "roles": [role.value for role in user.roles],
            "permissions": [perm.value for perm in user.permissions],
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=self.jwt_expiry_hours)
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

    async def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            
            # Check if user still exists and is active
            user_id = payload.get("user_id")
            if user_id not in self.users or not self.users[user_id].is_active:
                return None
            
            # Check if token is in user's active sessions
            if token not in self.users[user_id].session_tokens:
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("🔒 JWT token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("🔒 Invalid JWT token")
            return None

    async def logout_user(self, token: str, ip_address: str, user_agent: str) -> bool:
        """Logout user and invalidate token"""
        payload = await self.verify_jwt_token(token)
        if not payload:
            return False
        
        user_id = payload["user_id"]
        user = self.users.get(user_id)
        if user:
            user.session_tokens.discard(token)
            
            await self._log_security_event(
                SecurityEvent.LOGOUT,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                details={"username": user.username}
            )
            
            logger.info(f"👋 User logged out: {user.username} ({user_id})")
            return True
        
        return False

    async def check_permission(self, token: str, required_permission: Permission) -> bool:
        """Check if user has required permission"""
        payload = await self.verify_jwt_token(token)
        if not payload:
            return False
        
        user_permissions = [Permission(p) for p in payload.get("permissions", [])]
        return required_permission in user_permissions

    async def check_rate_limit(self, endpoint: str, ip_address: str, user_id: Optional[str] = None) -> bool:
        """Check if request is within rate limits"""
        
        # Check if IP is blocked
        if ip_address in self.blocked_ips:
            if self.blocked_ips[ip_address] > datetime.now(timezone.utc):
                return False
            else:
                del self.blocked_ips[ip_address]
        
        # Find applicable rate limit rule
        rule = None
        for r in self.rate_limit_rules:
            if endpoint.startswith(r.endpoint.replace("*", "")):
                rule = r
                break
        
        if not rule:
            return True  # No rate limit rule applies
        
        # Create rate limit key
        key = f"{ip_address}:{endpoint}"
        if user_id:
            key = f"{user_id}:{endpoint}"
        
        current_time = time.time()
        
        # Initialize rate limit data if not exists
        if key not in self.rate_limit_data:
            self.rate_limit_data[key] = {
                "requests": deque(),
                "burst_used": 0,
                "last_reset": current_time
            }
        
        data = self.rate_limit_data[key]
        
        # Clean old requests outside time window
        while data["requests"] and data["requests"][0] < current_time - rule.time_window:
            data["requests"].popleft()
        
        # Reset burst allowance if time window passed
        if current_time - data["last_reset"] >= rule.time_window:
            data["burst_used"] = 0
            data["last_reset"] = current_time
        
        # Check if within limits
        current_requests = len(data["requests"])
        
        if current_requests < rule.max_requests:
            # Within normal limits
            data["requests"].append(current_time)
            return True
        elif data["burst_used"] < rule.burst_allowance:
            # Use burst allowance
            data["requests"].append(current_time)
            data["burst_used"] += 1
            return True
        else:
            # Rate limit exceeded
            if rule.block_duration > 0:
                self.blocked_ips[ip_address] = datetime.now(timezone.utc) + timedelta(seconds=rule.block_duration)
            
            await self._log_security_event(
                SecurityEvent.RATE_LIMIT_EXCEEDED,
                user_id=user_id,
                ip_address=ip_address,
                user_agent="unknown",
                details={"endpoint": endpoint, "rule": rule.endpoint, "requests": current_requests, "limit": rule.max_requests},
                risk_level="medium"
            )
            
            logger.warning(f"🚫 Rate limit exceeded for {key} on {endpoint}")
            return False

    async def create_api_key(self, user_id: str, name: str, permissions: Set[Permission], 
                           expires_at: Optional[datetime] = None) -> str:
        """Create API key for user"""
        user = self.users.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Generate API key
        key_id = f"ak_{secrets.token_urlsafe(8)}"
        api_key = f"revo_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # Create API key entity
        api_key_entity = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            user_id=user_id,
            name=name,
            permissions=permissions,
            created_at=datetime.now(timezone.utc),
            expires_at=expires_at
        )
        
        self.api_keys[key_id] = api_key_entity
        user.api_keys.append(key_id)
        
        await self._log_security_event(
            SecurityEvent.API_KEY_CREATED,
            user_id=user_id,
            ip_address="system",
            user_agent="system",
            details={"key_id": key_id, "name": name, "permissions": [p.value for p in permissions]}
        )
        
        logger.info(f"🔑 API key created: {name} ({key_id}) for user {user.username}")
        return api_key

    async def verify_api_key(self, api_key: str) -> Optional[APIKey]:
        """Verify API key and return key entity"""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        for key_entity in self.api_keys.values():
            if key_entity.key_hash == key_hash and key_entity.is_active:
                # Check expiration
                if key_entity.expires_at and key_entity.expires_at < datetime.now(timezone.utc):
                    key_entity.is_active = False
                    return None
                
                # Update last used
                key_entity.last_used = datetime.now(timezone.utc)
                return key_entity
        
        return None

    async def _log_security_event(self, event_type: SecurityEvent, user_id: Optional[str],
                                ip_address: str, user_agent: str, details: Dict[str, Any],
                                risk_level: str = "low"):
        """Log security event for audit trail"""
        event = SecurityAuditLog(
            event_id=f"evt_{secrets.token_urlsafe(8)}",
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.now(timezone.utc),
            details=details,
            risk_level=risk_level
        )
        
        self.audit_logs.append(event)
        
        # Log high-risk events
        if risk_level in ["high", "critical"]:
            logger.warning(f"🚨 High-risk security event: {event_type.value} - {details}")

    async def get_security_metrics(self) -> Dict[str, Any]:
        """Get security metrics and statistics"""
        current_time = datetime.now(timezone.utc)
        last_24h = current_time - timedelta(hours=24)
        
        # Count events in last 24 hours
        recent_events = [log for log in self.audit_logs if log.timestamp >= last_24h]
        
        event_counts = defaultdict(int)
        risk_counts = defaultdict(int)
        
        for event in recent_events:
            event_counts[event.event_type.value] += 1
            risk_counts[event.risk_level] += 1
        
        # Active users
        active_users = sum(1 for user in self.users.values() if user.is_active)
        locked_users = sum(1 for user in self.users.values() 
                          if user.account_locked_until and user.account_locked_until > current_time)
        
        # API keys
        active_api_keys = sum(1 for key in self.api_keys.values() if key.is_active)
        
        return {
            "users": {
                "total": len(self.users),
                "active": active_users,
                "locked": locked_users
            },
            "api_keys": {
                "total": len(self.api_keys),
                "active": active_api_keys
            },
            "events_24h": {
                "total": len(recent_events),
                "by_type": dict(event_counts),
                "by_risk": dict(risk_counts)
            },
            "rate_limiting": {
                "blocked_ips": len(self.blocked_ips),
                "active_limits": len(self.rate_limit_data)
            },
            "security_score": self._calculate_security_score()
        }

    def _calculate_security_score(self) -> int:
        """Calculate overall security score (0-100)"""
        score = 100
        
        # Deduct points for security issues
        current_time = datetime.now(timezone.utc)
        last_24h = current_time - timedelta(hours=24)
        
        recent_events = [log for log in self.audit_logs if log.timestamp >= last_24h]
        
        # Deduct for failed logins
        failed_logins = sum(1 for event in recent_events 
                           if event.event_type == SecurityEvent.LOGIN_FAILURE)
        score -= min(failed_logins * 2, 20)
        
        # Deduct for rate limit violations
        rate_limit_violations = sum(1 for event in recent_events 
                                  if event.event_type == SecurityEvent.RATE_LIMIT_EXCEEDED)
        score -= min(rate_limit_violations * 5, 30)
        
        # Deduct for high-risk events
        high_risk_events = sum(1 for event in recent_events 
                              if event.risk_level in ["high", "critical"])
        score -= min(high_risk_events * 10, 40)
        
        # Deduct for locked accounts
        locked_users = sum(1 for user in self.users.values() 
                          if user.account_locked_until and user.account_locked_until > current_time)
        score -= min(locked_users * 5, 15)
        
        return max(score, 0)

# Example usage and testing
async def main():
    """Example usage of Enterprise Security Manager"""
    
    # Configuration
    config = {
        "jwt_secret": "your-super-secret-jwt-key-change-in-production",
        "jwt_expiry_hours": 24,
        "max_login_attempts": 5,
        "account_lockout_duration": 1800,
        "password_min_length": 12,
        "require_password_complexity": True
    }
    
    # Initialize security manager
    security_manager = EnterpriseSecurityManager(config)
    
    print("🛡️ Enterprise Security Manager Demo")
    print("=" * 50)
    
    try:
        # Create admin user
        admin_user = await security_manager.create_user(
            username="admin",
            email="admin@revoagent.com",
            password="SecurePassword123!",
            roles={UserRole.ADMIN}
        )
        print(f"✅ Admin user created: {admin_user.username}")
        
        # Create developer user
        dev_user = await security_manager.create_user(
            username="developer",
            email="dev@revoagent.com",
            password="DevPassword456!",
            roles={UserRole.DEVELOPER}
        )
        print(f"✅ Developer user created: {dev_user.username}")
        
        # Authenticate admin
        admin_token = await security_manager.authenticate_user(
            username="admin",
            password="SecurePassword123!",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 (Test Browser)"
        )
        print(f"✅ Admin authenticated, token: {admin_token[:20]}...")
        
        # Check permissions
        can_admin = await security_manager.check_permission(admin_token, Permission.SYSTEM_ADMIN)
        can_dev_admin = await security_manager.check_permission(admin_token, Permission.AI_GENERATE)
        print(f"✅ Admin can perform system admin: {can_admin}")
        print(f"✅ Admin can generate AI: {can_dev_admin}")
        
        # Test rate limiting
        for i in range(3):
            within_limit = await security_manager.check_rate_limit(
                "/api/ai/generate", "192.168.1.100", admin_user.user_id
            )
            print(f"✅ Rate limit check {i+1}: {within_limit}")
        
        # Create API key
        api_key = await security_manager.create_api_key(
            user_id=admin_user.user_id,
            name="Admin API Key",
            permissions={Permission.AI_GENERATE, Permission.DATA_READ}
        )
        print(f"✅ API key created: {api_key[:20]}...")
        
        # Verify API key
        key_entity = await security_manager.verify_api_key(api_key)
        print(f"✅ API key verified: {key_entity.name if key_entity else 'Invalid'}")
        
        # Get security metrics
        metrics = await security_manager.get_security_metrics()
        print(f"✅ Security metrics:")
        print(f"   - Total users: {metrics['users']['total']}")
        print(f"   - Active users: {metrics['users']['active']}")
        print(f"   - Security score: {metrics['security_score']}/100")
        print(f"   - Events (24h): {metrics['events_24h']['total']}")
        
        # Logout
        logout_success = await security_manager.logout_user(
            admin_token, "192.168.1.100", "Mozilla/5.0 (Test Browser)"
        )
        print(f"✅ Logout successful: {logout_success}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())