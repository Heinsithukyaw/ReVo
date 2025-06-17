#!/usr/bin/env python3
"""
API Providers for reVoAgent
Handles DeepSeek API, OpenAI, Anthropic, and Gemini integrations
"""

import asyncio
import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class DeepSeekAPIProvider:
    """DeepSeek API Provider - Most cost-effective option"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.base_url = "https://api.deepseek.com/v1"
        self.model = "deepseek-r1"
        self.cost_per_1k_tokens = 0.0014  # Very affordable
        
    async def generate_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate response using DeepSeek API"""
        try:
            if not self.api_key:
                raise Exception("DeepSeek API key not provided")
            
            import openai
            
            client = openai.AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            
            response = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=kwargs.get("max_tokens", 2048),
                temperature=kwargs.get("temperature", 0.7),
                top_p=kwargs.get("top_p", 0.9)
            )
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            cost = (tokens_used / 1000) * self.cost_per_1k_tokens
            
            return {
                "content": content,
                "model": f"DeepSeek R1 (API)",
                "tokens_used": tokens_used,
                "cost": cost,
                "provider": "deepseek_api",
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"DeepSeek API error: {e}")
            raise

class OpenAIProvider:
    """OpenAI API Provider"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = "gpt-4o-mini"  # Most cost-effective GPT-4 model
        self.cost_per_1k_tokens = 0.015  # Input tokens
        
    async def generate_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate response using OpenAI API"""
        try:
            if not self.api_key:
                raise Exception("OpenAI API key not provided")
            
            import openai
            
            client = openai.AsyncOpenAI(api_key=self.api_key)
            
            response = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=kwargs.get("max_tokens", 2048),
                temperature=kwargs.get("temperature", 0.7),
                top_p=kwargs.get("top_p", 0.9)
            )
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            cost = (tokens_used / 1000) * self.cost_per_1k_tokens
            
            return {
                "content": content,
                "model": f"GPT-4o Mini (API)",
                "tokens_used": tokens_used,
                "cost": cost,
                "provider": "openai_api",
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

class AnthropicProvider:
    """Anthropic Claude API Provider"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = "claude-3-haiku-20240307"  # Most cost-effective Claude
        self.cost_per_1k_tokens = 0.0125  # Input tokens
        
    async def generate_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate response using Anthropic API"""
        try:
            if not self.api_key:
                raise Exception("Anthropic API key not provided")
            
            try:
                import anthropic
            except ImportError:
                # Try to install anthropic if not available
                import subprocess
                import sys
                subprocess.check_call([sys.executable, "-m", "pip", "install", "anthropic"])
                import anthropic
            
            client = anthropic.AsyncAnthropic(api_key=self.api_key)
            
            response = await client.messages.create(
                model=self.model,
                max_tokens=kwargs.get("max_tokens", 2048),
                temperature=kwargs.get("temperature", 0.7),
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            cost = (tokens_used / 1000) * self.cost_per_1k_tokens
            
            return {
                "content": content,
                "model": f"Claude 3 Haiku (API)",
                "tokens_used": tokens_used,
                "cost": cost,
                "provider": "anthropic_api",
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise

class GeminiProvider:
    """Google Gemini API Provider"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = "gemini-1.5-flash"  # Fast and affordable
        self.cost_per_1k_tokens = 0.0075  # Very competitive pricing
        
    async def generate_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate response using Gemini API"""
        try:
            if not self.api_key:
                raise Exception("Gemini API key not provided")
            
            try:
                import google.generativeai as genai
            except ImportError:
                # Try to install google-generativeai if not available
                import subprocess
                import sys
                subprocess.check_call([sys.executable, "-m", "pip", "install", "google-generativeai"])
                import google.generativeai as genai
            
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(self.model)
            
            # Configure generation parameters
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=kwargs.get("max_tokens", 2048),
                temperature=kwargs.get("temperature", 0.7),
                top_p=kwargs.get("top_p", 0.9)
            )
            
            # Use sync method and run in thread for async compatibility
            def _generate():
                return model.generate_content(
                    prompt,
                    generation_config=generation_config
                )
            
            response = await asyncio.to_thread(_generate)
            
            content = response.text
            # Estimate tokens (Gemini doesn't always provide exact count)
            tokens_used = len(prompt.split()) + len(content.split())
            cost = (tokens_used / 1000) * self.cost_per_1k_tokens
            
            return {
                "content": content,
                "model": f"Gemini 1.5 Flash (API)",
                "tokens_used": tokens_used,
                "cost": cost,
                "provider": "gemini_api",
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise

class APIProviderManager:
    """Manages all API providers with intelligent fallback"""
    
    def __init__(self):
        self.providers = {
            "deepseek_api": DeepSeekAPIProvider(),
            "openai_api": OpenAIProvider(),
            "anthropic_api": AnthropicProvider(),
            "gemini_api": GeminiProvider()
        }
        
        self.provider_priority = [
            "deepseek_api",    # Most cost-effective
            "gemini_api",      # Good balance of cost and quality
            "openai_api",      # High quality, higher cost
            "anthropic_api"    # Premium option
        ]
        
        self.current_provider = None
        self.fallback_enabled = True
        
    async def initialize(self) -> bool:
        """Initialize the API provider manager"""
        try:
            # Test providers in priority order
            for provider_name in self.provider_priority:
                if await self._test_provider(provider_name):
                    self.current_provider = provider_name
                    logger.info(f"Initialized with provider: {provider_name}")
                    return True
            
            logger.warning("No API providers available")
            return False
            
        except Exception as e:
            logger.error(f"Failed to initialize API providers: {e}")
            return False
    
    async def _test_provider(self, provider_name: str) -> bool:
        """Test if a provider is available and working"""
        try:
            provider = self.providers[provider_name]
            
            # Check if API key is available
            if not provider.api_key:
                logger.debug(f"No API key for {provider_name}")
                return False
            
            # Quick test with minimal prompt
            test_response = await provider.generate_response(
                "Hello", 
                max_tokens=10
            )
            
            if test_response.get("status") == "success":
                logger.info(f"✅ {provider_name} is working")
                return True
            else:
                logger.warning(f"❌ {provider_name} test failed")
                return False
                
        except Exception as e:
            logger.debug(f"Provider {provider_name} test failed: {e}")
            return False
    
    async def generate_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate response with automatic fallback"""
        
        # Try current provider first
        if self.current_provider:
            try:
                provider = self.providers[self.current_provider]
                result = await provider.generate_response(prompt, **kwargs)
                logger.info(f"Response generated with {self.current_provider}")
                return result
                
            except Exception as e:
                logger.warning(f"Current provider {self.current_provider} failed: {e}")
                
                # Try fallback if enabled
                if self.fallback_enabled:
                    return await self._try_fallback_providers(prompt, **kwargs)
                else:
                    raise
        
        # No current provider, try all in priority order
        return await self._try_fallback_providers(prompt, **kwargs)
    
    async def _try_fallback_providers(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Try fallback providers in priority order"""
        
        for provider_name in self.provider_priority:
            if provider_name == self.current_provider:
                continue  # Skip the one that just failed
                
            try:
                provider = self.providers[provider_name]
                
                if not provider.api_key:
                    continue
                
                result = await provider.generate_response(prompt, **kwargs)
                
                # Update current provider to the working one
                self.current_provider = provider_name
                logger.info(f"Switched to fallback provider: {provider_name}")
                
                return result
                
            except Exception as e:
                logger.debug(f"Fallback provider {provider_name} failed: {e}")
                continue
        
        # All providers failed
        raise Exception("All API providers failed")
    
    def set_provider(self, provider_name: str) -> bool:
        """Manually set the current provider"""
        if provider_name in self.providers:
            self.current_provider = provider_name
            logger.info(f"Provider manually set to: {provider_name}")
            return True
        else:
            logger.error(f"Provider {provider_name} not available")
            return False
    
    def get_available_providers(self) -> List[Dict[str, Any]]:
        """Get list of available providers"""
        providers_info = []
        
        for name, provider in self.providers.items():
            providers_info.append({
                "name": name,
                "display_name": name.replace("_", " ").title(),
                "model": provider.model,
                "cost_per_1k_tokens": provider.cost_per_1k_tokens,
                "has_api_key": bool(provider.api_key),
                "is_current": name == self.current_provider
            })
        
        return providers_info
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get current provider status"""
        return {
            "current_provider": self.current_provider,
            "fallback_enabled": self.fallback_enabled,
            "total_providers": len(self.providers),
            "available_providers": len([p for p in self.providers.values() if p.api_key]),
            "provider_priority": self.provider_priority
        }
    
    def set_api_key(self, provider_name: str, api_key: str) -> bool:
        """Set API key for a specific provider"""
        if provider_name in self.providers:
            self.providers[provider_name].api_key = api_key
            logger.info(f"API key set for {provider_name}")
            return True
        else:
            logger.error(f"Provider {provider_name} not found")
            return False

# Global instance
api_provider_manager = APIProviderManager()