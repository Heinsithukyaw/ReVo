"""
Enterprise Configuration Management for reVoAgent
Handles all configuration loading and validation
"""
import os
import logging
from typing import Optional, List, Dict, Any
from functools import lru_cache
from pydantic import BaseSettings, Field, validator
from pathlib import Path

logger = logging.getLogger(__name__)

class DatabaseSettings(BaseSettings):
    """Database configuration settings"""
    host: str = Field(default="localhost", env="DB_HOST")
    port: int = Field(default=5433, env="DB_PORT")
    name: str = Field(default="revoagent", env="DB_NAME")
    user: str = Field(default="revoagent", env="DB_USER")
    password: str = Field(default="revoagent_enterprise_secure_2024", env="DB_PASSWORD")
    
    @property
    def url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

class RedisSettings(BaseSettings):
    """Redis configuration settings"""
    host: str = Field(default="localhost", env="REDIS_HOST")
    port: int = Field(default=6380, env="REDIS_PORT")
    db: int = Field(default=0, env="REDIS_DB")
    password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    @property
    def url(self) -> str:
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"

class LLMSettings(BaseSettings):
    """LLM configuration settings"""
    use_local_models: bool = Field(default=True, env="USE_LOCAL_MODELS")
    primary_model: str = Field(default="deepseek_r1", env="PRIMARY_MODEL")
    fallback_model: str = Field(default="openai", env="FALLBACK_MODEL")
    deepseek_model_path: str = Field(default="./models/deepseek-r1.gguf", env="DEEPSEEK_MODEL_PATH")
    model_timeout: int = Field(default=30, env="MODEL_TIMEOUT")
    max_tokens: int = Field(default=2048, env="MAX_TOKENS")
    temperature: float = Field(default=0.7, env="TEMPERATURE")
    
    # API Keys
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    huggingface_api_key: Optional[str] = Field(default=None, env="HUGGINGFACE_API_KEY")

