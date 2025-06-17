"""
📊 Real-Time Engine Monitoring System

Provides live monitoring of all three engines with real-time metrics,
status updates, and performance tracking for the dashboard.
"""

import asyncio
import time
import json
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import psutil
import logging

logger = logging.getLogger(__name__)

class EngineType(Enum):
    PERFECT_RECALL = "perfect_recall"
    PARALLEL_MIND = "parallel_mind"
    CREATIVE = "creative"
    COORDINATOR = "coordinator"

class EngineStatus(Enum):
    ACTIVE = "active"
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"

@dataclass
class EngineMetrics:
    """Real-time metrics for engine performance"""
    # Common metrics
    status: EngineStatus
    uptime_seconds: float
    cpu_usage_percent: float
    memory_usage_mb: float
    requests_per_second: float
    error_rate: float
    last_activity: datetime
    
    # Engine-specific metrics
    engine_specific: Dict[str, Any]

@dataclass
class PerfectRecallMetrics:
    """Perfect Recall Engine specific metrics"""
    retrieval_latency_ms: float
    memory_usage_mb: float
    contexts_stored: int
    cache_hit_rate: float
    sub_100ms_rate: float  # Percentage of retrievals under 100ms
    active_sessions: int

@dataclass
class ParallelMindMetrics:
    """Parallel Mind Engine specific metrics"""
    active_workers: int
    max_workers: int
    queue_length: int
    worker_utilization: float
    tasks_completed: int
    scaling_events: int
    avg_task_duration_ms: float

@dataclass
class CreativeMetrics:
    """Creative Engine specific metrics"""
    solutions_generated: int
    avg_innovation_score: float
    generation_time_ms: float
    creativity_techniques_used: List[str]
    user_satisfaction_score: float
    learning_iterations: int

@dataclass
class CoordinatorMetrics:
    """Engine Coordinator specific metrics"""
    coordination_latency_ms: float
    successful_coordinations: int
    failed_coordinations: int
    engines_online: int
    active_workflows: int
    strategy_distribution: Dict[str, int]

