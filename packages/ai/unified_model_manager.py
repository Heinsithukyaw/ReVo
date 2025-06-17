"""
Unified Model Manager

Orchestrates the focused AI services to provide a clean, unified interface.
This replaces the monolithic ModelManager with a service-oriented architecture.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

from .schemas import (
    ModelConfig, ModelInfo, ModelType, ModelStatus,
    GenerationRequest, GenerationResponse, ModelLoadRequest,
    ModelUnloadRequest, ModelSwitchRequest, SystemStatus
)
from .services import (
    ModelLoader, ResponseGenerator, MetricsCollector,
    FallbackManager, ResourceManager
)

logger = logging.getLogger(__name__)


class UnifiedModelManager:
    """
    Unified Model Manager using service-oriented architecture.
    
    This class orchestrates focused services to provide a clean interface
    for AI model management while maintaining separation of concerns.
    """
    
    def __init__(self):
        # Initialize focused services
        self.model_loader = ModelLoader()
        self.metrics_collector = MetricsCollector()
        self.fallback_manager = FallbackManager()
        self.resource_manager = ResourceManager()
        self.response_generator = ResponseGenerator(
            model_loader=self.model_loader,
            fallback_manager=self.fallback_manager
        )
        
        # Register cleanup callback with resource manager
        self.resource_manager.register_cleanup_callback(self._cleanup_unused_models)
        
        # Initialize default models
        self._initialize_default_models()
        
        # Background services will be started when first used
        self._background_services_started = False
    
    async def _start_background_services(self):
        """Start background services."""
        if self._background_services_started:
            return
            
        try:
            await self.resource_manager.start_monitoring(interval_seconds=30)
            self._background_services_started = True
            logger.info("Background services started successfully")
        except Exception as e:
            logger.error(f"Failed to start background services: {e}")
    
    def _initialize_default_models(self):
        """Initialize default model configurations."""
        # DeepSeek R1 0528
        deepseek_config = ModelConfig(
            model_id="deepseek-r1-0528",
            model_path="deepseek-ai/DeepSeek-R1-0528",
            model_type=ModelType.DEEPSEEK_R1,
            device="auto",
            max_length=4096,
            temperature=0.7,
            quantization="4bit"
        )
        
        deepseek_info = ModelInfo(
            id="deepseek-r1-0528",
            name="DeepSeek R1 0528",
            type=ModelType.DEEPSEEK_R1,
            size="70B",
            status=ModelStatus.UNLOADED,
            performance_score=94.0
        )
        
        self.model_loader.register_model_info("deepseek-r1-0528", deepseek_info)
        
        # Llama 3.2 8B
        llama_config = ModelConfig(
            model_id="llama-3.2-8b",
            model_path="meta-llama/Llama-3.2-8B-Instruct",
            model_type=ModelType.LLAMA,
            device="auto",
            max_length=8192,
            quantization="4bit"
        )
        
        llama_info = ModelInfo(
            id="llama-3.2-8b",
            name="Llama 3.2 8B",
            type=ModelType.LLAMA,
            size="8B",
            status=ModelStatus.UNLOADED,
            performance_score=78.0
        )
        
        self.model_loader.register_model_info("llama-3.2-8b", llama_info)
        
        logger.info("Default model configurations initialized")
    
    async def load_model(self, request: ModelLoadRequest) -> Dict[str, Any]:
        """
        Load a model with proper validation and resource checking.
        
        Args:
            request: Model load request with validation
            
        Returns:
            Dict containing load result and metadata
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Check resource availability
            available, reason = await self.resource_manager.check_resource_availability(
                required_memory_gb=4.0,  # Estimate based on model size
                required_gpu_memory_gb=8.0 if request.model_type in [ModelType.DEEPSEEK_R1, ModelType.LLAMA] else 0.0
            )
            
            if not available:
                return {
                    "success": False,
                    "error": f"Insufficient resources: {reason}",
                    "model_id": request.model_id
                }
            
            # Create model config
            config = ModelConfig(
                model_id=request.model_id,
                model_path=request.model_path,
                model_type=request.model_type,
                **(request.config or {})
            )
            
            # Record request start
            request_id = self.metrics_collector.record_request_start(request.model_id)
            
            # Load the model
            success = await self.model_loader.load_model(request.model_id, config)
            
            # Record completion
            response_time = asyncio.get_event_loop().time() - start_time
            self.metrics_collector.record_request_completion(
                request.model_id, response_time, 0, success
            )
            
            if success:
                # Set as active if no active model
                if not self.response_generator.get_active_model():
                    self.response_generator.set_active_model(request.model_id)
                
                return {
                    "success": True,
                    "model_id": request.model_id,
                    "response_time": response_time,
                    "message": f"Model {request.model_id} loaded successfully"
                }
            else:
                return {
                    "success": False,
                    "model_id": request.model_id,
                    "error": "Failed to load model",
                    "response_time": response_time
                }
                
        except Exception as e:
            logger.error(f"Error loading model {request.model_id}: {e}")
            return {
                "success": False,
                "model_id": request.model_id,
                "error": str(e)
            }
    
    async def unload_model(self, request: ModelUnloadRequest) -> Dict[str, Any]:
        """
        Unload a model with proper cleanup.
        
        Args:
            request: Model unload request
            
        Returns:
            Dict containing unload result
        """
        try:
            success = await self.model_loader.unload_model(request.model_id)
            
            if success:
                # Update active model if this was the active one
                if self.response_generator.get_active_model() == request.model_id:
                    # Try to set another loaded model as active
                    loaded_models = list(self.model_loader.get_loaded_models().keys())
                    if loaded_models:
                        self.response_generator.set_active_model(loaded_models[0])
                    else:
                        self.response_generator.set_active_model(None)
                
                return {
                    "success": True,
                    "model_id": request.model_id,
                    "message": f"Model {request.model_id} unloaded successfully"
                }
            else:
                return {
                    "success": False,
                    "model_id": request.model_id,
                    "error": "Failed to unload model"
                }
                
        except Exception as e:
            logger.error(f"Error unloading model {request.model_id}: {e}")
            return {
                "success": False,
                "model_id": request.model_id,
                "error": str(e)
            }
    
    async def switch_model(self, request: ModelSwitchRequest) -> Dict[str, Any]:
        """
        Switch to a different active model.
        
        Args:
            request: Model switch request
            
        Returns:
            Dict containing switch result
        """
        try:
            # Check if model is loaded
            if not self.model_loader.is_model_loaded(request.model_id):
                if request.load_if_needed:
                    # Try to load the model first
                    load_request = ModelLoadRequest(
                        model_id=request.model_id,
                        model_path=f"auto/{request.model_id}",  # Auto-detect path
                        model_type=ModelType.CUSTOM  # Will be determined during load
                    )
                    load_result = await self.load_model(load_request)
                    if not load_result["success"]:
                        return {
                            "success": False,
                            "model_id": request.model_id,
                            "error": f"Failed to load model: {load_result.get('error', 'Unknown error')}"
                        }
                else:
                    return {
                        "success": False,
                        "model_id": request.model_id,
                        "error": "Model not loaded and load_if_needed is False"
                    }
            
            # Switch to the model
            self.response_generator.set_active_model(request.model_id)
            
            return {
                "success": True,
                "model_id": request.model_id,
                "message": f"Switched to model {request.model_id}"
            }
            
        except Exception as e:
            logger.error(f"Error switching to model {request.model_id}: {e}")
            return {
                "success": False,
                "model_id": request.model_id,
                "error": str(e)
            }
    
    async def generate_text(self, request: GenerationRequest, model_id: Optional[str] = None) -> GenerationResponse:
        """
        Generate text using the AI models.
        
        Args:
            request: Validated generation request
            model_id: Optional specific model to use
            
        Returns:
            GenerationResponse with generated text and metadata
        """
        # Start background services if not already started
        await self._start_background_services()
        # Record request start
        target_model = model_id or self.response_generator.get_active_model() or "unknown"
        request_id = self.metrics_collector.record_request_start(target_model)
        
        try:
            # Generate response
            response = await self.response_generator.generate_text(request, model_id)
            
            # Record completion
            self.metrics_collector.record_request_completion(
                response.model_used,
                response.response_time,
                response.tokens_used or 0,
                response.status == "completed"
            )
            
            # Cache successful responses
            if response.status == "completed" and not response.fallback_used:
                self.fallback_manager.cache_response(request, response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            
            # Record failure
            self.metrics_collector.record_request_completion(
                target_model, 0.0, 0, False, str(e)
            )
            
            # Try fallback
            fallback_response = await self.fallback_manager.handle_generation_error(
                target_model, request, str(e)
            )
            
            return fallback_response or GenerationResponse(
                content="",
                model_used=target_model,
                status="error",
                response_time=0.0,
                error=str(e)
            )
    
    async def generate_code(self, request: GenerationRequest, model_id: Optional[str] = None) -> GenerationResponse:
        """
        Generate code using the AI models.
        
        Args:
            request: Code generation request
            model_id: Optional specific model to use
            
        Returns:
            GenerationResponse with generated code
        """
        # Ensure task type is set for code generation
        request.task_type = "code_generation"
        return await self.generate_text(request, model_id)
    
    def get_model_info(self, model_id: Optional[str] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Get information about models.
        
        Args:
            model_id: Optional specific model ID
            
        Returns:
            Model information
        """
        if model_id:
            info = self.model_loader.model_info.get(model_id)
            if info:
                return {
                    "id": info.id,
                    "name": info.name,
                    "type": info.type.value,
                    "size": info.size,
                    "status": info.status.value,
                    "memory_usage": info.memory_usage,
                    "gpu_memory": info.gpu_memory,
                    "performance_score": info.performance_score,
                    "last_used": info.last_used,
                    "error_message": info.error_message
                }
            return {}
        
        # Return all models
        return [
            {
                "id": info.id,
                "name": info.name,
                "type": info.type.value,
                "size": info.size,
                "status": info.status.value,
                "memory_usage": info.memory_usage,
                "gpu_memory": info.gpu_memory,
                "performance_score": info.performance_score,
                "last_used": info.last_used,
                "error_message": info.error_message
            }
            for info in self.model_loader.model_info.values()
        ]
    
    async def get_system_status(self) -> SystemStatus:
        """
        Get comprehensive system status.
        
        Returns:
            SystemStatus with health information
        """
        # Get metrics
        performance_summary = self.metrics_collector.get_performance_summary()
        resource_summary = self.resource_manager.get_resource_summary()
        alerts = self.metrics_collector.get_alerts()
        
        # Determine overall status
        error_rate = performance_summary.get("overall_error_rate", 0)
        memory_percent = resource_summary["current_usage"]["memory_percent"]
        
        if error_rate > 20 or memory_percent > 95:
            status = "critical"
        elif error_rate > 10 or memory_percent > 85:
            status = "degraded"
        else:
            status = "healthy"
        
        # Get model health
        model_health = []
        for model_id, info in self.model_loader.model_info.items():
            model_health.append({
                "model_id": model_id,
                "status": "healthy" if info.status == ModelStatus.LOADED else "unhealthy",
                "last_check": datetime.now(),
                "memory_usage_gb": info.memory_usage,
                "gpu_memory_gb": info.gpu_memory
            })
        
        return SystemStatus(
            status=status,
            timestamp=datetime.now(),
            active_models=len(self.model_loader.get_loaded_models()),
            total_requests=performance_summary.get("total_requests", 0),
            error_rate=error_rate,
            avg_response_time=performance_summary.get("average_response_time", 0),
            cpu_percent=resource_summary["current_usage"]["cpu_percent"],
            memory_percent=memory_percent,
            gpu_utilization=resource_summary["current_usage"]["gpu_utilization"],
            model_health=model_health,
            alerts=alerts
        )
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive metrics."""
        return {
            "performance": self.metrics_collector.get_performance_summary(),
            "resources": self.resource_manager.get_resource_summary(),
            "fallback_health": self.fallback_manager.get_health_status(),
            "response_generator": await self.response_generator.health_check()
        }
    
    async def optimize_resources(self) -> Dict[str, Any]:
        """Optimize system resources."""
        return await self.resource_manager.optimize_memory_usage()
    
    async def _cleanup_unused_models(self):
        """Cleanup callback for unused models."""
        try:
            # Get model usage metrics
            model_metrics = self.metrics_collector.get_model_metrics()
            
            # Find models that haven't been used recently
            unused_models = []
            for model_id in self.model_loader.get_loaded_models():
                metrics = model_metrics.get(model_id, {})
                if metrics.get("total_requests", 0) == 0:
                    unused_models.append(model_id)
            
            # Unload unused models (except active model)
            active_model = self.response_generator.get_active_model()
            for model_id in unused_models:
                if model_id != active_model:
                    await self.model_loader.unload_model(model_id)
                    logger.info(f"Unloaded unused model: {model_id}")
                    
        except Exception as e:
            logger.error(f"Error in cleanup callback: {e}")
    
    async def shutdown(self):
        """Gracefully shutdown the model manager."""
        logger.info("Shutting down Unified Model Manager")
        
        try:
            # Stop resource monitoring
            await self.resource_manager.stop_monitoring()
            
            # Unload all models
            for model_id in list(self.model_loader.get_loaded_models().keys()):
                await self.model_loader.unload_model(model_id)
            
            logger.info("Unified Model Manager shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


# Global instance
unified_model_manager = UnifiedModelManager()