class SecuritySettings(BaseSettings):
    """Security configuration settings"""
    jwt_secret: str = Field(default="revoagent_enterprise_jwt_ultra_secure_key_2024_production", env="JWT_SECRET")
    api_key: str = Field(default="revoagent_enterprise_api_key_2024", env="API_KEY")
    cors_origins: List[str] = Field(default=["http://localhost:3000"], env="CORS_ORIGINS")
    allowed_hosts: List[str] = Field(default=["localhost", "127.0.0.1"], env="ALLOWED_HOSTS")
    
    @validator('cors_origins', pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            # Handle JSON string format from environment
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                # Fallback to comma-separated
                return [origin.strip() for origin in v.split(',')]
        return v

class MonitoringSettings(BaseSettings):
    """Monitoring and observability settings"""
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    prometheus_enabled: bool = Field(default=True, env="PROMETHEUS_ENABLED")
    grafana_enabled: bool = Field(default=True, env="GRAFANA_ENABLED")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    structured_logging: bool = Field(default=True, env="STRUCTURED_LOGGING")
    health_check_interval: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")

class PerformanceSettings(BaseSettings):
    """Performance configuration settings"""
    async_workers: int = Field(default=8, env="ASYNC_WORKERS")
    connection_pool_size: int = Field(default=20, env="CONNECTION_POOL_SIZE")
    query_timeout: int = Field(default=30, env="QUERY_TIMEOUT")
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")

class ThreeEngineSettings(BaseSettings):
    """Three-Engine architecture settings"""
    enable_three_engines: bool = Field(default=True, env="ENABLE_THREE_ENGINES")
    perfect_recall_enabled: bool = Field(default=True, env="PERFECT_RECALL_ENABLED")
    parallel_mind_enabled: bool = Field(default=True, env="PARALLEL_MIND_ENABLED")
    creative_engine_enabled: bool = Field(default=True, env="CREATIVE_ENGINE_ENABLED")
    engine_coordination_timeout: int = Field(default=10, env="ENGINE_COORDINATION_TIMEOUT")

class MemorySettings(BaseSettings):
    """Memory and knowledge system settings"""
    enable_memory_system: bool = Field(default=True, env="ENABLE_MEMORY_SYSTEM")
    cognee_enabled: bool = Field(default=True, env="COGNEE_ENABLED")
    vector_db_path: str = Field(default="./data/vectors", env="VECTOR_DB_PATH")
    knowledge_graph_enabled: bool = Field(default=True, env="KNOWLEDGE_GRAPH_ENABLED")
    memory_retention_days: int = Field(default=365, env="MEMORY_RETENTION_DAYS")

class Settings(BaseSettings):
    """Main application settings"""
    
    # Basic app settings
    app_name: str = Field(default="reVoAgent Enterprise", env="APP_NAME")
    app_version: str = Field(default="2.0.0", env="APP_VERSION")
    environment: str = Field(default="enterprise", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Server settings
    backend_host: str = Field(default="0.0.0.0", env="BACKEND_HOST")
    backend_port: int = Field(default=8080, env="BACKEND_PORT")
    frontend_port: int = Field(default=3000, env="FRONTEND_PORT")
    memory_port: int = Field(default=8082, env="MEMORY_PORT")
    engine_port: int = Field(default=8084, env="ENGINE_PORT")
    
    # API settings
    api_prefix: str = Field(default="/api/v1", env="API_PREFIX")
    max_workers: int = Field(default=4, env="MAX_WORKERS")
    timeout: int = Field(default=30, env="TIMEOUT")
    
    # URLs
    api_url: str = Field(default="http://localhost:8080", env="VITE_API_URL")
    ws_url: str = Field(default="ws://localhost:8084", env="VITE_WS_URL")
    memory_api_url: str = Field(default="http://localhost:8082", env="MEMORY_API_URL")
    engine_api_url: str = Field(default="http://localhost:8084", env="ENGINE_API_URL")
    
    # File paths
    upload_dir: str = Field(default="./data/uploads", env="UPLOAD_DIR")
    models_dir: str = Field(default="./models", env="MODELS_DIR")
    logs_dir: str = Field(default="./logs", env="LOGS_DIR")
    backup_dir: str = Field(default="./backups", env="BACKUP_DIR")
    
    # Sub-configurations
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    llm: LLMSettings = LLMSettings()
    security: SecuritySettings = SecuritySettings()
    monitoring: MonitoringSettings = MonitoringSettings()
    performance: PerformanceSettings = PerformanceSettings()
    three_engine: ThreeEngineSettings = ThreeEngineSettings()
    memory: MemorySettings = MemorySettings()
    
    class Config:
        env_file = ".env.enterprise"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._ensure_directories()
        self._log_configuration()
    
    def _ensure_directories(self):
        """Ensure required directories exist"""
        dirs = [
            self.upload_dir,
            self.models_dir,
            self.logs_dir,
            self.backup_dir,
            self.memory.vector_db_path,
            "config/enterprise",
            "deployment/scripts",
            "deployment/k8s",
            "deployment/monitoring"
        ]
        
        for directory in dirs:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def _log_configuration(self):
        """Log key configuration details"""
        logger.info(f"🚀 {self.app_name} v{self.app_version}")
        logger.info(f"📊 Environment: {self.environment}")
        logger.info(f"🔌 Backend: {self.backend_host}:{self.backend_port}")
        logger.info(f"🎨 Frontend: localhost:{self.frontend_port}")
        logger.info(f"🧠 Memory Service: localhost:{self.memory_port}")
        logger.info(f"⚡ Engine Coordinator: localhost:{self.engine_port}")
        logger.info(f"🤖 Primary LLM: {self.llm.primary_model}")
        logger.info(f"🗄️ Database: {self.database.host}:{self.database.port}")
        logger.info(f"🔄 Redis: {self.redis.host}:{self.redis.port}")
    
    @property
    def is_development(self) -> bool:
        return self.environment in ["development", "dev"]
    
    @property
    def is_production(self) -> bool:
        return self.environment in ["production", "prod", "enterprise"]
    
    @property
    def database_url(self) -> str:
        return self.database.url
    
    @property
    def redis_url(self) -> str:
        return self.redis.url

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

def reload_settings() -> Settings:
    """Reload settings (clears cache)"""
    get_settings.cache_clear()
    return get_settings()

# Convenience functions for commonly used settings
def get_database_url() -> str:
    """Get database URL"""
    return get_settings().database_url

def get_redis_url() -> str:
    """Get Redis URL"""
    return get_settings().redis_url

def get_api_url() -> str:
    """Get API URL"""
    return get_settings().api_url

def is_development() -> bool:
    """Check if running in development mode"""
    return get_settings().is_development

def is_production() -> bool:
    """Check if running in production mode"""
    return get_settings().is_production

# Export commonly used settings
def get_cors_origins() -> List[str]:
    """Get CORS origins"""
    return get_settings().security.cors_origins

def get_llm_config() -> LLMSettings:
    """Get LLM configuration"""
    return get_settings().llm

def get_monitoring_config() -> MonitoringSettings:
    """Get monitoring configuration"""
    return get_settings().monitoring
