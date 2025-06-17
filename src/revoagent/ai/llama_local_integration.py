"""
Llama Local Integration - High-Performance Local AI Execution

This module provides optimized local execution of Llama models with
GPU acceleration, quantization, and performance optimization for
development tasks.
"""

import asyncio
import logging
import time
import gc
from typing import Any, Dict, List, Optional, Union, AsyncGenerator
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import torch
import torch.nn.functional as F
from transformers import (
    AutoTokenizer, AutoModelForCausalLM, 
    BitsAndBytesConfig, GenerationConfig
)
from accelerate import init_empty_weights, load_checkpoint_and_dispatch
import psutil
import GPUtil


class LlamaModelSize(Enum):
    """Llama model sizes"""
    LLAMA_7B = "7b"
    LLAMA_13B = "13b"
    LLAMA_30B = "30b"
    LLAMA_65B = "65b"
    LLAMA2_7B = "llama2_7b"
    LLAMA2_13B = "llama2_13b"
    LLAMA2_70B = "llama2_70b"
    CODE_LLAMA_7B = "code_llama_7b"
    CODE_LLAMA_13B = "code_llama_13b"
    CODE_LLAMA_34B = "code_llama_34b"


class QuantizationMode(Enum):
    """Model quantization modes"""
    NONE = "none"
    INT8 = "int8"
    INT4 = "int4"
    GPTQ = "gptq"
    AWQ = "awq"


class TaskType(Enum):
    """Types of tasks for Llama"""
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    DEBUGGING = "debugging"
    DOCUMENTATION = "documentation"
    EXPLANATION = "explanation"
    REFACTORING = "refactoring"
    TESTING = "testing"
    GENERAL = "general"


@dataclass
class LlamaConfig:
    """Configuration for Llama model"""
    model_size: LlamaModelSize
    quantization: QuantizationMode
    max_memory_gb: float
    use_gpu: bool
    gpu_memory_fraction: float
    cache_dir: Optional[str] = None
    custom_model_path: Optional[str] = None


@dataclass
class GenerationRequest:
    """Request for text generation"""
    prompt: str
    task_type: TaskType
    max_tokens: int = 2048
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 50
    repetition_penalty: float = 1.1
    stop_sequences: List[str] = None
    context: Dict[str, Any] = None


@dataclass
class GenerationResult:
    """Result from text generation"""
    request_id: str
    generated_text: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    generation_time: float
    tokens_per_second: float
    model_info: Dict[str, Any]
    metadata: Dict[str, Any]


