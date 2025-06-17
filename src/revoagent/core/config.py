"""Configuration management for reVoAgent platform."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, validator
from dataclasses import dataclass


class ModelConfig(BaseModel):
    """Configuration for AI models."""
    name: str
    type: str = "local"  # local, api, remote
    path: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.0
    quantization: bool = True
    context_length: int = 8192


class AgentConfig(BaseModel):
    """Configuration for individual agents."""
    enabled: bool = True
    model: str = "local/deepseek-coder"
    tools: List[str] = Field(default_factory=list)
    max_iterations: int = 50
    timeout: int = 300
    memory_size: int = 1000


class SecurityConfig(BaseModel):
    """Security configuration."""
    sandbox_enabled: bool = True
    network_isolation: bool = True
    file_system_limits: bool = True
    allowed_domains: List[str] = Field(default_factory=list)
    blocked_commands: List[str] = Field(default_factory=list)
    max_file_size: int = 100 * 1024 * 1024  # 100MB


class ResourceConfig(BaseModel):
    """Resource management configuration."""
    max_memory_mb: int = 4096
    max_cpu_percent: float = 80.0
    max_disk_mb: int = 10240
    gpu_enabled: bool = False
    gpu_memory_fraction: float = 0.8


class PlatformConfig(BaseModel):
    """Platform-wide configuration."""
    name: str = "reVoAgent"
    version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"
    data_dir: str = "./data"
    models_dir: str = "./models"
    temp_dir: str = "./temp"


class Config(BaseModel):
    """Main configuration class for reVoAgent platform."""
    
    platform: PlatformConfig = Field(default_factory=PlatformConfig)
    models: Dict[str, ModelConfig] = Field(default_factory=dict)
    agents: Dict[str, AgentConfig] = Field(default_factory=dict)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    resources: ResourceConfig = Field(default_factory=ResourceConfig)
    
    @classmethod
    def load_from_file(cls, config_path: str) -> "Config":
        """Load configuration from YAML file."""
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_file, 'r') as f:
            config_data = yaml.safe_load(f)
        
        return cls(**config_data)
    
    @classmethod
    def load_default(cls) -> "Config":
        """Load default configuration with sensible defaults."""
        return cls(
            models={
                "local/deepseek-coder": ModelConfig(
                    name="deepseek-coder",
                    type="local",
                    path="./models/deepseek-coder-6.7b-instruct.gguf",
                    quantization=True
                ),
                "local/llama-3.2": ModelConfig(
                    name="llama-3.2",
                    type="local", 
                    path="./models/llama-3.2-3b-instruct.gguf",
                    quantization=True
                )
            },
            agents={
                "code_generator": AgentConfig(
                    enabled=True,
                    model="local/deepseek-coder",
                    tools=["git", "docker", "editor", "terminal"]
                ),
                "browser_agent": AgentConfig(
                    enabled=True,
                    model="local/llama-3.2",
                    tools=["browser", "screenshot", "web_search"]
                ),
                "debugging_agent": AgentConfig(
                    enabled=True,
                    model="local/deepseek-coder",
                    tools=["debugger", "profiler", "log_analyzer"]
                ),
                "testing_agent": AgentConfig(
                    enabled=True,
                    model="local/deepseek-coder",
                    tools=["pytest", "coverage", "test_generator"]
                )
            }
        )
    
    def save_to_file(self, config_path: str) -> None:
        """Save configuration to YAML file."""
        config_file = Path(config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w') as f:
            yaml.dump(self.dict(), f, default_flow_style=False, indent=2)
    
    def get_model_config(self, model_name: str) -> Optional[ModelConfig]:
        """Get configuration for a specific model."""
        return self.models.get(model_name)
    
    def get_agent_config(self, agent_name: str) -> Optional[AgentConfig]:
        """Get configuration for a specific agent."""
        return self.agents.get(agent_name)
    
    def validate_paths(self) -> None:
        """Validate that all configured paths exist or can be created."""
        paths_to_check = [
            self.platform.data_dir,
            self.platform.models_dir,
            self.platform.temp_dir
        ]
        
        for path_str in paths_to_check:
            path = Path(path_str)
            path.mkdir(parents=True, exist_ok=True)
    
    @validator('models')
    def validate_models(cls, v):
        """Validate model configurations."""
        for model_name, model_config in v.items():
            if model_config.type == "local" and model_config.path:
                if not Path(model_config.path).exists():
                    print(f"Warning: Model file not found: {model_config.path}")
        return v


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        config_path = os.getenv("REVOAGENT_CONFIG", "config/config.yaml")
        try:
            _config = Config.load_from_file(config_path)
        except FileNotFoundError:
            print(f"Configuration file not found at {config_path}, using defaults")
            _config = Config.load_default()
        
        _config.validate_paths()
    
    return _config


def set_config(config: Config) -> None:
    """Set the global configuration instance."""
    global _config
    _config = config