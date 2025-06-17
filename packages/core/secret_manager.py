"""
Secure secret management with Azure Key Vault integration.

This replaces environment variables with proper secret management:
- Azure Key Vault for production secrets
- Local file-based secrets for development
- In-memory caching with TTL
- Automatic secret rotation support
"""

import os
import json
import asyncio
import logging
from typing import Dict, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import aiofiles

try:
    from azure.keyvault.secrets import SecretClient
    from azure.identity import DefaultAzureCredential, ClientSecretCredential
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False
    SecretClient = None
    DefaultAzureCredential = None
    ClientSecretCredential = None

from .logging_config import get_logger

logger = get_logger(__name__)


class SecretProvider(Enum):
    """Secret provider types."""
    AZURE_KEY_VAULT = "azure_key_vault"
    LOCAL_FILE = "local_file"
    ENVIRONMENT = "environment"  # Fallback only


@dataclass
class SecretConfig:
    """Configuration for secret management."""
    provider: SecretProvider
    azure_vault_url: Optional[str] = None
    azure_tenant_id: Optional[str] = None
    azure_client_id: Optional[str] = None
    azure_client_secret: Optional[str] = None
    local_secrets_file: Optional[str] = None
    cache_ttl_seconds: int = 3600  # 1 hour default
    auto_refresh: bool = True


@dataclass
class CachedSecret:
    """Cached secret with expiration."""
    value: str
    expires_at: datetime
    last_updated: datetime