class LlamaLocalIntegration:
    """
    High-performance local Llama integration with optimization features.
    
    Features:
    - Multiple model size support
    - GPU acceleration with memory optimization
    - Quantization for reduced memory usage
    - Streaming generation
    - Task-specific prompting
    - Performance monitoring
    """
    
    def __init__(self, config: LlamaConfig):
        self.config = config
        self.logger = logging.getLogger("llama_local")
        
        # Model components
        self.model = None
        self.tokenizer = None
        self.device = None
        self.generation_config = None
        
        # Performance tracking
        self.performance_metrics = {
            "total_requests": 0,
            "total_tokens_generated": 0,
            "average_tokens_per_second": 0.0,
            "memory_usage_mb": 0.0,
            "gpu_utilization": 0.0
        }
        
        # Task-specific prompts
        self.task_prompts = {
            TaskType.CODE_GENERATION: self._get_code_generation_prompt(),
            TaskType.CODE_REVIEW: self._get_code_review_prompt(),
            TaskType.DEBUGGING: self._get_debugging_prompt(),
            TaskType.DOCUMENTATION: self._get_documentation_prompt(),
            TaskType.EXPLANATION: self._get_explanation_prompt(),
            TaskType.REFACTORING: self._get_refactoring_prompt(),
            TaskType.TESTING: self._get_testing_prompt(),
            TaskType.GENERAL: self._get_general_prompt()
        }
        
        # Model mappings
        self.model_mappings = {
            LlamaModelSize.LLAMA_7B: "huggingface/CodeLlama-7b-hf",
            LlamaModelSize.LLAMA_13B: "huggingface/CodeLlama-13b-hf",
            LlamaModelSize.LLAMA2_7B: "meta-llama/Llama-2-7b-chat-hf",
            LlamaModelSize.LLAMA2_13B: "meta-llama/Llama-2-13b-chat-hf",
            LlamaModelSize.LLAMA2_70B: "meta-llama/Llama-2-70b-chat-hf",
            LlamaModelSize.CODE_LLAMA_7B: "codellama/CodeLlama-7b-Instruct-hf",
            LlamaModelSize.CODE_LLAMA_13B: "codellama/CodeLlama-13b-Instruct-hf",
            LlamaModelSize.CODE_LLAMA_34B: "codellama/CodeLlama-34b-Instruct-hf"
        }
    
    async def initialize(self) -> bool:
        """Initialize Llama model with optimizations"""
        try:
            self.logger.info(f"Initializing Llama {self.config.model_size.value}...")
            
            # Setup device
            await self._setup_device()
            
            # Load model and tokenizer
            await self._load_model()
            
            # Setup generation config
            self._setup_generation_config()
            
            # Warm up model
            await self._warmup_model()
            
            self.logger.info("Llama integration initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Llama: {e}")
            return False
    
    async def generate(self, request: GenerationRequest) -> GenerationResult:
        """
        Generate text using Llama model.
        
        Args:
            request: Generation request with prompt and parameters
            
        Returns:
            Generation result with text and performance metrics
        """
        start_time = time.time()
        request_id = f"llama_req_{int(start_time)}"
        
        try:
            self.logger.info(f"Processing generation request: {request_id}")
            
            # Prepare prompt
            formatted_prompt = self._format_prompt(request)
            
            # Tokenize input
            inputs = self.tokenizer(
                formatted_prompt,
                return_tensors="pt",
                truncation=True,
                max_length=4096
            ).to(self.device)
            
            prompt_tokens = inputs.input_ids.shape[1]
            
            # Generate text
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=request.max_tokens,
                    temperature=request.temperature,
                    top_p=request.top_p,
                    top_k=request.top_k,
                    repetition_penalty=request.repetition_penalty,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    generation_config=self.generation_config
                )
            
            # Decode generated text
            generated_text = self.tokenizer.decode(
                outputs[0][prompt_tokens:],
                skip_special_tokens=True
            )
            
            # Apply stop sequences
            if request.stop_sequences:
                for stop_seq in request.stop_sequences:
                    if stop_seq in generated_text:
                        generated_text = generated_text.split(stop_seq)[0]
                        break
            
            # Calculate metrics
            completion_tokens = outputs.shape[1] - prompt_tokens
            total_tokens = outputs.shape[1]
            generation_time = time.time() - start_time
            tokens_per_second = completion_tokens / generation_time if generation_time > 0 else 0
            
            # Update performance metrics
            await self._update_performance_metrics(completion_tokens, tokens_per_second)
            
            return GenerationResult(
                request_id=request_id,
                generated_text=generated_text,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                generation_time=generation_time,
                tokens_per_second=tokens_per_second,
                model_info={
                    "model_size": self.config.model_size.value,
                    "quantization": self.config.quantization.value,
                    "device": str(self.device)
                },
                metadata={
                    "task_type": request.task_type.value,
                    "temperature": request.temperature,
                    "top_p": request.top_p
                }
            )
            
        except Exception as e:
            self.logger.error(f"Generation failed for {request_id}: {e}")
            raise
    
    async def stream_generate(self, request: GenerationRequest) -> AsyncGenerator[str, None]:
        """
        Stream text generation in real-time.
        
        Args:
            request: Generation request
            
        Yields:
            Generated text chunks
        """
        try:
            # Prepare prompt
            formatted_prompt = self._format_prompt(request)
            
            # Tokenize input
            inputs = self.tokenizer(
                formatted_prompt,
                return_tensors="pt",
                truncation=True,
                max_length=4096
            ).to(self.device)
            
            prompt_length = inputs.input_ids.shape[1]
            
            # Generate tokens one by one
            with torch.no_grad():
                for _ in range(request.max_tokens):
                    # Generate next token
                    outputs = self.model(**inputs)
                    logits = outputs.logits[0, -1, :]
                    
                    # Apply temperature and sampling
                    if request.temperature > 0:
                        logits = logits / request.temperature
                        probs = F.softmax(logits, dim=-1)
                        
                        # Top-p sampling
                        if request.top_p < 1.0:
                            sorted_probs, sorted_indices = torch.sort(probs, descending=True)
                            cumulative_probs = torch.cumsum(sorted_probs, dim=-1)
                            sorted_indices_to_remove = cumulative_probs > request.top_p
                            sorted_indices_to_remove[1:] = sorted_indices_to_remove[:-1].clone()
                            sorted_indices_to_remove[0] = 0
                            indices_to_remove = sorted_indices[sorted_indices_to_remove]
                            probs[indices_to_remove] = 0
                            probs = probs / probs.sum()
                        
                        next_token = torch.multinomial(probs, num_samples=1)
                    else:
                        next_token = torch.argmax(logits, dim=-1, keepdim=True)
                    
                    # Check for EOS token
                    if next_token.item() == self.tokenizer.eos_token_id:
                        break
                    
                    # Decode and yield token
                    token_text = self.tokenizer.decode(next_token, skip_special_tokens=True)
                    yield token_text
                    
                    # Update inputs for next iteration
                    inputs.input_ids = torch.cat([inputs.input_ids, next_token.unsqueeze(0)], dim=1)
                    
                    # Check stop sequences
                    if request.stop_sequences:
                        current_text = self.tokenizer.decode(
                            inputs.input_ids[0][prompt_length:],
                            skip_special_tokens=True
                        )
                        if any(stop_seq in current_text for stop_seq in request.stop_sequences):
                            break
                    
                    # Memory management
                    if inputs.input_ids.shape[1] > 8192:  # Prevent excessive memory usage
                        break
                        
        except Exception as e:
            self.logger.error(f"Streaming generation failed: {e}")
            yield f"Error: {str(e)}"
    
    async def batch_generate(self, requests: List[GenerationRequest]) -> List[GenerationResult]:
        """Process multiple generation requests efficiently"""
        self.logger.info(f"Processing batch of {len(requests)} requests")
        
        # Process requests with memory management
        results = []
        batch_size = 2  # Adjust based on available memory
        
        for i in range(0, len(requests), batch_size):
            batch = requests[i:i + batch_size]
            
            # Process batch in parallel
            batch_tasks = [self.generate(req) for req in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Handle results and exceptions
            for result in batch_results:
                if isinstance(result, Exception):
                    self.logger.error(f"Batch generation failed: {result}")
                else:
                    results.append(result)
            
            # Memory cleanup between batches
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            gc.collect()
        
        return results
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        # Update system metrics
        memory_usage = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        gpu_utilization = 0.0
        if torch.cuda.is_available():
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu_utilization = gpus[0].load * 100
            except:
                pass
        
        self.performance_metrics.update({
            "memory_usage_mb": memory_usage,
            "gpu_utilization": gpu_utilization
        })
        
        return self.performance_metrics.copy()
    
    async def optimize_model(self) -> Dict[str, Any]:
        """Optimize model for better performance"""
        optimization_results = {
            "optimizations_applied": [],
            "memory_saved_mb": 0.0,
            "speed_improvement": 0.0
        }
        
        try:
            initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
            
            # Apply optimizations
            if hasattr(self.model, 'half') and self.device.type == 'cuda':
                self.model = self.model.half()
                optimization_results["optimizations_applied"].append("fp16_conversion")
            
            # Compile model for PyTorch 2.0+
            if hasattr(torch, 'compile') and torch.__version__ >= "2.0":
                self.model = torch.compile(self.model)
                optimization_results["optimizations_applied"].append("torch_compile")
            
            # Memory cleanup
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            gc.collect()
            
            final_memory = psutil.Process().memory_info().rss / 1024 / 1024
            optimization_results["memory_saved_mb"] = initial_memory - final_memory
            
            self.logger.info(f"Model optimization complete: {optimization_results}")
            return optimization_results
            
        except Exception as e:
            self.logger.error(f"Model optimization failed: {e}")
            return optimization_results
    
    # Private Methods
    
    async def _setup_device(self) -> None:
        """Setup compute device"""
        if self.config.use_gpu and torch.cuda.is_available():
            self.device = torch.device("cuda")
            
            # Set memory fraction
            if self.config.gpu_memory_fraction < 1.0:
                torch.cuda.set_per_process_memory_fraction(self.config.gpu_memory_fraction)
            
            self.logger.info(f"Using GPU: {torch.cuda.get_device_name()}")
            self.logger.info(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
        else:
            self.device = torch.device("cpu")
            self.logger.info("Using CPU")
    
    async def _load_model(self) -> None:
        """Load model and tokenizer with optimizations"""
        model_name = self.config.custom_model_path or self.model_mappings[self.config.model_size]
        
        # Setup quantization config
        quantization_config = None
        if self.config.quantization == QuantizationMode.INT8:
            quantization_config = BitsAndBytesConfig(load_in_8bit=True)
        elif self.config.quantization == QuantizationMode.INT4:
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True
            )
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            cache_dir=self.config.cache_dir,
            trust_remote_code=True
        )
        
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Load model
        model_kwargs = {
            "cache_dir": self.config.cache_dir,
            "trust_remote_code": True,
            "torch_dtype": torch.float16 if self.device.type == "cuda" else torch.float32
        }
        
        if quantization_config:
            model_kwargs["quantization_config"] = quantization_config
        elif self.device.type == "cuda":
            model_kwargs["device_map"] = "auto"
        
        self.model = AutoModelForCausalLM.from_pretrained(model_name, **model_kwargs)
        
        if self.device.type == "cpu" and not quantization_config:
            self.model = self.model.to(self.device)
        
        # Set to evaluation mode
        self.model.eval()
        
        self.logger.info(f"Loaded {model_name} with {self.config.quantization.value} quantization")
    
    def _setup_generation_config(self) -> None:
        """Setup generation configuration"""
        self.generation_config = GenerationConfig(
            do_sample=True,
            pad_token_id=self.tokenizer.eos_token_id,
            eos_token_id=self.tokenizer.eos_token_id,
            use_cache=True
        )
    
    async def _warmup_model(self) -> None:
        """Warm up model with a test generation"""
        try:
            warmup_prompt = "def hello_world():"
            inputs = self.tokenizer(warmup_prompt, return_tensors="pt").to(self.device)
            
            with torch.no_grad():
                _ = self.model.generate(
                    **inputs,
                    max_new_tokens=10,
                    do_sample=False,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            self.logger.info("Model warmup completed")
            
        except Exception as e:
            self.logger.warning(f"Model warmup failed: {e}")
    
    def _format_prompt(self, request: GenerationRequest) -> str:
        """Format prompt based on task type"""
        task_template = self.task_prompts[request.task_type]
        
        context_str = ""
        if request.context:
            context_str = f"Context: {request.context}\n\n"
        
        return task_template.format(
            context=context_str,
            prompt=request.prompt
        )
    
    async def _update_performance_metrics(self, tokens_generated: int, tokens_per_second: float) -> None:
        """Update performance metrics"""
        self.performance_metrics["total_requests"] += 1
        self.performance_metrics["total_tokens_generated"] += tokens_generated
        
        # Update average tokens per second
        current_avg = self.performance_metrics["average_tokens_per_second"]
        total_requests = self.performance_metrics["total_requests"]
        self.performance_metrics["average_tokens_per_second"] = (
            (current_avg * (total_requests - 1) + tokens_per_second) / total_requests
        )
    
    # Task-specific prompt templates
    
    def _get_code_generation_prompt(self) -> str:
        return """You are an expert software developer. Generate high-quality code based on the requirements.

{context}Requirements: {prompt}

Please provide clean, well-documented code with appropriate comments:"""
    
    def _get_code_review_prompt(self) -> str:
        return """You are an expert code reviewer. Analyze the following code and provide detailed feedback.

{context}Code to review:
{prompt}

Please provide:
1. Code quality assessment
2. Potential issues or bugs
3. Suggestions for improvement
4. Best practices recommendations

Review:"""
    
    def _get_debugging_prompt(self) -> str:
        return """You are an expert debugger. Help identify and fix the issue in the following code.

{context}Problem description and code:
{prompt}

Please provide:
1. Issue identification
2. Root cause analysis
3. Step-by-step fix
4. Prevention strategies

Debug analysis:"""
    
    def _get_documentation_prompt(self) -> str:
        return """You are a technical documentation expert. Create comprehensive documentation for the following code.

{context}Code to document:
{prompt}

Please provide:
1. Overview and purpose
2. Function/class descriptions
3. Parameter explanations
4. Usage examples
5. Return value descriptions

Documentation:"""
    
    def _get_explanation_prompt(self) -> str:
        return """You are a programming instructor. Explain the following code in detail.

{context}Code to explain:
{prompt}

Please provide:
1. High-level overview
2. Step-by-step breakdown
3. Key concepts explanation
4. Why this approach is used

Explanation:"""
    
    def _get_refactoring_prompt(self) -> str:
        return """You are a refactoring expert. Improve the following code while maintaining functionality.

{context}Code to refactor:
{prompt}

Please provide:
1. Refactored code
2. Explanation of changes
3. Benefits of the refactoring
4. Any trade-offs

Refactored code:"""
    
    def _get_testing_prompt(self) -> str:
        return """You are a testing expert. Create comprehensive tests for the following code.

{context}Code to test:
{prompt}

Please provide:
1. Unit tests
2. Edge case tests
3. Integration tests (if applicable)
4. Test explanations

Test code:"""
    
    def _get_general_prompt(self) -> str:
        return """You are a helpful AI assistant. Please respond to the following request.

{context}Request: {prompt}

Response:"""
    
    async def cleanup(self) -> None:
        """Cleanup resources"""
        if self.model:
            del self.model
        if self.tokenizer:
            del self.tokenizer
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        gc.collect()
        self.logger.info("Llama integration cleanup complete")