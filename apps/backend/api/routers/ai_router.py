#!/usr/bin/env python3
"""
AI Service Router
Handles AI generation requests and model management
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, Any, Optional
from pydantic import BaseModel
import sys
from pathlib import Path

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from apps.backend.services.ai_service import ProductionAIService, GenerationRequest, GenerationResponse

router = APIRouter()

class AIGenerationRequest(BaseModel):
    """AI generation request model"""
    prompt: str
    model_preference: Optional[str] = "auto"
    max_tokens: int = 1000
    temperature: float = 0.7
    force_local: bool = True
    fallback_allowed: bool = True
    cost_limit: Optional[float] = None

class AIGenerationResponse(BaseModel):
    """AI generation response model"""
    content: str
    model_used: str
    tokens_used: int
    cost: float
    response_time: float
    success: bool
    error_message: Optional[str] = None

async def get_ai_service(request: Request) -> ProductionAIService:
    """Get AI service from app state"""
    return request.app.state.ai_service

@router.post("/generate", response_model=AIGenerationResponse)
async def generate_ai_response(
    request: AIGenerationRequest,
    ai_service: ProductionAIService = Depends(get_ai_service)
):
    """Generate AI response with cost optimization"""
    try:
        # Convert to internal request format
        generation_request = GenerationRequest(
            prompt=request.prompt,
            model_preference=request.model_preference,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            force_local=request.force_local,
            fallback_allowed=request.fallback_allowed,
            cost_limit=request.cost_limit
        )
        
        # Generate response
        response = await ai_service.generate_with_cost_optimization(generation_request)
        
        # Convert to API response format
        return AIGenerationResponse(
            content=response.content,
            model_used=response.model_used,
            tokens_used=response.tokens_used,
            cost=response.cost,
            response_time=response.response_time,
            success=response.success,
            error_message=response.error_message
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models")
async def get_available_models(ai_service: ProductionAIService = Depends(get_ai_service)):
    """Get available AI models and their status"""
    try:
        # Get model status from the enhanced model manager
        model_status = ai_service.local_manager.get_health_status()
        return {
            "models": model_status,
            "local_models": ["deepseek-r1", "llama"],
            "cloud_models": ["openai-gpt4", "anthropic-claude", "gemini-pro"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cost-summary")
async def get_cost_summary(ai_service: ProductionAIService = Depends(get_ai_service)):
    """Get cost optimization summary"""
    try:
        return ai_service.get_cost_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance")
async def get_performance_summary(ai_service: ProductionAIService = Depends(get_ai_service)):
    """Get AI service performance summary"""
    try:
        return ai_service.get_performance_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))