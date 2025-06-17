"""
Anomaly Detection Engine
Part of reVoAgent Phase 5: Advanced Intelligence & Automation
"""

import asyncio
import logging
import numpy as np
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
import math

logger = logging.getLogger(__name__)

class AnomalySeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AnomalyType(Enum):
    PERFORMANCE = "performance"
    RESOURCE = "resource"
    SECURITY = "security"
    AVAILABILITY = "availability"
    PATTERN = "pattern"
    TREND = "trend"

@dataclass
class Anomaly:
    id: str
    type: AnomalyType
    severity: AnomalySeverity
    metric: str
    value: float
    expected_value: float
    deviation: float
    confidence: float
    timestamp: datetime
    description: str
    context: Dict[str, Any]
    suggested_actions: List[str]

@dataclass
class PredictedIssue:
    id: str
    issue_type: str
    probability: float
    estimated_time: datetime
    impact_level: str
    description: str
    prevention_actions: List[str]
    monitoring_metrics: List[str]

@dataclass
class TrendData:
    metric: str
    values: List[float]
    timestamps: List[datetime]
    trend_direction: str
    trend_strength: float
    seasonality: Optional[Dict[str, float]]

class StatisticalDetector:
    """Statistical anomaly detection using Z-score and IQR methods"""
    
    def __init__(self, window_size: int = 100, z_threshold: float = 3.0):
        self.window_size = window_size
        self.z_threshold = z_threshold
        self.data_windows: Dict[str, List[float]] = {}
    
    def add_data_point(self, metric: str, value: float):
        """Add a new data point for a metric"""
        if metric not in self.data_windows:
            self.data_windows[metric] = []
        
        self.data_windows[metric].append(value)
        
        # Keep only recent data
        if len(self.data_windows[metric]) > self.window_size:
            self.data_windows[metric] = self.data_windows[metric][-self.window_size:]
    
    def detect_anomaly(self, metric: str, value: float) -> Optional[Tuple[float, float]]:
        """Detect anomaly using Z-score method. Returns (z_score, expected_value) if anomaly"""
        if metric not in self.data_windows or len(self.data_windows[metric]) < 10:
            return None
        
        data = self.data_windows[metric]
        mean = statistics.mean(data)
        std_dev = statistics.stdev(data) if len(data) > 1 else 0
        
        if std_dev == 0:
            return None
        
        z_score = abs(value - mean) / std_dev
        
        if z_score > self.z_threshold:
            return z_score, mean
        
        return None
    
    def detect_iqr_anomaly(self, metric: str, value: float) -> Optional[Tuple[float, float]]:
        """Detect anomaly using Interquartile Range method"""
        if metric not in self.data_windows or len(self.data_windows[metric]) < 20:
            return None
        
        data = sorted(self.data_windows[metric])
        n = len(data)
        
        q1_idx = n // 4
        q3_idx = 3 * n // 4
        
        q1 = data[q1_idx]
        q3 = data[q3_idx]
        iqr = q3 - q1
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        if value < lower_bound or value > upper_bound:
            expected = statistics.median(data)
            deviation = abs(value - expected) / (iqr if iqr > 0 else 1)
            return deviation, expected
        
        return None

