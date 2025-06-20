"""
reVoAgent AI Module

This module provides AI model management and integration capabilities.
"""

from .model_manager import ModelManager, model_manager
from .deepseek_integration import DeepSeekR1Model
from .llama_integration import LlamaModel
from .openai_integration import OpenAIModel
from .llm_bridge import LLMBridge, llm_bridge
from .cpu_optimized_deepseek import CPUOptimizedDeepSeek
from .llm_manager import LLMManager, llm_manager

__all__ = [
    'ModelManager',
    'model_manager',
    'DeepSeekR1Model', 
    'LlamaModel',
    'OpenAIModel',
    'LLMBridge',
    'llm_bridge',
    'CPUOptimizedDeepSeek',
    'LLMManager',
    'llm_manager'
]