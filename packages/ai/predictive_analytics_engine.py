"""
Predictive Analytics Engine
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
import pickle
import os

logger = logging.getLogger(__name__)

class PredictionType(Enum):
    PERFORMANCE = "performance"
    RESOURCE_USAGE = "resource_usage"
    TASK_SUCCESS = "task_success"
    RESPONSE_TIME = "response_time"
    SYSTEM_LOAD = "system_load"

@dataclass
class PredictionResult:
    prediction_type: PredictionType
    predicted_value: float
    confidence: float
    timestamp: datetime
    features_used: List[str]
    model_version: str
    metadata: Dict[str, Any]

@dataclass
class PerformanceMetrics:
    agent_id: str
    task_type: str
    success_rate: float
    avg_response_time: float
    resource_usage: float
    timestamp: datetime
    context: Dict[str, Any]

@dataclass
class WorkloadProfile:
    concurrent_tasks: int
    task_complexity: float
    resource_requirements: Dict[str, float]
    time_constraints: float
    priority_level: int

@dataclass
class Configuration:
    agent_count: int
    resource_allocation: Dict[str, float]
    timeout_settings: Dict[str, float]
    optimization_params: Dict[str, Any]

class SimpleMLModel:
    """Simple ML model for predictions without external dependencies"""
    
    def __init__(self, model_type: str = "linear_regression"):
        self.model_type = model_type
        self.weights = None
        self.bias = 0.0
        self.feature_means = None
        self.feature_stds = None
        self.is_trained = False
        
    def fit(self, X: np.ndarray, y: np.ndarray):
        """Train the model using simple linear regression"""
        if len(X) == 0:
            logger.warning("No training data provided")
            return
            
        # Normalize features
        self.feature_means = np.mean(X, axis=0)
        self.feature_stds = np.std(X, axis=0) + 1e-8  # Avoid division by zero
        X_normalized = (X - self.feature_means) / self.feature_stds
        
        # Simple linear regression using normal equation
        try:
            # Add bias term
            X_with_bias = np.column_stack([np.ones(len(X_normalized)), X_normalized])
            
            # Normal equation: theta = (X^T * X)^(-1) * X^T * y
            XtX = np.dot(X_with_bias.T, X_with_bias)
            Xty = np.dot(X_with_bias.T, y)
            
            # Add regularization to avoid singular matrix
            regularization = 1e-6 * np.eye(XtX.shape[0])
            theta = np.linalg.solve(XtX + regularization, Xty)
            
            self.bias = theta[0]
            self.weights = theta[1:]
            self.is_trained = True
            
            logger.info(f"Model trained with {len(X)} samples, {X.shape[1]} features")
            
        except Exception as e:
            logger.error(f"Model training failed: {e}")
            # Fallback to simple average
            self.bias = np.mean(y)
            self.weights = np.zeros(X.shape[1])
            self.is_trained = True
    
    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Make predictions with confidence estimates"""
        if not self.is_trained:
            logger.warning("Model not trained, returning default predictions")
            return np.full(len(X), 0.5), np.full(len(X), 0.1)
        
        if len(X) == 0:
            return np.array([]), np.array([])
        
        # Normalize features
        X_normalized = (X - self.feature_means) / self.feature_stds
        
        # Make predictions
        predictions = self.bias + np.dot(X_normalized, self.weights)
        
        # Simple confidence estimation based on feature variance
        feature_variance = np.var(X_normalized, axis=1)
        confidence = np.exp(-feature_variance)  # Higher variance = lower confidence
        confidence = np.clip(confidence, 0.1, 0.95)
        
        return predictions, confidence