class PatternDetector:
    """Pattern-based anomaly detection"""
    
    def __init__(self, pattern_window: int = 50):
        self.pattern_window = pattern_window
        self.patterns: Dict[str, List[List[float]]] = {}
    
    def learn_pattern(self, metric: str, values: List[float]):
        """Learn normal patterns for a metric"""
        if metric not in self.patterns:
            self.patterns[metric] = []
        
        # Extract patterns of fixed length
        pattern_length = min(10, len(values))
        if len(values) >= pattern_length:
            for i in range(len(values) - pattern_length + 1):
                pattern = values[i:i + pattern_length]
                self.patterns[metric].append(pattern)
        
        # Keep only recent patterns
        if len(self.patterns[metric]) > self.pattern_window:
            self.patterns[metric] = self.patterns[metric][-self.pattern_window:]
    
    def detect_pattern_anomaly(self, metric: str, recent_values: List[float]) -> Optional[float]:
        """Detect pattern anomalies by comparing with learned patterns"""
        if metric not in self.patterns or len(self.patterns[metric]) < 5:
            return None
        
        if len(recent_values) < 5:
            return None
        
        # Compare recent pattern with learned patterns
        recent_pattern = recent_values[-5:]  # Last 5 values
        
        similarities = []
        for learned_pattern in self.patterns[metric]:
            if len(learned_pattern) >= 5:
                similarity = self._calculate_pattern_similarity(recent_pattern, learned_pattern[:5])
                similarities.append(similarity)
        
        if similarities:
            avg_similarity = statistics.mean(similarities)
            # If similarity is very low, it's an anomaly
            if avg_similarity < 0.3:  # Threshold for pattern anomaly
                return 1.0 - avg_similarity
        
        return None
    
    def _calculate_pattern_similarity(self, pattern1: List[float], pattern2: List[float]) -> float:
        """Calculate similarity between two patterns (0-1, higher is more similar)"""
        if len(pattern1) != len(pattern2):
            return 0.0
        
        # Normalize patterns
        def normalize(pattern):
            if not pattern:
                return pattern
            min_val, max_val = min(pattern), max(pattern)
            if max_val == min_val:
                return [0.5] * len(pattern)
            return [(x - min_val) / (max_val - min_val) for x in pattern]
        
        norm1 = normalize(pattern1)
        norm2 = normalize(pattern2)
        
        # Calculate correlation coefficient
        try:
            correlation = np.corrcoef(norm1, norm2)[0, 1]
            return max(0, correlation)  # Only positive correlations
        except:
            return 0.0

