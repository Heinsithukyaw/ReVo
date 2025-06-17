import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our enhanced model manager
try:
    from packages.ai.enhanced_local_model_manager import (
        EnhancedLocalModelManager, 
        GenerationRequest, 
        ModelProvider
    )
except ImportError:
    logger.warning("Could not import enhanced model manager, using fallback")
    EnhancedLocalModelManager = None

app = FastAPI(
    title="reVoAgent Enhanced Backend",
    description="Enhanced backend with intelligent AI model fallbacks",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model manager
model_manager: Optional[EnhancedLocalModelManager] = None

class ChatRequest(BaseModel):
    content: str
    system_prompt: Optional[str] = None
    max_tokens: int = 1024
    temperature: float = 0.7

class ChatResponse(BaseModel):
    content: str
    provider: str
    tokens_used: int
    generation_time: float

@app.on_event("startup")
async def startup_event():
    """Initialize the application"""
    global model_manager
    
    logger.info("🚀 Starting reVoAgent Enhanced Backend...")
    
    # Initialize model manager
    if EnhancedLocalModelManager:
        config = {
            "openai_api_key": os.getenv("OPENAI_API_KEY"),
            "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
        }
        
        model_manager = EnhancedLocalModelManager(config)
        await model_manager.initialize_with_fallback()
    
    logger.info("✅ Backend initialization complete")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health_data = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "services": {
            "backend": "running",
            "database": "checking...",
            "redis": "checking...",
            "ai_models": "checking..."
        }
    }
    
    # Check model manager
    if model_manager:
        try:
            model_health = await model_manager.health_check()
            health_data["services"]["ai_models"] = model_health["status"]
            health_data["ai_providers"] = model_health.get("available_providers", [])
        except Exception as e:
            health_data["services"]["ai_models"] = f"error: {str(e)}"
    else:
        health_data["services"]["ai_models"] = "not_initialized"
    
    return health_data

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Chat endpoint with AI model integration"""
    try:
        if not model_manager:
            raise HTTPException(status_code=503, detail="AI models not available")
        
        # Create generation request
        gen_request = GenerationRequest(
            prompt=request.content,
            system_prompt=request.system_prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        # Generate response
        response = await model_manager.generate(gen_request)
        
        return ChatResponse(
            content=response.content,
            provider=response.provider.value,
            tokens_used=response.tokens_used,
            generation_time=response.generation_time
        )
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/models")
async def list_models():
    """List available AI models"""
    if not model_manager:
        return {"models": [], "status": "not_initialized"}
    
    try:
        health = await model_manager.health_check()
        return {
            "models": health.get("available_providers", []),
            "status": health["status"],
            "resources": health.get("resources", {})
        }
    except Exception as e:
        return {"models": [], "status": f"error: {str(e)}"}

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for real-time chat"""
    await websocket.accept()
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            
            if not model_manager:
                await websocket.send_json({
                    "error": "AI models not available",
                    "type": "error"
                })
                continue
            
            # Process chat request
            try:
                gen_request = GenerationRequest(
                    prompt=data.get("content", ""),
                    system_prompt=data.get("system_prompt"),
                    max_tokens=data.get("max_tokens", 1024),
                    temperature=data.get("temperature", 0.7)
                )
                
                response = await model_manager.generate(gen_request)
                
                await websocket.send_json({
                    "content": response.content,
                    "provider": response.provider.value,
                    "tokens_used": response.tokens_used,
                    "generation_time": response.generation_time,
                    "type": "response"
                })
                
            except Exception as e:
                await websocket.send_json({
                    "error": str(e),
                    "type": "error"
                })
                
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )
