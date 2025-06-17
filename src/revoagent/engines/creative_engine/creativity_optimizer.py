"""
Creative Engine - Creativity Optimizer
Adaptive creativity and learning mechanisms
"""

import asyncio
import time
import uuid
import random
import math
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging

from .solution_generator import Solution, Problem, GenerationRequest
from .innovation_engine import InnovationMetrics, BreakthroughCandidate

logger = logging.getLogger(__name__)

class OptimizationStrategy(Enum):
    EXPLORATION = "exploration"
    EXPLOITATION = "exploitation"
    BALANCED = "balanced"
    ADAPTIVE = "adaptive"

class LearningMode(Enum):
    SUPERVISED = "supervised"
    REINFORCEMENT = "reinforcement"
    UNSUPERVISED = "unsupervised"
    HYBRID = "hybrid"

@dataclass
class CreativityFeedback:
    """Feedback for creativity optimization"""
    solution_id: str
    user_rating: float  # 0.0 to 1.0
    effectiveness_score: float
    innovation_rating: float
    feasibility_rating: float
    feedback_text: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class OptimizationMetrics:
    """Metrics for creativity optimization"""
    creativity_score: float
    innovation_rate: float
    success_rate: float
    diversity_index: float
    learning_velocity: float
    adaptation_efficiency: float
    exploration_ratio: float

@dataclass
class CreativityProfile:
    """Profile for creativity optimization"""
    profile_id: str
    domain: str
    preferred_strategies: List[str]
    creativity_level: float
    innovation_bias: float
    risk_tolerance: float
    learning_rate: float
    adaptation_history: List[Dict[str, Any]]

