#!/usr/bin/env python3
"""
Cost Optimization Router for reVoAgent
Implements intelligent routing to achieve 95% cost savings vs full cloud deployment
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
import json
from pathlib import Path
import sys

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from .ai_service import GenerationRequest, GenerationResponse, ModelType

logger = logging.getLogger(__name__)

class CostTier(Enum):
    """Cost tiers for different model types"""
    FREE = "free"              # Local models
    CHEAP = "cheap"            # Budget cloud models
    MODERATE = "moderate"      # Standard cloud models  
    EXPENSIVE = "expensive"    # Premium cloud models

@dataclass
class ModelCostProfile:
    """Cost profile for AI models"""
    model_id: str
    cost_tier: CostTier
    cost_per_1k_tokens: float
    performance_score: float  # 0-1 scale
    reliability_score: float  # 0-1 scale
    speed_score: float       # 0-1 scale
    max_context_length: int
    specialties: List[str] = None

class CostOptimizedRouter:
    """
    Cost optimization routing system
    
    Achieves 95% cost savings through intelligent model selection:
    - 70% local models (free)
    - 20% budget cloud models 
    - 10% premium cloud models (only for complex tasks)
    """
    
    def __init__(self):
        """Initialize the cost optimizer"""
        
        # Model cost profiles
        self.local_models = {
            "deepseek_r1": ModelCostProfile(
                model_id="deepseek_r1",
                cost_tier=CostTier.FREE,
                cost_per_1k_tokens=0.0,
                performance_score=0.85,
                reliability_score=0.90,
                speed_score=0.80,
                max_context_length=32768,
                specialties=["code_generation", "analysis", "reasoning"]
            ),
            "llama_local": ModelCostProfile(
                model_id="llama_local", 
                cost_tier=CostTier.FREE,
                cost_per_1k_tokens=0.0,
                performance_score=0.80,
                reliability_score=0.85,
                speed_score=0.75,
                max_context_length=8192,
                specialties=["general_purpose", "conversation", "summarization"]
            )
        }
        
        self.cloud_models = {
            "gemini-pro": ModelCostProfile(
                model_id="gemini-pro",
                cost_tier=CostTier.CHEAP,
                cost_per_1k_tokens=0.0005,
                performance_score=0.88,
                reliability_score=0.95,
                speed_score=0.90,
                max_context_length=32768,
                specialties=["analysis", "reasoning", "multimodal"]
            ),
            "claude-3-haiku": ModelCostProfile(
                model_id="claude-3-haiku",
                cost_tier=CostTier.CHEAP,
                cost_per_1k_tokens=0.00025,
                performance_score=0.82,
                reliability_score=0.93,
                speed_score=0.95,
                max_context_length=200000,
                specialties=["fast_responses", "simple_tasks"]
            ),
            "claude-3-sonnet": ModelCostProfile(
                model_id="claude-3-sonnet",
                cost_tier=CostTier.MODERATE,
                cost_per_1k_tokens=0.003,
                performance_score=0.92,
                reliability_score=0.96,
                speed_score=0.85,
                max_context_length=200000,
                specialties=["complex_reasoning", "code_review", "analysis"]
            ),
            "gpt-4": ModelCostProfile(
                model_id="gpt-4",
                cost_tier=CostTier.EXPENSIVE,
                cost_per_1k_tokens=0.03,
                performance_score=0.95,
                reliability_score=0.97,
                speed_score=0.70,
                max_context_length=8192,
                specialties=["complex_tasks", "creative_writing", "advanced_reasoning"]
            ),
            "gpt-4-turbo": ModelCostProfile(
                model_id="gpt-4-turbo",
                cost_tier=CostTier.EXPENSIVE,
                cost_per_1k_tokens=0.01,
                performance_score=0.94,
                reliability_score=0.96,
                speed_score=0.85,
                max_context_length=128000,
                specialties=["large_context", "complex_analysis", "code_generation"]
            )
        }
        
        # Cost tracking
        self.cost_metrics = {
            "daily_budget": 100.0,  # $100 daily budget
            "monthly_budget": 2000.0,  # $2000 monthly budget
            "current_daily_cost": 0.0,
            "current_monthly_cost": 0.0,
            "cost_savings_target": 0.95,  # 95% savings target
            "actual_savings": 0.0,
            "baseline_cost": 0.0,  # What it would cost with premium models only
            "routing_stats": {
                "local_requests": 0,
                "cheap_cloud_requests": 0,
                "moderate_cloud_requests": 0,
                "expensive_cloud_requests": 0
            }
        }
        
        # Routing thresholds
        self.routing_config = {
            "local_preference_ratio": 0.70,  # 70% local
            "cheap_cloud_ratio": 0.20,       # 20% cheap cloud
            "moderate_cloud_ratio": 0.08,    # 8% moderate cloud
            "expensive_cloud_ratio": 0.02,   # 2% expensive cloud
            "complexity_threshold_moderate": 7,  # Complexity 7+ can use moderate
            "complexity_threshold_expensive": 9, # Complexity 9+ can use expensive
            "emergency_fallback": True
        }
        
        logger.info("💰 Cost Optimization Router initialized")
        logger.info(f"🎯 Target: {self.cost_metrics['cost_savings_target']*100}% cost savings")
    
    async def route_request(self, request: GenerationRequest) -> Tuple[str, ModelCostProfile]:
        """
        Route request to optimal model based on cost optimization strategy
        
        Returns: (model_id, cost_profile)
        """
        
        # Analyze request complexity and requirements
        complexity = await self._analyze_request_complexity(request)
        estimated_tokens = await self._estimate_token_usage(request)
        
        # Check budget constraints
        if await self._is_over_budget():
            logger.warning("💸 Over budget - forcing local models only")
            return await self._route_to_local_model(request, complexity)
        
        # Apply routing strategy based on complexity and current ratios
        current_ratios = self._calculate_current_ratios()
        
        # Route based on complexity and current usage ratios
        if complexity <= 5 or current_ratios["local"] < self.routing_config["local_preference_ratio"]:
            # Route to local models
            return await self._route_to_local_model(request, complexity)
        
        elif complexity <= 7 and current_ratios["cheap_cloud"] < self.routing_config["cheap_cloud_ratio"]:
            # Route to cheap cloud models
            return await self._route_to_cheap_cloud(request, complexity)
        
        elif complexity <= 9 and current_ratios["moderate_cloud"] < self.routing_config["moderate_cloud_ratio"]:
            # Route to moderate cloud models
            return await self._route_to_moderate_cloud(request, complexity)
        
        elif complexity > 9 and current_ratios["expensive_cloud"] < self.routing_config["expensive_cloud_ratio"]:
            # Route to expensive cloud models (only for very complex tasks)
            return await self._route_to_expensive_cloud(request, complexity)
        
        else:
            # Default to local models to maintain cost savings
            return await self._route_to_local_model(request, complexity)
    
    async def _analyze_request_complexity(self, request: GenerationRequest) -> int:
        """Analyze request complexity on a 1-10 scale"""
        
        prompt = request.prompt.lower()
        complexity = 1
        
        # Base complexity factors
        if len(request.prompt) > 1000:
            complexity += 1
        if len(request.prompt) > 2000:
            complexity += 1
        
        # Content complexity indicators
        complexity_indicators = {
            "complex": 2, "advanced": 2, "sophisticated": 2,
            "analyze": 1, "optimize": 1, "refactor": 2,
            "architecture": 2, "design pattern": 2,
            "algorithm": 2, "data structure": 1,
            "machine learning": 3, "ai": 1,
            "security": 2, "performance": 1,
            "database": 1, "sql": 1,
            "test": 1, "debug": 1,
            "deploy": 1, "devops": 1,
            "review": 1, "documentation": 1
        }
        
        for indicator, weight in complexity_indicators.items():
            if indicator in prompt:
                complexity += weight
        
        # Max tokens requirement
        if request.max_tokens > 2000:
            complexity += 1
        if request.max_tokens > 4000:
            complexity += 1
        
        # Temperature (creativity requirement)
        if request.temperature > 0.8:
            complexity += 1
        
        return min(complexity, 10)  # Cap at 10
    
    async def _estimate_token_usage(self, request: GenerationRequest) -> int:
        """Estimate token usage for cost calculation"""
        
        # Rough estimation: 1 token ≈ 0.75 words
        input_tokens = len(request.prompt.split()) * 1.33
        output_tokens = request.max_tokens
        
        return int(input_tokens + output_tokens)
    
    async def _is_over_budget(self) -> bool:
        """Check if we're over budget"""
        return (
            self.cost_metrics["current_daily_cost"] >= self.cost_metrics["daily_budget"] * 0.9 or
            self.cost_metrics["current_monthly_cost"] >= self.cost_metrics["monthly_budget"] * 0.9
        )
    
    def _calculate_current_ratios(self) -> Dict[str, float]:
        """Calculate current usage ratios"""
        stats = self.cost_metrics["routing_stats"]
        total = sum(stats.values())
        
        if total == 0:
            return {"local": 0.0, "cheap_cloud": 0.0, "moderate_cloud": 0.0, "expensive_cloud": 0.0}
        
        return {
            "local": stats["local_requests"] / total,
            "cheap_cloud": stats["cheap_cloud_requests"] / total,
            "moderate_cloud": stats["moderate_cloud_requests"] / total,
            "expensive_cloud": stats["expensive_cloud_requests"] / total
        }
    
    async def _route_to_local_model(self, request: GenerationRequest, complexity: int) -> Tuple[str, ModelCostProfile]:
        """Route to best available local model"""
        
        # Choose best local model based on complexity and specialties
        if complexity >= 6 and "deepseek_r1" in self.local_models:
            model_id = "deepseek_r1"
        else:
            model_id = "llama_local"
        
        # Update routing stats
        self.cost_metrics["routing_stats"]["local_requests"] += 1
        
        return model_id, self.local_models[model_id]
    
    async def _route_to_cheap_cloud(self, request: GenerationRequest, complexity: int) -> Tuple[str, ModelCostProfile]:
        """Route to cheap cloud models"""
        
        # Choose between cheap cloud options
        if complexity >= 6:
            model_id = "gemini-pro"
        else:
            model_id = "claude-3-haiku"
        
        # Update routing stats
        self.cost_metrics["routing_stats"]["cheap_cloud_requests"] += 1
        
        return model_id, self.cloud_models[model_id]
    
    async def _route_to_moderate_cloud(self, request: GenerationRequest, complexity: int) -> Tuple[str, ModelCostProfile]:
        """Route to moderate cost cloud models"""
        
        model_id = "claude-3-sonnet"  # Best moderate option
        
        # Update routing stats
        self.cost_metrics["routing_stats"]["moderate_cloud_requests"] += 1
        
        return model_id, self.cloud_models[model_id]
    
    async def _route_to_expensive_cloud(self, request: GenerationRequest, complexity: int) -> Tuple[str, ModelCostProfile]:
        """Route to expensive cloud models (only for very complex tasks)"""
        
        # Choose based on context requirements
        if len(request.prompt) > 10000:
            model_id = "gpt-4-turbo"  # Large context
        else:
            model_id = "gpt-4"  # Standard premium
        
        # Update routing stats
        self.cost_metrics["routing_stats"]["expensive_cloud_requests"] += 1
        
        return model_id, self.cloud_models[model_id]
    
    async def calculate_cost_savings(self, actual_cost: float, tokens_used: int) -> float:
        """Calculate cost savings vs baseline (premium models only)"""
        
        # Calculate what it would have cost with GPT-4
        baseline_cost = tokens_used * self.cloud_models["gpt-4"].cost_per_1k_tokens / 1000
        
        # Update baseline tracking
        self.cost_metrics["baseline_cost"] += baseline_cost
        
        # Calculate savings
        savings = baseline_cost - actual_cost
        self.cost_metrics["actual_savings"] = (
            self.cost_metrics["baseline_cost"] - 
            (self.cost_metrics["current_daily_cost"] + self.cost_metrics["current_monthly_cost"])
        ) / self.cost_metrics["baseline_cost"] if self.cost_metrics["baseline_cost"] > 0 else 0
        
        return savings
    
    async def update_cost_tracking(self, cost: float, model_used: str):
        """Update cost tracking metrics"""
        
        self.cost_metrics["current_daily_cost"] += cost
        self.cost_metrics["current_monthly_cost"] += cost
        
        # Log if approaching budget limits
        daily_usage = self.cost_metrics["current_daily_cost"] / self.cost_metrics["daily_budget"]
        if daily_usage > 0.8:
            logger.warning(f"💸 Daily budget at {daily_usage:.1%} - consider more local routing")
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """Get comprehensive cost summary"""
        
        ratios = self._calculate_current_ratios()
        total_requests = sum(self.cost_metrics["routing_stats"].values())
        
        return {
            "cost_metrics": self.cost_metrics,
            "routing_ratios": ratios,
            "total_requests": total_requests,
            "savings_vs_target": {
                "target_savings": self.cost_metrics["cost_savings_target"],
                "actual_savings": self.cost_metrics["actual_savings"],
                "on_track": self.cost_metrics["actual_savings"] >= self.cost_metrics["cost_savings_target"] * 0.9
            },
            "budget_status": {
                "daily_usage": self.cost_metrics["current_daily_cost"] / self.cost_metrics["daily_budget"],
                "monthly_usage": self.cost_metrics["current_monthly_cost"] / self.cost_metrics["monthly_budget"],
                "daily_remaining": self.cost_metrics["daily_budget"] - self.cost_metrics["current_daily_cost"],
                "monthly_remaining": self.cost_metrics["monthly_budget"] - self.cost_metrics["current_monthly_cost"]
            },
            "model_distribution": {
                "local_models": f"{ratios['local']:.1%}",
                "cheap_cloud": f"{ratios['cheap_cloud']:.1%}",
                "moderate_cloud": f"{ratios['moderate_cloud']:.1%}",
                "expensive_cloud": f"{ratios['expensive_cloud']:.1%}"
            }
        }
    
    async def reset_daily_costs(self):
        """Reset daily cost tracking (call at midnight)"""
        self.cost_metrics["current_daily_cost"] = 0.0
        logger.info("🔄 Daily cost tracking reset")
    
    async def reset_monthly_costs(self):
        """Reset monthly cost tracking (call at month start)"""
        self.cost_metrics["current_monthly_cost"] = 0.0
        self.cost_metrics["routing_stats"] = {
            "local_requests": 0,
            "cheap_cloud_requests": 0,
            "moderate_cloud_requests": 0,
            "expensive_cloud_requests": 0
        }
        logger.info("🔄 Monthly cost tracking reset")

