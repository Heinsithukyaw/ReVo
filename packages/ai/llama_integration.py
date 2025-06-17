"""
Llama Model Integration

Integration with Llama models for local LLM capabilities.
"""

import asyncio
import logging
import torch
from typing import Optional, Dict, Any, List
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM, 
    pipeline,
    BitsAndBytesConfig
)
import gc

from .model_manager import ModelConfig

logger = logging.getLogger(__name__)

class LlamaModel:
    """
    Llama model integration for local LLM capabilities.
    
    Supports various Llama model variants with optimizations.
    """
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.model = None
        self.tokenizer = None
        self.pipeline = None
        self.device = self._determine_device()
        self.is_loaded = False
        
    def _determine_device(self) -> str:
        """Determine the best device for model execution."""
        if self.config.device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            elif hasattr(torch, 'backends') and torch.backends.mps.is_available():
                return "mps"
            else:
                return "cpu"
        return self.config.device
    
    def _get_quantization_config(self) -> Optional[BitsAndBytesConfig]:
        """Get quantization configuration if specified."""
        if not self.config.quantization:
            return None
            
        if self.config.quantization == "4bit":
            return BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4"
            )
        elif self.config.quantization == "8bit":
            return BitsAndBytesConfig(
                load_in_8bit=True
            )
        
        return None
    
    async def load(self) -> bool:
        """
        Load the Llama model and tokenizer.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Loading Llama model from {self.config.model_path}")
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.config.model_path,
                trust_remote_code=self.config.trust_remote_code
            )
            
            # Set pad token if not present
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Configure model loading parameters
            model_kwargs = {
                "trust_remote_code": self.config.trust_remote_code,
                "torch_dtype": torch.float16 if self.device != "cpu" else torch.float32,
                "device_map": "auto" if self.device == "cuda" else None,
            }
            
            # Add quantization if specified
            quantization_config = self._get_quantization_config()
            if quantization_config:
                model_kwargs["quantization_config"] = quantization_config
            
            # Load model
            self.model = AutoModelForCausalLM.from_pretrained(
                self.config.model_path,
                **model_kwargs
            )
            
            # Move to device if not using device_map
            if self.device != "cuda" or not model_kwargs.get("device_map"):
                self.model = self.model.to(self.device)
            
            # Create pipeline for easier text generation
            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device == "cuda" else -1,
                trust_remote_code=self.config.trust_remote_code
            )
            
            self.is_loaded = True
            logger.info("Llama model loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load Llama model: {str(e)}")
            await self.unload()
            return False
    
    async def unload(self):
        """Unload the model to free memory."""
        try:
            if self.pipeline:
                del self.pipeline
                self.pipeline = None
            
            if self.model:
                del self.model
                self.model = None
            
            if self.tokenizer:
                del self.tokenizer
                self.tokenizer = None
            
            # Clear GPU cache
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            # Force garbage collection
            gc.collect()
            
            self.is_loaded = False
            logger.info("Llama model unloaded")
            
        except Exception as e:
            logger.error(f"Error unloading Llama model: {str(e)}")
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text using the Llama model.
        
        Args:
            prompt: Input prompt
            **kwargs: Additional generation parameters
            
        Returns:
            str: Generated text
        """
        if not self.is_loaded:
            raise RuntimeError("Model not loaded. Call load() first.")
        
        try:
            # Prepare generation parameters
            generation_params = {
                "max_length": kwargs.get("max_length", self.config.max_length),
                "temperature": kwargs.get("temperature", self.config.temperature),
                "top_p": kwargs.get("top_p", self.config.top_p),
                "top_k": kwargs.get("top_k", self.config.top_k),
                "do_sample": kwargs.get("do_sample", self.config.do_sample),
                "num_return_sequences": 1,
                "pad_token_id": self.tokenizer.eos_token_id,
                "return_full_text": False
            }
            
            # Handle chat format if messages are provided
            messages = kwargs.get("messages")
            if messages:
                # Format as chat using Llama chat template
                formatted_prompt = self._format_chat_messages(messages)
            else:
                formatted_prompt = prompt
            
            # Generate text
            result = self.pipeline(
                formatted_prompt,
                **generation_params
            )
            
            # Extract generated text
            if result and len(result) > 0:
                generated_text = result[0]["generated_text"]
                return generated_text.strip()
            
            return ""
            
        except Exception as e:
            logger.error(f"Error generating text with Llama: {str(e)}")
            raise
    
    def _format_chat_messages(self, messages: List[Dict[str, str]]) -> str:
        """
        Format chat messages for Llama model.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            
        Returns:
            str: Formatted prompt
        """
        # Use Llama chat template if available
        if hasattr(self.tokenizer, 'apply_chat_template'):
            try:
                return self.tokenizer.apply_chat_template(
                    messages, 
                    tokenize=False, 
                    add_generation_prompt=True
                )
            except:
                pass
        
        # Fallback to manual formatting
        formatted_parts = []
        
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            
            if role == "system":
                formatted_parts.append(f"<|system|>\n{content}<|end|>")
            elif role == "user":
                formatted_parts.append(f"<|user|>\n{content}<|end|>")
            elif role == "assistant":
                formatted_parts.append(f"<|assistant|>\n{content}<|end|>")
        
        # Add assistant prompt
        formatted_parts.append("<|assistant|>")
        
        return "\n".join(formatted_parts)
    
    async def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Generate chat completion using the Llama model.
        
        Args:
            messages: List of chat messages
            **kwargs: Additional parameters
            
        Returns:
            str: Generated response
        """
        return await self.generate("", messages=messages, **kwargs)
    
    async def generate_summary(self, text: str, **kwargs) -> str:
        """
        Generate a summary of the given text.
        
        Args:
            text: Text to summarize
            **kwargs: Additional parameters
            
        Returns:
            str: Generated summary
        """
        summary_prompt = f"""Please provide a concise summary of the following text:

Text:
{text}

Summary:"""
        
        return await self.generate(summary_prompt, **kwargs)
    
    async def answer_question(self, question: str, context: str = "", **kwargs) -> str:
        """
        Answer a question, optionally with context.
        
        Args:
            question: Question to answer
            context: Optional context
            **kwargs: Additional parameters
            
        Returns:
            str: Generated answer
        """
        if context:
            qa_prompt = f"""Based on the following context, please answer the question:

Context:
{context}

Question: {question}

Answer:"""
        else:
            qa_prompt = f"""Question: {question}

Answer:"""
        
        return await self.generate(qa_prompt, **kwargs)
    
    def get_memory_usage(self) -> float:
        """Get model memory usage in GB."""
        if not self.is_loaded or not self.model:
            return 0.0
        
        try:
            if hasattr(self.model, 'get_memory_footprint'):
                return self.model.get_memory_footprint() / (1024**3)
            
            # Estimate based on parameters
            total_params = sum(p.numel() for p in self.model.parameters())
            # Assume 2 bytes per parameter (float16)
            estimated_memory = total_params * 2 / (1024**3)
            return estimated_memory
            
        except Exception:
            return 0.0
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get detailed model information."""
        info = {
            "model_path": self.config.model_path,
            "device": self.device,
            "is_loaded": self.is_loaded,
            "memory_usage_gb": self.get_memory_usage(),
            "quantization": self.config.quantization,
        }
        
        if self.is_loaded and self.model:
            try:
                total_params = sum(p.numel() for p in self.model.parameters())
                info["total_parameters"] = total_params
                info["model_size"] = f"{total_params / 1e9:.1f}B"
            except:
                pass
        
        return info