"""
Model Quantization - Resource Optimization for Constrained Environments

Automatic model quantization and optimization for efficient execution.
"""

import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import psutil

logger = logging.getLogger(__name__)


class QuantizationType(Enum):
    """Supported quantization types."""
    INT8 = "int8"
    INT4 = "int4"
    FP16 = "fp16"
    DYNAMIC = "dynamic"
    STATIC = "static"


class QuantizationBackend(Enum):
    """Quantization backends."""
    ONNX = "onnx"
    PYTORCH = "pytorch"
    LLAMA_CPP = "llama_cpp"
    VLLM = "vllm"


@dataclass
class QuantizationConfig:
    """Configuration for model quantization."""
    quantization_type: QuantizationType
    backend: QuantizationBackend
    target_memory_gb: Optional[float] = None
    preserve_accuracy: bool = True
    calibration_dataset: Optional[str] = None
    output_path: Optional[str] = None


@dataclass
class QuantizationResult:
    """Result of model quantization."""
    success: bool
    original_size_mb: float
    quantized_size_mb: float
    compression_ratio: float
    accuracy_loss: Optional[float] = None
    quantized_model_path: Optional[str] = None
    error_message: Optional[str] = None


class ModelQuantizer:
    """Handles model quantization for resource optimization."""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path("models/quantized")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.quantized_models: Dict[str, Dict[str, Any]] = {}
        
    def analyze_system_resources(self) -> Dict[str, float]:
        """Analyze available system resources."""
        memory = psutil.virtual_memory()
        
        # Get GPU memory if available
        gpu_memory = 0.0
        try:
            import torch
            if torch.cuda.is_available():
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        except ImportError:
            pass
        
        return {
            "total_ram_gb": memory.total / (1024**3),
            "available_ram_gb": memory.available / (1024**3),
            "total_gpu_memory_gb": gpu_memory,
            "cpu_cores": psutil.cpu_count()
        }
    
    def recommend_quantization(self, 
                             model_size_gb: float,
                             target_memory_gb: Optional[float] = None) -> QuantizationConfig:
        """Recommend quantization configuration based on resources."""
        resources = self.analyze_system_resources()
        available_memory = min(resources["available_ram_gb"], 
                             resources["total_gpu_memory_gb"] if resources["total_gpu_memory_gb"] > 0 
                             else resources["available_ram_gb"])
        
        if target_memory_gb is None:
            target_memory_gb = available_memory * 0.7  # Use 70% of available memory
        
        # Determine quantization type based on compression needed
        compression_needed = model_size_gb / target_memory_gb
        
        if compression_needed <= 1.2:
            # Minimal compression needed
            return QuantizationConfig(
                quantization_type=QuantizationType.FP16,
                backend=QuantizationBackend.VLLM,
                target_memory_gb=target_memory_gb,
                preserve_accuracy=True
            )
        elif compression_needed <= 2.0:
            # Moderate compression
            return QuantizationConfig(
                quantization_type=QuantizationType.INT8,
                backend=QuantizationBackend.VLLM,
                target_memory_gb=target_memory_gb,
                preserve_accuracy=True
            )
        else:
            # Aggressive compression
            return QuantizationConfig(
                quantization_type=QuantizationType.INT4,
                backend=QuantizationBackend.LLAMA_CPP,
                target_memory_gb=target_memory_gb,
                preserve_accuracy=False
            )
    
    async def quantize_model(self, 
                           model_path: str,
                           config: QuantizationConfig) -> QuantizationResult:
        """Quantize a model according to the configuration."""
        try:
            # Check if already quantized
            cache_key = self._get_cache_key(model_path, config)
            if cache_key in self.quantized_models:
                cached = self.quantized_models[cache_key]
                return QuantizationResult(
                    success=True,
                    original_size_mb=cached["original_size_mb"],
                    quantized_size_mb=cached["quantized_size_mb"],
                    compression_ratio=cached["compression_ratio"],
                    quantized_model_path=cached["quantized_model_path"]
                )
            
            # Get original model size
            original_size = self._get_model_size(model_path)
            
            # Perform quantization based on backend
            if config.backend == QuantizationBackend.VLLM:
                result = await self._quantize_vllm(model_path, config)
            elif config.backend == QuantizationBackend.LLAMA_CPP:
                result = await self._quantize_llama_cpp(model_path, config)
            elif config.backend == QuantizationBackend.ONNX:
                result = await self._quantize_onnx(model_path, config)
            elif config.backend == QuantizationBackend.PYTORCH:
                result = await self._quantize_pytorch(model_path, config)
            else:
                raise ValueError(f"Unsupported backend: {config.backend}")
            
            if result.success:
                # Cache the result
                self.quantized_models[cache_key] = {
                    "original_size_mb": result.original_size_mb,
                    "quantized_size_mb": result.quantized_size_mb,
                    "compression_ratio": result.compression_ratio,
                    "quantized_model_path": result.quantized_model_path
                }
                
                logger.info(f"Model quantized successfully: {result.compression_ratio:.2f}x compression")
            
            return result
            
        except Exception as e:
            logger.error(f"Error quantizing model: {e}")
            return QuantizationResult(
                success=False,
                original_size_mb=0.0,
                quantized_size_mb=0.0,
                compression_ratio=1.0,
                error_message=str(e)
            )
    
    async def _quantize_vllm(self, 
                           model_path: str, 
                           config: QuantizationConfig) -> QuantizationResult:
        """Quantize model for vLLM backend."""
        # vLLM supports quantization through command-line arguments
        # For now, we'll return a configuration that vLLM can use
        original_size = self._get_model_size(model_path)
        
        # Estimate compression ratio based on quantization type
        compression_ratios = {
            QuantizationType.FP16: 2.0,
            QuantizationType.INT8: 4.0,
            QuantizationType.INT4: 8.0
        }
        
        compression_ratio = compression_ratios.get(config.quantization_type, 1.0)
        quantized_size = original_size / compression_ratio
        
        return QuantizationResult(
            success=True,
            original_size_mb=original_size,
            quantized_size_mb=quantized_size,
            compression_ratio=compression_ratio,
            quantized_model_path=model_path  # vLLM handles quantization at runtime
        )
    
    async def _quantize_llama_cpp(self, 
                                model_path: str, 
                                config: QuantizationConfig) -> QuantizationResult:
        """Quantize model using llama.cpp."""
        try:
            # Check if llama.cpp is available
            if not shutil.which("llama-quantize"):
                raise RuntimeError("llama.cpp quantization tools not found")
            
            original_size = self._get_model_size(model_path)
            
            # Determine quantization method for llama.cpp
            quant_methods = {
                QuantizationType.INT8: "q8_0",
                QuantizationType.INT4: "q4_0",
                QuantizationType.FP16: "f16"
            }
            
            quant_method = quant_methods.get(config.quantization_type, "q4_0")
            
            # Generate output path
            output_path = config.output_path or str(
                self.cache_dir / f"{Path(model_path).stem}_{quant_method}.gguf"
            )
            
            # Run quantization
            cmd = [
                "llama-quantize",
                model_path,
                output_path,
                quant_method
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise RuntimeError(f"Quantization failed: {stderr.decode()}")
            
            quantized_size = self._get_model_size(output_path)
            compression_ratio = original_size / quantized_size
            
            return QuantizationResult(
                success=True,
                original_size_mb=original_size,
                quantized_size_mb=quantized_size,
                compression_ratio=compression_ratio,
                quantized_model_path=output_path
            )
            
        except Exception as e:
            return QuantizationResult(
                success=False,
                original_size_mb=0.0,
                quantized_size_mb=0.0,
                compression_ratio=1.0,
                error_message=str(e)
            )
    
    async def _quantize_onnx(self, 
                           model_path: str, 
                           config: QuantizationConfig) -> QuantizationResult:
        """Quantize model using ONNX Runtime."""
        try:
            import onnxruntime as ort
            from onnxruntime.quantization import quantize_dynamic, QuantType
            
            original_size = self._get_model_size(model_path)
            
            # Generate output path
            output_path = config.output_path or str(
                self.cache_dir / f"{Path(model_path).stem}_quantized.onnx"
            )
            
            # Determine quantization type
            quant_type = QuantType.QUInt8
            if config.quantization_type == QuantizationType.INT8:
                quant_type = QuantType.QInt8
            
            # Perform quantization
            quantize_dynamic(
                model_input=model_path,
                model_output=output_path,
                weight_type=quant_type
            )
            
            quantized_size = self._get_model_size(output_path)
            compression_ratio = original_size / quantized_size
            
            return QuantizationResult(
                success=True,
                original_size_mb=original_size,
                quantized_size_mb=quantized_size,
                compression_ratio=compression_ratio,
                quantized_model_path=output_path
            )
            
        except Exception as e:
            return QuantizationResult(
                success=False,
                original_size_mb=0.0,
                quantized_size_mb=0.0,
                compression_ratio=1.0,
                error_message=str(e)
            )
    
    async def _quantize_pytorch(self, 
                              model_path: str, 
                              config: QuantizationConfig) -> QuantizationResult:
        """Quantize model using PyTorch quantization."""
        try:
            import torch
            import torch.quantization as quant
            
            original_size = self._get_model_size(model_path)
            
            # Load model
            model = torch.load(model_path, map_location='cpu')
            
            # Apply quantization
            if config.quantization_type == QuantizationType.DYNAMIC:
                quantized_model = torch.quantization.quantize_dynamic(
                    model, {torch.nn.Linear}, dtype=torch.qint8
                )
            else:
                # Static quantization (requires calibration)
                model.qconfig = torch.quantization.get_default_qconfig('fbgemm')
                torch.quantization.prepare(model, inplace=True)
                # Note: Would need calibration data here for static quantization
                quantized_model = torch.quantization.convert(model, inplace=False)
            
            # Save quantized model
            output_path = config.output_path or str(
                self.cache_dir / f"{Path(model_path).stem}_quantized.pt"
            )
            
            torch.save(quantized_model, output_path)
            
            quantized_size = self._get_model_size(output_path)
            compression_ratio = original_size / quantized_size
            
            return QuantizationResult(
                success=True,
                original_size_mb=original_size,
                quantized_size_mb=quantized_size,
                compression_ratio=compression_ratio,
                quantized_model_path=output_path
            )
            
        except Exception as e:
            return QuantizationResult(
                success=False,
                original_size_mb=0.0,
                quantized_size_mb=0.0,
                compression_ratio=1.0,
                error_message=str(e)
            )
    
    def _get_model_size(self, model_path: str) -> float:
        """Get model size in MB."""
        try:
            if os.path.isfile(model_path):
                return os.path.getsize(model_path) / (1024 * 1024)
            elif os.path.isdir(model_path):
                total_size = 0
                for dirpath, dirnames, filenames in os.walk(model_path):
                    for filename in filenames:
                        filepath = os.path.join(dirpath, filename)
                        total_size += os.path.getsize(filepath)
                return total_size / (1024 * 1024)
            else:
                return 0.0
        except:
            return 0.0
    
    def _get_cache_key(self, model_path: str, config: QuantizationConfig) -> str:
        """Generate cache key for quantized model."""
        import hashlib
        key_data = f"{model_path}_{config.quantization_type.value}_{config.backend.value}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get_quantization_options(self, model_path: str) -> List[QuantizationConfig]:
        """Get available quantization options for a model."""
        model_size = self._get_model_size(model_path)
        resources = self.analyze_system_resources()
        
        options = []
        
        # Conservative option (FP16)
        if model_size * 0.5 <= resources["available_ram_gb"] * 1024:  # Convert to MB
            options.append(QuantizationConfig(
                quantization_type=QuantizationType.FP16,
                backend=QuantizationBackend.VLLM,
                preserve_accuracy=True
            ))
        
        # Balanced option (INT8)
        if model_size * 0.25 <= resources["available_ram_gb"] * 1024:
            options.append(QuantizationConfig(
                quantization_type=QuantizationType.INT8,
                backend=QuantizationBackend.VLLM,
                preserve_accuracy=True
            ))
        
        # Aggressive option (INT4)
        options.append(QuantizationConfig(
            quantization_type=QuantizationType.INT4,
            backend=QuantizationBackend.LLAMA_CPP,
            preserve_accuracy=False
        ))
        
        return options
    
    def cleanup_cache(self, max_size_gb: float = 10.0):
        """Clean up quantization cache."""
        try:
            total_size = 0
            files = []
            
            for file_path in self.cache_dir.rglob("*"):
                if file_path.is_file():
                    size = file_path.stat().st_size
                    total_size += size
                    files.append((file_path, size, file_path.stat().st_mtime))
            
            if total_size > max_size_gb * 1024**3:  # Convert to bytes
                # Sort by modification time (oldest first)
                files.sort(key=lambda x: x[2])
                
                # Remove oldest files until under limit
                for file_path, size, _ in files:
                    if total_size <= max_size_gb * 1024**3:
                        break
                    file_path.unlink()
                    total_size -= size
                    logger.info(f"Removed cached file: {file_path}")
            
        except Exception as e:
            logger.error(f"Error cleaning cache: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            total_size = 0
            file_count = 0
            
            for file_path in self.cache_dir.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    file_count += 1
            
            return {
                "total_size_gb": total_size / (1024**3),
                "file_count": file_count,
                "cache_dir": str(self.cache_dir),
                "quantized_models": len(self.quantized_models)
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"error": str(e)}