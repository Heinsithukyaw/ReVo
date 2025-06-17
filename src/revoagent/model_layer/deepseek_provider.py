"""
DeepSeek R1 Provider - Zero-Cost AI Model Serving

Provides DeepSeek R1 0528 model integration with automatic system detection
and optimization for CPU/GPU execution.
"""

import asyncio
import logging
import torch
import psutil
import platform
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import json
import time

logger = logging.getLogger(__name__)


class ExecutionMode(Enum):
    """Model execution modes."""
    CPU = "cpu"
    GPU = "gpu"
    AUTO = "auto"


class ModelFormat(Enum):
    """Model formats."""
    TRANSFORMERS = "transformers"
    GGUF = "gguf"
    VLLM = "vllm"


@dataclass
class SystemCapabilities:
    """System hardware capabilities."""
    cpu_cores: int
    cpu_threads: int
    total_ram_gb: float
    available_ram_gb: float
    has_gpu: bool
    gpu_count: int
    gpu_memory_gb: float
    gpu_name: str
    platform: str
    architecture: str
    recommended_mode: ExecutionMode
    recommended_format: ModelFormat
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "cpu_cores": self.cpu_cores,
            "cpu_threads": self.cpu_threads,
            "total_ram_gb": self.total_ram_gb,
            "available_ram_gb": self.available_ram_gb,
            "has_gpu": self.has_gpu,
            "gpu_count": self.gpu_count,
            "gpu_memory_gb": self.gpu_memory_gb,
            "gpu_name": self.gpu_name,
            "platform": self.platform,
            "architecture": self.architecture,
            "recommended_mode": self.recommended_mode.value,
            "recommended_format": self.recommended_format.value
        }


@dataclass
class ModelConfig:
    """Configuration for DeepSeek model."""
    model_name: str = "deepseek-ai/DeepSeek-R1-0528"
    execution_mode: ExecutionMode = ExecutionMode.AUTO
    model_format: ModelFormat = ModelFormat.TRANSFORMERS
    max_length: int = 2048
    temperature: float = 0.1
    top_p: float = 0.9
    do_sample: bool = True
    trust_remote_code: bool = True
    device_map: Optional[str] = "auto"
    torch_dtype: Optional[str] = "auto"
    load_in_8bit: bool = False
    load_in_4bit: bool = False
    use_cache: bool = True
    cache_dir: Optional[str] = None


