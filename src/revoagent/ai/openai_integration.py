"""
OpenAI API Integration

Integration with OpenAI API for fallback and comparison capabilities.
"""

import asyncio
import logging
import os
from typing import Optional, Dict, Any, List
import openai

from .model_manager import ModelConfig

logger = logging.getLogger(__name__)

class OpenAIModel:
    """
    OpenAI API integration for fallback capabilities.
    
    Provides access to OpenAI models when local models are not available
    or for comparison purposes.
    """
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.client = None
        self.is_loaded = False
        self.api_key = os.getenv("OPENAI_API_KEY")
        
    async def load(self) -> bool:
        """
        Initialize OpenAI client.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.api_key:
                logger.warning("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
                return False
            
            self.client = openai.AsyncOpenAI(api_key=self.api_key)
            self.is_loaded = True
            logger.info("OpenAI client initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {str(e)}")
            return False
    
    async def unload(self):
        """Cleanup OpenAI client."""
        self.client = None
        self.is_loaded = False
        logger.info("OpenAI client unloaded")
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text using OpenAI API.
        
        Args:
            prompt: Input prompt
            **kwargs: Additional generation parameters
            
        Returns:
            str: Generated text
        """
        if not self.is_loaded:
            raise RuntimeError("OpenAI client not initialized. Call load() first.")
        
        try:
            # Handle chat format if messages are provided
            messages = kwargs.get("messages")
            if messages:
                chat_messages = messages
            else:
                chat_messages = [{"role": "user", "content": prompt}]
            
            # Prepare parameters
            model = kwargs.get("model", "gpt-3.5-turbo")
            max_tokens = kwargs.get("max_tokens", 1000)
            temperature = kwargs.get("temperature", self.config.temperature)
            
            # Make API call
            response = await self.client.chat.completions.create(
                model=model,
                messages=chat_messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content.strip()
            
            return ""
            
        except Exception as e:
            logger.error(f"Error generating text with OpenAI: {str(e)}")
            raise
    
    async def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Generate chat completion using OpenAI API.
        
        Args:
            messages: List of chat messages
            **kwargs: Additional parameters
            
        Returns:
            str: Generated response
        """
        return await self.generate("", messages=messages, **kwargs)
    
    async def generate_code(self, task_description: str, language: str = "python", **kwargs) -> str:
        """
        Generate code using OpenAI API.
        
        Args:
            task_description: Description of the coding task
            language: Programming language
            **kwargs: Additional parameters
            
        Returns:
            str: Generated code
        """
        code_prompt = f"""You are an expert {language} programmer. Generate clean, efficient, and well-documented code for the following task:

Task: {task_description}

Requirements:
- Write production-ready code
- Include proper error handling
- Add clear comments and docstrings
- Follow best practices for {language}
- Make the code modular and reusable

Please provide only the code without additional explanation."""
        
        return await self.generate(code_prompt, model="gpt-4", **kwargs)
    
    async def debug_code(self, code: str, error_message: str = "", **kwargs) -> str:
        """
        Debug and fix code using OpenAI API.
        
        Args:
            code: Code to debug
            error_message: Optional error message
            **kwargs: Additional parameters
            
        Returns:
            str: Fixed code with explanation
        """
        debug_prompt = f"""You are an expert debugger. Analyze the following code and fix any issues:

Code:
```
{code}
```

{f"Error message: {error_message}" if error_message else ""}

Please:
1. Identify the issues in the code
2. Provide the corrected code
3. Explain what was wrong and how you fixed it"""
        
        return await self.generate(debug_prompt, model="gpt-4", **kwargs)
    
    def get_memory_usage(self) -> float:
        """Get memory usage (always 0 for API)."""
        return 0.0
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            "model_type": "openai_api",
            "is_loaded": self.is_loaded,
            "memory_usage_gb": 0.0,
            "api_key_configured": bool(self.api_key),
        }