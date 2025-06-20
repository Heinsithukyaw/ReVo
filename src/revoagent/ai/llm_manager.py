"""
LLM Manager - Main entry point for all LLM operations

This module provides a centralized interface for interacting with LLMs,
whether they're provided by local models or external APIs.
"""

import os
import logging
import asyncio
from typing import Dict, List, Any, Optional, Union
import yaml
import time

# Import LLM-related modules
from .model_manager import ModelManager, model_manager
from .llm_bridge import LLMBridge, llm_bridge
from .cpu_optimized_deepseek import CPUOptimizedDeepSeek

# Configure logging
logger = logging.getLogger(__name__)

class LLMManager:
    """
    Centralized manager for all LLM interactions.
    
    This class provides a unified interface to work with:
    1. Local models via ModelManager
    2. API-based models via LLMBridge
    3. CPU-optimized local models
    
    It handles automatic fallbacks, resource optimization, and
    intelligent routing of requests to the appropriate backend.
    """
    
    def __init__(self):
        self.model_manager = model_manager
        self.llm_bridge = llm_bridge
        self.cpu_optimized = None
        self.initialized = False
        self.config = {}
        
        # Track available models and their sources
        self.available_models = {}
        
        # Performance stats
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "local_requests": 0,
            "api_requests": 0,
            "cpu_optimized_requests": 0,
            "average_latency": 0.0,
            "last_error": None,
            "last_request_time": None
        }
    
    async def initialize(self, config_path: Optional[str] = None) -> bool:
        """Initialize all LLM subsystems."""
        try:
            # Load configuration
            await self._load_config(config_path)
            
            # Initialize all subsystems
            await self._initialize_subsystems()
            
            # Discover available models
            await self._discover_models()
            
            self.initialized = True
            logger.info(f"LLM Manager initialized with {len(self.available_models)} models")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM Manager: {e}")
            return False
    
    async def _load_config(self, config_path: Optional[str] = None) -> None:
        """Load configuration from file or environment variables."""
        try:
            # Default config
            self.config = {
                "llm": {
                    "default_model": "deepseek-r1",
                    "fallback_model": "llama-3.1-70b",
                    "providers": {
                        "deepseek": {"enabled": True, "api_key": os.getenv('DEEPSEEK_API_KEY')},
                        "openai": {"enabled": False, "api_key": os.getenv('OPENAI_API_KEY')},
                        "anthropic": {"enabled": False, "api_key": os.getenv('ANTHROPIC_API_KEY')},
                        "gemini": {"enabled": False, "api_key": os.getenv('GEMINI_API_KEY')}
                    }
                },
                "resources": {
                    "optimize_for_cpu": True,
                    "low_memory_mode": False
                }
            }
            
            # Try to load from YAML file
            config_locations = [
                config_path,
                "config/environment.yaml",
                "environment.yaml"
            ]
            
            for location in config_locations:
                if location and os.path.exists(location):
                    try:
                        with open(location, 'r') as f:
                            file_config = yaml.safe_load(f)
                            if file_config and isinstance(file_config, dict):
                                # Merge configurations
                                if "llm" in file_config:
                                    self.config["llm"].update(file_config["llm"])
                                if "resources" in file_config:
                                    self.config["resources"].update(file_config["resources"])
                                logger.info(f"Loaded config from {location}")
                                break
                    except Exception as e:
                        logger.warning(f"Error loading config from {location}: {e}")
            
        except Exception as e:
            logger.error(f"Config loading error: {e}")
    
    async def _initialize_subsystems(self) -> None:
        """Initialize all LLM subsystems."""
        initialization_tasks = []
        
        # Initialize LLM Bridge for API-based models
        initialization_tasks.append(self.llm_bridge.initialize())
        
        # Initialize CPU-optimized model if configured
        if self.config["resources"]["optimize_for_cpu"]:
            self.cpu_optimized = CPUOptimizedDeepSeek()
            initialization_tasks.append(self.cpu_optimized.load())
        
        # Wait for all initializations to complete
        await asyncio.gather(*initialization_tasks, return_exceptions=True)
        
        logger.info("All LLM subsystems initialized")
    
    async def _discover_models(self) -> None:
        """Discover all available models from all sources."""
        # Clear existing models
        self.available_models = {}
        
        # Get models from LLM Bridge (API-based)
        try:
            api_models = await self.llm_bridge.get_available_models()
            for model in api_models:
                self.available_models[model] = {
                    "source": "api",
                    "provider": self._detect_provider(model),
                    "status": "available"
                }
            logger.info(f"Discovered {len(api_models)} API-based models")
        except Exception as e:
            logger.error(f"Failed to discover API models: {e}")
        
        # Add CPU-optimized models
        if self.cpu_optimized and hasattr(self.cpu_optimized, "is_loaded") and self.cpu_optimized.is_loaded:
            self.available_models["deepseek-r1"] = {
                "source": "cpu-optimized",
                "provider": "deepseek",
                "status": "available"
            }
            logger.info("Added CPU-optimized DeepSeek R1 model")
        
        # Get models from ModelManager (local)
        try:
            model_info = self.model_manager.get_model_info()
            for model_id, info in model_info.items():
                self.available_models[model_id] = {
                    "source": "local",
                    "provider": info.type.value if hasattr(info, "type") else "unknown",
                    "status": info.status.value if hasattr(info, "status") else "unknown"
                }
            logger.info(f"Discovered {len(model_info)} local models")
        except Exception as e:
            logger.error(f"Failed to discover local models: {e}")
    
    def _detect_provider(self, model_name: str) -> str:
        """Detect the provider based on model name."""
        model_name = model_name.lower()
        if "deepseek" in model_name:
            return "deepseek"
        elif "llama" in model_name:
            return "llama"
        elif "gpt" in model_name:
            return "openai"
        elif "claude" in model_name:
            return "anthropic"
        elif "gemini" in model_name:
            return "gemini"
        return "unknown"
    
    async def generate_response(
        self, 
        message: str, 
        model: Optional[str] = None, 
        **kwargs
    ) -> str:
        """
        Generate a response using the specified or default model.
        
        Args:
            message: Input message
            model: Optional model to use, otherwise uses default
            **kwargs: Additional parameters for generation
            
        Returns:
            Generated response text
        """
        start_time = time.time()
        self.stats["total_requests"] += 1
        self.stats["last_request_time"] = time.time()
        
        # Use default model if not specified
        target_model = model or self.config["llm"]["default_model"]
        
        try:
            # Check if model is available
            if target_model not in self.available_models:
                logger.warning(f"Model {target_model} not available, using fallback")
                target_model = self.config["llm"]["fallback_model"]
                
                # If fallback also not available, use first available model
                if target_model not in self.available_models and self.available_models:
                    target_model = next(iter(self.available_models.keys()))
            
            # Get model source
            model_info = self.available_models.get(target_model, {"source": "unknown"})
            model_source = model_info["source"]
            
            # Generate using appropriate backend
            response = None
            
            if model_source == "cpu-optimized":
                # Use CPU-optimized model
                logger.info(f"Using CPU-optimized model: {target_model}")
                if hasattr(self.cpu_optimized, "generate_code"):
                    # For code generation
                    result = await self.cpu_optimized.generate_code({"task_description": message, **kwargs})
                    response = result.get("generated_code", "")
                else:
                    # Fallback to LLM Bridge
                    response = await self.llm_bridge.generate_response(message, target_model, **kwargs)
                
                self.stats["cpu_optimized_requests"] += 1
                
            elif model_source == "api":
                # Use LLM Bridge for API-based models
                logger.info(f"Using API-based model: {target_model}")
                response = await self.llm_bridge.generate_response(message, target_model, **kwargs)
                self.stats["api_requests"] += 1
                
            elif model_source == "local":
                # Use ModelManager for local models
                logger.info(f"Using local model: {target_model}")
                response = await self.model_manager.generate_text(message, target_model, **kwargs)
                self.stats["local_requests"] += 1
                
            else:
                # Unknown source, try all methods
                logger.warning(f"Unknown model source for {target_model}, trying all backends")
                
                # Try LLM Bridge first
                try:
                    response = await self.llm_bridge.generate_response(message, target_model, **kwargs)
                    self.stats["api_requests"] += 1
                except Exception as e:
                    logger.error(f"LLM Bridge error: {e}")
                    
                    # Try CPU-optimized next
                    if self.cpu_optimized:
                        try:
                            result = await self.cpu_optimized.generate_code({"task_description": message, **kwargs})
                            response = result.get("generated_code", "")
                            self.stats["cpu_optimized_requests"] += 1
                        except Exception as e2:
                            logger.error(f"CPU-optimized model error: {e2}")
                            
                            # Try ModelManager last
                            try:
                                response = await self.model_manager.generate_text(message, target_model, **kwargs)
                                self.stats["local_requests"] += 1
                            except Exception as e3:
                                logger.error(f"ModelManager error: {e3}")
                                response = f"Error: Failed to generate response with all backends. {str(e3)}"
            
            # Update stats
            latency = time.time() - start_time
            self._update_stats(True, latency)
            
            return response or f"No response generated from {target_model}"
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            self.stats["last_error"] = str(e)
            self._update_stats(False, time.time() - start_time)
            
            # Return error message
            return f"Error: {str(e)}"
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of all available models with metadata."""
        if not self.initialized:
            await self.initialize()
        
        models_list = []
        
        for model_id, info in self.available_models.items():
            model_data = {
                "id": model_id,
                "name": model_id.replace("-", " ").title(),
                "provider": info.get("provider", "unknown"),
                "source": info.get("source", "unknown"),
                "status": info.get("status", "unknown"),
                "cost_per_token": self._get_cost_per_token(model_id),
            }
            models_list.append(model_data)
        
        return models_list
    
    def _get_cost_per_token(self, model_id: str) -> float:
        """Get approximate cost per token for a model."""
        model_id = model_id.lower()
        
        # Free for local models
        if model_id in self.available_models and self.available_models[model_id].get("source") in ["local", "cpu-optimized"]:
            return 0.0
        
        # Approximate costs for API models
        if "gpt-4" in model_id:
            return 0.01
        elif "gpt-3.5" in model_id:
            return 0.002
        elif "claude-3-opus" in model_id:
            return 0.015
        elif "claude-3-sonnet" in model_id:
            return 0.008
        elif "claude-3-haiku" in model_id:
            return 0.002
        elif "deepseek" in model_id:
            return 0.0005
        elif "gemini" in model_id:
            return 0.0035
        
        return 0.001  # Default cost estimate
    
    async def get_health(self) -> Dict[str, Any]:
        """Get health status of all LLM systems."""
        if not self.initialized:
            return {"status": "not_initialized"}
        
        health = {
            "status": "healthy",
            "models_available": len(self.available_models),
            "stats": self.stats.copy(),
            "subsystems": {}
        }
        
        # Get API health
        try:
            api_health = await self.llm_bridge.health_check()
            health["subsystems"]["api"] = api_health
        except Exception as e:
            health["subsystems"]["api"] = {"status": "error", "error": str(e)}
        
        # Get CPU-optimized health
        if self.cpu_optimized:
            try:
                cpu_health = self.cpu_optimized.get_status() if hasattr(self.cpu_optimized, "get_status") else {"status": "unknown"}
                health["subsystems"]["cpu_optimized"] = cpu_health
            except Exception as e:
                health["subsystems"]["cpu_optimized"] = {"status": "error", "error": str(e)}
        
        # Determine overall health
        healthy_subsystems = sum(1 for sys in health["subsystems"].values() 
                              if sys.get("status") in ["healthy", "active", "loaded"])
        
        if healthy_subsystems == 0:
            health["status"] = "unhealthy"
        elif healthy_subsystems < len(health["subsystems"]):
            health["status"] = "degraded"
        
        return health
    
    def _update_stats(self, success: bool, latency: float) -> None:
        """Update performance statistics."""
        if success:
            self.stats["successful_requests"] += 1
        else:
            self.stats["failed_requests"] += 1
        
        # Update average latency
        total = self.stats["successful_requests"] + self.stats["failed_requests"]
        if total > 0:
            self.stats["average_latency"] = (
                (self.stats["average_latency"] * (total - 1) + latency) / total
            )

# Global instance
llm_manager = LLMManager()