class AnomalyDetectionEngine:
    """AI-powered anomaly detection system"""
    
    def __init__(self):
        self.statistical_detector = StatisticalDetector()
        self.pattern_detector = PatternDetector()
        self.anomalies: List[Anomaly] = []
        self.predicted_issues: List[PredictedIssue] = []
        self.trend_data: Dict[str, TrendData] = {}
        
        # Anomaly thresholds
        self.severity_thresholds = {
            "z_score": {"low": 2.0, "medium": 3.0, "high": 4.0, "critical": 5.0},
            "deviation": {"low": 1.5, "medium": 2.0, "high": 3.0, "critical": 4.0}
        }
        
        logger.info("🔍 Anomaly Detection Engine initialized")
    
    async def detect_performance_anomalies(self, metrics: Dict[str, float]) -> List[Anomaly]:
        """Detect performance anomalies in system metrics"""
        anomalies = []
        
        try:
            for metric, value in metrics.items():
                # Add data point to statistical detector
                self.statistical_detector.add_data_point(metric, value)
                
                # Statistical anomaly detection
                z_result = self.statistical_detector.detect_anomaly(metric, value)
                if z_result:
                    z_score, expected = z_result
                    anomaly = self._create_anomaly(
                        metric, value, expected, z_score, 
                        AnomalyType.PERFORMANCE, "z_score"
                    )
                    anomalies.append(anomaly)
                
                # IQR anomaly detection
                iqr_result = self.statistical_detector.detect_iqr_anomaly(metric, value)
                if iqr_result:
                    deviation, expected = iqr_result
                    anomaly = self._create_anomaly(
                        metric, value, expected, deviation,
                        AnomalyType.PERFORMANCE, "iqr"
                    )
                    anomalies.append(anomaly)
                
                # Update trend data
                await self._update_trend_data(metric, value)
            
            # Pattern-based detection
            for metric in metrics:
                if metric in self.statistical_detector.data_windows:
                    recent_values = self.statistical_detector.data_windows[metric]
                    pattern_anomaly = self.pattern_detector.detect_pattern_anomaly(metric, recent_values)
                    
                    if pattern_anomaly:
                        expected = statistics.mean(recent_values[-10:]) if len(recent_values) >= 10 else metrics[metric]
                        anomaly = self._create_anomaly(
                            metric, metrics[metric], expected, pattern_anomaly,
                            AnomalyType.PATTERN, "pattern"
                        )
                        anomalies.append(anomaly)
                    
                    # Learn patterns from recent data
                    if len(recent_values) >= 20:
                        self.pattern_detector.learn_pattern(metric, recent_values[-20:])
            
            # Store detected anomalies
            self.anomalies.extend(anomalies)
            
            # Keep only recent anomalies
            cutoff_time = datetime.now() - timedelta(hours=24)
            self.anomalies = [a for a in self.anomalies if a.timestamp > cutoff_time]
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Performance anomaly detection failed: {e}")
            return []
    
    async def predict_potential_issues(self, trend_data: Dict[str, TrendData]) -> List[PredictedIssue]:
        """Predict potential issues based on trend analysis"""
        predicted_issues = []
        
        try:
            for metric, trend in trend_data.items():
                # Analyze trend for potential issues
                issue = await self._analyze_trend_for_issues(metric, trend)
                if issue:
                    predicted_issues.append(issue)
            
            # Cross-metric analysis
            cross_metric_issues = await self._cross_metric_analysis(trend_data)
            predicted_issues.extend(cross_metric_issues)
            
            # Store predictions
            self.predicted_issues.extend(predicted_issues)
            
            # Keep only recent predictions
            cutoff_time = datetime.now() - timedelta(hours=48)
            self.predicted_issues = [p for p in self.predicted_issues if p.estimated_time > cutoff_time]
            
            return predicted_issues
            
        except Exception as e:
            logger.error(f"Issue prediction failed: {e}")
            return []
    
    def _create_anomaly(self, metric: str, value: float, expected: float, 
                       deviation: float, anomaly_type: AnomalyType, method: str) -> Anomaly:
        """Create an anomaly object"""
        
        # Determine severity
        severity = self._determine_severity(deviation, method)
        
        # Generate description
        description = self._generate_anomaly_description(metric, value, expected, deviation, method)
        
        # Suggest actions
        suggested_actions = self._suggest_actions(metric, anomaly_type, severity)
        
        # Calculate confidence
        confidence = min(0.95, deviation / 5.0) if method == "z_score" else min(0.95, deviation / 3.0)
        
        return Anomaly(
            id=f"anomaly_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(metric) % 1000}",
            type=anomaly_type,
            severity=severity,
            metric=metric,
            value=value,
            expected_value=expected,
            deviation=deviation,
            confidence=confidence,
            timestamp=datetime.now(),
            description=description,
            context={"method": method, "metric_type": self._classify_metric(metric)},
            suggested_actions=suggested_actions
        )
    
    def _determine_severity(self, deviation: float, method: str) -> AnomalySeverity:
        """Determine anomaly severity based on deviation"""
        thresholds = self.severity_thresholds.get(method, self.severity_thresholds["z_score"])
        
        if deviation >= thresholds["critical"]:
            return AnomalySeverity.CRITICAL
        elif deviation >= thresholds["high"]:
            return AnomalySeverity.HIGH
        elif deviation >= thresholds["medium"]:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW
    
    def _generate_anomaly_description(self, metric: str, value: float, expected: float, 
                                    deviation: float, method: str) -> str:
        """Generate human-readable anomaly description"""
        direction = "higher" if value > expected else "lower"
        percentage = abs((value - expected) / expected * 100) if expected != 0 else 0
        
        return (f"{metric} is {direction} than expected: {value:.2f} vs {expected:.2f} "
                f"({percentage:.1f}% deviation, detected by {method})")
    
    def _suggest_actions(self, metric: str, anomaly_type: AnomalyType, severity: AnomalySeverity) -> List[str]:
        """Suggest actions based on anomaly characteristics"""
        actions = []
        
        # Metric-specific actions
        if "cpu" in metric.lower():
            actions.extend([
                "Check for runaway processes",
                "Consider scaling up resources",
                "Review recent deployments"
            ])
        elif "memory" in metric.lower():
            actions.extend([
                "Check for memory leaks",
                "Review memory-intensive operations",
                "Consider increasing memory allocation"
            ])
        elif "response_time" in metric.lower():
            actions.extend([
                "Check database performance",
                "Review network latency",
                "Optimize slow queries"
            ])
        elif "error" in metric.lower():
            actions.extend([
                "Check application logs",
                "Review recent changes",
                "Validate input data"
            ])
        
        # Severity-specific actions
        if severity in [AnomalySeverity.HIGH, AnomalySeverity.CRITICAL]:
            actions.extend([
                "Alert on-call engineer",
                "Consider immediate intervention",
                "Prepare rollback plan"
            ])
        
        return actions[:5]  # Limit to 5 actions
    
    def _classify_metric(self, metric: str) -> str:
        """Classify metric type for context"""
        metric_lower = metric.lower()
        
        if any(keyword in metric_lower for keyword in ["cpu", "processor"]):
            return "cpu"
        elif any(keyword in metric_lower for keyword in ["memory", "ram"]):
            return "memory"
        elif any(keyword in metric_lower for keyword in ["disk", "storage"]):
            return "storage"
        elif any(keyword in metric_lower for keyword in ["network", "bandwidth"]):
            return "network"
        elif any(keyword in metric_lower for keyword in ["response", "latency"]):
            return "performance"
        elif any(keyword in metric_lower for keyword in ["error", "failure"]):
            return "reliability"
        else:
            return "general"
    
    async def _update_trend_data(self, metric: str, value: float):
        """Update trend data for a metric"""
        if metric not in self.trend_data:
            self.trend_data[metric] = TrendData(
                metric=metric,
                values=[],
                timestamps=[],
                trend_direction="stable",
                trend_strength=0.0,
                seasonality=None
            )
        
        trend = self.trend_data[metric]
        trend.values.append(value)
        trend.timestamps.append(datetime.now())
        
        # Keep only recent data (last 100 points)
        if len(trend.values) > 100:
            trend.values = trend.values[-100:]
            trend.timestamps = trend.timestamps[-100:]
        
        # Update trend analysis
        if len(trend.values) >= 10:
            trend.trend_direction, trend.trend_strength = self._calculate_trend(trend.values)
    
    def _calculate_trend(self, values: List[float]) -> Tuple[str, float]:
        """Calculate trend direction and strength"""
        if len(values) < 2:
            return "stable", 0.0
        
        # Simple linear regression
        n = len(values)
        x = list(range(n))
        
        x_mean = sum(x) / n
        y_mean = sum(values) / n
        
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return "stable", 0.0
        
        slope = numerator / denominator
        
        # Determine direction and strength
        if abs(slope) < 0.01:
            return "stable", abs(slope)
        elif slope > 0:
            return "increasing", abs(slope)
        else:
            return "decreasing", abs(slope)
    
    async def _analyze_trend_for_issues(self, metric: str, trend: TrendData) -> Optional[PredictedIssue]:
        """Analyze trend data to predict potential issues"""
        if len(trend.values) < 20:
            return None
        
        # Check for concerning trends
        if trend.trend_direction == "increasing" and trend.trend_strength > 0.1:
            if "cpu" in metric.lower() or "memory" in metric.lower():
                # Predict resource exhaustion
                current_value = trend.values[-1]
                rate_of_increase = trend.trend_strength
                
                # Estimate time to reach critical threshold (e.g., 90%)
                critical_threshold = 90.0
                if current_value < critical_threshold:
                    time_to_critical = (critical_threshold - current_value) / rate_of_increase
                    estimated_time = datetime.now() + timedelta(minutes=time_to_critical)
                    
                    return PredictedIssue(
                        id=f"predicted_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(metric) % 1000}",
                        issue_type="resource_exhaustion",
                        probability=min(0.9, trend.trend_strength * 2),
                        estimated_time=estimated_time,
                        impact_level="high" if time_to_critical < 60 else "medium",
                        description=f"{metric} trending upward, may reach critical levels",
                        prevention_actions=[
                            "Scale up resources proactively",
                            "Optimize resource usage",
                            "Set up additional monitoring"
                        ],
                        monitoring_metrics=[metric, f"{metric}_rate_of_change"]
                    )
        
        return None
    
    async def _cross_metric_analysis(self, trend_data: Dict[str, TrendData]) -> List[PredictedIssue]:
        """Analyze multiple metrics together to predict issues"""
        issues = []
        
        try:
            # Look for correlated issues
            cpu_trend = trend_data.get("cpu_usage")
            memory_trend = trend_data.get("memory_usage")
            response_time_trend = trend_data.get("response_time")
            
            # Check for system overload pattern
            if (cpu_trend and memory_trend and 
                cpu_trend.trend_direction == "increasing" and 
                memory_trend.trend_direction == "increasing"):
                
                combined_strength = (cpu_trend.trend_strength + memory_trend.trend_strength) / 2
                
                if combined_strength > 0.05:
                    issue = PredictedIssue(
                        id=f"predicted_overload_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        issue_type="system_overload",
                        probability=min(0.85, combined_strength * 3),
                        estimated_time=datetime.now() + timedelta(minutes=30),
                        impact_level="high",
                        description="System showing signs of overload (CPU and memory increasing)",
                        prevention_actions=[
                            "Scale out application instances",
                            "Optimize database queries",
                            "Review recent traffic patterns"
                        ],
                        monitoring_metrics=["cpu_usage", "memory_usage", "response_time"]
                    )
                    issues.append(issue)
            
            # Check for performance degradation pattern
            if (response_time_trend and 
                response_time_trend.trend_direction == "increasing" and 
                response_time_trend.trend_strength > 0.1):
                
                issue = PredictedIssue(
                    id=f"predicted_perf_deg_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    issue_type="performance_degradation",
                    probability=min(0.8, response_time_trend.trend_strength * 2),
                    estimated_time=datetime.now() + timedelta(minutes=15),
                    impact_level="medium",
                    description="Response times trending upward, performance may degrade",
                    prevention_actions=[
                        "Check database performance",
                        "Review application bottlenecks",
                        "Consider caching strategies"
                    ],
                    monitoring_metrics=["response_time", "database_query_time", "cache_hit_rate"]
                )
                issues.append(issue)
            
        except Exception as e:
            logger.error(f"Cross-metric analysis failed: {e}")
        
        return issues
    
    async def get_anomaly_analytics(self) -> Dict[str, Any]:
        """Get analytics about anomaly detection performance"""
        
        # Count anomalies by type and severity
        anomaly_counts = {}
        severity_counts = {}
        
        for anomaly in self.anomalies:
            anomaly_type = anomaly.type.value
            severity = anomaly.severity.value
            
            anomaly_counts[anomaly_type] = anomaly_counts.get(anomaly_type, 0) + 1
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Recent anomalies
        recent_anomalies = [
            {
                "id": a.id,
                "type": a.type.value,
                "severity": a.severity.value,
                "metric": a.metric,
                "description": a.description,
                "timestamp": a.timestamp.isoformat()
            }
            for a in sorted(self.anomalies, key=lambda x: x.timestamp, reverse=True)[:10]
        ]
        
        # Predicted issues
        predicted_issues_data = [
            {
                "id": p.id,
                "type": p.issue_type,
                "probability": p.probability,
                "estimated_time": p.estimated_time.isoformat(),
                "impact": p.impact_level,
                "description": p.description
            }
            for p in self.predicted_issues
        ]
        
        return {
            "total_anomalies": len(self.anomalies),
            "anomaly_counts_by_type": anomaly_counts,
            "severity_distribution": severity_counts,
            "recent_anomalies": recent_anomalies,
            "predicted_issues": predicted_issues_data,
            "metrics_monitored": len(self.statistical_detector.data_windows),
            "patterns_learned": sum(len(patterns) for patterns in self.pattern_detector.patterns.values()),
            "trend_data_size": len(self.trend_data)
        }

# Global instance
anomaly_detection_engine = AnomalyDetectionEngine()