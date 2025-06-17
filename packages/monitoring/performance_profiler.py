"""
Performance Profiler for Phase 4 Comprehensive Monitoring

Provides detailed performance profiling, bottleneck detection,
memory usage analysis, and optimization recommendations.
"""

import asyncio
import cProfile
import pstats
import tracemalloc
import time
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json
import aiofiles
from pathlib import Path
import functools
import threading
from collections import defaultdict
import gc
import sys

logger = logging.getLogger(__name__)

@dataclass
class ProfileResult:
    """Performance profile result"""
    function_name: str
    filename: str
    line_number: int
    total_time: float
    cumulative_time: float
    call_count: int
    per_call_time: float
    percentage: float

@dataclass
class MemorySnapshot:
    """Memory usage snapshot"""
    timestamp: datetime
    current_mb: float
    peak_mb: float
    traced_mb: float
    top_allocations: List[Dict[str, Any]]
    gc_stats: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

@dataclass
class PerformanceBottleneck:
    """Performance bottleneck detection result"""
    function_name: str
    issue_type: str
    severity: str
    description: str
    recommendation: str
    metrics: Dict[str, Any]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

class PerformanceProfiler:
    """
    Comprehensive performance profiler with memory tracking,
    bottleneck detection, and optimization recommendations
    """
    
    def __init__(self,
                 storage_path: str = "monitoring/performance",
                 profile_interval: float = 300.0,  # 5 minutes
                 memory_tracking: bool = True):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.profile_interval = profile_interval
        self.memory_tracking = memory_tracking
        
        # Profiling state
        self.is_profiling = False
        self.profiler = None
        self.profile_results: List[ProfileResult] = []
        self.memory_snapshots: List[MemorySnapshot] = []
        self.bottlenecks: List[PerformanceBottleneck] = []
        
        # Function timing
        self.function_timings: Dict[str, List[float]] = defaultdict(list)
        self.function_call_counts: Dict[str, int] = defaultdict(int)
        
        # Memory tracking
        if self.memory_tracking:
            tracemalloc.start()
        
        # Performance thresholds
        self.thresholds = {
            'slow_function_ms': 100,
            'memory_leak_mb': 50,
            'high_call_count': 1000,
            'cpu_intensive_percent': 5.0
        }
        
        logger.info("PerformanceProfiler initialized")
    
    async def start_profiling(self):
        """Start continuous performance profiling"""
        if self.is_profiling:
            logger.warning("Profiling already running")
            return
        
        self.is_profiling = True
        logger.info("Starting performance profiling")
        
        # Start background profiling task
        asyncio.create_task(self._profiling_loop())
    
    async def stop_profiling(self):
        """Stop performance profiling"""
        self.is_profiling = False
        logger.info("Stopped performance profiling")
    
    async def _profiling_loop(self):
        """Main profiling loop"""
        while self.is_profiling:
            try:
                await self._run_profile_cycle()
                await asyncio.sleep(self.profile_interval)
            except Exception as e:
                logger.error(f"Error in profiling loop: {e}")
                await asyncio.sleep(10)  # Short delay before retry
    
    async def _run_profile_cycle(self):
        """Run a single profiling cycle"""
        logger.debug("Running profile cycle")
        
        # CPU profiling
        await self._profile_cpu_usage()
        
        # Memory profiling
        if self.memory_tracking:
            await self._profile_memory_usage()
        
        # Bottleneck detection
        await self._detect_bottlenecks()
        
        # Save results
        await self._save_profile_results()
        
        # Cleanup old data
        await self._cleanup_old_data()
    
    async def _profile_cpu_usage(self):
        """Profile CPU usage and function performance"""
        try:
            # Create and run profiler
            profiler = cProfile.Profile()
            
            # Profile for a short duration
            start_time = time.time()
            profiler.enable()
            
            # Let it run for a few seconds to collect data
            await asyncio.sleep(5)
            
            profiler.disable()
            end_time = time.time()
            
            # Analyze results
            stats = pstats.Stats(profiler)
            stats.sort_stats('cumulative')
            
            # Extract top functions
            self.profile_results.clear()
            total_time = end_time - start_time
            
            for func_info, (call_count, total_time_func, cumulative_time, callers) in stats.stats.items():
                filename, line_number, function_name = func_info
                
                if total_time_func > 0:  # Only include functions that took time
                    per_call_time = total_time_func / call_count if call_count > 0 else 0
                    percentage = (total_time_func / total_time) * 100 if total_time > 0 else 0
                    
                    result = ProfileResult(
                        function_name=function_name,
                        filename=filename,
                        line_number=line_number,
                        total_time=total_time_func,
                        cumulative_time=cumulative_time,
                        call_count=call_count,
                        per_call_time=per_call_time,
                        percentage=percentage
                    )
                    
                    self.profile_results.append(result)
            
            # Sort by total time
            self.profile_results.sort(key=lambda x: x.total_time, reverse=True)
            self.profile_results = self.profile_results[:50]  # Keep top 50
            
            logger.debug(f"Profiled {len(self.profile_results)} functions")
            
        except Exception as e:
            logger.error(f"Error in CPU profiling: {e}")
    
    async def _profile_memory_usage(self):
        """Profile memory usage and detect leaks"""
        try:
            if not tracemalloc.is_tracing():
                tracemalloc.start()
            
            # Get current memory usage
            current, peak = tracemalloc.get_traced_memory()
            
            # Get top memory allocations
            snapshot = tracemalloc.take_snapshot()
            top_stats = snapshot.statistics('lineno')
            
            top_allocations = []
            for stat in top_stats[:10]:  # Top 10 allocations
                top_allocations.append({
                    'filename': stat.traceback.format()[0] if stat.traceback.format() else 'unknown',
                    'size_mb': stat.size / (1024 * 1024),
                    'count': stat.count
                })
            
            # Get garbage collection stats
            gc_stats = {
                'collections': gc.get_stats(),
                'objects': len(gc.get_objects()),
                'garbage': len(gc.garbage)
            }
            
            # Create memory snapshot
            memory_snapshot = MemorySnapshot(
                timestamp=datetime.now(),
                current_mb=current / (1024 * 1024),
                peak_mb=peak / (1024 * 1024),
                traced_mb=current / (1024 * 1024),
                top_allocations=top_allocations,
                gc_stats=gc_stats
            )
            
            self.memory_snapshots.append(memory_snapshot)
            
            # Keep only recent snapshots
            if len(self.memory_snapshots) > 100:
                self.memory_snapshots = self.memory_snapshots[-100:]
            
            logger.debug(f"Memory snapshot: {current / (1024 * 1024):.1f}MB current, {peak / (1024 * 1024):.1f}MB peak")
            
        except Exception as e:
            logger.error(f"Error in memory profiling: {e}")
    
    async def _detect_bottlenecks(self):
        """Detect performance bottlenecks and generate recommendations"""
        try:
            new_bottlenecks = []
            
            # Analyze CPU bottlenecks
            for result in self.profile_results[:10]:  # Top 10 functions
                if result.percentage > self.thresholds['cpu_intensive_percent']:
                    bottleneck = PerformanceBottleneck(
                        function_name=result.function_name,
                        issue_type="cpu_intensive",
                        severity="warning" if result.percentage < 10 else "critical",
                        description=f"Function {result.function_name} consumes {result.percentage:.1f}% of CPU time",
                        recommendation=self._get_cpu_optimization_recommendation(result),
                        metrics={
                            'cpu_percentage': result.percentage,
                            'total_time': result.total_time,
                            'call_count': result.call_count,
                            'per_call_time': result.per_call_time
                        },
                        timestamp=datetime.now()
                    )
                    new_bottlenecks.append(bottleneck)
                
                if result.call_count > self.thresholds['high_call_count']:
                    bottleneck = PerformanceBottleneck(
                        function_name=result.function_name,
                        issue_type="high_call_frequency",
                        severity="warning",
                        description=f"Function {result.function_name} called {result.call_count} times",
                        recommendation="Consider caching results or reducing call frequency",
                        metrics={
                            'call_count': result.call_count,
                            'per_call_time': result.per_call_time
                        },
                        timestamp=datetime.now()
                    )
                    new_bottlenecks.append(bottleneck)
            
            # Analyze memory bottlenecks
            if self.memory_snapshots:
                latest_snapshot = self.memory_snapshots[-1]
                
                # Check for memory growth
                if len(self.memory_snapshots) > 5:
                    old_snapshot = self.memory_snapshots[-6]
                    memory_growth = latest_snapshot.current_mb - old_snapshot.current_mb
                    
                    if memory_growth > self.thresholds['memory_leak_mb']:
                        bottleneck = PerformanceBottleneck(
                            function_name="memory_system",
                            issue_type="memory_leak",
                            severity="critical" if memory_growth > 100 else "warning",
                            description=f"Memory usage increased by {memory_growth:.1f}MB in recent cycles",
                            recommendation="Investigate memory leaks, check for unclosed resources",
                            metrics={
                                'memory_growth_mb': memory_growth,
                                'current_memory_mb': latest_snapshot.current_mb,
                                'peak_memory_mb': latest_snapshot.peak_mb
                            },
                            timestamp=datetime.now()
                        )
                        new_bottlenecks.append(bottleneck)
                
                # Check for high memory usage
                if latest_snapshot.current_mb > 500:  # 500MB threshold
                    bottleneck = PerformanceBottleneck(
                        function_name="memory_system",
                        issue_type="high_memory_usage",
                        severity="warning" if latest_snapshot.current_mb < 1000 else "critical",
                        description=f"High memory usage: {latest_snapshot.current_mb:.1f}MB",
                        recommendation="Consider memory optimization, garbage collection tuning",
                        metrics={
                            'current_memory_mb': latest_snapshot.current_mb,
                            'peak_memory_mb': latest_snapshot.peak_mb
                        },
                        timestamp=datetime.now()
                    )
                    new_bottlenecks.append(bottleneck)
            
            # Add new bottlenecks
            self.bottlenecks.extend(new_bottlenecks)
            
            # Keep only recent bottlenecks
            cutoff_time = datetime.now() - timedelta(hours=24)
            self.bottlenecks = [b for b in self.bottlenecks if b.timestamp > cutoff_time]
            
            logger.debug(f"Detected {len(new_bottlenecks)} new bottlenecks")
            
        except Exception as e:
            logger.error(f"Error in bottleneck detection: {e}")
    
    def _get_cpu_optimization_recommendation(self, result: ProfileResult) -> str:
        """Get optimization recommendation for CPU-intensive function"""
        recommendations = []
        
        if result.call_count > 1000:
            recommendations.append("Consider caching results to reduce call frequency")
        
        if result.per_call_time > 0.01:  # 10ms per call
            recommendations.append("Optimize algorithm or consider async processing")
        
        if 'loop' in result.function_name.lower():
            recommendations.append("Review loop efficiency and consider vectorization")
        
        if 'database' in result.function_name.lower() or 'query' in result.function_name.lower():
            recommendations.append("Optimize database queries and consider connection pooling")
        
        if not recommendations:
            recommendations.append("Profile function internals for optimization opportunities")
        
        return "; ".join(recommendations)
    
    async def _save_profile_results(self):
        """Save profiling results to storage"""
        try:
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save CPU profile results
            if self.profile_results:
                cpu_file = self.storage_path / f"cpu_profile_{timestamp_str}.json"
                cpu_data = [asdict(result) for result in self.profile_results]
                async with aiofiles.open(cpu_file, 'w') as f:
                    await f.write(json.dumps(cpu_data, indent=2))
            
            # Save memory snapshots
            if self.memory_snapshots:
                memory_file = self.storage_path / f"memory_profile_{timestamp_str}.json"
                memory_data = [snapshot.to_dict() for snapshot in self.memory_snapshots[-10:]]
                async with aiofiles.open(memory_file, 'w') as f:
                    await f.write(json.dumps(memory_data, indent=2))
            
            # Save bottlenecks
            if self.bottlenecks:
                bottlenecks_file = self.storage_path / f"bottlenecks_{timestamp_str}.json"
                bottlenecks_data = [bottleneck.to_dict() for bottleneck in self.bottlenecks[-20:]]
                async with aiofiles.open(bottlenecks_file, 'w') as f:
                    await f.write(json.dumps(bottlenecks_data, indent=2))
            
        except Exception as e:
            logger.error(f"Error saving profile results: {e}")
    
    async def _cleanup_old_data(self):
        """Clean up old profiling data"""
        try:
            # Keep only recent memory snapshots
            if len(self.memory_snapshots) > 200:
                self.memory_snapshots = self.memory_snapshots[-200:]
            
            # Keep only recent bottlenecks
            cutoff_time = datetime.now() - timedelta(hours=48)
            self.bottlenecks = [b for b in self.bottlenecks if b.timestamp > cutoff_time]
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
    
    def profile_function(self, func: Callable) -> Callable:
        """Decorator to profile individual functions"""
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                end_time = time.time()
                duration = (end_time - start_time) * 1000  # Convert to ms
                
                func_name = f"{func.__module__}.{func.__name__}"
                self.function_timings[func_name].append(duration)
                self.function_call_counts[func_name] += 1
                
                # Keep only recent timings
                if len(self.function_timings[func_name]) > 1000:
                    self.function_timings[func_name] = self.function_timings[func_name][-1000:]
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                end_time = time.time()
                duration = (end_time - start_time) * 1000  # Convert to ms
                
                func_name = f"{func.__module__}.{func.__name__}"
                self.function_timings[func_name].append(duration)
                self.function_call_counts[func_name] += 1
                
                # Keep only recent timings
                if len(self.function_timings[func_name]) > 1000:
                    self.function_timings[func_name] = self.function_timings[func_name][-1000:]
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance profiling summary"""
        summary = {
            "profiling_active": self.is_profiling,
            "profile_interval": self.profile_interval,
            "memory_tracking": self.memory_tracking,
            "cpu_profile_functions": len(self.profile_results),
            "memory_snapshots": len(self.memory_snapshots),
            "detected_bottlenecks": len(self.bottlenecks),
            "function_timings_count": len(self.function_timings)
        }
        
        # Add top CPU consumers
        if self.profile_results:
            summary["top_cpu_consumers"] = [
                {
                    "function": result.function_name,
                    "cpu_percentage": result.percentage,
                    "call_count": result.call_count
                }
                for result in self.profile_results[:5]
            ]
        
        # Add memory info
        if self.memory_snapshots:
            latest_memory = self.memory_snapshots[-1]
            summary["current_memory"] = {
                "current_mb": latest_memory.current_mb,
                "peak_mb": latest_memory.peak_mb,
                "gc_objects": latest_memory.gc_stats.get('objects', 0)
            }
        
        # Add recent bottlenecks
        recent_bottlenecks = [b for b in self.bottlenecks if b.timestamp > datetime.now() - timedelta(hours=1)]
        summary["recent_bottlenecks"] = [
            {
                "function": b.function_name,
                "issue_type": b.issue_type,
                "severity": b.severity,
                "description": b.description
            }
            for b in recent_bottlenecks
        ]
        
        return summary
    
    def get_function_performance(self, function_name: Optional[str] = None) -> Dict[str, Any]:
        """Get performance data for specific function or all functions"""
        if function_name:
            if function_name not in self.function_timings:
                return {"status": "no_data"}
            
            timings = self.function_timings[function_name]
            return {
                "function_name": function_name,
                "call_count": self.function_call_counts[function_name],
                "avg_duration_ms": sum(timings) / len(timings),
                "min_duration_ms": min(timings),
                "max_duration_ms": max(timings),
                "recent_calls": timings[-10:]
            }
        else:
            return {
                func_name: {
                    "call_count": self.function_call_counts[func_name],
                    "avg_duration_ms": sum(timings) / len(timings),
                    "min_duration_ms": min(timings),
                    "max_duration_ms": max(timings)
                }
                for func_name, timings in self.function_timings.items()
                if timings
            }
    
    def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Get optimization recommendations based on profiling data"""
        recommendations = []
        
        # Recent bottlenecks
        recent_bottlenecks = [b for b in self.bottlenecks if b.timestamp > datetime.now() - timedelta(hours=6)]
        for bottleneck in recent_bottlenecks:
            recommendations.append({
                "priority": "high" if bottleneck.severity == "critical" else "medium",
                "category": bottleneck.issue_type,
                "function": bottleneck.function_name,
                "description": bottleneck.description,
                "recommendation": bottleneck.recommendation,
                "metrics": bottleneck.metrics
            })
        
        # Function-specific recommendations
        for func_name, timings in self.function_timings.items():
            if not timings:
                continue
            
            avg_time = sum(timings) / len(timings)
            call_count = self.function_call_counts[func_name]
            
            if avg_time > 100:  # 100ms average
                recommendations.append({
                    "priority": "medium",
                    "category": "slow_function",
                    "function": func_name,
                    "description": f"Function has average execution time of {avg_time:.1f}ms",
                    "recommendation": "Consider optimization or async processing",
                    "metrics": {"avg_time_ms": avg_time, "call_count": call_count}
                })
            
            if call_count > 10000:  # High call frequency
                recommendations.append({
                    "priority": "medium",
                    "category": "high_frequency",
                    "function": func_name,
                    "description": f"Function called {call_count} times",
                    "recommendation": "Consider caching or reducing call frequency",
                    "metrics": {"call_count": call_count, "avg_time_ms": avg_time}
                })
        
        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda x: priority_order.get(x["priority"], 3))
        
        return recommendations[:20]  # Top 20 recommendations

# Global instance
_performance_profiler = None

async def get_performance_profiler() -> PerformanceProfiler:
    """Get or create global performance profiler instance"""
    global _performance_profiler
    if _performance_profiler is None:
        _performance_profiler = PerformanceProfiler()
    return _performance_profiler