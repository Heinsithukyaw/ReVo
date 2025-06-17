"""
Enterprise Secrets Management
Secure handling of API keys, database credentials, and other sensitive data
"""

import os
import json
import asyncio
import logging
from typing import Dict, Any, Optional, Union, List
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import lru_cache
import base64
import hashlib
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SecretNotFoundError(Exception):
    """Raised when a secret is not found"""
    pass

class SecretValidationError(Exception):
    """Raised when secret validation fails"""
    pass

@dataclass
class SecretMetadata:
    """Metadata for secrets"""
    name: str
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None
    rotation_interval: Optional[timedelta] = None
    tags: Dict[str, str] = None
    encrypted: bool = True

class SecretsManager(ABC):
    """
    Abstract base class for secrets management
    """
    
    @abstractmethod
    async def get_secret(self, name: str) -> str:
        """Get a secret by name"""
        pass
    
    @abstractmethod
    async def set_secret(self, name: str, value: str, metadata: SecretMetadata = None) -> bool:
        """Set a secret"""
        pass
    
    @abstractmethod
    async def delete_secret(self, name: str) -> bool:
        """Delete a secret"""
        pass
    
    @abstractmethod
    async def list_secrets(self) -> List[str]:
        """List all secret names"""
        pass
    
    @abstractmethod
    async def rotate_secret(self, name: str, new_value: str) -> bool:
        """Rotate a secret"""
        pass

class EnvironmentSecretsManager(SecretsManager):
    """
    Environment-based secrets manager for development
    """
    
    def __init__(self, prefix: str = "REVOAGENT_"):
        self.prefix = prefix
        self._cache = {}
        logger.info(f"🔐 Environment secrets manager initialized with prefix: {prefix}")
    
    async def get_secret(self, name: str) -> str:
        """Get secret from environment variables"""
        env_name = f"{self.prefix}{name.upper()}"
        
        # Check cache first
        if env_name in self._cache:
            return self._cache[env_name]
        
        value = os.getenv(env_name)
        if value is None:
            raise SecretNotFoundError(f"Secret '{name}' not found in environment")
        
        # Cache the value
        self._cache[env_name] = value
        logger.debug(f"🔑 Retrieved secret '{name}' from environment")
        
        return value
    
    async def set_secret(self, name: str, value: str, metadata: SecretMetadata = None) -> bool:
        """Set secret in environment (for testing only)"""
        env_name = f"{self.prefix}{name.upper()}"
        os.environ[env_name] = value
        self._cache[env_name] = value
        
        logger.info(f"🔐 Set secret '{name}' in environment")
        return True
    
    async def delete_secret(self, name: str) -> bool:
        """Delete secret from environment"""
        env_name = f"{self.prefix}{name.upper()}"
        
        if env_name in os.environ:
            del os.environ[env_name]
        
        if env_name in self._cache:
            del self._cache[env_name]
        
        logger.info(f"🗑️ Deleted secret '{name}' from environment")
        return True
    
    async def list_secrets(self) -> List[str]:
        """List all secrets with the prefix"""
        secrets = []
        for key in os.environ.keys():
            if key.startswith(self.prefix):
                secret_name = key[len(self.prefix):].lower()
                secrets.append(secret_name)
        
        return secrets
    
    async def rotate_secret(self, name: str, new_value: str) -> bool:
        """Rotate a secret"""
        return await self.set_secret(name, new_value)

