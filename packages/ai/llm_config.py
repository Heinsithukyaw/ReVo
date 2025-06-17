"""
LLM Configuration Management
Handles configuration for multiple LLM providers with cost optimization
"""

import os
from typing import Dict, Optional
from .llm_client import LLMProvider, LLMConfig


class LLMConfigManager:
    """Manages LLM configurations with environment variable support."""
    
    @staticmethod
    def get_default_configs() -> Dict[LLMProvider, LLMConfig]:
        """Get default LLM configurations from environment variables."""
        configs = {}
        
        # DeepSeek R1 0528 Local (Primary - Free)
        deepseek_endpoint = os.getenv("DEEPSEEK_ENDPOINT", "http://localhost:8001")
        if deepseek_endpoint:
            configs[LLMProvider.DEEPSEEK_LOCAL] = LLMConfig(
                provider=LLMProvider.DEEPSEEK_LOCAL,
                endpoint=deepseek_endpoint,
                model=os.getenv("DEEPSEEK_MODEL", "deepseek-r1-0528"),
                max_tokens=int(os.getenv("DEEPSEEK_MAX_TOKENS", "4000")),
                temperature=float(os.getenv("DEEPSEEK_TEMPERATURE", "0.7")),
                timeout=int(os.getenv("DEEPSEEK_TIMEOUT", "30")),
                enabled=os.getenv("DEEPSEEK_ENABLED", "true").lower() == "true",
                cost_per_token=0.0  # Free local model
            )
        
        # Llama Local (Secondary - Free)
        llama_endpoint = os.getenv("LLAMA_ENDPOINT", "http://localhost:11434")
        if llama_endpoint:
            configs[LLMProvider.LLAMA_LOCAL] = LLMConfig(
                provider=LLMProvider.LLAMA_LOCAL,
                endpoint=llama_endpoint,
                model=os.getenv("LLAMA_MODEL", "llama3.1:8b"),
                max_tokens=int(os.getenv("LLAMA_MAX_TOKENS", "4000")),
                temperature=float(os.getenv("LLAMA_TEMPERATURE", "0.7")),
                timeout=int(os.getenv("LLAMA_TIMEOUT", "45")),
                enabled=os.getenv("LLAMA_ENABLED", "true").lower() == "true",
                cost_per_token=0.0  # Free local model
            )
        
        # OpenAI (Fallback - Paid)
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            configs[LLMProvider.OPENAI] = LLMConfig(
                provider=LLMProvider.OPENAI,
                api_key=openai_api_key,
                model=os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview"),
                max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "4000")),
                temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
                timeout=int(os.getenv("OPENAI_TIMEOUT", "30")),
                enabled=os.getenv("OPENAI_ENABLED", "true").lower() == "true",
                cost_per_token=float(os.getenv("OPENAI_COST_PER_TOKEN", "0.00003"))  # Approximate
            )
        
        # Anthropic (Emergency Fallback - Paid)
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_api_key:
            configs[LLMProvider.ANTHROPIC] = LLMConfig(
                provider=LLMProvider.ANTHROPIC,
                api_key=anthropic_api_key,
                model=os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229"),
                max_tokens=int(os.getenv("ANTHROPIC_MAX_TOKENS", "4000")),
                temperature=float(os.getenv("ANTHROPIC_TEMPERATURE", "0.7")),
                timeout=int(os.getenv("ANTHROPIC_TIMEOUT", "30")),
                enabled=os.getenv("ANTHROPIC_ENABLED", "true").lower() == "true",
                cost_per_token=float(os.getenv("ANTHROPIC_COST_PER_TOKEN", "0.000015"))  # Approximate
            )
        
        return configs
    
    @staticmethod
    def get_development_configs() -> Dict[LLMProvider, LLMConfig]:
        """Get development configurations for testing."""
        return {
            LLMProvider.DEEPSEEK_LOCAL: LLMConfig(
                provider=LLMProvider.DEEPSEEK_LOCAL,
                endpoint="http://localhost:8001",
                model="deepseek-r1-0528",
                max_tokens=2000,
                temperature=0.7,
                timeout=30,
                enabled=True,
                cost_per_token=0.0
            ),
            LLMProvider.LLAMA_LOCAL: LLMConfig(
                provider=LLMProvider.LLAMA_LOCAL,
                endpoint="http://localhost:11434",
                model="llama3.1:8b",
                max_tokens=2000,
                temperature=0.7,
                timeout=45,
                enabled=True,
                cost_per_token=0.0
            )
        }
    
    @staticmethod
    def validate_config(config: LLMConfig) -> bool:
        """Validate LLM configuration."""
        if not config.enabled:
            return True  # Disabled configs are valid
        
        if config.provider in [LLMProvider.DEEPSEEK_LOCAL, LLMProvider.LLAMA_LOCAL]:
            return config.endpoint is not None
        
        if config.provider in [LLMProvider.OPENAI, LLMProvider.ANTHROPIC]:
            return config.api_key is not None
        
        return False
    
    @staticmethod
    def get_config_summary(configs: Dict[LLMProvider, LLMConfig]) -> Dict[str, any]:
        """Get a summary of configurations for logging."""
        summary = {}
        
        for provider, config in configs.items():
            summary[provider.value] = {
                "enabled": config.enabled,
                "model": config.model,
                "endpoint": config.endpoint if config.endpoint else "API",
                "cost_per_token": config.cost_per_token,
                "max_tokens": config.max_tokens
            }
        
        return summary


