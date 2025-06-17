"""
vLLM Integration for reVoAgent

Provides zero-cost local model serving with vLLM for optimal performance.
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any, AsyncGenerator
from datetime import datetime
import httpx

logger = logging.getLogger(__name__)


class VLLMIntegration:
    """Integration with vLLM model serving platform."""
    
    def __init__(self, 
                 base_url: str = "http://localhost:8000",
                 api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=60.0)
        self.status = "disconnected"
        self.last_health_check = None
        self.loaded_models = {}
        
    async def initialize(self):
        """Initialize the vLLM integration."""
        try:
            await self.health_check()
            await self.refresh_model_list()
            logger.info("vLLM integration initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize vLLM integration: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Check vLLM service health."""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            if response.status_code == 200:
                self.status = "healthy"
                self.last_health_check = datetime.now()
                return {
                    "status": "healthy",
                    "response_time": response.elapsed.total_seconds() * 1000,
                    "timestamp": self.last_health_check.isoformat()
                }
            else:
                self.status = "unhealthy"
                return {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}",
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            self.status = "error"
            logger.error(f"vLLM health check failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def generate_completion(self, 
                                prompt: str, 
                                model: str = "deepseek-r1",
                                max_tokens: int = 2048,
                                temperature: float = 0.7,
                                top_p: float = 0.9,
                                stream: bool = False) -> Dict[str, Any]:
        """Generate text completion using vLLM."""
        try:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            payload = {
                "model": model,
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "stream": stream
            }
            
            response = await self.client.post(
                f"{self.base_url}/v1/completions",
                json=payload,
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Generated completion using model {model}")
                return result
            else:
                raise Exception(f"Completion generation failed: HTTP {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error generating completion: {e}")
            raise
    
    async def generate_chat_completion(self,
                                     messages: List[Dict[str, str]],
                                     model: str = "deepseek-r1",
                                     max_tokens: int = 2048,
                                     temperature: float = 0.7,
                                     top_p: float = 0.9,
                                     stream: bool = False) -> Dict[str, Any]:
        """Generate chat completion using vLLM."""
        try:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "stream": stream
            }
            
            response = await self.client.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Generated chat completion using model {model}")
                return result
            else:
                raise Exception(f"Chat completion failed: HTTP {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error generating chat completion: {e}")
            raise
    
    async def stream_completion(self,
                              prompt: str,
                              model: str = "deepseek-r1",
                              max_tokens: int = 2048,
                              temperature: float = 0.7) -> AsyncGenerator[str, None]:
        """Stream text completion from vLLM."""
        try:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            payload = {
                "model": model,
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": True
            }
            
            async with self.client.stream(
                "POST",
                f"{self.base_url}/v1/completions",
                json=payload,
                headers=headers
            ) as response:
                if response.status_code == 200:
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]  # Remove "data: " prefix
                            if data.strip() == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data)
                                if "choices" in chunk and chunk["choices"]:
                                    text = chunk["choices"][0].get("text", "")
                                    if text:
                                        yield text
                            except json.JSONDecodeError:
                                continue
                else:
                    raise Exception(f"Streaming failed: HTTP {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Error streaming completion: {e}")
            raise
    
    async def get_model_list(self) -> List[Dict[str, Any]]:
        """Get list of available models."""
        try:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            response = await self.client.get(
                f"{self.base_url}/v1/models",
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("data", [])
            else:
                raise Exception(f"Failed to get model list: HTTP {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error getting model list: {e}")
            raise
    
    async def refresh_model_list(self):
        """Refresh the cached model list."""
        try:
            models = await self.get_model_list()
            self.loaded_models = {model["id"]: model for model in models}
            logger.info(f"Refreshed model list: {len(models)} models available")
        except Exception as e:
            logger.error(f"Error refreshing model list: {e}")
    
    async def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific model."""
        try:
            if model_id in self.loaded_models:
                return self.loaded_models[model_id]
            
            # Refresh model list and try again
            await self.refresh_model_list()
            return self.loaded_models.get(model_id, {})
            
        except Exception as e:
            logger.error(f"Error getting model info for {model_id}: {e}")
            raise
    
    async def get_server_stats(self) -> Dict[str, Any]:
        """Get vLLM server statistics."""
        try:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            response = await self.client.get(
                f"{self.base_url}/stats",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                # If stats endpoint doesn't exist, return basic info
                return {
                    "status": "running",
                    "models_loaded": len(self.loaded_models),
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting server stats: {e}")
            return {
                "status": "unknown",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_integration_metrics(self) -> Dict[str, Any]:
        """Get integration metrics and statistics."""
        try:
            health = await self.health_check()
            stats = await self.get_server_stats()
            
            metrics = {
                "service_name": "vLLM",
                "status": self.status,
                "health": health,
                "server_stats": stats,
                "models_loaded": len(self.loaded_models),
                "features": {
                    "local_inference": True,
                    "zero_cost": True,
                    "high_performance": True,
                    "streaming": True,
                    "multiple_models": True,
                    "gpu_acceleration": True
                },
                "capabilities": [
                    "Text completion",
                    "Chat completion", 
                    "Code generation",
                    "Streaming responses",
                    "Multiple model support",
                    "GPU optimization"
                ]
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting vLLM metrics: {e}")
            return {
                "service_name": "vLLM",
                "status": "error",
                "error": str(e)
            }
    
    async def close(self):
        """Close the integration and cleanup resources."""
        await self.client.aclose()
        logger.info("vLLM integration closed")


# Mock implementation for demonstration
class MockVLLMIntegration(VLLMIntegration):
    """Mock vLLM integration for testing and demonstration."""
    
    def __init__(self):
        super().__init__()
        self.status = "healthy"
        self.loaded_models = {
            "deepseek-r1": {
                "id": "deepseek-r1",
                "object": "model",
                "created": 1640995200,
                "owned_by": "deepseek",
                "permission": [],
                "root": "deepseek-r1",
                "parent": None
            },
            "codellama-70b": {
                "id": "codellama-70b",
                "object": "model", 
                "created": 1640995200,
                "owned_by": "meta",
                "permission": [],
                "root": "codellama-70b",
                "parent": None
            },
            "mistral-7b": {
                "id": "mistral-7b",
                "object": "model",
                "created": 1640995200,
                "owned_by": "mistralai",
                "permission": [],
                "root": "mistral-7b", 
                "parent": None
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Mock health check."""
        self.last_health_check = datetime.now()
        return {
            "status": "healthy",
            "response_time": 156,  # Mock response time
            "timestamp": self.last_health_check.isoformat(),
            "version": "0.2.7",
            "gpu_memory_usage": "18.2GB",
            "models_loaded": len(self.loaded_models)
        }
    
    async def generate_completion(self, 
                                prompt: str, 
                                model: str = "deepseek-r1",
                                max_tokens: int = 2048,
                                temperature: float = 0.7,
                                top_p: float = 0.9,
                                stream: bool = False) -> Dict[str, Any]:
        """Mock completion generation."""
        # Simulate processing time
        await asyncio.sleep(0.5)
        
        return {
            "id": f"cmpl-{datetime.now().timestamp()}",
            "object": "text_completion",
            "created": int(datetime.now().timestamp()),
            "model": model,
            "choices": [{
                "text": f"# Generated code based on prompt: {prompt[:50]}...\n\ndef example_function():\n    return 'Mock generated code'",
                "index": 0,
                "logprobs": None,
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": len(prompt.split()),
                "completion_tokens": 50,
                "total_tokens": len(prompt.split()) + 50
            }
        }
    
    async def generate_chat_completion(self,
                                     messages: List[Dict[str, str]],
                                     model: str = "deepseek-r1",
                                     max_tokens: int = 2048,
                                     temperature: float = 0.7,
                                     top_p: float = 0.9,
                                     stream: bool = False) -> Dict[str, Any]:
        """Mock chat completion generation."""
        # Simulate processing time
        await asyncio.sleep(0.8)
        
        last_message = messages[-1]["content"] if messages else "Hello"
        
        return {
            "id": f"chatcmpl-{datetime.now().timestamp()}",
            "object": "chat.completion",
            "created": int(datetime.now().timestamp()),
            "model": model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": f"I understand you want me to help with: {last_message[:100]}...\n\nHere's a comprehensive solution:\n\n```python\n# Generated solution\ndef solve_problem():\n    return 'Mock AI response'\n```"
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": sum(len(msg["content"].split()) for msg in messages),
                "completion_tokens": 75,
                "total_tokens": sum(len(msg["content"].split()) for msg in messages) + 75
            }
        }
    
    async def get_server_stats(self) -> Dict[str, Any]:
        """Mock server statistics."""
        return {
            "status": "running",
            "models_loaded": len(self.loaded_models),
            "gpu_memory_usage": "18.2GB",
            "gpu_utilization": 78,
            "requests_per_minute": 45,
            "avg_tokens_per_second": 2340,
            "avg_latency_ms": 847,
            "cache_hit_rate": 0.89,
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_integration_metrics(self) -> Dict[str, Any]:
        """Mock integration metrics."""
        return {
            "service_name": "vLLM",
            "status": "healthy",
            "health": await self.health_check(),
            "server_stats": await self.get_server_stats(),
            "models_loaded": len(self.loaded_models),
            "features": {
                "local_inference": True,
                "zero_cost": True,
                "high_performance": True,
                "streaming": True,
                "multiple_models": True,
                "gpu_acceleration": True
            },
            "performance": {
                "avg_response_time": 156,
                "tokens_per_second": 2340,
                "gpu_utilization": 78,
                "cache_hit_rate": 89,
                "uptime": "99.9%"
            }
        }