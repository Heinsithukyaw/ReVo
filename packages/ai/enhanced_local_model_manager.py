import os
import asyncio
import torch
from typing import Dict, Any, Optional, List
import logging
from dataclasses import dataclass
from enum import Enum
import gc
from concurrent.futures import ThreadPoolExecutor
import psutil

logger = logging.getLogger(__name__)

class ModelProvider(Enum):
    DEEPSEEK_R1 = "deepseek_r1_0528"
    LLAMA_LOCAL = "llama_local"
    OPENAI_BACKUP = "openai"
    ANTHROPIC_BACKUP = "anthropic"
    FALLBACK_MOCK = "mock"

@dataclass
class GenerationRequest:
    prompt: str
    max_tokens: int = 1024
    temperature: float = 0.7
    task_type: str = "general"
    system_prompt: Optional[str] = None
    preferred_provider: Optional[ModelProvider] = None

@dataclass
class GenerationResponse:
    content: str
    provider: ModelProvider
    tokens_used: int
    generation_time: float
    cost: float = 0.0
    reasoning_steps: Optional[List[str]] = None

@dataclass
class SystemResources:
    total_memory: float
    available_memory: float
    gpu_available: bool
    gpu_memory: float = 0.0
    cpu_cores: int = 1

class EnhancedLocalModelManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.models = {}
        self.tokenizers = {}
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.resources = self._check_system_resources()
        self.initialization_lock = asyncio.Lock()
        self.available_providers = []
        
    def _check_system_resources(self) -> SystemResources:
        """Check available system resources for optimal model loading"""
        memory = psutil.virtual_memory()
        
        resources = SystemResources(
            total_memory=memory.total / (1024**3),  # GB
            available_memory=memory.available / (1024**3),  # GB
            gpu_available=torch.cuda.is_available(),
            cpu_cores=psutil.cpu_count()
        )
        
        if resources.gpu_available:
            resources.gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            
        logger.info(f"System Resources: {resources}")
        return resources
    
    async def initialize_with_fallback(self):
        """Initialize models with intelligent fallback based on resources"""
        async with self.initialization_lock:
            logger.info("🤖 Initializing AI models with resource-aware fallback...")
            
            # Always add mock fallback first
            self.available_providers.append(ModelProvider.FALLBACK_MOCK)
            
            # Try to initialize real models
            await self._try_initialize_deepseek()
            await self._try_initialize_api_providers()
            
            logger.info(f"✅ Available providers: {[p.value for p in self.available_providers]}")
    
    async def _try_initialize_deepseek(self):
        """Try to initialize DeepSeek R1 with fallback"""
        try:
            if self.resources.available_memory > 2.0:  # 2GB minimum
                logger.info("📥 Attempting to load DeepSeek R1...")
                
                # Try to import transformers
                from transformers import AutoTokenizer, AutoModelForCausalLM
                
                model_name = "deepseek-ai/deepseek-r1-distill-qwen-1.5b"
                
                # Simple CPU-based loading for compatibility
                tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
                model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    torch_dtype=torch.float32,
                    device_map="cpu",
                    trust_remote_code=True,
                    low_cpu_mem_usage=True
                )
                
                self.tokenizers[ModelProvider.DEEPSEEK_R1] = tokenizer
                self.models[ModelProvider.DEEPSEEK_R1] = model
                self.available_providers.append(ModelProvider.DEEPSEEK_R1)
                
                logger.info("✅ DeepSeek R1 loaded successfully")
                
        except Exception as e:
            logger.warning(f"⚠️ DeepSeek R1 failed to load: {e}")
            logger.info("💡 Consider installing: pip install torch transformers accelerate")
    
    async def _try_initialize_api_providers(self):
        """Try to initialize API providers"""
        if self.config.get("openai_api_key"):
            self.available_providers.append(ModelProvider.OPENAI_BACKUP)
            logger.info("✅ OpenAI backup enabled")
        
        if self.config.get("anthropic_api_key"):
            self.available_providers.append(ModelProvider.ANTHROPIC_BACKUP)
            logger.info("✅ Anthropic backup enabled")
    
    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate response using best available provider"""
        for provider in self.available_providers:
            try:
                if provider == ModelProvider.DEEPSEEK_R1:
                    return await self._generate_deepseek(request)
                elif provider == ModelProvider.FALLBACK_MOCK:
                    return await self._generate_mock(request)
                # Add other providers as needed
            except Exception as e:
                logger.warning(f"Provider {provider.value} failed: {e}")
                continue
        
        # If all fail, return error response
        return GenerationResponse(
            content="⚠️ All AI providers unavailable. Please check configuration.",
            provider=ModelProvider.FALLBACK_MOCK,
            tokens_used=0,
            generation_time=0,
            cost=0.0
        )
    
    async def _generate_deepseek(self, request: GenerationRequest) -> GenerationResponse:
        """Generate with DeepSeek R1"""
        model = self.models[ModelProvider.DEEPSEEK_R1]
        tokenizer = self.tokenizers[ModelProvider.DEEPSEEK_R1]
        
        # Format prompt
        system_prompt = request.system_prompt or "You are a helpful AI assistant."
        formatted_prompt = f"System: {system_prompt}\nUser: {request.prompt}\nAssistant:"
        
        # Tokenize and generate
        inputs = tokenizer(formatted_prompt, return_tensors="pt")
        
        with torch.no_grad():
            outputs = model.generate(
                inputs.input_ids,
                max_new_tokens=min(request.max_tokens, 512),  # Limit for stability
                temperature=request.temperature,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
        
        # Decode response
        response_text = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
        
        return GenerationResponse(
            content=response_text.strip(),
            provider=ModelProvider.DEEPSEEK_R1,
            tokens_used=len(outputs[0]),
            generation_time=1.0,  # Placeholder
            cost=0.0
        )
    
    async def _generate_mock(self, request: GenerationRequest) -> GenerationResponse:
        """Mock generation for testing"""
        mock_responses = [
            "I'm a mock AI assistant. The real models are currently unavailable.",
            "This is a fallback response. Please configure your AI providers.",
            "Mock response: I understand your request but I'm running in fallback mode."
        ]
        
        import random
        response = random.choice(mock_responses)
        
        return GenerationResponse(
            content=response,
            provider=ModelProvider.FALLBACK_MOCK,
            tokens_used=len(response.split()),
            generation_time=0.1,
            cost=0.0
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """Check model manager health"""
        return {
            "status": "healthy",
            "available_providers": [p.value for p in self.available_providers],
            "resources": {
                "memory_gb": self.resources.available_memory,
                "gpu_available": self.resources.gpu_available,
                "cpu_cores": self.resources.cpu_cores
            }
        }
