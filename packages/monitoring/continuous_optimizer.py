"""
Continuous Optimizer for Phase 4 Comprehensive Monitoring

Provides automated performance monitoring, optimization recommendations,
and continuous improvement capabilities.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json
import aiofiles
from pathlib import Path
from enum import Enum
import statistics
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class OptimizationType(Enum):
    """Types of optimizations"""
    PERFORMANCE = "performance"
    MEMORY = "memory"
    CPU = "cpu"
    NETWORK = "network"
    DATABASE = "database"
    CACHE = "cache"
    CONFIGURATION = "configuration"

class OptimizationPriority(Enum):
    """Optimization priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class OptimizationStatus(Enum):
    """Optimization implementation status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class OptimizationRecommendation:
    """Optimization recommendation"""
    id: str
    title: str
    description: str
    optimization_type: OptimizationType
    priority: OptimizationPriority
    estimated_impact: str
    implementation_effort: str
    prerequisites: List[str]
    steps: List[str]
    metrics_to_monitor: List[str]
    expected_improvement: Dict[str, float]
    timestamp: datetime
    status: OptimizationStatus = OptimizationStatus.PENDING
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['optimization_type'] = self.optimization_type.value
        data['priority'] = self.priority.value
        data['status'] = self.status.value
        data['timestamp'] = self.timestamp.isoformat()
        return data

@dataclass
class PerformanceTrend:
    """Performance trend analysis"""
    metric_name: str
    time_period_hours: int
    trend_direction: str  # "improving", "degrading", "stable"
    change_percentage: float
    current_value: float
    baseline_value: float
    confidence_score: float
    data_points: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)

@dataclass
class OptimizationResult:
    """Result of an optimization implementation"""
    recommendation_id: str
    implementation_date: datetime
    before_metrics: Dict[str, float]
    after_metrics: Dict[str, float]
    improvement_achieved: Dict[str, float]
    success: bool
    notes: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['implementation_date'] = self.implementation_date.isoformat()
        return data

class ContinuousOptimizer:
    """
    Continuous optimization system that monitors performance,
    identifies optimization opportunities, and tracks improvements
    """
    
    def __init__(self,
                 storage_path: str = "monitoring/optimization",
                 analysis_interval: float = 300.0,  # 5 minutes
                 trend_analysis_hours: int = 24):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.analysis_interval = analysis_interval
        self.trend_analysis_hours = trend_analysis_hours
        
        # Optimization state
        self.recommendations: Dict[str, OptimizationRecommendation] = {}
        self.performance_trends: Dict[str, PerformanceTrend] = {}
        self.optimization_results: List[OptimizationResult] = []
        
        # Metrics collection
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.metric_providers: List[Callable] = []
        
        # Analysis state
        self.is_running = False
        self.last_analysis = datetime.now()
        
        # Optimization rules
        self.optimization_rules = self._create_optimization_rules()
        
        logger.info("ContinuousOptimizer initialized")
    
    def _create_optimization_rules(self) -> List[Dict[str, Any]]:
        """Create optimization rules for automatic recommendation generation"""
        return [
            {
                "name": "high_cpu_optimization",
                "condition": lambda metrics: metrics.get('cpu_percent', 0) > 80,
                "recommendation": {
                    "title": "High CPU Usage Optimization",
                    "description": "CPU usage is consistently high, consider optimization strategies",
                    "optimization_type": OptimizationType.CPU,
                    "priority": OptimizationPriority.HIGH,
                    "estimated_impact": "20-40% CPU reduction",
                    "implementation_effort": "Medium",
                    "prerequisites": ["Performance profiling", "Code analysis"],
                    "steps": [
                        "Profile CPU-intensive functions",
                        "Optimize algorithms and data structures",
                        "Implement caching where appropriate",
                        "Consider async processing for I/O operations"
                    ],
                    "metrics_to_monitor": ["cpu_percent", "response_time_ms"],
                    "expected_improvement": {"cpu_percent": -25.0, "response_time_ms": -15.0}
                }
            },
            {
                "name": "high_memory_optimization",
                "condition": lambda metrics: metrics.get('memory_percent', 0) > 85,
                "recommendation": {
                    "title": "Memory Usage Optimization",
                    "description": "Memory usage is high, implement memory optimization strategies",
                    "optimization_type": OptimizationType.MEMORY,
                    "priority": OptimizationPriority.HIGH,
                    "estimated_impact": "15-30% memory reduction",
                    "implementation_effort": "Medium",
                    "prerequisites": ["Memory profiling", "Leak detection"],
                    "steps": [
                        "Identify memory leaks and fix them",
                        "Optimize data structures and object lifecycle",
                        "Implement object pooling where appropriate",
                        "Tune garbage collection settings"
                    ],
                    "metrics_to_monitor": ["memory_percent", "memory_used_gb"],
                    "expected_improvement": {"memory_percent": -20.0}
                }
            },
            {
                "name": "slow_response_optimization",
                "condition": lambda metrics: metrics.get('avg_response_time_ms', 0) > 2000,
                "recommendation": {
                    "title": "API Response Time Optimization",
                    "description": "API response times are slow, implement performance optimizations",
                    "optimization_type": OptimizationType.PERFORMANCE,
                    "priority": OptimizationPriority.HIGH,
                    "estimated_impact": "30-50% response time improvement",
                    "implementation_effort": "High",
                    "prerequisites": ["Request tracing", "Database analysis"],
                    "steps": [
                        "Optimize database queries and add indexes",
                        "Implement response caching",
                        "Optimize serialization/deserialization",
                        "Consider CDN for static content",
                        "Implement connection pooling"
                    ],
                    "metrics_to_monitor": ["avg_response_time_ms", "p95_response_time_ms"],
                    "expected_improvement": {"avg_response_time_ms": -40.0, "p95_response_time_ms": -35.0}
                }
            },
            {
                "name": "high_error_rate_optimization",
                "condition": lambda metrics: metrics.get('error_rate', 0) > 0.05,
                "recommendation": {
                    "title": "Error Rate Reduction",
                    "description": "Error rate is high, implement reliability improvements",
                    "optimization_type": OptimizationType.PERFORMANCE,
                    "priority": OptimizationPriority.CRITICAL,
                    "estimated_impact": "50-80% error reduction",
                    "implementation_effort": "High",
                    "prerequisites": ["Error analysis", "Log investigation"],
                    "steps": [
                        "Analyze error patterns and root causes",
                        "Implement better error handling and retries",
                        "Add input validation and sanitization",
                        "Improve external service integration resilience",
                        "Add circuit breakers and fallbacks"
                    ],
                    "metrics_to_monitor": ["error_rate", "successful_requests"],
                    "expected_improvement": {"error_rate": -60.0}
                }
            },
            {
                "name": "database_optimization",
                "condition": lambda metrics: (
                    metrics.get('avg_response_time_ms', 0) > 1000 and 
                    metrics.get('database_query_time_ms', 0) > 500
                ),
                "recommendation": {
                    "title": "Database Performance Optimization",
                    "description": "Database queries are slow, optimize database performance",
                    "optimization_type": OptimizationType.DATABASE,
                    "priority": OptimizationPriority.HIGH,
                    "estimated_impact": "40-60% query time improvement",
                    "implementation_effort": "Medium",
                    "prerequisites": ["Query analysis", "Index review"],
                    "steps": [
                        "Analyze slow queries and add appropriate indexes",
                        "Optimize query structure and joins",
                        "Implement query result caching",
                        "Consider database connection pooling",
                        "Review and optimize database schema"
                    ],
                    "metrics_to_monitor": ["database_query_time_ms", "avg_response_time_ms"],
                    "expected_improvement": {"database_query_time_ms": -50.0, "avg_response_time_ms": -25.0}
                }
            },
            {
                "name": "cache_optimization",
                "condition": lambda metrics: metrics.get('cache_hit_rate', 1.0) < 0.8,
                "recommendation": {
                    "title": "Cache Hit Rate Optimization",
                    "description": "Cache hit rate is low, optimize caching strategy",
                    "optimization_type": OptimizationType.CACHE,
                    "priority": OptimizationPriority.MEDIUM,
                    "estimated_impact": "15-25% performance improvement",
                    "implementation_effort": "Low",
                    "prerequisites": ["Cache analysis", "Usage patterns review"],
                    "steps": [
                        "Analyze cache usage patterns",
                        "Optimize cache key strategies",
                        "Adjust cache TTL values",
                        "Implement cache warming strategies",
                        "Consider multi-level caching"
                    ],
                    "metrics_to_monitor": ["cache_hit_rate", "avg_response_time_ms"],
                    "expected_improvement": {"cache_hit_rate": 15.0, "avg_response_time_ms": -20.0}
                }
            }
        ]
    
    async def start(self):
        """Start continuous optimization"""
        if self.is_running:
            logger.warning("ContinuousOptimizer already running")
            return
        
        self.is_running = True
        logger.info("Starting ContinuousOptimizer")
        
        # Start background analysis
        asyncio.create_task(self._optimization_loop())
    
    async def stop(self):
        """Stop continuous optimization"""
        self.is_running = False
        logger.info("Stopped ContinuousOptimizer")
    
    async def _optimization_loop(self):
        """Main optimization analysis loop"""
        while self.is_running:
            try:
                await self._run_optimization_analysis()
                await asyncio.sleep(self.analysis_interval)
            except Exception as e:
                logger.error(f"Error in optimization loop: {e}")
                await asyncio.sleep(30)
    
    async def _run_optimization_analysis(self):
        """Run optimization analysis cycle"""
        try:
            # Collect current metrics
            current_metrics = await self._collect_current_metrics()
            
            # Update metrics history
            self._update_metrics_history(current_metrics)
            
            # Analyze performance trends
            await self._analyze_performance_trends()
            
            # Generate optimization recommendations
            await self._generate_recommendations(current_metrics)
            
            # Save analysis results
            await self._save_analysis_results()
            
            self.last_analysis = datetime.now()
            logger.debug("Completed optimization analysis cycle")
            
        except Exception as e:
            logger.error(f"Error in optimization analysis: {e}")
    
    async def _collect_current_metrics(self) -> Dict[str, float]:
        """Collect current metrics from all providers"""
        metrics = {}
        
        for provider in self.metric_providers:
            try:
                provider_metrics = await provider()
                if isinstance(provider_metrics, dict):
                    metrics.update(provider_metrics)
            except Exception as e:
                logger.warning(f"Error collecting metrics from provider: {e}")
        
        return metrics
    
    def _update_metrics_history(self, metrics: Dict[str, float]):
        """Update metrics history for trend analysis"""
        timestamp = datetime.now()
        
        for metric_name, value in metrics.items():
            self.metrics_history[metric_name].append({
                'timestamp': timestamp,
                'value': value
            })
    
    async def _analyze_performance_trends(self):
        """Analyze performance trends over time"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=self.trend_analysis_hours)
            
            for metric_name, history in self.metrics_history.items():
                # Filter recent data
                recent_data = [
                    point for point in history 
                    if point['timestamp'] > cutoff_time
                ]
                
                if len(recent_data) < 10:  # Need at least 10 data points
                    continue
                
                # Calculate trend
                trend = await self._calculate_trend(metric_name, recent_data)
                if trend:
                    self.performance_trends[metric_name] = trend
            
        except Exception as e:
            logger.error(f"Error analyzing performance trends: {e}")
    
    async def _calculate_trend(self, metric_name: str, data: List[Dict[str, Any]]) -> Optional[PerformanceTrend]:
        """Calculate trend for a specific metric"""
        try:
            if len(data) < 10:
                return None
            
            values = [point['value'] for point in data]
            
            # Calculate baseline (first 25% of data)
            baseline_size = max(1, len(values) // 4)
            baseline_values = values[:baseline_size]
            baseline_avg = statistics.mean(baseline_values)
            
            # Calculate current (last 25% of data)
            current_values = values[-baseline_size:]
            current_avg = statistics.mean(current_values)
            
            # Calculate change
            if baseline_avg != 0:
                change_percentage = ((current_avg - baseline_avg) / baseline_avg) * 100
            else:
                change_percentage = 0
            
            # Determine trend direction
            if abs(change_percentage) < 5:  # Less than 5% change
                trend_direction = "stable"
            elif change_percentage > 0:
                # For metrics like error_rate, response_time - increase is bad
                if metric_name in ['error_rate', 'avg_response_time_ms', 'cpu_percent', 'memory_percent']:
                    trend_direction = "degrading"
                else:
                    trend_direction = "improving"
            else:
                # For metrics like error_rate, response_time - decrease is good
                if metric_name in ['error_rate', 'avg_response_time_ms', 'cpu_percent', 'memory_percent']:
                    trend_direction = "improving"
                else:
                    trend_direction = "degrading"
            
            # Calculate confidence score based on data consistency
            variance = statistics.variance(values) if len(values) > 1 else 0
            confidence_score = max(0.1, min(1.0, 1.0 - (variance / (current_avg + 1))))
            
            return PerformanceTrend(
                metric_name=metric_name,
                time_period_hours=self.trend_analysis_hours,
                trend_direction=trend_direction,
                change_percentage=change_percentage,
                current_value=current_avg,
                baseline_value=baseline_avg,
                confidence_score=confidence_score,
                data_points=len(data)
            )
            
        except Exception as e:
            logger.error(f"Error calculating trend for {metric_name}: {e}")
            return None
    
    async def _generate_recommendations(self, current_metrics: Dict[str, float]):
        """Generate optimization recommendations based on current metrics and trends"""
        try:
            for rule in self.optimization_rules:
                try:
                    # Check if rule condition is met
                    if rule['condition'](current_metrics):
                        # Check if we already have this recommendation
                        recommendation_id = f"{rule['name']}_{datetime.now().strftime('%Y%m%d')}"
                        
                        if recommendation_id not in self.recommendations:
                            # Create new recommendation
                            rec_data = rule['recommendation']
                            recommendation = OptimizationRecommendation(
                                id=recommendation_id,
                                title=rec_data['title'],
                                description=rec_data['description'],
                                optimization_type=rec_data['optimization_type'],
                                priority=rec_data['priority'],
                                estimated_impact=rec_data['estimated_impact'],
                                implementation_effort=rec_data['implementation_effort'],
                                prerequisites=rec_data['prerequisites'],
                                steps=rec_data['steps'],
                                metrics_to_monitor=rec_data['metrics_to_monitor'],
                                expected_improvement=rec_data['expected_improvement'],
                                timestamp=datetime.now()
                            )
                            
                            self.recommendations[recommendation_id] = recommendation
                            logger.info(f"Generated optimization recommendation: {recommendation.title}")
                
                except Exception as e:
                    logger.error(f"Error processing optimization rule {rule['name']}: {e}")
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
    
    async def _save_analysis_results(self):
        """Save analysis results to storage"""
        try:
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save recommendations
            if self.recommendations:
                rec_file = self.storage_path / f"recommendations_{timestamp_str}.json"
                rec_data = {rid: rec.to_dict() for rid, rec in self.recommendations.items()}
                async with aiofiles.open(rec_file, 'w') as f:
                    await f.write(json.dumps(rec_data, indent=2))
            
            # Save trends
            if self.performance_trends:
                trends_file = self.storage_path / f"trends_{timestamp_str}.json"
                trends_data = {name: trend.to_dict() for name, trend in self.performance_trends.items()}
                async with aiofiles.open(trends_file, 'w') as f:
                    await f.write(json.dumps(trends_data, indent=2))
            
        except Exception as e:
            logger.error(f"Error saving analysis results: {e}")
    
    def add_metric_provider(self, provider: Callable):
        """Add a metric provider function"""
        self.metric_providers.append(provider)
        logger.info("Added metric provider to ContinuousOptimizer")
    
    async def implement_recommendation(self, recommendation_id: str, 
                                     implementation_notes: str = "") -> bool:
        """Mark recommendation as implemented and track results"""
        try:
            if recommendation_id not in self.recommendations:
                return False
            
            recommendation = self.recommendations[recommendation_id]
            
            # Collect before metrics
            before_metrics = await self._collect_current_metrics()
            
            # Update recommendation status
            recommendation.status = OptimizationStatus.IN_PROGRESS
            
            # In a real implementation, you would trigger the actual optimization here
            # For now, we'll simulate implementation
            await asyncio.sleep(1)
            
            # Collect after metrics (simulated improvement)
            after_metrics = await self._collect_current_metrics()
            
            # Calculate improvement (simulated)
            improvement_achieved = {}
            for metric, expected_change in recommendation.expected_improvement.items():
                if metric in before_metrics:
                    # Simulate partial achievement of expected improvement
                    actual_change = expected_change * 0.7  # 70% of expected improvement
                    improvement_achieved[metric] = actual_change
            
            # Create optimization result
            result = OptimizationResult(
                recommendation_id=recommendation_id,
                implementation_date=datetime.now(),
                before_metrics=before_metrics,
                after_metrics=after_metrics,
                improvement_achieved=improvement_achieved,
                success=True,
                notes=implementation_notes
            )
            
            self.optimization_results.append(result)
            recommendation.status = OptimizationStatus.COMPLETED
            
            # Save result
            await self._save_optimization_result(result)
            
            logger.info(f"Implemented optimization recommendation: {recommendation.title}")
            return True
            
        except Exception as e:
            logger.error(f"Error implementing recommendation {recommendation_id}: {e}")
            if recommendation_id in self.recommendations:
                self.recommendations[recommendation_id].status = OptimizationStatus.FAILED
            return False
    
    async def _save_optimization_result(self, result: OptimizationResult):
        """Save optimization result to storage"""
        try:
            result_file = self.storage_path / f"optimization_result_{result.recommendation_id}.json"
            async with aiofiles.open(result_file, 'w') as f:
                await f.write(json.dumps(result.to_dict(), indent=2))
        except Exception as e:
            logger.error(f"Error saving optimization result: {e}")
    
    def get_optimization_summary(self) -> Dict[str, Any]:
        """Get optimization summary"""
        # Count recommendations by status
        status_counts = defaultdict(int)
        priority_counts = defaultdict(int)
        type_counts = defaultdict(int)
        
        for rec in self.recommendations.values():
            status_counts[rec.status.value] += 1
            priority_counts[rec.priority.value] += 1
            type_counts[rec.optimization_type.value] += 1
        
        # Calculate trend summary
        trend_summary = {}
        for metric_name, trend in self.performance_trends.items():
            trend_summary[metric_name] = {
                "direction": trend.trend_direction,
                "change_percent": trend.change_percentage,
                "confidence": trend.confidence_score
            }
        
        return {
            "is_running": self.is_running,
            "last_analysis": self.last_analysis.isoformat(),
            "total_recommendations": len(self.recommendations),
            "recommendations_by_status": dict(status_counts),
            "recommendations_by_priority": dict(priority_counts),
            "recommendations_by_type": dict(type_counts),
            "optimization_results": len(self.optimization_results),
            "performance_trends": trend_summary,
            "metrics_tracked": len(self.metrics_history)
        }
    
    def get_recommendations(self, priority: Optional[OptimizationPriority] = None,
                          status: Optional[OptimizationStatus] = None) -> List[OptimizationRecommendation]:
        """Get optimization recommendations with optional filtering"""
        recommendations = list(self.recommendations.values())
        
        if priority:
            recommendations = [r for r in recommendations if r.priority == priority]
        
        if status:
            recommendations = [r for r in recommendations if r.status == status]
        
        # Sort by priority and timestamp
        priority_order = {
            OptimizationPriority.CRITICAL: 0,
            OptimizationPriority.HIGH: 1,
            OptimizationPriority.MEDIUM: 2,
            OptimizationPriority.LOW: 3
        }
        
        recommendations.sort(key=lambda r: (priority_order[r.priority], r.timestamp), reverse=True)
        
        return recommendations
    
    def get_performance_trends(self) -> Dict[str, PerformanceTrend]:
        """Get current performance trends"""
        return self.performance_trends.copy()
    
    def get_optimization_results(self) -> List[OptimizationResult]:
        """Get optimization implementation results"""
        return self.optimization_results.copy()

# Global instance
_continuous_optimizer = None

async def get_continuous_optimizer() -> ContinuousOptimizer:
    """Get or create global continuous optimizer instance"""
    global _continuous_optimizer
    if _continuous_optimizer is None:
        _continuous_optimizer = ContinuousOptimizer()
    return _continuous_optimizer