class EngineMonitor:
    """Real-time monitoring system for all engines"""
    
    def __init__(self, engines: Dict[EngineType, Any]):
        self.engines = engines
        self.metrics_history: Dict[EngineType, List[EngineMetrics]] = {
            engine_type: [] for engine_type in EngineType
        }
        self.monitoring_active = False
        self.update_interval = 1.0  # 1 second updates
        self.history_retention = 300  # Keep 5 minutes of history
        
        # Performance thresholds
        self.thresholds = {
            EngineType.PERFECT_RECALL: {
                'retrieval_latency_ms': 100,
                'sub_100ms_rate': 95.0,
                'memory_usage_mb': 4000
            },
            EngineType.PARALLEL_MIND: {
                'worker_utilization': 90.0,
                'queue_length': 50,
                'scaling_response_time': 30
            },
            EngineType.CREATIVE: {
                'generation_time_ms': 30000,
                'innovation_score': 0.6,
                'solution_count': 3
            },
            EngineType.COORDINATOR: {
                'coordination_latency_ms': 5000,
                'success_rate': 80.0
            }
        }
    
    async def start_monitoring(self):
        """Start real-time monitoring of all engines"""
        self.monitoring_active = True
        logger.info("🔄 Starting real-time engine monitoring")
        
        # Start monitoring tasks for each engine
        monitoring_tasks = [
            asyncio.create_task(self._monitor_engine(engine_type))
            for engine_type in EngineType
        ]
        
        # Start cleanup task
        cleanup_task = asyncio.create_task(self._cleanup_old_metrics())
        
        await asyncio.gather(*monitoring_tasks, cleanup_task, return_exceptions=True)
    
    async def stop_monitoring(self):
        """Stop monitoring system"""
        self.monitoring_active = False
        logger.info("🛑 Stopping engine monitoring")
    
    async def _monitor_engine(self, engine_type: EngineType):
        """Monitor a specific engine continuously"""
        while self.monitoring_active:
            try:
                metrics = await self._collect_engine_metrics(engine_type)
                
                # Store metrics
                self.metrics_history[engine_type].append(metrics)
                
                # Limit history size
                if len(self.metrics_history[engine_type]) > self.history_retention:
                    self.metrics_history[engine_type] = self.metrics_history[engine_type][-self.history_retention:]
                
                # Check thresholds and generate alerts
                await self._check_thresholds(engine_type, metrics)
                
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"Error monitoring {engine_type.value}: {e}")
                await asyncio.sleep(self.update_interval * 2)  # Back off on error
    
    async def _collect_engine_metrics(self, engine_type: EngineType) -> EngineMetrics:
        """Collect metrics for a specific engine"""
        engine = self.engines.get(engine_type)
        
        if not engine:
            return EngineMetrics(
                status=EngineStatus.OFFLINE,
                uptime_seconds=0,
                cpu_usage_percent=0,
                memory_usage_mb=0,
                requests_per_second=0,
                error_rate=0,
                last_activity=datetime.now(),
                engine_specific={}
            )
        
        # Collect common metrics
        try:
            # Get engine status
            if hasattr(engine, 'get_engine_status'):
                engine_status = await engine.get_engine_status()
                status = EngineStatus.ACTIVE if engine_status.get('status') == 'active' else EngineStatus.IDLE
            else:
                status = EngineStatus.ACTIVE
            
            # System metrics
            cpu_usage = psutil.cpu_percent(interval=0.1)
            memory_info = psutil.virtual_memory()
            memory_usage_mb = memory_info.used / (1024 * 1024)
            
            # Engine-specific metrics
            engine_specific = await self._collect_engine_specific_metrics(engine_type, engine)
            
            return EngineMetrics(
                status=status,
                uptime_seconds=time.time() - getattr(engine, '_start_time', time.time()),
                cpu_usage_percent=cpu_usage,
                memory_usage_mb=memory_usage_mb,
                requests_per_second=self._calculate_rps(engine_type),
                error_rate=self._calculate_error_rate(engine_type),
                last_activity=datetime.now(),
                engine_specific=engine_specific
            )
            
        except Exception as e:
            logger.error(f"Error collecting metrics for {engine_type.value}: {e}")
            return EngineMetrics(
                status=EngineStatus.ERROR,
                uptime_seconds=0,
                cpu_usage_percent=0,
                memory_usage_mb=0,
                requests_per_second=0,
                error_rate=1.0,
                last_activity=datetime.now(),
                engine_specific={"error": str(e)}
            )
    
    async def _collect_engine_specific_metrics(self, engine_type: EngineType, engine: Any) -> Dict[str, Any]:
        """Collect engine-specific metrics"""
        try:
            if engine_type == EngineType.PERFECT_RECALL:
                return await self._collect_perfect_recall_metrics(engine)
            elif engine_type == EngineType.PARALLEL_MIND:
                return await self._collect_parallel_mind_metrics(engine)
            elif engine_type == EngineType.CREATIVE:
                return await self._collect_creative_metrics(engine)
            elif engine_type == EngineType.COORDINATOR:
                return await self._collect_coordinator_metrics(engine)
            else:
                return {}
        except Exception as e:
            logger.error(f"Error collecting {engine_type.value} specific metrics: {e}")
            return {"error": str(e)}
    
    async def _collect_perfect_recall_metrics(self, engine) -> Dict[str, Any]:
        """Collect Perfect Recall Engine metrics"""
        try:
            # Get engine status
            status = await engine.get_engine_status()
            
            # Calculate sub-100ms rate from recent history
            recent_metrics = self.metrics_history[EngineType.PERFECT_RECALL][-60:]  # Last minute
            sub_100ms_count = 0
            total_retrievals = 0
            
            for metric in recent_metrics:
                if 'retrieval_latency_ms' in metric.engine_specific:
                    total_retrievals += 1
                    if metric.engine_specific['retrieval_latency_ms'] < 100:
                        sub_100ms_count += 1
            
            sub_100ms_rate = (sub_100ms_count / total_retrievals * 100) if total_retrievals > 0 else 100.0
            
            return {
                'retrieval_latency_ms': status.get('avg_retrieval_time_ms', 0),
                'memory_usage_mb': status.get('memory_usage_mb', 0),
                'contexts_stored': status.get('total_contexts', 0),
                'cache_hit_rate': status.get('cache_hit_rate', 0.8),
                'sub_100ms_rate': sub_100ms_rate,
                'active_sessions': status.get('active_sessions', 0)
            }
        except Exception as e:
            return {'error': str(e)}
    
    async def _collect_parallel_mind_metrics(self, engine) -> Dict[str, Any]:
        """Collect Parallel Mind Engine metrics"""
        try:
            if hasattr(engine, 'get_status'):
                status = await engine.get_status()
                return {
                    'active_workers': status.get('total_workers', 0),
                    'max_workers': 16,  # From configuration
                    'queue_length': status.get('queue_size', 0),
                    'worker_utilization': status.get('system_load', 0) * 100,
                    'tasks_completed': status.get('total_tasks_completed', 0),
                    'scaling_events': 0,  # Would track scaling events
                    'avg_task_duration_ms': status.get('avg_processing_time', 0) * 1000
                }
            else:
                return {
                    'active_workers': 4,
                    'max_workers': 16,
                    'queue_length': 0,
                    'worker_utilization': 50.0,
                    'tasks_completed': 0,
                    'scaling_events': 0,
                    'avg_task_duration_ms': 1000
                }
        except Exception as e:
            return {'error': str(e)}
    
    async def _collect_creative_metrics(self, engine) -> Dict[str, Any]:
        """Collect Creative Engine metrics"""
        try:
            status = await engine.get_engine_status()
            return {
                'solutions_generated': status.get('total_solutions_generated', 0),
                'avg_innovation_score': status.get('avg_innovation_score', 0.7),
                'generation_time_ms': status.get('avg_generation_time', 0) * 1000,
                'creativity_techniques_used': ['brainstorming', 'lateral_thinking', 'analogical'],
                'user_satisfaction_score': status.get('user_satisfaction', 0.8),
                'learning_iterations': status.get('learning_iterations', 0)
            }
        except Exception as e:
            return {'error': str(e)}
    
    async def _collect_coordinator_metrics(self, engine) -> Dict[str, Any]:
        """Collect Engine Coordinator metrics"""
        try:
            status = await engine.get_system_status()
            return {
                'coordination_latency_ms': status.get('avg_coordination_time', 0),
                'successful_coordinations': status.get('successful_coordinations', 0),
                'failed_coordinations': status.get('failed_coordinations', 0),
                'engines_online': len([e for e in status.get('engine_statuses', {}).values() 
                                     if e.get('status') == 'active']),
                'active_workflows': status.get('active_workflows', 0),
                'strategy_distribution': status.get('strategy_usage', {})
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _calculate_rps(self, engine_type: EngineType) -> float:
        """Calculate requests per second for an engine"""
        recent_metrics = self.metrics_history[engine_type][-60:]  # Last minute
        if len(recent_metrics) < 2:
            return 0.0
        
        # Simple RPS calculation based on activity
        return len(recent_metrics) / 60.0  # Approximate
    
    def _calculate_error_rate(self, engine_type: EngineType) -> float:
        """Calculate error rate for an engine"""
        recent_metrics = self.metrics_history[engine_type][-60:]  # Last minute
        if not recent_metrics:
            return 0.0
        
        error_count = sum(1 for m in recent_metrics if m.status == EngineStatus.ERROR)
        return error_count / len(recent_metrics)
    
    async def _check_thresholds(self, engine_type: EngineType, metrics: EngineMetrics):
        """Check if metrics exceed thresholds and generate alerts"""
        thresholds = self.thresholds.get(engine_type, {})
        alerts = []
        
        # Check engine-specific thresholds
        for metric_name, threshold in thresholds.items():
            if metric_name in metrics.engine_specific:
                value = metrics.engine_specific[metric_name]
                
                # Different threshold types
                if metric_name.endswith('_rate') and value < threshold:
                    alerts.append(f"{engine_type.value}: {metric_name} below threshold ({value:.1f}% < {threshold}%)")
                elif metric_name.endswith('_ms') and value > threshold:
                    alerts.append(f"{engine_type.value}: {metric_name} above threshold ({value:.1f}ms > {threshold}ms)")
                elif metric_name == 'queue_length' and value > threshold:
                    alerts.append(f"{engine_type.value}: Queue length too high ({value} > {threshold})")
        
        # Log alerts
        for alert in alerts:
            logger.warning(f"🚨 THRESHOLD ALERT: {alert}")
    
    async def _cleanup_old_metrics(self):
        """Cleanup old metrics to prevent memory leaks"""
        while self.monitoring_active:
            try:
                cutoff_time = datetime.now() - timedelta(minutes=5)
                
                for engine_type in EngineType:
                    # Remove metrics older than 5 minutes
                    self.metrics_history[engine_type] = [
                        m for m in self.metrics_history[engine_type]
                        if m.last_activity > cutoff_time
                    ]
                
                await asyncio.sleep(60)  # Cleanup every minute
                
            except Exception as e:
                logger.error(f"Error during metrics cleanup: {e}")
                await asyncio.sleep(60)
    
    def get_current_metrics(self, engine_type: Optional[EngineType] = None) -> Union[EngineMetrics, Dict[EngineType, EngineMetrics]]:
        """Get current metrics for engine(s)"""
        if engine_type:
            history = self.metrics_history.get(engine_type, [])
            return history[-1] if history else None
        else:
            return {
                engine_type: (history[-1] if history else None)
                for engine_type, history in self.metrics_history.items()
            }
    
    def get_metrics_history(self, engine_type: EngineType, minutes: int = 5) -> List[EngineMetrics]:
        """Get metrics history for an engine"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [
            m for m in self.metrics_history.get(engine_type, [])
            if m.last_activity > cutoff_time
        ]
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health summary"""
        current_metrics = self.get_current_metrics()
        
        health_summary = {
            'overall_status': 'healthy',
            'engines_online': 0,
            'engines_total': len(EngineType),
            'alerts': [],
            'performance_summary': {}
        }
        
        for engine_type, metrics in current_metrics.items():
            if metrics:
                if metrics.status in [EngineStatus.ACTIVE, EngineStatus.IDLE, EngineStatus.BUSY]:
                    health_summary['engines_online'] += 1
                
                # Check for performance issues
                if engine_type == EngineType.PERFECT_RECALL:
                    sub_100ms_rate = metrics.engine_specific.get('sub_100ms_rate', 100)
                    if sub_100ms_rate < 95:
                        health_summary['alerts'].append(f"Perfect Recall: {sub_100ms_rate:.1f}% under 100ms (target: 95%)")
                
                elif engine_type == EngineType.PARALLEL_MIND:
                    queue_length = metrics.engine_specific.get('queue_length', 0)
                    if queue_length > 50:
                        health_summary['alerts'].append(f"Parallel Mind: High queue length ({queue_length})")
                
                elif engine_type == EngineType.CREATIVE:
                    innovation_score = metrics.engine_specific.get('avg_innovation_score', 0.8)
                    if innovation_score < 0.6:
                        health_summary['alerts'].append(f"Creative Engine: Low innovation score ({innovation_score:.2f})")
        
        # Overall status
        if health_summary['engines_online'] < health_summary['engines_total']:
            health_summary['overall_status'] = 'degraded'
        if health_summary['alerts']:
            health_summary['overall_status'] = 'warning'
        if health_summary['engines_online'] == 0:
            health_summary['overall_status'] = 'critical'
        
        return health_summary
    
    def export_metrics_json(self, engine_type: Optional[EngineType] = None) -> str:
        """Export metrics as JSON for external monitoring"""
        if engine_type:
            data = {
                'engine_type': engine_type.value,
                'current_metrics': asdict(self.get_current_metrics(engine_type)) if self.get_current_metrics(engine_type) else None,
                'history': [asdict(m) for m in self.get_metrics_history(engine_type)]
            }
        else:
            data = {
                'system_health': self.get_system_health(),
                'all_engines': {
                    engine_type.value: {
                        'current_metrics': asdict(metrics) if metrics else None,
                        'history_count': len(self.get_metrics_history(engine_type))
                    }
                    for engine_type, metrics in self.get_current_metrics().items()
                }
            }
        
        return json.dumps(data, default=str, indent=2)