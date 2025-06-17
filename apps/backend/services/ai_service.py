#!/usr/bin/env python3
"""
Production-Ready AI Service for reVoAgent
Integrates Enhanced Local AI Model Manager with cost optimization
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import sys
from pathlib import Path

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.packages.ai.enhanced_model_manager import (
    EnhancedModelManager, 
    GenerationRequest, 
    GenerationResponse,
    ModelType
)

logger = logging.getLogger(__name__)

def create_local_ai_config() -> Dict[str, Any]:
    """Create optimized configuration for local AI models"""
    return {
        "deepseek_path": "/models/deepseek-r1",
        "llama_path": "/models/llama-3.1-70b",
        "openai_api_key": None,  # Will use environment variable
        "anthropic_api_key": None,  # Will use environment variable
        "cost_optimization": {
            "local_preference_ratio": 0.7,  # 70% local, 30% cloud
            "max_daily_cost": 100.0,  # $100 daily limit
            "emergency_fallback": True
        },
        "performance": {
            "max_concurrent_requests": 10,
            "timeout_seconds": 30,
            "retry_attempts": 3
        }
    }

class ProductionAIService:
    """
    Production-ready AI service with cost optimization and intelligent routing
    
    Features:
    - 70% local model usage (free)
    - 30% cloud API fallback
    - Cost tracking and optimization
    - Performance monitoring
    - Automatic failover
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the production AI service"""
        self.config = config or create_local_ai_config()
        self.local_manager = EnhancedModelManager(self.config)
        
        # Cost tracking
        self.cost_tracker = {
            "daily_cost": 0.0,
            "monthly_cost": 0.0,
            "local_requests": 0,
            "cloud_requests": 0,
            "cost_savings": 0.0,
            "last_reset": datetime.now()
        }
        
        # Performance metrics
        self.performance_metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
            "local_success_rate": 0.0,
            "cloud_success_rate": 0.0
        }
        
        # Request queue for load balancing
        self.request_queue = asyncio.Queue()
        self.processing_tasks = []
        
        logger.info("🚀 Production AI Service initialized")
        logger.info(f"💰 Cost optimization: {self.config['cost_optimization']['local_preference_ratio']*100}% local preference")
    
    async def initialize(self):
        """Initialize the AI service and start background tasks"""
        try:
            # Start health monitoring for the enhanced model manager
            self.local_manager.start_health_monitoring()
            
            # Start background processing tasks
            await self._start_background_tasks()
            
            logger.info("✅ Production AI Service fully initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize AI service: {e}")
            raise
    
    async def _start_background_tasks(self):
        """Start background processing tasks"""
        # Start request processor
        self.processing_tasks.append(
            asyncio.create_task(self._process_request_queue())
        )
        
        # Start cost monitoring
        self.processing_tasks.append(
            asyncio.create_task(self._monitor_costs())
        )
        
        # Start performance monitoring
        self.processing_tasks.append(
            asyncio.create_task(self._monitor_performance())
        )
    
    async def generate_with_cost_optimization(self, request: GenerationRequest) -> GenerationResponse:
        """
        Generate AI response with intelligent cost optimization
        
        Routing strategy:
        - Route 70% to local models (free)
        - Route 30% to cloud APIs (paid)
        - Always try local first for cost savings
        """
        start_time = datetime.now()
        
        try:
            # Update metrics
            self.performance_metrics["total_requests"] += 1
            
            # Determine routing strategy
            should_use_local = await self._should_use_local_model(request)
            
            if should_use_local:
                # Try local models first
                try:
                    response = await self._generate_local(request)
                    if response.success:
                        self.cost_tracker["local_requests"] += 1
                        self.performance_metrics["successful_requests"] += 1
                        return response
                except Exception as e:
                    logger.warning(f"Local generation failed: {e}")
            
            # Fallback to cloud if local failed or not preferred
            if request.fallback_allowed:
                response = await self._cloud_fallback(request)
                self.cost_tracker["cloud_requests"] += 1
                
                if response.success:
                    self.performance_metrics["successful_requests"] += 1
                else:
                    self.performance_metrics["failed_requests"] += 1
                
                return response
            else:
                # No fallback allowed, return error
                self.performance_metrics["failed_requests"] += 1
                return GenerationResponse(
                    content="",
                    model_used="none",
                    model_type=ModelType.LOCAL_OPENSOURCE,
                    tokens_used=0,
                    cost=0.0,
                    response_time=(datetime.now() - start_time).total_seconds(),
                    success=False,
                    error_message="Local generation failed and fallback not allowed"
                )
                
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            self.performance_metrics["failed_requests"] += 1
            
            return GenerationResponse(
                content="",
                model_used="error",
                model_type=ModelType.LOCAL_OPENSOURCE,
                tokens_used=0,
                cost=0.0,
                response_time=(datetime.now() - start_time).total_seconds(),
                success=False,
                error_message=str(e)
            )
    
    async def _should_use_local_model(self, request: GenerationRequest) -> bool:
        """Determine if we should use local model based on optimization strategy"""
        
        # Force local if requested
        if request.force_local:
            return True
        
        # Check cost limits
        if request.cost_limit and request.cost_limit <= 0.001:  # Very low cost limit
            return True
        
        # Check daily cost limits
        if self.cost_tracker["daily_cost"] >= self.config["cost_optimization"]["max_daily_cost"]:
            return True
        
        # Apply 70/30 ratio strategy
        local_ratio = self.config["cost_optimization"]["local_preference_ratio"]
        total_requests = self.cost_tracker["local_requests"] + self.cost_tracker["cloud_requests"]
        
        if total_requests == 0:
            return True  # Start with local
        
        current_local_ratio = self.cost_tracker["local_requests"] / total_requests
        
        # If we're below target local ratio, prefer local
        return current_local_ratio < local_ratio
    
    async def _generate_local(self, request: GenerationRequest) -> GenerationResponse:
        """Generate response using local models"""
        return await self.local_manager.generate_response(request)
    
    async def _cloud_fallback(self, request: GenerationRequest) -> GenerationResponse:
        """Fallback to cloud models with cost tracking"""
        start_time = datetime.now()
        
        try:
            # Create a cloud-forced request
            cloud_request = GenerationRequest(
                prompt=request.prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                force_cloud=True,
                model_preference="gpt-4"  # Prefer cloud model
            )
            
            # Use the enhanced model manager's cloud fallback
            response = await self.local_manager.generate_response(cloud_request)
            
            # Track costs
            self.cost_tracker["daily_cost"] += response.cost
            self.cost_tracker["monthly_cost"] += response.cost
            
            # Calculate savings (what we would have paid for cloud-only)
            estimated_cloud_cost = len(request.prompt.split()) * 0.03 / 1000  # Rough estimate
            if response.cost < estimated_cloud_cost:
                self.cost_tracker["cost_savings"] += (estimated_cloud_cost - response.cost)
            
            return response
            
        except Exception as e:
            logger.error(f"Cloud fallback failed: {e}")
            
            return GenerationResponse(
                content="",
                model_used="cloud-error",
                model_type=ModelType.CLOUD_OPENAI,
                tokens_used=0,
                cost=0.0,
                response_time=(datetime.now() - start_time).total_seconds(),
                success=False,
                error_message=f"Cloud fallback failed: {e}"
            )
    
    async def _cloud_generation(self, request: GenerationRequest) -> GenerationResponse:
        """Direct cloud generation for complex requests"""
        return await self._cloud_fallback(request)
    
    async def _process_request_queue(self):
        """Background task to process queued requests"""
        while True:
            try:
                # Process requests from queue
                await asyncio.sleep(0.1)  # Small delay to prevent busy waiting
                
                # Add queue processing logic here if needed
                
            except Exception as e:
                logger.error(f"Request queue processing error: {e}")
                await asyncio.sleep(1)
    
    async def _monitor_costs(self):
        """Background task to monitor and optimize costs"""
        while True:
            try:
                await asyncio.sleep(3600)  # Check every hour
                
                # Reset daily costs at midnight
                now = datetime.now()
                if now.date() > self.cost_tracker["last_reset"].date():
                    self.cost_tracker["daily_cost"] = 0.0
                    self.cost_tracker["last_reset"] = now
                    logger.info("🔄 Daily cost tracking reset")
                
                # Log cost summary
                logger.info(f"💰 Cost Summary - Daily: ${self.cost_tracker['daily_cost']:.2f}, "
                          f"Savings: ${self.cost_tracker['cost_savings']:.2f}")
                
            except Exception as e:
                logger.error(f"Cost monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _monitor_performance(self):
        """Background task to monitor performance metrics"""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                # Calculate success rates
                total = self.performance_metrics["total_requests"]
                if total > 0:
                    success_rate = self.performance_metrics["successful_requests"] / total
                    logger.info(f"📊 Performance - Success Rate: {success_rate:.2%}, "
                              f"Total Requests: {total}")
                
            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")
                await asyncio.sleep(60)
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """Get current cost summary"""
        total_requests = self.cost_tracker["local_requests"] + self.cost_tracker["cloud_requests"]
        local_percentage = 0.0
        
        if total_requests > 0:
            local_percentage = self.cost_tracker["local_requests"] / total_requests
        
        return {
            "daily_cost": self.cost_tracker["daily_cost"],
            "monthly_cost": self.cost_tracker["monthly_cost"],
            "cost_savings": self.cost_tracker["cost_savings"],
            "local_requests": self.cost_tracker["local_requests"],
            "cloud_requests": self.cost_tracker["cloud_requests"],
            "local_usage_percentage": local_percentage,
            "total_requests": total_requests
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get current performance summary"""
        return {
            **self.performance_metrics,
            "cost_summary": self.get_cost_summary(),
            "model_health": self.local_manager.get_health_status()
        }
    
    async def shutdown(self):
        """Gracefully shutdown the AI service"""
        logger.info("🛑 Shutting down Production AI Service...")
        
        # Cancel background tasks
        for task in self.processing_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.processing_tasks, return_exceptions=True)
        
        logger.info("✅ Production AI Service shutdown complete")

# Factory function for easy integration
async def create_production_ai_service(config: Optional[Dict[str, Any]] = None) -> ProductionAIService:
    """Create and initialize a production AI service"""
    service = ProductionAIService(config)
    await service.initialize()
    return service

# Compatibility alias
LocalModelManager = EnhancedModelManager