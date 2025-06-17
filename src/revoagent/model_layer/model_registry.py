"""
Model Registry - Centralized Model Discovery and Management

Manages available models, their capabilities, and resource requirements.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Supported model types."""
    VLLM = "vllm"
    TRANSFORMERS = "transformers"
    GGUF = "gguf"
    ONNX = "onnx"


class ModelCapability(Enum):
    """Model capabilities."""
    CODE_GENERATION = "code_generation"
    TEXT_GENERATION = "text_generation"
    CHAT = "chat"
    DEBUGGING = "debugging"
    TESTING = "testing"
    DOCUMENTATION = "documentation"


@dataclass
class ModelInfo:
    """Information about a model."""
    name: str
    display_name: str
    model_type: ModelType
    model_path: str
    capabilities: List[ModelCapability]
    resource_requirements: Dict[str, Any]
    parameters: Dict[str, Any]
    description: str
    version: str = "1.0.0"
    author: str = "Unknown"
    license: str = "Unknown"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["model_type"] = self.model_type.value
        data["capabilities"] = [cap.value for cap in self.capabilities]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelInfo":
        """Create from dictionary."""
        data["model_type"] = ModelType(data["model_type"])
        data["capabilities"] = [ModelCapability(cap) for cap in data["capabilities"]]
        return cls(**data)