class SystemDetector:
    """Detects system capabilities and recommends optimal configuration."""
    
    @staticmethod
    def detect_system() -> SystemCapabilities:
        """Detect system hardware capabilities."""
        logger.info("Detecting system capabilities...")
        
        # CPU information
        cpu_cores = psutil.cpu_count(logical=False)
        cpu_threads = psutil.cpu_count(logical=True)
        
        # Memory information
        memory = psutil.virtual_memory()
        total_ram_gb = memory.total / (1024**3)
        available_ram_gb = memory.available / (1024**3)
        
        # Platform information
        system_platform = platform.system()
        architecture = platform.machine()
        
        # GPU detection
        has_gpu = False
        gpu_count = 0
        gpu_memory_gb = 0.0
        gpu_name = "None"
        
        try:
            import torch
            if torch.cuda.is_available():
                has_gpu = True
                gpu_count = torch.cuda.device_count()
                if gpu_count > 0:
                    gpu_properties = torch.cuda.get_device_properties(0)
                    gpu_memory_gb = gpu_properties.total_memory / (1024**3)
                    gpu_name = gpu_properties.name
                    logger.info(f"GPU detected: {gpu_name} with {gpu_memory_gb:.1f}GB VRAM")
        except ImportError:
            logger.warning("PyTorch not available, GPU detection skipped")
        except Exception as e:
            logger.warning(f"GPU detection failed: {e}")
        
        # Determine recommendations
        recommended_mode, recommended_format = SystemDetector._get_recommendations(
            cpu_cores, total_ram_gb, has_gpu, gpu_memory_gb
        )
        
        capabilities = SystemCapabilities(
            cpu_cores=cpu_cores,
            cpu_threads=cpu_threads,
            total_ram_gb=total_ram_gb,
            available_ram_gb=available_ram_gb,
            has_gpu=has_gpu,
            gpu_count=gpu_count,
            gpu_memory_gb=gpu_memory_gb,
            gpu_name=gpu_name,
            platform=system_platform,
            architecture=architecture,
            recommended_mode=recommended_mode,
            recommended_format=recommended_format
        )
        
        logger.info(f"System detection complete: {capabilities.to_dict()}")
        return capabilities
    
    @staticmethod
    def _get_recommendations(cpu_cores: int, 
                           total_ram_gb: float, 
                           has_gpu: bool, 
                           gpu_memory_gb: float) -> tuple[ExecutionMode, ModelFormat]:
        """Get recommended execution mode and format."""
        
        # GPU recommendations
        if has_gpu and gpu_memory_gb >= 16:
            return ExecutionMode.GPU, ModelFormat.TRANSFORMERS
        elif has_gpu and gpu_memory_gb >= 8:
            return ExecutionMode.GPU, ModelFormat.TRANSFORMERS
        elif has_gpu and gpu_memory_gb >= 4:
            return ExecutionMode.GPU, ModelFormat.GGUF
        
        # CPU recommendations
        if total_ram_gb >= 32 and cpu_cores >= 8:
            return ExecutionMode.CPU, ModelFormat.TRANSFORMERS
        elif total_ram_gb >= 16 and cpu_cores >= 4:
            return ExecutionMode.CPU, ModelFormat.GGUF
        else:
            return ExecutionMode.CPU, ModelFormat.GGUF
    
    @staticmethod
    def get_optimal_config(capabilities: SystemCapabilities, 
                          user_preference: Optional[ExecutionMode] = None) -> ModelConfig:
        """Get optimal model configuration based on system capabilities."""
        
        execution_mode = user_preference or capabilities.recommended_mode
        model_format = capabilities.recommended_format
        
        config = ModelConfig(
            execution_mode=execution_mode,
            model_format=model_format
        )
        
        # Adjust configuration based on capabilities
        if execution_mode == ExecutionMode.GPU:
            if capabilities.gpu_memory_gb < 8:
                config.load_in_8bit = True
            elif capabilities.gpu_memory_gb < 4:
                config.load_in_4bit = True
            
            config.device_map = "auto"
            config.torch_dtype = "float16"
        else:
            config.device_map = "cpu"
            config.torch_dtype = "float32"
            
            # CPU optimizations
            if capabilities.available_ram_gb < 16:
                config.load_in_8bit = True
                config.max_length = 1024
        
        # Cache configuration
        config.cache_dir = str(Path.home() / ".cache" / "revoagent" / "models")
        
        return config


