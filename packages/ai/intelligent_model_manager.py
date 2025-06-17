"""
Intelligent Model Manager

Manages AI models with intelligent loading, switching, and optimization.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

from .schemas import ModelType, ModelStatus, ModelInfo, ModelConfig
from .services.model_loader import ModelLoader

logger = logging.getLogger(__name__)


class ModelProvider(Enum):
    """Model providers."""
    DEEPSEEK = "deepseek"
    LLAMA = "llama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"


@dataclass
class ModelPerformanceMetrics:
    """Performance metrics for a model."""
    latency: float = 0.0
    throughput: float = 0.0
    memory_usage: float = 0.0
    gpu_usage: float = 0.0
    accuracy_score: float = 0.0
    cost_per_token: float = 0.0


class ModelManager:
    """
    Intelligent Model Manager for handling multiple AI models.
    
    Features:
    - Dynamic model loading/unloading
    - Performance monitoring
    - Intelligent model selection
    - Resource optimization
    """
    
    def __init__(self):
        self.model_loader = ModelLoader()
        self.models: Dict[str, Any] = {}
        self.model_configs: Dict[str, ModelConfig] = {}
        self.performance_metrics: Dict[str, ModelPerformanceMetrics] = {}
        self.active_model: Optional[str] = None
        
    async def register_model(self, model_id: str, config: ModelConfig) -> bool:
        """Register a new model configuration."""
        try:
            self.model_configs[model_id] = config
            
            # Register with model loader
            model_info = ModelInfo(
                id=model_id,
                name=config.model_id,
                type=config.model_type,
                size="Unknown",
                status=ModelStatus.UNLOADED
            )
            self.model_loader.register_model_info(model_id, model_info)
            
            logger.info(f"Registered model {model_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register model {model_id}: {e}")
            return False
    
    async def load_model(self, model_id: str) -> bool:
        """Load a specific model."""
        if model_id not in self.model_configs:
            logger.error(f"Model {model_id} not registered")
            return False
            
        try:
            config = self.model_configs[model_id]
            success = await self.model_loader.load_model(model_id, config)
            
            if success:
                self.models[model_id] = self.model_loader.models[model_id]
                self.active_model = model_id
                logger.info(f"Loaded model {model_id}")
                
            return success
            
        except Exception as e:
            logger.error(f"Failed to load model {model_id}: {e}")
            return False
    
    async def unload_model(self, model_id: str) -> bool:
        """Unload a specific model."""
        try:
            success = await self.model_loader.unload_model(model_id)
            
            if success and model_id in self.models:
                del self.models[model_id]
                if self.active_model == model_id:
                    self.active_model = None
                logger.info(f"Unloaded model {model_id}")
                
            return success
            
        except Exception as e:
            logger.error(f"Failed to unload model {model_id}: {e}")
            return False
    
    async def switch_model(self, model_id: str) -> bool:
        """Switch to a different model."""
        if model_id not in self.model_configs:
            logger.error(f"Model {model_id} not registered")
            return False
            
        # Load the new model if not already loaded
        if model_id not in self.models:
            success = await self.load_model(model_id)
            if not success:
                return False
        
        self.active_model = model_id
        logger.info(f"Switched to model {model_id}")
        return True
    
    async def generate(self, prompt: str, model_id: Optional[str] = None, **kwargs) -> str:
        """Generate text using the specified or active model."""
        target_model = model_id or self.active_model
        
        if not target_model:
            raise ValueError("No active model and no model specified")
            
        if target_model not in self.models:
            # Try to load the model
            success = await self.load_model(target_model)
            if not success:
                raise ValueError(f"Model {target_model} not available")
        
        model = self.models[target_model]
        
        # Generate using the model
        if hasattr(model, 'generate'):
            return await model.generate(prompt, **kwargs)
        else:
            raise ValueError(f"Model {target_model} does not support generation")
    
    def get_model_status(self, model_id: str) -> Optional[ModelStatus]:
        """Get the status of a specific model."""
        return self.model_loader.get_model_status(model_id)
    
    def get_loaded_models(self) -> List[str]:
        """Get list of currently loaded models."""
        return list(self.models.keys())
    
    def get_available_models(self) -> List[str]:
        """Get list of all registered models."""
        return list(self.model_configs.keys())
    
    def get_performance_metrics(self, model_id: str) -> Optional[ModelPerformanceMetrics]:
        """Get performance metrics for a model."""
        return self.performance_metrics.get(model_id)
    
    async def optimize_models(self) -> None:
        """Optimize model loading based on usage patterns."""
        # This is a placeholder for intelligent optimization logic
        # Could include:
        # - Unloading unused models
        # - Preloading frequently used models
        # - Memory optimization
        logger.info("Model optimization completed")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all models."""
        health_status = {
            "active_model": self.active_model,
            "loaded_models": len(self.models),
            "registered_models": len(self.model_configs),
            "models": {}
        }
        
        for model_id in self.model_configs:
            status = self.get_model_status(model_id)
            health_status["models"][model_id] = {
                "status": status.value if status else "unknown",
                "loaded": model_id in self.models
            }
        
        return health_status


# Global model manager instance
model_manager = ModelManager()


# Convenience functions
async def load_model(model_id: str, config: ModelConfig) -> bool:
    """Load a model using the global model manager."""
    await model_manager.register_model(model_id, config)
    return await model_manager.load_model(model_id)


async def generate_text(prompt: str, model_id: Optional[str] = None, **kwargs) -> str:
    """Generate text using the global model manager."""
    return await model_manager.generate(prompt, model_id, **kwargs)


def get_model_manager() -> ModelManager:
    """Get the global model manager instance."""
    return model_manager