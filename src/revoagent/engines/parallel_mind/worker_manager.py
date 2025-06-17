"""
⚡ Parallel Mind Worker Manager

Auto-scaling worker management system (4-16 workers) with intelligent load balancing.
Implements the complete worker management from the implementation guide.
"""

import asyncio
import time
import psutil
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import uuid
from concurrent.futures import ThreadPoolExecutor
import multiprocessing as mp
import logging

logger = logging.getLogger(__name__)

class WorkerStatus(Enum):
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    STOPPING = "stopping"

@dataclass
class WorkerMetrics:
    """Performance metrics for a worker"""
    tasks_completed: int = 0
    total_processing_time: float = 0.0
    avg_processing_time: float = 0.0
    error_count: int = 0
    last_task_time: Optional[float] = None
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0

@dataclass
class Worker:
    """Individual worker instance"""
    id: str
    status: WorkerStatus = WorkerStatus.IDLE
    current_task: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    metrics: WorkerMetrics = field(default_factory=WorkerMetrics)
    executor: Optional[ThreadPoolExecutor] = None

@dataclass
class Task:
    """Task to be executed by workers"""
    id: str
    function: Callable
    args: tuple
    kwargs: dict
    priority: int = 5  # 1-10, higher = more priority
    created_at: float = field(default_factory=time.time)
    timeout: Optional[float] = None
    retries: int = 0
    max_retries: int = 3

@dataclass
class TaskResult:
    """Result from task execution"""
    task_id: str
    worker_id: str
    result: Any
    execution_time: float
    success: bool
    error: Optional[str] = None
    completed_at: float = field(default_factory=time.time)