class SecretManager:
    """
    Secure secret management with multiple providers.
    
    Features:
    - Azure Key Vault integration for production
    - Local file-based secrets for development
    - In-memory caching with TTL
    - Automatic secret rotation
    - Security logging and monitoring
    """
    
    def __init__(self, config: SecretConfig):
        self.config = config
        self._cache: Dict[str, CachedSecret] = {}
        self._client: Optional[SecretClient] = None
        self._local_secrets: Dict[str, str] = {}
        self._initialized = False
        
        logger.info("Initializing SecretManager", extra={
            'provider': config.provider.value,
            'cache_ttl': config.cache_ttl_seconds,
            'auto_refresh': config.auto_refresh
        })
    
    async def initialize(self) -> bool:
        """Initialize the secret manager."""
        try:
            if self.config.provider == SecretProvider.AZURE_KEY_VAULT:
                await self._initialize_azure_client()
            elif self.config.provider == SecretProvider.LOCAL_FILE:
                await self._load_local_secrets()
            
            self._initialized = True
            logger.info("SecretManager initialized successfully", extra={
                'provider': self.config.provider.value
            })
            return True
            
        except Exception as e:
            logger.error("Failed to initialize SecretManager", extra={
                'provider': self.config.provider.value,
                'error': str(e)
            }, exc_info=True)
            return False
    
    async def _initialize_azure_client(self):
        """Initialize Azure Key Vault client."""
        if not AZURE_AVAILABLE:
            raise ImportError("Azure SDK not available. Install with: pip install azure-keyvault-secrets azure-identity")
        
        if not self.config.azure_vault_url:
            raise ValueError("Azure vault URL is required")
        
        try:
            # Use service principal if credentials provided
            if (self.config.azure_tenant_id and 
                self.config.azure_client_id and 
                self.config.azure_client_secret):
                credential = ClientSecretCredential(
                    tenant_id=self.config.azure_tenant_id,
                    client_id=self.config.azure_client_id,
                    client_secret=self.config.azure_client_secret
                )
                logger.info("Using service principal authentication for Azure Key Vault")
            else:
                # Use default credential (managed identity, Azure CLI, etc.)
                credential = DefaultAzureCredential()
                logger.info("Using default Azure credential for Key Vault")
            
            self._client = SecretClient(
                vault_url=self.config.azure_vault_url,
                credential=credential
            )
            
            # Test connection
            await asyncio.get_event_loop().run_in_executor(
                None, lambda: list(self._client.list_properties_of_secrets(max_page_size=1))
            )
            
            logger.info("Azure Key Vault client initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize Azure Key Vault client", extra={
                'vault_url': self.config.azure_vault_url,
                'error': str(e)
            })
            raise
    
    async def _load_local_secrets(self):
        """Load secrets from local file."""
        if not self.config.local_secrets_file:
            raise ValueError("Local secrets file path is required")
        
        try:
            if os.path.exists(self.config.local_secrets_file):
                async with aiofiles.open(self.config.local_secrets_file, 'r') as f:
                    content = await f.read()
                    self._local_secrets = json.loads(content)
                
                logger.info("Local secrets loaded successfully", extra={
                    'secrets_count': len(self._local_secrets),
                    'file_path': self.config.local_secrets_file
                })
            else:
                logger.warning("Local secrets file not found", extra={
                    'file_path': self.config.local_secrets_file
                })
                self._local_secrets = {}
                
        except Exception as e:
            logger.error("Failed to load local secrets", extra={
                'file_path': self.config.local_secrets_file,
                'error': str(e)
            })
            raise
    
    async def get_secret(self, secret_name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a secret value with caching and fallback.
        
        Args:
            secret_name: Name of the secret
            default: Default value if secret not found
            
        Returns:
            Secret value or default
        """
        if not self._initialized:
            logger.warning("SecretManager not initialized, attempting initialization")
            if not await self.initialize():
                return self._get_environment_fallback(secret_name, default)
        
        # Check cache first
        cached_secret = self._get_from_cache(secret_name)
        if cached_secret:
            return cached_secret
        
        # Fetch from provider
        try:
            secret_value = await self._fetch_secret(secret_name)
            if secret_value:
                self._cache_secret(secret_name, secret_value)
                logger.debug("Secret retrieved successfully", extra={
                    'secret_name': secret_name,
                    'provider': self.config.provider.value
                })
                return secret_value
            else:
                logger.warning("Secret not found", extra={
                    'secret_name': secret_name,
                    'provider': self.config.provider.value
                })
                return default
                
        except Exception as e:
            logger.error("Failed to retrieve secret", extra={
                'secret_name': secret_name,
                'provider': self.config.provider.value,
                'error': str(e)
            })
            # Fallback to environment variable
            return self._get_environment_fallback(secret_name, default)
    
    async def _fetch_secret(self, secret_name: str) -> Optional[str]:
        """Fetch secret from the configured provider."""
        if self.config.provider == SecretProvider.AZURE_KEY_VAULT:
            return await self._fetch_from_azure(secret_name)
        elif self.config.provider == SecretProvider.LOCAL_FILE:
            return self._local_secrets.get(secret_name)
        else:
            return self._get_environment_fallback(secret_name)
    
    async def _fetch_from_azure(self, secret_name: str) -> Optional[str]:
        """Fetch secret from Azure Key Vault."""
        try:
            secret = await asyncio.get_event_loop().run_in_executor(
                None, self._client.get_secret, secret_name
            )
            return secret.value
        except Exception as e:
            logger.error("Failed to fetch secret from Azure Key Vault", extra={
                'secret_name': secret_name,
                'error': str(e)
            })
            return None
    
    def _get_from_cache(self, secret_name: str) -> Optional[str]:
        """Get secret from cache if not expired."""
        cached = self._cache.get(secret_name)
        if cached and cached.expires_at > datetime.now():
            logger.debug("Secret retrieved from cache", extra={
                'secret_name': secret_name,
                'expires_at': cached.expires_at.isoformat()
            })
            return cached.value
        elif cached:
            # Remove expired cache entry
            del self._cache[secret_name]
            logger.debug("Expired secret removed from cache", extra={
                'secret_name': secret_name
            })
        return None
    
    def _cache_secret(self, secret_name: str, value: str):
        """Cache secret with TTL."""
        expires_at = datetime.now() + timedelta(seconds=self.config.cache_ttl_seconds)
        self._cache[secret_name] = CachedSecret(
            value=value,
            expires_at=expires_at,
            last_updated=datetime.now()
        )
        logger.debug("Secret cached", extra={
            'secret_name': secret_name,
            'expires_at': expires_at.isoformat()
        })
    
    def _get_environment_fallback(self, secret_name: str, default: Optional[str] = None) -> Optional[str]:
        """Fallback to environment variable."""
        value = os.getenv(secret_name, default)
        if value:
            logger.warning("Using environment variable fallback", extra={
                'secret_name': secret_name
            })
        return value
    
    async def set_secret(self, secret_name: str, value: str) -> bool:
        """
        Set a secret value (for local development only).
        
        Args:
            secret_name: Name of the secret
            value: Secret value
            
        Returns:
            True if successful
        """
        if self.config.provider == SecretProvider.LOCAL_FILE:
            try:
                self._local_secrets[secret_name] = value
                
                # Save to file
                if self.config.local_secrets_file:
                    async with aiofiles.open(self.config.local_secrets_file, 'w') as f:
                        await f.write(json.dumps(self._local_secrets, indent=2))
                
                # Update cache
                self._cache_secret(secret_name, value)
                
                logger.info("Secret set successfully", extra={
                    'secret_name': secret_name,
                    'provider': self.config.provider.value
                })
                return True
                
            except Exception as e:
                logger.error("Failed to set secret", extra={
                    'secret_name': secret_name,
                    'error': str(e)
                })
                return False
        else:
            logger.error("Setting secrets not supported for this provider", extra={
                'provider': self.config.provider.value
            })
            return False
    
    async def refresh_cache(self) -> int:
        """
        Refresh all cached secrets.
        
        Returns:
            Number of secrets refreshed
        """
        refreshed_count = 0
        
        for secret_name in list(self._cache.keys()):
            try:
                secret_value = await self._fetch_secret(secret_name)
                if secret_value:
                    self._cache_secret(secret_name, secret_value)
                    refreshed_count += 1
                else:
                    # Remove from cache if no longer available
                    del self._cache[secret_name]
                    
            except Exception as e:
                logger.error("Failed to refresh secret", extra={
                    'secret_name': secret_name,
                    'error': str(e)
                })
        
        logger.info("Cache refresh completed", extra={
            'refreshed_count': refreshed_count,
            'total_cached': len(self._cache)
        })
        
        return refreshed_count
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        now = datetime.now()
        expired_count = sum(1 for cached in self._cache.values() if cached.expires_at <= now)
        
        return {
            'total_cached': len(self._cache),
            'expired_count': expired_count,
            'active_count': len(self._cache) - expired_count,
            'cache_ttl_seconds': self.config.cache_ttl_seconds,
            'provider': self.config.provider.value
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on secret manager."""
        health_status = {
            'status': 'healthy',
            'provider': self.config.provider.value,
            'initialized': self._initialized,
            'cache_stats': self.get_cache_stats(),
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Test secret retrieval
            if self.config.provider == SecretProvider.AZURE_KEY_VAULT and self._client:
                # Test Azure connection
                await asyncio.get_event_loop().run_in_executor(
                    None, lambda: list(self._client.list_properties_of_secrets(max_page_size=1))
                )
                health_status['azure_connection'] = 'healthy'
            elif self.config.provider == SecretProvider.LOCAL_FILE:
                # Test local file access
                if self.config.local_secrets_file and os.path.exists(self.config.local_secrets_file):
                    health_status['local_file_access'] = 'healthy'
                else:
                    health_status['local_file_access'] = 'file_not_found'
                    health_status['status'] = 'degraded'
            
        except Exception as e:
            health_status['status'] = 'unhealthy'
            health_status['error'] = str(e)
            logger.error("Secret manager health check failed", extra={
                'error': str(e)
            })
        
        return health_status


# Global secret manager instance
_secret_manager: Optional[SecretManager] = None


def get_secret_manager() -> Optional[SecretManager]:
    """Get the global secret manager instance."""
    return _secret_manager


def initialize_secret_manager(config: SecretConfig) -> SecretManager:
    """Initialize the global secret manager."""
    global _secret_manager
    _secret_manager = SecretManager(config)
    return _secret_manager


async def get_secret(secret_name: str, default: Optional[str] = None) -> Optional[str]:
    """Convenience function to get a secret."""
    if _secret_manager:
        return await _secret_manager.get_secret(secret_name, default)
    else:
        logger.warning("Secret manager not initialized, using environment fallback")
        return os.getenv(secret_name, default)


# Common secret names
class SecretNames:
    """Common secret names used in the application."""
    OPENAI_API_KEY = "openai-api-key"
    ANTHROPIC_API_KEY = "anthropic-api-key"
    DEEPSEEK_API_KEY = "deepseek-api-key"
    DATABASE_URL = "database-url"
    REDIS_URL = "redis-url"
    JWT_SECRET_KEY = "jwt-secret-key"
    ENCRYPTION_KEY = "encryption-key"
    WEBHOOK_SECRET = "webhook-secret"
    AZURE_STORAGE_KEY = "azure-storage-key"
    AWS_ACCESS_KEY = "aws-access-key"
    AWS_SECRET_KEY = "aws-secret-key"