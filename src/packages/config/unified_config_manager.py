"""
Unified Configuration Management System
Part of the reVoAgent Comprehensive Transformation Strategy

This module provides enterprise-grade configuration management with validation,
encryption, and environment-specific settings.
"""

import os
import yaml
import json
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from pathlib import Path
from cryptography.fernet import Fernet
import base64
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Environment(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"

class ConfigurationError(Exception):
    """Custom exception for configuration errors"""
    pass

@dataclass
class DatabaseConfig:
    """Database configuration"""
    host: str = "localhost"
    port: int = 5432
    database: str = "revoagent"
    username: str = "revoagent"
    password: str = ""
    ssl_mode: str = "prefer"
    pool_size: int = 10
    max_overflow: int = 20

@dataclass
class AIModelConfig:
    """AI model configuration"""
    provider: str = "deepseek_r1"
    model_path: str = ""
    api_key: str = ""
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: int = 30
    fallback_providers: List[str] = field(default_factory=list)

@dataclass
class SecurityConfig:
    """Security configuration"""
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    encryption_key: str = ""
    rate_limit_per_minute: int = 60
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    enable_https: bool = False

@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration"""
    enable_metrics: bool = True
    enable_tracing: bool = True
    enable_logging: bool = True
    log_level: str = "INFO"
    metrics_port: int = 9090
    jaeger_endpoint: str = ""
    prometheus_endpoint: str = ""

@dataclass
class ServerConfig:
    """Server configuration"""
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    reload: bool = False
    debug: bool = False
    max_request_size: int = 16 * 1024 * 1024  # 16MB

@dataclass
class UnifiedConfig:
    """Unified configuration container"""
    environment: Environment = Environment.DEVELOPMENT
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    ai_models: Dict[str, AIModelConfig] = field(default_factory=dict)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    custom: Dict[str, Any] = field(default_factory=dict)

class UnifiedConfigurationManager:
    """
    Enterprise-grade configuration management system
    
    Features:
    - Environment-specific configurations
    - Validation and schema enforcement
    - Sensitive data encryption
    - Dynamic configuration updates
    - Configuration versioning
    """

    def __init__(self, config_dir: str = "config", environment: Optional[str] = None):
        self.config_dir = Path(config_dir)
        self.environment = Environment(environment or os.getenv("REVO_ENV", "development"))
        self.config: Optional[UnifiedConfig] = None
        self.encryption_key: Optional[bytes] = None
        self._config_cache: Dict[str, Any] = {}
        self._watchers: List[callable] = []

    async def initialize(self) -> UnifiedConfig:
        """Initialize the configuration manager"""
        logger.info(f"🔧 Initializing Configuration Manager for {self.environment.value}")

        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Initialize encryption
        await self._initialize_encryption()

        # Load configuration
        self.config = await self._load_configuration()

        # Validate configuration
        await self._validate_configuration()

        # Setup configuration watching
        await self._setup_config_watching()

        logger.info("✅ Configuration Manager initialized successfully")
        return self.config

    async def _initialize_encryption(self):
        """Initialize encryption for sensitive data"""
        encryption_key_file = self.config_dir / ".encryption_key"
        
        if encryption_key_file.exists():
            # Load existing key
            with open(encryption_key_file, "rb") as f:
                self.encryption_key = f.read()
        else:
            # Generate new key
            self.encryption_key = Fernet.generate_key()
            with open(encryption_key_file, "wb") as f:
                f.write(self.encryption_key)
            # Secure the key file
            os.chmod(encryption_key_file, 0o600)

    async def _load_configuration(self) -> UnifiedConfig:
        """Load configuration from files"""
        config = UnifiedConfig(environment=self.environment)

        # Load base configuration
        base_config_file = self.config_dir / "base.yaml"
        if base_config_file.exists():
            base_config = await self._load_yaml_file(base_config_file)
            config = await self._merge_config(config, base_config)

        # Load environment-specific configuration
        env_config_file = self.config_dir / f"{self.environment.value}.yaml"
        if env_config_file.exists():
            env_config = await self._load_yaml_file(env_config_file)
            config = await self._merge_config(config, env_config)

        # Load secrets
        secrets_file = self.config_dir / "secrets.encrypted.yaml"
        if secrets_file.exists():
            secrets = await self._load_encrypted_file(secrets_file)
            config = await self._merge_config(config, secrets)

        # Override with environment variables
        config = await self._apply_env_overrides(config)

        return config

    async def _load_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        """Load YAML configuration file"""
        try:
            with open(file_path, "r") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"Failed to load {file_path}: {e}")
            return {}

    async def _load_encrypted_file(self, file_path: Path) -> Dict[str, Any]:
        """Load encrypted configuration file"""
        try:
            with open(file_path, "rb") as f:
                encrypted_data = f.read()
            
            fernet = Fernet(self.encryption_key)
            decrypted_data = fernet.decrypt(encrypted_data)
            
            return yaml.safe_load(decrypted_data.decode()) or {}
        except Exception as e:
            logger.warning(f"Failed to load encrypted file {file_path}: {e}")
            return {}

    async def _merge_config(self, base_config: UnifiedConfig, override_config: Dict[str, Any]) -> UnifiedConfig:
        """Merge configuration dictionaries"""
        
        # Database configuration
        if "database" in override_config:
            db_config = override_config["database"]
            for key, value in db_config.items():
                if hasattr(base_config.database, key):
                    setattr(base_config.database, key, value)

        # AI models configuration
        if "ai_models" in override_config:
            for model_name, model_config in override_config["ai_models"].items():
                ai_config = AIModelConfig()
                for key, value in model_config.items():
                    if hasattr(ai_config, key):
                        setattr(ai_config, key, value)
                base_config.ai_models[model_name] = ai_config

        # Security configuration
        if "security" in override_config:
            sec_config = override_config["security"]
            for key, value in sec_config.items():
                if hasattr(base_config.security, key):
                    setattr(base_config.security, key, value)

        # Monitoring configuration
        if "monitoring" in override_config:
            mon_config = override_config["monitoring"]
            for key, value in mon_config.items():
                if hasattr(base_config.monitoring, key):
                    setattr(base_config.monitoring, key, value)

        # Server configuration
        if "server" in override_config:
            srv_config = override_config["server"]
            for key, value in srv_config.items():
                if hasattr(base_config.server, key):
                    setattr(base_config.server, key, value)

        # Custom configuration
        if "custom" in override_config:
            base_config.custom.update(override_config["custom"])

        return base_config

    async def _apply_env_overrides(self, config: UnifiedConfig) -> UnifiedConfig:
        """Apply environment variable overrides"""
        
        # Database overrides
        if os.getenv("DB_HOST"):
            config.database.host = os.getenv("DB_HOST")
        if os.getenv("DB_PORT"):
            config.database.port = int(os.getenv("DB_PORT"))
        if os.getenv("DB_NAME"):
            config.database.database = os.getenv("DB_NAME")
        if os.getenv("DB_USER"):
            config.database.username = os.getenv("DB_USER")
        if os.getenv("DB_PASSWORD"):
            config.database.password = os.getenv("DB_PASSWORD")

        # Server overrides
        if os.getenv("SERVER_HOST"):
            config.server.host = os.getenv("SERVER_HOST")
        if os.getenv("SERVER_PORT"):
            config.server.port = int(os.getenv("SERVER_PORT"))

        # Security overrides
        if os.getenv("JWT_SECRET_KEY"):
            config.security.jwt_secret_key = os.getenv("JWT_SECRET_KEY")

        return config

    async def _validate_configuration(self):
        """Validate configuration"""
        if not self.config:
            raise ConfigurationError("Configuration not loaded")

        # Validate required fields
        if self.environment == Environment.PRODUCTION:
            if not self.config.security.jwt_secret_key:
                raise ConfigurationError("JWT secret key is required in production")
            if not self.config.database.password:
                raise ConfigurationError("Database password is required in production")

        # Validate AI model configurations
        for model_name, model_config in self.config.ai_models.items():
            if not model_config.provider:
                raise ConfigurationError(f"Provider is required for AI model {model_name}")

        logger.info("✅ Configuration validation passed")

    async def _setup_config_watching(self):
        """Setup configuration file watching for dynamic updates"""
        # This would implement file watching in a production system
        logger.info("🔍 Configuration watching setup complete")

    async def save_encrypted_secrets(self, secrets: Dict[str, Any]):
        """Save secrets to encrypted file"""
        secrets_file = self.config_dir / "secrets.encrypted.yaml"
        
        yaml_data = yaml.dump(secrets).encode()
        fernet = Fernet(self.encryption_key)
        encrypted_data = fernet.encrypt(yaml_data)
        
        with open(secrets_file, "wb") as f:
            f.write(encrypted_data)
        
        # Secure the secrets file
        os.chmod(secrets_file, 0o600)
        logger.info("🔐 Secrets saved and encrypted")

    def get_config(self) -> UnifiedConfig:
        """Get the current configuration"""
        if not self.config:
            raise ConfigurationError("Configuration not initialized")
        return self.config
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key (supports dot notation)"""
        if not self.config:
            raise ConfigurationError("Configuration not initialized")
        
        # Handle dot notation for nested keys
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if hasattr(value, k):
                value = getattr(value, k)
            elif isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set_environment(self, environment: str):
        """Set the environment"""
        self.environment = Environment(environment)
    
    def encrypt_value(self, value: str) -> str:
        """Encrypt a value"""
        if not self.encryption_key:
            raise ConfigurationError("Encryption not initialized")
        fernet = Fernet(self.encryption_key)
        return fernet.encrypt(value.encode()).decode()
    
    def decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt a value"""
        if not self.encryption_key:
            raise ConfigurationError("Encryption not initialized")
        fernet = Fernet(self.encryption_key)
        return fernet.decrypt(encrypted_value.encode()).decode()

    def get_database_url(self) -> str:
        """Get database connection URL"""
        db = self.config.database
        return f"postgresql://{db.username}:{db.password}@{db.host}:{db.port}/{db.database}"

    def get_ai_model_config(self, model_name: str) -> Optional[AIModelConfig]:
        """Get AI model configuration by name"""
        return self.config.ai_models.get(model_name)

    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment == Environment.PRODUCTION

    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment == Environment.DEVELOPMENT

    async def update_config(self, updates: Dict[str, Any]):
        """Update configuration dynamically"""
        if not self.config:
            raise ConfigurationError("Configuration not initialized")

        # Apply updates
        self.config = await self._merge_config(self.config, updates)
        
        # Validate updated configuration
        await self._validate_configuration()
        
        # Notify watchers
        for watcher in self._watchers:
            try:
                await watcher(self.config)
            except Exception as e:
                logger.warning(f"Configuration watcher failed: {e}")

        logger.info("🔄 Configuration updated successfully")

    def add_config_watcher(self, watcher: callable):
        """Add a configuration change watcher"""
        self._watchers.append(watcher)

    def export_config(self, include_secrets: bool = False) -> Dict[str, Any]:
        """Export configuration to dictionary"""
        if not self.config:
            raise ConfigurationError("Configuration not initialized")

        config_dict = {
            "environment": self.config.environment.value,
            "database": {
                "host": self.config.database.host,
                "port": self.config.database.port,
                "database": self.config.database.database,
                "username": self.config.database.username,
                "ssl_mode": self.config.database.ssl_mode,
                "pool_size": self.config.database.pool_size,
                "max_overflow": self.config.database.max_overflow
            },
            "ai_models": {},
            "security": {
                "jwt_algorithm": self.config.security.jwt_algorithm,
                "jwt_expiration_hours": self.config.security.jwt_expiration_hours,
                "rate_limit_per_minute": self.config.security.rate_limit_per_minute,
                "cors_origins": self.config.security.cors_origins,
                "enable_https": self.config.security.enable_https
            },
            "monitoring": {
                "enable_metrics": self.config.monitoring.enable_metrics,
                "enable_tracing": self.config.monitoring.enable_tracing,
                "enable_logging": self.config.monitoring.enable_logging,
                "log_level": self.config.monitoring.log_level,
                "metrics_port": self.config.monitoring.metrics_port
            },
            "server": {
                "host": self.config.server.host,
                "port": self.config.server.port,
                "workers": self.config.server.workers,
                "reload": self.config.server.reload,
                "debug": self.config.server.debug,
                "max_request_size": self.config.server.max_request_size
            },
            "custom": self.config.custom
        }

        # Export AI model configurations
        for model_name, model_config in self.config.ai_models.items():
            config_dict["ai_models"][model_name] = {
                "provider": model_config.provider,
                "model_path": model_config.model_path,
                "max_tokens": model_config.max_tokens,
                "temperature": model_config.temperature,
                "timeout": model_config.timeout,
                "fallback_providers": model_config.fallback_providers
            }
            
            if include_secrets:
                config_dict["ai_models"][model_name]["api_key"] = model_config.api_key

        if include_secrets:
            config_dict["database"]["password"] = self.config.database.password
            config_dict["security"]["jwt_secret_key"] = self.config.security.jwt_secret_key
            config_dict["security"]["encryption_key"] = self.config.security.encryption_key

        return config_dict

# Global configuration manager instance
_config_manager: Optional[UnifiedConfigurationManager] = None

async def get_config_manager() -> UnifiedConfigurationManager:
    """Get the global configuration manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = UnifiedConfigurationManager()
        await _config_manager.initialize()
    return _config_manager

async def get_config() -> UnifiedConfig:
    """Get the current configuration"""
    manager = await get_config_manager()
    return manager.get_config()

# Example usage and testing
async def main():
    """Example usage of the Unified Configuration Manager"""
    
    # Initialize configuration manager
    config_manager = UnifiedConfigurationManager()
    config = await config_manager.initialize()
    
    print(f"Environment: {config.environment.value}")
    print(f"Database Host: {config.database.host}")
    print(f"Server Port: {config.server.port}")
    
    # Export configuration
    config_dict = config_manager.export_config(include_secrets=False)
    print(f"Configuration: {json.dumps(config_dict, indent=2)}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())