class VaultSecretsManager(SecretsManager):
    """
    HashiCorp Vault secrets manager for production
    """
    
    def __init__(self, vault_url: str = None, vault_token: str = None, mount_point: str = "secret"):
        self.vault_url = vault_url or os.getenv("VAULT_URL", "http://localhost:8200")
        self.vault_token = vault_token or os.getenv("VAULT_TOKEN")
        self.mount_point = mount_point
        self.client = None
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes cache TTL
        self._cache_timestamps = {}
        
        if not self.vault_token:
            raise ValueError("Vault token is required")
        
        logger.info(f"🏛️ Vault secrets manager initialized: {self.vault_url}")
    
    async def _get_client(self):
        """Get or create Vault client"""
        if self.client is None:
            try:
                import hvac
                self.client = hvac.Client(url=self.vault_url, token=self.vault_token)
                
                if not self.client.is_authenticated():
                    raise Exception("Vault authentication failed")
                
                logger.info("✅ Vault client authenticated successfully")
                
            except ImportError:
                raise ImportError("hvac library is required for Vault integration. Install with: pip install hvac")
            except Exception as e:
                logger.error(f"❌ Vault client initialization failed: {str(e)}")
                raise
        
        return self.client
    
    def _is_cache_valid(self, name: str) -> bool:
        """Check if cached value is still valid"""
        if name not in self._cache_timestamps:
            return False
        
        cache_time = self._cache_timestamps[name]
        return (datetime.now() - cache_time).total_seconds() < self._cache_ttl
    
    async def get_secret(self, name: str) -> str:
        """Get secret from Vault"""
        # Check cache first
        if name in self._cache and self._is_cache_valid(name):
            logger.debug(f"🔑 Retrieved secret '{name}' from cache")
            return self._cache[name]
        
        try:
            client = await self._get_client()
            
            # Read secret from Vault
            response = client.secrets.kv.v2.read_secret_version(
                path=name,
                mount_point=self.mount_point
            )
            
            if not response or 'data' not in response or 'data' not in response['data']:
                raise SecretNotFoundError(f"Secret '{name}' not found in Vault")
            
            secret_data = response['data']['data']
            
            # Handle different secret formats
            if 'value' in secret_data:
                value = secret_data['value']
            elif len(secret_data) == 1:
                value = list(secret_data.values())[0]
            else:
                # Return as JSON if multiple values
                value = json.dumps(secret_data)
            
            # Cache the value
            self._cache[name] = value
            self._cache_timestamps[name] = datetime.now()
            
            logger.debug(f"🔑 Retrieved secret '{name}' from Vault")
            return value
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve secret '{name}' from Vault: {str(e)}")
            raise SecretNotFoundError(f"Failed to retrieve secret '{name}': {str(e)}")
    
    async def set_secret(self, name: str, value: str, metadata: SecretMetadata = None) -> bool:
        """Set secret in Vault"""
        try:
            client = await self._get_client()
            
            secret_data = {"value": value}
            
            # Add metadata if provided
            if metadata:
                secret_data.update({
                    "created_at": metadata.created_at.isoformat(),
                    "updated_at": metadata.updated_at.isoformat(),
                    "tags": metadata.tags or {}
                })
                
                if metadata.expires_at:
                    secret_data["expires_at"] = metadata.expires_at.isoformat()
            
            # Write secret to Vault
            client.secrets.kv.v2.create_or_update_secret(
                path=name,
                secret=secret_data,
                mount_point=self.mount_point
            )
            
            # Update cache
            self._cache[name] = value
            self._cache_timestamps[name] = datetime.now()
            
            logger.info(f"🔐 Set secret '{name}' in Vault")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to set secret '{name}' in Vault: {str(e)}")
            return False
    
    async def delete_secret(self, name: str) -> bool:
        """Delete secret from Vault"""
        try:
            client = await self._get_client()
            
            # Delete secret from Vault
            client.secrets.kv.v2.delete_metadata_and_all_versions(
                path=name,
                mount_point=self.mount_point
            )
            
            # Remove from cache
            if name in self._cache:
                del self._cache[name]
            if name in self._cache_timestamps:
                del self._cache_timestamps[name]
            
            logger.info(f"🗑️ Deleted secret '{name}' from Vault")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to delete secret '{name}' from Vault: {str(e)}")
            return False
    
    async def list_secrets(self) -> List[str]:
        """List all secrets in Vault"""
        try:
            client = await self._get_client()
            
            response = client.secrets.kv.v2.list_secrets(
                path="",
                mount_point=self.mount_point
            )
            
            if response and 'data' in response and 'keys' in response['data']:
                return response['data']['keys']
            
            return []
            
        except Exception as e:
            logger.error(f"❌ Failed to list secrets from Vault: {str(e)}")
            return []
    
    async def rotate_secret(self, name: str, new_value: str) -> bool:
        """Rotate a secret in Vault"""
        metadata = SecretMetadata(
            name=name,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            tags={"rotated": "true", "rotation_date": datetime.now().isoformat()}
        )
        
        return await self.set_secret(name, new_value, metadata)
    
    def clear_cache(self):
        """Clear the secrets cache"""
        self._cache.clear()
        self._cache_timestamps.clear()
        logger.info("🧹 Vault secrets cache cleared")

