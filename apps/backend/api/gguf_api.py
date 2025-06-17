#!/usr/bin/env python3
"""
GGUF API Integration for reVoAgent Backend
Provides RESTful API endpoints for local GGUF model management and inference

This module exposes:
- Model management endpoints (load, unload, status)
- Inference endpoints (generate, chat completion)
- Performance monitoring endpoints
- Cost optimization endpoints
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

# Configure logging
logger = logging.getLogger(__name__)

# Request/Response Models
class GGUFGenerationRequest(BaseModel):
    """Request model for GGUF generation"""
    prompt: str = Field(..., description="Input prompt for generation")
    model_id: str = Field(default="deepseek-r1", description="Model ID to use")
    max_tokens: int = Field(default=2048, ge=1, le=4096, description="Maximum tokens to generate")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    top_p: float = Field(default=0.9, ge=0.0, le=1.0, description="Top-p sampling")
    top_k: int = Field(default=40, ge=1, le=100, description="Top-k sampling")
    repeat_penalty: float = Field(default=1.1, ge=1.0, le=2.0, description="Repeat penalty")

class GGUFChatMessage(BaseModel):
    """Chat message model"""
    role: str = Field(..., description="Message role (user, assistant, system)")
    content: str = Field(..., description="Message content")

class GGUFChatRequest(BaseModel):
    """Request model for GGUF chat completion"""
    messages: List[GGUFChatMessage] = Field(..., description="Chat messages")
    model_id: str = Field(default="deepseek-r1", description="Model ID to use")
    max_tokens: int = Field(default=2048, ge=1, le=4096, description="Maximum tokens to generate")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    top_p: float = Field(default=0.9, ge=0.0, le=1.0, description="Top-p sampling")
    top_k: int = Field(default=40, ge=1, le=100, description="Top-k sampling")

class GGUFResponse(BaseModel):
    """Response model for GGUF operations"""
    success: bool = Field(..., description="Operation success status")
    content: str = Field(default="", description="Generated content")
    model_used: str = Field(default="", description="Model ID used")
    tokens_generated: int = Field(default=0, description="Number of tokens generated")
    inference_time: float = Field(default=0.0, description="Inference time in seconds")
    tokens_per_second: float = Field(default=0.0, description="Generation speed")
    cost: float = Field(default=0.0, description="Cost (always $0.00 for GGUF)")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")

class ModelLoadRequest(BaseModel):
    """Request model for loading models"""
    model_id: str = Field(..., description="Model ID to load")
    force_reload: bool = Field(default=False, description="Force reload if already loaded")

class ModelStatusResponse(BaseModel):
    """Response model for model status"""
    model_id: str
    model_name: str
    loaded: bool
    load_time: float
    memory_usage_mb: float
    inferences: int
    total_tokens: int
    average_speed: float
    cost_per_inference: float

class GGUFMetricsResponse(BaseModel):
    """Response model for GGUF metrics"""
    performance: Dict[str, Any]
    resource_usage: Dict[str, Any]
    cost_optimization: Dict[str, Any]
    models: Dict[str, Any]

# Global GGUF manager instance
gguf_manager = None

async def get_gguf_manager():
    """Get or create GGUF manager instance"""
    global gguf_manager
    
    if gguf_manager is None:
        try:
            from src.packages.ai.gguf_model_manager import create_gguf_manager, GGUF_AVAILABLE
            
            if not GGUF_AVAILABLE:
                raise HTTPException(
                    status_code=503,
                    detail="GGUF not available - llama-cpp-python not installed"
                )
            
            gguf_manager = await create_gguf_manager()
            logger.info("✅ GGUF Manager initialized for API")
            
        except ImportError:
            raise HTTPException(
                status_code=503,
                detail="GGUF integration not available - missing dependencies"
            )
    
    return gguf_manager

# Create API router
router = APIRouter(prefix="/api/gguf", tags=["GGUF Models"])

@router.get("/health")
async def gguf_health():
    """Check GGUF service health"""
    try:
        manager = await get_gguf_manager()
        models = manager.list_available_models()
        
        return {
            "status": "healthy",
            "gguf_available": True,
            "available_models": models,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "gguf_available": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@router.get("/models")
async def list_models() -> List[str]:
    """List available GGUF models"""
    try:
        manager = await get_gguf_manager()
        return manager.list_available_models()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/{model_id}/status")
async def get_model_status(model_id: str) -> ModelStatusResponse:
    """Get status of a specific model"""
    try:
        manager = await get_gguf_manager()
        model_info = manager.get_model_info(model_id)
        
        if not model_info:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
        
        return ModelStatusResponse(**model_info)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/models/{model_id}/load")
async def load_model(model_id: str, request: ModelLoadRequest, background_tasks: BackgroundTasks):
    """Load a GGUF model into memory"""
    try:
        manager = await get_gguf_manager()
        
        # Check if model exists
        available_models = manager.list_available_models()
        if model_id not in available_models:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
        
        # Check if already loaded
        if manager.is_model_loaded(model_id) and not request.force_reload:
            return {
                "success": True,
                "message": f"Model {model_id} already loaded",
                "model_id": model_id,
                "loaded": True
            }
        
        # Load model in background
        async def load_model_task():
            try:
                success = await manager.load_model(model_id)
                logger.info(f"Model {model_id} load result: {success}")
            except Exception as e:
                logger.error(f"Failed to load model {model_id}: {e}")
        
        background_tasks.add_task(load_model_task)
        
        return {
            "success": True,
            "message": f"Loading model {model_id} in background",
            "model_id": model_id,
            "loaded": False,
            "loading": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/models/{model_id}/unload")
async def unload_model(model_id: str):
    """Unload a GGUF model from memory"""
    try:
        manager = await get_gguf_manager()
        
        if not manager.is_model_loaded(model_id):
            raise HTTPException(status_code=400, detail=f"Model {model_id} not loaded")
        
        success = manager.unload_model(model_id)
        
        return {
            "success": success,
            "message": f"Model {model_id} unloaded",
            "model_id": model_id,
            "loaded": False
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate")
async def generate_text(request: GGUFGenerationRequest) -> GGUFResponse:
    """Generate text using GGUF model"""
    try:
        manager = await get_gguf_manager()
        
        # Check if model is loaded
        if not manager.is_model_loaded(request.model_id):
            raise HTTPException(
                status_code=400,
                detail=f"Model {request.model_id} not loaded. Load it first using /models/{request.model_id}/load"
            )
        
        # Generate response
        response = await manager.generate_response(
            request.model_id,
            request.prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            top_k=request.top_k,
            repeat_penalty=request.repeat_penalty
        )
        
        return GGUFResponse(
            success=response.success,
            content=response.text,
            model_used=request.model_id,
            tokens_generated=response.tokens_generated,
            inference_time=response.inference_time,
            tokens_per_second=response.tokens_per_second,
            cost=0.0,  # Always free for GGUF models
            error_message=response.error_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/completions")
async def chat_completion(request: GGUFChatRequest) -> GGUFResponse:
    """Generate chat completion using GGUF model"""
    try:
        manager = await get_gguf_manager()
        
        # Check if model is loaded
        if not manager.is_model_loaded(request.model_id):
            raise HTTPException(
                status_code=400,
                detail=f"Model {request.model_id} not loaded. Load it first using /models/{request.model_id}/load"
            )
        
        # Convert messages to the format expected by GGUF manager
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in request.messages
        ]
        
        # Generate chat completion
        response = await manager.chat_completion(
            request.model_id,
            messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            top_k=request.top_k
        )
        
        return GGUFResponse(
            success=response.success,
            content=response.text,
            model_used=request.model_id,
            tokens_generated=response.tokens_generated,
            inference_time=response.inference_time,
            tokens_per_second=response.tokens_per_second,
            cost=0.0,  # Always free for GGUF models
            error_message=response.error_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat completion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics")
async def get_metrics() -> GGUFMetricsResponse:
    """Get comprehensive GGUF metrics"""
    try:
        manager = await get_gguf_manager()
        metrics = manager.get_metrics()
        
        return GGUFMetricsResponse(
            performance=metrics["performance"],
            resource_usage=metrics["resource_usage"],
            cost_optimization=metrics["cost_optimization"],
            models=metrics["models"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cost-savings")
async def get_cost_savings():
    """Get cost savings analysis for GGUF vs cloud models"""
    try:
        manager = await get_gguf_manager()
        metrics = manager.get_metrics()
        
        total_inferences = metrics["performance"]["total_inferences"]
        gguf_cost = 0.0  # Always free
        estimated_cloud_cost = total_inferences * 0.03  # Estimate GPT-4 cost
        savings = estimated_cloud_cost - gguf_cost
        savings_percentage = (savings / max(estimated_cloud_cost, 0.01)) * 100
        
        return {
            "total_inferences": total_inferences,
            "gguf_cost": gguf_cost,
            "estimated_cloud_cost": estimated_cloud_cost,
            "total_savings": savings,
            "savings_percentage": savings_percentage,
            "cost_per_inference": 0.0,
            "cloud_cost_per_inference": 0.03,
            "roi_analysis": {
                "daily_savings": savings if total_inferences > 0 else 0,
                "monthly_savings": savings * 30 if total_inferences > 0 else 0,
                "yearly_savings": savings * 365 if total_inferences > 0 else 0
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/shutdown")
async def shutdown_gguf():
    """Shutdown GGUF service and unload all models"""
    try:
        global gguf_manager
        
        if gguf_manager:
            gguf_manager.unload_all_models()
            gguf_manager = None
        
        return {
            "success": True,
            "message": "GGUF service shutdown complete",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Initialize on module import
async def initialize_gguf_api():
    """Initialize GGUF API on startup"""
    try:
        await get_gguf_manager()
        logger.info("🚀 GGUF API initialized successfully")
    except Exception as e:
        logger.error(f"⚠️ GGUF API initialization failed: {e}")

# Export router for main app
__all__ = ["router", "initialize_gguf_api"]
