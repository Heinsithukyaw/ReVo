#!/usr/bin/env python3
"""
API LLM Manager for reVoAgent
Simplified version focusing on API providers (Option B)
"""

import asyncio
import logging
import os
import time
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import json

# Import API providers
from .api_providers import (
    APIProviderManager, 
    DeepSeekAPIProvider, 
    AnthropicProvider, 
    GeminiProvider, 
    OpenAIProvider
)

logger = logging.getLogger("api_llm_manager")

class ModelType(Enum):
    API_DEEPSEEK = "api_deepseek"
    API_CLAUDE = "api_claude"
    API_GEMINI = "api_gemini"
    API_OPENAI = "api_openai"

@dataclass
class LLMResponse:
    """Standardized LLM response format"""
    content: str
    model: str
    model_type: ModelType
    tokens_used: int
    cost: float
    response_time: float
    confidence: float
    provider: str
    timestamp: float
    metadata: Dict[str, Any]

@dataclass
class ModelConfig:
    """Configuration for each model"""
    model_type: ModelType
    enabled: bool
    priority: int
    cost_per_1k_tokens: float
    max_tokens: int
    temperature: float
    top_p: float
    api_key: Optional[str] = None

class APILLMManager:
    """
    API LLM Manager for real API integrations
    
    Features:
    - Real API integrations (Claude, Gemini, DeepSeek, OpenAI)
    - Intelligent fallback system
    - Cost optimization
    - Performance monitoring
    - Automatic model switching
    """
    
    def __init__(self):
        self.models = {}
        self.current_model = None
        self.fallback_enabled = True
        self.cost_optimization = True
        self.performance_monitoring = True
        
        # Performance metrics
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_cost": 0.0,
            "total_tokens": 0,
            "average_response_time": 0.0,
            "model_usage": {},
            "cost_savings": 0.0
        }
        
        # Model configurations
        self.model_configs = self._get_default_configs()
        
        # Initialize API manager
        self.api_manager = APIProviderManager()
        
        # Model priority (cost-optimized)
        self.model_priority = [
            ModelType.API_DEEPSEEK,    # Cheapest API
            ModelType.API_GEMINI,      # Good balance
            ModelType.API_CLAUDE,      # High quality
            ModelType.API_OPENAI       # Premium option
        ]
    
    def _get_default_configs(self) -> Dict[ModelType, ModelConfig]:
        """Get default model configurations"""
        return {
            ModelType.API_DEEPSEEK: ModelConfig(
                model_type=ModelType.API_DEEPSEEK,
                enabled=True,
                priority=1,
                cost_per_1k_tokens=0.0014,  # Very cheap
                max_tokens=2048,
                temperature=0.7,
                top_p=0.9
            ),
            ModelType.API_GEMINI: ModelConfig(
                model_type=ModelType.API_GEMINI,
                enabled=True,
                priority=2,
                cost_per_1k_tokens=0.0075,  # Good balance
                max_tokens=2048,
                temperature=0.7,
                top_p=0.9,
                api_key=os.getenv("GEMINI_API_KEY")  # Provided key
            ),
            ModelType.API_CLAUDE: ModelConfig(
                model_type=ModelType.API_CLAUDE,
                enabled=True,
                priority=3,
                cost_per_1k_tokens=0.0125,  # High quality
                max_tokens=2048,
                temperature=0.7,
                top_p=0.9,
                api_key=os.getenv("ANTHROPIC_API_KEY")  # Provided key
            ),
            ModelType.API_OPENAI: ModelConfig(
                model_type=ModelType.API_OPENAI,
                enabled=False,  # Disabled by default (no key provided)
                priority=4,
                cost_per_1k_tokens=0.015,  # Most expensive
                max_tokens=2048,
                temperature=0.7,
                top_p=0.9
            )
        }
    
    async def initialize(self) -> bool:
        """Initialize the API LLM Manager"""
        try:
            logger.info("🚀 Initializing API LLM Manager...")
            
            # Set API keys from configuration
            await self._configure_api_keys()
            
            # Initialize API providers
            logger.info("🌐 Initializing API providers...")
            api_success = await self._initialize_api_providers()
            
            # Determine current model based on priority and availability
            await self._select_optimal_model()
            
            if api_success:
                logger.info("✅ API LLM Manager initialized successfully!")
                logger.info(f"🎯 Current model: {self.current_model}")
                logger.info(f"💰 Cost optimization: {'Enabled' if self.cost_optimization else 'Disabled'}")
                logger.info(f"🔄 Fallback system: {'Enabled' if self.fallback_enabled else 'Disabled'}")
            else:
                logger.error("❌ Failed to initialize any API models")
            
            return api_success
            
        except Exception as e:
            logger.error(f"Failed to initialize API LLM Manager: {e}")
            return False
    
    async def _configure_api_keys(self) -> None:
        """Configure API keys for providers"""
        try:
            # Set provided API keys
            claude_key = self.model_configs[ModelType.API_CLAUDE].api_key
            gemini_key = self.model_configs[ModelType.API_GEMINI].api_key
            
            if claude_key:
                os.environ["ANTHROPIC_API_KEY"] = claude_key
                self.api_manager.set_api_key("anthropic_api", claude_key)
                logger.info("🔑 Claude API key configured")
            
            if gemini_key:
                os.environ["GEMINI_API_KEY"] = gemini_key
                self.api_manager.set_api_key("gemini_api", gemini_key)
                logger.info("🔑 Gemini API key configured")
            
            # Check for DeepSeek API key (free from open sources)
            deepseek_key = os.getenv("DEEPSEEK_API_KEY")
            if deepseek_key:
                self.api_manager.set_api_key("deepseek_api", deepseek_key)
                logger.info("🔑 DeepSeek API key configured")
            else:
                logger.info("💡 DeepSeek API key not found - will skip DeepSeek API")
            
            # Check for OpenAI key
            openai_key = os.getenv("OPENAI_API_KEY")
            if openai_key:
                self.api_manager.set_api_key("openai_api", openai_key)
                self.model_configs[ModelType.API_OPENAI].enabled = True
                logger.info("🔑 OpenAI API key configured")
            
        except Exception as e:
            logger.warning(f"Error configuring API keys: {e}")
    
    async def _initialize_api_providers(self) -> bool:
        """Initialize API providers"""
        try:
            success = await self.api_manager.initialize()
            
            if success:
                # Map API providers to our model types
                provider_mapping = {
                    "deepseek_api": ModelType.API_DEEPSEEK,
                    "anthropic_api": ModelType.API_CLAUDE,
                    "gemini_api": ModelType.API_GEMINI,
                    "openai_api": ModelType.API_OPENAI
                }
                
                for provider_name, model_type in provider_mapping.items():
                    if provider_name in self.api_manager.providers:
                        provider = self.api_manager.providers[provider_name]
                        if provider.api_key:
                            self.models[model_type] = provider
                            logger.info(f"✅ {model_type.value} API ready")
                
                return len(self.models) > 0
            else:
                logger.warning("⚠️ No API providers initialized")
                return False
                
        except Exception as e:
            logger.error(f"API providers initialization error: {e}")
            return False
    
    async def _select_optimal_model(self) -> None:
        """Select the optimal model based on priority and availability"""
        try:
            for model_type in self.model_priority:
                config = self.model_configs.get(model_type)
                if config and config.enabled and model_type in self.models:
                    self.current_model = model_type
                    logger.info(f"🎯 Selected optimal model: {model_type.value}")
                    return
            
            # Fallback to any available model
            if self.models:
                self.current_model = list(self.models.keys())[0]
                logger.warning(f"⚠️ Using fallback model: {self.current_model.value}")
            else:
                logger.error("❌ No models available")
                
        except Exception as e:
            logger.error(f"Model selection error: {e}")
    
    async def generate_response(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate response using the optimal available model"""
        start_time = time.time()
        
        try:
            # Update metrics
            self.metrics["total_requests"] += 1
            
            # Try current model first
            if self.current_model and self.current_model in self.models:
                try:
                    response = await self._generate_with_model(
                        self.current_model, prompt, **kwargs
                    )
                    
                    # Update success metrics
                    self.metrics["successful_requests"] += 1
                    self.metrics["total_cost"] += response.cost
                    self.metrics["total_tokens"] += response.tokens_used
                    self._update_model_usage(self.current_model)
                    
                    return response
                    
                except Exception as e:
                    logger.warning(f"Current model {self.current_model.value} failed: {e}")
                    
                    # Try fallback if enabled
                    if self.fallback_enabled:
                        return await self._try_fallback_models(prompt, **kwargs)
                    else:
                        raise
            
            # No current model, try fallback
            return await self._try_fallback_models(prompt, **kwargs)
            
        except Exception as e:
            # Update failure metrics
            self.metrics["failed_requests"] += 1
            logger.error(f"All models failed: {e}")
            
            # Return error response
            return self._create_error_response(prompt, str(e), time.time() - start_time)
    
    async def _generate_with_model(self, model_type: ModelType, prompt: str, **kwargs) -> LLMResponse:
        """Generate response with a specific model"""
        start_time = time.time()
        
        try:
            config = self.model_configs[model_type]
            model = self.models[model_type]
            
            # Prepare generation parameters
            generation_params = {
                "max_tokens": kwargs.get("max_tokens", config.max_tokens),
                "temperature": kwargs.get("temperature", config.temperature),
                "top_p": kwargs.get("top_p", config.top_p)
            }
            
            # Generate using API model
            result = await model.generate_response(prompt, **generation_params)
            
            return LLMResponse(
                content=result["content"],
                model=result["model"],
                model_type=model_type,
                tokens_used=result["tokens_used"],
                cost=result["cost"],
                response_time=time.time() - start_time,
                confidence=90.0,
                provider=result["provider"],
                timestamp=time.time(),
                metadata=result
            )
                
        except Exception as e:
            logger.error(f"Model {model_type.value} generation failed: {e}")
            raise
    
    async def _try_fallback_models(self, prompt: str, **kwargs) -> LLMResponse:
        """Try fallback models in priority order"""
        
        for model_type in self.model_priority:
            if model_type == self.current_model:
                continue  # Skip the one that just failed
            
            if model_type not in self.models:
                continue
            
            config = self.model_configs.get(model_type)
            if not config or not config.enabled:
                continue
            
            try:
                logger.info(f"🔄 Trying fallback model: {model_type.value}")
                response = await self._generate_with_model(model_type, prompt, **kwargs)
                
                # Update current model to the working one
                self.current_model = model_type
                logger.info(f"✅ Switched to fallback model: {model_type.value}")
                
                # Update metrics
                self.metrics["successful_requests"] += 1
                self.metrics["total_cost"] += response.cost
                self.metrics["total_tokens"] += response.tokens_used
                self._update_model_usage(model_type)
                
                return response
                
            except Exception as e:
                logger.debug(f"Fallback model {model_type.value} failed: {e}")
                continue
        
        # All models failed
        raise Exception("All models failed")
    
    def _create_error_response(self, prompt: str, error: str, response_time: float) -> LLMResponse:
        """Create error response when all models fail"""
        error_content = f"""🤖 reVoAgent AI Assistant (Error Recovery Mode)

I apologize, but I'm currently experiencing technical difficulties with all AI models.

Error: {error}

Your prompt: "{prompt[:100]}..."

I'm working to restore full functionality. Please try again in a moment, or contact support if the issue persists.

Available models: {', '.join([m.value for m in self.models.keys()])}
Current model: {self.current_model.value if self.current_model else 'None'}"""

        return LLMResponse(
            content=error_content,
            model="error-recovery",
            model_type=ModelType.API_GEMINI,  # Default
            tokens_used=len(error_content.split()),
            cost=0.0,
            response_time=response_time,
            confidence=0.0,
            provider="error_recovery",
            timestamp=time.time(),
            metadata={"error": error, "prompt": prompt}
        )
    
    def _update_model_usage(self, model_type: ModelType) -> None:
        """Update model usage statistics"""
        model_name = model_type.value
        if model_name not in self.metrics["model_usage"]:
            self.metrics["model_usage"][model_name] = 0
        self.metrics["model_usage"][model_name] += 1
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status of the LLM manager"""
        return {
            "current_model": self.current_model.value if self.current_model else None,
            "available_models": [m.value for m in self.models.keys()],
            "total_models": len(self.models),
            "fallback_enabled": self.fallback_enabled,
            "cost_optimization": self.cost_optimization,
            "performance_monitoring": self.performance_monitoring,
            "metrics": self.metrics,
            "model_configs": {
                m.value: {
                    "enabled": config.enabled,
                    "priority": config.priority,
                    "cost_per_1k_tokens": config.cost_per_1k_tokens,
                    "has_api_key": bool(config.api_key)
                }
                for m, config in self.model_configs.items()
            },
            "api_provider_status": self.api_manager.get_provider_status() if hasattr(self, 'api_manager') else None
        }
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models with details"""
        models_info = []
        
        for model_type, config in self.model_configs.items():
            is_available = model_type in self.models
            is_current = model_type == self.current_model
            
            model_info = {
                "id": model_type.value,
                "name": self._get_model_display_name(model_type),
                "type": "api",
                "enabled": config.enabled,
                "available": is_available,
                "current": is_current,
                "priority": config.priority,
                "cost_per_1k_tokens": config.cost_per_1k_tokens,
                "cost_per_request": self._estimate_cost_per_request(config),
                "max_tokens": config.max_tokens,
                "has_api_key": bool(config.api_key),
                "status": "active" if is_available else "unavailable"
            }
            
            models_info.append(model_info)
        
        return sorted(models_info, key=lambda x: x["priority"])
    
    def _get_model_display_name(self, model_type: ModelType) -> str:
        """Get display name for model type"""
        names = {
            ModelType.API_DEEPSEEK: "DeepSeek R1 (API)",
            ModelType.API_CLAUDE: "Claude 3 Haiku (API)",
            ModelType.API_GEMINI: "Gemini 1.5 Flash (API)",
            ModelType.API_OPENAI: "GPT-4o Mini (API)"
        }
        return names.get(model_type, model_type.value)
    
    def _estimate_cost_per_request(self, config: ModelConfig) -> float:
        """Estimate cost per typical request"""
        # Assume average request is ~500 tokens
        avg_tokens = 500
        return (avg_tokens / 1000) * config.cost_per_1k_tokens
    
    async def set_current_model(self, model_type: Union[str, ModelType]) -> bool:
        """Manually set the current model"""
        try:
            if isinstance(model_type, str):
                model_type = ModelType(model_type)
            
            if model_type in self.models:
                self.current_model = model_type
                logger.info(f"🎯 Current model set to: {model_type.value}")
                return True
            else:
                logger.error(f"❌ Model {model_type.value} not available")
                return False
                
        except Exception as e:
            logger.error(f"Failed to set current model: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all models"""
        health_status = {
            "overall_status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "models": {}
        }
        
        for model_type in self.models:
            try:
                # Quick test generation
                test_prompt = "Hello"
                start_time = time.time()
                
                response = await self._generate_with_model(
                    model_type, test_prompt, max_tokens=10
                )
                
                response_time = time.time() - start_time
                
                health_status["models"][model_type.value] = {
                    "status": "healthy",
                    "response_time": response_time,
                    "test_successful": True
                }
                
            except Exception as e:
                health_status["models"][model_type.value] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "test_successful": False
                }
                health_status["overall_status"] = "degraded"
        
        return health_status

# Global instance
api_llm_manager = APILLMManager()

# Convenience functions
async def initialize_api_llm() -> bool:
    """Initialize the API LLM manager"""
    return await api_llm_manager.initialize()

async def generate_ai_response(prompt: str, **kwargs) -> LLMResponse:
    """Generate AI response using the API LLM manager"""
    return await api_llm_manager.generate_response(prompt, **kwargs)

def get_llm_status() -> Dict[str, Any]:
    """Get LLM manager status"""
    return api_llm_manager.get_status()

def get_available_models() -> List[Dict[str, Any]]:
    """Get available models"""
    return api_llm_manager.get_available_models()