class SecureSecretsManager:
    """
    High-level secrets manager with encryption and validation
    """
    
    def __init__(self, backend: SecretsManager, encryption_key: str = None):
        self.backend = backend
        self.encryption_key = encryption_key or self._generate_encryption_key()
        self._secret_validators = {}
        
        logger.info(f"🔒 Secure secrets manager initialized with backend: {type(backend).__name__}")
    
    def _generate_encryption_key(self) -> str:
        """Generate encryption key from environment or create new one"""
        key = os.getenv("REVOAGENT_ENCRYPTION_KEY")
        if not key:
            import secrets
            key = base64.b64encode(secrets.token_bytes(32)).decode()
            logger.warning("⚠️ Generated new encryption key. Set REVOAGENT_ENCRYPTION_KEY environment variable for persistence.")
        
        return key
    
    def _encrypt_value(self, value: str) -> str:
        """Encrypt a secret value"""
        try:
            from cryptography.fernet import Fernet
            
            # Create Fernet instance with key
            key_bytes = base64.b64decode(self.encryption_key.encode())
            if len(key_bytes) != 32:
                # Hash the key to ensure it's 32 bytes
                key_bytes = hashlib.sha256(self.encryption_key.encode()).digest()
            
            fernet_key = base64.urlsafe_b64encode(key_bytes)
            fernet = Fernet(fernet_key)
            
            # Encrypt the value
            encrypted_value = fernet.encrypt(value.encode())
            return base64.b64encode(encrypted_value).decode()
            
        except ImportError:
            logger.warning("⚠️ cryptography library not available. Storing secrets unencrypted.")
            return value
        except Exception as e:
            logger.error(f"❌ Encryption failed: {str(e)}")
            return value
    
    def _decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt a secret value"""
        try:
            from cryptography.fernet import Fernet
            
            # Create Fernet instance with key
            key_bytes = base64.b64decode(self.encryption_key.encode())
            if len(key_bytes) != 32:
                key_bytes = hashlib.sha256(self.encryption_key.encode()).digest()
            
            fernet_key = base64.urlsafe_b64encode(key_bytes)
            fernet = Fernet(fernet_key)
            
            # Decrypt the value
            encrypted_bytes = base64.b64decode(encrypted_value.encode())
            decrypted_value = fernet.decrypt(encrypted_bytes)
            return decrypted_value.decode()
            
        except ImportError:
            # No encryption available, return as-is
            return encrypted_value
        except Exception as e:
            logger.error(f"❌ Decryption failed: {str(e)}")
            # Try returning as-is in case it wasn't encrypted
            return encrypted_value
    
    def add_validator(self, secret_name: str, validator_func):
        """Add a validator function for a secret"""
        self._secret_validators[secret_name] = validator_func
        logger.info(f"📋 Added validator for secret '{secret_name}'")
    
    def _validate_secret(self, name: str, value: str) -> bool:
        """Validate a secret value"""
        if name in self._secret_validators:
            try:
                return self._secret_validators[name](value)
            except Exception as e:
                logger.error(f"❌ Secret validation failed for '{name}': {str(e)}")
                return False
        
        return True
    
    async def get_secret(self, name: str) -> str:
        """Get and decrypt a secret"""
        encrypted_value = await self.backend.get_secret(name)
        decrypted_value = self._decrypt_value(encrypted_value)
        
        # Validate the secret
        if not self._validate_secret(name, decrypted_value):
            raise SecretValidationError(f"Secret '{name}' failed validation")
        
        return decrypted_value
    
    async def set_secret(self, name: str, value: str, metadata: SecretMetadata = None) -> bool:
        """Encrypt and set a secret"""
        # Validate the secret before storing
        if not self._validate_secret(name, value):
            raise SecretValidationError(f"Secret '{name}' failed validation")
        
        encrypted_value = self._encrypt_value(value)
        return await self.backend.set_secret(name, encrypted_value, metadata)
    
    async def rotate_secret(self, name: str, new_value: str) -> bool:
        """Rotate a secret with validation"""
        if not self._validate_secret(name, new_value):
            raise SecretValidationError(f"New secret value for '{name}' failed validation")
        
        encrypted_value = self._encrypt_value(new_value)
        return await self.backend.rotate_secret(name, encrypted_value)
    
    # Delegate other methods to backend
    async def delete_secret(self, name: str) -> bool:
        return await self.backend.delete_secret(name)
    
    async def list_secrets(self) -> List[str]:
        return await self.backend.list_secrets()

class SecretsManagerFactory:
    """
    Factory for creating secrets managers
    """
    
    @staticmethod
    def create_secrets_manager(backend_type: str = "auto", **kwargs) -> SecretsManager:
        """Create a secrets manager based on environment"""
        
        if backend_type == "auto":
            # Auto-detect based on environment
            if os.getenv("VAULT_URL") and os.getenv("VAULT_TOKEN"):
                backend_type = "vault"
            else:
                backend_type = "environment"
        
        if backend_type == "vault":
            return VaultSecretsManager(**kwargs)
        elif backend_type == "environment":
            return EnvironmentSecretsManager(**kwargs)
        else:
            raise ValueError(f"Unknown backend type: {backend_type}")
    
    @staticmethod
    def create_secure_secrets_manager(backend_type: str = "auto", **kwargs) -> SecureSecretsManager:
        """Create a secure secrets manager with encryption"""
        backend = SecretsManagerFactory.create_secrets_manager(backend_type, **kwargs)
        return SecureSecretsManager(backend)

# Convenience functions for common secret types
class CommonSecrets:
    """
    Helper class for managing common secret types
    """
    
    def __init__(self, secrets_manager: SecretsManager):
        self.secrets_manager = secrets_manager
    
    async def get_database_url(self) -> str:
        """Get database connection URL"""
        return await self.secrets_manager.get_secret("database_url")
    
    async def get_api_key(self, service: str) -> str:
        """Get API key for a service"""
        return await self.secrets_manager.get_secret(f"{service}_api_key")
    
    async def get_jwt_secret(self) -> str:
        """Get JWT signing secret"""
        return await self.secrets_manager.get_secret("jwt_secret")
    
    async def get_encryption_key(self) -> str:
        """Get encryption key"""
        return await self.secrets_manager.get_secret("encryption_key")
    
    async def set_database_credentials(self, host: str, port: int, username: str, password: str, database: str):
        """Set database credentials"""
        db_url = f"postgresql://{username}:{password}@{host}:{port}/{database}"
        await self.secrets_manager.set_secret("database_url", db_url)
    
    async def set_api_key(self, service: str, api_key: str):
        """Set API key for a service"""
        await self.secrets_manager.set_secret(f"{service}_api_key", api_key)

# Global secrets manager instance
_secrets_manager: Optional[SecretsManager] = None

def get_secrets_manager() -> SecretsManager:
    """Get the global secrets manager instance"""
    global _secrets_manager
    
    if _secrets_manager is None:
        _secrets_manager = SecretsManagerFactory.create_secure_secrets_manager()
    
    return _secrets_manager

def set_secrets_manager(manager: SecretsManager):
    """Set the global secrets manager instance"""
    global _secrets_manager
    _secrets_manager = manager

# Convenience functions
async def get_secret(name: str) -> str:
    """Get a secret using the global secrets manager"""
    manager = get_secrets_manager()
    return await manager.get_secret(name)

async def set_secret(name: str, value: str) -> bool:
    """Set a secret using the global secrets manager"""
    manager = get_secrets_manager()
    return await manager.set_secret(name, value)

if __name__ == "__main__":
    # Example usage
    async def test_secrets_manager():
        # Test environment secrets manager
        env_manager = EnvironmentSecretsManager()
        
        # Set a test secret
        await env_manager.set_secret("test_api_key", "sk-test123456")
        
        # Get the secret
        api_key = await env_manager.get_secret("test_api_key")
        print(f"Retrieved API key: {api_key}")
        
        # Test secure secrets manager with encryption
        secure_manager = SecureSecretsManager(env_manager)
        
        # Add validator for API keys
        def validate_api_key(value: str) -> bool:
            return value.startswith("sk-") and len(value) > 10
        
        secure_manager.add_validator("test_api_key", validate_api_key)
        
        # Set and get encrypted secret
        await secure_manager.set_secret("encrypted_key", "sk-encrypted123456")
        encrypted_key = await secure_manager.get_secret("encrypted_key")
        print(f"Retrieved encrypted key: {encrypted_key}")
        
        # Test common secrets helper
        common = CommonSecrets(secure_manager)
        await common.set_api_key("openai", "sk-openai123456")
        openai_key = await common.get_api_key("openai")
        print(f"OpenAI API key: {openai_key}")
    
    asyncio.run(test_secrets_manager())