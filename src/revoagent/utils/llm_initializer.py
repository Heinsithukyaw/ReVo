"""
LLM Initializer for reVoAgent

Provides a simplified way to initialize the LLM system
with proper template-based fallbacks.
"""

import logging
import os
import yaml
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class LLMInitializer:
    """
    Simplified LLM initialization with template fallbacks.
    """
    
    @staticmethod
    async def initialize_llm_system():
        """Initialize the LLM system with proper error handling."""
        try:
            # First try to import the enhanced LLM manager
            try:
                from ..ai.llm_manager_enhanced import LLMManagerEnhanced
                llm_manager = LLMManagerEnhanced()
                success = await llm_manager.initialize()
                
                if success:
                    logger.info("Enhanced LLM Manager initialized successfully")
                    return llm_manager
                else:
                    logger.warning("Enhanced LLM Manager initialization failed, falling back")
            except ImportError as e:
                logger.warning(f"Enhanced LLM Manager not available: {e}")
                llm_manager = None
                
            # Fall back to the basic LLM manager
            try:
                from ..ai.llm_manager import LLMManager
                llm_manager = LLMManager()
                success = await llm_manager.initialize()
                
                if success:
                    logger.info("Basic LLM Manager initialized successfully")
                    return llm_manager
                else:
                    logger.warning("Basic LLM Manager initialization failed, falling back")
            except ImportError as e:
                logger.warning(f"Basic LLM Manager not available: {e}")
            
            # Fall back to template-based system
            try:
                from ..ai.cpu_optimized_deepseek import CPUOptimizedDeepSeek
                
                class TemplateLLMManager:
                    """Simple template-based LLM manager."""
                    
                    def __init__(self):
                        self.initialized = True
                        self.fallback_manager = None
                    
                    async def initialize(self):
                        return True
                    
                    async def generate_response(self, message, model=None, **kwargs):
                        return f"I'm a template-based AI assistant. You asked: {message}\n\nI'm currently running in template mode because the LLM system is not fully initialized."
                    
                    async def get_available_models(self):
                        return [
                            {
                                "id": "template-model",
                                "name": "Template Model",
                                "provider": "template",
                                "source": "template",
                                "status": "available",
                                "cost_per_token": 0.0,
                                "features": ["template_based"]
                            }
                        ]
                    
                    async def get_health(self):
                        return {
                            "status": "template_mode",
                            "models_available": 1,
                            "stats": {
                                "total_requests": 0,
                                "successful_requests": 0
                            }
                        }
                
                logger.info("Using template-based LLM manager")
                return TemplateLLMManager()
                
            except Exception as e:
                logger.error(f"Failed to initialize any LLM system: {e}")
                return None
                
        except Exception as e:
            logger.error(f"Error in LLM initialization: {e}")
            return None