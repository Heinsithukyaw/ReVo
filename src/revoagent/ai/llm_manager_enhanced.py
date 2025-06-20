"""
Enhanced LLM Manager - Main entry point for all LLM operations

This module integrates the new fallback system for LLM operations.
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
from .cpu_optimized_deepseek_enhanced import CPUOptimizedDeepSeekEnhanced
from .llm_fallback_manager import LLMFallbackManager, llm_fallback_manager

# Configure logging
logger = logging.getLogger(__name__)

class LLMManagerEnhanced:
    """
    Enhanced centralized manager for all LLM interactions with fallback support.
    
    This class extends the original LLM Manager to include:
    1. Integrated local + fallback model system
    2. Intelligent model selection based on request content
    3. Resource-aware model routing
    """
    
    def __init__(self):
        self.model_manager = model_manager
        self.llm_bridge = llm_bridge
        self.cpu_optimized = None
        self.fallback_manager = llm_fallback_manager
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
            "fallback_requests": 0,
            "average_latency": 0.0,
            "last_error": None,
            "last_request_time": None
        }
    
    async def initialize(self, config_path: Optional[str] = None) -> bool:
        """Initialize all LLM subsystems including the fallback system."""
        try:
            # Load configuration
            await self._load_config(config_path)
            
            # Initialize all subsystems
            await self._initialize_subsystems()
            
            # Discover available models
            await self._discover_models()
            
            self.initialized = True
            logger.info(f"Enhanced LLM Manager initialized with {len(self.available_models)} models")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Enhanced LLM Manager: {e}")
            return False
    
    async def _load_config(self, config_path: Optional[str] = None) -> None:
        """Load configuration from file or environment variables."""
        try:
            # Default config
            self.config = {
                "llm": {
                    "default_model": "deepseek-r1",
                    "fallback_model": "llama-3.2-8b",
                    "providers": {
                        "deepseek": {"enabled": True, "api_key": os.getenv('DEEPSEEK_API_KEY')},
                        "openai": {"enabled": False, "api_key": os.getenv('OPENAI_API_KEY')},
                        "anthropic": {"enabled": False, "api_key": os.getenv('ANTHROPIC_API_KEY')},
                        "gemini": {"enabled": False, "api_key": os.getenv('GEMINI_API_KEY')}
                    },
                    "use_fallback_system": True
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
        """Initialize all LLM subsystems including fallback manager."""
        initialization_tasks = []
        
        # Initialize LLM Bridge for API-based models
        initialization_tasks.append(self.llm_bridge.initialize())
        
        # Initialize Fallback Manager
        initialization_tasks.append(self.fallback_manager.initialize())
        
        # Initialize CPU-optimized model with enhanced version
        self.cpu_optimized = CPUOptimizedDeepSeekEnhanced()
        
        # Configure the CPU model based on settings
        # If GGUF models are enabled in fallback config, use that type
        if self.fallback_manager.config.get("local_models", {}).get("deepseek_r1_gguf", {}).get("enabled", False):
            model_path = self.fallback_manager.config.get("local_models", {}).get("deepseek_r1_gguf", {}).get("path")
            if model_path and os.path.exists(model_path):
                initialization_tasks.append(self.cpu_optimized.load(model_path=model_path, model_type="gguf"))
            else:
                initialization_tasks.append(self.cpu_optimized.load())  # Default fallback
        else:
            initialization_tasks.append(self.cpu_optimized.load())  # Default template-based
        
        # Wait for all initializations to complete
        await asyncio.gather(*initialization_tasks, return_exceptions=True)
        
        logger.info("All LLM subsystems initialized including fallback system")
    
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
        if self.cpu_optimized and self.cpu_optimized.is_loaded:
            model_type = self.cpu_optimized.model_type
            model_id = "deepseek-r1"
            
            self.available_models[model_id] = {
                "source": f"cpu-optimized-{model_type}",
                "provider": "deepseek",
                "status": "available"
            }
            logger.info(f"Added CPU-optimized model: {model_id} (type: {model_type})")
            
            # Add local GGUF models from fallback config
            for model_id, model_config in self.fallback_manager.local_models.items():
                self.available_models[model_id] = {
                    "source": "local-gguf",
                    "provider": model_id.split("_")[0] if "_" in model_id else "unknown",
                    "status": "available" if model_config.get("loaded", False) else "registered"
                }
        
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
        Generate a response using the specified or default model with fallback support.
        
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
        use_fallback = self.config["llm"].get("use_fallback_system", True)
        
        try:
            # Check if fallback system is enabled and configured
            if use_fallback and self.fallback_manager and self.fallback_manager.enabled:
                # Use fallback system for smart routing and handling
                logger.debug(f"Using fallback system with target model: {target_model}")
                
                # Let fallback manager select optimal model based on content/resources
                context = {"model": target_model, **kwargs}
                optimal_model = await self.fallback_manager.select_optimal_model(message, context)
                
                if optimal_model != target_model:
                    logger.info(f"Fallback manager selected optimal model: {optimal_model} (original: {target_model})")
                    target_model = optimal_model
                
                # Generate with fallback handling
                response, metadata = await self.fallback_manager.generate_with_fallback(
                    message, target_model, **kwargs
                )
                
                # Update stats
                if metadata.get("fallback_used", False):
                    self.stats["fallback_requests"] += 1
                    # Store the model that was actually used
                    target_model = metadata.get("model", target_model)
                
                # Update source-specific counters
                model_info = self.available_models.get(target_model, {})
                source = model_info.get("source", "unknown")
                if "cpu" in source:
                    self.stats["cpu_optimized_requests"] += 1
                elif source == "api":
                    self.stats["api_requests"] += 1
                elif source == "local":
                    self.stats["local_requests"] += 1
                
                # Update latency stats
                latency = metadata.get("latency", time.time() - start_time)
                self._update_stats(True, latency)
                
                return response
                
            else:
                # Legacy approach when fallback system is disabled
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
                
                if "cpu-optimized" in model_source:
                    # Use CPU-optimized model
                    logger.info(f"Using CPU-optimized model: {target_model}")
                    response = await self.cpu_optimized.generate_response(message, **kwargs)
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
                                response = await self.cpu_optimized.generate_response(message, **kwargs)
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
    
    async def generate_code(
        self, 
        request: Dict[str, Any], 
        model: Optional[str] = None, 
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate code with fallback support.
        
        Args:
            request: Code generation request with task_description, etc.
            model: Optional model to use, otherwise uses default
            **kwargs: Additional parameters for generation
            
        Returns:
            Dict containing generated code and metadata
        """
        start_time = time.time()
        self.stats["total_requests"] += 1
        self.stats["last_request_time"] = time.time()
        
        try:
            # Use default model if not specified
            target_model = model or self.config["llm"]["default_model"]
            use_fallback = self.config["llm"].get("use_fallback_system", True)
            
            # Convert request to message for routing purposes
            message = f"Generate {request.get('language', 'code')} for: {request.get('task_description', '')}"
            
            # Legacy approach when fallback system is disabled or not available
            if not use_fallback or not self.fallback_manager or not self.fallback_manager.enabled:
                # Use CPU-optimized model directly for code generation
                logger.info(f"Using CPU-optimized model for code generation")
                result = await self.cpu_optimized.generate_code(request)
                
                # Update stats
                self.stats["cpu_optimized_requests"] += 1
                latency = time.time() - start_time
                self._update_stats(True, latency)
                
                return result
            
            # With fallback system enabled, use smarter routing
            # Select optimal model for code generation based on content/resources
            context = {"model": target_model, "request_type": "code", **kwargs}
            optimal_model = await self.fallback_manager.select_optimal_model(message, context)
            
            if optimal_model != target_model:
                logger.info(f"Fallback manager selected optimal model: {optimal_model} for code generation")
            
            # Get model source to determine implementation approach
            model_info = self.available_models.get(optimal_model, {"source": "unknown"})
            model_source = model_info["source"]
            
            # For code generation, prioritize cpu-optimized implementation
            if "cpu" in model_source or model_source == "unknown":
                result = await self.cpu_optimized.generate_code(request)
                self.stats["cpu_optimized_requests"] += 1
            
            # If it's an API model known for code generation, use it
            elif model_source == "api" and "deepseek" in optimal_model:
                # Generate code via LLM bridge but format as code response
                response = await self.llm_bridge.generate_response(message, optimal_model, **kwargs)
                self.stats["api_requests"] += 1
                
                result = {
                    "generated_code": response,
                    "model_used": optimal_model,
                    "generation_time": f"{time.time() - start_time:.2f}s",
                    "quality_score": 92.0,  # DeepSeek API is generally good at code
                    "estimated_lines": len(response.split('\n')),
                    "status": "completed"
                }
            
            # Otherwise, fallback to CPU-optimized implementation
            else:
                result = await self.cpu_optimized.generate_code(request)
                self.stats["cpu_optimized_requests"] += 1
            
            # Update stats
            latency = time.time() - start_time
            self._update_stats(True, latency)
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating code: {e}")
            self.stats["last_error"] = str(e)
            self._update_stats(False, time.time() - start_time)
            
            # Return error result
            return {
                "error": str(e),
                "status": "failed",
                "model_used": model or self.config["llm"]["default_model"]
            }
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of all available models with metadata."""
        if not self.initialized:
            await self.initialize()
        
        models_list = []
        
        for model_id, info in self.available_models.items():
            model_data = {
                "id": model_id,
                "name": model_id.replace("-", " ").replace("_", " ").title(),
                "provider": info.get("provider", "unknown"),
                "source": info.get("source", "unknown"),
                "status": info.get("status", "unknown"),
                "cost_per_token": self._get_cost_per_token(model_id),
                "features": self._get_model_features(model_id, info),
            }
            models_list.append(model_data)
        
        return models_list
    
    def _get_model_features(self, model_id: str, info: Dict[str, Any]) -> List[str]:
        """Get features supported by a specific model."""
        features = []
        
        # Add features based on model source
        source = info.get("source", "")
        
        if "local" in source or "cpu" in source:
            features.append("local_inference")
            features.append("offline_capable")
        
        if "api" in source:
            features.append("cloud_inference")
            
        # Add features based on known capabilities
        if "deepseek" in model_id.lower():
            features.append("code_generation")
            
        if "llama" in model_id.lower() and "70b" in model_id.lower():
            features.append("high_quality")
            
        if "gpt-4" in model_id.lower():
            features.append("high_quality")
        
        # Add fallback feature if model is part of fallback chain
        if self.fallback_manager and self.fallback_manager.enabled:
            try:
                fallback_chain = self.fallback_manager.get_fallback_chain("dummy-model")
                if model_id in fallback_chain:
                    features.append("fallback_capable")
            except:
                pass
        
        return features
    
    def _get_cost_per_token(self, model_id: str) -> float:
        """Get approximate cost per token for a model."""
        model_id = model_id.lower()
        
        # Free for local models
        if model_id in self.available_models:
            source = self.available_models[model_id].get("source", "")
            if "local" in source or "cpu" in source:
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
                cpu_health = self.cpu_optimized.get_status()
                health["subsystems"]["cpu_optimized"] = cpu_health
            except Exception as e:
                health["subsystems"]["cpu_optimized"] = {"status": "error", "error": str(e)}
        
        # Get fallback system health
        if self.fallback_manager:
            try:
                fallback_stats = self.fallback_manager.get_fallback_stats()
                health["subsystems"]["fallback"] = {
                    "status": "healthy" if self.fallback_manager.enabled else "disabled",
                    "stats": fallback_stats
                }
            except Exception as e:
                health["subsystems"]["fallback"] = {"status": "error", "error": str(e)}
        
        # Determine overall health
        healthy_subsystems = sum(1 for sys in health["subsystems"].values() 
                              if isinstance(sys, dict) and sys.get("status") in ["healthy", "active", "loaded"])
        
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
llm_manager_enhanced = LLMManagerEnhanced()