def create_llm_client_from_env() -> 'LLMClient':
    """Create LLM client from environment variables."""
    from .llm_client import LLMClient
    
    configs = LLMConfigManager.get_default_configs()
    
    # Validate configurations
    valid_configs = {}
    for provider, config in configs.items():
        if LLMConfigManager.validate_config(config):
            valid_configs[provider] = config
        else:
            print(f"Warning: Invalid configuration for {provider.value}")
    
    if not valid_configs:
        print("Warning: No valid LLM configurations found. Using development configs.")
        valid_configs = LLMConfigManager.get_development_configs()
    
    # Log configuration summary
    summary = LLMConfigManager.get_config_summary(valid_configs)
    print("LLM Configuration Summary:")
    for provider, info in summary.items():
        status = "✅" if info["enabled"] else "❌"
        cost = "Free" if info["cost_per_token"] == 0 else f"${info['cost_per_token']}/token"
        print(f"  {status} {provider}: {info['model']} ({cost})")
    
    return LLMClient(valid_configs)


def setup_environment_template():
    """Print environment variable template for LLM setup."""
    template = """
# LLM Configuration Environment Variables

# DeepSeek R1 0528 Local (Primary - Free)
DEEPSEEK_ENDPOINT=http://localhost:8001
DEEPSEEK_MODEL=deepseek-r1-0528
DEEPSEEK_MAX_TOKENS=4000
DEEPSEEK_TEMPERATURE=0.7
DEEPSEEK_TIMEOUT=30
DEEPSEEK_ENABLED=true

# Llama Local (Secondary - Free)
LLAMA_ENDPOINT=http://localhost:11434
LLAMA_MODEL=llama3.1:8b
LLAMA_MAX_TOKENS=4000
LLAMA_TEMPERATURE=0.7
LLAMA_TIMEOUT=45
LLAMA_ENABLED=true

# OpenAI (Fallback - Paid)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_MAX_TOKENS=4000
OPENAI_TEMPERATURE=0.7
OPENAI_TIMEOUT=30
OPENAI_ENABLED=true
OPENAI_COST_PER_TOKEN=0.00003

# Anthropic (Emergency Fallback - Paid)
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ANTHROPIC_MODEL=claude-3-sonnet-20240229
ANTHROPIC_MAX_TOKENS=4000
ANTHROPIC_TEMPERATURE=0.7
ANTHROPIC_TIMEOUT=30
ANTHROPIC_ENABLED=true
ANTHROPIC_COST_PER_TOKEN=0.000015
"""
    return template.strip()


if __name__ == "__main__":
    print("LLM Configuration Template:")
    print("=" * 50)
    print(setup_environment_template())
    print("=" * 50)
    print("\nTo test configuration:")
    print("python -m packages.ai.llm_config")