class PredictiveAnalyticsEngine:
    """AI-powered predictive analytics for system optimization"""
    
    def __init__(self):
        self.models: Dict[PredictionType, SimpleMLModel] = {}
        self.historical_data: Dict[str, List[Dict]] = {}
        self.performance_history: List[PerformanceMetrics] = []
        self.prediction_cache: Dict[str, PredictionResult] = {}
        self.model_version = "1.0.0"
        
        # Initialize models for different prediction types
        for pred_type in PredictionType:
            self.models[pred_type] = SimpleMLModel()
        
        logger.info("🧠 Predictive Analytics Engine initialized")
    
    async def add_performance_data(self, metrics: PerformanceMetrics):
        """Add new performance data for training"""
        self.performance_history.append(metrics)
        
        # Keep only recent data (last 1000 entries)
        if len(self.performance_history) > 1000:
            self.performance_history = self.performance_history[-1000:]
        
        # Trigger model retraining if we have enough data
        if len(self.performance_history) >= 10:
            await self._retrain_models()
    
    async def predict_agent_performance(self, task_type: str, agent_id: str, context: Dict[str, Any] = None) -> PredictionResult:
        """Predict agent performance for a specific task"""
        try:
            # Extract features from historical data
            features = self._extract_features(task_type, agent_id, context or {})
            
            # Use performance prediction model
            model = self.models[PredictionType.PERFORMANCE]
            if not model.is_trained:
                # Return default prediction if model not trained
                return PredictionResult(
                    prediction_type=PredictionType.PERFORMANCE,
                    predicted_value=0.75,  # Default success rate
                    confidence=0.5,
                    timestamp=datetime.now(),
                    features_used=list(features.keys()),
                    model_version=self.model_version,
                    metadata={"status": "default_prediction", "reason": "model_not_trained"}
                )
            
            # Make prediction
            X = np.array([list(features.values())])
            predictions, confidence = model.predict(X)
            
            result = PredictionResult(
                prediction_type=PredictionType.PERFORMANCE,
                predicted_value=float(predictions[0]),
                confidence=float(confidence[0]),
                timestamp=datetime.now(),
                features_used=list(features.keys()),
                model_version=self.model_version,
                metadata={"task_type": task_type, "agent_id": agent_id}
            )
            
            # Cache the result
            cache_key = f"{task_type}_{agent_id}_{hash(str(context))}"
            self.prediction_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            logger.error(f"Performance prediction failed: {e}")
            return PredictionResult(
                prediction_type=PredictionType.PERFORMANCE,
                predicted_value=0.5,
                confidence=0.1,
                timestamp=datetime.now(),
                features_used=[],
                model_version=self.model_version,
                metadata={"error": str(e)}
            )
    
    async def predict_response_time(self, task_complexity: float, system_load: float) -> PredictionResult:
        """Predict response time based on task complexity and system load"""
        try:
            features = {
                "task_complexity": task_complexity,
                "system_load": system_load,
                "hour_of_day": datetime.now().hour,
                "historical_avg": self._get_historical_average_response_time()
            }
            
            model = self.models[PredictionType.RESPONSE_TIME]
            if not model.is_trained:
                # Estimate based on complexity and load
                estimated_time = task_complexity * (1 + system_load) * 2.0
                return PredictionResult(
                    prediction_type=PredictionType.RESPONSE_TIME,
                    predicted_value=estimated_time,
                    confidence=0.6,
                    timestamp=datetime.now(),
                    features_used=list(features.keys()),
                    model_version=self.model_version,
                    metadata={"estimation_method": "heuristic"}
                )
            
            X = np.array([list(features.values())])
            predictions, confidence = model.predict(X)
            
            return PredictionResult(
                prediction_type=PredictionType.RESPONSE_TIME,
                predicted_value=float(predictions[0]),
                confidence=float(confidence[0]),
                timestamp=datetime.now(),
                features_used=list(features.keys()),
                model_version=self.model_version,
                metadata={"task_complexity": task_complexity, "system_load": system_load}
            )
            
        except Exception as e:
            logger.error(f"Response time prediction failed: {e}")
            return PredictionResult(
                prediction_type=PredictionType.RESPONSE_TIME,
                predicted_value=5.0,  # Default 5 seconds
                confidence=0.1,
                timestamp=datetime.now(),
                features_used=[],
                model_version=self.model_version,
                metadata={"error": str(e)}
            )
    
    async def recommend_optimal_configuration(self, workload: WorkloadProfile) -> Configuration:
        """AI-powered system configuration recommendation"""
        try:
            # Predict resource requirements
            resource_prediction = await self._predict_resource_requirements(workload)
            
            # Calculate optimal agent count
            optimal_agents = max(1, min(workload.concurrent_tasks, 
                                      int(workload.task_complexity * 2)))
            
            # Optimize resource allocation
            total_cpu = resource_prediction.predicted_value
            total_memory = total_cpu * 2  # Heuristic: 2GB per CPU core
            
            resource_allocation = {
                "cpu": total_cpu,
                "memory": total_memory,
                "storage": max(10, workload.concurrent_tasks * 0.5),  # GB
                "network": min(1000, workload.concurrent_tasks * 10)  # Mbps
            }
            
            # Set timeout based on complexity
            timeout_settings = {
                "task_timeout": max(30, workload.task_complexity * 60),
                "connection_timeout": 30,
                "response_timeout": max(10, workload.task_complexity * 10)
            }
            
            # Optimization parameters
            optimization_params = {
                "batch_size": max(1, workload.concurrent_tasks // optimal_agents),
                "retry_attempts": 3 if workload.priority_level > 5 else 1,
                "cache_enabled": workload.task_complexity < 5,
                "parallel_processing": workload.concurrent_tasks > 1
            }
            
            return Configuration(
                agent_count=optimal_agents,
                resource_allocation=resource_allocation,
                timeout_settings=timeout_settings,
                optimization_params=optimization_params
            )
            
        except Exception as e:
            logger.error(f"Configuration recommendation failed: {e}")
            # Return safe default configuration
            return Configuration(
                agent_count=2,
                resource_allocation={"cpu": 2, "memory": 4, "storage": 10, "network": 100},
                timeout_settings={"task_timeout": 300, "connection_timeout": 30, "response_timeout": 60},
                optimization_params={"batch_size": 1, "retry_attempts": 2, "cache_enabled": True, "parallel_processing": False}
            )
    
    async def _predict_resource_requirements(self, workload: WorkloadProfile) -> PredictionResult:
        """Predict resource requirements for a workload"""
        features = {
            "concurrent_tasks": workload.concurrent_tasks,
            "task_complexity": workload.task_complexity,
            "time_constraints": workload.time_constraints,
            "priority_level": workload.priority_level
        }
        
        # Simple heuristic for resource prediction
        base_cpu = workload.concurrent_tasks * 0.5
        complexity_multiplier = 1 + (workload.task_complexity / 10)
        priority_multiplier = 1 + (workload.priority_level / 20)
        
        predicted_cpu = base_cpu * complexity_multiplier * priority_multiplier
        
        return PredictionResult(
            prediction_type=PredictionType.RESOURCE_USAGE,
            predicted_value=predicted_cpu,
            confidence=0.8,
            timestamp=datetime.now(),
            features_used=list(features.keys()),
            model_version=self.model_version,
            metadata={"workload": asdict(workload)}
        )
    
    def _extract_features(self, task_type: str, agent_id: str, context: Dict[str, Any]) -> Dict[str, float]:
        """Extract features for ML prediction"""
        features = {
            "task_type_hash": hash(task_type) % 1000 / 1000.0,  # Normalize hash
            "agent_id_hash": hash(agent_id) % 1000 / 1000.0,
            "hour_of_day": datetime.now().hour / 24.0,
            "day_of_week": datetime.now().weekday() / 7.0,
            "historical_success_rate": self._get_agent_success_rate(agent_id, task_type),
            "avg_response_time": self._get_agent_avg_response_time(agent_id, task_type),
            "recent_load": self._get_recent_system_load(),
            "context_complexity": len(str(context)) / 1000.0  # Rough complexity measure
        }
        
        return features
    
    def _get_agent_success_rate(self, agent_id: str, task_type: str) -> float:
        """Get historical success rate for agent and task type"""
        relevant_metrics = [
            m for m in self.performance_history 
            if m.agent_id == agent_id and m.task_type == task_type
        ]
        
        if not relevant_metrics:
            return 0.75  # Default success rate
        
        return sum(m.success_rate for m in relevant_metrics) / len(relevant_metrics)
    
    def _get_agent_avg_response_time(self, agent_id: str, task_type: str) -> float:
        """Get average response time for agent and task type"""
        relevant_metrics = [
            m for m in self.performance_history 
            if m.agent_id == agent_id and m.task_type == task_type
        ]
        
        if not relevant_metrics:
            return 2.0  # Default response time
        
        return sum(m.avg_response_time for m in relevant_metrics) / len(relevant_metrics)
    
    def _get_recent_system_load(self) -> float:
        """Get recent system load estimate"""
        recent_metrics = [
            m for m in self.performance_history 
            if (datetime.now() - m.timestamp).total_seconds() < 300  # Last 5 minutes
        ]
        
        if not recent_metrics:
            return 0.5  # Default load
        
        return sum(m.resource_usage for m in recent_metrics) / len(recent_metrics)
    
    def _get_historical_average_response_time(self) -> float:
        """Get overall historical average response time"""
        if not self.performance_history:
            return 2.0
        
        return sum(m.avg_response_time for m in self.performance_history) / len(self.performance_history)
    
    async def _retrain_models(self):
        """Retrain ML models with new data"""
        try:
            if len(self.performance_history) < 10:
                return
            
            logger.info("Retraining predictive models...")
            
            # Prepare training data
            X_performance = []
            y_performance = []
            X_response_time = []
            y_response_time = []
            
            for metrics in self.performance_history:
                features = self._extract_features(metrics.task_type, metrics.agent_id, metrics.context)
                feature_vector = list(features.values())
                
                X_performance.append(feature_vector)
                y_performance.append(metrics.success_rate)
                
                X_response_time.append(feature_vector)
                y_response_time.append(metrics.avg_response_time)
            
            # Train models
            if X_performance:
                self.models[PredictionType.PERFORMANCE].fit(
                    np.array(X_performance), np.array(y_performance)
                )
                
                self.models[PredictionType.RESPONSE_TIME].fit(
                    np.array(X_response_time), np.array(y_response_time)
                )
            
            logger.info(f"Models retrained with {len(X_performance)} samples")
            
        except Exception as e:
            logger.error(f"Model retraining failed: {e}")
    
    async def get_prediction_analytics(self) -> Dict[str, Any]:
        """Get analytics about prediction performance"""
        return {
            "total_predictions": len(self.prediction_cache),
            "models_trained": sum(1 for model in self.models.values() if model.is_trained),
            "historical_data_points": len(self.performance_history),
            "model_version": self.model_version,
            "last_training": datetime.now().isoformat(),
            "prediction_types": [pt.value for pt in PredictionType],
            "cache_size": len(self.prediction_cache)
        }

# Global instance
predictive_analytics_engine = PredictiveAnalyticsEngine()