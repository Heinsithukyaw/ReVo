"""
AI Model Manager

Centralized management for all AI models in the reVoAgent platform.
"""

import asyncio
import logging
import psutil
import threading
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import torch
import gc

logger = logging.getLogger(__name__)

class ModelType(Enum):
    """Supported model types."""
    DEEPSEEK_R1 = "deepseek-r1"
    LLAMA = "llama"
    OPENAI = "openai"
    CUSTOM = "custom"

class ModelStatus(Enum):
    """Model loading status."""
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    ERROR = "error"

@dataclass
class ModelInfo:
    """Model information and metadata."""
    id: str
    name: str
    type: ModelType
    size: str
    status: ModelStatus
    memory_usage: float = 0.0
    gpu_memory: float = 0.0
    performance_score: float = 0.0
    last_used: Optional[str] = None
    error_message: Optional[str] = None

@dataclass
class ModelConfig:
    """Model configuration settings."""
    model_id: str
    model_path: str
    device: str = "auto"
    max_length: int = 4096
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 50
    do_sample: bool = True
    quantization: Optional[str] = None
    trust_remote_code: bool = True

class ModelManager:
    """
    Centralized AI model management system.
    
    Handles loading, unloading, and switching between different AI models
    with automatic resource management and optimization.
    """
    
    def __init__(self):
        self.models: Dict[str, Any] = {}
        self.model_configs: Dict[str, ModelConfig] = {}
        self.model_info: Dict[str, ModelInfo] = {}
        self.active_model: Optional[str] = None
        self.lock = threading.Lock()
        
        # System resources
        self.max_gpu_memory = self._get_gpu_memory()
        self.max_cpu_memory = psutil.virtual_memory().total
        
        # Initialize default models
        self._initialize_default_models()
    
    def _get_gpu_memory(self) -> float:
        """Get total GPU memory in GB."""
        if torch.cuda.is_available():
            return torch.cuda.get_device_properties(0).total_memory / (1024**3)
        return 0.0
    
    def _initialize_default_models(self):
        """Initialize default model configurations."""
        # DeepSeek R1 0528
        self.model_configs["deepseek-r1-0528"] = ModelConfig(
            model_id="deepseek-r1-0528",
            model_path="deepseek-ai/DeepSeek-R1-0528",
            device="auto",
            max_length=4096,  # Reduced for CPU environments
            temperature=0.7,
            quantization="4bit" if torch.cuda.is_available() else None
        )
        
        self.model_info["deepseek-r1-0528"] = ModelInfo(
            id="deepseek-r1-0528",
            name="DeepSeek R1 0528",
            type=ModelType.DEEPSEEK_R1,
            size="70B",
            status=ModelStatus.UNLOADED,
            performance_score=94.0
        )
        
        # Llama models
        self.model_configs["llama-3.2-8b"] = ModelConfig(
            model_id="llama-3.2-8b",
            model_path="meta-llama/Llama-3.2-8B-Instruct",
            device="auto",
            max_length=8192,
            quantization="4bit"
        )
        
        self.model_info["llama-3.2-8b"] = ModelInfo(
            id="llama-3.2-8b",
            name="Llama 3.2 8B",
            type=ModelType.LLAMA,
            size="8B",
            status=ModelStatus.UNLOADED,
            performance_score=78.0
        )
    
    async def load_model(self, model_id: str) -> bool:
        """
        Load a specific model.
        
        Args:
            model_id: ID of the model to load
            
        Returns:
            bool: True if successful, False otherwise
        """
        if model_id not in self.model_configs:
            logger.error(f"Model {model_id} not found in configurations")
            return False
        
        with self.lock:
            if model_id in self.models:
                logger.info(f"Model {model_id} already loaded")
                return True
            
            # Update status to loading
            self.model_info[model_id].status = ModelStatus.LOADING
            
            try:
                config = self.model_configs[model_id]
                model_type = self.model_info[model_id].type
                
                if model_type == ModelType.DEEPSEEK_R1:
                    # Use CPU-optimized version for better compatibility
                    from .cpu_optimized_deepseek import CPUOptimizedDeepSeek
                    model = CPUOptimizedDeepSeek()
                elif model_type == ModelType.LLAMA:
                    from .llama_integration import LlamaModel
                    model = LlamaModel(config)
                else:
                    raise ValueError(f"Unsupported model type: {model_type}")
                
                # Load the model
                success = await model.load()
                if success:
                    self.models[model_id] = model
                    
                    # Update model info
                    self.model_info[model_id].status = ModelStatus.LOADED
                    self.model_info[model_id].memory_usage = self._get_model_memory_usage(model)
                    self.model_info[model_id].gpu_memory = self._get_model_gpu_memory(model)
                    
                    # Set as active if no active model
                    if self.active_model is None:
                        self.active_model = model_id
                    
                    logger.info(f"Successfully loaded model {model_id}")
                    return True
                else:
                    # Model failed to load
                    self.model_info[model_id].status = ModelStatus.ERROR
                    self.model_info[model_id].error_message = "Failed to load model"
                    logger.error(f"Failed to load model {model_id}")
                    return False
                
            except Exception as e:
                logger.error(f"Failed to load model {model_id}: {str(e)}")
                self.model_info[model_id].status = ModelStatus.ERROR
                self.model_info[model_id].error_message = str(e)
                return False
    
    async def unload_model(self, model_id: str) -> bool:
        """
        Unload a specific model to free resources.
        
        Args:
            model_id: ID of the model to unload
            
        Returns:
            bool: True if successful, False otherwise
        """
        with self.lock:
            if model_id not in self.models:
                logger.warning(f"Model {model_id} not loaded")
                return True
            
            try:
                model = self.models[model_id]
                await model.unload()
                del self.models[model_id]
                
                # Clear GPU cache
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                
                # Force garbage collection
                gc.collect()
                
                # Update model info
                self.model_info[model_id].status = ModelStatus.UNLOADED
                self.model_info[model_id].memory_usage = 0.0
                self.model_info[model_id].gpu_memory = 0.0
                
                # Update active model
                if self.active_model == model_id:
                    self.active_model = None
                    # Set another loaded model as active
                    for mid in self.models.keys():
                        self.active_model = mid
                        break
                
                logger.info(f"Successfully unloaded model {model_id}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to unload model {model_id}: {str(e)}")
                return False
    
    async def switch_model(self, model_id: str) -> bool:
        """
        Switch to a different model as the active model.
        
        Args:
            model_id: ID of the model to switch to
            
        Returns:
            bool: True if successful, False otherwise
        """
        if model_id not in self.model_configs:
            logger.error(f"Model {model_id} not found")
            return False
        
        # Load model if not already loaded
        if model_id not in self.models:
            success = await self.load_model(model_id)
            if not success:
                return False
        
        self.active_model = model_id
        logger.info(f"Switched to model {model_id}")
        return True
    
    async def generate_text(self, prompt: str, model_id: Optional[str] = None, **kwargs) -> str:
        """
        Generate text using the specified or active model.
        
        Args:
            prompt: Input prompt
            model_id: Optional specific model to use
            **kwargs: Additional generation parameters
            
        Returns:
            str: Generated text
        """
        target_model = model_id or self.active_model
        
        if not target_model or target_model not in self.models:
            raise ValueError(f"No active model or model {target_model} not loaded")
        
        model = self.models[target_model]
        
        # Check if this is the CPU-optimized DeepSeek model
        if hasattr(model, 'generate_code'):
            # For code generation requests, use the specialized method
            if isinstance(prompt, dict):
                return await model.generate_code(prompt)
            else:
                # Convert string prompt to request format
                request = {
                    "task_description": prompt,
                    "language": kwargs.get("language", "python"),
                    "framework": kwargs.get("framework", "fastapi"),
                    "database": kwargs.get("database", "postgresql"),
                    "features": kwargs.get("features", ["auth", "tests"])
                }
                result = await model.generate_code(request)
                return result.get("generated_code", "")
        else:
            # Fallback to standard generation
            return await model.generate(prompt, **kwargs)
    
    async def generate_code(self, request: Dict[str, Any], model_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate code using the specified or active model.
        
        Args:
            request: Code generation request with task_description, language, etc.
            model_id: Optional specific model to use
            
        Returns:
            Dict containing generated code and metadata
        """
        target_model = model_id or self.active_model
        
        if not target_model or target_model not in self.models:
            raise ValueError(f"No active model or model {target_model} not loaded")
        
        model = self.models[target_model]
        
        # Check if this is the CPU-optimized DeepSeek model
        if hasattr(model, 'generate_code'):
            return await model.generate_code(request)
        else:
            # Fallback for other models - convert to text generation
            prompt = f"Generate {request.get('language', 'python')} code for: {request.get('task_description', '')}"
            generated_text = await model.generate(prompt)
            return {
                "generated_code": generated_text,
                "model_used": target_model,
                "status": "completed"
            }
    
    def get_model_info(self, model_id: Optional[str] = None) -> Union[ModelInfo, Dict[str, ModelInfo]]:
        """
        Get information about a specific model or all models.
        
        Args:
            model_id: Optional specific model ID
            
        Returns:
            ModelInfo or dict of ModelInfo
        """
        if model_id:
            return self.model_info.get(model_id)
        return self.model_info.copy()
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get current system resource statistics."""
        # CPU and memory
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # GPU stats
        gpu_stats = {}
        if torch.cuda.is_available():
            gpu_stats = {
                "gpu_count": torch.cuda.device_count(),
                "gpu_memory_used": torch.cuda.memory_allocated() / (1024**3),
                "gpu_memory_total": torch.cuda.get_device_properties(0).total_memory / (1024**3),
                "gpu_utilization": self._get_gpu_utilization()
            }
        
        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_used_gb": memory.used / (1024**3),
            "memory_total_gb": memory.total / (1024**3),
            "loaded_models": len(self.models),
            "active_model": self.active_model,
            **gpu_stats
        }
    
    def _get_model_memory_usage(self, model) -> float:
        """Get model memory usage in GB."""
        try:
            if hasattr(model, 'get_memory_usage'):
                return model.get_memory_usage()
            return 0.0
        except:
            return 0.0
    
    def _get_model_gpu_memory(self, model) -> float:
        """Get model GPU memory usage in GB."""
        try:
            if torch.cuda.is_available() and hasattr(model, 'model'):
                return torch.cuda.memory_allocated() / (1024**3)
            return 0.0
        except:
            return 0.0
    
    def _get_gpu_utilization(self) -> float:
        """Get GPU utilization percentage."""
        try:
            import nvidia_ml_py as nvml
            nvml.nvmlInit()
            handle = nvml.nvmlDeviceGetHandleByIndex(0)
            util = nvml.nvmlDeviceGetUtilizationRates(handle)
            return util.gpu
        except:
            return 0.0
    
    async def optimize_resources(self):
        """Optimize resource usage by managing loaded models."""
        with self.lock:
            # Get current resource usage
            stats = self.get_system_stats()
            
            # If memory usage is high, unload least used models
            if stats.get("memory_percent", 0) > 85:
                logger.info("High memory usage detected, optimizing...")
                
                # Sort models by last used (keep active model)
                models_to_check = [
                    (mid, info) for mid, info in self.model_info.items()
                    if mid != self.active_model and mid in self.models
                ]
                
                # Unload oldest models first
                for model_id, _ in models_to_check:
                    if stats.get("memory_percent", 0) > 80:
                        await self.unload_model(model_id)
                        stats = self.get_system_stats()
                    else:
                        break

# Global model manager instance
model_manager = ModelManager()