class DeepSeekTransformersProvider:
    """DeepSeek R1 provider using Transformers library."""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.model = None
        self.tokenizer = None
        self.pipeline = None
        self.is_loaded = False
        
    async def load_model(self) -> bool:
        """Load the DeepSeek model."""
        try:
            logger.info(f"Loading DeepSeek R1 model: {self.config.model_name}")
            
            # Import transformers
            from transformers import (
                AutoTokenizer, 
                AutoModelForCausalLM, 
                pipeline,
                BitsAndBytesConfig
            )
            
            # Prepare loading arguments
            model_kwargs = {
                "trust_remote_code": self.config.trust_remote_code,
                "cache_dir": self.config.cache_dir,
                "use_cache": self.config.use_cache
            }
            
            # Configure quantization
            if self.config.load_in_8bit or self.config.load_in_4bit:
                quantization_config = BitsAndBytesConfig(
                    load_in_8bit=self.config.load_in_8bit,
                    load_in_4bit=self.config.load_in_4bit,
                    bnb_4bit_compute_dtype=torch.float16 if self.config.load_in_4bit else None
                )
                model_kwargs["quantization_config"] = quantization_config
            
            # Configure device and dtype
            if self.config.device_map:
                model_kwargs["device_map"] = self.config.device_map
            
            if self.config.torch_dtype and self.config.torch_dtype != "auto":
                if self.config.torch_dtype == "float16":
                    model_kwargs["torch_dtype"] = torch.float16
                elif self.config.torch_dtype == "float32":
                    model_kwargs["torch_dtype"] = torch.float32
            
            # Load tokenizer
            logger.info("Loading tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.config.model_name,
                trust_remote_code=self.config.trust_remote_code,
                cache_dir=self.config.cache_dir
            )
            
            # Load model
            logger.info("Loading model...")
            self.model = AutoModelForCausalLM.from_pretrained(
                self.config.model_name,
                **model_kwargs
            )
            
            # Create pipeline
            logger.info("Creating pipeline...")
            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                trust_remote_code=self.config.trust_remote_code,
                device_map=self.config.device_map
            )
            
            self.is_loaded = True
            logger.info("DeepSeek R1 model loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error loading DeepSeek model: {e}")
            return False
    
    async def generate(self, 
                      messages: List[Dict[str, str]], 
                      **kwargs) -> str:
        """Generate text using the model."""
        if not self.is_loaded:
            raise RuntimeError("Model not loaded")
        
        try:
            # Prepare generation parameters
            generation_kwargs = {
                "max_length": kwargs.get("max_length", self.config.max_length),
                "temperature": kwargs.get("temperature", self.config.temperature),
                "top_p": kwargs.get("top_p", self.config.top_p),
                "do_sample": kwargs.get("do_sample", self.config.do_sample),
                "pad_token_id": self.tokenizer.eos_token_id,
                "return_full_text": False
            }
            
            # Generate using pipeline
            result = self.pipeline(messages, **generation_kwargs)
            
            if result and len(result) > 0:
                return result[0]["generated_text"]
            else:
                return ""
                
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            raise
    
    async def generate_simple(self, prompt: str, **kwargs) -> str:
        """Generate text from a simple prompt."""
        messages = [{"role": "user", "content": prompt}]
        return await self.generate(messages, **kwargs)
    
    def unload_model(self):
        """Unload the model to free memory."""
        if self.model:
            del self.model
            self.model = None
        
        if self.tokenizer:
            del self.tokenizer
            self.tokenizer = None
        
        if self.pipeline:
            del self.pipeline
            self.pipeline = None
        
        # Clear GPU cache if available
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except:
            pass
        
        self.is_loaded = False
        logger.info("DeepSeek model unloaded")


