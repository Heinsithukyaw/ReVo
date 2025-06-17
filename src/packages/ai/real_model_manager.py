#!/usr/bin/env python3
"""
Real AI Model Manager for reVoAgent
Production-ready AI model management with actual model integrations

This module implements real AI model integrations:
- DeepSeek R1 (local model via API)
- Llama 3.1 (local model via Ollama)
- Claude 3.5 Sonnet (Anthropic API)
- Gemini Pro (Google API)
- GPT-4 (OpenAI API)
"""

import asyncio
import aiohttp
import json
import time
import logging
import os
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import subprocess
import psutil
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelType(Enum):
    """Real AI model types"""
    DEEPSEEK_R1 = "deepseek_r1"
    LLAMA_LOCAL = "llama_local"
    CLAUDE_SONNET = "claude_sonnet"
    GEMINI_PRO = "gemini_pro"
    GPT_4 = "gpt_4"

class ModelStatus(Enum):
    """Model availability status"""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    LOADING = "loading"
    ERROR = "error"
    RATE_LIMITED = "rate_limited"

@dataclass
class RealModelConfig:
    """Configuration for real AI models"""
    model_type: ModelType
    endpoint_url: Optional[str] = None
    api_key: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7
    cost_per_1k_input_tokens: float = 0.0
    cost_per_1k_output_tokens: float = 0.0
    rate_limit_rpm: int = 60  # requests per minute
    timeout_seconds: int = 30
    is_local: bool = False

@dataclass
class RealGenerationRequest:
    """Request for real AI generation"""
    prompt: str
    model_preference: ModelType = ModelType.DEEPSEEK_R1
    max_tokens: int = 1000
    temperature: float = 0.7
    system_prompt: Optional[str] = None
    context: Optional[str] = None
    task_type: str = "general"
    priority: str = "normal"
    
