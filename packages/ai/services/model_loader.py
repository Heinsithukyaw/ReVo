"""
Model Loader Service

Focused service for loading and unloading AI models with proper resource management.
"""

import asyncio
import threading
from typing import Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None

import gc

from ..schemas import ModelConfig, ModelInfo, ModelType, ModelStatus
from ...core.logging_config import get_logger, log_async_function_call

logger = get_logger(__name__)


class CPUOptimizedDeepSeek:
    """CPU-optimized version of DeepSeek for resource-constrained environments"""
    
    def __init__(self, model_path: str, **kwargs):
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        self.loaded = False
        
    async def load(self):
        """Load the model and tokenizer"""
        try:
            if not TORCH_AVAILABLE:
                raise ImportError("PyTorch is required for DeepSeek models")
                
            # Use dynamic imports to avoid dependency issues
            from transformers import AutoTokenizer, AutoModelForCausalLM
            
            logger.info(f"Loading CPU-optimized DeepSeek model from {self.model_path}")
            
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                torch_dtype=torch.float32,  # CPU optimized
                device_map="cpu",
                load_in_8bit=False,  # Not supported on CPU
                trust_remote_code=True
            )
            self.loaded = True
            logger.info("CPU-optimized DeepSeek model loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load CPU-optimized DeepSeek model: {e}")
            self.loaded = False
            return False
        
    async def generate(self, prompt: str, max_tokens: int = 1024) -> str:
        """Generate text using the loaded model"""
        if not self.loaded or self.model is None:
            raise RuntimeError("Model not loaded. Call load() first.")
            
        try:
            inputs = self.tokenizer(prompt, return_tensors="pt")
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    max_new_tokens=max_tokens,
                    pad_token_id=self.tokenizer.eos_token_id,
                    do_sample=True,
                    temperature=0.7
                )
            return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise
    
    def unload(self):
        """Unload the model and free memory"""
        if self.model is not None:
            del self.model
            self.model = None
        if self.tokenizer is not None:
            del self.tokenizer
            self.tokenizer = None
        self.loaded = False
        if TORCH_AVAILABLE:
            torch.cuda.empty_cache()
        gc.collect()


class LlamaModel:
    """Wrapper for Llama model with consistent interface"""
    
    def __init__(self, model_path: str, **kwargs):
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        self.loaded = False
        
    async def load(self):
        """Load the Llama model and tokenizer"""
        try:
            if not TORCH_AVAILABLE:
                raise ImportError("PyTorch is required for Llama models")
                
            # Use dynamic imports to avoid dependency issues
            try:
                from transformers import LlamaTokenizer, LlamaForCausalLM
            except ImportError:
                # Fallback to AutoTokenizer/AutoModel if specific Llama classes not available
                from transformers import AutoTokenizer, AutoModelForCausalLM
                LlamaTokenizer = AutoTokenizer
                LlamaForCausalLM = AutoModelForCausalLM
            
            logger.info(f"Loading Llama model from {self.model_path}")
            
            self.tokenizer = LlamaTokenizer.from_pretrained(self.model_path)
            self.model = LlamaForCausalLM.from_pretrained(
                self.model_path,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else "cpu"
            )
            self.loaded = True
            logger.info("Llama model loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load Llama model: {e}")
            self.loaded = False
            return False
        
    async def generate(self, prompt: str, max_tokens: int = 1024) -> str:
        """Generate text using the loaded Llama model"""
        if not self.loaded or self.model is None:
            raise RuntimeError("Model not loaded. Call load() first.")
            
        try:
            inputs = self.tokenizer(prompt, return_tensors="pt")
            if torch.cuda.is_available():
                inputs = {k: v.cuda() for k, v in inputs.items()}
                
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs['input_ids'],
                    max_new_tokens=max_tokens,
                    pad_token_id=self.tokenizer.eos_token_id,
                    do_sample=True,
                    temperature=0.7
                )
            return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise
    
    def unload(self):
        """Unload the model and free memory"""
        if self.model is not None:
            del self.model
            self.model = None
        if self.tokenizer is not None:
            del self.tokenizer
            self.tokenizer = None
        self.loaded = False
        if TORCH_AVAILABLE:
            torch.cuda.empty_cache()
        gc.collect()


