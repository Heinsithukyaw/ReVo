"""
LLM Fallback Manager

Provides intelligent fallback capabilities between local and API-based models.
"""

import os
import logging
import asyncio
import time
import yaml
import psutil
import re
from typing import Dict, List, Any, Optional, Tuple, Union
from enum import Enum
from dataclasses import dataclass
from pathlib import Path

# Internal imports
from .model_manager import model_manager
from .llm_bridge import llm_bridge
from .cpu_optimized_deepseek import CPUOptimizedDeepSeek

logger = logging.getLogger(__name__)

class FallbackReason(Enum):
    """Reasons for fallback to occur"""
    API_ERROR = "api_error"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    CONTENT_POLICY = "content_policy"
    LOW_RESOURCES = "low_resources"
    MANUAL_OVERRIDE = "manual_override"
    COST_LIMIT = "cost_limit"
    CONTENT_BASED = "content_based"
    SYSTEM_ERROR = "system_error"

@dataclass
class FallbackEvent:
    """Record of a fallback event"""
    timestamp: float
    original_model: str
    fallback_model: str
    reason: FallbackReason
    message_hash: str  # Hash of the user message for privacy
    success: bool
    latency: Optional[float] = None
    error_message: Optional[str] = None

class LLMFallbackManager:
    """
    Manages fallbacks between different LLM models.
    
    This class provides:
    1. Intelligent selection of fallback models
    2. Automatic switching based on errors or timeouts
    3. Content-based routing to appropriate models
    4. Cost and resource-aware model selection
    """
    
    def __init__(self):
        self.config = {}
        self.local_models = {}
        self.api_fallbacks = {}
        self.fallback_events = []
        self.enabled = False
        self.routing_rules = {}
        
        # Reference to model subsystems
        self.model_manager = model_manager
        self.llm_bridge = llm_bridge
        self.cpu_optimized = None
        
        # Optimal model selection cache
        self._model_performance_cache = {}
    
    async def initialize(self, config_path: Optional[str] = None) -> bool:
        """Initialize the fallback system."""
        try:
            # Load configuration
            await self._load_config(config_path)
            
            # Create CPU-optimized model for local fallback
            self.cpu_optimized = CPUOptimizedDeepSeek()
            
            # Initialize local models
            if self.config.get("local_models", {}):
                for model_id, model_config in self.config["local_models"].items():
                    if model_config.get("enabled", False):
                        await self._initialize_local_model(model_id, model_config)
            
            # Cache API fallbacks for quick access
            if self.config.get("api_fallbacks", {}):
                # Primary provider
                if "primary" in self.config["api_fallbacks"]:
                    provider = self.config["api_fallbacks"]["primary"]
                    if provider.get("enabled", False):
                        self.api_fallbacks["primary"] = provider
                
                # Secondary providers
                if "secondary" in self.config["api_fallbacks"]:
                    enabled_secondaries = [
                        provider for provider in self.config["api_fallbacks"]["secondary"]
                        if provider.get("enabled", False)
                    ]
                    # Sort by priority
                    enabled_secondaries.sort(key=lambda p: p.get("priority", 999))
                    self.api_fallbacks["secondary"] = enabled_secondaries
            
            # Set enabled status
            self.enabled = self.config.get("fallback_system", {}).get("enabled", True)
            
            # Cache routing rules
            if "routing_rules" in self.config:
                self.routing_rules = self.config["routing_rules"]
            
            logger.info(f"LLM Fallback Manager initialized. Enabled: {self.enabled}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM Fallback Manager: {e}")
            return False
    
    async def _load_config(self, config_path: Optional[str] = None) -> None:
        """Load fallback configuration."""
        try:
            # Default config locations
            config_locations = [
                config_path,
                "config/fallback_config.yaml",
                "fallback_config.yaml"
            ]
            
            for location in config_locations:
                if location and Path(location).exists():
                    try:
                        with open(location, 'r') as f:
                            self.config = yaml.safe_load(f)
                            logger.info(f"Loaded fallback config from {location}")
                            return
                    except Exception as e:
                        logger.warning(f"Error loading fallback config from {location}: {e}")
            
            # If no config found, use minimal default configuration
            self.config = {
                "fallback_system": {
                    "enabled": True,
                    "auto_switch": True,
                    "max_retries": 3
                },
                "local_models": {
                    "cpu_optimized_deepseek": {
                        "enabled": True
                    }
                },
                "behavior": {
                    "selection_strategy": "sequential"
                }
            }
            logger.warning("Using default fallback configuration")
            
        except Exception as e:
            logger.error(f"Error loading fallback config: {e}")
            # Set minimal default config
            self.config = {"fallback_system": {"enabled": False}}
    
    async def _initialize_local_model(self, model_id: str, model_config: Dict) -> bool:
        """Initialize a local model for fallback."""
        try:
            # Check resource requirements
            has_resources = self._check_system_resources(model_config)
            if not has_resources:
                logger.warning(f"Insufficient resources for local model {model_id}")
                return False
            
            # Handle auto-download if configured
            if model_config.get("auto_download", False):
                model_path = model_config.get("path")
                if model_path and not Path(model_path).exists():
                    logger.info(f"Model file not found at {model_path}, will trigger download")
                    # Signal that we need to download when first used
                    model_config["needs_download"] = True
            
            # Register the model with local_models
            self.local_models[model_id] = {
                "config": model_config,
                "loaded": False,
                "instance": None
            }
            
            logger.info(f"Registered local model {model_id} for fallback")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize local model {model_id}: {e}")
            return False
    
    def _check_system_resources(self, model_config: Dict) -> bool:
        """Check if system has sufficient resources for this model."""
        try:
            # Check RAM requirements
            min_ram_gb = model_config.get("min_ram_gb", 0)
            if min_ram_gb > 0:
                available_ram_gb = psutil.virtual_memory().available / (1024**3)
                if available_ram_gb < min_ram_gb:
                    logger.warning(f"Available RAM ({available_ram_gb:.1f} GB) below minimum requirement ({min_ram_gb} GB)")
                    return False
            
            # Always return True for now - we want to register models even if resources
            # are constrained, because resource situation might change
            return True
            
        except Exception as e:
            logger.error(f"Error checking system resources: {e}")
            return True  # Default to True in case of error
    
    async def select_optimal_model(self, message: str, context: Dict[str, Any]) -> str:
        """
        Select optimal model based on message content, system resources, and rules.
        
        Args:
            message: User message
            context: Request context with additional info
            
        Returns:
            model_id: ID of the selected model
        """
        if not self.enabled:
            return context.get("model", "")
        
        try:
            original_model = context.get("model", "")
            
            # Check if we're in a low memory situation
            low_memory_mode = self._check_low_memory_mode()
            
            # Content-based routing
            if "content_based" in self.routing_rules:
                for rule in self.routing_rules.get("content_based", []):
                    pattern = rule.get("pattern", "")
                    if pattern and re.search(pattern, message, re.IGNORECASE):
                        preferred_models = rule.get("preferred_models", [])
                        if preferred_models:
                            # Return first available preferred model
                            for model in preferred_models:
                                if await self._is_model_available(model):
                                    return model
            
            # Resource-based routing in low memory mode
            if low_memory_mode and "resource_based" in self.routing_rules:
                low_mem_config = self.routing_rules.get("resource_based", {}).get("low_memory", {})
                preferred_models = low_mem_config.get("preferred_models", [])
                if preferred_models:
                    # Return first available preferred model
                    for model in preferred_models:
                        if await self._is_model_available(model):
                            return model
            
            # If we couldn't find a special routing rule match, return the original model
            return original_model
            
        except Exception as e:
            logger.error(f"Error selecting optimal model: {e}")
            return context.get("model", "")
    
    async def _is_model_available(self, model_id: str) -> bool:
        """Check if a model is available (either local or API)."""
        # Check local models first
        if model_id in self.local_models:
            return True
        
        # Check API models via llm_bridge
        api_models = await self.llm_bridge.get_available_models()
        if model_id in api_models:
            return True
            
        # Check model_manager
        try:
            model_info = self.model_manager.get_model_info(model_id)
            if model_info and model_info.status.name != "ERROR":
                return True
        except:
            pass
            
        return False
    
    def _check_low_memory_mode(self) -> bool:
        """Check if the system is in a low memory situation."""
        try:
            mem = psutil.virtual_memory()
            # Consider low memory if less than 25% available
            return mem.percent > 75
        except:
            return False
    
    async def get_fallback_chain(self, original_model: str) -> List[str]:
        """
        Get a prioritized list of fallback models for a given original model.
        
        Args:
            original_model: The original model that might need fallback
            
        Returns:
            List of model IDs in fallback priority order
        """
        fallback_chain = []
        
        try:
            # If original is a local model, try API models first
            if original_model in self.local_models:
                # Add primary API fallback if configured
                if "primary" in self.api_fallbacks:
                    primary = self.api_fallbacks["primary"]
                    fallback_chain.append(primary.get("model_name", ""))
                
                # Add secondary API fallbacks
                for provider in self.api_fallbacks.get("secondary", []):
                    fallback_chain.append(provider.get("model_name", ""))
                
                # Add other local models
                for model_id in self.local_models:
                    if model_id != original_model:
                        fallback_chain.append(model_id)
            
            # If original is an API model, try other API models first, then local
            else:
                # Add other API models
                if "primary" in self.api_fallbacks:
                    primary_name = self.api_fallbacks["primary"].get("model_name", "")
                    if primary_name != original_model:
                        fallback_chain.append(primary_name)
                
                for provider in self.api_fallbacks.get("secondary", []):
                    model_name = provider.get("model_name", "")
                    if model_name != original_model:
                        fallback_chain.append(model_name)
                
                # Add local models
                for model_id in self.local_models:
                    fallback_chain.append(model_id)
            
            # Add CPU-optimized as last resort if available
            fallback_chain.append("deepseek-r1")
            
        except Exception as e:
            logger.error(f"Error building fallback chain: {e}")
            # Return a basic fallback with CPU-optimized
            fallback_chain = ["deepseek-r1"]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_chain = [x for x in fallback_chain if not (x in seen or seen.add(x))]
        
        return unique_chain
    
    async def generate_with_fallback(
        self,
        message: str,
        model: Optional[str] = None,
        **kwargs
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate a response with automatic fallback if needed.
        
        Args:
            message: Input message
            model: Optional model to use, otherwise uses default
            **kwargs: Additional parameters for generation
            
        Returns:
            Tuple of (response_text, metadata)
        """
        if not self.enabled:
            # If fallback system is disabled, just pass through to llm_bridge
            response = await self.llm_bridge.generate_response(message, model, **kwargs)
            return response, {"model": model, "fallback_used": False}
        
        context = {
            "model": model,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1000),
            "original_request_time": time.time()
        }
        
        # Select best model based on content and resources
        optimal_model = await self.select_optimal_model(message, context)
        if optimal_model != model:
            logger.info(f"Optimal model selected: {optimal_model} (original: {model})")
            model = optimal_model
            context["model"] = model
            context["model_selection"] = "content_based"
        
        # Get fallback chain for this model
        fallback_chain = await self.get_fallback_chain(model)
        logger.debug(f"Fallback chain for {model}: {fallback_chain}")
        
        # Try original model first
        try:
            original_start = time.time()
            response = await self._try_generate_with_model(message, model, **kwargs)
            original_latency = time.time() - original_start
            
            return response, {
                "model": model,
                "fallback_used": False,
                "latency": original_latency
            }
            
        except Exception as primary_error:
            logger.warning(f"Primary model {model} failed: {primary_error}")
            
            # Record fallback event
            event = FallbackEvent(
                timestamp=time.time(),
                original_model=model,
                fallback_model="",  # Will be set in the loop
                reason=self._determine_fallback_reason(str(primary_error)),
                message_hash=str(hash(message))[:10],
                success=False,
                error_message=str(primary_error)
            )
            
            # Try each fallback model in sequence
            for i, fallback_model in enumerate(fallback_chain):
                try:
                    logger.info(f"Trying fallback model: {fallback_model} ({i+1}/{len(fallback_chain)})")
                    event.fallback_model = fallback_model
                    
                    fallback_start = time.time()
                    response = await self._try_generate_with_model(message, fallback_model, **kwargs)
                    fallback_latency = time.time() - fallback_start
                    
                    # Record successful fallback
                    event.success = True
                    event.latency = fallback_latency
                    self.fallback_events.append(event)
                    
                    return response, {
                        "model": fallback_model,
                        "original_model": model,
                        "fallback_used": True,
                        "fallback_reason": event.reason.value,
                        "latency": fallback_latency
                    }
                    
                except Exception as fallback_error:
                    logger.warning(f"Fallback model {fallback_model} failed: {fallback_error}")
                    
                    # Try next fallback model
                    continue
            
            # If all fallbacks failed, record the event and raise error
            event.success = False
            self.fallback_events.append(event)
            
            # Get fallback behavior configuration
            persistent_failure_strategy = self.config.get("behavior", {}).get(
                "persistent_failure_strategy", "degrade"
            )
            
            if persistent_failure_strategy == "degrade":
                # Return a degraded response
                return (
                    "I'm currently experiencing technical difficulties. "
                    "Please try again later or rephrase your request."
                ), {
                        "model": "degraded",
                        "original_model": model,
                        "fallback_used": True,
                        "fallback_success": False,
                        "error": str(primary_error)
                    }
            else:
                # Re-raise the original error
                raise primary_error
    
    async def _try_generate_with_model(self, message: str, model: str, **kwargs) -> str:
        """Attempt to generate a response with a specific model."""
        # Set timeout from config
        timeout = self.config.get("fallback_system", {}).get("timeout", 30)
        
        # Check if this is a local model
        if model in self.local_models:
            # TODO: Implement local model generation logic
            return f"Generated from local model {model}: {message[:20]}..."
        
        # Handle CPU-optimized DeepSeek specially
        if model == "deepseek-r1" and self.cpu_optimized:
            try:
                # Make sure model is loaded
                if not self.cpu_optimized.is_loaded:
                    await self.cpu_optimized.load()
                
                # Generate with timeout
                result = await asyncio.wait_for(
                    self.cpu_optimized.generate_code({"task_description": message}),
                    timeout=timeout
                )
                return result.get("generated_code", "")
            except asyncio.TimeoutError:
                raise TimeoutError(f"CPU-optimized model timed out after {timeout}s")
        
        # Default to LLM Bridge for API models
        try:
            # Generate with timeout
            response = await asyncio.wait_for(
                self.llm_bridge.generate_response(message, model, **kwargs),
                timeout=timeout
            )
            return response
        except asyncio.TimeoutError:
            raise TimeoutError(f"API model timed out after {timeout}s")
    
    def _determine_fallback_reason(self, error_message: str) -> FallbackReason:
        """Determine fallback reason from error message."""
        error_lower = error_message.lower()
        
        if "time" in error_lower and ("out" in error_lower or "exceed" in error_lower):
            return FallbackReason.TIMEOUT
        elif "rate" in error_lower and "limit" in error_lower:
            return FallbackReason.RATE_LIMIT
        elif any(word in error_lower for word in ["content", "policy", "moderation"]):
            return FallbackReason.CONTENT_POLICY
        elif any(word in error_lower for word in ["resource", "memory", "capacity"]):
            return FallbackReason.LOW_RESOURCES
        elif any(word in error_lower for word in ["cost", "billing", "quota"]):
            return FallbackReason.COST_LIMIT
        else:
            return FallbackReason.API_ERROR
    
    def get_fallback_stats(self) -> Dict[str, Any]:
        """Get statistics about fallback events."""
        if not self.fallback_events:
            return {"total_events": 0}
        
        # Count events by reason
        reason_counts = {}
        for event in self.fallback_events:
            reason = event.reason.value
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        
        # Count events by success/failure
        successes = sum(1 for event in self.fallback_events if event.success)
        failures = len(self.fallback_events) - successes
        
        # Average latency
        latencies = [event.latency for event in self.fallback_events if event.latency is not None]
        avg_latency = sum(latencies) / len(latencies) if latencies else None
        
        # Model counts
        original_models = {}
        fallback_models = {}
        for event in self.fallback_events:
            original_models[event.original_model] = original_models.get(event.original_model, 0) + 1
            fallback_models[event.fallback_model] = fallback_models.get(event.fallback_model, 0) + 1
        
        return {
            "total_events": len(self.fallback_events),
            "success_rate": successes / len(self.fallback_events) if self.fallback_events else 0,
            "successes": successes,
            "failures": failures,
            "reason_counts": reason_counts,
            "avg_latency": avg_latency,
            "original_models": original_models,
            "fallback_models": fallback_models,
            "last_event_time": self.fallback_events[-1].timestamp if self.fallback_events else None
        }

# Global instance
llm_fallback_manager = LLMFallbackManager()