class DeepSeekGGUFProvider:
    """DeepSeek R1 provider using GGUF format with llama.cpp."""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.llama_cpp = None
        self.is_loaded = False
        
    async def load_model(self) -> bool:
        """Load the DeepSeek model in GGUF format."""
        try:
            logger.info("Loading DeepSeek R1 model in GGUF format")
            
            # Try to import llama-cpp-python
            try:
                from llama_cpp import Llama
            except ImportError:
                logger.error("llama-cpp-python not installed. Install with: pip install llama-cpp-python")
                return False
            
            # Find or download GGUF model
            model_path = await self._get_gguf_model_path()
            if not model_path:
                logger.error("GGUF model not found")
                return False
            
            # Configure llama.cpp parameters
            llama_kwargs = {
                "model_path": str(model_path),
                "n_ctx": self.config.max_length,
                "verbose": False,
                "use_mmap": True,
                "use_mlock": False
            }
            
            # GPU configuration
            if self.config.execution_mode == ExecutionMode.GPU:
                try:
                    import torch
                    if torch.cuda.is_available():
                        llama_kwargs["n_gpu_layers"] = -1  # Use all GPU layers
                        logger.info("Using GPU acceleration for GGUF model")
                except:
                    logger.warning("GPU acceleration not available, using CPU")
            
            # CPU configuration
            if self.config.execution_mode == ExecutionMode.CPU:
                # Use multiple threads for CPU
                llama_kwargs["n_threads"] = min(psutil.cpu_count(), 8)
            
            # Load model
            self.llama_cpp = Llama(**llama_kwargs)
            self.is_loaded = True
            
            logger.info("DeepSeek R1 GGUF model loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error loading GGUF model: {e}")
            return False
    
    async def _get_gguf_model_path(self) -> Optional[Path]:
        """Get path to GGUF model, download if necessary."""
        cache_dir = Path(self.config.cache_dir or Path.home() / ".cache" / "revoagent" / "models")
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Look for existing GGUF files
        gguf_files = list(cache_dir.glob("*.gguf"))
        if gguf_files:
            logger.info(f"Found existing GGUF model: {gguf_files[0]}")
            return gguf_files[0]
        
        # Try to download a compatible GGUF model
        logger.info("No GGUF model found, attempting to download...")
        
        # This would typically download from Hugging Face or other sources
        # For now, we'll provide instructions to the user
        logger.warning("""
GGUF model not found. Please download a compatible DeepSeek R1 GGUF model:

1. Visit: https://huggingface.co/deepseek-ai/DeepSeek-R1-0528
2. Download a .gguf file (e.g., deepseek-r1-0528.q4_0.gguf)
3. Place it in: {cache_dir}

Or use the transformers format instead.
        """.format(cache_dir=cache_dir))
        
        return None
    
    async def generate(self, 
                      messages: List[Dict[str, str]], 
                      **kwargs) -> str:
        """Generate text using the GGUF model."""
        if not self.is_loaded:
            raise RuntimeError("Model not loaded")
        
        try:
            # Convert messages to prompt
            prompt = self._messages_to_prompt(messages)
            
            # Generate
            result = self.llama_cpp(
                prompt,
                max_tokens=kwargs.get("max_length", self.config.max_length),
                temperature=kwargs.get("temperature", self.config.temperature),
                top_p=kwargs.get("top_p", self.config.top_p),
                echo=False,
                stop=["</s>", "<|im_end|>"]
            )
            
            if result and "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["text"].strip()
            else:
                return ""
                
        except Exception as e:
            logger.error(f"Error generating text with GGUF: {e}")
            raise
    
    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert messages to prompt format."""
        prompt_parts = []
        
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        prompt_parts.append("Assistant:")
        return "\n".join(prompt_parts)
    
    async def generate_simple(self, prompt: str, **kwargs) -> str:
        """Generate text from a simple prompt."""
        messages = [{"role": "user", "content": prompt}]
        return await self.generate(messages, **kwargs)
    
    def unload_model(self):
        """Unload the model to free memory."""
        if self.llama_cpp:
            del self.llama_cpp
            self.llama_cpp = None
        
        self.is_loaded = False
        logger.info("DeepSeek GGUF model unloaded")


class DeepSeekProvider:
    """Main DeepSeek R1 provider with automatic system detection and optimization."""
    
    def __init__(self, user_preference: Optional[ExecutionMode] = None):
        self.capabilities = SystemDetector.detect_system()
        self.config = SystemDetector.get_optimal_config(self.capabilities, user_preference)
        self.provider = None
        self.is_loaded = False
        
        logger.info(f"DeepSeek provider initialized with {self.config.execution_mode.value} mode")
    
    async def initialize(self) -> bool:
        """Initialize the appropriate provider based on configuration."""
        try:
            if self.config.model_format == ModelFormat.TRANSFORMERS:
                self.provider = DeepSeekTransformersProvider(self.config)
            elif self.config.model_format == ModelFormat.GGUF:
                self.provider = DeepSeekGGUFProvider(self.config)
            else:
                raise ValueError(f"Unsupported model format: {self.config.model_format}")
            
            # Load the model
            success = await self.provider.load_model()
            if success:
                self.is_loaded = True
                logger.info("DeepSeek provider initialized successfully")
            
            return success
            
        except Exception as e:
            logger.error(f"Error initializing DeepSeek provider: {e}")
            return False
    
    async def generate(self, 
                      messages: List[Dict[str, str]], 
                      **kwargs) -> str:
        """Generate text using the loaded model."""
        if not self.is_loaded:
            raise RuntimeError("Provider not initialized")
        
        return await self.provider.generate(messages, **kwargs)
    
    async def generate_simple(self, prompt: str, **kwargs) -> str:
        """Generate text from a simple prompt."""
        if not self.is_loaded:
            raise RuntimeError("Provider not initialized")
        
        return await self.provider.generate_simple(prompt, **kwargs)
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system capabilities and configuration."""
        return {
            "capabilities": self.capabilities.to_dict(),
            "config": {
                "model_name": self.config.model_name,
                "execution_mode": self.config.execution_mode.value,
                "model_format": self.config.model_format.value,
                "max_length": self.config.max_length,
                "temperature": self.config.temperature,
                "load_in_8bit": self.config.load_in_8bit,
                "load_in_4bit": self.config.load_in_4bit
            },
            "is_loaded": self.is_loaded
        }
    
    def get_available_modes(self) -> List[Dict[str, Any]]:
        """Get available execution modes for user selection."""
        modes = []
        
        # CPU mode (always available)
        modes.append({
            "mode": ExecutionMode.CPU.value,
            "name": "CPU Only",
            "description": f"Use {self.capabilities.cpu_cores} CPU cores with {self.capabilities.total_ram_gb:.1f}GB RAM",
            "recommended": self.capabilities.recommended_mode == ExecutionMode.CPU,
            "requirements": "4GB+ RAM recommended"
        })
        
        # GPU mode (if available)
        if self.capabilities.has_gpu:
            modes.append({
                "mode": ExecutionMode.GPU.value,
                "name": f"GPU ({self.capabilities.gpu_name})",
                "description": f"Use GPU with {self.capabilities.gpu_memory_gb:.1f}GB VRAM",
                "recommended": self.capabilities.recommended_mode == ExecutionMode.GPU,
                "requirements": "4GB+ VRAM recommended"
            })
        
        return modes
    
    async def switch_mode(self, new_mode: ExecutionMode) -> bool:
        """Switch execution mode."""
        if new_mode == self.config.execution_mode:
            return True
        
        try:
            # Unload current model
            if self.is_loaded:
                self.provider.unload_model()
                self.is_loaded = False
            
            # Update configuration
            self.config = SystemDetector.get_optimal_config(self.capabilities, new_mode)
            
            # Reinitialize with new mode
            return await self.initialize()
            
        except Exception as e:
            logger.error(f"Error switching mode: {e}")
            return False
    
    def shutdown(self):
        """Shutdown the provider and free resources."""
        if self.provider and self.is_loaded:
            self.provider.unload_model()
        
        self.is_loaded = False
        logger.info("DeepSeek provider shutdown complete")


