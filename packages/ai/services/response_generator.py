"""
Response Generator Service

Focused service for generating AI responses with proper validation and error handling.
"""

import asyncio
import logging
import time
from typing import Dict, Optional, Any, Union
from datetime import datetime

from ..schemas import GenerationRequest, GenerationResponse
from .fallback_manager import FallbackManager

logger = logging.getLogger(__name__)


class ResponseGenerator:
    """
    Focused service for AI response generation.
    
    Responsibilities:
    - Generate text responses using loaded models
    - Generate code using specialized models
    - Handle generation errors gracefully
    - Track generation metrics
    - Implement fallback strategies
    """
    
    def __init__(self, model_loader, fallback_manager: Optional[FallbackManager] = None):
        self.model_loader = model_loader
        self.fallback_manager = fallback_manager or FallbackManager()
        self.active_model: Optional[str] = None
        
    async def generate_text(self, request: GenerationRequest, model_id: Optional[str] = None) -> GenerationResponse:
        """
        Generate text using the specified or active model.
        
        Args:
            request: Validated generation request
            model_id: Optional specific model to use
            
        Returns:
            GenerationResponse: Response with generated text and metadata
        """
        target_model = model_id or self.active_model
        start_time = time.time()
        
        if not target_model:
            return GenerationResponse(
                content="",
                model_used="none",
                status="error",
                error="No active model available",
                response_time=time.time() - start_time
            )
        
        if not self.model_loader.is_model_loaded(target_model):
            # Try fallback strategy
            fallback_result = await self.fallback_manager.handle_model_unavailable(target_model, request)
            if fallback_result:
                return fallback_result
            
            return GenerationResponse(
                content="",
                model_used=target_model,
                status="error", 
                error=f"Model {target_model} not loaded",
                response_time=time.time() - start_time
            )
        
        try:
            models = self.model_loader.get_loaded_models()
            model = models[target_model]
            
            # Generate response based on task type
            if request.task_type == "code_generation":
                content = await self._generate_code_response(model, request)
            else:
                content = await self._generate_text_response(model, request)
            
            return GenerationResponse(
                content=content,
                model_used=target_model,
                status="completed",
                response_time=time.time() - start_time,
                tokens_used=self._estimate_tokens(request.prompt + content),
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error generating response with model {target_model}: {e}")
            
            # Try fallback strategy
            fallback_result = await self.fallback_manager.handle_generation_error(target_model, request, str(e))
            if fallback_result:
                return fallback_result
            
            return GenerationResponse(
                content="",
                model_used=target_model,
                status="error",
                error=str(e),
                response_time=time.time() - start_time
            )
    
    async def generate_code(self, request: GenerationRequest, model_id: Optional[str] = None) -> GenerationResponse:
        """
        Generate code using the specified or active model.
        
        Args:
            request: Code generation request
            model_id: Optional specific model to use
            
        Returns:
            GenerationResponse: Response with generated code and metadata
        """
        # Set task type for code generation
        request.task_type = "code_generation"
        return await self.generate_text(request, model_id)
    
    async def _generate_text_response(self, model: Any, request: GenerationRequest) -> str:
        """Generate text response using the model."""
        if hasattr(model, 'generate'):
            return await model.generate(
                request.prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                top_k=request.top_k
            )
        else:
            raise ValueError(f"Model does not support text generation")
    
    async def _generate_code_response(self, model: Any, request: GenerationRequest) -> str:
        """Generate code response using specialized model method."""
        if hasattr(model, 'generate_code'):
            # Convert request to code generation format
            code_request = {
                "task_description": request.prompt,
                "language": getattr(request, 'language', 'python'),
                "framework": getattr(request, 'framework', 'fastapi'),
                "database": getattr(request, 'database', 'postgresql'),
                "features": getattr(request, 'features', ["auth", "tests"])
            }
            
            result = await model.generate_code(code_request)
            return result.get("generated_code", "") if isinstance(result, dict) else str(result)
        else:
            # Fallback to text generation with code prompt
            code_prompt = f"Generate {getattr(request, 'language', 'python')} code for: {request.prompt}"
            return await self._generate_text_response(model, GenerationRequest(
                prompt=code_prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            ))
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        # Simple estimation: ~1.3 tokens per word
        return int(len(text.split()) * 1.3)
    
    def set_active_model(self, model_id: str):
        """Set the active model for generation."""
        if self.model_loader.is_model_loaded(model_id):
            self.active_model = model_id
            logger.info(f"Set active model to: {model_id}")
        else:
            logger.warning(f"Cannot set active model to {model_id}: model not loaded")
    
    def get_active_model(self) -> Optional[str]:
        """Get the currently active model."""
        return self.active_model
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the response generator."""
        return {
            "active_model": self.active_model,
            "loaded_models": list(self.model_loader.get_loaded_models().keys()),
            "fallback_available": self.fallback_manager is not None,
            "status": "healthy" if self.active_model else "no_active_model"
        }