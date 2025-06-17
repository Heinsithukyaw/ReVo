#!/usr/bin/env python3
"""
GGUF Model Manager for DeepSeek R1 Integration
Provides native GGUF model loading and inference using llama-cpp-python

This module handles:
- GGUF model loading and initialization
- Local inference with DeepSeek R1 
- Memory and performance optimization
- Model health monitoring
- Zero-cost local processing
"""

import asyncio
import logging
import json
import time
import os
import psutil
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Optional GGUF dependencies
try:
    from llama_cpp import Llama
    GGUF_AVAILABLE = True
    logger.info("✅ llama-cpp-python is available for GGUF models")
except ImportError:
    GGUF_AVAILABLE = False
    logger.warning("⚠️ llama-cpp-python not installed. Install with: pip install llama-cpp-python")
    Llama = None

@dataclass
class GGUFModelConfig:
    """Configuration for GGUF models"""
    model_path: str
    model_name: str
    context_length: int = 4096
    n_threads: int = 8
    n_gpu_layers: int = 0  # 0 = CPU only, -1 = all GPU layers
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    repeat_penalty: float = 1.1
    max_tokens: int = 2048
    verbose: bool = False
    chat_format: str = "chatml"

@dataclass
class GGUFResponse:
    """Response from GGUF model inference"""
    text: str
    tokens_generated: int
    inference_time: float
    tokens_per_second: float
    success: bool
    error_message: Optional[str] = None

