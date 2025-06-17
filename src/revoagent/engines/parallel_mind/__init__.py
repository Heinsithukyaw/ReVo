"""
Parallel Mind Engine - Multi-threaded Processing
Target: 4-16 worker auto-scaling with 95% utilization
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import logging

from .worker_manager import WorkerManager, Task, TaskResult, WorkerMetrics
from .task_coordinator import TaskCoordinator, CoordinatedTask, CoordinationResult, TaskType
from .parallel_processor import ParallelProcessor, ProcessingResult

logger = logging.getLogger(__name__)

@dataclass
class EngineStatus:
    """Parallel Mind Engine status"""
    status: str
    total_workers: int
    busy_workers: int
    idle_workers: int
    queue_size: int
    worker_utilization: float
    avg_task_time: float
    tasks_completed: int
    tasks_failed: int
    last_activity: Optional[datetime]

class ParallelMindEngine:
    """
    Parallel Mind Engine - Multi-threaded problem solving and parallel processing
    
    Capabilities:
    - Auto-scaling 4-16 workers based on demand
    - Intelligent task coordination
    - Multiple parallelization strategies
    - Load balancing and optimization
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.min_workers = self.config.get('min_workers', 4)
        self.max_workers = self.config.get('max_workers', 16)
        self.scaling_threshold = self.config.get('scaling_threshold', 0.8)
        
        # Initialize components
        self.worker_manager = WorkerManager(
            task_executor=self._default_task_executor,
            min_workers=self.min_workers,
            max_workers=self.max_workers
        )
        self.task_coordinator = TaskCoordinator(self.worker_manager)
        self.parallel_processor = ParallelProcessor(self.worker_manager, self.task_coordinator)
        
        self.is_initialized = False
        self.start_time = datetime.now()
        self.custom_executors: Dict[str, Callable] = {}
        
    async def initialize(self) -> bool:
        """Initialize the Parallel Mind Engine"""
        try:
            # Initialize components
            worker_init = await self.worker_manager.initialize()
            coordinator_init = await self.task_coordinator.initialize()
            processor_init = await self.parallel_processor.initialize()
            
            if worker_init and coordinator_init and processor_init:
                self.is_initialized = True
                logger.info("🟣 Parallel Mind Engine: Fully initialized")
                return True
            else:
                logger.error("🟣 Parallel Mind Engine: Failed to initialize components")
                return False
                
        except Exception as e:
            logger.error(f"🟣 Parallel Mind Engine initialization error: {e}")
            return False
    
    async def execute_parallel_task(self, task_type: str, data: Dict[str, Any],
                                  strategy: str = 'parallel',
                                  max_workers: Optional[int] = None,
                                  timeout: float = 60.0,
                                  priority: int = 1) -> TaskResult:
        """
        Execute a single task with parallel processing capabilities
        """
        if not self.is_initialized:
            raise RuntimeError("Engine not initialized")
        
        try:
            task = Task(
                task_id=f"parallel_{int(time.time() * 1000)}",
                task_type=task_type,
                data=data,
                priority=priority,
                timeout=timeout
            )
            
            result = await self.worker_manager.execute_task_sync(task)
            logger.debug(f"🟣 Executed parallel task {task.task_id}")
            return result
            
        except Exception as e:
            logger.error(f"🟣 Error executing parallel task: {e}")
            raise
    
    async def coordinate_complex_task(self, task_type: TaskType, data: Dict[str, Any],
                                    strategy: Optional[str] = None,
                                    dependencies: Optional[List[str]] = None,
                                    timeout: float = 120.0,
                                    priority: int = 1) -> CoordinationResult:
        """
        Coordinate complex multi-worker tasks
        """
        if not self.is_initialized:
            raise RuntimeError("Engine not initialized")
        
        try:
            task_id = await self.task_coordinator.submit_coordinated_task(
                task_type=task_type,
                data=data,
                strategy=strategy,
                dependencies=dependencies,
                priority=priority,
                timeout=timeout
            )
            
            result = await self.task_coordinator.get_coordination_result(task_id, timeout)
            
            if result is None:
                raise TimeoutError(f"Coordinated task {task_id} timed out")
            
            logger.debug(f"🟣 Coordinated complex task {task_id}")
            return result
            
        except Exception as e:
            logger.error(f"🟣 Error coordinating complex task: {e}")
            raise
    
    async def process_parallel_data(self, processing_type: str, data: Dict[str, Any],
                                  strategy: str = 'data_parallel',
                                  max_workers: Optional[int] = None,
                                  timeout: float = 120.0) -> ProcessingResult:
        """
        Process data using parallel processing strategies
        """
        if not self.is_initialized:
            raise RuntimeError("Engine not initialized")
        
        try:
            result = await self.parallel_processor.process_parallel(
                processing_type=processing_type,
                data=data,
                strategy=strategy,
                max_workers=max_workers,
                timeout=timeout
            )
            
            logger.debug(f"🟣 Processed parallel data with strategy {strategy}")
            return result
            
        except Exception as e:
            logger.error(f"🟣 Error processing parallel data: {e}")
            raise
    
    async def analyze_code_parallel(self, code_files: List[str],
                                  analysis_types: List[str] = None) -> ProcessingResult:
        """
        Perform parallel code analysis across multiple files
        """
        if not self.is_initialized:
            raise RuntimeError("Engine not initialized")
        
        try:
            result = await self.parallel_processor.process_code_analysis_parallel(
                code_files=code_files,
                analysis_types=analysis_types
            )
            
            logger.info(f"🟣 Analyzed {len(code_files)} code files in parallel")
            return result
            
        except Exception as e:
            logger.error(f"🟣 Error in parallel code analysis: {e}")
            raise
    
    async def execute_tests_parallel(self, test_suites: List[Dict[str, Any]],
                                   test_types: List[str] = None) -> ProcessingResult:
        """
        Execute tests in parallel across multiple test suites
        """
        if not self.is_initialized:
            raise RuntimeError("Engine not initialized")
        
        try:
            result = await self.parallel_processor.process_testing_parallel(
                test_suites=test_suites,
                test_types=test_types
            )
            
            logger.info(f"🟣 Executed {len(test_suites)} test suites in parallel")
            return result
            
        except Exception as e:
            logger.error(f"🟣 Error in parallel test execution: {e}")
            raise
    
    async def debug_parallel(self, error_data: Dict[str, Any],
                           debugging_strategies: List[str] = None) -> CoordinationResult:
        """
        Perform parallel debugging using multiple strategies
        """
        if not self.is_initialized:
            raise RuntimeError("Engine not initialized")
        
        try:
            if debugging_strategies is None:
                debugging_strategies = ['static_analysis', 'dynamic_analysis', 'log_analysis']
            
            data = {
                'error_data': error_data,
                'debugging_strategies': debugging_strategies,
                'parallel_debugging': True
            }
            
            result = await self.coordinate_complex_task(
                task_type=TaskType.DEBUGGING,
                data=data,
                strategy='parallel'
            )
            
            logger.info(f"🟣 Performed parallel debugging with {len(debugging_strategies)} strategies")
            return result
            
        except Exception as e:
            logger.error(f"🟣 Error in parallel debugging: {e}")
            raise
    
    async def optimize_parallel(self, optimization_targets: List[Dict[str, Any]],
                              algorithms: List[str] = None) -> ProcessingResult:
        """
        Perform parallel optimization using multiple algorithms
        """
        if not self.is_initialized:
            raise RuntimeError("Engine not initialized")
        
        try:
            result = await self.parallel_processor.process_optimization_parallel(
                optimization_targets=optimization_targets,
                algorithms=algorithms or ['genetic', 'simulated_annealing', 'gradient_descent']
            )
            
            logger.info(f"🟣 Optimized {len(optimization_targets)} targets in parallel")
            return result
            
        except Exception as e:
            logger.error(f"🟣 Error in parallel optimization: {e}")
            raise
    
    async def scale_workers(self, target_count: int) -> bool:
        """
        Manually scale workers to target count
        """
        if not self.is_initialized:
            raise RuntimeError("Engine not initialized")
        
        try:
            success = await self.worker_manager.scale_workers(target_count)
            
            if success:
                logger.info(f"🟣 Scaled workers to {target_count}")
            else:
                logger.warning(f"🟣 Failed to scale workers to {target_count}")
            
            return success
            
        except Exception as e:
            logger.error(f"🟣 Error scaling workers: {e}")
            return False
    
    async def get_engine_status(self) -> EngineStatus:
        """
        Get comprehensive engine status
        """
        try:
            # Get worker manager stats
            manager_stats = await self.worker_manager.get_manager_stats()
            
            # Get worker metrics
            worker_metrics = await self.worker_manager.get_worker_metrics()
            
            # Calculate aggregated metrics
            total_tasks = manager_stats.get('total_tasks_processed', 0)
            completed_tasks = manager_stats.get('tasks_completed', 0)
            failed_tasks = manager_stats.get('tasks_failed', 0)
            
            avg_task_time = 0.0
            if worker_metrics:
                task_times = [m.avg_task_time for m in worker_metrics if m.avg_task_time > 0]
                if task_times:
                    avg_task_time = sum(task_times) / len(task_times)
            
            status = EngineStatus(
                status='active' if self.is_initialized else 'inactive',
                total_workers=manager_stats.get('total_workers', 0),
                busy_workers=manager_stats.get('busy_workers', 0),
                idle_workers=manager_stats.get('idle_workers', 0),
                queue_size=manager_stats.get('queue_size', 0),
                worker_utilization=manager_stats.get('worker_utilization', 0),
                avg_task_time=avg_task_time,
                tasks_completed=completed_tasks,
                tasks_failed=failed_tasks,
                last_activity=datetime.now()
            )
            
            return status
            
        except Exception as e:
            logger.error(f"🟣 Error getting engine status: {e}")
            return EngineStatus(
                status='error',
                total_workers=0,
                busy_workers=0,
                idle_workers=0,
                queue_size=0,
                worker_utilization=0,
                avg_task_time=0,
                tasks_completed=0,
                tasks_failed=0,
                last_activity=None
            )
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get detailed performance metrics
        """
        try:
            # Get stats from all components
            manager_stats = await self.worker_manager.get_manager_stats()
            coordination_stats = await self.task_coordinator.get_coordination_stats()
            processing_stats = await self.parallel_processor.get_processing_stats()
            
            # Combine metrics
            metrics = {
                'engine_uptime_seconds': (datetime.now() - self.start_time).total_seconds(),
                'worker_management': manager_stats,
                'task_coordination': coordination_stats,
                'parallel_processing': processing_stats,
                'overall_performance': {
                    'total_operations': (
                        manager_stats.get('total_tasks_processed', 0) +
                        coordination_stats.get('total_tasks', 0) +
                        processing_stats.get('total_requests', 0)
                    ),
                    'success_rate': self._calculate_overall_success_rate(
                        manager_stats, coordination_stats, processing_stats
                    ),
                    'avg_response_time': self._calculate_avg_response_time(
                        manager_stats, coordination_stats, processing_stats
                    )
                }
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"🟣 Error getting performance metrics: {e}")
            return {}
    
    def register_custom_executor(self, task_type: str, executor: Callable) -> None:
        """
        Register a custom task executor for specific task types
        """
        self.custom_executors[task_type] = executor
        logger.info(f"🟣 Registered custom executor for task type: {task_type}")
    
    async def _default_task_executor(self, task: Task) -> Any:
        """
        Default task executor - can be overridden for specific task types
        """
        try:
            # Check for custom executor
            if task.task_type in self.custom_executors:
                return await self.custom_executors[task.task_type](task)
            
            # Default execution based on task type
            if task.task_type == "code_analysis":
                return await self._execute_code_analysis(task)
            elif task.task_type == "testing":
                return await self._execute_testing(task)
            elif task.task_type == "debugging":
                return await self._execute_debugging(task)
            elif task.task_type == "optimization":
                return await self._execute_optimization(task)
            else:
                # Generic task execution
                return await self._execute_generic_task(task)
                
        except Exception as e:
            logger.error(f"🟣 Error in task executor: {e}")
            raise
    
    async def _execute_code_analysis(self, task: Task) -> Dict[str, Any]:
        """Execute code analysis task"""
        # Simulate code analysis
        await asyncio.sleep(0.1)  # Simulate processing time
        
        code = task.data.get('code', '')
        analysis_type = task.data.get('analysis_type', 'quality')
        
        # Mock analysis results
        result = {
            'analysis_type': analysis_type,
            'code_length': len(code),
            'issues_found': len(code) // 100,  # Mock: 1 issue per 100 chars
            'quality_score': max(0.5, 1.0 - (len(code) // 1000) * 0.1),  # Mock quality score
            'suggestions': ['Improve variable naming', 'Add error handling'],
            'file_index': task.data.get('file_index', 0)
        }
        
        return result
    
    async def _execute_testing(self, task: Task) -> Dict[str, Any]:
        """Execute testing task"""
        # Simulate test execution
        await asyncio.sleep(0.2)  # Simulate test execution time
        
        test_suite = task.data.get('test_suite', {})
        
        # Mock test results
        total_tests = test_suite.get('test_count', 10)
        passed_tests = int(total_tests * 0.9)  # 90% pass rate
        
        result = {
            'test_suite_name': test_suite.get('name', 'unknown'),
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'execution_time': 0.2,
            'suite_index': task.data.get('suite_index', 0)
        }
        
        return result
    
    async def _execute_debugging(self, task: Task) -> Dict[str, Any]:
        """Execute debugging task"""
        # Simulate debugging
        await asyncio.sleep(0.3)  # Simulate debugging time
        
        error_data = task.data.get('error_data', {})
        debugging_step = task.data.get('debugging_step', 'analyze')
        
        # Mock debugging results
        result = {
            'debugging_step': debugging_step,
            'step_completed': True,
            'findings': [f'Found issue in {debugging_step}'],
            'recommendations': [f'Fix {debugging_step} issue'],
            'issue_resolved': debugging_step == 'fix',
            'step_index': task.data.get('step_index', 0)
        }
        
        return result
    
    async def _execute_optimization(self, task: Task) -> Dict[str, Any]:
        """Execute optimization task"""
        # Simulate optimization
        await asyncio.sleep(0.5)  # Simulate optimization time
        
        target = task.data.get('optimization_target', {})
        algorithm = task.data.get('algorithm', 'genetic')
        
        # Mock optimization results
        result = {
            'algorithm': algorithm,
            'optimization_target': target.get('name', 'unknown'),
            'improvement': 0.15,  # 15% improvement
            'iterations': 100,
            'converged': True
        }
        
        return result
    
    async def _execute_generic_task(self, task: Task) -> Dict[str, Any]:
        """Execute generic task"""
        # Simulate generic processing
        await asyncio.sleep(0.1)
        
        return {
            'task_type': task.task_type,
            'processed': True,
            'data_size': len(str(task.data)),
            'processing_time': 0.1
        }
    
    def _calculate_overall_success_rate(self, manager_stats: Dict, 
                                      coordination_stats: Dict, 
                                      processing_stats: Dict) -> float:
        """Calculate overall success rate across all components"""
        try:
            total_operations = 0
            successful_operations = 0
            
            # Manager stats
            manager_total = manager_stats.get('total_tasks_processed', 0)
            manager_success = manager_stats.get('tasks_completed', 0)
            total_operations += manager_total
            successful_operations += manager_success
            
            # Coordination stats
            coord_total = coordination_stats.get('total_tasks', 0)
            coord_success = coordination_stats.get('successful_tasks', 0)
            total_operations += coord_total
            successful_operations += coord_success
            
            # Processing stats
            proc_total = processing_stats.get('total_requests', 0)
            proc_success = processing_stats.get('successful_requests', 0)
            total_operations += proc_total
            successful_operations += proc_success
            
            if total_operations == 0:
                return 0.0
            
            return (successful_operations / total_operations) * 100
            
        except Exception as e:
            logger.error(f"🟣 Error calculating success rate: {e}")
            return 0.0
    
    def _calculate_avg_response_time(self, manager_stats: Dict, 
                                   coordination_stats: Dict, 
                                   processing_stats: Dict) -> float:
        """Calculate average response time across all components"""
        try:
            response_times = []
            
            # Manager stats
            if manager_stats.get('avg_task_time'):
                response_times.append(manager_stats['avg_task_time'])
            
            # Coordination stats
            if coordination_stats.get('avg_execution_time'):
                response_times.append(coordination_stats['avg_execution_time'])
            
            # Processing stats
            if processing_stats.get('avg_execution_time'):
                response_times.append(processing_stats['avg_execution_time'])
            
            if not response_times:
                return 0.0
            
            return sum(response_times) / len(response_times)
            
        except Exception as e:
            logger.error(f"🟣 Error calculating response time: {e}")
            return 0.0
    
    async def cleanup(self) -> None:
        """
        Cleanup engine resources
        """
        try:
            await self.worker_manager.cleanup()
            await self.task_coordinator.cleanup()
            await self.parallel_processor.cleanup()
            
            self.custom_executors.clear()
            self.is_initialized = False
            
            logger.info("🟣 Parallel Mind Engine: Cleanup completed")
            
        except Exception as e:
            logger.error(f"🟣 Error during cleanup: {e}")

# Export main classes
__all__ = [
    'ParallelMindEngine',
    'WorkerManager', 
    'TaskCoordinator', 
    'ParallelProcessor',
    'Task',
    'TaskResult',
    'CoordinatedTask',
    'CoordinationResult',
    'ProcessingResult',
    'EngineStatus'
]