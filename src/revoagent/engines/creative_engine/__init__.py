"""
🎨 Creative Engine - Innovation and Solution Generation

Revolutionary solution generation with multiple creativity techniques.
Target: 3-5 solution alternatives with 80%+ innovation score
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

from .solution_generator import (
    SolutionGenerator, Solution, SolutionCriteria, GenerationContext, SolutionType, CreativityTechnique
)

logger = logging.getLogger(__name__)

@dataclass
class CreativeEngineStatus:
    """Creative Engine status"""
    status: str
    solutions_generated: int
    avg_innovation_score: float
    avg_creativity_score: float
    total_requests: int
    avg_generation_time: float

class CreativeEngine:
    """
    🎨 Creative Engine - Revolutionary solution generation
    
    Capabilities:
    - Generate 3-5 alternative solutions per request
    - Multiple creativity techniques (brainstorming, lateral thinking, etc.)
    - Innovation scoring and feasibility assessment
    - Domain-specific solution patterns
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.solution_generator = SolutionGenerator()
        
        # Performance tracking
        self.total_requests = 0
        self.total_solutions_generated = 0
        self.total_generation_time = 0.0
        self.start_time = datetime.now()
        
        logger.info("🎨 Creative Engine initialized")
    
    async def generate_creative_solutions(self, problem_statement: str,
                                        domain: str = "general",
                                        constraints: List[str] = None,
                                        innovation_level: float = 0.7,
                                        solution_count: int = 5) -> List[Solution]:
        """Generate creative solutions for a problem"""
        start_time = time.time()
        
        try:
            # Create solution criteria
            criteria = SolutionCriteria(
                problem_domain=domain,
                constraints=constraints or [],
                performance_requirements={},
                innovation_level=innovation_level,
                target_count=solution_count
            )
            
            # Create generation context
            context = GenerationContext(
                problem_statement=problem_statement,
                existing_solutions=[],
                domain_knowledge={},
                user_preferences={},
                constraints=constraints or []
            )
            
            # Generate solutions
            solutions = await self.solution_generator.generate_solutions(criteria, context)
            
            # Update metrics
            generation_time = time.time() - start_time
            self.total_requests += 1
            self.total_solutions_generated += len(solutions)
            self.total_generation_time += generation_time
            
            logger.info(f"🎨 Generated {len(solutions)} creative solutions in {generation_time:.2f}s")
            return solutions
            
        except Exception as e:
            logger.error(f"🎨 Error generating creative solutions: {e}")
            raise
    
    async def get_engine_status(self) -> CreativeEngineStatus:
        """Get engine status"""
        avg_innovation = 0.8  # Default
        avg_creativity = 0.8  # Default
        avg_generation_time = (
            self.total_generation_time / self.total_requests 
            if self.total_requests > 0 else 0.0
        )
        
        return CreativeEngineStatus(
            status="active",
            solutions_generated=self.total_solutions_generated,
            avg_innovation_score=avg_innovation,
            avg_creativity_score=avg_creativity,
            total_requests=self.total_requests,
            avg_generation_time=avg_generation_time
        )

# Export main classes
__all__ = [
    'CreativeEngine',
    'CreativeEngineStatus',
    'Solution',
    'SolutionCriteria',
    'GenerationContext',
    'SolutionType',
    'CreativityTechnique'
]
