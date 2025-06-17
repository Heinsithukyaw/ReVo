"""
Model Selector - Interactive Model Selection and Configuration

Provides an interactive interface for users to select optimal AI models
based on their system capabilities and preferences.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json

from .deepseek_provider import DeepSeekProvider, SystemDetector, ExecutionMode, ModelFormat
from .local_models import LocalModelManager
from .model_registry import ModelRegistry, ModelInfo, ModelCapability

logger = logging.getLogger(__name__)


class ModelProvider(Enum):
    """Available model providers."""
    DEEPSEEK = "deepseek"
    LLAMA = "llama"
    CODELLAMA = "codellama"
    MISTRAL = "mistral"
    CUSTOM = "custom"


@dataclass
class ModelOption:
    """Model selection option."""
    provider: ModelProvider
    name: str
    display_name: str
    description: str
    requirements: Dict[str, Any]
    capabilities: List[str]
    execution_modes: List[ExecutionMode]
    model_formats: List[ModelFormat]
    recommended_for: List[str]
    size_gb: float
    performance_score: float
    is_available: bool
    setup_complexity: str  # "easy", "medium", "advanced"


class ModelSelector:
    """Interactive model selection and configuration."""
    
    def __init__(self):
        self.system_capabilities = SystemDetector.detect_system()
        self.model_registry = ModelRegistry()
        self.available_models = []
        self._initialize_model_options()
    
    def _initialize_model_options(self):
        """Initialize available model options."""
        self.available_models = [
            # DeepSeek R1 0528 - Primary recommendation
            ModelOption(
                provider=ModelProvider.DEEPSEEK,
                name="deepseek-ai/DeepSeek-R1-0528",
                display_name="DeepSeek R1 0528",
                description="Latest DeepSeek R1 model with enhanced reasoning and coding capabilities",
                requirements={
                    "min_ram_gb": 8,
                    "min_vram_gb": 4,
                    "min_cpu_cores": 4
                },
                capabilities=["code_generation", "debugging", "reasoning", "chat"],
                execution_modes=[ExecutionMode.CPU, ExecutionMode.GPU],
                model_formats=[ModelFormat.TRANSFORMERS, ModelFormat.GGUF],
                recommended_for=["coding", "debugging", "general_ai"],
                size_gb=14.0,
                performance_score=9.5,
                is_available=True,
                setup_complexity="easy"
            ),
            
            # DeepSeek Coder
            ModelOption(
                provider=ModelProvider.DEEPSEEK,
                name="deepseek-ai/deepseek-coder-6.7b-instruct",
                display_name="DeepSeek Coder 6.7B",
                description="Specialized coding model with excellent code generation capabilities",
                requirements={
                    "min_ram_gb": 6,
                    "min_vram_gb": 3,
                    "min_cpu_cores": 2
                },
                capabilities=["code_generation", "code_completion", "debugging"],
                execution_modes=[ExecutionMode.CPU, ExecutionMode.GPU],
                model_formats=[ModelFormat.TRANSFORMERS, ModelFormat.GGUF],
                recommended_for=["coding", "code_completion"],
                size_gb=6.7,
                performance_score=8.5,
                is_available=True,
                setup_complexity="easy"
            ),
            
            # Llama 3.2
            ModelOption(
                provider=ModelProvider.LLAMA,
                name="meta-llama/Llama-3.2-3B-Instruct",
                display_name="Llama 3.2 3B",
                description="Efficient general-purpose model with good performance",
                requirements={
                    "min_ram_gb": 4,
                    "min_vram_gb": 2,
                    "min_cpu_cores": 2
                },
                capabilities=["text_generation", "chat", "reasoning"],
                execution_modes=[ExecutionMode.CPU, ExecutionMode.GPU],
                model_formats=[ModelFormat.TRANSFORMERS, ModelFormat.GGUF],
                recommended_for=["general_ai", "chat", "low_resource"],
                size_gb=3.0,
                performance_score=7.5,
                is_available=True,
                setup_complexity="easy"
            ),
            
            # Code Llama
            ModelOption(
                provider=ModelProvider.CODELLAMA,
                name="codellama/CodeLlama-7b-Instruct-hf",
                display_name="Code Llama 7B",
                description="Meta's specialized code generation model",
                requirements={
                    "min_ram_gb": 8,
                    "min_vram_gb": 4,
                    "min_cpu_cores": 4
                },
                capabilities=["code_generation", "code_completion"],
                execution_modes=[ExecutionMode.CPU, ExecutionMode.GPU],
                model_formats=[ModelFormat.TRANSFORMERS, ModelFormat.GGUF],
                recommended_for=["coding", "code_completion"],
                size_gb=7.0,
                performance_score=8.0,
                is_available=True,
                setup_complexity="easy"
            ),
            
            # Mistral 7B
            ModelOption(
                provider=ModelProvider.MISTRAL,
                name="mistralai/Mistral-7B-Instruct-v0.3",
                display_name="Mistral 7B Instruct",
                description="High-quality general-purpose model with good reasoning",
                requirements={
                    "min_ram_gb": 8,
                    "min_vram_gb": 4,
                    "min_cpu_cores": 4
                },
                capabilities=["text_generation", "chat", "reasoning"],
                execution_modes=[ExecutionMode.CPU, ExecutionMode.GPU],
                model_formats=[ModelFormat.TRANSFORMERS, ModelFormat.GGUF],
                recommended_for=["general_ai", "reasoning", "chat"],
                size_gb=7.0,
                performance_score=8.2,
                is_available=True,
                setup_complexity="easy"
            )
        ]
        
        # Update availability based on system capabilities
        self._update_model_availability()
    
    def _update_model_availability(self):
        """Update model availability based on system capabilities."""
        for model in self.available_models:
            # Check if system meets minimum requirements
            meets_ram = self.system_capabilities.total_ram_gb >= model.requirements["min_ram_gb"]
            meets_vram = (not self.system_capabilities.has_gpu or 
                         self.system_capabilities.gpu_memory_gb >= model.requirements["min_vram_gb"])
            meets_cpu = self.system_capabilities.cpu_cores >= model.requirements["min_cpu_cores"]
            
            model.is_available = meets_ram and meets_vram and meets_cpu
    
    def get_system_summary(self) -> Dict[str, Any]:
        """Get system capabilities summary."""
        return {
            "cpu": {
                "cores": self.system_capabilities.cpu_cores,
                "threads": self.system_capabilities.cpu_threads,
                "architecture": self.system_capabilities.architecture
            },
            "memory": {
                "total_gb": round(self.system_capabilities.total_ram_gb, 1),
                "available_gb": round(self.system_capabilities.available_ram_gb, 1)
            },
            "gpu": {
                "available": self.system_capabilities.has_gpu,
                "count": self.system_capabilities.gpu_count,
                "memory_gb": round(self.system_capabilities.gpu_memory_gb, 1),
                "name": self.system_capabilities.gpu_name
            },
            "platform": {
                "system": self.system_capabilities.platform,
                "architecture": self.system_capabilities.architecture
            },
            "recommendations": {
                "execution_mode": self.system_capabilities.recommended_mode.value,
                "model_format": self.system_capabilities.recommended_format.value
            }
        }
    
    def get_recommended_models(self, use_case: Optional[str] = None) -> List[ModelOption]:
        """Get recommended models based on system capabilities and use case."""
        available_models = [m for m in self.available_models if m.is_available]
        
        if use_case:
            # Filter by use case
            available_models = [m for m in available_models if use_case in m.recommended_for]
        
        # Sort by performance score and system compatibility
        def score_model(model: ModelOption) -> float:
            score = model.performance_score
            
            # Bonus for fitting well within system resources
            ram_ratio = model.requirements["min_ram_gb"] / self.system_capabilities.total_ram_gb
            if ram_ratio < 0.5:
                score += 1.0  # Bonus for using less than 50% of RAM
            elif ram_ratio < 0.7:
                score += 0.5  # Bonus for using less than 70% of RAM
            
            # Bonus for GPU compatibility
            if (self.system_capabilities.has_gpu and 
                ExecutionMode.GPU in model.execution_modes):
                vram_ratio = model.requirements["min_vram_gb"] / self.system_capabilities.gpu_memory_gb
                if vram_ratio < 0.7:
                    score += 1.0
            
            # Penalty for complexity
            if model.setup_complexity == "advanced":
                score -= 0.5
            
            return score
        
        available_models.sort(key=score_model, reverse=True)
        return available_models[:5]  # Return top 5
    
    def get_model_details(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific model."""
        model = next((m for m in self.available_models if m.name == model_name), None)
        if not model:
            return None
        
        # Calculate resource usage
        ram_usage_percent = (model.requirements["min_ram_gb"] / 
                           self.system_capabilities.total_ram_gb * 100)
        
        vram_usage_percent = 0
        if self.system_capabilities.has_gpu and model.requirements["min_vram_gb"] > 0:
            vram_usage_percent = (model.requirements["min_vram_gb"] / 
                                self.system_capabilities.gpu_memory_gb * 100)
        
        # Determine optimal execution mode
        optimal_mode = ExecutionMode.CPU
        if (self.system_capabilities.has_gpu and 
            ExecutionMode.GPU in model.execution_modes and
            vram_usage_percent < 80):
            optimal_mode = ExecutionMode.GPU
        
        return {
            "model": {
                "name": model.name,
                "display_name": model.display_name,
                "description": model.description,
                "provider": model.provider.value,
                "size_gb": model.size_gb,
                "performance_score": model.performance_score,
                "setup_complexity": model.setup_complexity
            },
            "capabilities": model.capabilities,
            "requirements": model.requirements,
            "compatibility": {
                "is_available": model.is_available,
                "ram_usage_percent": round(ram_usage_percent, 1),
                "vram_usage_percent": round(vram_usage_percent, 1),
                "optimal_execution_mode": optimal_mode.value,
                "supported_formats": [f.value for f in model.model_formats]
            },
            "recommendations": {
                "use_cases": model.recommended_for,
                "execution_modes": [m.value for m in model.execution_modes]
            }
        }
    
    def get_execution_mode_options(self, model_name: str) -> List[Dict[str, Any]]:
        """Get available execution mode options for a model."""
        model = next((m for m in self.available_models if m.name == model_name), None)
        if not model:
            return []
        
        options = []
        
        # CPU option
        if ExecutionMode.CPU in model.execution_modes:
            ram_usage = (model.requirements["min_ram_gb"] / 
                        self.system_capabilities.total_ram_gb * 100)
            
            options.append({
                "mode": ExecutionMode.CPU.value,
                "name": "CPU Only",
                "description": f"Use {self.system_capabilities.cpu_cores} CPU cores",
                "resource_usage": f"{ram_usage:.1f}% RAM",
                "performance": "Good for general tasks",
                "recommended": ram_usage < 70 and not self.system_capabilities.has_gpu,
                "available": True
            })
        
        # GPU option
        if (ExecutionMode.GPU in model.execution_modes and 
            self.system_capabilities.has_gpu):
            
            vram_usage = (model.requirements["min_vram_gb"] / 
                         self.system_capabilities.gpu_memory_gb * 100)
            
            options.append({
                "mode": ExecutionMode.GPU.value,
                "name": f"GPU ({self.system_capabilities.gpu_name})",
                "description": f"Use GPU acceleration with {self.system_capabilities.gpu_memory_gb:.1f}GB VRAM",
                "resource_usage": f"{vram_usage:.1f}% VRAM",
                "performance": "Best performance for AI tasks",
                "recommended": vram_usage < 80,
                "available": vram_usage < 95
            })
        
        return options
    
    def get_format_options(self, model_name: str, execution_mode: str) -> List[Dict[str, Any]]:
        """Get available format options for a model and execution mode."""
        model = next((m for m in self.available_models if m.name == model_name), None)
        if not model:
            return []
        
        mode = ExecutionMode(execution_mode)
        options = []
        
        # Transformers format
        if ModelFormat.TRANSFORMERS in model.model_formats:
            options.append({
                "format": ModelFormat.TRANSFORMERS.value,
                "name": "Transformers (HuggingFace)",
                "description": "Full precision model with all features",
                "pros": ["Full model capabilities", "Easy to use", "Wide compatibility"],
                "cons": ["Higher memory usage", "Slower loading"],
                "memory_usage": "High",
                "loading_time": "Medium",
                "recommended": mode == ExecutionMode.GPU,
                "setup_complexity": "easy"
            })
        
        # GGUF format
        if ModelFormat.GGUF in model.model_formats:
            options.append({
                "format": ModelFormat.GGUF.value,
                "name": "GGUF (llama.cpp)",
                "description": "Quantized model optimized for efficiency",
                "pros": ["Lower memory usage", "Faster inference", "CPU optimized"],
                "cons": ["Requires conversion", "Slightly lower quality"],
                "memory_usage": "Low",
                "loading_time": "Fast",
                "recommended": mode == ExecutionMode.CPU,
                "setup_complexity": "medium"
            })
        
        return options
    
    async def create_provider(self, 
                            model_name: str,
                            execution_mode: str,
                            model_format: str) -> Optional[Any]:
        """Create a model provider with the specified configuration."""
        try:
            model = next((m for m in self.available_models if m.name == model_name), None)
            if not model:
                logger.error(f"Model {model_name} not found")
                return None
            
            if model.provider == ModelProvider.DEEPSEEK:
                # Create DeepSeek provider
                mode = ExecutionMode(execution_mode)
                provider = DeepSeekProvider(mode)
                
                # Override format if specified
                if model_format:
                    provider.config.model_format = ModelFormat(model_format)
                
                # Override model name if different
                if model.name != "deepseek-ai/DeepSeek-R1-0528":
                    provider.config.model_name = model.name
                
                success = await provider.initialize()
                if success:
                    logger.info(f"Created DeepSeek provider for {model_name}")
                    return provider
                else:
                    logger.error(f"Failed to initialize DeepSeek provider")
                    return None
            
            else:
                # For other providers, use the generic LocalModelManager
                # This would be implemented based on the specific provider
                logger.warning(f"Provider {model.provider.value} not yet implemented")
                return None
                
        except Exception as e:
            logger.error(f"Error creating provider: {e}")
            return None
    
    def get_setup_instructions(self, 
                             model_name: str,
                             execution_mode: str,
                             model_format: str) -> Dict[str, Any]:
        """Get setup instructions for a specific configuration."""
        model = next((m for m in self.available_models if m.name == model_name), None)
        if not model:
            return {"error": "Model not found"}
        
        instructions = {
            "model": model.display_name,
            "execution_mode": execution_mode,
            "model_format": model_format,
            "steps": [],
            "requirements": [],
            "estimated_time": "5-15 minutes",
            "difficulty": model.setup_complexity
        }
        
        # Add requirements
        instructions["requirements"].extend([
            f"RAM: {model.requirements['min_ram_gb']}GB minimum",
            f"CPU: {model.requirements['min_cpu_cores']} cores minimum"
        ])
        
        if execution_mode == "gpu":
            instructions["requirements"].append(
                f"GPU: {model.requirements['min_vram_gb']}GB VRAM minimum"
            )
        
        # Add setup steps
        if model_format == "transformers":
            instructions["steps"].extend([
                "Install required Python packages",
                "Download model from HuggingFace Hub",
                "Initialize model and tokenizer",
                "Run initial test"
            ])
            instructions["estimated_time"] = "10-30 minutes"
        
        elif model_format == "gguf":
            instructions["steps"].extend([
                "Install llama-cpp-python",
                "Download GGUF model file",
                "Configure llama.cpp settings",
                "Run initial test"
            ])
            instructions["estimated_time"] = "5-15 minutes"
        
        # Add specific commands
        if model.provider == ModelProvider.DEEPSEEK:
            instructions["commands"] = [
                "pip install transformers torch",
                f"python -c \"from transformers import AutoTokenizer; AutoTokenizer.from_pretrained('{model.name}', trust_remote_code=True)\"",
                "python -m revoagent.model_layer.deepseek_provider"
            ]
        
        return instructions
    
    def export_configuration(self, 
                           model_name: str,
                           execution_mode: str,
                           model_format: str) -> Dict[str, Any]:
        """Export configuration for saving/sharing."""
        return {
            "model_selection": {
                "model_name": model_name,
                "execution_mode": execution_mode,
                "model_format": model_format,
                "timestamp": asyncio.get_event_loop().time()
            },
            "system_info": self.get_system_summary(),
            "model_details": self.get_model_details(model_name)
        }


