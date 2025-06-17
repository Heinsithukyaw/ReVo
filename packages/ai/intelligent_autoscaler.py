"""
Intelligent Auto-scaling Engine
Part of reVoAgent Phase 5: Advanced Intelligence & Automation
"""

import asyncio
import logging
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json

logger = logging.getLogger(__name__)

class ScalingDirection(Enum):
    UP = "up"
    DOWN = "down"
    MAINTAIN = "maintain"

class ScalingTrigger(Enum):
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    QUEUE_LENGTH = "queue_length"
    RESPONSE_TIME = "response_time"
    ERROR_RATE = "error_rate"
    PREDICTIVE = "predictive"

@dataclass
class SystemMetrics:
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: float
    active_connections: int
    queue_length: int
    response_time: float
    error_rate: float
    timestamp: datetime

@dataclass
class ScalingDecision:
    direction: ScalingDirection
    target_instances: int
    current_instances: int
    confidence: float
    triggers: List[ScalingTrigger]
    reasoning: str
    estimated_impact: Dict[str, float]
    timestamp: datetime

@dataclass
class ScalingRule:
    metric: str
    threshold_up: float
    threshold_down: float
    cooldown_period: int  # seconds
    weight: float
    enabled: bool

@dataclass
class AutoScalingConfig:
    min_instances: int
    max_instances: int
    target_cpu_utilization: float
    target_memory_utilization: float
    scale_up_cooldown: int
    scale_down_cooldown: int
    prediction_window: int  # minutes
    rules: List[ScalingRule]