class WorkerManager:
    """Manages pool of workers with auto-scaling"""
    
    def __init__(self, min_workers: int = 4, max_workers: int = 16):
        self.min_workers = min_workers
        self.max_workers = max_workers
        self.workers: Dict[str, Worker] = {}
        self.task_queue = asyncio.PriorityQueue()
        self.result_queue = asyncio.Queue()
        self.completed_tasks: Dict[str, TaskResult] = {}
        self.system_load = 0.0
        self.scaling_threshold = 0.8
        self.is_running = False
        
        # Performance tracking
        self.total_tasks_completed = 0
        self.total_processing_time = 0.0
        self.avg_queue_wait_time = 0.0
        
        logger.info(f"⚡ Worker Manager initialized (min: {min_workers}, max: {max_workers})")
        
    async def start(self) -> bool:
        """Start the worker manager"""
        try:
            self.is_running = True
            
            # Create initial workers
            for i in range(self.min_workers):
                await self._create_worker()
            
            # Start management tasks
            asyncio.create_task(self._worker_manager_loop())
            asyncio.create_task(self._auto_scaler_loop())
            asyncio.create_task(self._metrics_collector_loop())
            
            logger.info(f"⚡ WorkerManager started with {len(self.workers)} workers")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start WorkerManager: {e}")
            return False
    
    async def _create_worker(self) -> Worker:
        """Create a new worker"""
        worker_id = f"worker_{uuid.uuid4().hex[:8]}"
        executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix=worker_id)
        
        worker = Worker(
            id=worker_id,
            executor=executor
        )
        
        self.workers[worker_id] = worker
        
        # Start worker task
        asyncio.create_task(self._worker_loop(worker))
        
        logger.info(f"✅ Created worker: {worker_id}")
        return worker
    
    async def _worker_loop(self, worker: Worker):
        """Main loop for individual worker"""
        while self.is_running and worker.id in self.workers:
            try:
                # Get task from queue
                priority, task = await asyncio.wait_for(
                    self.task_queue.get(), timeout=1.0
                )
                
                # Update worker status
                worker.status = WorkerStatus.BUSY
                worker.current_task = task.id
                worker.last_active = time.time()
                
                # Execute task
                result = await self._execute_task(worker, task)
                
                # Store result
                self.completed_tasks[task.id] = result
                await self.result_queue.put(result)
                
                # Update metrics
                worker.metrics.tasks_completed += 1
                worker.metrics.total_processing_time += result.execution_time
                worker.metrics.avg_processing_time = (
                    worker.metrics.total_processing_time / worker.metrics.tasks_completed
                )
                
                # Update global metrics
                self.total_tasks_completed += 1
                self.total_processing_time += result.execution_time
                
                # Reset worker status
                worker.status = WorkerStatus.IDLE
                worker.current_task = None
                
            except asyncio.TimeoutError:
                # No tasks available, continue
                continue
            except Exception as e:
                worker.status = WorkerStatus.ERROR
                worker.metrics.error_count += 1
                logger.error(f"❌ Worker {worker.id} error: {e}")
                await asyncio.sleep(1)  # Brief pause before retry
    
    async def _execute_task(self, worker: Worker, task: Task) -> TaskResult:
        """Execute a task in the worker"""
        start_time = time.time()
        
        try:
            # Execute task with timeout
            if task.timeout:
                result = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        worker.executor, task.function, *task.args, **task.kwargs
                    ),
                    timeout=task.timeout
                )
            else:
                result = await asyncio.get_event_loop().run_in_executor(
                    worker.executor, task.function, *task.args, **task.kwargs
                )
            
            execution_time = time.time() - start_time
            
            return TaskResult(
                task_id=task.id,
                worker_id=worker.id,
                result=result,
                execution_time=execution_time,
                success=True
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            return TaskResult(
                task_id=task.id,
                worker_id=worker.id,
                result=None,
                execution_time=execution_time,
                success=False,
                error=str(e)
            )
    
    async def submit_task(self, function: Callable, *args, priority: int = 5, 
                         timeout: Optional[float] = None, **kwargs) -> str:
        """Submit a task for execution"""
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            function=function,
            args=args,
            kwargs=kwargs,
            priority=priority,
            timeout=timeout
        )
        
        # Add to priority queue (negative priority for max-heap behavior)
        await self.task_queue.put((-priority, task))
        
        return task_id
    
    async def get_task_result(self, task_id: str, timeout: Optional[float] = None) -> TaskResult:
        """Get result for a specific task"""
        # Check if result is already available
        if task_id in self.completed_tasks:
            return self.completed_tasks[task_id]
        
        # Wait for result
        start_time = time.time()
        while timeout is None or (time.time() - start_time) < timeout:
            if task_id in self.completed_tasks:
                return self.completed_tasks[task_id]
            await asyncio.sleep(0.1)
        
        raise TimeoutError(f"Task {task_id} did not complete within {timeout} seconds")
    
    async def _worker_manager_loop(self):
        """Main management loop"""
        while self.is_running:
            try:
                # Clean up completed tasks (keep only recent ones)
                current_time = time.time()
                cutoff_time = current_time - 3600  # 1 hour
                
                tasks_to_remove = [
                    task_id for task_id, result in self.completed_tasks.items()
                    if result.completed_at < cutoff_time
                ]
                
                for task_id in tasks_to_remove:
                    del self.completed_tasks[task_id]
                
                # Check worker health
                for worker in list(self.workers.values()):
                    if worker.status == WorkerStatus.ERROR:
                        if worker.metrics.error_count > 5:
                            await self._remove_worker(worker.id)
                    elif current_time - worker.last_active > 300:  # 5 minutes idle
                        if len(self.workers) > self.min_workers:
                            await self._remove_worker(worker.id)
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"❌ Worker manager loop error: {e}")
                await asyncio.sleep(10)
    
    async def _auto_scaler_loop(self):
        """Auto-scaling based on queue size and system load"""
        while self.is_running:
            try:
                queue_size = self.task_queue.qsize()
                worker_count = len(self.workers)
                busy_workers = sum(1 for w in self.workers.values() 
                                 if w.status == WorkerStatus.BUSY)
                
                # Calculate load
                worker_load = busy_workers / worker_count if worker_count > 0 else 0
                queue_load = min(queue_size / (worker_count * 2), 1.0) if worker_count > 0 else 1.0
                self.system_load = max(worker_load, queue_load)
                
                # Scale up if needed
                if (self.system_load > self.scaling_threshold and 
                    worker_count < self.max_workers):
                    await self._create_worker()
                    logger.info(f"📈 Scaled up to {len(self.workers)} workers (load: {self.system_load:.2f})")
                
                # Scale down if possible
                elif (self.system_load < 0.3 and 
                      worker_count > self.min_workers and 
                      queue_size == 0):
                    idle_workers = [w for w in self.workers.values() 
                                  if w.status == WorkerStatus.IDLE]
                    if idle_workers:
                        await self._remove_worker(idle_workers[0].id)
                        logger.info(f"📉 Scaled down to {len(self.workers)} workers")
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"❌ Auto-scaler error: {e}")
                await asyncio.sleep(30)
    
    async def _metrics_collector_loop(self):
        """Collect system and worker metrics"""
        while self.is_running:
            try:
                # Update worker metrics
                for worker in self.workers.values():
                    if worker.executor:
                        # Simplified metrics (in production, use proper monitoring)
                        try:
                            worker.metrics.memory_usage_mb = psutil.virtual_memory().used / 1024 / 1024
                            worker.metrics.cpu_usage_percent = psutil.cpu_percent()
                        except:
                            pass  # Ignore psutil errors
                
                await asyncio.sleep(60)  # Collect every minute
                
            except Exception as e:
                logger.error(f"❌ Metrics collector error: {e}")
                await asyncio.sleep(60)
    
    async def _remove_worker(self, worker_id: str):
        """Remove a worker"""
        if worker_id not in self.workers:
            return
        
        worker = self.workers[worker_id]
        worker.status = WorkerStatus.STOPPING
        
        # Shutdown executor
        if worker.executor:
            worker.executor.shutdown(wait=False)
        
        # Remove from workers dict
        del self.workers[worker_id]
        logger.info(f"🗑️ Removed worker: {worker_id}")
    
    async def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status"""
        busy_count = sum(1 for w in self.workers.values() if w.status == WorkerStatus.BUSY)
        idle_count = sum(1 for w in self.workers.values() if w.status == WorkerStatus.IDLE)
        error_count = sum(1 for w in self.workers.values() if w.status == WorkerStatus.ERROR)
        
        avg_processing_time = (
            self.total_processing_time / self.total_tasks_completed 
            if self.total_tasks_completed > 0 else 0
        )
        
        return {
            'total_workers': len(self.workers),
            'busy_workers': busy_count,
            'idle_workers': idle_count,
            'error_workers': error_count,
            'queue_size': self.task_queue.qsize(),
            'system_load': self.system_load,
            'total_tasks_completed': self.total_tasks_completed,
            'avg_processing_time': avg_processing_time,
            'scaling_config': {
                'min_workers': self.min_workers,
                'max_workers': self.max_workers,
                'scaling_threshold': self.scaling_threshold
            },
            'performance_metrics': {
                'tasks_per_minute': self._calculate_tasks_per_minute(),
                'worker_utilization': busy_count / len(self.workers) * 100 if self.workers else 0,
                'avg_queue_wait_time': self.avg_queue_wait_time
            }
        }
    
    def _calculate_tasks_per_minute(self) -> float:
        """Calculate tasks per minute"""
        # Simple calculation based on recent performance
        if self.total_tasks_completed > 0 and self.total_processing_time > 0:
            return min(60.0 / (self.total_processing_time / self.total_tasks_completed), 60.0)
        return 0.0
    
    async def shutdown(self):
        """Shutdown all workers"""
        self.is_running = False
        
        for worker_id in list(self.workers.keys()):
            await self._remove_worker(worker_id)
        
        logger.info("🛑 WorkerManager shutdown complete")
