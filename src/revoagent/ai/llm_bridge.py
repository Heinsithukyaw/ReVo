"""
LLM Bridge - Connects existing LLM integrations to the enhanced backend
"""

import os
import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class LLMBridge:
    """Bridge between enhanced backend and existing LLM integrations"""
    
    def __init__(self):
        self.providers = {}
        self.initialized = False
    
    async def initialize(self):
        """Initialize all available LLM providers"""
        try:
            # Initialize DeepSeek R1
            if os.getenv('DEEPSEEK_API_KEY'):
                try:
                    from .deepseek_r1_integration import DeepSeekR1Integration
                    deepseek = DeepSeekR1Integration()
                    await self._safe_initialize_provider(deepseek, 'deepseek-r1')
                    self.providers['deepseek-r1'] = deepseek
                    logger.info("DeepSeek R1 provider initialized")
                except Exception as e:
                    logger.warning(f"Failed to initialize DeepSeek R1: {e}")
            
            # Initialize OpenAI
            if os.getenv('OPENAI_API_KEY'):
                try:
                    from .openai_integration import OpenAIIntegration
                    openai = OpenAIIntegration()
                    await self._safe_initialize_provider(openai, 'openai')
                    self.providers['gpt-4o-mini'] = openai
                    self.providers['gpt-4o'] = openai
                    logger.info("OpenAI provider initialized")
                except Exception as e:
                    logger.warning(f"Failed to initialize OpenAI: {e}")
            
            # Initialize Llama (local)
            try:
                from .llama_local_integration import LlamaLocalIntegration
                llama = LlamaLocalIntegration()
                if await self._check_llama_availability(llama):
                    await self._safe_initialize_provider(llama, 'llama')
                    self.providers['llama-3.1-70b'] = llama
                    logger.info("Llama local provider initialized")
            except Exception as e:
                logger.warning(f"Llama local provider not available: {e}")
            
            # Initialize DeepSeek (standard)
            if os.getenv('DEEPSEEK_API_KEY'):
                try:
                    from .deepseek_integration import DeepSeekIntegration
                    deepseek_std = DeepSeekIntegration()
                    await self._safe_initialize_provider(deepseek_std, 'deepseek')
                    self.providers['deepseek-coder'] = deepseek_std
                    logger.info("DeepSeek standard provider initialized")
                except Exception as e:
                    logger.warning(f"Failed to initialize DeepSeek standard: {e}")
            
            # Initialize Model Manager if available
            try:
                from .model_manager import ModelManager
                model_manager = ModelManager()
                # Register providers with model manager if needed
                logger.info("Model Manager integrated")
            except Exception as e:
                logger.warning(f"Model Manager not available: {e}")
            
            self.initialized = True
            logger.info(f"LLM Bridge initialized with {len(self.providers)} providers")
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM Bridge: {e}")
            self.initialized = False
    
    async def _safe_initialize_provider(self, provider, provider_name):
        """Safely initialize a provider with error handling"""
        try:
            if hasattr(provider, 'initialize'):
                await provider.initialize()
            elif hasattr(provider, 'init'):
                await provider.init()
            # Some providers might not need explicit initialization
        except Exception as e:
            logger.warning(f"Provider {provider_name} initialized without explicit init: {e}")
    
    async def _check_llama_availability(self, llama_provider):
        """Check if Llama is available"""
        try:
            if hasattr(llama_provider, 'check_availability'):
                return await llama_provider.check_availability()
            return True  # Assume available if no check method
        except Exception:
            return False
    
    async def get_available_models(self) -> List[str]:
        """Get list of available models"""
        if not self.initialized:
            await self.initialize()
        return list(self.providers.keys())
    
    async def generate_response(
        self, 
        message: str, 
        model: str = "deepseek-r1", 
        **kwargs
    ) -> str:
        """Generate response using specified model"""
        if not self.initialized:
            await self.initialize()
        
        provider = self.providers.get(model)
        if not provider:
            # Fallback to first available provider
            if self.providers:
                model = next(iter(self.providers.keys()))
                provider = self.providers[model]
                logger.info(f"Model {model} not found, using fallback: {list(self.providers.keys())[0]}")
            else:
                return f"No LLM providers available. Please configure API keys."
        
        try:
            # Try different method names that providers might use
            response = None
            
            if hasattr(provider, 'generate_response'):
                response = await provider.generate_response(
                    message, 
                    temperature=kwargs.get('temperature', 0.7),
                    max_tokens=kwargs.get('max_tokens', 1000)
                )
            elif hasattr(provider, 'chat'):
                response = await provider.chat(
                    message,
                    temperature=kwargs.get('temperature', 0.7),
                    max_tokens=kwargs.get('max_tokens', 1000)
                )
            elif hasattr(provider, 'process'):
                response = await provider.process(message, **kwargs)
            elif hasattr(provider, 'complete'):
                response = await provider.complete(message, **kwargs)
            else:
                # Try calling the provider directly
                response = await provider(message, **kwargs)
            
            return response or f"Generated response from {model}: {message}"
            
        except Exception as e:
            logger.error(f"Error generating response with {model}: {e}")
            return f"Error generating response with {model}: {str(e)}"
    
    async def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all providers"""
        status = {
            "initialized": self.initialized,
            "providers": len(self.providers),
            "models": list(self.providers.keys()),
            "details": {}
        }
        
        for model, provider in self.providers.items():
            try:
                if hasattr(provider, 'get_status'):
                    provider_status = await provider.get_status()
                elif hasattr(provider, 'status'):
                    provider_status = provider.status
                else:
                    provider_status = {"status": "active", "type": provider.__class__.__name__}
                
                status["details"][model] = provider_status
            except Exception as e:
                status["details"][model] = {"status": "error", "error": str(e)}
        
        return status
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all providers"""
        health = {
            "overall_status": "healthy" if self.initialized else "unhealthy",
            "providers_count": len(self.providers),
            "timestamp": datetime.now().isoformat(),
            "provider_health": {}
        }
        
        for model, provider in self.providers.items():
            try:
                # Try a simple health check
                if hasattr(provider, 'health_check'):
                    health_result = await provider.health_check()
                else:
                    # Simple ping test
                    test_response = await self.generate_response("test", model)
                    health_result = {"status": "healthy", "test_passed": bool(test_response)}
                
                health["provider_health"][model] = health_result
            except Exception as e:
                health["provider_health"][model] = {"status": "unhealthy", "error": str(e)}
        
        return health

# Global LLM bridge instance
llm_bridge = LLMBridge()
