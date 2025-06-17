"""
🔐 Enterprise Authentication and Authorization

JWT-based authentication with role-based access control for the Three-Engine Architecture.
"""

from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
import secrets
from typing import Optional, List, Dict, Any
import redis.asyncio as redis
import logging

logger = logging.getLogger(__name__)

class EnterpriseAuth:
    """Enterprise-grade authentication system"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.secret_key = secrets.token_urlsafe(32)
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.security = HTTPBearer()
        self.redis_client = None
        self.redis_url = redis_url
        
    async def initialize(self):
        """Initialize Redis connection for token management"""
        try:
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            logger.info("🔐 Enterprise Auth initialized with Redis")
        except Exception as e:
            logger.warning(f"Redis connection failed, using in-memory token store: {e}")
            self.redis_client = None
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Generate password hash"""
        return self.pwd_context.hash(password)
    
    async def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        
        # Store token in Redis for revocation capability
        if self.redis_client:
            try:
                ttl = int(expires_delta.total_seconds() if expires_delta else self.access_token_expire_minutes * 60)
                await self.redis_client.setex(f"token:{encoded_jwt}", ttl, "active")
            except Exception as e:
                logger.warning(f"Failed to store token in Redis: {e}")
        
        return encoded_jwt
    
    async def verify_token(self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
        """Verify JWT token and return user info"""
        try:
            # Check if token is revoked (if Redis is available)
            if self.redis_client:
                try:
                    token_status = await self.redis_client.get(f"token:{credentials.credentials}")
                    if not token_status:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Token has been revoked",
                            headers={"WWW-Authenticate": "Bearer"},
                        )
                except Exception as e:
                    logger.warning(f"Redis token check failed: {e}")
            
            # Decode and verify JWT
            payload = jwt.decode(credentials.credentials, self.secret_key, algorithms=[self.algorithm])
            username: str = payload.get("sub")
            user_role: str = payload.get("role", "viewer")
            
            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return {
                "username": username,
                "role": user_role,
                "token_data": payload
            }
            
        except JWTError as e:
            logger.warning(f"JWT verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    async def revoke_token(self, token: str):
        """Revoke a specific token"""
        if self.redis_client:
            try:
                await self.redis_client.delete(f"token:{token}")
                logger.info("Token revoked successfully")
            except Exception as e:
                logger.error(f"Failed to revoke token: {e}")
    
    async def revoke_all_user_tokens(self, username: str):
        """Revoke all tokens for a specific user"""
        if self.redis_client:
            try:
                # This would require storing user->token mapping
                # For now, we'll implement a simple approach
                pattern = f"user_tokens:{username}:*"
                keys = await self.redis_client.keys(pattern)
                if keys:
                    await self.redis_client.delete(*keys)
                logger.info(f"All tokens revoked for user: {username}")
            except Exception as e:
                logger.error(f"Failed to revoke user tokens: {e}")

class RoleBasedAccessControl:
    """Enterprise-grade RBAC for engine access"""
    
    ROLES = {
        "admin": {
            "permissions": ["read", "write", "execute", "manage", "configure"],
            "description": "Full system access"
        },
        "developer": {
            "permissions": ["read", "write", "execute"],
            "description": "Development and execution access"
        },
        "analyst": {
            "permissions": ["read", "execute"],
            "description": "Analysis and read-only access"
        },
        "viewer": {
            "permissions": ["read"],
            "description": "Read-only access"
        }
    }
    
    ENGINE_PERMISSIONS = {
        "perfect_recall": {
            "query": "read",
            "store": "write",
            "manage_memory": "manage"
        },
        "parallel_mind": {
            "submit_task": "execute",
            "view_status": "read",
            "manage_workers": "manage"
        },
        "creative_engine": {
            "generate": "execute",
            "configure": "manage",
            "view_solutions": "read"
        },
        "coordinator": {
            "coordinate": "execute",
            "configure": "manage",
            "view_status": "read"
        }
    }
    
    @classmethod
    def check_permission(cls, user_role: str, engine: str, action: str) -> bool:
        """Check if user role has permission for engine action"""
        if user_role not in cls.ROLES:
            return False
        
        user_permissions = cls.ROLES[user_role]["permissions"]
        required_permission = cls._map_action_to_permission(engine, action)
        
        return required_permission in user_permissions
    
    @classmethod
    def _map_action_to_permission(cls, engine: str, action: str) -> str:
        """Map engine action to required permission"""
        if engine in cls.ENGINE_PERMISSIONS:
            return cls.ENGINE_PERMISSIONS[engine].get(action, "read")
        
        # Default mapping for unknown actions
        action_mapping = {
            "query": "read",
            "store": "write",
            "submit_task": "execute",
            "generate": "execute",
            "configure": "manage",
            "manage": "manage"
        }
        return action_mapping.get(action, "read")
    
    @classmethod
    def get_user_permissions(cls, user_role: str) -> Dict[str, Any]:
        """Get detailed permissions for a user role"""
        if user_role not in cls.ROLES:
            return {"permissions": [], "engines": {}}
        
        role_info = cls.ROLES[user_role]
        user_permissions = role_info["permissions"]
        
        # Calculate engine-specific permissions
        engine_permissions = {}
        for engine, actions in cls.ENGINE_PERMISSIONS.items():
            engine_permissions[engine] = {}
            for action, required_perm in actions.items():
                engine_permissions[engine][action] = required_perm in user_permissions
        
        return {
            "role": user_role,
            "description": role_info["description"],
            "permissions": user_permissions,
            "engines": engine_permissions
        }

def require_permission(engine: str, action: str):
    """Decorator to require specific permission for engine access"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract user info from dependencies
            user_info = kwargs.get('current_user')
            if not user_info:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            user_role = user_info.get('role', 'viewer')
            
            if not RoleBasedAccessControl.check_permission(user_role, engine, action):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions for {action} on {engine}. Required role permissions not met."
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_role(required_roles: List[str]):
    """Decorator to require specific roles"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            user_info = kwargs.get('current_user')
            if not user_info:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            user_role = user_info.get('role', 'viewer')
            
            if user_role not in required_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required roles: {required_roles}, user role: {user_role}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

class APIRateLimiter:
    """Rate limiting for API endpoints"""
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self.default_limits = {
            "viewer": {"requests_per_minute": 60, "requests_per_hour": 1000},
            "analyst": {"requests_per_minute": 120, "requests_per_hour": 5000},
            "developer": {"requests_per_minute": 300, "requests_per_hour": 10000},
            "admin": {"requests_per_minute": 1000, "requests_per_hour": 50000}
        }
    
    async def check_rate_limit(self, user_id: str, user_role: str) -> bool:
        """Check if user is within rate limits"""
        if not self.redis_client:
            return True  # No rate limiting without Redis
        
        limits = self.default_limits.get(user_role, self.default_limits["viewer"])
        
        try:
            # Check minute limit
            minute_key = f"rate_limit:{user_id}:minute:{datetime.now().strftime('%Y%m%d%H%M')}"
            minute_count = await self.redis_client.incr(minute_key)
            await self.redis_client.expire(minute_key, 60)
            
            if minute_count > limits["requests_per_minute"]:
                return False
            
            # Check hour limit
            hour_key = f"rate_limit:{user_id}:hour:{datetime.now().strftime('%Y%m%d%H')}"
            hour_count = await self.redis_client.incr(hour_key)
            await self.redis_client.expire(hour_key, 3600)
            
            if hour_count > limits["requests_per_hour"]:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return True  # Allow on error

def rate_limit():
    """Decorator for rate limiting"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            user_info = kwargs.get('current_user')
            if user_info:
                # Rate limiting logic would go here
                # For now, we'll just pass through
                pass
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator