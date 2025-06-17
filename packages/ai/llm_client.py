"""
Advanced LLM Client with Multi-Provider Fallback Support
Optimized for cost efficiency with DeepSeek R1 0528 as primary, Llama local, and cloud fallbacks
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import httpx
import openai
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Available LLM providers."""
    DEEPSEEK_LOCAL = "deepseek_local"
    LLAMA_LOCAL = "llama_local"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


@dataclass
class LLMConfig:
    """Configuration for LLM providers."""
    provider: LLMProvider
    endpoint: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    max_tokens: int = 4000
    temperature: float = 0.7
    timeout: int = 30
    enabled: bool = True
    cost_per_token: float = 0.0  # Cost optimization tracking


@dataclass
class LLMResponse:
    """Standardized LLM response."""
    content: str
    provider: LLMProvider
    model: str
    tokens_used: int
    response_time: float
    cost: float
    function_calls: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


class LLMClient:
    """
    Advanced LLM client with intelligent fallback and cost optimization.
    Primary: DeepSeek R1 0528 (local/opensource) - Cost: $0
    Secondary: Llama (local) - Cost: $0
    Fallback: OpenAI GPT-4 - Cost: Variable
    Emergency: Anthropic Claude - Cost: Variable
    """
    
    def __init__(self, configs: Dict[LLMProvider, LLMConfig]):
        self.configs = configs
        self.providers = self._initialize_providers()
        self.usage_stats = {provider: {"calls": 0, "tokens": 0, "cost": 0.0} for provider in LLMProvider}
        self.fallback_order = [
            LLMProvider.DEEPSEEK_LOCAL,
            LLMProvider.LLAMA_LOCAL,
            LLMProvider.OPENAI,
            LLMProvider.ANTHROPIC
        ]
        
        # Health tracking
        self.provider_health = {provider: {"available": True, "last_error": None, "error_count": 0} 
                               for provider in LLMProvider}
    
    def _initialize_providers(self) -> Dict[LLMProvider, Any]:
        """Initialize provider clients."""
        providers = {}
        
        # OpenAI client
        if LLMProvider.OPENAI in self.configs:
            config = self.configs[LLMProvider.OPENAI]
            if config.api_key:
                providers[LLMProvider.OPENAI] = openai.AsyncOpenAI(api_key=config.api_key)
        
        # Anthropic client
        if LLMProvider.ANTHROPIC in self.configs:
            config = self.configs[LLMProvider.ANTHROPIC]
            if config.api_key:
                providers[LLMProvider.ANTHROPIC] = Anthropic(api_key=config.api_key)
        
        # HTTP client for local providers
        providers["http_client"] = httpx.AsyncClient(timeout=30.0)
        
        return providers
    
    async def chat_completion(self, 
                            messages: List[Dict[str, str]], 
                            tools: Optional[List[Dict[str, Any]]] = None,
                            preferred_provider: Optional[LLMProvider] = None) -> LLMResponse:
        """
        Get chat completion with intelligent fallback.
        
        Args:
            messages: Chat messages in OpenAI format
            tools: Function calling tools schema
            preferred_provider: Override default fallback order
        
        Returns:
            LLMResponse with content and metadata
        """
        start_time = time.time()
        
        # Determine provider order
        provider_order = self.fallback_order.copy()
        if preferred_provider and preferred_provider in provider_order:
            provider_order.remove(preferred_provider)
            provider_order.insert(0, preferred_provider)
        
        last_error = None
        
        for provider in provider_order:
            if not self._is_provider_available(provider):
                continue
            
            try:
                logger.info(f"Attempting LLM call with {provider.value}")
                response = await self._call_provider(provider, messages, tools)
                
                # Update success stats
                self._update_provider_health(provider, success=True)
                self._update_usage_stats(provider, response)
                
                response.response_time = time.time() - start_time
                logger.info(f"LLM call successful with {provider.value} in {response.response_time:.2f}s")
                
                return response
                
            except Exception as e:
                last_error = str(e)
                logger.warning(f"LLM call failed with {provider.value}: {e}")
                self._update_provider_health(provider, success=False, error=str(e))
                continue
        
        # All providers failed
        error_response = LLMResponse(
            content="I'm experiencing technical difficulties. Please try again in a moment.",
            provider=LLMProvider.DEEPSEEK_LOCAL,
            model="error",
            tokens_used=0,
            response_time=time.time() - start_time,
            cost=0.0,
            error=f"All providers failed. Last error: {last_error}"
        )
        
        logger.error(f"All LLM providers failed. Last error: {last_error}")
        return error_response
    
    async def _call_provider(self, 
                           provider: LLMProvider, 
                           messages: List[Dict[str, str]], 
                           tools: Optional[List[Dict[str, Any]]] = None) -> LLMResponse:
        """Call specific LLM provider."""
        config = self.configs[provider]
        
        if provider == LLMProvider.DEEPSEEK_LOCAL:
            return await self._call_deepseek_local(messages, tools, config)
        elif provider == LLMProvider.LLAMA_LOCAL:
            return await self._call_llama_local(messages, tools, config)
        elif provider == LLMProvider.OPENAI:
            return await self._call_openai(messages, tools, config)
        elif provider == LLMProvider.ANTHROPIC:
            return await self._call_anthropic(messages, tools, config)
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    async def _call_deepseek_local(self, 
                                 messages: List[Dict[str, str]], 
                                 tools: Optional[List[Dict[str, Any]]], 
                                 config: LLMConfig) -> LLMResponse:
        """Call DeepSeek R1 0528 local instance."""
        http_client = self.providers["http_client"]
        
        payload = {
            "model": config.model or "deepseek-r1-0528",
            "messages": messages,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "stream": False
        }
        
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        
        response = await http_client.post(
            f"{config.endpoint}/v1/chat/completions",
            json=payload,
            timeout=config.timeout
        )
        response.raise_for_status()
        
        data = response.json()
        choice = data["choices"][0]
        message = choice["message"]
        
        # Extract function calls if present
        function_calls = None
        if message.get("tool_calls"):
            function_calls = [
                {
                    "name": call["function"]["name"],
                    "arguments": json.loads(call["function"]["arguments"])
                }
                for call in message["tool_calls"]
            ]
        
        return LLMResponse(
            content=message.get("content", ""),
            provider=LLMProvider.DEEPSEEK_LOCAL,
            model=config.model or "deepseek-r1-0528",
            tokens_used=data.get("usage", {}).get("total_tokens", 0),
            response_time=0.0,  # Will be set by caller
            cost=0.0,  # Free local model
            function_calls=function_calls
        )
    
    async def _call_llama_local(self, 
                              messages: List[Dict[str, str]], 
                              tools: Optional[List[Dict[str, Any]]], 
                              config: LLMConfig) -> LLMResponse:
        """Call Llama local instance (Ollama or similar)."""
        http_client = self.providers["http_client"]
        
        # Convert messages to Llama format
        prompt = self._convert_messages_to_prompt(messages)
        
        payload = {
            "model": config.model or "llama3.1:8b",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": config.temperature,
                "num_predict": config.max_tokens
            }
        }
        
        response = await http_client.post(
            f"{config.endpoint}/api/generate",
            json=payload,
            timeout=config.timeout
        )
        response.raise_for_status()
        
        data = response.json()
        
        # Parse function calls from response if tools were provided
        function_calls = None
        content = data.get("response", "")
        
        if tools and "function_call:" in content.lower():
            function_calls = self._extract_function_calls_from_text(content)
        
        return LLMResponse(
            content=content,
            provider=LLMProvider.LLAMA_LOCAL,
            model=config.model or "llama3.1:8b",
            tokens_used=len(content.split()) * 1.3,  # Rough token estimation
            response_time=0.0,
            cost=0.0,  # Free local model
            function_calls=function_calls
        )
    
    async def _call_openai(self, 
                         messages: List[Dict[str, str]], 
                         tools: Optional[List[Dict[str, Any]]], 
                         config: LLMConfig) -> LLMResponse:
        """Call OpenAI API."""
        client = self.providers[LLMProvider.OPENAI]
        
        kwargs = {
            "model": config.model or "gpt-4-turbo-preview",
            "messages": messages,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature
        }
        
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        
        response = await client.chat.completions.create(**kwargs)
        
        choice = response.choices[0]
        message = choice.message
        
        # Extract function calls
        function_calls = None
        if message.tool_calls:
            function_calls = [
                {
                    "name": call.function.name,
                    "arguments": json.loads(call.function.arguments)
                }
                for call in message.tool_calls
            ]
        
        tokens_used = response.usage.total_tokens
        cost = tokens_used * config.cost_per_token
        
        return LLMResponse(
            content=message.content or "",
            provider=LLMProvider.OPENAI,
            model=kwargs["model"],
            tokens_used=tokens_used,
            response_time=0.0,
            cost=cost,
            function_calls=function_calls
        )
    
    async def _call_anthropic(self, 
                            messages: List[Dict[str, str]], 
                            tools: Optional[List[Dict[str, Any]]], 
                            config: LLMConfig) -> LLMResponse:
        """Call Anthropic Claude API."""
        client = self.providers[LLMProvider.ANTHROPIC]
        
        # Convert OpenAI format to Anthropic format
        system_message = ""
        anthropic_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                anthropic_messages.append(msg)
        
        kwargs = {
            "model": config.model or "claude-3-sonnet-20240229",
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "messages": anthropic_messages
        }
        
        if system_message:
            kwargs["system"] = system_message
        
        if tools:
            kwargs["tools"] = self._convert_tools_to_anthropic_format(tools)
        
        response = await asyncio.to_thread(client.messages.create, **kwargs)
        
        content = ""
        function_calls = None
        
        for content_block in response.content:
            if content_block.type == "text":
                content += content_block.text
            elif content_block.type == "tool_use":
                if function_calls is None:
                    function_calls = []
                function_calls.append({
                    "name": content_block.name,
                    "arguments": content_block.input
                })
        
        tokens_used = response.usage.input_tokens + response.usage.output_tokens
        cost = tokens_used * config.cost_per_token
        
        return LLMResponse(
            content=content,
            provider=LLMProvider.ANTHROPIC,
            model=kwargs["model"],
            tokens_used=tokens_used,
            response_time=0.0,
            cost=cost,
            function_calls=function_calls
        )
    
    def _convert_messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert OpenAI messages format to a single prompt."""
        prompt_parts = []
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"Human: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        prompt_parts.append("Assistant:")
        return "\n\n".join(prompt_parts)
    
    def _extract_function_calls_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract function calls from text response (for local models without native function calling)."""
        function_calls = []
        
        # Simple pattern matching for function calls
        # This would need to be more sophisticated in production
        import re
        
        pattern = r"function_call:\s*(\w+)\s*\((.*?)\)"
        matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            function_name = match[0]
            args_str = match[1]
            
            try:
                # Try to parse arguments as JSON
                arguments = json.loads(f"{{{args_str}}}")
            except:
                # Fallback to simple parsing
                arguments = {"command": args_str.strip()}
            
            function_calls.append({
                "name": function_name,
                "arguments": arguments
            })
        
        return function_calls
    
    def _convert_tools_to_anthropic_format(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert OpenAI tools format to Anthropic format."""
        anthropic_tools = []
        
        for tool in tools:
            if tool["type"] == "function":
                func = tool["function"]
                anthropic_tools.append({
                    "name": func["name"],
                    "description": func["description"],
                    "input_schema": func["parameters"]
                })
        
        return anthropic_tools
    
    def _is_provider_available(self, provider: LLMProvider) -> bool:
        """Check if provider is available and enabled."""
        if provider not in self.configs:
            return False
        
        config = self.configs[provider]
        if not config.enabled:
            return False
        
        health = self.provider_health[provider]
        
        # Disable provider temporarily if too many errors
        if health["error_count"] > 3:
            return False
        
        return health["available"]
    
    def _update_provider_health(self, provider: LLMProvider, success: bool, error: Optional[str] = None):
        """Update provider health status."""
        health = self.provider_health[provider]
        
        if success:
            health["available"] = True
            health["error_count"] = max(0, health["error_count"] - 1)  # Reduce error count on success
            health["last_error"] = None
        else:
            health["error_count"] += 1
            health["last_error"] = error
            
            # Disable if too many consecutive errors
            if health["error_count"] > 3:
                health["available"] = False
                logger.warning(f"Provider {provider.value} disabled due to repeated errors")
    
    def _update_usage_stats(self, provider: LLMProvider, response: LLMResponse):
        """Update usage statistics."""
        stats = self.usage_stats[provider]
        stats["calls"] += 1
        stats["tokens"] += response.tokens_used
        stats["cost"] += response.cost
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics for all providers."""
        return {
            "providers": self.usage_stats,
            "total_cost": sum(stats["cost"] for stats in self.usage_stats.values()),
            "total_tokens": sum(stats["tokens"] for stats in self.usage_stats.values()),
            "total_calls": sum(stats["calls"] for stats in self.usage_stats.values()),
            "provider_health": self.provider_health
        }
    
    def get_optimal_provider(self) -> LLMProvider:
        """Get the optimal provider based on availability and cost."""
        for provider in self.fallback_order:
            if self._is_provider_available(provider):
                return provider
        
        return self.fallback_order[0]  # Fallback to first provider
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all providers."""
        health_results = {}
        
        for provider in LLMProvider:
            if provider not in self.configs:
                health_results[provider.value] = {"status": "not_configured"}
                continue
            
            try:
                # Simple health check message
                test_messages = [{"role": "user", "content": "Hello"}]
                response = await self._call_provider(provider, test_messages)
                
                health_results[provider.value] = {
                    "status": "healthy",
                    "response_time": response.response_time,
                    "model": response.model
                }
                
                self._update_provider_health(provider, success=True)
                
            except Exception as e:
                health_results[provider.value] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                
                self._update_provider_health(provider, success=False, error=str(e))
        
        return health_results