# Expected savings calculation
def calculate_expected_savings() -> Dict[str, Any]:
    """Calculate expected cost savings vs full cloud deployment"""
    
    # Baseline: 100% GPT-4 usage
    baseline_cost_per_1k_tokens = 0.03
    
    # Our optimized mix
    optimized_mix = {
        "local_models": {"ratio": 0.70, "cost_per_1k": 0.0},
        "cheap_cloud": {"ratio": 0.20, "cost_per_1k": 0.0005},
        "moderate_cloud": {"ratio": 0.08, "cost_per_1k": 0.003},
        "expensive_cloud": {"ratio": 0.02, "cost_per_1k": 0.03}
    }
    
    # Calculate weighted average cost
    optimized_cost = sum(
        mix["ratio"] * mix["cost_per_1k"] 
        for mix in optimized_mix.values()
    )
    
    # Calculate savings
    savings_percentage = (baseline_cost_per_1k_tokens - optimized_cost) / baseline_cost_per_1k_tokens
    
    # Monthly projections (assuming 1M tokens/month)
    monthly_tokens = 1_000_000
    baseline_monthly_cost = monthly_tokens * baseline_cost_per_1k_tokens / 1000
    optimized_monthly_cost = monthly_tokens * optimized_cost / 1000
    monthly_savings = baseline_monthly_cost - optimized_monthly_cost
    
    return {
        "savings_percentage": savings_percentage,
        "baseline_cost_per_1k_tokens": baseline_cost_per_1k_tokens,
        "optimized_cost_per_1k_tokens": optimized_cost,
        "monthly_projections": {
            "baseline_cost": baseline_monthly_cost,
            "optimized_cost": optimized_monthly_cost,
            "monthly_savings": monthly_savings,
            "annual_savings": monthly_savings * 12
        },
        "model_distribution": optimized_mix
    }

# Log expected savings on import
expected = calculate_expected_savings()
logger.info(f"💰 Expected cost savings: {expected['savings_percentage']:.1%}")
logger.info(f"💵 Projected annual savings: ${expected['monthly_projections']['annual_savings']:,.2f}")