class IntelligentAutoScaler:
    """AI-powered intelligent auto-scaling system"""
    
    def __init__(self, config: AutoScalingConfig = None):
        self.config = config or self._get_default_config()
        self.metrics_history: List[SystemMetrics] = []
        self.scaling_history: List[ScalingDecision] = []
        self.current_instances = 1
        self.last_scaling_action = datetime.now() - timedelta(hours=1)
        self.predictive_model = None
        
        # Performance tracking
        self.scaling_effectiveness: Dict[str, List[float]] = {
            "cpu_improvement": [],
            "memory_improvement": [],
            "response_time_improvement": [],
            "cost_efficiency": []
        }
        
        logger.info("🚀 Intelligent Auto-scaler initialized")
    
    def _get_default_config(self) -> AutoScalingConfig:
        """Get default auto-scaling configuration"""
        return AutoScalingConfig(
            min_instances=1,
            max_instances=10,
            target_cpu_utilization=70.0,
            target_memory_utilization=80.0,
            scale_up_cooldown=300,  # 5 minutes
            scale_down_cooldown=600,  # 10 minutes
            prediction_window=15,  # 15 minutes
            rules=[
                ScalingRule("cpu_usage", 80.0, 30.0, 300, 1.0, True),
                ScalingRule("memory_usage", 85.0, 40.0, 300, 0.8, True),
                ScalingRule("queue_length", 50.0, 5.0, 180, 0.9, True),
                ScalingRule("response_time", 5.0, 1.0, 240, 0.7, True),
                ScalingRule("error_rate", 5.0, 1.0, 120, 1.2, True)
            ]
        )
    
    async def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            # Simulate additional metrics (in real implementation, these would come from monitoring)
            active_connections = len(psutil.net_connections())
            queue_length = self._estimate_queue_length()
            response_time = self._estimate_response_time()
            error_rate = self._estimate_error_rate()
            
            metrics = SystemMetrics(
                cpu_usage=cpu_percent,
                memory_usage=memory.percent,
                disk_usage=disk.percent,
                network_io=network.bytes_sent + network.bytes_recv,
                active_connections=active_connections,
                queue_length=queue_length,
                response_time=response_time,
                error_rate=error_rate,
                timestamp=datetime.now()
            )
            
            # Store in history
            self.metrics_history.append(metrics)
            
            # Keep only recent history (last 24 hours)
            cutoff_time = datetime.now() - timedelta(hours=24)
            self.metrics_history = [
                m for m in self.metrics_history 
                if m.timestamp > cutoff_time
            ]
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            # Return default metrics
            return SystemMetrics(
                cpu_usage=50.0, memory_usage=60.0, disk_usage=30.0,
                network_io=0, active_connections=10, queue_length=5,
                response_time=2.0, error_rate=1.0, timestamp=datetime.now()
            )
    
    async def analyze_system_load(self) -> ScalingDecision:
        """Analyze current system load and make scaling decision"""
        try:
            # Collect current metrics
            current_metrics = await self.collect_system_metrics()
            
            # Check cooldown periods
            time_since_last_scaling = (datetime.now() - self.last_scaling_action).total_seconds()
            
            # Analyze each scaling rule
            scaling_signals = []
            total_weight = 0
            weighted_score = 0
            
            for rule in self.config.rules:
                if not rule.enabled:
                    continue
                
                metric_value = getattr(current_metrics, rule.metric, 0)
                signal_strength = self._evaluate_scaling_rule(rule, metric_value, time_since_last_scaling)
                
                scaling_signals.append({
                    "rule": rule.metric,
                    "value": metric_value,
                    "signal": signal_strength,
                    "weight": rule.weight
                })
                
                weighted_score += signal_strength * rule.weight
                total_weight += rule.weight
            
            # Normalize score
            if total_weight > 0:
                normalized_score = weighted_score / total_weight
            else:
                normalized_score = 0
            
            # Add predictive analysis
            predictive_signal = await self._get_predictive_scaling_signal()
            if predictive_signal:
                scaling_signals.append(predictive_signal)
                normalized_score = (normalized_score + predictive_signal["signal"]) / 2
            
            # Make scaling decision
            decision = self._make_scaling_decision(normalized_score, current_metrics, scaling_signals)
            
            # Store decision
            self.scaling_history.append(decision)
            
            return decision
            
        except Exception as e:
            logger.error(f"System load analysis failed: {e}")
            return ScalingDecision(
                direction=ScalingDirection.MAINTAIN,
                target_instances=self.current_instances,
                current_instances=self.current_instances,
                confidence=0.1,
                triggers=[],
                reasoning=f"Analysis failed: {e}",
                estimated_impact={},
                timestamp=datetime.now()
            )
    
    def _evaluate_scaling_rule(self, rule: ScalingRule, metric_value: float, time_since_last_scaling: float) -> float:
        """Evaluate a single scaling rule and return signal strength (-1 to 1)"""
        # Check cooldown
        if time_since_last_scaling < rule.cooldown_period:
            return 0  # No signal during cooldown
        
        # Scale up signal
        if metric_value > rule.threshold_up:
            # Stronger signal for higher values
            excess = metric_value - rule.threshold_up
            max_excess = 100 - rule.threshold_up  # Assuming percentage metrics
            signal = min(1.0, excess / max_excess) if max_excess > 0 else 1.0
            return signal
        
        # Scale down signal
        elif metric_value < rule.threshold_down:
            # Stronger signal for lower values
            deficit = rule.threshold_down - metric_value
            max_deficit = rule.threshold_down  # Down to 0
            signal = -min(1.0, deficit / max_deficit) if max_deficit > 0 else -1.0
            return signal
        
        # No scaling signal
        return 0
    
    async def _get_predictive_scaling_signal(self) -> Optional[Dict[str, Any]]:
        """Get predictive scaling signal based on historical patterns"""
        try:
            if len(self.metrics_history) < 10:
                return None
            
            # Simple trend analysis
            recent_metrics = self.metrics_history[-10:]
            
            # Calculate trends
            cpu_trend = self._calculate_trend([m.cpu_usage for m in recent_metrics])
            memory_trend = self._calculate_trend([m.memory_usage for m in recent_metrics])
            queue_trend = self._calculate_trend([m.queue_length for m in recent_metrics])
            
            # Combine trends
            combined_trend = (cpu_trend + memory_trend + queue_trend) / 3
            
            # Convert trend to scaling signal
            if combined_trend > 2.0:  # Strong upward trend
                signal = 0.7
            elif combined_trend > 1.0:  # Moderate upward trend
                signal = 0.4
            elif combined_trend < -2.0:  # Strong downward trend
                signal = -0.7
            elif combined_trend < -1.0:  # Moderate downward trend
                signal = -0.4
            else:
                signal = 0
            
            return {
                "rule": "predictive",
                "value": combined_trend,
                "signal": signal,
                "weight": 0.5
            }
            
        except Exception as e:
            logger.error(f"Predictive analysis failed: {e}")
            return None
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend in a series of values"""
        if len(values) < 2:
            return 0
        
        # Simple linear trend calculation
        n = len(values)
        x = list(range(n))
        
        # Calculate slope using least squares
        x_mean = sum(x) / n
        y_mean = sum(values) / n
        
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0
        
        slope = numerator / denominator
        return slope
    
    def _make_scaling_decision(self, signal_score: float, current_metrics: SystemMetrics, 
                             scaling_signals: List[Dict]) -> ScalingDecision:
        """Make final scaling decision based on analysis"""
        
        # Determine scaling direction
        if signal_score > 0.3:  # Scale up threshold
            direction = ScalingDirection.UP
            target_instances = min(self.config.max_instances, self.current_instances + 1)
        elif signal_score < -0.3:  # Scale down threshold
            direction = ScalingDirection.DOWN
            target_instances = max(self.config.min_instances, self.current_instances - 1)
        else:
            direction = ScalingDirection.MAINTAIN
            target_instances = self.current_instances
        
        # Calculate confidence
        confidence = min(0.95, abs(signal_score))
        
        # Identify triggers
        triggers = []
        for signal in scaling_signals:
            if abs(signal["signal"]) > 0.2:
                if signal["rule"] == "cpu_usage":
                    triggers.append(ScalingTrigger.CPU_USAGE)
                elif signal["rule"] == "memory_usage":
                    triggers.append(ScalingTrigger.MEMORY_USAGE)
                elif signal["rule"] == "queue_length":
                    triggers.append(ScalingTrigger.QUEUE_LENGTH)
                elif signal["rule"] == "response_time":
                    triggers.append(ScalingTrigger.RESPONSE_TIME)
                elif signal["rule"] == "error_rate":
                    triggers.append(ScalingTrigger.ERROR_RATE)
                elif signal["rule"] == "predictive":
                    triggers.append(ScalingTrigger.PREDICTIVE)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(direction, signal_score, scaling_signals, current_metrics)
        
        # Estimate impact
        estimated_impact = self._estimate_scaling_impact(direction, target_instances, current_metrics)
        
        return ScalingDecision(
            direction=direction,
            target_instances=target_instances,
            current_instances=self.current_instances,
            confidence=confidence,
            triggers=triggers,
            reasoning=reasoning,
            estimated_impact=estimated_impact,
            timestamp=datetime.now()
        )
    
    def _generate_reasoning(self, direction: ScalingDirection, signal_score: float, 
                          scaling_signals: List[Dict], current_metrics: SystemMetrics) -> str:
        """Generate human-readable reasoning for scaling decision"""
        
        if direction == ScalingDirection.MAINTAIN:
            return f"System metrics within acceptable ranges. Signal score: {signal_score:.2f}"
        
        # Find strongest signals
        strong_signals = [s for s in scaling_signals if abs(s["signal"]) > 0.3]
        strong_signals.sort(key=lambda x: abs(x["signal"]), reverse=True)
        
        if direction == ScalingDirection.UP:
            reasons = []
            for signal in strong_signals[:3]:  # Top 3 reasons
                if signal["signal"] > 0:
                    reasons.append(f"{signal['rule']} at {signal['value']:.1f}")
            
            reason_text = ", ".join(reasons) if reasons else "predictive analysis"
            return f"Scaling up due to high {reason_text}. Signal score: {signal_score:.2f}"
        
        else:  # Scale down
            reasons = []
            for signal in strong_signals[:3]:
                if signal["signal"] < 0:
                    reasons.append(f"{signal['rule']} at {signal['value']:.1f}")
            
            reason_text = ", ".join(reasons) if reasons else "low utilization"
            return f"Scaling down due to low {reason_text}. Signal score: {signal_score:.2f}"
    
    def _estimate_scaling_impact(self, direction: ScalingDirection, target_instances: int, 
                               current_metrics: SystemMetrics) -> Dict[str, float]:
        """Estimate the impact of scaling action"""
        
        if direction == ScalingDirection.MAINTAIN:
            return {"cpu_change": 0, "memory_change": 0, "cost_change": 0, "performance_change": 0}
        
        instance_ratio = target_instances / self.current_instances if self.current_instances > 0 else 1
        
        # Estimate resource changes (inverse relationship)
        cpu_change = -(current_metrics.cpu_usage * (1 - 1/instance_ratio)) if direction == ScalingDirection.UP else current_metrics.cpu_usage * (1 - instance_ratio)
        memory_change = -(current_metrics.memory_usage * (1 - 1/instance_ratio)) if direction == ScalingDirection.UP else current_metrics.memory_usage * (1 - instance_ratio)
        
        # Estimate cost change (linear relationship)
        cost_change = (target_instances - self.current_instances) * 100  # $100 per instance
        
        # Estimate performance change
        if direction == ScalingDirection.UP:
            performance_change = min(50, current_metrics.response_time * 0.3)  # Improvement
        else:
            performance_change = -min(20, current_metrics.response_time * 0.1)  # Degradation
        
        return {
            "cpu_change": cpu_change,
            "memory_change": memory_change,
            "cost_change": cost_change,
            "performance_change": performance_change
        }
    
    async def auto_scale_agents(self, scaling_decision: ScalingDecision) -> bool:
        """Execute auto-scaling action"""
        try:
            if scaling_decision.direction == ScalingDirection.MAINTAIN:
                logger.info("No scaling action needed")
                return True
            
            logger.info(f"Executing scaling action: {scaling_decision.direction.value} to {scaling_decision.target_instances} instances")
            logger.info(f"Reasoning: {scaling_decision.reasoning}")
            
            # In a real implementation, this would interact with container orchestration
            # For now, we'll simulate the scaling action
            
            old_instances = self.current_instances
            self.current_instances = scaling_decision.target_instances
            self.last_scaling_action = datetime.now()
            
            # Track scaling effectiveness
            await self._track_scaling_effectiveness(scaling_decision, old_instances)
            
            logger.info(f"✅ Scaling completed: {old_instances} → {self.current_instances} instances")
            return True
            
        except Exception as e:
            logger.error(f"Auto-scaling failed: {e}")
            return False
    
    async def _track_scaling_effectiveness(self, decision: ScalingDecision, old_instances: int):
        """Track the effectiveness of scaling decisions"""
        try:
            # Wait a bit for the scaling to take effect
            await asyncio.sleep(30)
            
            # Collect metrics after scaling
            post_scaling_metrics = await self.collect_system_metrics()
            
            # Calculate actual improvements
            if len(self.metrics_history) >= 2:
                pre_scaling_metrics = self.metrics_history[-2]
                
                cpu_improvement = pre_scaling_metrics.cpu_usage - post_scaling_metrics.cpu_usage
                memory_improvement = pre_scaling_metrics.memory_usage - post_scaling_metrics.memory_usage
                response_time_improvement = pre_scaling_metrics.response_time - post_scaling_metrics.response_time
                
                # Calculate cost efficiency (improvement per dollar spent)
                cost_change = abs(decision.estimated_impact.get("cost_change", 0))
                total_improvement = cpu_improvement + memory_improvement + response_time_improvement
                cost_efficiency = total_improvement / max(cost_change, 1)
                
                # Store effectiveness metrics
                self.scaling_effectiveness["cpu_improvement"].append(cpu_improvement)
                self.scaling_effectiveness["memory_improvement"].append(memory_improvement)
                self.scaling_effectiveness["response_time_improvement"].append(response_time_improvement)
                self.scaling_effectiveness["cost_efficiency"].append(cost_efficiency)
                
                # Keep only recent effectiveness data
                for key in self.scaling_effectiveness:
                    if len(self.scaling_effectiveness[key]) > 50:
                        self.scaling_effectiveness[key] = self.scaling_effectiveness[key][-50:]
                
                logger.info(f"Scaling effectiveness - CPU: {cpu_improvement:.1f}%, Memory: {memory_improvement:.1f}%, Response: {response_time_improvement:.1f}s")
            
        except Exception as e:
            logger.error(f"Failed to track scaling effectiveness: {e}")
    
    def _estimate_queue_length(self) -> int:
        """Estimate current queue length (simulation)"""
        # In real implementation, this would come from monitoring
        import random
        base_queue = random.randint(0, 20)
        cpu_factor = psutil.cpu_percent() / 10
        return int(base_queue + cpu_factor)
    
    def _estimate_response_time(self) -> float:
        """Estimate current response time (simulation)"""
        # In real implementation, this would come from monitoring
        import random
        base_time = random.uniform(0.5, 3.0)
        load_factor = psutil.cpu_percent() / 50
        return base_time * (1 + load_factor)
    
    def _estimate_error_rate(self) -> float:
        """Estimate current error rate (simulation)"""
        # In real implementation, this would come from monitoring
        import random
        base_rate = random.uniform(0.1, 2.0)
        stress_factor = max(0, (psutil.cpu_percent() - 70) / 30)
        return base_rate * (1 + stress_factor)
    
    async def get_scaling_analytics(self) -> Dict[str, Any]:
        """Get analytics about auto-scaling performance"""
        
        # Calculate average effectiveness
        avg_effectiveness = {}
        for key, values in self.scaling_effectiveness.items():
            avg_effectiveness[key] = sum(values) / len(values) if values else 0
        
        # Recent scaling actions
        recent_actions = [
            {
                "timestamp": decision.timestamp.isoformat(),
                "direction": decision.direction.value,
                "instances": f"{decision.current_instances} → {decision.target_instances}",
                "confidence": decision.confidence,
                "triggers": [t.value for t in decision.triggers]
            }
            for decision in self.scaling_history[-10:]  # Last 10 actions
        ]
        
        return {
            "current_instances": self.current_instances,
            "total_scaling_actions": len(self.scaling_history),
            "avg_effectiveness": avg_effectiveness,
            "recent_actions": recent_actions,
            "config": asdict(self.config),
            "metrics_history_size": len(self.metrics_history),
            "last_scaling_action": self.last_scaling_action.isoformat()
        }

# Global instance
intelligent_autoscaler = IntelligentAutoScaler()