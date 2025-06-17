"""
⚡ Parallel Mind Engine

Task Decomposition and Multi-Worker Processing:
- Task Decomposition: Breaks complex problems into parallel tasks
- Multi-Worker Processing: Specialized workers for different task types
- Intelligent Orchestration: Optimal resource allocation and scheduling
- Result Synthesis: Combines parallel results into cohesive solutions
"""

import asyncio
import logging
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Union
from queue import Queue, PriorityQueue
import threading

logger = logging.getLogger(__name__)

class TaskType(Enum):
    """Types of tasks that can be processed."""
    CODE_GENERATION = "code_generation"
    CODE_ANALYSIS = "code_analysis"
    TESTING = "testing"
    DEBUGGING = "debugging"
    DOCUMENTATION = "documentation"
    DEPLOYMENT = "deployment"
    WEB_AUTOMATION = "web_automation"
    DATA_PROCESSING = "data_processing"

class TaskPriority(Enum):
    """Task priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class Task:
    """Represents a single task in the parallel processing system."""
    id: str
    task_type: TaskType
    priority: TaskPriority
    description: str
    input_data: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    estimated_duration: float = 60.0  # seconds
    max_retries: int = 3
    timeout: float = 300.0  # seconds
    
    # Runtime fields
    status: TaskStatus = TaskStatus.PENDING
    worker_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    retry_count: int = 0
    progress: float = 0.0

@dataclass
class Worker:
    """Represents a worker in the parallel processing system."""
    id: str
    worker_type: TaskType
    max_concurrent_tasks: int
    current_tasks: List[str] = field(default_factory=list)
    total_completed: int = 0
    total_failed: int = 0
    average_duration: float = 0.0
    is_busy: bool = False
    last_activity: Optional[datetime] = None

@dataclass
class WorkflowResult:
    """Result of a complete workflow execution."""
    workflow_id: str
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    total_duration: float
    results: Dict[str, Any]
    errors: List[str]
    performance_metrics: Dict[str, Any]

class ParallelMindEngine:
    """
    ⚡ Parallel Mind Engine
    
    Advanced task decomposition and parallel processing system that breaks down
    complex problems into manageable parallel tasks and orchestrates their execution.
    """
    
    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or min(32, (asyncio.get_event_loop().get_debug() and 4) or 8)
        
        # Task management
        self.tasks: Dict[str, Task] = {}
        self.task_queue = PriorityQueue()
        self.completed_tasks: Dict[str, Task] = {}
        
        # Worker management
        self.workers: Dict[str, Worker] = {}
        self.worker_pools: Dict[TaskType, ThreadPoolExecutor] = {}
        
        # Orchestration
        self.dependency_graph: Dict[str, List[str]] = {}
        self.running_workflows: Dict[str, Dict[str, Any]] = {}
        
        # Performance tracking
        self.performance_metrics = {
            "total_tasks_processed": 0,
            "average_task_duration": 0.0,
            "success_rate": 0.0,
            "parallel_efficiency": 0.0,
            "resource_utilization": 0.0
        }
        
        # Synchronization
        self._lock = threading.Lock()
        self._shutdown = False
        
        # Initialize components
        self._initialize_workers()
        self._start_orchestrator()
        
        logger.info(f"⚡ Parallel Mind Engine initialized with {self.max_workers} workers")
    
    def _initialize_workers(self):
        """Initialize specialized workers for different task types."""
        worker_configs = {
            TaskType.CODE_GENERATION: {"count": 4, "max_concurrent": 2},
            TaskType.CODE_ANALYSIS: {"count": 2, "max_concurrent": 3},
            TaskType.TESTING: {"count": 3, "max_concurrent": 2},
            TaskType.DEBUGGING: {"count": 2, "max_concurrent": 1},
            TaskType.DOCUMENTATION: {"count": 2, "max_concurrent": 3},
            TaskType.DEPLOYMENT: {"count": 1, "max_concurrent": 1},
            TaskType.WEB_AUTOMATION: {"count": 2, "max_concurrent": 2},
            TaskType.DATA_PROCESSING: {"count": 2, "max_concurrent": 2}
        }
        
        for task_type, config in worker_configs.items():
            # Create thread pool for this task type
            self.worker_pools[task_type] = ThreadPoolExecutor(
                max_workers=config["count"],
                thread_name_prefix=f"ParallelMind-{task_type.value}"
            )
            
            # Create worker metadata
            for i in range(config["count"]):
                worker_id = f"{task_type.value}-worker-{i+1}"
                self.workers[worker_id] = Worker(
                    id=worker_id,
                    worker_type=task_type,
                    max_concurrent_tasks=config["max_concurrent"]
                )
        
        logger.info(f"🔧 Initialized {len(self.workers)} specialized workers")
    
    def _start_orchestrator(self):
        """Start the task orchestrator."""
        self.orchestrator_task = asyncio.create_task(self._orchestrator_loop())
        logger.info("🎭 Task orchestrator started")
    
    async def _orchestrator_loop(self):
        """Main orchestrator loop that manages task execution."""
        while not self._shutdown:
            try:
                await self._process_pending_tasks()
                await self._check_completed_tasks()
                await self._update_performance_metrics()
                await asyncio.sleep(0.1)  # Small delay to prevent busy waiting
            except Exception as e:
                logger.error(f"Orchestrator error: {e}")
                await asyncio.sleep(1)
    
    async def _process_pending_tasks(self):
        """Process pending tasks and assign them to available workers."""
        with self._lock:
            # Get tasks ready for execution (dependencies satisfied)
            ready_tasks = []
            
            for task in self.tasks.values():
                if (task.status == TaskStatus.PENDING and 
                    self._are_dependencies_satisfied(task)):
                    ready_tasks.append(task)
            
            # Sort by priority
            ready_tasks.sort(key=lambda t: t.priority.value, reverse=True)
            
            # Assign tasks to available workers
            for task in ready_tasks:
                worker = self._find_available_worker(task.task_type)
                if worker:
                    await self._assign_task_to_worker(task, worker)
    
    def _are_dependencies_satisfied(self, task: Task) -> bool:
        """Check if all task dependencies are satisfied."""
        for dep_id in task.dependencies:
            if dep_id not in self.completed_tasks:
                return False
            if self.completed_tasks[dep_id].status != TaskStatus.COMPLETED:
                return False
        return True
    
    def _find_available_worker(self, task_type: TaskType) -> Optional[Worker]:
        """Find an available worker for the given task type."""
        for worker in self.workers.values():
            if (worker.worker_type == task_type and 
                len(worker.current_tasks) < worker.max_concurrent_tasks):
                return worker
        return None
    
    async def _assign_task_to_worker(self, task: Task, worker: Worker):
        """Assign a task to a worker."""
        task.status = TaskStatus.RUNNING
        task.worker_id = worker.id
        task.start_time = datetime.now()
        
        worker.current_tasks.append(task.id)
        worker.is_busy = True
        worker.last_activity = datetime.now()
        
        # Submit task to appropriate thread pool
        future = self.worker_pools[task.task_type].submit(
            self._execute_task, task
        )
        
        # Store future for tracking
        task.future = future
        
        logger.info(f"⚡ Assigned task {task.id} to worker {worker.id}")
    
    def _execute_task(self, task: Task) -> Any:
        """Execute a single task."""
        try:
            # Get the appropriate task executor
            executor = self._get_task_executor(task.task_type)
            
            # Execute the task
            result = executor(task)
            
            # Update task status
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.end_time = datetime.now()
            task.progress = 100.0
            
            return result
            
        except Exception as e:
            logger.error(f"Task {task.id} failed: {e}")
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.end_time = datetime.now()
            
            # Retry logic
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.PENDING
                logger.info(f"Retrying task {task.id} (attempt {task.retry_count})")
            
            return None
    
    def _get_task_executor(self, task_type: TaskType) -> Callable:
        """Get the appropriate executor function for a task type."""
        executors = {
            TaskType.CODE_GENERATION: self._execute_code_generation,
            TaskType.CODE_ANALYSIS: self._execute_code_analysis,
            TaskType.TESTING: self._execute_testing,
            TaskType.DEBUGGING: self._execute_debugging,
            TaskType.DOCUMENTATION: self._execute_documentation,
            TaskType.DEPLOYMENT: self._execute_deployment,
            TaskType.WEB_AUTOMATION: self._execute_web_automation,
            TaskType.DATA_PROCESSING: self._execute_data_processing
        }
        
        return executors.get(task_type, self._execute_generic_task)
    
    def _execute_code_generation(self, task: Task) -> Dict[str, Any]:
        """Execute code generation task."""
        # Simulate code generation
        time.sleep(2)  # Simulate processing time
        
        return {
            "generated_code": f"# Generated code for: {task.description}\nprint('Hello, World!')",
            "language": task.input_data.get("language", "python"),
            "framework": task.input_data.get("framework", "generic"),
            "quality_score": 0.95
        }
    
    def _execute_code_analysis(self, task: Task) -> Dict[str, Any]:
        """Execute code analysis task."""
        time.sleep(1)
        
        return {
            "analysis_results": {
                "complexity": "medium",
                "maintainability": "high",
                "security_score": 0.9,
                "performance_score": 0.85
            },
            "suggestions": ["Add error handling", "Optimize loops"],
            "issues_found": 2
        }
    
    def _execute_testing(self, task: Task) -> Dict[str, Any]:
        """Execute testing task."""
        time.sleep(1.5)
        
        return {
            "test_results": {
                "total_tests": 25,
                "passed": 23,
                "failed": 2,
                "coverage": 0.92
            },
            "test_files_generated": ["test_main.py", "test_utils.py"],
            "execution_time": 1.5
        }
    
    def _execute_debugging(self, task: Task) -> Dict[str, Any]:
        """Execute debugging task."""
        time.sleep(3)
        
        return {
            "bugs_found": 3,
            "bugs_fixed": 2,
            "fixes_applied": [
                "Fixed null pointer exception in line 42",
                "Corrected logic error in validation function"
            ],
            "remaining_issues": ["Performance bottleneck in data processing"]
        }
    
    def _execute_documentation(self, task: Task) -> Dict[str, Any]:
        """Execute documentation task."""
        time.sleep(1)
        
        return {
            "documentation_generated": {
                "api_docs": "Generated API documentation",
                "user_guide": "Generated user guide",
                "code_comments": "Added inline comments"
            },
            "pages_generated": 5,
            "format": "markdown"
        }
    
    def _execute_deployment(self, task: Task) -> Dict[str, Any]:
        """Execute deployment task."""
        time.sleep(4)
        
        return {
            "deployment_status": "success",
            "environment": task.input_data.get("environment", "production"),
            "containers_deployed": 3,
            "services_started": ["api", "web", "database"],
            "health_check": "passed"
        }
    
    def _execute_web_automation(self, task: Task) -> Dict[str, Any]:
        """Execute web automation task."""
        time.sleep(2)
        
        return {
            "automation_results": {
                "pages_processed": 10,
                "data_extracted": 150,
                "forms_submitted": 5,
                "screenshots_taken": 3
            },
            "success_rate": 0.95,
            "execution_time": 2.0
        }
    
    def _execute_data_processing(self, task: Task) -> Dict[str, Any]:
        """Execute data processing task."""
        time.sleep(2.5)
        
        return {
            "processing_results": {
                "records_processed": 10000,
                "data_cleaned": True,
                "transformations_applied": 5,
                "output_format": "json"
            },
            "processing_time": 2.5,
            "data_quality_score": 0.98
        }
    
    def _execute_generic_task(self, task: Task) -> Dict[str, Any]:
        """Execute generic task."""
        time.sleep(1)
        
        return {
            "task_completed": True,
            "description": task.description,
            "execution_time": 1.0
        }
    
    async def _check_completed_tasks(self):
        """Check for completed tasks and update worker status."""
        with self._lock:
            completed_task_ids = []
            
            for task in self.tasks.values():
                if (task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED] and 
                    hasattr(task, 'future') and task.future.done()):
                    
                    # Update worker status
                    if task.worker_id:
                        worker = self.workers.get(task.worker_id)
                        if worker and task.id in worker.current_tasks:
                            worker.current_tasks.remove(task.id)
                            worker.is_busy = len(worker.current_tasks) > 0
                            
                            if task.status == TaskStatus.COMPLETED:
                                worker.total_completed += 1
                            else:
                                worker.total_failed += 1
                    
                    # Move to completed tasks
                    self.completed_tasks[task.id] = task
                    completed_task_ids.append(task.id)
            
            # Remove from active tasks
            for task_id in completed_task_ids:
                del self.tasks[task_id]
    
    async def _update_performance_metrics(self):
        """Update performance metrics."""
        total_tasks = len(self.completed_tasks)
        if total_tasks == 0:
            return
        
        # Calculate metrics
        total_duration = 0
        successful_tasks = 0
        
        for task in self.completed_tasks.values():
            if task.start_time and task.end_time:
                duration = (task.end_time - task.start_time).total_seconds()
                total_duration += duration
                
                if task.status == TaskStatus.COMPLETED:
                    successful_tasks += 1
        
        self.performance_metrics.update({
            "total_tasks_processed": total_tasks,
            "average_task_duration": total_duration / total_tasks if total_tasks > 0 else 0,
            "success_rate": successful_tasks / total_tasks if total_tasks > 0 else 0,
            "parallel_efficiency": self._calculate_parallel_efficiency(),
            "resource_utilization": self._calculate_resource_utilization()
        })
    
    def _calculate_parallel_efficiency(self) -> float:
        """Calculate parallel processing efficiency."""
        active_workers = sum(1 for w in self.workers.values() if w.is_busy)
        total_workers = len(self.workers)
        return active_workers / total_workers if total_workers > 0 else 0
    
    def _calculate_resource_utilization(self) -> float:
        """Calculate overall resource utilization."""
        total_capacity = sum(w.max_concurrent_tasks for w in self.workers.values())
        current_load = sum(len(w.current_tasks) for w in self.workers.values())
        return current_load / total_capacity if total_capacity > 0 else 0
    
    async def decompose_complex_task(
        self,
        description: str,
        task_type: TaskType,
        input_data: Dict[str, Any],
        complexity_level: str = "medium"
    ) -> List[Task]:
        """
        Decompose a complex task into smaller parallel tasks.
        
        Args:
            description: Task description
            task_type: Primary task type
            input_data: Input data for the task
            complexity_level: Complexity level (low, medium, high)
            
        Returns:
            List of decomposed tasks
        """
        tasks = []
        
        # Task decomposition strategies based on type
        if task_type == TaskType.CODE_GENERATION:
            tasks = self._decompose_code_generation(description, input_data, complexity_level)
        elif task_type == TaskType.WEB_AUTOMATION:
            tasks = self._decompose_web_automation(description, input_data, complexity_level)
        elif task_type == TaskType.DATA_PROCESSING:
            tasks = self._decompose_data_processing(description, input_data, complexity_level)
        else:
            # Generic decomposition
            tasks = self._decompose_generic_task(description, task_type, input_data, complexity_level)
        
        logger.info(f"🧩 Decomposed complex task into {len(tasks)} parallel tasks")
        return tasks
    
    def _decompose_code_generation(self, description: str, input_data: Dict[str, Any], complexity: str) -> List[Task]:
        """Decompose code generation task."""
        tasks = []
        base_id = str(uuid.uuid4())[:8]
        
        # Architecture planning
        tasks.append(Task(
            id=f"{base_id}-arch",
            task_type=TaskType.CODE_ANALYSIS,
            priority=TaskPriority.HIGH,
            description=f"Architecture planning for: {description}",
            input_data={"phase": "architecture", **input_data},
            estimated_duration=30.0
        ))
        
        # Core code generation
        tasks.append(Task(
            id=f"{base_id}-core",
            task_type=TaskType.CODE_GENERATION,
            priority=TaskPriority.HIGH,
            description=f"Core code generation: {description}",
            input_data={"phase": "core", **input_data},
            dependencies=[f"{base_id}-arch"],
            estimated_duration=120.0
        ))
        
        # Testing
        tasks.append(Task(
            id=f"{base_id}-test",
            task_type=TaskType.TESTING,
            priority=TaskPriority.NORMAL,
            description=f"Generate tests for: {description}",
            input_data={"phase": "testing", **input_data},
            dependencies=[f"{base_id}-core"],
            estimated_duration=60.0
        ))
        
        # Documentation
        tasks.append(Task(
            id=f"{base_id}-docs",
            task_type=TaskType.DOCUMENTATION,
            priority=TaskPriority.NORMAL,
            description=f"Generate documentation for: {description}",
            input_data={"phase": "documentation", **input_data},
            dependencies=[f"{base_id}-core"],
            estimated_duration=45.0
        ))
        
        return tasks
    
    def _decompose_web_automation(self, description: str, input_data: Dict[str, Any], complexity: str) -> List[Task]:
        """Decompose web automation task."""
        tasks = []
        base_id = str(uuid.uuid4())[:8]
        
        # Page analysis
        tasks.append(Task(
            id=f"{base_id}-analyze",
            task_type=TaskType.WEB_AUTOMATION,
            priority=TaskPriority.HIGH,
            description=f"Analyze web pages for: {description}",
            input_data={"phase": "analysis", **input_data},
            estimated_duration=30.0
        ))
        
        # Data extraction
        tasks.append(Task(
            id=f"{base_id}-extract",
            task_type=TaskType.WEB_AUTOMATION,
            priority=TaskPriority.HIGH,
            description=f"Extract data: {description}",
            input_data={"phase": "extraction", **input_data},
            dependencies=[f"{base_id}-analyze"],
            estimated_duration=90.0
        ))
        
        # Data processing
        tasks.append(Task(
            id=f"{base_id}-process",
            task_type=TaskType.DATA_PROCESSING,
            priority=TaskPriority.NORMAL,
            description=f"Process extracted data: {description}",
            input_data={"phase": "processing", **input_data},
            dependencies=[f"{base_id}-extract"],
            estimated_duration=60.0
        ))
        
        return tasks
    
    def _decompose_data_processing(self, description: str, input_data: Dict[str, Any], complexity: str) -> List[Task]:
        """Decompose data processing task."""
        tasks = []
        base_id = str(uuid.uuid4())[:8]
        
        # Data validation
        tasks.append(Task(
            id=f"{base_id}-validate",
            task_type=TaskType.DATA_PROCESSING,
            priority=TaskPriority.HIGH,
            description=f"Validate data for: {description}",
            input_data={"phase": "validation", **input_data},
            estimated_duration=30.0
        ))
        
        # Data transformation
        tasks.append(Task(
            id=f"{base_id}-transform",
            task_type=TaskType.DATA_PROCESSING,
            priority=TaskPriority.HIGH,
            description=f"Transform data: {description}",
            input_data={"phase": "transformation", **input_data},
            dependencies=[f"{base_id}-validate"],
            estimated_duration=90.0
        ))
        
        # Data analysis
        tasks.append(Task(
            id=f"{base_id}-analyze",
            task_type=TaskType.CODE_ANALYSIS,
            priority=TaskPriority.NORMAL,
            description=f"Analyze processed data: {description}",
            input_data={"phase": "analysis", **input_data},
            dependencies=[f"{base_id}-transform"],
            estimated_duration=60.0
        ))
        
        return tasks
    
    def _decompose_generic_task(self, description: str, task_type: TaskType, input_data: Dict[str, Any], complexity: str) -> List[Task]:
        """Generic task decomposition."""
        tasks = []
        base_id = str(uuid.uuid4())[:8]
        
        # Simple decomposition into preparation, execution, and validation
        tasks.append(Task(
            id=f"{base_id}-prep",
            task_type=task_type,
            priority=TaskPriority.NORMAL,
            description=f"Prepare for: {description}",
            input_data={"phase": "preparation", **input_data},
            estimated_duration=30.0
        ))
        
        tasks.append(Task(
            id=f"{base_id}-exec",
            task_type=task_type,
            priority=TaskPriority.HIGH,
            description=f"Execute: {description}",
            input_data={"phase": "execution", **input_data},
            dependencies=[f"{base_id}-prep"],
            estimated_duration=90.0
        ))
        
        tasks.append(Task(
            id=f"{base_id}-validate",
            task_type=task_type,
            priority=TaskPriority.NORMAL,
            description=f"Validate results: {description}",
            input_data={"phase": "validation", **input_data},
            dependencies=[f"{base_id}-exec"],
            estimated_duration=30.0
        ))
        
        return tasks
    
    async def execute_workflow(
        self,
        workflow_id: str,
        tasks: List[Task],
        timeout: float = 600.0
    ) -> WorkflowResult:
        """
        Execute a complete workflow of parallel tasks.
        
        Args:
            workflow_id: Unique workflow identifier
            tasks: List of tasks to execute
            timeout: Maximum execution time in seconds
            
        Returns:
            Workflow execution result
        """
        start_time = datetime.now()
        
        # Add tasks to the system
        for task in tasks:
            self.tasks[task.id] = task
        
        # Track workflow
        self.running_workflows[workflow_id] = {
            "start_time": start_time,
            "task_ids": [task.id for task in tasks],
            "total_tasks": len(tasks)
        }
        
        logger.info(f"🚀 Starting workflow {workflow_id} with {len(tasks)} tasks")
        
        # Wait for completion or timeout
        completed_tasks = 0
        failed_tasks = 0
        results = {}
        errors = []
        
        while True:
            # Check completion status
            completed_count = 0
            failed_count = 0
            
            for task_id in self.running_workflows[workflow_id]["task_ids"]:
                if task_id in self.completed_tasks:
                    task = self.completed_tasks[task_id]
                    if task.status == TaskStatus.COMPLETED:
                        completed_count += 1
                        results[task_id] = task.result
                    elif task.status == TaskStatus.FAILED:
                        failed_count += 1
                        errors.append(f"Task {task_id}: {task.error}")
            
            completed_tasks = completed_count
            failed_tasks = failed_count
            
            # Check if all tasks are done
            if completed_tasks + failed_tasks >= len(tasks):
                break
            
            # Check timeout
            if (datetime.now() - start_time).total_seconds() > timeout:
                logger.warning(f"Workflow {workflow_id} timed out")
                break
            
            await asyncio.sleep(0.5)
        
        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()
        
        # Calculate performance metrics
        performance_metrics = {
            "execution_time": total_duration,
            "parallel_efficiency": completed_tasks / len(tasks) if len(tasks) > 0 else 0,
            "success_rate": completed_tasks / (completed_tasks + failed_tasks) if (completed_tasks + failed_tasks) > 0 else 0,
            "average_task_duration": total_duration / len(tasks) if len(tasks) > 0 else 0
        }
        
        # Clean up workflow tracking
        del self.running_workflows[workflow_id]
        
        result = WorkflowResult(
            workflow_id=workflow_id,
            total_tasks=len(tasks),
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
            total_duration=total_duration,
            results=results,
            errors=errors,
            performance_metrics=performance_metrics
        )
        
        logger.info(f"✅ Workflow {workflow_id} completed: {completed_tasks}/{len(tasks)} tasks successful")
        return result
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get current system status and metrics."""
        active_tasks = len(self.tasks)
        completed_tasks = len(self.completed_tasks)
        
        worker_status = {}
        for worker in self.workers.values():
            worker_status[worker.id] = {
                "type": worker.worker_type.value,
                "current_tasks": len(worker.current_tasks),
                "max_concurrent": worker.max_concurrent_tasks,
                "total_completed": worker.total_completed,
                "total_failed": worker.total_failed,
                "is_busy": worker.is_busy,
                "utilization": len(worker.current_tasks) / worker.max_concurrent_tasks
            }
        
        return {
            "active_tasks": active_tasks,
            "completed_tasks": completed_tasks,
            "running_workflows": len(self.running_workflows),
            "workers": worker_status,
            "performance_metrics": self.performance_metrics,
            "system_health": "optimal" if self.performance_metrics["success_rate"] > 0.9 else "degraded"
        }
    
    async def shutdown(self):
        """Gracefully shutdown the parallel mind engine."""
        logger.info("🛑 Shutting down Parallel Mind Engine...")
        
        self._shutdown = True
        
        # Cancel orchestrator
        if hasattr(self, 'orchestrator_task'):
            self.orchestrator_task.cancel()
        
        # Shutdown worker pools
        for pool in self.worker_pools.values():
            pool.shutdown(wait=True)
        
        logger.info("✅ Parallel Mind Engine shutdown complete")