class CreativityOptimizer:
    """
    Adaptive creativity optimization with learning mechanisms
    Learns from solution effectiveness and adapts creative strategies
    """
    
    def __init__(self, learning_rate: float = 0.1, adaptation_threshold: float = 0.7):
        self.learning_rate = learning_rate
        self.adaptation_threshold = adaptation_threshold
        self.feedback_history: List[CreativityFeedback] = []
        self.creativity_profiles: Dict[str, CreativityProfile] = {}
        self.strategy_performance: Dict[str, float] = {}
        self.optimization_history: List[OptimizationMetrics] = []
        self.current_strategy = OptimizationStrategy.BALANCED
        self.learning_mode = LearningMode.HYBRID
        
        # Initialize strategy performance tracking
        self.strategy_performance = {
            'analogical_reasoning': 0.7,
            'constraint_relaxation': 0.6,
            'combination_synthesis': 0.65,
            'inversion_thinking': 0.8,
            'random_stimulation': 0.75,
            'pattern_breaking': 0.85,
            'biomimetic': 0.7,
            'lateral_thinking': 0.75
        }
        
        # Creativity parameters that can be optimized
        self.creativity_parameters = {
            'creativity_level': 0.8,
            'innovation_bias': 0.6,
            'solution_count': 5,
            'diversity_weight': 0.7,
            'risk_tolerance': 0.5,
            'exploration_rate': 0.3
        }
        
    async def initialize(self) -> bool:
        """Initialize creativity optimizer"""
        try:
            logger.info("🩷 Creative Engine: Creativity Optimizer initialized")
            return True
        except Exception as e:
            logger.error(f"🩷 Failed to initialize Creativity Optimizer: {e}")
            return False
    
    async def optimize_creativity_parameters(self, problem: Problem, 
                                           feedback_history: List[CreativityFeedback] = None) -> Dict[str, Any]:
        """
        Optimize creativity parameters based on problem characteristics and feedback
        """
        try:
            # Use provided feedback or internal history
            feedback_data = feedback_history or self.feedback_history
            
            # Get or create creativity profile for domain
            profile = await self._get_or_create_profile(problem.domain)
            
            # Analyze recent performance
            performance_metrics = await self._analyze_performance(feedback_data)
            
            # Adapt parameters based on performance
            optimized_params = await self._adapt_parameters(
                problem, profile, performance_metrics
            )
            
            # Update strategy selection
            optimal_strategy = await self._select_optimal_strategy(
                problem, performance_metrics
            )
            
            # Update profile with new parameters
            await self._update_profile(profile, optimized_params, performance_metrics)
            
            optimization_result = {
                'optimized_parameters': optimized_params,
                'optimal_strategy': optimal_strategy,
                'performance_metrics': performance_metrics,
                'profile_id': profile.profile_id,
                'adaptation_confidence': await self._calculate_adaptation_confidence(performance_metrics)
            }
            
            logger.info(f"🩷 Optimized creativity parameters for domain {problem.domain}")
            return optimization_result
            
        except Exception as e:
            logger.error(f"🩷 Error optimizing creativity parameters: {e}")
            return {'optimized_parameters': self.creativity_parameters.copy()}
    
    async def learn_from_feedback(self, feedback: CreativityFeedback) -> Dict[str, Any]:
        """
        Learn from solution feedback and adapt strategies
        """
        try:
            # Store feedback
            self.feedback_history.append(feedback)
            
            # Analyze feedback impact
            learning_insights = await self._analyze_feedback_impact(feedback)
            
            # Update strategy performance
            await self._update_strategy_performance(feedback, learning_insights)
            
            # Adapt creativity parameters
            parameter_adjustments = await self._adapt_from_feedback(feedback)
            
            # Update learning metrics
            learning_metrics = await self._calculate_learning_metrics()
            
            learning_result = {
                'feedback_processed': True,
                'learning_insights': learning_insights,
                'parameter_adjustments': parameter_adjustments,
                'learning_metrics': learning_metrics,
                'adaptation_triggered': learning_insights.get('adaptation_needed', False)
            }
            
            logger.debug(f"🩷 Learned from feedback for solution {feedback.solution_id}")
            return learning_result
            
        except Exception as e:
            logger.error(f"🩷 Error learning from feedback: {e}")
            return {'feedback_processed': False, 'error': str(e)}
    
    async def adapt_generation_strategy(self, problem: Problem, 
                                      recent_solutions: List[Solution]) -> Dict[str, Any]:
        """
        Adapt generation strategy based on recent solution performance
        """
        try:
            # Analyze recent solution quality
            solution_analysis = await self._analyze_solution_quality(recent_solutions)
            
            # Determine if adaptation is needed
            adaptation_needed = await self._should_adapt_strategy(solution_analysis)
            
            if adaptation_needed:
                # Select new strategy
                new_strategy = await self._select_adaptive_strategy(
                    problem, solution_analysis
                )
                
                # Calculate strategy parameters
                strategy_params = await self._calculate_strategy_parameters(
                    new_strategy, solution_analysis
                )
                
                # Update current strategy
                self.current_strategy = new_strategy
                
                adaptation_result = {
                    'adaptation_performed': True,
                    'new_strategy': new_strategy.value,
                    'strategy_parameters': strategy_params,
                    'adaptation_reason': solution_analysis.get('adaptation_reason'),
                    'expected_improvement': solution_analysis.get('expected_improvement', 0.1)
                }
            else:
                adaptation_result = {
                    'adaptation_performed': False,
                    'current_strategy': self.current_strategy.value,
                    'strategy_performance': solution_analysis.get('current_performance', 0.7)
                }
            
            logger.debug(f"🩷 Strategy adaptation: {adaptation_result['adaptation_performed']}")
            return adaptation_result
            
        except Exception as e:
            logger.error(f"🩷 Error adapting generation strategy: {e}")
            return {'adaptation_performed': False, 'error': str(e)}
    
    async def optimize_solution_diversity(self, solutions: List[Solution], 
                                        target_diversity: float = 0.8) -> List[Solution]:
        """
        Optimize solution diversity through intelligent selection and modification
        """
        try:
            if not solutions:
                return solutions
            
            # Calculate current diversity
            current_diversity = await self._calculate_solution_diversity(solutions)
            
            if current_diversity >= target_diversity:
                return solutions
            
            # Optimize diversity
            optimized_solutions = []
            remaining_solutions = solutions.copy()
            
            # Always include the best solution
            best_solution = max(solutions, key=lambda s: s.innovation_score)
            optimized_solutions.append(best_solution)
            remaining_solutions.remove(best_solution)
            
            # Select diverse solutions
            while len(optimized_solutions) < len(solutions) and remaining_solutions:
                # Find most diverse candidate
                best_candidate = None
                max_diversity_gain = -1
                
                for candidate in remaining_solutions:
                    diversity_gain = await self._calculate_diversity_gain(
                        candidate, optimized_solutions
                    )
                    
                    if diversity_gain > max_diversity_gain:
                        max_diversity_gain = diversity_gain
                        best_candidate = candidate
                
                if best_candidate:
                    optimized_solutions.append(best_candidate)
                    remaining_solutions.remove(best_candidate)
                else:
                    break
            
            # Verify diversity improvement
            final_diversity = await self._calculate_solution_diversity(optimized_solutions)
            
            logger.debug(f"🩷 Optimized diversity from {current_diversity:.3f} to {final_diversity:.3f}")
            return optimized_solutions
            
        except Exception as e:
            logger.error(f"🩷 Error optimizing solution diversity: {e}")
            return solutions
    
    async def get_optimization_metrics(self) -> OptimizationMetrics:
        """
        Get current optimization metrics
        """
        try:
            # Calculate metrics from recent history
            recent_feedback = self.feedback_history[-50:] if self.feedback_history else []
            
            # Creativity score (average from recent feedback)
            creativity_score = 0.8  # Default
            if recent_feedback:
                creativity_scores = [f.innovation_rating for f in recent_feedback]
                creativity_score = sum(creativity_scores) / len(creativity_scores)
            
            # Innovation rate (percentage of high-innovation solutions)
            innovation_rate = 0.6  # Default
            if recent_feedback:
                high_innovation = [f for f in recent_feedback if f.innovation_rating > 0.7]
                innovation_rate = len(high_innovation) / len(recent_feedback)
            
            # Success rate (percentage of well-rated solutions)
            success_rate = 0.7  # Default
            if recent_feedback:
                successful = [f for f in recent_feedback if f.user_rating > 0.6]
                success_rate = len(successful) / len(recent_feedback)
            
            # Diversity index (calculated from strategy performance variance)
            diversity_index = await self._calculate_diversity_index()
            
            # Learning velocity (rate of improvement)
            learning_velocity = await self._calculate_learning_velocity()
            
            # Adaptation efficiency (success rate of adaptations)
            adaptation_efficiency = await self._calculate_adaptation_efficiency()
            
            # Exploration ratio (balance between exploration and exploitation)
            exploration_ratio = self.creativity_parameters.get('exploration_rate', 0.3)
            
            metrics = OptimizationMetrics(
                creativity_score=creativity_score,
                innovation_rate=innovation_rate,
                success_rate=success_rate,
                diversity_index=diversity_index,
                learning_velocity=learning_velocity,
                adaptation_efficiency=adaptation_efficiency,
                exploration_ratio=exploration_ratio
            )
            
            # Store metrics history
            self.optimization_history.append(metrics)
            
            # Keep only recent history
            if len(self.optimization_history) > 100:
                self.optimization_history = self.optimization_history[-100:]
            
            return metrics
            
        except Exception as e:
            logger.error(f"🩷 Error getting optimization metrics: {e}")
            return OptimizationMetrics(
                creativity_score=0.5, innovation_rate=0.5, success_rate=0.5,
                diversity_index=0.5, learning_velocity=0.0, adaptation_efficiency=0.5,
                exploration_ratio=0.3
            )
    
    async def _get_or_create_profile(self, domain: str) -> CreativityProfile:
        """Get existing profile or create new one for domain"""
        try:
            if domain in self.creativity_profiles:
                return self.creativity_profiles[domain]
            
            # Create new profile
            profile = CreativityProfile(
                profile_id=f"profile_{uuid.uuid4().hex[:8]}",
                domain=domain,
                preferred_strategies=['analogical_reasoning', 'combination_synthesis'],
                creativity_level=0.8,
                innovation_bias=0.6,
                risk_tolerance=0.5,
                learning_rate=self.learning_rate,
                adaptation_history=[]
            )
            
            self.creativity_profiles[domain] = profile
            return profile
            
        except Exception as e:
            logger.error(f"🩷 Error getting/creating profile: {e}")
            return CreativityProfile(
                profile_id="default", domain=domain, preferred_strategies=[],
                creativity_level=0.8, innovation_bias=0.6, risk_tolerance=0.5,
                learning_rate=0.1, adaptation_history=[]
            )
    
    async def _analyze_performance(self, feedback_data: List[CreativityFeedback]) -> Dict[str, Any]:
        """Analyze performance from feedback data"""
        try:
            if not feedback_data:
                return {'performance_score': 0.7, 'trend': 'stable'}
            
            # Calculate performance metrics
            user_ratings = [f.user_rating for f in feedback_data]
            innovation_ratings = [f.innovation_rating for f in feedback_data]
            effectiveness_scores = [f.effectiveness_score for f in feedback_data]
            
            performance_metrics = {
                'avg_user_rating': sum(user_ratings) / len(user_ratings),
                'avg_innovation_rating': sum(innovation_ratings) / len(innovation_ratings),
                'avg_effectiveness': sum(effectiveness_scores) / len(effectiveness_scores),
                'feedback_count': len(feedback_data),
                'performance_score': (
                    sum(user_ratings) + sum(innovation_ratings) + sum(effectiveness_scores)
                ) / (3 * len(feedback_data))
            }
            
            # Calculate trend
            if len(feedback_data) >= 5:
                recent_performance = sum(user_ratings[-5:]) / 5
                older_performance = sum(user_ratings[:-5]) / max(1, len(user_ratings) - 5)
                
                if recent_performance > older_performance + 0.1:
                    performance_metrics['trend'] = 'improving'
                elif recent_performance < older_performance - 0.1:
                    performance_metrics['trend'] = 'declining'
                else:
                    performance_metrics['trend'] = 'stable'
            else:
                performance_metrics['trend'] = 'insufficient_data'
            
            return performance_metrics
            
        except Exception as e:
            logger.error(f"🩷 Error analyzing performance: {e}")
            return {'performance_score': 0.5, 'trend': 'unknown'}
    
    async def _adapt_parameters(self, problem: Problem, 
                              profile: CreativityProfile, 
                              performance_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt creativity parameters based on performance"""
        try:
            adapted_params = self.creativity_parameters.copy()
            
            # Adapt based on performance trend
            performance_score = performance_metrics.get('performance_score', 0.7)
            trend = performance_metrics.get('trend', 'stable')
            
            if trend == 'declining' or performance_score < 0.6:
                # Increase exploration and creativity
                adapted_params['creativity_level'] = min(1.0, adapted_params['creativity_level'] + 0.1)
                adapted_params['exploration_rate'] = min(1.0, adapted_params['exploration_rate'] + 0.1)
                adapted_params['innovation_bias'] = min(1.0, adapted_params['innovation_bias'] + 0.05)
            elif trend == 'improving' and performance_score > 0.8:
                # Fine-tune current approach
                adapted_params['creativity_level'] = max(0.3, adapted_params['creativity_level'] - 0.05)
                adapted_params['exploration_rate'] = max(0.1, adapted_params['exploration_rate'] - 0.05)
            
            # Adapt based on problem complexity
            if problem.complexity > 0.8:
                adapted_params['solution_count'] = min(7, adapted_params['solution_count'] + 1)
                adapted_params['diversity_weight'] = min(1.0, adapted_params['diversity_weight'] + 0.1)
            
            # Adapt based on profile preferences
            adapted_params['risk_tolerance'] = (
                adapted_params['risk_tolerance'] * 0.7 + profile.risk_tolerance * 0.3
            )
            
            return adapted_params
            
        except Exception as e:
            logger.error(f"🩷 Error adapting parameters: {e}")
            return self.creativity_parameters.copy()
    
    async def _select_optimal_strategy(self, problem: Problem, 
                                     performance_metrics: Dict[str, Any]) -> OptimizationStrategy:
        """Select optimal optimization strategy"""
        try:
            performance_score = performance_metrics.get('performance_score', 0.7)
            trend = performance_metrics.get('trend', 'stable')
            
            # Strategy selection logic
            if performance_score < 0.5 or trend == 'declining':
                return OptimizationStrategy.EXPLORATION
            elif performance_score > 0.8 and trend == 'improving':
                return OptimizationStrategy.EXPLOITATION
            elif problem.complexity > 0.7:
                return OptimizationStrategy.ADAPTIVE
            else:
                return OptimizationStrategy.BALANCED
                
        except Exception as e:
            logger.error(f"🩷 Error selecting optimal strategy: {e}")
            return OptimizationStrategy.BALANCED
    
    async def _update_profile(self, profile: CreativityProfile, 
                            optimized_params: Dict[str, Any], 
                            performance_metrics: Dict[str, Any]) -> None:
        """Update creativity profile with new data"""
        try:
            # Update profile parameters
            profile.creativity_level = optimized_params.get('creativity_level', profile.creativity_level)
            profile.innovation_bias = optimized_params.get('innovation_bias', profile.innovation_bias)
            profile.risk_tolerance = optimized_params.get('risk_tolerance', profile.risk_tolerance)
            
            # Add to adaptation history
            adaptation_record = {
                'timestamp': datetime.now().isoformat(),
                'parameters': optimized_params,
                'performance': performance_metrics,
                'adaptation_reason': performance_metrics.get('trend', 'optimization')
            }
            
            profile.adaptation_history.append(adaptation_record)
            
            # Keep only recent history
            if len(profile.adaptation_history) > 20:
                profile.adaptation_history = profile.adaptation_history[-20:]
                
        except Exception as e:
            logger.error(f"🩷 Error updating profile: {e}")
    
    async def _calculate_adaptation_confidence(self, performance_metrics: Dict[str, Any]) -> float:
        """Calculate confidence in adaptation decisions"""
        try:
            feedback_count = performance_metrics.get('feedback_count', 0)
            performance_score = performance_metrics.get('performance_score', 0.5)
            
            # Confidence based on data quantity and quality
            data_confidence = min(1.0, feedback_count / 10.0)  # Full confidence with 10+ feedback
            quality_confidence = performance_score
            
            # Combined confidence
            confidence = (data_confidence * 0.6 + quality_confidence * 0.4)
            
            return confidence
            
        except Exception as e:
            logger.error(f"🩷 Error calculating adaptation confidence: {e}")
            return 0.5
    
    async def _analyze_feedback_impact(self, feedback: CreativityFeedback) -> Dict[str, Any]:
        """Analyze the impact of feedback on learning"""
        try:
            insights = {
                'feedback_quality': (feedback.user_rating + feedback.innovation_rating + feedback.effectiveness_score) / 3,
                'innovation_strength': feedback.innovation_rating,
                'feasibility_strength': feedback.feasibility_rating,
                'overall_satisfaction': feedback.user_rating
            }
            
            # Determine if adaptation is needed
            if insights['feedback_quality'] < 0.5:
                insights['adaptation_needed'] = True
                insights['adaptation_type'] = 'major'
            elif insights['feedback_quality'] < 0.7:
                insights['adaptation_needed'] = True
                insights['adaptation_type'] = 'minor'
            else:
                insights['adaptation_needed'] = False
                insights['adaptation_type'] = 'none'
            
            return insights
            
        except Exception as e:
            logger.error(f"🩷 Error analyzing feedback impact: {e}")
            return {'feedback_quality': 0.5, 'adaptation_needed': False}
    
    async def _update_strategy_performance(self, feedback: CreativityFeedback, 
                                         insights: Dict[str, Any]) -> None:
        """Update strategy performance based on feedback"""
        try:
            # This would require tracking which strategy generated which solution
            # For now, update all strategies slightly based on overall feedback
            feedback_quality = insights.get('feedback_quality', 0.5)
            
            # Small adjustment to all strategies
            adjustment = (feedback_quality - 0.7) * self.learning_rate * 0.1
            
            for strategy in self.strategy_performance:
                self.strategy_performance[strategy] = max(0.1, min(1.0, 
                    self.strategy_performance[strategy] + adjustment
                ))
                
        except Exception as e:
            logger.error(f"🩷 Error updating strategy performance: {e}")
    
    async def _adapt_from_feedback(self, feedback: CreativityFeedback) -> Dict[str, float]:
        """Adapt creativity parameters from feedback"""
        try:
            adjustments = {}
            
            # Adjust creativity level based on innovation rating
            if feedback.innovation_rating < 0.5:
                adjustments['creativity_level'] = self.learning_rate * 0.1
            elif feedback.innovation_rating > 0.8:
                adjustments['creativity_level'] = -self.learning_rate * 0.05
            
            # Adjust innovation bias based on user rating
            if feedback.user_rating < 0.5 and feedback.innovation_rating > 0.7:
                adjustments['innovation_bias'] = -self.learning_rate * 0.1  # Too innovative, not practical
            elif feedback.user_rating > 0.8 and feedback.innovation_rating < 0.5:
                adjustments['innovation_bias'] = self.learning_rate * 0.1  # Need more innovation
            
            # Apply adjustments
            for param, adjustment in adjustments.items():
                if param in self.creativity_parameters:
                    self.creativity_parameters[param] = max(0.1, min(1.0,
                        self.creativity_parameters[param] + adjustment
                    ))
            
            return adjustments
            
        except Exception as e:
            logger.error(f"🩷 Error adapting from feedback: {e}")
            return {}
    
    async def _calculate_learning_metrics(self) -> Dict[str, float]:
        """Calculate learning progress metrics"""
        try:
            if len(self.feedback_history) < 2:
                return {'learning_rate': 0.0, 'improvement_rate': 0.0}
            
            # Calculate improvement over time
            recent_feedback = self.feedback_history[-10:]
            older_feedback = self.feedback_history[-20:-10] if len(self.feedback_history) >= 20 else []
            
            if older_feedback:
                recent_avg = sum(f.user_rating for f in recent_feedback) / len(recent_feedback)
                older_avg = sum(f.user_rating for f in older_feedback) / len(older_feedback)
                improvement_rate = (recent_avg - older_avg) / len(recent_feedback)
            else:
                improvement_rate = 0.0
            
            metrics = {
                'learning_rate': self.learning_rate,
                'improvement_rate': improvement_rate,
                'feedback_count': len(self.feedback_history),
                'adaptation_frequency': len([f for f in self.feedback_history[-10:] 
                                           if f.user_rating < 0.6]) / 10.0
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"🩷 Error calculating learning metrics: {e}")
            return {'learning_rate': 0.0, 'improvement_rate': 0.0}
    
    async def _analyze_solution_quality(self, solutions: List[Solution]) -> Dict[str, Any]:
        """Analyze quality of recent solutions"""
        try:
            if not solutions:
                return {'current_performance': 0.5, 'adaptation_reason': 'no_solutions'}
            
            # Calculate quality metrics
            innovation_scores = [s.innovation_score for s in solutions]
            creativity_scores = [s.creativity_score for s in solutions]
            feasibility_scores = [s.feasibility_score for s in solutions]
            
            analysis = {
                'avg_innovation': sum(innovation_scores) / len(innovation_scores),
                'avg_creativity': sum(creativity_scores) / len(creativity_scores),
                'avg_feasibility': sum(feasibility_scores) / len(feasibility_scores),
                'solution_count': len(solutions),
                'diversity': await self._calculate_solution_diversity(solutions)
            }
            
            # Calculate overall performance
            analysis['current_performance'] = (
                analysis['avg_innovation'] * 0.4 +
                analysis['avg_creativity'] * 0.3 +
                analysis['avg_feasibility'] * 0.3
            )
            
            # Determine adaptation reason
            if analysis['current_performance'] < 0.5:
                analysis['adaptation_reason'] = 'low_performance'
            elif analysis['diversity'] < 0.5:
                analysis['adaptation_reason'] = 'low_diversity'
            elif analysis['avg_innovation'] < 0.6:
                analysis['adaptation_reason'] = 'low_innovation'
            else:
                analysis['adaptation_reason'] = 'optimization'
            
            return analysis
            
        except Exception as e:
            logger.error(f"🩷 Error analyzing solution quality: {e}")
            return {'current_performance': 0.5, 'adaptation_reason': 'error'}
    
    async def _should_adapt_strategy(self, solution_analysis: Dict[str, Any]) -> bool:
        """Determine if strategy adaptation is needed"""
        try:
            current_performance = solution_analysis.get('current_performance', 0.7)
            diversity = solution_analysis.get('diversity', 0.7)
            
            # Adapt if performance or diversity is below threshold
            return (current_performance < self.adaptation_threshold or 
                   diversity < 0.5)
                   
        except Exception as e:
            logger.error(f"🩷 Error determining adaptation need: {e}")
            return False
    
    async def _select_adaptive_strategy(self, problem: Problem, 
                                      solution_analysis: Dict[str, Any]) -> OptimizationStrategy:
        """Select adaptive strategy based on analysis"""
        try:
            current_performance = solution_analysis.get('current_performance', 0.7)
            diversity = solution_analysis.get('diversity', 0.7)
            avg_innovation = solution_analysis.get('avg_innovation', 0.7)
            
            if current_performance < 0.4:
                return OptimizationStrategy.EXPLORATION
            elif diversity < 0.4:
                return OptimizationStrategy.EXPLORATION
            elif avg_innovation < 0.5:
                return OptimizationStrategy.EXPLORATION
            elif current_performance > 0.8:
                return OptimizationStrategy.EXPLOITATION
            else:
                return OptimizationStrategy.ADAPTIVE
                
        except Exception as e:
            logger.error(f"🩷 Error selecting adaptive strategy: {e}")
            return OptimizationStrategy.BALANCED
    
    async def _calculate_strategy_parameters(self, strategy: OptimizationStrategy, 
                                           analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate parameters for selected strategy"""
        try:
            if strategy == OptimizationStrategy.EXPLORATION:
                return {
                    'creativity_boost': 0.2,
                    'innovation_boost': 0.15,
                    'diversity_weight': 0.8,
                    'risk_tolerance': 0.7
                }
            elif strategy == OptimizationStrategy.EXPLOITATION:
                return {
                    'creativity_boost': -0.1,
                    'innovation_boost': -0.05,
                    'diversity_weight': 0.4,
                    'risk_tolerance': 0.3
                }
            elif strategy == OptimizationStrategy.ADAPTIVE:
                return {
                    'creativity_boost': 0.1,
                    'innovation_boost': 0.1,
                    'diversity_weight': 0.6,
                    'risk_tolerance': 0.5
                }
            else:  # BALANCED
                return {
                    'creativity_boost': 0.0,
                    'innovation_boost': 0.0,
                    'diversity_weight': 0.5,
                    'risk_tolerance': 0.5
                }
                
        except Exception as e:
            logger.error(f"🩷 Error calculating strategy parameters: {e}")
            return {}
    
    async def _calculate_solution_diversity(self, solutions: List[Solution]) -> float:
        """Calculate diversity index for solutions"""
        try:
            if len(solutions) < 2:
                return 1.0
            
            # Calculate diversity based on multiple factors
            diversity_factors = []
            
            # Approach diversity
            approaches = [s.approach for s in solutions]
            unique_approaches = len(set(approaches))
            approach_diversity = unique_approaches / len(approaches)
            diversity_factors.append(approach_diversity)
            
            # Solution type diversity
            types = [s.solution_type for s in solutions]
            unique_types = len(set(types))
            type_diversity = unique_types / len(types)
            diversity_factors.append(type_diversity)
            
            # Score diversity (variance in innovation scores)
            innovation_scores = [s.innovation_score for s in solutions]
            if len(innovation_scores) > 1:
                mean_score = sum(innovation_scores) / len(innovation_scores)
                variance = sum((score - mean_score) ** 2 for score in innovation_scores) / len(innovation_scores)
                score_diversity = min(1.0, variance * 4)  # Normalize variance
                diversity_factors.append(score_diversity)
            
            return sum(diversity_factors) / len(diversity_factors)
            
        except Exception as e:
            logger.error(f"🩷 Error calculating solution diversity: {e}")
            return 0.5
    
    async def _calculate_diversity_gain(self, candidate: Solution, 
                                      selected: List[Solution]) -> float:
        """Calculate diversity gain from adding candidate to selected solutions"""
        try:
            if not selected:
                return 1.0
            
            diversity_gains = []
            
            for existing in selected:
                # Approach diversity
                approach_gain = 0.5 if candidate.approach != existing.approach else 0.0
                
                # Type diversity
                type_gain = 0.3 if candidate.solution_type != existing.solution_type else 0.0
                
                # Score diversity
                score_diff = abs(candidate.innovation_score - existing.innovation_score)
                score_gain = min(0.2, score_diff)
                
                total_gain = approach_gain + type_gain + score_gain
                diversity_gains.append(total_gain)
            
            # Return minimum gain (most conservative)
            return min(diversity_gains) if diversity_gains else 1.0
            
        except Exception as e:
            logger.error(f"🩷 Error calculating diversity gain: {e}")
            return 0.5
    
    async def _calculate_diversity_index(self) -> float:
        """Calculate overall diversity index from strategy performance"""
        try:
            if not self.strategy_performance:
                return 0.5
            
            # Calculate variance in strategy performance
            performances = list(self.strategy_performance.values())
            mean_performance = sum(performances) / len(performances)
            variance = sum((p - mean_performance) ** 2 for p in performances) / len(performances)
            
            # Convert variance to diversity index (higher variance = higher diversity)
            diversity_index = min(1.0, variance * 10)  # Scale variance
            
            return diversity_index
            
        except Exception as e:
            logger.error(f"🩷 Error calculating diversity index: {e}")
            return 0.5
    
    async def _calculate_learning_velocity(self) -> float:
        """Calculate learning velocity from optimization history"""
        try:
            if len(self.optimization_history) < 2:
                return 0.0
            
            # Calculate improvement rate in recent metrics
            recent_metrics = self.optimization_history[-5:]
            
            if len(recent_metrics) < 2:
                return 0.0
            
            # Calculate trend in success rate
            success_rates = [m.success_rate for m in recent_metrics]
            velocity = (success_rates[-1] - success_rates[0]) / len(success_rates)
            
            return max(-1.0, min(1.0, velocity))
            
        except Exception as e:
            logger.error(f"🩷 Error calculating learning velocity: {e}")
            return 0.0
    
    async def _calculate_adaptation_efficiency(self) -> float:
        """Calculate efficiency of adaptations"""
        try:
            # Simple efficiency calculation based on recent performance
            if len(self.feedback_history) < 5:
                return 0.5
            
            recent_feedback = self.feedback_history[-10:]
            successful_adaptations = len([f for f in recent_feedback if f.user_rating > 0.7])
            
            efficiency = successful_adaptations / len(recent_feedback)
            return efficiency
            
        except Exception as e:
            logger.error(f"🩷 Error calculating adaptation efficiency: {e}")
            return 0.5
    
    async def cleanup(self) -> None:
        """Cleanup creativity optimizer"""
        try:
            self.feedback_history.clear()
            self.creativity_profiles.clear()
            self.optimization_history.clear()
            logger.info("🩷 Creative Engine: Creativity Optimizer cleaned up")
        except Exception as e:
            logger.error(f"🩷 Error during cleanup: {e}")