class ModelLoader:
    """
    Focused service for AI model loading and unloading.
    
    Responsibilities:
    - Load models from various providers
    - Unload models and clean up resources
    - Track model loading status
    - Handle loading errors gracefully
    """
    
    def __init__(self):
        self.models: Dict[str, Any] = {}
        self.model_info: Dict[str, ModelInfo] = {}
        self.lock = threading.Lock()
        
    @log_async_function_call
    async def load_model(self, model_id: str, config: ModelConfig) -> bool:
        """
        Load a specific model with proper error handling and resource management.
        
        Args:
            model_id: Unique identifier for the model
            config: Model configuration
            
        Returns:
            bool: True if successful, False otherwise
        """
        with self.lock:
            if model_id in self.models:
                logger.info(f"Model {model_id} already loaded")
                return True
            
            # Update status to loading
            if model_id in self.model_info:
                self.model_info[model_id].status = ModelStatus.LOADING
            
            try:
                logger.info(
                    "Loading model",
                    extra={
                        'model_id': model_id,
                        'model_type': config.model_type.value,
                        'model_path': config.model_path,
                        'device': config.device
                    }
                )
                
                # Load model based on type
                model, error_msg = await self._load_model_by_type(config)
                
                if model:
                    self.models[model_id] = model
                    
                    # Update model info
                    if model_id in self.model_info:
                        self.model_info[model_id].status = ModelStatus.LOADED
                        self.model_info[model_id].memory_usage = self._get_model_memory_usage(model)
                        self.model_info[model_id].gpu_memory = self._get_model_gpu_memory(model)
                    
                    logger.info(f"Successfully loaded model {model_id}")
                    return True
                else:
                    # Model failed to load
                    if model_id in self.model_info:
                        self.model_info[model_id].status = ModelStatus.ERROR
                        self.model_info[model_id].error_message = error_msg or "Failed to load model"
                    logger.error(f"Failed to load model {model_id}: {error_msg}")
                    return False
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Failed to load model {model_id}: {error_msg}")
                if model_id in self.model_info:
                    self.model_info[model_id].status = ModelStatus.ERROR
                    self.model_info[model_id].error_message = error_msg
                return False
    
    async def unload_model(self, model_id: str) -> bool:
        """
        Unload a specific model and clean up resources.
        
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
                
                # Call model's unload method if available
                if hasattr(model, 'unload'):
                    if asyncio.iscoroutinefunction(model.unload):
                        await model.unload()
                    else:
                        model.unload()
                
                # Remove from memory
                del self.models[model_id]
                
                # Clean up GPU memory
                await self._cleanup_gpu_memory()
                
                # Force garbage collection
                gc.collect()
                
                # Update model info
                if model_id in self.model_info:
                    self.model_info[model_id].status = ModelStatus.UNLOADED
                    self.model_info[model_id].memory_usage = 0.0
                    self.model_info[model_id].gpu_memory = 0.0
                
                logger.info(f"Successfully unloaded model {model_id}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to unload model {model_id}: {str(e)}")
                return False
    
    async def _load_model_by_type(self, config: ModelConfig) -> tuple[Optional[Any], Optional[str]]:
        """Load model based on its type. Returns (model, error_message)."""
        try:
            if config.model_type == ModelType.DEEPSEEK_R1:
                # Use the local CPUOptimizedDeepSeek class
                model = CPUOptimizedDeepSeek(config.model_path)
                success = await model.load()
                return (model, None) if success is not False else (None, "Failed to load DeepSeek model")
                
            elif config.model_type == ModelType.LLAMA:
                # Use the local LlamaModel class
                model = LlamaModel(config.model_path)
                success = await model.load()
                return (model, None) if success is not False else (None, "Failed to load Llama model")
                
            elif config.model_type == ModelType.OPENAI:
                try:
                    from ..openai_integration import OpenAIModel
                    model = OpenAIModel(config)
                    success = await model.load()
                    return (model, None) if success else (None, "Failed to load OpenAI model")
                except ImportError:
                    logger.warning("OpenAI integration not available")
                    return (None, "OpenAI integration not available")
                
            else:
                error_msg = f"Unsupported model type: {config.model_type}"
                return (None, error_msg)
                
        except ImportError as e:
            error_msg = f"Failed to import model class: {e}"
            logger.error(error_msg)
            return (None, error_msg)
        except Exception as e:
            error_msg = f"Failed to load model: {e}"
            logger.error(error_msg)
            return (None, error_msg)
    
    async def _cleanup_gpu_memory(self):
        """Clean up GPU memory after model unloading."""
        try:
            if TORCH_AVAILABLE and torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
        except Exception as e:
            # Don't fail unloading if GPU cleanup fails
            logger.warning(f"GPU cleanup failed: {e}")
    
    def _get_model_memory_usage(self, model) -> float:
        """Get model memory usage in GB."""
        try:
            if hasattr(model, 'get_memory_usage'):
                return model.get_memory_usage()
            return 0.0
        except Exception:
            return 0.0
    
    def _get_model_gpu_memory(self, model) -> float:
        """Get model GPU memory usage in GB."""
        try:
            if TORCH_AVAILABLE and torch.cuda.is_available() and hasattr(model, 'model'):
                return torch.cuda.memory_allocated() / (1024**3)
            return 0.0
        except Exception:
            return 0.0
    
    def get_loaded_models(self) -> Dict[str, Any]:
        """Get dictionary of currently loaded models."""
        return self.models.copy()
    
    def is_model_loaded(self, model_id: str) -> bool:
        """Check if a model is currently loaded."""
        return model_id in self.models
    
    def get_model_status(self, model_id: str) -> Optional[ModelStatus]:
        """Get the current status of a model."""
        if model_id in self.model_info:
            return self.model_info[model_id].status
        return None
    
    def register_model_info(self, model_id: str, model_info: ModelInfo):
        """Register model information."""
        self.model_info[model_id] = model_info