"""
Model Layer - AI Model Management and Execution

This module provides comprehensive AI model management including:
- Local model loading and execution
- Model quantization and optimization
- Dynamic model switching
- Model registry and discovery
"""

from .local_models import LocalModelManager
from .model_registry import ModelRegistry
from .model_switching import ModelSwitcher
from .model_quantization import ModelQuantizer

__all__ = [
    'LocalModelManager',
    'ModelRegistry', 
    'ModelSwitcher',
    'ModelQuantizer'
]