class GGUFModelManager:
    """
    GGUF Model Manager for local AI inference
    
    Handles DeepSeek R1 and other GGUF models with:
    - Local model loading and initialization
    - Efficient inference with performance monitoring
    - Memory management and optimization
    - Zero-cost local processing
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize GGUF Model Manager"""
        self.config = config or {}
        self.models: Dict[str, Llama] = {}
        self.model_configs: Dict[str, GGUFModelConfig] = {}
        self.model_stats: Dict[str, Dict[str, Any]] = {}
        
        # Performance metrics
        self.metrics = {
            "total_inferences": 0,
            "successful_inferences": 0,
            "failed_inferences": 0,
            "total_tokens_generated": 0,
            "total_inference_time": 0.0,
            "average_tokens_per_second": 0.0,
            "memory_usage_mb": 0.0,
            "models_loaded": 0
        }
        
        logger.info("🤖 GGUF Model Manager initialized")
        
        if not GGUF_AVAILABLE:
            logger.error("❌ llama-cpp-python not available. GGUF models will not work.")
            return
        
        # Load model configurations
        self._load_model_configs()
        
    def _load_model_configs(self):
        """Load GGUF model configurations"""
        
        # DeepSeek R1 Configuration
        deepseek_config_path = Path("models/deepseek-r1/config.json")
        if deepseek_config_path.exists():
            try:
                with open(deepseek_config_path, 'r') as f:
                    deepseek_data = json.load(f)
                
                deepseek_config = GGUFModelConfig(
                    model_path=deepseek_data.get("model_path", "models/deepseek-r1/DeepSeek-R1-0528-Qwen3-8B-Q4_K_M.gguf"),
                    model_name=deepseek_data.get("model_name", "DeepSeek-R1"),
                    context_length=deepseek_data.get("context_length", 4096),
                    n_threads=deepseek_data.get("n_threads", 8),
                    n_gpu_layers=deepseek_data.get("n_gpu_layers", 0),
                    temperature=deepseek_data.get("temperature", 0.7),
                    top_p=deepseek_data.get("top_p", 0.9),
                    top_k=deepseek_data.get("top_k", 40),
                    repeat_penalty=deepseek_data.get("repeat_penalty", 1.1),
                    max_tokens=deepseek_data.get("max_tokens", 2048),
                    verbose=deepseek_data.get("verbose", False),
                    chat_format=deepseek_data.get("chat_format", "chatml")
                )
                
                self.model_configs["deepseek-r1"] = deepseek_config
                self.model_stats["deepseek-r1"] = {
                    "loaded": False,
                    "load_time": 0.0,
                    "memory_usage": 0.0,
                    "inferences": 0,
                    "total_tokens": 0,
                    "average_speed": 0.0
                }
                
                logger.info(f"✅ DeepSeek R1 configuration loaded from {deepseek_config_path}")
                
            except Exception as e:
                logger.error(f"❌ Failed to load DeepSeek R1 config: {e}")
        else:
            # Default configuration if config file doesn't exist
            default_config = GGUFModelConfig(
                model_path="models/deepseek-r1/DeepSeek-R1-0528-Qwen3-8B-Q4_K_M.gguf",
                model_name="DeepSeek-R1",
                context_length=4096,
                n_threads=8,
                n_gpu_layers=0,
                temperature=0.7
            )
            
            self.model_configs["deepseek-r1"] = default_config
            self.model_stats["deepseek-r1"] = {
                "loaded": False,
                "load_time": 0.0,
                "memory_usage": 0.0,
                "inferences": 0,
                "total_tokens": 0,
                "average_speed": 0.0
            }
            
            logger.info("✅ DeepSeek R1 default configuration loaded")
    
    async def load_model(self, model_id: str) -> bool:
        """Load GGUF model into memory"""
        
        if not GGUF_AVAILABLE:
            logger.error("❌ Cannot load GGUF model: llama-cpp-python not available")
            return False
        
        if model_id not in self.model_configs:
            logger.error(f"❌ Model configuration not found: {model_id}")
            return False
        
        config = self.model_configs[model_id]
        
        # Check if model file exists
        if not os.path.exists(config.model_path):
            logger.error(f"❌ Model file not found: {config.model_path}")
            logger.info(f"💡 Download the model file from:")
            logger.info(f"   {config.model_path}")
            return False
        
        logger.info(f"🔄 Loading GGUF model: {config.model_name}")
        logger.info(f"📁 Model path: {config.model_path}")
        
        start_time = time.time()
        
        try:
            # Initialize llama-cpp model
            model = Llama(
                model_path=config.model_path,
                n_ctx=config.context_length,
                n_threads=config.n_threads,
                n_gpu_layers=config.n_gpu_layers,
                verbose=config.verbose,
                chat_format=config.chat_format
            )
            
            load_time = time.time() - start_time
            
            # Store model and update stats
            self.models[model_id] = model
            self.model_stats[model_id]["loaded"] = True
            self.model_stats[model_id]["load_time"] = load_time
            
            # Calculate memory usage
            process = psutil.Process()
            memory_info = process.memory_info()
            self.model_stats[model_id]["memory_usage"] = memory_info.rss / 1024 / 1024  # MB
            self.metrics["memory_usage_mb"] = memory_info.rss / 1024 / 1024
            self.metrics["models_loaded"] += 1
            
            logger.info(f"✅ GGUF model loaded successfully:")
            logger.info(f"   - Model: {config.model_name}")
            logger.info(f"   - Load time: {load_time:.2f}s")
            logger.info(f"   - Memory usage: {self.model_stats[model_id]['memory_usage']:.1f} MB")
            logger.info(f"   - Context length: {config.context_length}")
            logger.info(f"   - Threads: {config.n_threads}")
            logger.info(f"   - GPU layers: {config.n_gpu_layers}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load GGUF model {model_id}: {e}")
            self.model_stats[model_id]["loaded"] = False
            return False
    
    async def generate_response(self, model_id: str, prompt: str, **kwargs) -> GGUFResponse:
        """Generate response using GGUF model"""
        
        if not GGUF_AVAILABLE:
            return GGUFResponse(
                text="",
                tokens_generated=0,
                inference_time=0.0,
                tokens_per_second=0.0,
                success=False,
                error_message="llama-cpp-python not available"
            )
        
        if model_id not in self.models:
            return GGUFResponse(
                text="",
                tokens_generated=0,
                inference_time=0.0,
                tokens_per_second=0.0,
                success=False,
                error_message=f"Model {model_id} not loaded"
            )
        
        model = self.models[model_id]
        config = self.model_configs[model_id]
        
        # Extract generation parameters
        max_tokens = kwargs.get("max_tokens", config.max_tokens)
        temperature = kwargs.get("temperature", config.temperature)
        top_p = kwargs.get("top_p", config.top_p)
        top_k = kwargs.get("top_k", config.top_k)
        repeat_penalty = kwargs.get("repeat_penalty", config.repeat_penalty)
        
        logger.info(f"🔄 Generating response with {config.model_name}")
        
        start_time = time.time()
        
        try:
            # Generate response
            response = model(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                repeat_penalty=repeat_penalty,
                stop=["</s>", "<|im_end|>", "\n\n"],
                echo=False
            )
            
            inference_time = time.time() - start_time
            
            # Extract response text and tokens
            response_text = response["choices"][0]["text"]
            tokens_generated = len(response_text.split())  # Rough token estimate
            tokens_per_second = tokens_generated / inference_time if inference_time > 0 else 0
            
            # Update metrics
            self.metrics["total_inferences"] += 1
            self.metrics["successful_inferences"] += 1
            self.metrics["total_tokens_generated"] += tokens_generated
            self.metrics["total_inference_time"] += inference_time
            
            # Update model stats
            self.model_stats[model_id]["inferences"] += 1
            self.model_stats[model_id]["total_tokens"] += tokens_generated
            self.model_stats[model_id]["average_speed"] = (
                self.model_stats[model_id]["total_tokens"] / 
                (self.model_stats[model_id]["inferences"] * inference_time)
            )
            
            # Calculate average tokens per second
            if self.metrics["total_inference_time"] > 0:
                self.metrics["average_tokens_per_second"] = (
                    self.metrics["total_tokens_generated"] / self.metrics["total_inference_time"]
                )
            
            logger.info(f"✅ Response generated:")
            logger.info(f"   - Tokens: {tokens_generated}")
            logger.info(f"   - Time: {inference_time:.2f}s")
            logger.info(f"   - Speed: {tokens_per_second:.1f} tokens/s")
            logger.info(f"   - Cost: $0.00 (local processing)")
            
            return GGUFResponse(
                text=response_text,
                tokens_generated=tokens_generated,
                inference_time=inference_time,
                tokens_per_second=tokens_per_second,
                success=True
            )
            
        except Exception as e:
            inference_time = time.time() - start_time
            self.metrics["total_inferences"] += 1
            self.metrics["failed_inferences"] += 1
            
            logger.error(f"❌ GGUF inference failed: {e}")
            
            return GGUFResponse(
                text="",
                tokens_generated=0,
                inference_time=inference_time,
                tokens_per_second=0.0,
                success=False,
                error_message=str(e)
            )
    
    async def chat_completion(self, model_id: str, messages: List[Dict[str, str]], **kwargs) -> GGUFResponse:
        """Generate chat completion using GGUF model"""
        
        if not GGUF_AVAILABLE:
            return GGUFResponse(
                text="",
                tokens_generated=0,
                inference_time=0.0,
                tokens_per_second=0.0,
                success=False,
                error_message="llama-cpp-python not available"
            )
        
        if model_id not in self.models:
            return GGUFResponse(
                text="",
                tokens_generated=0,
                inference_time=0.0,
                tokens_per_second=0.0,
                success=False,
                error_message=f"Model {model_id} not loaded"
            )
        
        model = self.models[model_id]
        config = self.model_configs[model_id]
        
        logger.info(f"🔄 Chat completion with {config.model_name}")
        
        start_time = time.time()
        
        try:
            # Generate chat completion
            response = model.create_chat_completion(
                messages=messages,
                max_tokens=kwargs.get("max_tokens", config.max_tokens),
                temperature=kwargs.get("temperature", config.temperature),
                top_p=kwargs.get("top_p", config.top_p),
                top_k=kwargs.get("top_k", config.top_k),
                repeat_penalty=kwargs.get("repeat_penalty", config.repeat_penalty)
            )
            
            inference_time = time.time() - start_time
            
            # Extract response
            response_text = response["choices"][0]["message"]["content"]
            tokens_generated = response["usage"]["completion_tokens"]
            tokens_per_second = tokens_generated / inference_time if inference_time > 0 else 0
            
            # Update metrics
            self.metrics["total_inferences"] += 1
            self.metrics["successful_inferences"] += 1
            self.metrics["total_tokens_generated"] += tokens_generated
            self.metrics["total_inference_time"] += inference_time
            
            logger.info(f"✅ Chat completion generated:")
            logger.info(f"   - Tokens: {tokens_generated}")
            logger.info(f"   - Time: {inference_time:.2f}s")
            logger.info(f"   - Speed: {tokens_per_second:.1f} tokens/s")
            
            return GGUFResponse(
                text=response_text,
                tokens_generated=tokens_generated,
                inference_time=inference_time,
                tokens_per_second=tokens_per_second,
                success=True
            )
            
        except Exception as e:
            inference_time = time.time() - start_time
            self.metrics["total_inferences"] += 1
            self.metrics["failed_inferences"] += 1
            
            logger.error(f"❌ Chat completion failed: {e}")
            
            return GGUFResponse(
                text="",
                tokens_generated=0,
                inference_time=inference_time,
                tokens_per_second=0.0,
                success=False,
                error_message=str(e)
            )
    
    def is_model_loaded(self, model_id: str) -> bool:
        """Check if model is loaded"""
        return model_id in self.models and self.model_stats[model_id]["loaded"]
    
    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get model information"""
        if model_id not in self.model_configs:
            return None
        
        config = self.model_configs[model_id]
        stats = self.model_stats[model_id]
        
        return {
            "model_id": model_id,
            "model_name": config.model_name,
            "model_path": config.model_path,
            "loaded": stats["loaded"],
            "load_time": stats["load_time"],
            "memory_usage_mb": stats["memory_usage"],
            "context_length": config.context_length,
            "n_threads": config.n_threads,
            "n_gpu_layers": config.n_gpu_layers,
            "inferences": stats["inferences"],
            "total_tokens": stats["total_tokens"],
            "average_speed": stats["average_speed"],
            "cost_per_inference": 0.0  # Always $0.00 for local models
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive metrics"""
        success_rate = 0.0
        if self.metrics["total_inferences"] > 0:
            success_rate = (self.metrics["successful_inferences"] / self.metrics["total_inferences"]) * 100
        
        return {
            "performance": {
                "total_inferences": self.metrics["total_inferences"],
                "successful_inferences": self.metrics["successful_inferences"],
                "failed_inferences": self.metrics["failed_inferences"],
                "success_rate": success_rate,
                "total_tokens_generated": self.metrics["total_tokens_generated"],
                "average_tokens_per_second": self.metrics["average_tokens_per_second"],
                "total_inference_time": self.metrics["total_inference_time"]
            },
            "resource_usage": {
                "memory_usage_mb": self.metrics["memory_usage_mb"],
                "models_loaded": self.metrics["models_loaded"]
            },
            "cost_optimization": {
                "total_cost": 0.0,  # Always $0.00 for local models
                "cost_per_inference": 0.0,
                "cost_per_token": 0.0,
                "savings_vs_cloud": self.metrics["total_inferences"] * 0.03  # Estimated savings vs OpenAI
            },
            "models": {
                model_id: self.get_model_info(model_id)
                for model_id in self.model_configs.keys()
            }
        }
    
    def list_available_models(self) -> List[str]:
        """List available model IDs"""
        return list(self.model_configs.keys())
    
    def unload_model(self, model_id: str) -> bool:
        """Unload model from memory"""
        if model_id in self.models:
            del self.models[model_id]
            self.model_stats[model_id]["loaded"] = False
            self.metrics["models_loaded"] -= 1
            logger.info(f"✅ Model {model_id} unloaded")
            return True
        return False
    
    def unload_all_models(self):
        """Unload all models from memory"""
        for model_id in list(self.models.keys()):
            self.unload_model(model_id)
        logger.info("✅ All GGUF models unloaded")