# Convenience functions for easy usage
async def create_deepseek_provider(execution_mode: Optional[str] = None) -> DeepSeekProvider:
    """Create and initialize a DeepSeek provider."""
    mode = None
    if execution_mode:
        mode = ExecutionMode(execution_mode.lower())
    
    provider = DeepSeekProvider(mode)
    await provider.initialize()
    return provider


async def quick_generate(prompt: str, 
                        execution_mode: Optional[str] = None,
                        **kwargs) -> str:
    """Quick text generation with automatic setup."""
    provider = await create_deepseek_provider(execution_mode)
    try:
        return await provider.generate_simple(prompt, **kwargs)
    finally:
        provider.shutdown()


# Example usage
if __name__ == "__main__":
    async def main():
        # Detect system capabilities
        capabilities = SystemDetector.detect_system()
        print("System Capabilities:")
        print(json.dumps(capabilities.to_dict(), indent=2))
        
        # Create provider
        provider = DeepSeekProvider()
        
        # Show available modes
        print("\nAvailable Execution Modes:")
        for mode in provider.get_available_modes():
            print(f"- {mode['name']}: {mode['description']}")
            if mode['recommended']:
                print("  (Recommended)")
        
        # Initialize provider
        if await provider.initialize():
            print(f"\nProvider initialized successfully!")
            print(f"Using: {provider.config.execution_mode.value} mode with {provider.config.model_format.value} format")
            
            # Test generation
            try:
                response = await provider.generate_simple("Hello, who are you?")
                print(f"\nTest Response: {response}")
            except Exception as e:
                print(f"Generation failed: {e}")
        else:
            print("Failed to initialize provider")
        
        # Cleanup
        provider.shutdown()
    
    asyncio.run(main())