class ModelRegistry:
    """Registry for managing available models."""
    
    def __init__(self, registry_path: Optional[Path] = None):
        self.registry_path = registry_path or Path("models/registry.json")
        self.models: Dict[str, ModelInfo] = {}
        self._load_registry()
    
    def _load_registry(self):
        """Load the model registry from file."""
        if self.registry_path.exists():
            try:
                with open(self.registry_path, 'r') as f:
                    data = json.load(f)
                    for model_data in data.get("models", []):
                        model_info = ModelInfo.from_dict(model_data)
                        self.models[model_info.name] = model_info
                logger.info(f"Loaded {len(self.models)} models from registry")
            except Exception as e:
                logger.error(f"Error loading model registry: {e}")
        else:
            # Create default registry
            self._create_default_registry()
    
    def _save_registry(self):
        """Save the model registry to file."""
        try:
            self.registry_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "version": "1.0.0",
                "models": [model.to_dict() for model in self.models.values()]
            }
            with open(self.registry_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info("Model registry saved")
        except Exception as e:
            logger.error(f"Error saving model registry: {e}")
    
    def _create_default_registry(self):
        """Create a default model registry with common models."""
        default_models = [
            ModelInfo(
                name="deepseek-coder-6.7b",
                display_name="DeepSeek Coder 6.7B",
                model_type=ModelType.VLLM,
                model_path="deepseek-ai/deepseek-coder-6.7b-instruct",
                capabilities=[
                    ModelCapability.CODE_GENERATION,
                    ModelCapability.DEBUGGING,
                    ModelCapability.TESTING,
                    ModelCapability.DOCUMENTATION
                ],
                resource_requirements={
                    "min_ram_gb": 8,
                    "min_vram_gb": 8,
                    "min_cpu_cores": 4
                },
                parameters={
                    "max_tokens": 4096,
                    "temperature": 0.1,
                    "top_p": 0.9
                },
                description="DeepSeek Coder model optimized for code generation and debugging"
            ),
            ModelInfo(
                name="deepseek-r1-0528",
                display_name="DeepSeek R1 0528",
                model_type=ModelType.VLLM,
                model_path="deepseek-ai/DeepSeek-R1-0528",
                capabilities=[
                    ModelCapability.CODE_GENERATION,
                    ModelCapability.CHAT,
                    ModelCapability.DEBUGGING,
                    ModelCapability.TESTING
                ],
                resource_requirements={
                    "min_ram_gb": 16,
                    "min_vram_gb": 12,
                    "min_cpu_cores": 8
                },
                parameters={
                    "max_tokens": 8192,
                    "temperature": 0.1,
                    "top_p": 0.9
                },
                description="Latest DeepSeek R1 model with enhanced reasoning capabilities"
            ),
            ModelInfo(
                name="codellama-7b",
                display_name="Code Llama 7B",
                model_type=ModelType.VLLM,
                model_path="codellama/CodeLlama-7b-Instruct-hf",
                capabilities=[
                    ModelCapability.CODE_GENERATION,
                    ModelCapability.DEBUGGING
                ],
                resource_requirements={
                    "min_ram_gb": 8,
                    "min_vram_gb": 8,
                    "min_cpu_cores": 4
                },
                parameters={
                    "max_tokens": 4096,
                    "temperature": 0.1,
                    "top_p": 0.9
                },
                description="Meta's Code Llama model for code generation"
            )
        ]
        
        for model in default_models:
            self.models[model.name] = model
        
        self._save_registry()
        logger.info("Created default model registry")
    
    def register_model(self, model_info: ModelInfo) -> bool:
        """Register a new model."""
        try:
            self.models[model_info.name] = model_info
            self._save_registry()
            logger.info(f"Registered model: {model_info.name}")
            return True
        except Exception as e:
            logger.error(f"Error registering model {model_info.name}: {e}")
            return False
    
    def unregister_model(self, model_name: str) -> bool:
        """Unregister a model."""
        if model_name in self.models:
            del self.models[model_name]
            self._save_registry()
            logger.info(f"Unregistered model: {model_name}")
            return True
        else:
            logger.warning(f"Model {model_name} not found in registry")
            return False
    
    def get_model(self, model_name: str) -> Optional[ModelInfo]:
        """Get model information."""
        return self.models.get(model_name)
    
    def list_models(self) -> List[ModelInfo]:
        """List all registered models."""
        return list(self.models.values())
    
    def find_models_by_capability(self, capability: ModelCapability) -> List[ModelInfo]:
        """Find models with a specific capability."""
        return [
            model for model in self.models.values()
            if capability in model.capabilities
        ]
    
    def find_models_by_type(self, model_type: ModelType) -> List[ModelInfo]:
        """Find models of a specific type."""
        return [
            model for model in self.models.values()
            if model.model_type == model_type
        ]
    
    def get_compatible_models(self, 
                            available_ram_gb: float,
                            available_vram_gb: float,
                            cpu_cores: int) -> List[ModelInfo]:
        """Get models compatible with available resources."""
        compatible = []
        for model in self.models.values():
            req = model.resource_requirements
            if (available_ram_gb >= req.get("min_ram_gb", 0) and
                available_vram_gb >= req.get("min_vram_gb", 0) and
                cpu_cores >= req.get("min_cpu_cores", 1)):
                compatible.append(model)
        return compatible
    
    def recommend_model(self, 
                       capability: ModelCapability,
                       available_ram_gb: float,
                       available_vram_gb: float,
                       cpu_cores: int) -> Optional[ModelInfo]:
        """Recommend the best model for given capability and resources."""
        # Find models with the capability
        capable_models = self.find_models_by_capability(capability)
        
        # Filter by resource compatibility
        compatible_models = []
        for model in capable_models:
            req = model.resource_requirements
            if (available_ram_gb >= req.get("min_ram_gb", 0) and
                available_vram_gb >= req.get("min_vram_gb", 0) and
                cpu_cores >= req.get("min_cpu_cores", 1)):
                compatible_models.append(model)
        
        if not compatible_models:
            return None
        
        # Sort by resource efficiency (prefer models that use resources efficiently)
        def efficiency_score(model: ModelInfo) -> float:
            req = model.resource_requirements
            ram_ratio = req.get("min_ram_gb", 1) / available_ram_gb
            vram_ratio = req.get("min_vram_gb", 1) / available_vram_gb
            cpu_ratio = req.get("min_cpu_cores", 1) / cpu_cores
            return ram_ratio + vram_ratio + cpu_ratio
        
        compatible_models.sort(key=efficiency_score)
        return compatible_models[0]
    
    def update_model(self, model_name: str, updates: Dict[str, Any]) -> bool:
        """Update model information."""
        if model_name not in self.models:
            logger.error(f"Model {model_name} not found")
            return False
        
        try:
            model = self.models[model_name]
            model_dict = model.to_dict()
            model_dict.update(updates)
            self.models[model_name] = ModelInfo.from_dict(model_dict)
            self._save_registry()
            logger.info(f"Updated model: {model_name}")
            return True
        except Exception as e:
            logger.error(f"Error updating model {model_name}: {e}")
            return False
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        stats = {
            "total_models": len(self.models),
            "models_by_type": {},
            "models_by_capability": {},
            "total_capabilities": set()
        }
        
        for model in self.models.values():
            # Count by type
            model_type = model.model_type.value
            stats["models_by_type"][model_type] = stats["models_by_type"].get(model_type, 0) + 1
            
            # Count by capability
            for capability in model.capabilities:
                cap_name = capability.value
                stats["models_by_capability"][cap_name] = stats["models_by_capability"].get(cap_name, 0) + 1
                stats["total_capabilities"].add(cap_name)
        
        stats["total_capabilities"] = len(stats["total_capabilities"])
        return stats