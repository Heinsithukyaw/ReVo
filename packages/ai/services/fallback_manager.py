"""
Fallback Manager Service

Focused service for handling model failures and implementing fallback strategies.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import time

from ..schemas import GenerationRequest, GenerationResponse

logger = logging.getLogger(__name__)


class FallbackStrategy(Enum):
    """Available fallback strategies."""
    ALTERNATIVE_MODEL = "alternative_model"
    MOCK_RESPONSE = "mock_response"
    CACHED_RESPONSE = "cached_response"
    EXTERNAL_API = "external_api"
    GRACEFUL_DEGRADATION = "graceful_degradation"


@dataclass
class FallbackRule:
    """Configuration for a fallback rule."""
    trigger_condition: str  # "model_unavailable", "generation_error", "timeout"
    strategy: FallbackStrategy
    priority: int
    config: Dict[str, Any]
    enabled: bool = True


class FallbackManager:
    """
    Focused service for handling model failures and fallback strategies.
    
    Responsibilities:
    - Handle model unavailability
    - Manage fallback strategies
    - Implement circuit breaker pattern
    - Provide graceful degradation
    - Cache responses for fallback
    """
    
    def __init__(self):
        self.fallback_rules: List[FallbackRule] = []
        self.model_health: Dict[str, Dict[str, Any]] = {}
        self.response_cache: Dict[str, GenerationResponse] = {}
        self.circuit_breakers: Dict[str, Dict[str, Any]] = {}
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Setup default fallback rules."""
        self.fallback_rules = [
            FallbackRule(
                trigger_condition="model_unavailable",
                strategy=FallbackStrategy.ALTERNATIVE_MODEL,
                priority=1,
                config={"alternative_models": ["gpt-3.5-turbo", "claude-3-sonnet"]}
            ),
            FallbackRule(
                trigger_condition="generation_error",
                strategy=FallbackStrategy.CACHED_RESPONSE,
                priority=2,
                config={"cache_ttl": 3600}
            ),
            FallbackRule(
                trigger_condition="timeout",
                strategy=FallbackStrategy.MOCK_RESPONSE,
                priority=3,
                config={"response_template": "I apologize, but I'm experiencing technical difficulties. Please try again later."}
            ),
            FallbackRule(
                trigger_condition="circuit_breaker_open",
                strategy=FallbackStrategy.GRACEFUL_DEGRADATION,
                priority=4,
                config={"degraded_response": "Service temporarily unavailable. Limited functionality active."}
            )
        ]
    
    async def handle_model_unavailable(self, model_id: str, request: GenerationRequest) -> Optional[GenerationResponse]:
        """
        Handle case where requested model is unavailable.
        
        Args:
            model_id: ID of the unavailable model
            request: Original generation request
            
        Returns:
            Optional[GenerationResponse]: Fallback response if available
        """
        logger.warning(f"Model {model_id} unavailable, attempting fallback")
        
        # Update model health
        self._update_model_health(model_id, "unavailable")
        
        # Find applicable fallback rules
        applicable_rules = [
            rule for rule in self.fallback_rules
            if rule.trigger_condition == "model_unavailable" and rule.enabled
        ]
        
        # Sort by priority
        applicable_rules.sort(key=lambda r: r.priority)
        
        for rule in applicable_rules:
            try:
                response = await self._execute_fallback_strategy(rule, model_id, request)
                if response:
                    logger.info(f"Fallback successful using strategy: {rule.strategy.value}")
                    return response
            except Exception as e:
                logger.error(f"Fallback strategy {rule.strategy.value} failed: {e}")
                continue
        
        logger.error(f"All fallback strategies failed for model {model_id}")
        return None
    
    async def handle_generation_error(self, model_id: str, request: GenerationRequest, error: str) -> Optional[GenerationResponse]:
        """
        Handle generation errors with fallback strategies.
        
        Args:
            model_id: ID of the model that failed
            request: Original generation request
            error: Error message
            
        Returns:
            Optional[GenerationResponse]: Fallback response if available
        """
        logger.warning(f"Generation error for model {model_id}: {error}")
        
        # Update model health and circuit breaker
        self._update_model_health(model_id, "error", error)
        self._update_circuit_breaker(model_id, success=False)
        
        # Check if circuit breaker should open
        if self._should_open_circuit_breaker(model_id):
            self._open_circuit_breaker(model_id)
            return await self.handle_circuit_breaker_open(model_id, request)
        
        # Find applicable fallback rules
        applicable_rules = [
            rule for rule in self.fallback_rules
            if rule.trigger_condition == "generation_error" and rule.enabled
        ]
        
        # Sort by priority
        applicable_rules.sort(key=lambda r: r.priority)
        
        for rule in applicable_rules:
            try:
                response = await self._execute_fallback_strategy(rule, model_id, request, error)
                if response:
                    logger.info(f"Error fallback successful using strategy: {rule.strategy.value}")
                    return response
            except Exception as e:
                logger.error(f"Error fallback strategy {rule.strategy.value} failed: {e}")
                continue
        
        return None
    
    async def handle_circuit_breaker_open(self, model_id: str, request: GenerationRequest) -> Optional[GenerationResponse]:
        """
        Handle requests when circuit breaker is open.
        
        Args:
            model_id: ID of the model with open circuit breaker
            request: Original generation request
            
        Returns:
            Optional[GenerationResponse]: Fallback response
        """
        logger.warning(f"Circuit breaker open for model {model_id}")
        
        # Find circuit breaker fallback rules
        applicable_rules = [
            rule for rule in self.fallback_rules
            if rule.trigger_condition == "circuit_breaker_open" and rule.enabled
        ]
        
        for rule in applicable_rules:
            try:
                response = await self._execute_fallback_strategy(rule, model_id, request)
                if response:
                    return response
            except Exception as e:
                logger.error(f"Circuit breaker fallback failed: {e}")
                continue
        
        return None
    
    async def _execute_fallback_strategy(self, rule: FallbackRule, model_id: str, 
                                       request: GenerationRequest, error: Optional[str] = None) -> Optional[GenerationResponse]:
        """Execute a specific fallback strategy."""
        start_time = time.time()
        
        if rule.strategy == FallbackStrategy.ALTERNATIVE_MODEL:
            return await self._try_alternative_model(rule.config, request)
        
        elif rule.strategy == FallbackStrategy.MOCK_RESPONSE:
            return self._generate_mock_response(rule.config, request, start_time)
        
        elif rule.strategy == FallbackStrategy.CACHED_RESPONSE:
            return self._get_cached_response(request, start_time)
        
        elif rule.strategy == FallbackStrategy.EXTERNAL_API:
            return await self._try_external_api(rule.config, request, start_time)
        
        elif rule.strategy == FallbackStrategy.GRACEFUL_DEGRADATION:
            return self._generate_degraded_response(rule.config, request, start_time)
        
        return None
    
    async def _try_alternative_model(self, config: Dict[str, Any], request: GenerationRequest) -> Optional[GenerationResponse]:
        """Try alternative models as fallback."""
        alternative_models = config.get("alternative_models", [])
        
        for alt_model in alternative_models:
            try:
                # This would need to be injected or accessed through a service locator
                # For now, return a placeholder response
                logger.info(f"Would try alternative model: {alt_model}")
                return GenerationResponse(
                    content=f"Response from alternative model {alt_model}: {request.prompt[:100]}...",
                    model_used=alt_model,
                    status="completed",
                    response_time=1.0,
                    fallback_used=True
                )
            except Exception as e:
                logger.error(f"Alternative model {alt_model} failed: {e}")
                continue
        
        return None
    
    def _generate_mock_response(self, config: Dict[str, Any], request: GenerationRequest, start_time: float) -> GenerationResponse:
        """Generate a mock response as fallback."""
        template = config.get("response_template", "I apologize, but I'm currently unable to process your request.")
        
        if request.task_type == "code_generation":
            content = f'''# Mock code generation for: {request.prompt[:50]}...
def mock_function():
    """
    This is a mock implementation generated as a fallback.
    Please try again later for a proper AI-generated response.
    """
    return "Mock implementation"

# TODO: Replace with actual implementation
'''
        else:
            content = f"{template}\n\nYour request: {request.prompt[:100]}..."
        
        return GenerationResponse(
            content=content,
            model_used="mock_fallback",
            status="completed",
            response_time=time.time() - start_time,
            fallback_used=True
        )
    
    def _get_cached_response(self, request: GenerationRequest, start_time: float) -> Optional[GenerationResponse]:
        """Get cached response if available."""
        cache_key = self._generate_cache_key(request)
        
        if cache_key in self.response_cache:
            cached_response = self.response_cache[cache_key]
            # Update response time and mark as cached
            cached_response.response_time = time.time() - start_time
            cached_response.fallback_used = True
            cached_response.status = "cached_fallback"
            logger.info("Returning cached response as fallback")
            return cached_response
        
        return None
    
    async def _try_external_api(self, config: Dict[str, Any], request: GenerationRequest, start_time: float) -> Optional[GenerationResponse]:
        """Try external API as fallback."""
        # Placeholder for external API integration
        logger.info("Would try external API fallback")
        return None
    
    def _generate_degraded_response(self, config: Dict[str, Any], request: GenerationRequest, start_time: float) -> GenerationResponse:
        """Generate a degraded response when service is limited."""
        degraded_message = config.get("degraded_response", "Service operating in degraded mode.")
        
        return GenerationResponse(
            content=f"{degraded_message}\n\nLimited response for: {request.prompt[:100]}...",
            model_used="degraded_service",
            status="degraded",
            response_time=time.time() - start_time,
            fallback_used=True
        )
    
    def _update_model_health(self, model_id: str, status: str, error: Optional[str] = None):
        """Update model health tracking."""
        if model_id not in self.model_health:
            self.model_health[model_id] = {
                "status": "unknown",
                "last_error": None,
                "error_count": 0,
                "last_success": None,
                "consecutive_failures": 0
            }
        
        health = self.model_health[model_id]
        health["status"] = status
        
        if status == "error":
            health["last_error"] = error
            health["error_count"] += 1
            health["consecutive_failures"] += 1
        elif status == "success":
            health["last_success"] = time.time()
            health["consecutive_failures"] = 0
    
    def _update_circuit_breaker(self, model_id: str, success: bool):
        """Update circuit breaker state."""
        if model_id not in self.circuit_breakers:
            self.circuit_breakers[model_id] = {
                "state": "closed",  # closed, open, half_open
                "failure_count": 0,
                "last_failure_time": None,
                "success_count": 0,
                "failure_threshold": 5,
                "timeout": 60  # seconds
            }
        
        breaker = self.circuit_breakers[model_id]
        
        if success:
            breaker["success_count"] += 1
            breaker["failure_count"] = 0
            if breaker["state"] == "half_open" and breaker["success_count"] >= 3:
                breaker["state"] = "closed"
                logger.info(f"Circuit breaker closed for model {model_id}")
        else:
            breaker["failure_count"] += 1
            breaker["last_failure_time"] = time.time()
            breaker["success_count"] = 0
    
    def _should_open_circuit_breaker(self, model_id: str) -> bool:
        """Check if circuit breaker should open."""
        if model_id not in self.circuit_breakers:
            return False
        
        breaker = self.circuit_breakers[model_id]
        return (breaker["state"] == "closed" and 
                breaker["failure_count"] >= breaker["failure_threshold"])
    
    def _open_circuit_breaker(self, model_id: str):
        """Open circuit breaker for a model."""
        if model_id in self.circuit_breakers:
            self.circuit_breakers[model_id]["state"] = "open"
            logger.warning(f"Circuit breaker opened for model {model_id}")
    
    def _generate_cache_key(self, request: GenerationRequest) -> str:
        """Generate cache key for request."""
        return f"{request.prompt[:100]}_{request.max_tokens}_{request.temperature}"
    
    def cache_response(self, request: GenerationRequest, response: GenerationResponse):
        """Cache a successful response."""
        cache_key = self._generate_cache_key(request)
        self.response_cache[cache_key] = response
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all models."""
        return {
            "model_health": self.model_health.copy(),
            "circuit_breakers": self.circuit_breakers.copy(),
            "cache_size": len(self.response_cache)
        }