@dataclass
class RealGenerationResponse:
    """Response from real AI generation"""
    content: str
    model_used: ModelType
    tokens_used: int
    cost: float
    response_time: float
    success: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class RealModelManager:
    """Production AI Model Manager with real integrations"""
    
    def __init__(self):
        self.models: Dict[ModelType, RealModelConfig] = {}
        self.model_status: Dict[ModelType, ModelStatus] = {}
        self.usage_stats: Dict[ModelType, Dict[str, Any]] = {}
        self.session: Optional[aiohttp.ClientSession] = None
        self.cost_tracker = {
            "total_cost": 0.0,
            "daily_cost": 0.0,
            "requests_today": 0,
            "cost_by_model": {}
        }
        
    async def initialize(self):
        """Initialize all real AI models"""
        logger.info("🚀 Initializing Real AI Model Manager...")
        
        # Create HTTP session
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60)
        )
        
        # Initialize model configurations
        await self._setup_model_configs()
        
        # Test model availability
        await self._test_model_availability()
        
        # Initialize usage tracking
        self._initialize_usage_tracking()
        
        logger.info(f"✅ Real AI Model Manager initialized with {len(self.models)} models")
    
    async def _setup_model_configs(self):
        """Setup configurations for all real models"""
        
        # DeepSeek R1 (Local/API)
        self.models[ModelType.DEEPSEEK_R1] = RealModelConfig(
            model_type=ModelType.DEEPSEEK_R1,
            endpoint_url="https://api.deepseek.com/v1/chat/completions",
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            cost_per_1k_input_tokens=0.0,  # Free tier or local
            cost_per_1k_output_tokens=0.0,
            rate_limit_rpm=100,
            is_local=True
        )
        
        # Llama 3.1 (Local via Ollama)
        self.models[ModelType.LLAMA_LOCAL] = RealModelConfig(
            model_type=ModelType.LLAMA_LOCAL,
            endpoint_url="http://localhost:11434/api/generate",
            cost_per_1k_input_tokens=0.0,  # Local model
            cost_per_1k_output_tokens=0.0,
            rate_limit_rpm=200,
            is_local=True
        )
        
        # Claude 3.5 Sonnet (Anthropic)
        self.models[ModelType.CLAUDE_SONNET] = RealModelConfig(
            model_type=ModelType.CLAUDE_SONNET,
            endpoint_url="https://api.anthropic.com/v1/messages",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            cost_per_1k_input_tokens=3.0,  # $3 per 1M tokens
            cost_per_1k_output_tokens=15.0,  # $15 per 1M tokens
            rate_limit_rpm=50,
            is_local=False
        )
        
        # Gemini Pro (Google)
        self.models[ModelType.GEMINI_PRO] = RealModelConfig(
            model_type=ModelType.GEMINI_PRO,
            endpoint_url="https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent",
            api_key=os.getenv("GOOGLE_API_KEY"),
            cost_per_1k_input_tokens=0.5,  # $0.5 per 1M tokens
            cost_per_1k_output_tokens=1.5,  # $1.5 per 1M tokens
            rate_limit_rpm=60,
            is_local=False
        )
        
        # GPT-4 (OpenAI)
        self.models[ModelType.GPT_4] = RealModelConfig(
            model_type=ModelType.GPT_4,
            endpoint_url="https://api.openai.com/v1/chat/completions",
            api_key=os.getenv("OPENAI_API_KEY"),
            cost_per_1k_input_tokens=30.0,  # $30 per 1M tokens
            cost_per_1k_output_tokens=60.0,  # $60 per 1M tokens
            rate_limit_rpm=40,
            is_local=False
        )
    
    async def _test_model_availability(self):
        """Test availability of all configured models"""
        logger.info("🔍 Testing model availability...")
        
        for model_type, config in self.models.items():
            try:
                if config.is_local:
                    status = await self._test_local_model(config)
                else:
                    status = await self._test_cloud_model(config)
                
                self.model_status[model_type] = status
                logger.info(f"📊 {model_type.value}: {status.value}")
                
            except Exception as e:
                self.model_status[model_type] = ModelStatus.ERROR
                logger.warning(f"⚠️ {model_type.value}: Error - {e}")
    
    async def _test_local_model(self, config: RealModelConfig) -> ModelStatus:
        """Test local model availability"""
        if config.model_type == ModelType.DEEPSEEK_R1:
            # Test DeepSeek API
            if config.api_key:
                return await self._test_api_endpoint(config, "DeepSeek test")
            else:
                logger.warning("⚠️ DeepSeek API key not found")
                return ModelStatus.UNAVAILABLE
                
        elif config.model_type == ModelType.LLAMA_LOCAL:
            # Test Ollama local installation
            try:
                result = subprocess.run(
                    ["ollama", "list"], 
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
                if result.returncode == 0 and "llama" in result.stdout.lower():
                    return ModelStatus.AVAILABLE
                else:
                    logger.warning("⚠️ Llama model not found in Ollama")
                    return ModelStatus.UNAVAILABLE
            except (subprocess.TimeoutExpired, FileNotFoundError):
                logger.warning("⚠️ Ollama not installed or not responding")
                return ModelStatus.UNAVAILABLE
        
        return ModelStatus.UNAVAILABLE
    
    async def _test_cloud_model(self, config: RealModelConfig) -> ModelStatus:
        """Test cloud model availability"""
        if not config.api_key:
            logger.warning(f"⚠️ API key not found for {config.model_type.value}")
            return ModelStatus.UNAVAILABLE
        
        return await self._test_api_endpoint(config, "API test")
    
    async def _test_api_endpoint(self, config: RealModelConfig, test_prompt: str) -> ModelStatus:
        """Test API endpoint with a simple request"""
        try:
            if config.model_type == ModelType.CLAUDE_SONNET:
                headers = {
                    "x-api-key": config.api_key,
                    "content-type": "application/json",
                    "anthropic-version": "2023-06-01"
                }
                data = {
                    "model": "claude-3-5-sonnet-20241022",
                    "max_tokens": 10,
                    "messages": [{"role": "user", "content": test_prompt}]
                }
                
            elif config.model_type == ModelType.GEMINI_PRO:
                headers = {"Content-Type": "application/json"}
                url = f"{config.endpoint_url}?key={config.api_key}"
                data = {
                    "contents": [{"parts": [{"text": test_prompt}]}],
                    "generationConfig": {"maxOutputTokens": 10}
                }
                config.endpoint_url = url
                
            elif config.model_type == ModelType.GPT_4:
                headers = {
                    "Authorization": f"Bearer {config.api_key}",
                    "Content-Type": "application/json"
                }
                data = {
                    "model": "gpt-4",
                    "messages": [{"role": "user", "content": test_prompt}],
                    "max_tokens": 10
                }
                
            elif config.model_type == ModelType.DEEPSEEK_R1:
                headers = {
                    "Authorization": f"Bearer {config.api_key}",
                    "Content-Type": "application/json"
                }
                data = {
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": test_prompt}],
                    "max_tokens": 10
                }
            
            async with self.session.post(
                config.endpoint_url,
                headers=headers,
                json=data,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    return ModelStatus.AVAILABLE
                elif response.status == 429:
                    return ModelStatus.RATE_LIMITED
                else:
                    logger.warning(f"⚠️ API test failed: {response.status}")
                    return ModelStatus.ERROR
                    
        except asyncio.TimeoutError:
            logger.warning(f"⚠️ API test timeout for {config.model_type.value}")
            return ModelStatus.UNAVAILABLE
        except Exception as e:
            logger.warning(f"⚠️ API test error for {config.model_type.value}: {e}")
            return ModelStatus.ERROR
    
    def _initialize_usage_tracking(self):
        """Initialize usage tracking for all models"""
        for model_type in self.models.keys():
            self.usage_stats[model_type] = {
                "requests_count": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
                "average_response_time": 0.0,
                "success_rate": 1.0,
                "last_used": None
            }
            self.cost_tracker["cost_by_model"][model_type.value] = 0.0
    
    async def generate_response(self, request: RealGenerationRequest) -> RealGenerationResponse:
        """Generate response using real AI models with intelligent routing"""
        start_time = time.time()
        
        # Determine best model to use
        selected_model = await self._select_optimal_model(request)
        
        if not selected_model:
            return RealGenerationResponse(
                content="",
                model_used=request.model_preference,
                tokens_used=0,
                cost=0.0,
                response_time=time.time() - start_time,
                success=False,
                error_message="No available models"
            )
        
        # Generate response with selected model
        try:
            response = await self._generate_with_model(selected_model, request)
            
            # Update usage statistics
            await self._update_usage_stats(selected_model, response)
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Generation failed with {selected_model.value}: {e}")
            
            # Try fallback model
            fallback_model = await self._get_fallback_model(selected_model)
            if fallback_model:
                try:
                    response = await self._generate_with_model(fallback_model, request)
                    await self._update_usage_stats(fallback_model, response)
                    return response
                except Exception as fallback_error:
                    logger.error(f"❌ Fallback also failed: {fallback_error}")
            
            return RealGenerationResponse(
                content="",
                model_used=selected_model,
                tokens_used=0,
                cost=0.0,
                response_time=time.time() - start_time,
                success=False,
                error_message=str(e)
            )
    
    async def _select_optimal_model(self, request: RealGenerationRequest) -> Optional[ModelType]:
        """Select optimal model based on request and availability"""
        
        # Check if preferred model is available
        if (request.model_preference in self.model_status and 
            self.model_status[request.model_preference] == ModelStatus.AVAILABLE):
            return request.model_preference
        
        # Intelligent model selection based on task type and cost
        if request.task_type in ["code_generation", "simple_task"]:
            # Prefer local models for code generation
            for model_type in [ModelType.DEEPSEEK_R1, ModelType.LLAMA_LOCAL]:
                if (model_type in self.model_status and 
                    self.model_status[model_type] == ModelStatus.AVAILABLE):
                    return model_type
        
        elif request.task_type in ["analysis", "complex_reasoning"]:
            # Prefer high-quality models for analysis
            for model_type in [ModelType.CLAUDE_SONNET, ModelType.GPT_4, ModelType.GEMINI_PRO]:
                if (model_type in self.model_status and 
                    self.model_status[model_type] == ModelStatus.AVAILABLE):
                    return model_type
        
        # Fallback to any available model (cost-optimized order)
        priority_order = [
            ModelType.DEEPSEEK_R1,    # Free
            ModelType.LLAMA_LOCAL,    # Free
            ModelType.GEMINI_PRO,     # Cheapest cloud
            ModelType.CLAUDE_SONNET,  # Mid-tier cloud
            ModelType.GPT_4           # Most expensive
        ]
        
        for model_type in priority_order:
            if (model_type in self.model_status and 
                self.model_status[model_type] == ModelStatus.AVAILABLE):
                return model_type
        
        return None
    
    async def _generate_with_model(self, model_type: ModelType, request: RealGenerationRequest) -> RealGenerationResponse:
        """Generate response with specific model"""
        config = self.models[model_type]
        start_time = time.time()
        
        if model_type == ModelType.DEEPSEEK_R1:
            return await self._generate_deepseek(config, request, start_time)
        elif model_type == ModelType.LLAMA_LOCAL:
            return await self._generate_llama(config, request, start_time)
        elif model_type == ModelType.CLAUDE_SONNET:
            return await self._generate_claude(config, request, start_time)
        elif model_type == ModelType.GEMINI_PRO:
            return await self._generate_gemini(config, request, start_time)
        elif model_type == ModelType.GPT_4:
            return await self._generate_gpt4(config, request, start_time)
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
    
    async def _generate_deepseek(self, config: RealModelConfig, request: RealGenerationRequest, start_time: float) -> RealGenerationResponse:
        """Generate response using DeepSeek R1"""
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        if request.context:
            messages.append({"role": "user", "content": f"Context: {request.context}"})
        messages.append({"role": "user", "content": request.prompt})
        
        data = {
            "model": "deepseek-chat",
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature
        }
        
        async with self.session.post(config.endpoint_url, headers=headers, json=data) as response:
            if response.status == 200:
                result = await response.json()
                content = result["choices"][0]["message"]["content"]
                tokens_used = result.get("usage", {}).get("total_tokens", 0)
                
                return RealGenerationResponse(
                    content=content,
                    model_used=ModelType.DEEPSEEK_R1,
                    tokens_used=tokens_used,
                    cost=0.0,  # Free model
                    response_time=time.time() - start_time,
                    success=True,
                    metadata={"provider": "deepseek", "model": "deepseek-chat"}
                )
            else:
                error_text = await response.text()
                raise Exception(f"DeepSeek API error {response.status}: {error_text}")
    
    async def _generate_llama(self, config: RealModelConfig, request: RealGenerationRequest, start_time: float) -> RealGenerationResponse:
        """Generate response using local Llama via Ollama"""
        
        # Construct prompt for Ollama
        full_prompt = ""
        if request.system_prompt:
            full_prompt += f"System: {request.system_prompt}\n\n"
        if request.context:
            full_prompt += f"Context: {request.context}\n\n"
        full_prompt += f"User: {request.prompt}\n\nAssistant:"
        
        data = {
            "model": "llama3.1",
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens
            }
        }
        
        async with self.session.post(config.endpoint_url, json=data) as response:
            if response.status == 200:
                result = await response.json()
                content = result.get("response", "")
                
                # Estimate tokens (rough approximation)
                tokens_used = len(content.split()) + len(full_prompt.split())
                
                return RealGenerationResponse(
                    content=content,
                    model_used=ModelType.LLAMA_LOCAL,
                    tokens_used=tokens_used,
                    cost=0.0,  # Local model
                    response_time=time.time() - start_time,
                    success=True,
                    metadata={"provider": "ollama", "model": "llama3.1"}
                )
            else:
                error_text = await response.text()
                raise Exception(f"Ollama API error {response.status}: {error_text}")
    
    async def _generate_claude(self, config: RealModelConfig, request: RealGenerationRequest, start_time: float) -> RealGenerationResponse:
        """Generate response using Claude 3.5 Sonnet"""
        headers = {
            "x-api-key": config.api_key,
            "content-type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        messages = []
        if request.context:
            messages.append({"role": "user", "content": f"Context: {request.context}"})
        messages.append({"role": "user", "content": request.prompt})
        
        data = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "messages": messages
        }
        
        if request.system_prompt:
            data["system"] = request.system_prompt
        
        async with self.session.post(config.endpoint_url, headers=headers, json=data) as response:
            if response.status == 200:
                result = await response.json()
                content = result["content"][0]["text"]
                usage = result.get("usage", {})
                input_tokens = usage.get("input_tokens", 0)
                output_tokens = usage.get("output_tokens", 0)
                
                # Calculate cost
                cost = (
                    (input_tokens / 1000) * config.cost_per_1k_input_tokens / 1000 +
                    (output_tokens / 1000) * config.cost_per_1k_output_tokens / 1000
                )
                
                return RealGenerationResponse(
                    content=content,
                    model_used=ModelType.CLAUDE_SONNET,
                    tokens_used=input_tokens + output_tokens,
                    cost=cost,
                    response_time=time.time() - start_time,
                    success=True,
                    metadata={"provider": "anthropic", "model": "claude-3-5-sonnet"}
                )
            else:
                error_text = await response.text()
                raise Exception(f"Claude API error {response.status}: {error_text}")
    
    async def _generate_gemini(self, config: RealModelConfig, request: RealGenerationRequest, start_time: float) -> RealGenerationResponse:
        """Generate response using Gemini Pro"""
        
        # Construct content for Gemini
        content_parts = []
        if request.system_prompt:
            content_parts.append({"text": f"System instructions: {request.system_prompt}"})
        if request.context:
            content_parts.append({"text": f"Context: {request.context}"})
        content_parts.append({"text": request.prompt})
        
        data = {
            "contents": [{"parts": content_parts}],
            "generationConfig": {
                "maxOutputTokens": request.max_tokens,
                "temperature": request.temperature
            }
        }
        
        async with self.session.post(config.endpoint_url, json=data) as response:
            if response.status == 200:
                result = await response.json()
                content = result["candidates"][0]["content"]["parts"][0]["text"]
                
                # Estimate tokens and cost
                input_tokens = sum(len(part.get("text", "").split()) for part in content_parts)
                output_tokens = len(content.split())
                
                cost = (
                    (input_tokens / 1000) * config.cost_per_1k_input_tokens / 1000 +
                    (output_tokens / 1000) * config.cost_per_1k_output_tokens / 1000
                )
                
                return RealGenerationResponse(
                    content=content,
                    model_used=ModelType.GEMINI_PRO,
                    tokens_used=input_tokens + output_tokens,
                    cost=cost,
                    response_time=time.time() - start_time,
                    success=True,
                    metadata={"provider": "google", "model": "gemini-pro"}
                )
            else:
                error_text = await response.text()
                raise Exception(f"Gemini API error {response.status}: {error_text}")
    
    async def _generate_gpt4(self, config: RealModelConfig, request: RealGenerationRequest, start_time: float) -> RealGenerationResponse:
        """Generate response using GPT-4"""
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        if request.context:
            messages.append({"role": "user", "content": f"Context: {request.context}"})
        messages.append({"role": "user", "content": request.prompt})
        
        data = {
            "model": "gpt-4",
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature
        }
        
        async with self.session.post(config.endpoint_url, headers=headers, json=data) as response:
            if response.status == 200:
                result = await response.json()
                content = result["choices"][0]["message"]["content"]
                usage = result.get("usage", {})
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)
                
                # Calculate cost
                cost = (
                    (prompt_tokens / 1000) * config.cost_per_1k_input_tokens / 1000 +
                    (completion_tokens / 1000) * config.cost_per_1k_output_tokens / 1000
                )
                
                return RealGenerationResponse(
                    content=content,
                    model_used=ModelType.GPT_4,
                    tokens_used=prompt_tokens + completion_tokens,
                    cost=cost,
                    response_time=time.time() - start_time,
                    success=True,
                    metadata={"provider": "openai", "model": "gpt-4"}
                )
            else:
                error_text = await response.text()
                raise Exception(f"GPT-4 API error {response.status}: {error_text}")
    
    async def _get_fallback_model(self, failed_model: ModelType) -> Optional[ModelType]:
        """Get fallback model when primary model fails"""
        fallback_order = {
            ModelType.DEEPSEEK_R1: [ModelType.LLAMA_LOCAL, ModelType.GEMINI_PRO],
            ModelType.LLAMA_LOCAL: [ModelType.DEEPSEEK_R1, ModelType.GEMINI_PRO],
            ModelType.CLAUDE_SONNET: [ModelType.GEMINI_PRO, ModelType.GPT_4],
            ModelType.GEMINI_PRO: [ModelType.CLAUDE_SONNET, ModelType.DEEPSEEK_R1],
            ModelType.GPT_4: [ModelType.CLAUDE_SONNET, ModelType.GEMINI_PRO]
        }
        
        for fallback in fallback_order.get(failed_model, []):
            if (fallback in self.model_status and 
                self.model_status[fallback] == ModelStatus.AVAILABLE):
                return fallback
        
        return None
    
    async def _update_usage_stats(self, model_type: ModelType, response: RealGenerationResponse):
        """Update usage statistics for model"""
        stats = self.usage_stats[model_type]
        
        stats["requests_count"] += 1
        stats["total_tokens"] += response.tokens_used
        stats["total_cost"] += response.cost
        stats["last_used"] = datetime.now(timezone.utc)
        
        # Update average response time
        current_avg = stats["average_response_time"]
        count = stats["requests_count"]
        stats["average_response_time"] = (current_avg * (count - 1) + response.response_time) / count
        
        # Update success rate
        if response.success:
            stats["success_rate"] = (stats["success_rate"] * (count - 1) + 1.0) / count
        else:
            stats["success_rate"] = (stats["success_rate"] * (count - 1) + 0.0) / count
        
        # Update cost tracker
        self.cost_tracker["total_cost"] += response.cost
        self.cost_tracker["daily_cost"] += response.cost
        self.cost_tracker["requests_today"] += 1
        self.cost_tracker["cost_by_model"][model_type.value] += response.cost
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """Get comprehensive usage summary"""
        return {
            "total_requests": sum(stats["requests_count"] for stats in self.usage_stats.values()),
            "total_cost": self.cost_tracker["total_cost"],
            "daily_cost": self.cost_tracker["daily_cost"],
            "model_status": {model.value: status.value for model, status in self.model_status.items()},
            "model_usage": {
                model.value: {
                    "requests": stats["requests_count"],
                    "cost": stats["total_cost"],
                    "avg_response_time": stats["average_response_time"],
                    "success_rate": stats["success_rate"]
                }
                for model, stats in self.usage_stats.items()
            },
            "cost_savings": self._calculate_cost_savings()
        }
    
    def _calculate_cost_savings(self) -> Dict[str, float]:
        """Calculate cost savings vs full cloud deployment"""
        total_requests = sum(stats["requests_count"] for stats in self.usage_stats.values())
        if total_requests == 0:
            return {"savings_percentage": 0.0, "amount_saved": 0.0}
        
        # Estimate cost if all requests used GPT-4 (most expensive)
        avg_tokens_per_request = sum(stats["total_tokens"] for stats in self.usage_stats.values()) / total_requests
        estimated_gpt4_cost = total_requests * (avg_tokens_per_request / 1000) * (30.0 / 1000)  # GPT-4 pricing
        
        actual_cost = self.cost_tracker["total_cost"]
        savings_amount = estimated_gpt4_cost - actual_cost
        savings_percentage = (savings_amount / estimated_gpt4_cost * 100) if estimated_gpt4_cost > 0 else 0
        
        return {
            "savings_percentage": savings_percentage,
            "amount_saved": savings_amount,
            "estimated_full_cloud_cost": estimated_gpt4_cost,
            "actual_cost": actual_cost
        }
    
    async def shutdown(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
        logger.info("🔄 Real AI Model Manager shutdown complete")


# Factory function for easy integration
async def create_real_model_manager() -> RealModelManager:
    """Create and initialize real model manager"""
    manager = RealModelManager()
    await manager.initialize()
    return manager


if __name__ == "__main__":
    # Test the real model manager
    async def test_real_models():
        manager = await create_real_model_manager()
        
        # Test request
        request = RealGenerationRequest(
            prompt="Write a simple Python function to calculate factorial",
            task_type="code_generation",
            max_tokens=200
        )
        
        response = await manager.generate_response(request)
        
        print(f"✅ Generated response using {response.model_used.value}")
        print(f"📝 Content: {response.content[:100]}...")
        print(f"💰 Cost: ${response.cost:.6f}")
        print(f"⏱️ Response time: {response.response_time:.2f}s")
        
        # Print usage summary
        summary = manager.get_usage_summary()
        print(f"📊 Usage Summary: {summary}")
        
        await manager.shutdown()
    
    asyncio.run(test_real_models())