"""
Local Model Manager - Zero-Cost AI Model Execution

Integrates vLLM server functionality from xCodeAgent01 for local model serving.
"""

import asyncio
import logging
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
import httpx
import psutil
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """Configuration for a local model."""
    name: str
    model_path: str
    model_type: str  # 'vllm', 'transformers', 'gguf'
    max_tokens: int = 2048
    temperature: float = 0.1
    top_p: float = 0.9
    gpu_memory_utilization: float = 0.8
    port: int = 8000
    quantization: Optional[str] = None


class VLLMServer:
    """vLLM Server Manager - Integrated from xCodeAgent01."""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        self.client = httpx.AsyncClient(timeout=30.0)
        self.is_running = False
        
    async def start(self) -> bool:
        """Start the vLLM server."""
        if self.is_running:
            return True
            
        try:
            # Check if port is available
            if self._is_port_in_use(self.config.port):
                logger.warning(f"Port {self.config.port} is already in use")
                return False
                
            # Start vLLM server
            cmd = self._build_vllm_command()
            logger.info(f"Starting vLLM server: {' '.join(cmd)}")
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for server to be ready
            if await self._wait_for_server():
                self.is_running = True
                logger.info(f"vLLM server started successfully on port {self.config.port}")
                return True
            else:
                logger.error("Failed to start vLLM server")
                await self.stop()
                return False
                
        except Exception as e:
            logger.error(f"Error starting vLLM server: {e}")
            return False
    
    async def stop(self):
        """Stop the vLLM server."""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            self.process = None
        
        self.is_running = False
        await self.client.aclose()
        logger.info("vLLM server stopped")
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using the vLLM server."""
        if not self.is_running:
            raise RuntimeError("vLLM server is not running")
        
        try:
            payload = {
                "model": self.config.name,
                "prompt": prompt,
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature),
                "top_p": kwargs.get("top_p", self.config.top_p),
                "stream": False
            }
            
            response = await self.client.post(
                f"http://localhost:{self.config.port}/v1/completions",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["text"]
            
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check if the vLLM server is healthy."""
        try:
            response = await self.client.get(
                f"http://localhost:{self.config.port}/health"
            )
            return response.status_code == 200
        except:
            return False
    
    def _build_vllm_command(self) -> List[str]:
        """Build the vLLM server command."""
        cmd = [
            "python", "-m", "vllm.entrypoints.openai.api_server",
            "--model", self.config.model_path,
            "--port", str(self.config.port),
            "--gpu-memory-utilization", str(self.config.gpu_memory_utilization),
            "--max-model-len", str(self.config.max_tokens * 2)
        ]
        
        if self.config.quantization:
            cmd.extend(["--quantization", self.config.quantization])
            
        return cmd
    
    def _is_port_in_use(self, port: int) -> bool:
        """Check if a port is in use."""
        for conn in psutil.net_connections():
            if conn.laddr.port == port:
                return True
        return False
    
    async def _wait_for_server(self, timeout: int = 120) -> bool:
        """Wait for the vLLM server to be ready."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if await self.health_check():
                return True
            await asyncio.sleep(2)
        return False


class LocalModelManager:
    """Manages local AI models with zero-cost execution."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.models: Dict[str, VLLMServer] = {}
        self.active_model: Optional[str] = None
        
    async def load_model(self, model_name: str, model_config: Dict[str, Any]) -> bool:
        """Load a local model."""
        try:
            config = ModelConfig(
                name=model_name,
                model_path=model_config["model_path"],
                model_type=model_config.get("model_type", "vllm"),
                max_tokens=model_config.get("max_tokens", 2048),
                temperature=model_config.get("temperature", 0.1),
                top_p=model_config.get("top_p", 0.9),
                gpu_memory_utilization=model_config.get("gpu_memory_utilization", 0.8),
                port=model_config.get("port", 8000),
                quantization=model_config.get("quantization")
            )
            
            if config.model_type == "vllm":
                server = VLLMServer(config)
                if await server.start():
                    self.models[model_name] = server
                    if not self.active_model:
                        self.active_model = model_name
                    logger.info(f"Model {model_name} loaded successfully")
                    return True
                else:
                    logger.error(f"Failed to load model {model_name}")
                    return False
            else:
                logger.error(f"Unsupported model type: {config.model_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error loading model {model_name}: {e}")
            return False
    
    async def unload_model(self, model_name: str):
        """Unload a model."""
        if model_name in self.models:
            await self.models[model_name].stop()
            del self.models[model_name]
            if self.active_model == model_name:
                self.active_model = list(self.models.keys())[0] if self.models else None
            logger.info(f"Model {model_name} unloaded")
    
    async def generate(self, prompt: str, model_name: Optional[str] = None, **kwargs) -> str:
        """Generate text using a local model."""
        target_model = model_name or self.active_model
        if not target_model or target_model not in self.models:
            raise ValueError(f"Model {target_model} not available")
        
        return await self.models[target_model].generate(prompt, **kwargs)
    
    async def switch_model(self, model_name: str) -> bool:
        """Switch the active model."""
        if model_name in self.models:
            self.active_model = model_name
            logger.info(f"Switched to model: {model_name}")
            return True
        else:
            logger.error(f"Model {model_name} not loaded")
            return False
    
    def get_available_models(self) -> List[str]:
        """Get list of available models."""
        return list(self.models.keys())
    
    def get_active_model(self) -> Optional[str]:
        """Get the currently active model."""
        return self.active_model
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all loaded models."""
        health_status = {}
        for name, model in self.models.items():
            health_status[name] = await model.health_check()
        return health_status
    
    async def shutdown(self):
        """Shutdown all models."""
        for model in self.models.values():
            await model.stop()
        self.models.clear()
        self.active_model = None
        logger.info("All models shutdown")