# CLI interface for model selection
class ModelSelectorCLI:
    """Command-line interface for model selection."""
    
    def __init__(self):
        self.selector = ModelSelector()
    
    async def run_interactive_selection(self) -> Optional[Dict[str, Any]]:
        """Run interactive model selection."""
        print("🤖 reVoAgent Model Selector")
        print("=" * 50)
        
        # Show system summary
        system_info = self.selector.get_system_summary()
        print(f"\n📊 System Information:")
        print(f"  CPU: {system_info['cpu']['cores']} cores ({system_info['cpu']['architecture']})")
        print(f"  RAM: {system_info['memory']['total_gb']}GB total, {system_info['memory']['available_gb']}GB available")
        
        if system_info['gpu']['available']:
            print(f"  GPU: {system_info['gpu']['name']} ({system_info['gpu']['memory_gb']}GB VRAM)")
        else:
            print("  GPU: Not available")
        
        print(f"\n💡 Recommended: {system_info['recommendations']['execution_mode']} mode with {system_info['recommendations']['model_format']} format")
        
        # Show recommended models
        print(f"\n🎯 Recommended Models:")
        recommended = self.selector.get_recommended_models()
        
        for i, model in enumerate(recommended, 1):
            status = "✅" if model.is_available else "❌"
            print(f"  {i}. {status} {model.display_name}")
            print(f"     {model.description}")
            print(f"     Size: {model.size_gb}GB | Score: {model.performance_score}/10")
            print()
        
        # Get user selection
        while True:
            try:
                choice = input("Select a model (1-5) or 'q' to quit: ").strip()
                if choice.lower() == 'q':
                    return None
                
                model_idx = int(choice) - 1
                if 0 <= model_idx < len(recommended):
                    selected_model = recommended[model_idx]
                    break
                else:
                    print("Invalid selection. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a number or 'q'.")
        
        # Show model details
        details = self.selector.get_model_details(selected_model.name)
        print(f"\n📋 {selected_model.display_name} Details:")
        print(f"  Description: {details['model']['description']}")
        print(f"  Capabilities: {', '.join(details['capabilities'])}")
        print(f"  RAM Usage: {details['compatibility']['ram_usage_percent']}%")
        if details['compatibility']['vram_usage_percent'] > 0:
            print(f"  VRAM Usage: {details['compatibility']['vram_usage_percent']}%")
        
        # Select execution mode
        print(f"\n⚙️  Execution Mode Options:")
        mode_options = self.selector.get_execution_mode_options(selected_model.name)
        
        for i, option in enumerate(mode_options, 1):
            status = "✅" if option['available'] else "❌"
            rec = " (Recommended)" if option['recommended'] else ""
            print(f"  {i}. {status} {option['name']}{rec}")
            print(f"     {option['description']}")
            print(f"     Resource Usage: {option['resource_usage']}")
            print()
        
        # Get execution mode selection
        while True:
            try:
                choice = input(f"Select execution mode (1-{len(mode_options)}): ").strip()
                mode_idx = int(choice) - 1
                if 0 <= mode_idx < len(mode_options):
                    selected_mode = mode_options[mode_idx]
                    if selected_mode['available']:
                        break
                    else:
                        print("This mode is not available on your system.")
                else:
                    print("Invalid selection. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a number.")
        
        # Select model format
        print(f"\n📦 Model Format Options:")
        format_options = self.selector.get_format_options(selected_model.name, selected_mode['mode'])
        
        for i, option in enumerate(format_options, 1):
            rec = " (Recommended)" if option['recommended'] else ""
            print(f"  {i}. {option['name']}{rec}")
            print(f"     {option['description']}")
            print(f"     Memory Usage: {option['memory_usage']} | Setup: {option['setup_complexity']}")
            print()
        
        # Get format selection
        while True:
            try:
                choice = input(f"Select model format (1-{len(format_options)}): ").strip()
                format_idx = int(choice) - 1
                if 0 <= format_idx < len(format_options):
                    selected_format = format_options[format_idx]
                    break
                else:
                    print("Invalid selection. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a number.")
        
        # Show setup instructions
        instructions = self.selector.get_setup_instructions(
            selected_model.name,
            selected_mode['mode'],
            selected_format['format']
        )
        
        print(f"\n🛠️  Setup Instructions:")
        print(f"  Model: {instructions['model']}")
        print(f"  Difficulty: {instructions['difficulty']}")
        print(f"  Estimated Time: {instructions['estimated_time']}")
        print(f"\n  Requirements:")
        for req in instructions['requirements']:
            print(f"    - {req}")
        
        print(f"\n  Steps:")
        for i, step in enumerate(instructions['steps'], 1):
            print(f"    {i}. {step}")
        
        # Confirm setup
        confirm = input(f"\nProceed with setup? (y/n): ").strip().lower()
        if confirm != 'y':
            print("Setup cancelled.")
            return None
        
        # Return configuration
        return {
            "model_name": selected_model.name,
            "execution_mode": selected_mode['mode'],
            "model_format": selected_format['format'],
            "instructions": instructions
        }


# Example usage
if __name__ == "__main__":
    async def main():
        cli = ModelSelectorCLI()
        config = await cli.run_interactive_selection()
        
        if config:
            print(f"\n✅ Configuration selected:")
            print(json.dumps(config, indent=2))
            
            # Try to create provider
            print(f"\n🚀 Initializing model...")
            provider = await cli.selector.create_provider(
                config['model_name'],
                config['execution_mode'],
                config['model_format']
            )
            
            if provider:
                print("✅ Model initialized successfully!")
                
                # Test generation
                try:
                    response = await provider.generate_simple("Hello, who are you?")
                    print(f"\n🤖 Test Response: {response}")
                except Exception as e:
                    print(f"❌ Test failed: {e}")
                
                # Cleanup
                provider.shutdown()
            else:
                print("❌ Failed to initialize model")
        else:
            print("No configuration selected.")
    
    asyncio.run(main())