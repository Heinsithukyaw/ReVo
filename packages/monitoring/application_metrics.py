"""
Application Metrics Collector for Phase 4 Comprehensive Monitoring

Collects application-level metrics including custom business metrics,
request tracing, API performance, and user interaction analytics.
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json
import aiofiles
from pathlib import Path
import uuid
from enum import Enum

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Types of application metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"
    RATE = "rate"

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass
class RequestTrace:
    """Request tracing data structure"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    operation_name: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_ms: Optional[float]
    status_code: Optional[int]
    error: Optional[str]
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['start_time'] = self.start_time.isoformat()
        data['end_time'] = self.end_time.isoformat() if self.end_time else None
        return data

@dataclass
class BusinessMetric:
    """Business metric data structure"""
    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['metric_type'] = self.metric_type.value
        data['timestamp'] = self.timestamp.isoformat()
        return data

@dataclass
class APIMetrics:
    """API performance metrics"""
    endpoint: str
    method: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    error_rate: float
    throughput_rps: float
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

class ApplicationMetricsCollector:
    """
    Comprehensive application metrics collector with request tracing,
    business metrics, and performance analytics
    """
    
    def __init__(self,
                 storage_path: str = "monitoring/app_metrics",
                 retention_hours: int = 72,
                 trace_sampling_rate: float = 0.1):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.retention_hours = retention_hours
        self.trace_sampling_rate = trace_sampling_rate
        
        # Metrics storage
        self.business_metrics: List[BusinessMetric] = []
        self.request_traces: Dict[str, RequestTrace] = {}
        self.api_metrics: Dict[str, APIMetrics] = {}
        self.custom_metrics: Dict[str, Any] = defaultdict(list)
        
        # Performance tracking
        self.response_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.request_counts: Dict[str, int] = defaultdict(int)
        self.error_counts: Dict[str, int] = defaultdict(int)
        
        # Alert thresholds
        self.alert_thresholds = {
            'response_time_ms': {'warning': 1000, 'critical': 5000},
            'error_rate': {'warning': 0.05, 'critical': 0.15},
            'throughput_rps': {'warning': 10, 'critical': 5}
        }
        
        # Metric aggregation intervals
        self.aggregation_interval = 60  # seconds
        self.last_aggregation = time.time()
        
        logger.info("ApplicationMetricsCollector initialized")
    
    def start_trace(self, operation_name: str, parent_span_id: Optional[str] = None) -> str:
        """Start a new request trace"""
        trace_id = str(uuid.uuid4())
        span_id = str(uuid.uuid4())
        
        # Apply sampling
        if self.trace_sampling_rate < 1.0:
            import random
            if random.random() > self.trace_sampling_rate:
                return trace_id  # Return trace_id but don't store
        
        trace = RequestTrace(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            operation_name=operation_name,
            start_time=datetime.now(),
            end_time=None,
            duration_ms=None,
            status_code=None,
            error=None
        )
        
        self.request_traces[trace_id] = trace
        logger.debug(f"Started trace {trace_id} for {operation_name}")
        return trace_id
    
    def finish_trace(self, trace_id: str, status_code: Optional[int] = None, error: Optional[str] = None):
        """Finish a request trace"""
        if trace_id not in self.request_traces:
            return
        
        trace = self.request_traces[trace_id]
        trace.end_time = datetime.now()
        trace.duration_ms = (trace.end_time - trace.start_time).total_seconds() * 1000
        trace.status_code = status_code
        trace.error = error
        
        # Update API metrics
        self._update_api_metrics(trace)
        
        logger.debug(f"Finished trace {trace_id} in {trace.duration_ms:.2f}ms")
    
    def add_trace_tag(self, trace_id: str, key: str, value: Any):
        """Add tag to a trace"""
        if trace_id in self.request_traces:
            self.request_traces[trace_id].tags[key] = value
    
    def add_trace_log(self, trace_id: str, message: str, level: str = "info", **kwargs):
        """Add log entry to a trace"""
        if trace_id in self.request_traces:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'level': level,
                'message': message,
                **kwargs
            }
            self.request_traces[trace_id].logs.append(log_entry)
    
    def record_business_metric(self, name: str, value: float, metric_type: MetricType,
                             tags: Optional[Dict[str, str]] = None, description: Optional[str] = None):
        """Record a business metric"""
        metric = BusinessMetric(
            name=name,
            value=value,
            metric_type=metric_type,
            timestamp=datetime.now(),
            tags=tags or {},
            description=description
        )
        
        self.business_metrics.append(metric)
        logger.debug(f"Recorded business metric: {name} = {value}")
    
    def increment_counter(self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None):
        """Increment a counter metric"""
        self.record_business_metric(name, value, MetricType.COUNTER, tags)
    
    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Set a gauge metric"""
        self.record_business_metric(name, value, MetricType.GAUGE, tags)
    
    def record_timer(self, name: str, duration_ms: float, tags: Optional[Dict[str, str]] = None):
        """Record a timer metric"""
        self.record_business_metric(name, duration_ms, MetricType.TIMER, tags)
    
    def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a histogram metric"""
        self.record_business_metric(name, value, MetricType.HISTOGRAM, tags)
    
    def _update_api_metrics(self, trace: RequestTrace):
        """Update API metrics based on completed trace"""
        if not trace.end_time or not trace.duration_ms:
            return
        
        endpoint_key = f"{trace.tags.get('method', 'UNKNOWN')} {trace.tags.get('endpoint', trace.operation_name)}"
        
        # Update response times
        self.response_times[endpoint_key].append(trace.duration_ms)
        
        # Update request counts
        self.request_counts[endpoint_key] += 1
        
        # Update error counts
        if trace.error or (trace.status_code and trace.status_code >= 400):
            self.error_counts[endpoint_key] += 1
    
    async def aggregate_metrics(self):
        """Aggregate metrics for reporting"""
        current_time = time.time()
        if current_time - self.last_aggregation < self.aggregation_interval:
            return
        
        self.last_aggregation = current_time
        
        # Aggregate API metrics
        for endpoint_key in self.response_times.keys():
            response_times = list(self.response_times[endpoint_key])
            if not response_times:
                continue
            
            total_requests = self.request_counts[endpoint_key]
            failed_requests = self.error_counts[endpoint_key]
            successful_requests = total_requests - failed_requests
            
            # Calculate percentiles
            sorted_times = sorted(response_times)
            p95_index = int(len(sorted_times) * 0.95)
            p99_index = int(len(sorted_times) * 0.99)
            
            method, endpoint = endpoint_key.split(' ', 1) if ' ' in endpoint_key else ('UNKNOWN', endpoint_key)
            
            api_metric = APIMetrics(
                endpoint=endpoint,
                method=method,
                total_requests=total_requests,
                successful_requests=successful_requests,
                failed_requests=failed_requests,
                avg_response_time_ms=sum(response_times) / len(response_times),
                min_response_time_ms=min(response_times),
                max_response_time_ms=max(response_times),
                p95_response_time_ms=sorted_times[p95_index] if p95_index < len(sorted_times) else 0,
                p99_response_time_ms=sorted_times[p99_index] if p99_index < len(sorted_times) else 0,
                error_rate=failed_requests / total_requests if total_requests > 0 else 0,
                throughput_rps=total_requests / self.aggregation_interval,
                timestamp=datetime.now()
            )
            
            self.api_metrics[endpoint_key] = api_metric
        
        # Save aggregated metrics
        await self._save_aggregated_metrics()
        
        # Clean old data
        await self._cleanup_old_data()
    
    async def _save_aggregated_metrics(self):
        """Save aggregated metrics to storage"""
        try:
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save API metrics
            if self.api_metrics:
                api_file = self.storage_path / f"api_metrics_{timestamp_str}.json"
                api_data = {key: metrics.to_dict() for key, metrics in self.api_metrics.items()}
                async with aiofiles.open(api_file, 'w') as f:
                    await f.write(json.dumps(api_data, indent=2))
            
            # Save business metrics
            if self.business_metrics:
                business_file = self.storage_path / f"business_metrics_{timestamp_str}.json"
                business_data = [metric.to_dict() for metric in self.business_metrics[-100:]]  # Last 100
                async with aiofiles.open(business_file, 'w') as f:
                    await f.write(json.dumps(business_data, indent=2))
            
            # Save traces
            if self.request_traces:
                traces_file = self.storage_path / f"traces_{timestamp_str}.json"
                traces_data = {tid: trace.to_dict() for tid, trace in list(self.request_traces.items())[-50:]}
                async with aiofiles.open(traces_file, 'w') as f:
                    await f.write(json.dumps(traces_data, indent=2))
            
        except Exception as e:
            logger.error(f"Error saving aggregated metrics: {e}")
    
    async def _cleanup_old_data(self):
        """Clean up old metrics data"""
        cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)
        
        # Clean business metrics
        self.business_metrics = [
            m for m in self.business_metrics
            if m.timestamp > cutoff_time
        ]
        
        # Clean traces
        old_trace_ids = [
            tid for tid, trace in self.request_traces.items()
            if trace.start_time < cutoff_time
        ]
        for tid in old_trace_ids:
            del self.request_traces[tid]
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of application metrics"""
        return {
            "business_metrics_count": len(self.business_metrics),
            "active_traces_count": len(self.request_traces),
            "api_endpoints_count": len(self.api_metrics),
            "trace_sampling_rate": self.trace_sampling_rate,
            "retention_hours": self.retention_hours,
            "aggregation_interval": self.aggregation_interval,
            "recent_api_metrics": {
                key: {
                    "avg_response_time_ms": metrics.avg_response_time_ms,
                    "error_rate": metrics.error_rate,
                    "throughput_rps": metrics.throughput_rps
                }
                for key, metrics in list(self.api_metrics.items())[-5:]
            }
        }
    
    def get_business_metrics(self, name: Optional[str] = None, hours: int = 1) -> List[BusinessMetric]:
        """Get business metrics, optionally filtered by name and time"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        metrics = [m for m in self.business_metrics if m.timestamp > cutoff_time]
        
        if name:
            metrics = [m for m in metrics if m.name == name]
        
        return metrics
    
    def get_api_performance(self, endpoint: Optional[str] = None) -> Dict[str, Any]:
        """Get API performance metrics"""
        if endpoint:
            matching_metrics = {k: v for k, v in self.api_metrics.items() if endpoint in k}
        else:
            matching_metrics = self.api_metrics
        
        if not matching_metrics:
            return {"status": "no_data"}
        
        # Calculate overall performance
        total_requests = sum(m.total_requests for m in matching_metrics.values())
        total_errors = sum(m.failed_requests for m in matching_metrics.values())
        avg_response_time = sum(m.avg_response_time_ms for m in matching_metrics.values()) / len(matching_metrics)
        
        return {
            "total_requests": total_requests,
            "total_errors": total_errors,
            "overall_error_rate": total_errors / total_requests if total_requests > 0 else 0,
            "avg_response_time_ms": avg_response_time,
            "endpoints": {k: v.to_dict() for k, v in matching_metrics.items()}
        }
    
    async def generate_alerts(self) -> List[Dict[str, Any]]:
        """Generate alerts based on current metrics"""
        alerts = []
        
        for endpoint_key, metrics in self.api_metrics.items():
            # Response time alerts
            if metrics.avg_response_time_ms > self.alert_thresholds['response_time_ms']['critical']:
                alerts.append({
                    "severity": AlertSeverity.CRITICAL.value,
                    "type": "response_time",
                    "endpoint": endpoint_key,
                    "value": metrics.avg_response_time_ms,
                    "threshold": self.alert_thresholds['response_time_ms']['critical'],
                    "message": f"Critical response time for {endpoint_key}: {metrics.avg_response_time_ms:.1f}ms"
                })
            elif metrics.avg_response_time_ms > self.alert_thresholds['response_time_ms']['warning']:
                alerts.append({
                    "severity": AlertSeverity.WARNING.value,
                    "type": "response_time",
                    "endpoint": endpoint_key,
                    "value": metrics.avg_response_time_ms,
                    "threshold": self.alert_thresholds['response_time_ms']['warning'],
                    "message": f"High response time for {endpoint_key}: {metrics.avg_response_time_ms:.1f}ms"
                })
            
            # Error rate alerts
            if metrics.error_rate > self.alert_thresholds['error_rate']['critical']:
                alerts.append({
                    "severity": AlertSeverity.CRITICAL.value,
                    "type": "error_rate",
                    "endpoint": endpoint_key,
                    "value": metrics.error_rate,
                    "threshold": self.alert_thresholds['error_rate']['critical'],
                    "message": f"Critical error rate for {endpoint_key}: {metrics.error_rate:.1%}"
                })
            elif metrics.error_rate > self.alert_thresholds['error_rate']['warning']:
                alerts.append({
                    "severity": AlertSeverity.WARNING.value,
                    "type": "error_rate",
                    "endpoint": endpoint_key,
                    "value": metrics.error_rate,
                    "threshold": self.alert_thresholds['error_rate']['warning'],
                    "message": f"High error rate for {endpoint_key}: {metrics.error_rate:.1%}"
                })
            
            # Throughput alerts
            if metrics.throughput_rps < self.alert_thresholds['throughput_rps']['critical']:
                alerts.append({
                    "severity": AlertSeverity.CRITICAL.value,
                    "type": "throughput",
                    "endpoint": endpoint_key,
                    "value": metrics.throughput_rps,
                    "threshold": self.alert_thresholds['throughput_rps']['critical'],
                    "message": f"Critical low throughput for {endpoint_key}: {metrics.throughput_rps:.1f} RPS"
                })
            elif metrics.throughput_rps < self.alert_thresholds['throughput_rps']['warning']:
                alerts.append({
                    "severity": AlertSeverity.WARNING.value,
                    "type": "throughput",
                    "endpoint": endpoint_key,
                    "value": metrics.throughput_rps,
                    "threshold": self.alert_thresholds['throughput_rps']['warning'],
                    "message": f"Low throughput for {endpoint_key}: {metrics.throughput_rps:.1f} RPS"
                })
        
        return alerts

# Context manager for request tracing
class TraceContext:
    """Context manager for request tracing"""
    
    def __init__(self, collector: ApplicationMetricsCollector, operation_name: str, 
                 parent_span_id: Optional[str] = None):
        self.collector = collector
        self.operation_name = operation_name
        self.parent_span_id = parent_span_id
        self.trace_id = None
    
    def __enter__(self):
        self.trace_id = self.collector.start_trace(self.operation_name, self.parent_span_id)
        return self.trace_id
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.trace_id:
            error = str(exc_val) if exc_val else None
            status_code = 500 if exc_val else 200
            self.collector.finish_trace(self.trace_id, status_code, error)

# Global instance
_app_metrics_collector = None

async def get_app_metrics_collector() -> ApplicationMetricsCollector:
    """Get or create global application metrics collector instance"""
    global _app_metrics_collector
    if _app_metrics_collector is None:
        _app_metrics_collector = ApplicationMetricsCollector()
    return _app_metrics_collector