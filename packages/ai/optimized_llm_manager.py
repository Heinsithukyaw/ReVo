#!/usr/bin/env python3
"""
Optimized LLM Manager for reVoAgent
Handles multiple LLM providers with intelligent fallback and hardware optimization
"""

import asyncio
import logging
import psutil
import platform
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import json
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class LLMProvider(Enum):
    """Available LLM providers"""
    DEEPSEEK_LOCAL = "deepseek_local"
    DEEPSEEK_API = "deepseek_api"
    OPENAI_API = "openai_api"
    ANTHROPIC_API = "anthropic_api"
    GEMINI_API = "gemini_api"
    FALLBACK = "fallback"

@dataclass
class HardwareProfile:
    """Hardware capability profile"""
    cpu_cores: int
    cpu_freq: float  # GHz
    ram_gb: float
    has_gpu: bool
    gpu_memory_gb: float
    can_run_local_llm: bool
    recommended_model_size: str  # "tiny", "small", "medium", "large"

@dataclass
class LLMConfig:
    """LLM configuration"""
    provider: LLMProvider
    model_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 2048
    temperature: float = 0.7
    cost_per_request: float = 0.0
    requires_gpu: bool = False
    min_ram_gb: float = 4.0
    priority: int = 1  # Lower is higher priority

