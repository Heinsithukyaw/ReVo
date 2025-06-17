"""
Model Switching - Dynamic Model Selection and Switching

Intelligent model selection based on task requirements and resource availability.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from .model_registry import ModelRegistry, ModelInfo, ModelCapability
from .local_models import LocalModelManager

logger = logging.getLogger(__name__)


class SwitchingStrategy(Enum):
    """Model switching strategies."""
    PERFORMANCE = "performance"  # Prioritize best performance
    EFFICIENCY = "efficiency"    # Prioritize resource efficiency
    BALANCED = "balanced"        # Balance performance and efficiency
    COST = "cost"               # Prioritize lowest cost (local models)


@dataclass
class TaskRequirements:
    """Requirements for a specific task."""
    capability: ModelCapability
    complexity: str = "medium"  # low, medium, high
    max_response_time: Optional[float] = None
    quality_threshold: float = 0.8
    context_length: int = 2048


@dataclass
class ModelPerformanceMetrics:
    """Performance metrics for a model."""
    model_name: str
    avg_response_time: float
    success_rate: float
    quality_score: float
    resource_usage: Dict[str, float]
    last_updated: float


class ModelSwitcher:
    """Intelligent model switching based on task requirements and performance."""
    
    def __init__(self, 
                 model_manager: LocalModelManager,
                 model_registry: ModelRegistry,
                 strategy: SwitchingStrategy = SwitchingStrategy.BALANCED):
        self.model_manager = model_manager
        self.model_registry = model_registry
        self.strategy = strategy
        self.performance_metrics: Dict[str, ModelPerformanceMetrics] = {}
        self.task_history: List[Dict[str, Any]] = []
        self.model_preferences: Dict[ModelCapability, str] = {}
        
    async def select_model(self, task_requirements: TaskRequirements) -> Optional[str]:
        """Select the best model for a given task."""
        try:
            # Get available models with the required capability
            capable_models = self.model_registry.find_models_by_capability(
                task_requirements.capability
            )
            
            if not capable_models:
                logger.warning(f"No models found for capability: {task_requirements.capability}")
                return None
            
            # Filter by loaded models
            loaded_models = self.model_manager.get_available_models()
            available_models = [
                model for model in capable_models
                if model.name in loaded_models
            ]
            
            if not available_models:
                # Try to load a suitable model
                best_model = await self._find_best_unloaded_model(
                    capable_models, task_requirements
                )
                if best_model:
                    if await self._load_model_if_needed(best_model.name):
                        available_models = [best_model]
            
            if not available_models:
                logger.error("No suitable models available")
                return None
            
            # Select best model based on strategy
            selected_model = self._select_by_strategy(available_models, task_requirements)
            
            if selected_model:
                # Update preferences
                self.model_preferences[task_requirements.capability] = selected_model.name
                logger.info(f"Selected model {selected_model.name} for {task_requirements.capability}")
                return selected_model.name
            
            return None
            
        except Exception as e:
            logger.error(f"Error selecting model: {e}")
            return None
    
    def _select_by_strategy(self, 
                           models: List[ModelInfo], 
                           requirements: TaskRequirements) -> Optional[ModelInfo]:
        """Select model based on switching strategy."""
        if not models:
            return None
        
        if self.strategy == SwitchingStrategy.PERFORMANCE:
            return self._select_by_performance(models, requirements)
        elif self.strategy == SwitchingStrategy.EFFICIENCY:
            return self._select_by_efficiency(models, requirements)
        elif self.strategy == SwitchingStrategy.BALANCED:
            return self._select_balanced(models, requirements)
        elif self.strategy == SwitchingStrategy.COST:
            return self._select_by_cost(models, requirements)
        else:
            return models[0]  # Default to first available
    
    def _select_by_performance(self, 
                              models: List[ModelInfo], 
                              requirements: TaskRequirements) -> ModelInfo:
        """Select model prioritizing performance."""
        def performance_score(model: ModelInfo) -> float:
            metrics = self.performance_metrics.get(model.name)
            if metrics:
                return metrics.quality_score * metrics.success_rate
            else:
                # Estimate based on model size/complexity
                ram_req = model.resource_requirements.get("min_ram_gb", 4)
                return min(ram_req / 16.0, 1.0)  # Normalize to 0-1
        
        return max(models, key=performance_score)
    
    def _select_by_efficiency(self, 
                             models: List[ModelInfo], 
                             requirements: TaskRequirements) -> ModelInfo:
        """Select model prioritizing resource efficiency."""
        def efficiency_score(model: ModelInfo) -> float:
            metrics = self.performance_metrics.get(model.name)
            if metrics:
                # Higher score for lower resource usage and faster response
                resource_score = 1.0 / (metrics.resource_usage.get("memory", 1.0) + 1.0)
                time_score = 1.0 / (metrics.avg_response_time + 1.0)
                return resource_score * time_score * metrics.success_rate
            else:
                # Estimate based on resource requirements
                ram_req = model.resource_requirements.get("min_ram_gb", 4)
                return 1.0 / (ram_req + 1.0)
        
        return max(models, key=efficiency_score)
    
    def _select_balanced(self, 
                        models: List[ModelInfo], 
                        requirements: TaskRequirements) -> ModelInfo:
        """Select model balancing performance and efficiency."""
        def balanced_score(model: ModelInfo) -> float:
            metrics = self.performance_metrics.get(model.name)
            if metrics:
                performance = metrics.quality_score * metrics.success_rate
                efficiency = 1.0 / (metrics.avg_response_time + 1.0)
                resource_efficiency = 1.0 / (metrics.resource_usage.get("memory", 1.0) + 1.0)
                return (performance + efficiency + resource_efficiency) / 3.0
            else:
                # Estimate based on model characteristics
                ram_req = model.resource_requirements.get("min_ram_gb", 4)
                return 1.0 / (ram_req / 8.0 + 1.0)  # Favor medium-sized models
        
        return max(models, key=balanced_score)
    
    def _select_by_cost(self, 
                       models: List[ModelInfo], 
                       requirements: TaskRequirements) -> ModelInfo:
        """Select model prioritizing cost (prefer local models)."""
        # All models in this system are local, so select most efficient
        return self._select_by_efficiency(models, requirements)
    
    async def _find_best_unloaded_model(self, 
                                       models: List[ModelInfo], 
                                       requirements: TaskRequirements) -> Optional[ModelInfo]:
        """Find the best model that's not currently loaded."""
        # Get system resources
        import psutil
        available_ram = psutil.virtual_memory().available / (1024**3)  # GB
        
        # Estimate available VRAM (simplified)
        try:
            import torch
            if torch.cuda.is_available():
                available_vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            else:
                available_vram = 0
        except:
            available_vram = 0
        
        cpu_cores = psutil.cpu_count()
        
        # Find compatible models
        compatible_models = self.model_registry.get_compatible_models(
            available_ram, available_vram, cpu_cores
        )
        
        # Filter to models with required capability
        suitable_models = [
            model for model in compatible_models
            if model in models
        ]
        
        if suitable_models:
            return self._select_by_strategy(suitable_models, requirements)
        
        return None
    
    async def _load_model_if_needed(self, model_name: str) -> bool:
        """Load a model if it's not already loaded."""
        if model_name in self.model_manager.get_available_models():
            return True
        
        model_info = self.model_registry.get_model(model_name)
        if not model_info:
            logger.error(f"Model {model_name} not found in registry")
            return False
        
        # Create model config for loading
        model_config = {
            "model_path": model_info.model_path,
            "model_type": model_info.model_type.value,
            **model_info.parameters
        }
        
        return await self.model_manager.load_model(model_name, model_config)
    
    async def switch_to_model(self, model_name: str) -> bool:
        """Switch to a specific model."""
        try:
            # Ensure model is loaded
            if not await self._load_model_if_needed(model_name):
                return False
            
            # Switch to the model
            return await self.model_manager.switch_model(model_name)
            
        except Exception as e:
            logger.error(f"Error switching to model {model_name}: {e}")
            return False
    
    def update_performance_metrics(self, 
                                  model_name: str,
                                  response_time: float,
                                  success: bool,
                                  quality_score: float,
                                  resource_usage: Dict[str, float]):
        """Update performance metrics for a model."""
        import time
        
        if model_name in self.performance_metrics:
            metrics = self.performance_metrics[model_name]
            # Update with exponential moving average
            alpha = 0.1
            metrics.avg_response_time = (1 - alpha) * metrics.avg_response_time + alpha * response_time
            metrics.success_rate = (1 - alpha) * metrics.success_rate + alpha * (1.0 if success else 0.0)
            metrics.quality_score = (1 - alpha) * metrics.quality_score + alpha * quality_score
            metrics.resource_usage = resource_usage
            metrics.last_updated = time.time()
        else:
            self.performance_metrics[model_name] = ModelPerformanceMetrics(
                model_name=model_name,
                avg_response_time=response_time,
                success_rate=1.0 if success else 0.0,
                quality_score=quality_score,
                resource_usage=resource_usage,
                last_updated=time.time()
            )
    
    def get_model_recommendation(self, capability: ModelCapability) -> Optional[str]:
        """Get recommended model for a capability based on history."""
        return self.model_preferences.get(capability)
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get performance report for all models."""
        report = {
            "total_models": len(self.performance_metrics),
            "models": {},
            "best_performers": {},
            "strategy": self.strategy.value
        }
        
        for model_name, metrics in self.performance_metrics.items():
            report["models"][model_name] = {
                "avg_response_time": metrics.avg_response_time,
                "success_rate": metrics.success_rate,
                "quality_score": metrics.quality_score,
                "resource_usage": metrics.resource_usage
            }
        
        # Find best performers by category
        if self.performance_metrics:
            best_quality = max(self.performance_metrics.values(), key=lambda m: m.quality_score)
            best_speed = min(self.performance_metrics.values(), key=lambda m: m.avg_response_time)
            best_reliability = max(self.performance_metrics.values(), key=lambda m: m.success_rate)
            
            report["best_performers"] = {
                "quality": best_quality.model_name,
                "speed": best_speed.model_name,
                "reliability": best_reliability.model_name
            }
        
        return report
    
    def set_strategy(self, strategy: SwitchingStrategy):
        """Change the switching strategy."""
        self.strategy = strategy
        logger.info(f"Switching strategy changed to: {strategy.value}")
    
    async def optimize_model_selection(self):
        """Optimize model selection based on historical performance."""
        # Analyze task history and update preferences
        capability_performance = {}
        
        for task in self.task_history:
            capability = task.get("capability")
            model_used = task.get("model")
            success = task.get("success", False)
            quality = task.get("quality", 0.0)
            
            if capability and model_used:
                if capability not in capability_performance:
                    capability_performance[capability] = {}
                
                if model_used not in capability_performance[capability]:
                    capability_performance[capability][model_used] = []
                
                capability_performance[capability][model_used].append({
                    "success": success,
                    "quality": quality
                })
        
        # Update preferences based on performance
        for capability, models in capability_performance.items():
            best_model = None
            best_score = 0.0
            
            for model_name, results in models.items():
                if results:
                    avg_success = sum(r["success"] for r in results) / len(results)
                    avg_quality = sum(r["quality"] for r in results) / len(results)
                    score = avg_success * avg_quality
                    
                    if score > best_score:
                        best_score = score
                        best_model = model_name
            
            if best_model:
                self.model_preferences[ModelCapability(capability)] = best_model
        
        logger.info("Model selection optimization completed")