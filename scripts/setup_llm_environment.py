#!/usr/bin/env python3
"""
Setup LLM Environment for reVoAgent

Creates required directories and default configuration files for LLM operation.
"""

import os
import sys
import yaml
import shutil
from pathlib import Path

def create_directory(path, verbose=True):
    """Create directory if it doesn't exist"""
    if not os.path.exists(path):
        os.makedirs(path)
        if verbose:
            print(f"Created directory: {path}")
    elif verbose:
        print(f"Directory already exists: {path}")

def create_config_file(path, config_data, verbose=True):
    """Create config file if it doesn't exist"""
    if not os.path.exists(path):
        with open(path, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False)
        if verbose:
            print(f"Created config file: {path}")
    elif verbose:
        print(f"Config file already exists: {path}")

def setup_environment():
    """Setup the LLM environment for reVoAgent"""
    print("Setting up LLM environment for reVoAgent...")
    
    # Create required directories
    create_directory("models")
    create_directory("logs")
    create_directory("data")
    create_directory("config", verbose=False)
    
    # Create fallback config
    fallback_config = {
        "fallback_system": {
            "enabled": True,
            "timeout_seconds": 30,
            "max_retries": 3,
            "fallback_chain": ["deepseek-r1", "deepseek-r1-template"]
        },
        "local_models": {
            "deepseek_r1_gguf": {
                "enabled": False,
                "path": "models/deepseek-r1.gguf",
                "description": "DeepSeek R1 (GGUF version)",
                "model_type": "gguf"
            },
            "llama_3_1_8b_gguf": {
                "enabled": False,
                "path": "models/llama-3.1-8b.gguf",
                "description": "Llama 3.1 8B (GGUF version)",
                "model_type": "gguf"
            }
        }
    }
    
    create_config_file("config/fallback_config.yaml", fallback_config)
    
    # Create environment config
    environment_config = {
        "llm": {
            "default_model": "deepseek-r1",
            "providers": {
                "deepseek": {"enabled": True, "api_key_env": "DEEPSEEK_API_KEY"},
                "openai": {"enabled": False, "api_key_env": "OPENAI_API_KEY"},
                "anthropic": {"enabled": False, "api_key_env": "ANTHROPIC_API_KEY"},
                "gemini": {"enabled": False, "api_key_env": "GEMINI_API_KEY"}
            }
        },
        "resources": {
            "optimize_for_cpu": True,
            "low_memory_mode": True
        }
    }
    
    create_config_file("config/environment.yaml", environment_config)
    
    # Create ports config
    ports_config = {
        "production": {
            "backend": 12001,
            "frontend": 12000,
            "websocket": 12001,
            "model_server": 8080
        }
    }
    
    create_config_file("config/ports.yaml", ports_config)
    
    print("\nEnvironment setup complete!")
    print("\nYou can now start the reVoAgent platform with:")
    print("./start_consolidated.sh")

if __name__ == "__main__":
    setup_environment()