# Factory function for easy integration
async def create_gguf_manager(config: Optional[Dict[str, Any]] = None) -> GGUFModelManager:
    """Create and initialize GGUF Model Manager"""
    manager = GGUFModelManager(config)
    
    # Auto-load DeepSeek R1 if available
    if "deepseek-r1" in manager.model_configs:
        await manager.load_model("deepseek-r1")
    
    return manager

# Example usage
async def main():
    """Example usage of GGUF Model Manager"""
    
    print("🤖 GGUF Model Manager Demo")
    print("=" * 50)
    
    # Initialize manager
    manager = await create_gguf_manager()
    
    if not GGUF_AVAILABLE:
        print("❌ llama-cpp-python not available. Install with:")
        print("   pip install llama-cpp-python")
        return
    
    # Check available models
    models = manager.list_available_models()
    print(f"📋 Available models: {models}")
    
    # Test DeepSeek R1 if loaded
    if manager.is_model_loaded("deepseek-r1"):
        print("\n🔄 Testing DeepSeek R1...")
        
        response = await manager.generate_response(
            "deepseek-r1",
            "Explain the benefits of local AI models for cost optimization:",
            max_tokens=200
        )
        
        if response.success:
            print(f"✅ Response: {response.text[:100]}...")
            print(f"   - Tokens: {response.tokens_generated}")
            print(f"   - Speed: {response.tokens_per_second:.1f} tok/s")
            print(f"   - Cost: $0.00")
        else:
            print(f"❌ Error: {response.error_message}")
    
    # Show metrics
    metrics = manager.get_metrics()
    print(f"\n📊 Metrics:")
    print(f"   - Inferences: {metrics['performance']['total_inferences']}")
    print(f"   - Success rate: {metrics['performance']['success_rate']:.1f}%")
    print(f"   - Memory usage: {metrics['resource_usage']['memory_usage_mb']:.1f} MB")
    print(f"   - Cost savings: ${metrics['cost_optimization']['savings_vs_cloud']:.2f}")

if __name__ == "__main__":
    asyncio.run(main())