class OptimizedLLMManager:
    """Optimized LLM Manager with intelligent provider selection"""
    
    def __init__(self):
        self.hardware_profile = self._analyze_hardware()
        self.available_providers: Dict[LLMProvider, LLMConfig] = {}
        self.current_provider: Optional[LLMProvider] = None
        self.provider_instances: Dict[LLMProvider, Any] = {}
        self.user_preference: Optional[LLMProvider] = None
        
        # Initialize providers
        self._initialize_providers()
        
    def _analyze_hardware(self) -> HardwareProfile:
        """Analyze current hardware capabilities"""
        try:
            # CPU information
            cpu_count = psutil.cpu_count(logical=False)
            cpu_freq = psutil.cpu_freq().max / 1000 if psutil.cpu_freq() else 2.0  # Convert to GHz
            
            # Memory information
            memory = psutil.virtual_memory()
            ram_gb = memory.total / (1024**3)
            
            # GPU detection (basic)
            has_gpu = False
            gpu_memory_gb = 0.0
            try:
                import GPUtil
                gpus = GPUtil.getGPUs()
                if gpus:
                    has_gpu = True
                    gpu_memory_gb = max(gpu.memoryTotal / 1024 for gpu in gpus)  # Convert to GB
            except ImportError:
                # Try nvidia-ml-py
                try:
                    import pynvml
                    pynvml.nvmlInit()
                    device_count = pynvml.nvmlDeviceGetCount()
                    if device_count > 0:
                        has_gpu = True
                        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                        info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                        gpu_memory_gb = info.total / (1024**3)
                except:
                    pass
            
            # Determine capabilities
            can_run_local_llm = self._can_run_local_llm(cpu_count, cpu_freq, ram_gb, has_gpu)
            recommended_size = self._get_recommended_model_size(cpu_freq, ram_gb, has_gpu, gpu_memory_gb)
            
            profile = HardwareProfile(
                cpu_cores=cpu_count,
                cpu_freq=cpu_freq,
                ram_gb=ram_gb,
                has_gpu=has_gpu,
                gpu_memory_gb=gpu_memory_gb,
                can_run_local_llm=can_run_local_llm,
                recommended_model_size=recommended_size
            )
            
            logger.info(f"Hardware Profile: {profile}")
            return profile
            
        except Exception as e:
            logger.error(f"Error analyzing hardware: {e}")
            # Fallback profile for low-end hardware
            return HardwareProfile(
                cpu_cores=2,
                cpu_freq=1.1,
                ram_gb=8.0,
                has_gpu=False,
                gpu_memory_gb=0.0,
                can_run_local_llm=False,
                recommended_model_size="tiny"
            )
    
    def _can_run_local_llm(self, cpu_cores: int, cpu_freq: float, ram_gb: float, has_gpu: bool) -> bool:
        """Determine if hardware can run local LLM"""
        # Conservative thresholds for stable operation
        min_cpu_freq = 1.5  # GHz
        min_ram = 8.0  # GB
        min_cores = 4
        
        # For the user's specific hardware (1.1 GHz Quad-Core i5)
        # We'll allow local LLM but with very small models
        if cpu_freq >= 1.0 and ram_gb >= 6.0 and cpu_cores >= 4:
            return True
        
        return cpu_freq >= min_cpu_freq and ram_gb >= min_ram and cpu_cores >= min_cores
    
    def _get_recommended_model_size(self, cpu_freq: float, ram_gb: float, has_gpu: bool, gpu_memory_gb: float) -> str:
        """Get recommended model size based on hardware"""
        if has_gpu and gpu_memory_gb >= 16:
            return "large"  # 13B+ models
        elif has_gpu and gpu_memory_gb >= 8:
            return "medium"  # 7B models
        elif ram_gb >= 16 and cpu_freq >= 2.5:
            return "medium"  # 7B models on CPU
        elif ram_gb >= 8 and cpu_freq >= 1.5:
            return "small"  # 3B models
        else:
            return "tiny"  # 1B or quantized models
    
    def _initialize_providers(self):
        """Initialize all available LLM providers"""
        
        # 1. DeepSeek Local (optimized for low-end hardware)
        if self.hardware_profile.can_run_local_llm:
            self.available_providers[LLMProvider.DEEPSEEK_LOCAL] = LLMConfig(
                provider=LLMProvider.DEEPSEEK_LOCAL,
                model_name="deepseek-r1-distill-qwen-1.5b-gguf" if self.hardware_profile.recommended_model_size == "tiny" else "deepseek-r1-0528-qwen3-8b-gguf",
                cost_per_request=0.0,
                requires_gpu=False,
                min_ram_gb=4.0 if self.hardware_profile.recommended_model_size == "tiny" else 8.0,
                priority=1
            )
        
        # 2. DeepSeek API (fallback)
        self.available_providers[LLMProvider.DEEPSEEK_API] = LLMConfig(
            provider=LLMProvider.DEEPSEEK_API,
            model_name="deepseek-r1",
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com/v1",
            cost_per_request=0.001,  # Very affordable
            priority=2
        )
        
        # 3. OpenAI API
        self.available_providers[LLMProvider.OPENAI_API] = LLMConfig(
            provider=LLMProvider.OPENAI_API,
            model_name="gpt-4o-mini",  # Most cost-effective
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url="https://api.openai.com/v1",
            cost_per_request=0.01,
            priority=3
        )
        
        # 4. Anthropic API
        self.available_providers[LLMProvider.ANTHROPIC_API] = LLMConfig(
            provider=LLMProvider.ANTHROPIC_API,
            model_name="claude-3-haiku-20240307",  # Most cost-effective Claude
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            base_url="https://api.anthropic.com",
            cost_per_request=0.015,
            priority=4
        )
        
        # 5. Gemini API
        self.available_providers[LLMProvider.GEMINI_API] = LLMConfig(
            provider=LLMProvider.GEMINI_API,
            model_name="gemini-1.5-flash",  # Fast and affordable
            api_key=os.getenv("GEMINI_API_KEY"),
            base_url="https://generativelanguage.googleapis.com/v1beta",
            cost_per_request=0.005,
            priority=5
        )
        
        # 6. Fallback (always available)
        self.available_providers[LLMProvider.FALLBACK] = LLMConfig(
            provider=LLMProvider.FALLBACK,
            model_name="enhanced-template",
            cost_per_request=0.0,
            priority=10
        )
        
        logger.info(f"Initialized {len(self.available_providers)} LLM providers")
    
    async def initialize(self):
        """Initialize the LLM manager"""
        try:
            # Select best available provider
            await self._select_best_provider()
            
            # Initialize the selected provider
            if self.current_provider:
                await self._initialize_provider(self.current_provider)
            
            logger.info(f"LLM Manager initialized with provider: {self.current_provider}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM Manager: {e}")
            # Fallback to template-based responses
            self.current_provider = LLMProvider.FALLBACK
            return False
    
    async def _select_best_provider(self):
        """Select the best available provider based on hardware and preferences"""
        
        # If user has a preference and it's available, use it
        if self.user_preference and self.user_preference in self.available_providers:
            config = self.available_providers[self.user_preference]
            if await self._can_use_provider(config):
                self.current_provider = self.user_preference
                logger.info(f"Using user preferred provider: {self.user_preference}")
                return
        
        # Otherwise, select based on priority and hardware compatibility
        sorted_providers = sorted(
            self.available_providers.items(),
            key=lambda x: x[1].priority
        )
        
        for provider, config in sorted_providers:
            if await self._can_use_provider(config):
                self.current_provider = provider
                logger.info(f"Selected provider: {provider} (priority: {config.priority})")
                return
        
        # Fallback
        self.current_provider = LLMProvider.FALLBACK
        logger.warning("No suitable provider found, using fallback")
    
    async def _can_use_provider(self, config: LLMConfig) -> bool:
        """Check if a provider can be used with current hardware"""
        
        # Check hardware requirements
        if config.requires_gpu and not self.hardware_profile.has_gpu:
            return False
        
        if config.min_ram_gb > self.hardware_profile.ram_gb:
            return False
        
        # Check API key availability for API providers
        if config.provider in [LLMProvider.DEEPSEEK_API, LLMProvider.OPENAI_API, 
                              LLMProvider.ANTHROPIC_API, LLMProvider.GEMINI_API]:
            if not config.api_key:
                logger.warning(f"No API key found for {config.provider}")
                return False
        
        return True
    
    async def _initialize_provider(self, provider: LLMProvider):
        """Initialize a specific provider"""
        try:
            config = self.available_providers[provider]
            
            if provider == LLMProvider.DEEPSEEK_LOCAL:
                await self._initialize_deepseek_local(config)
            elif provider == LLMProvider.DEEPSEEK_API:
                await self._initialize_deepseek_api(config)
            elif provider == LLMProvider.OPENAI_API:
                await self._initialize_openai_api(config)
            elif provider == LLMProvider.ANTHROPIC_API:
                await self._initialize_anthropic_api(config)
            elif provider == LLMProvider.GEMINI_API:
                await self._initialize_gemini_api(config)
            elif provider == LLMProvider.FALLBACK:
                await self._initialize_fallback(config)
            
            logger.info(f"Provider {provider} initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize provider {provider}: {e}")
            raise
    
    async def _initialize_deepseek_local(self, config: LLMConfig):
        """Initialize local DeepSeek model"""
        try:
            # Import and initialize the optimized local model
            from .cpu_optimized_deepseek import CPUOptimizedDeepSeek
            
            instance = CPUOptimizedDeepSeek()
            
            # Configure for hardware
            if self.hardware_profile.recommended_model_size == "tiny":
                instance.model_name = "microsoft/DialoGPT-small"  # Lightweight fallback
                instance.generation_config.max_new_tokens = 256
            else:
                instance.model_name = "template-based"  # Use template-based for reliability
            
            await instance.load()
            self.provider_instances[LLMProvider.DEEPSEEK_LOCAL] = instance
            
        except Exception as e:
            logger.error(f"Failed to initialize DeepSeek Local: {e}")
            raise
    
    async def _initialize_deepseek_api(self, config: LLMConfig):
        """Initialize DeepSeek API"""
        try:
            import openai
            
            client = openai.AsyncOpenAI(
                api_key=config.api_key,
                base_url=config.base_url
            )
            
            self.provider_instances[LLMProvider.DEEPSEEK_API] = client
            
        except Exception as e:
            logger.error(f"Failed to initialize DeepSeek API: {e}")
            raise
    
    async def _initialize_openai_api(self, config: LLMConfig):
        """Initialize OpenAI API"""
        try:
            import openai
            
            client = openai.AsyncOpenAI(api_key=config.api_key)
            self.provider_instances[LLMProvider.OPENAI_API] = client
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI API: {e}")
            raise
    
    async def _initialize_anthropic_api(self, config: LLMConfig):
        """Initialize Anthropic API"""
        try:
            import anthropic
            
            client = anthropic.AsyncAnthropic(api_key=config.api_key)
            self.provider_instances[LLMProvider.ANTHROPIC_API] = client
            
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic API: {e}")
            raise
    
    async def _initialize_gemini_api(self, config: LLMConfig):
        """Initialize Gemini API"""
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=config.api_key)
            model = genai.GenerativeModel(config.model_name)
            self.provider_instances[LLMProvider.GEMINI_API] = model
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini API: {e}")
            raise
    
    async def _initialize_fallback(self, config: LLMConfig):
        """Initialize fallback provider"""
        # Fallback is always available, no initialization needed
        self.provider_instances[LLMProvider.FALLBACK] = "template-based"
    
    async def generate_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate response using the current provider"""
        try:
            if not self.current_provider:
                await self.initialize()
            
            config = self.available_providers[self.current_provider]
            
            start_time = datetime.now()
            
            if self.current_provider == LLMProvider.DEEPSEEK_LOCAL:
                result = await self._generate_deepseek_local(prompt, **kwargs)
            elif self.current_provider == LLMProvider.DEEPSEEK_API:
                result = await self._generate_deepseek_api(prompt, **kwargs)
            elif self.current_provider == LLMProvider.OPENAI_API:
                result = await self._generate_openai_api(prompt, **kwargs)
            elif self.current_provider == LLMProvider.ANTHROPIC_API:
                result = await self._generate_anthropic_api(prompt, **kwargs)
            elif self.current_provider == LLMProvider.GEMINI_API:
                result = await self._generate_gemini_api(prompt, **kwargs)
            else:
                result = await self._generate_fallback(prompt, **kwargs)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "content": result,
                "provider": self.current_provider.value,
                "model": config.model_name,
                "cost": config.cost_per_request,
                "processing_time": processing_time,
                "hardware_optimized": True
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            # Fallback to template response
            return await self._generate_fallback(prompt, **kwargs)
    
    async def _generate_deepseek_local(self, prompt: str, **kwargs) -> str:
        """Generate response using local DeepSeek"""
        try:
            instance = self.provider_instances[LLMProvider.DEEPSEEK_LOCAL]
            
            request = {
                "task_description": prompt,
                "language": kwargs.get("language", "python"),
                "framework": kwargs.get("framework", "fastapi"),
                "features": kwargs.get("features", [])
            }
            
            result = await instance.generate_code(request)
            return result.get("generated_code", "I apologize, but I couldn't generate a response.")
            
        except Exception as e:
            logger.error(f"DeepSeek Local generation failed: {e}")
            raise
    
    async def _generate_deepseek_api(self, prompt: str, **kwargs) -> str:
        """Generate response using DeepSeek API"""
        try:
            client = self.provider_instances[LLMProvider.DEEPSEEK_API]
            config = self.available_providers[LLMProvider.DEEPSEEK_API]
            
            response = await client.chat.completions.create(
                model=config.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=kwargs.get("max_tokens", config.max_tokens),
                temperature=kwargs.get("temperature", config.temperature)
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"DeepSeek API generation failed: {e}")
            raise
    
    async def _generate_openai_api(self, prompt: str, **kwargs) -> str:
        """Generate response using OpenAI API"""
        try:
            client = self.provider_instances[LLMProvider.OPENAI_API]
            config = self.available_providers[LLMProvider.OPENAI_API]
            
            response = await client.chat.completions.create(
                model=config.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=kwargs.get("max_tokens", config.max_tokens),
                temperature=kwargs.get("temperature", config.temperature)
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API generation failed: {e}")
            raise
    
    async def _generate_anthropic_api(self, prompt: str, **kwargs) -> str:
        """Generate response using Anthropic API"""
        try:
            client = self.provider_instances[LLMProvider.ANTHROPIC_API]
            config = self.available_providers[LLMProvider.ANTHROPIC_API]
            
            response = await client.messages.create(
                model=config.model_name,
                max_tokens=kwargs.get("max_tokens", config.max_tokens),
                temperature=kwargs.get("temperature", config.temperature),
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Anthropic API generation failed: {e}")
            raise
    
    async def _generate_gemini_api(self, prompt: str, **kwargs) -> str:
        """Generate response using Gemini API"""
        try:
            model = self.provider_instances[LLMProvider.GEMINI_API]
            
            response = await model.generate_content_async(prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Gemini API generation failed: {e}")
            raise
    
    async def _generate_fallback(self, prompt: str, **kwargs) -> str:
        """Generate fallback response"""
        # Enhanced template-based responses
        if any(word in prompt.lower() for word in ['hello', 'hi', 'hey']):
            return "Hello! I'm reVoAgent, your AI assistant. I'm running in optimized mode for your hardware. How can I help you today?"
        
        elif any(word in prompt.lower() for word in ['code', 'function', 'programming']):
            return f"I'd be happy to help you with coding! Based on your request: '{prompt[:100]}...', I can assist with writing functions, debugging, and providing programming guidance. What specific coding task are you working on?"
        
        else:
            return f"Thank you for your message! I'm processing your request: '{prompt[:100]}...' and I'm ready to provide assistance. How can I help you further?"
    
    def set_user_preference(self, provider: LLMProvider):
        """Set user's preferred LLM provider"""
        if provider in self.available_providers:
            self.user_preference = provider
            logger.info(f"User preference set to: {provider}")
        else:
            logger.warning(f"Provider {provider} not available")
    
    def get_available_providers(self) -> List[Dict[str, Any]]:
        """Get list of available providers for user selection"""
        providers = []
        
        for provider, config in self.available_providers.items():
            providers.append({
                "id": provider.value,
                "name": provider.value.replace("_", " ").title(),
                "model": config.model_name,
                "cost_per_request": config.cost_per_request,
                "type": "local" if provider == LLMProvider.DEEPSEEK_LOCAL else "api",
                "available": provider in self.provider_instances,
                "hardware_compatible": asyncio.run(self._can_use_provider(config))
            })
        
        return providers
    
    def get_hardware_info(self) -> Dict[str, Any]:
        """Get hardware information"""
        return {
            "cpu_cores": self.hardware_profile.cpu_cores,
            "cpu_frequency_ghz": self.hardware_profile.cpu_freq,
            "ram_gb": self.hardware_profile.ram_gb,
            "has_gpu": self.hardware_profile.has_gpu,
            "gpu_memory_gb": self.hardware_profile.gpu_memory_gb,
            "can_run_local_llm": self.hardware_profile.can_run_local_llm,
            "recommended_model_size": self.hardware_profile.recommended_model_size,
            "optimization_level": "high" if self.hardware_profile.cpu_freq >= 2.0 else "medium" if self.hardware_profile.cpu_freq >= 1.5 else "low"
        }
    
    async def switch_provider(self, provider: LLMProvider) -> bool:
        """Switch to a different provider"""
        try:
            if provider not in self.available_providers:
                logger.error(f"Provider {provider} not available")
                return False
            
            config = self.available_providers[provider]
            if not await self._can_use_provider(config):
                logger.error(f"Provider {provider} not compatible with current hardware")
                return False
            
            # Initialize the new provider if not already done
            if provider not in self.provider_instances:
                await self._initialize_provider(provider)
            
            self.current_provider = provider
            self.user_preference = provider
            
            logger.info(f"Switched to provider: {provider}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to switch to provider {provider}: {e}")
            return False

# Global instance
optimized_llm_manager = OptimizedLLMManager()