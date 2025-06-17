"""
DeepSeek R1 GGUF Integration for reVoAgent
Supports local GGUF models from Hugging Face with llama-cpp-python
"""

import os
import logging
import asyncio
import time
from typing import Dict, Any, Optional, List, AsyncGenerator
from dataclasses import dataclass
from pathlib import Path
import json

try:
    from llama_cpp import Llama
    from huggingface_hub import hf_hub_download, snapshot_download
    GGUF_AVAILABLE = True
except ImportError:
    GGUF_AVAILABLE = False
    Llama = None

logger = logging.getLogger("deepseek_r1_gguf")

@dataclass
class GGUFModelConfig:
    """Configuration for GGUF model"""
    model_id: str
    model_file: str
    repo_id: str
    n_ctx: int = 4096
    n_threads: int = 4
    n_gpu_layers: int = 0  # 0 for CPU-only
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 1024
    verbose: bool = False

class DeepSeekR1GGUFIntegration:
    """
    DeepSeek R1 GGUF Integration using llama-cpp-python
    
    Supports the unsloth/DeepSeek-R1-0528-Qwen3-8B-GGUF model from Hugging Face
    """
    
    def __init__(self, config: Optional[GGUFModelConfig] = None):
        self.config = config or self._get_default_config()
        self.model: Optional[Llama] = None
        self.model_path: Optional[str] = None
        self.is_loaded = False
        self.download_progress = {"status": "not_started", "progress": 0}
        
        # Performance metrics
        self.metrics = {
            "total_requests": 0,
            "total_tokens_generated": 0,
            "average_response_time": 0.0,
            "model_load_time": 0.0,
            "last_request_time": 0.0
        }
        
        if not GGUF_AVAILABLE:
            logger.warning("llama-cpp-python not available. GGUF integration disabled.")
    
    def _get_default_config(self) -> GGUFModelConfig:
        """Get default configuration for DeepSeek R1 GGUF"""
        return GGUFModelConfig(
            model_id="deepseek-r1-qwen3-8b-gguf",
            model_file="DeepSeek-R1-0528-Qwen3-8B-Q4_K_M.gguf",  # 4-bit quantized
            repo_id="unsloth/DeepSeek-R1-0528-Qwen3-8B-GGUF",
            n_ctx=4096,
            n_threads=min(8, os.cpu_count() or 4),
            n_gpu_layers=0,  # CPU-only by default
            temperature=0.7,
            top_p=0.9,
            max_tokens=1024,
            verbose=False
        )
    
    async def initialize(self) -> bool:
        """Initialize the GGUF model"""
        if not GGUF_AVAILABLE:
            logger.error("llama-cpp-python not available")
            return False
        
        try:
            logger.info(f"Initializing DeepSeek R1 GGUF model: {self.config.model_id}")
            
            # Download model if needed
            model_path = await self._ensure_model_downloaded()
            if not model_path:
                return False
            
            # Load model
            start_time = time.time()
            await self._load_model(model_path)
            load_time = time.time() - start_time
            
            self.metrics["model_load_time"] = load_time
            self.is_loaded = True
            
            logger.info(f"DeepSeek R1 GGUF model loaded successfully in {load_time:.2f}s")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize GGUF model: {e}")
            return False
    
    async def _ensure_model_downloaded(self) -> Optional[str]:
        """Download model from Hugging Face if not present"""
        try:
            # Create models directory
            models_dir = Path("./models/gguf")
            models_dir.mkdir(parents=True, exist_ok=True)
            
            model_path = models_dir / self.config.model_file
            
            if model_path.exists():
                logger.info(f"Model already exists: {model_path}")
                return str(model_path)
            
            logger.info(f"Downloading model from {self.config.repo_id}")
            self.download_progress = {"status": "downloading", "progress": 0}
            
            # Download the specific GGUF file
            downloaded_path = await asyncio.to_thread(
                hf_hub_download,
                repo_id=self.config.repo_id,
                filename=self.config.model_file,
                local_dir=models_dir,
                local_dir_use_symlinks=False
            )
            
            self.download_progress = {"status": "completed", "progress": 100}
            logger.info(f"Model downloaded successfully: {downloaded_path}")
            return downloaded_path
            
        except Exception as e:
            logger.error(f"Failed to download model: {e}")
            self.download_progress = {"status": "failed", "progress": 0}
            return None
    
    async def _load_model(self, model_path: str) -> None:
        """Load the GGUF model using llama-cpp-python"""
        def _load():
            return Llama(
                model_path=model_path,
                n_ctx=self.config.n_ctx,
                n_threads=self.config.n_threads,
                n_gpu_layers=self.config.n_gpu_layers,
                verbose=self.config.verbose,
                use_mmap=True,
                use_mlock=False
            )
        
        # Load model in thread to avoid blocking
        self.model = await asyncio.to_thread(_load)
        self.model_path = model_path
    
    async def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate text using the GGUF model"""
        if not self.is_loaded or not self.model:
            return await self._fallback_response(prompt, "Model not loaded")
        
        try:
            start_time = time.time()
            
            # Prepare generation parameters
            generation_params = {
                "prompt": prompt,
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature),
                "top_p": kwargs.get("top_p", self.config.top_p),
                "echo": False,
                "stop": kwargs.get("stop", ["</s>", "<|im_end|>", "<|endoftext|>"]),
                "stream": False
            }
            
            # Generate response
            def _generate():
                return self.model(**generation_params)
            
            response = await asyncio.to_thread(_generate)
            
            # Extract response data
            generated_text = response["choices"][0]["text"]
            usage = response.get("usage", {})
            
            # Update metrics
            response_time = time.time() - start_time
            self._update_metrics(response_time, usage.get("completion_tokens", 0))
            
            return {
                "content": generated_text.strip(),
                "response": generated_text.strip(),
                "model": self.config.model_id,
                "usage": {
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0)
                },
                "cost": 0.0,  # Local model, no cost
                "response_time": response_time,
                "model_type": "gguf",
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return await self._fallback_response(prompt, str(e))
    
    async def stream_generate(self, prompt: str, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream generate text using the GGUF model"""
        if not self.is_loaded or not self.model:
            yield {"error": "Model not loaded", "type": "error"}
            return
        
        try:
            # Prepare generation parameters
            generation_params = {
                "prompt": prompt,
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature),
                "top_p": kwargs.get("top_p", self.config.top_p),
                "echo": False,
                "stop": kwargs.get("stop", ["</s>", "<|im_end|>", "<|endoftext|>"]),
                "stream": True
            }
            
            # Stream generation
            def _stream_generate():
                return self.model(**generation_params)
            
            stream = await asyncio.to_thread(_stream_generate)
            
            for chunk in stream:
                if chunk["choices"][0]["text"]:
                    yield {
                        "type": "content",
                        "content": chunk["choices"][0]["text"],
                        "model": self.config.model_id,
                        "timestamp": time.time()
                    }
            
            yield {"type": "done", "model": self.config.model_id}
            
        except Exception as e:
            logger.error(f"Streaming generation failed: {e}")
            yield {"error": str(e), "type": "error"}
    
    async def _fallback_response(self, prompt: str, error: str) -> Dict[str, Any]:
        """Provide fallback response when model fails"""
        fallback_content = f"""🤖 DeepSeek R1 GGUF Response (Fallback Mode)

I apologize, but the local GGUF model is currently unavailable ({error}).

For your prompt: "{prompt[:100]}..."

This is a fallback response. To enable real AI generation:
1. Ensure the model is properly downloaded
2. Check system resources (RAM/CPU)
3. Verify llama-cpp-python installation

The system will attempt to use the real model for future requests."""

        return {
            "content": fallback_content,
            "response": fallback_content,
            "model": f"{self.config.model_id}-fallback",
            "usage": {
                "prompt_tokens": len(prompt.split()),
                "completion_tokens": len(fallback_content.split()),
                "total_tokens": len(prompt.split()) + len(fallback_content.split())
            },
            "cost": 0.0,
            "response_time": 0.1,
            "model_type": "fallback",
            "error": error,
            "timestamp": time.time()
        }
    
    def _update_metrics(self, response_time: float, tokens_generated: int) -> None:
        """Update performance metrics"""
        self.metrics["total_requests"] += 1
        self.metrics["total_tokens_generated"] += tokens_generated
        self.metrics["last_request_time"] = response_time
        
        # Update average response time
        total_requests = self.metrics["total_requests"]
        current_avg = self.metrics["average_response_time"]
        self.metrics["average_response_time"] = (
            (current_avg * (total_requests - 1) + response_time) / total_requests
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get model status and metrics"""
        return {
            "model_id": self.config.model_id,
            "model_file": self.config.model_file,
            "repo_id": self.config.repo_id,
            "is_loaded": self.is_loaded,
            "model_path": self.model_path,
            "download_progress": self.download_progress,
            "config": {
                "n_ctx": self.config.n_ctx,
                "n_threads": self.config.n_threads,
                "n_gpu_layers": self.config.n_gpu_layers,
                "temperature": self.config.temperature,
                "top_p": self.config.top_p,
                "max_tokens": self.config.max_tokens
            },
            "metrics": self.metrics,
            "gguf_available": GGUF_AVAILABLE
        }
    
    async def unload(self) -> None:
        """Unload the model to free memory"""
        if self.model:
            del self.model
            self.model = None
            self.is_loaded = False
            logger.info("Model unloaded successfully")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get detailed model information"""
        return {
            "name": "DeepSeek R1 0528 Qwen3 8B GGUF",
            "description": "DeepSeek R1 model optimized for reasoning tasks, quantized to GGUF format",
            "source": "unsloth/DeepSeek-R1-0528-Qwen3-8B-GGUF",
            "quantization": "Q4_K_M (4-bit)",
            "context_length": self.config.n_ctx,
            "parameters": "8B",
            "type": "local_gguf",
            "capabilities": [
                "Text generation",
                "Code generation", 
                "Reasoning tasks",
                "Question answering",
                "Creative writing"
            ],
            "requirements": {
                "ram": "8GB+ recommended",
                "storage": "5GB+ for model file",
                "cpu": "4+ cores recommended"
            }
        }

# Global instance for easy access
deepseek_r1_gguf = DeepSeekR1GGUFIntegration()

async def initialize_deepseek_r1_gguf() -> bool:
    """Initialize the global DeepSeek R1 GGUF instance"""
    return await deepseek_r1_gguf.initialize()

async def generate_with_deepseek_r1(prompt: str, **kwargs) -> Dict[str, Any]:
    """Generate text using DeepSeek R1 GGUF"""
    return await deepseek_r1_gguf.generate(prompt, **kwargs)

def get_deepseek_r1_status() -> Dict[str, Any]:
    """Get DeepSeek R1 GGUF status"""
    return deepseek_r1_gguf.get_status()