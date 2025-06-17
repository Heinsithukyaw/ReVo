"""
Parallel Mind Engine - Task Coordinator
Multi-threaded processing and intelligent task distribution
"""

import asyncio
import time
import uuid
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

from .worker_manager import WorkerManager, Task, TaskResult

logger = logging.getLogger(__name__)

class TaskType(Enum):
    CODE_ANALYSIS = "code_analysis"
    TESTING = "testing"
    DEBUGGING = "debugging"
    OPTIMIZATION = "optimization"
    PARALLEL_EXECUTION = "parallel_execution"
    DATA_PROCESSING = "data_processing"

class CoordinationStrategy(Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    PIPELINE = "pipeline"
    MAP_REDUCE = "map_reduce"

@dataclass
class CoordinatedTask:
    """High-level task that may involve multiple workers"""
    task_id: str
    task_type: TaskType
    strategy: CoordinationStrategy
    data: Dict[str, Any]
    subtasks: List[Task] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    priority: int = 1
    timeout: float = 60.0
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

@dataclass
class CoordinationResult:
    """Result of coordinated task execution"""
    task_id: str
    success: bool
    results: List[TaskResult]
    aggregated_result: Any
    execution_time: float
    strategy_used: CoordinationStrategy
    workers_used: int
    completed_at: datetime

class TaskCoordinator:
    """
    Intelligent task coordination and distribution
    Manages complex workflows across multiple workers
    """
    
    def __init__(self, worker_manager: WorkerManager):
        self.worker_manager = worker_manager
        self.active_tasks: Dict[str, CoordinatedTask] = {}
        self.completed_tasks: Dict[str, CoordinationResult] = {}
        self.task_dependencies: Dict[str, List[str]] = {}
        self.coordination_strategies: Dict[TaskType, CoordinationStrategy] = {
            TaskType.CODE_ANALYSIS: CoordinationStrategy.PARALLEL,
            TaskType.TESTING: CoordinationStrategy.PARALLEL,
            TaskType.DEBUGGING: CoordinationStrategy.SEQUENTIAL,
            TaskType.OPTIMIZATION: CoordinationStrategy.MAP_REDUCE,
            TaskType.PARALLEL_EXECUTION: CoordinationStrategy.PARALLEL,
            TaskType.DATA_PROCESSING: CoordinationStrategy.PIPELINE
        }
        
    async def initialize(self) -> bool:
        """Initialize task coordinator"""
        try:
            logger.info("🟣 Parallel Mind Engine: Task Coordinator initialized")
            return True
        except Exception as e:
            logger.error(f"🟣 Failed to initialize Task Coordinator: {e}")
            return False
    
    async def coordinate_task(self, coordinated_task: CoordinatedTask) -> CoordinationResult:
        """
        Coordinate execution of a complex task
        """
        start_time = time.time()
        coordinated_task.started_at = datetime.now()
        
        try:
            # Store active task
            self.active_tasks[coordinated_task.task_id] = coordinated_task
            
            # Check dependencies
            await self._wait_for_dependencies(coordinated_task)
            
            # Decompose task into subtasks if needed
            if not coordinated_task.subtasks:
                coordinated_task.subtasks = await self._decompose_task(coordinated_task)
            
            # Execute based on strategy
            if coordinated_task.strategy == CoordinationStrategy.SEQUENTIAL:
                results = await self._execute_sequential(coordinated_task)
            elif coordinated_task.strategy == CoordinationStrategy.PARALLEL:
                results = await self._execute_parallel(coordinated_task)
            elif coordinated_task.strategy == CoordinationStrategy.PIPELINE:
                results = await self._execute_pipeline(coordinated_task)
            elif coordinated_task.strategy == CoordinationStrategy.MAP_REDUCE:
                results = await self._execute_map_reduce(coordinated_task)
            else:
                raise ValueError(f"Unknown coordination strategy: {coordinated_task.strategy}")
            
            # Aggregate results
            aggregated_result = await self._aggregate_results(coordinated_task, results)
            
            execution_time = time.time() - start_time
            coordinated_task.completed_at = datetime.now()
            
            # Create coordination result
            coordination_result = CoordinationResult(
                task_id=coordinated_task.task_id,
                success=all(r.success for r in results),
                results=results,
                aggregated_result=aggregated_result,
                execution_time=execution_time,
                strategy_used=coordinated_task.strategy,
                workers_used=len(set(r.worker_id for r in results)),
                completed_at=coordinated_task.completed_at
            )
            
            # Store completed task
            self.completed_tasks[coordinated_task.task_id] = coordination_result
            
            # Remove from active tasks
            if coordinated_task.task_id in self.active_tasks:
                del self.active_tasks[coordinated_task.task_id]
            
            logger.info(f"🟣 Coordinated task {coordinated_task.task_id} completed in {execution_time:.3f}s")
            return coordination_result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"🟣 Error coordinating task {coordinated_task.task_id}: {e}")
            
            # Create error result
            error_result = CoordinationResult(
                task_id=coordinated_task.task_id,
                success=False,
                results=[],
                aggregated_result=None,
                execution_time=execution_time,
                strategy_used=coordinated_task.strategy,
                workers_used=0,
                completed_at=datetime.now()
            )
            
            self.completed_tasks[coordinated_task.task_id] = error_result
            
            if coordinated_task.task_id in self.active_tasks:
                del self.active_tasks[coordinated_task.task_id]
            
            return error_result
    
    async def submit_coordinated_task(self, task_type: TaskType, data: Dict[str, Any],
                                    strategy: Optional[CoordinationStrategy] = None,
                                    dependencies: Optional[List[str]] = None,
                                    priority: int = 1,
                                    timeout: float = 60.0) -> str:
        """
        Submit a coordinated task for execution
        """
        task_id = f"coord_{uuid.uuid4().hex[:8]}"
        
        # Use default strategy if not specified
        if strategy is None:
            strategy = self.coordination_strategies.get(task_type, CoordinationStrategy.PARALLEL)
        
        coordinated_task = CoordinatedTask(
            task_id=task_id,
            task_type=task_type,
            strategy=strategy,
            data=data,
            dependencies=dependencies or [],
            priority=priority,
            timeout=timeout
        )
        
        # Start coordination in background
        asyncio.create_task(self.coordinate_task(coordinated_task))
        
        logger.debug(f"🟣 Submitted coordinated task {task_id} with strategy {strategy.value}")
        return task_id
    
    async def get_coordination_result(self, task_id: str, timeout: float = 60.0) -> Optional[CoordinationResult]:
        """
        Get result of coordinated task
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if task_id in self.completed_tasks:
                return self.completed_tasks[task_id]
            await asyncio.sleep(0.1)
        
        return None
    
    async def execute_parallel_analysis(self, code_snippets: List[str],
                                      analysis_type: str = "quality") -> CoordinationResult:
        """
        Execute parallel code analysis across multiple workers
        """
        task_data = {
            'code_snippets': code_snippets,
            'analysis_type': analysis_type
        }
        
        task_id = await self.submit_coordinated_task(
            TaskType.CODE_ANALYSIS,
            task_data,
            CoordinationStrategy.PARALLEL
        )
        
        result = await self.get_coordination_result(task_id)
        return result
    
    async def execute_distributed_testing(self, test_suites: List[Dict[str, Any]]) -> CoordinationResult:
        """
        Execute distributed testing across multiple workers
        """
        task_data = {
            'test_suites': test_suites,
            'parallel_execution': True
        }
        
        task_id = await self.submit_coordinated_task(
            TaskType.TESTING,
            task_data,
            CoordinationStrategy.PARALLEL
        )
        
        result = await self.get_coordination_result(task_id)
        return result
    
    async def execute_debugging_workflow(self, error_data: Dict[str, Any]) -> CoordinationResult:
        """
        Execute sequential debugging workflow
        """
        task_data = {
            'error_data': error_data,
            'debugging_steps': ['analyze', 'locate', 'fix', 'verify']
        }
        
        task_id = await self.submit_coordinated_task(
            TaskType.DEBUGGING,
            task_data,
            CoordinationStrategy.SEQUENTIAL
        )
        
        result = await self.get_coordination_result(task_id)
        return result
    
    async def get_coordination_stats(self) -> Dict[str, Any]:
        """
        Get coordination statistics
        """
        try:
            completed_tasks = list(self.completed_tasks.values())
            
            if not completed_tasks:
                return {
                    'total_tasks': 0,
                    'active_tasks': len(self.active_tasks),
                    'success_rate': 0,
                    'avg_execution_time': 0,
                    'strategy_usage': {},
                    'worker_utilization': {}
                }
            
            successful_tasks = [t for t in completed_tasks if t.success]
            
            # Strategy usage statistics
            strategy_usage = {}
            for task in completed_tasks:
                strategy = task.strategy_used.value
                strategy_usage[strategy] = strategy_usage.get(strategy, 0) + 1
            
            # Worker utilization
            worker_usage = {}
            for task in completed_tasks:
                workers_used = task.workers_used
                worker_usage[workers_used] = worker_usage.get(workers_used, 0) + 1
            
            stats = {
                'total_tasks': len(completed_tasks),
                'active_tasks': len(self.active_tasks),
                'successful_tasks': len(successful_tasks),
                'failed_tasks': len(completed_tasks) - len(successful_tasks),
                'success_rate': len(successful_tasks) / len(completed_tasks) * 100,
                'avg_execution_time': sum(t.execution_time for t in completed_tasks) / len(completed_tasks),
                'avg_workers_per_task': sum(t.workers_used for t in completed_tasks) / len(completed_tasks),
                'strategy_usage': strategy_usage,
                'worker_utilization': worker_usage
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"🟣 Error getting coordination stats: {e}")
            return {}
    
    async def _wait_for_dependencies(self, coordinated_task: CoordinatedTask) -> None:
        """
        Wait for task dependencies to complete
        """
        if not coordinated_task.dependencies:
            return
        
        timeout = 30.0  # Maximum wait time for dependencies
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            pending_deps = [
                dep_id for dep_id in coordinated_task.dependencies
                if dep_id not in self.completed_tasks
            ]
            
            if not pending_deps:
                break
            
            await asyncio.sleep(0.5)
        
        # Check if all dependencies completed successfully
        failed_deps = [
            dep_id for dep_id in coordinated_task.dependencies
            if dep_id in self.completed_tasks and not self.completed_tasks[dep_id].success
        ]
        
        if failed_deps:
            raise RuntimeError(f"Dependencies failed: {failed_deps}")
    
    async def _decompose_task(self, coordinated_task: CoordinatedTask) -> List[Task]:
        """
        Decompose coordinated task into subtasks
        """
        subtasks = []
        
        if coordinated_task.task_type == TaskType.CODE_ANALYSIS:
            # Decompose code analysis
            code_snippets = coordinated_task.data.get('code_snippets', [])
            analysis_type = coordinated_task.data.get('analysis_type', 'quality')
            
            for i, code in enumerate(code_snippets):
                subtask = Task(
                    task_id=f"{coordinated_task.task_id}_sub_{i}",
                    task_type="code_analysis",
                    data={
                        'code': code,
                        'analysis_type': analysis_type,
                        'snippet_index': i
                    },
                    priority=coordinated_task.priority,
                    timeout=coordinated_task.timeout / len(code_snippets)
                )
                subtasks.append(subtask)
        
        elif coordinated_task.task_type == TaskType.TESTING:
            # Decompose testing
            test_suites = coordinated_task.data.get('test_suites', [])
            
            for i, test_suite in enumerate(test_suites):
                subtask = Task(
                    task_id=f"{coordinated_task.task_id}_test_{i}",
                    task_type="testing",
                    data={
                        'test_suite': test_suite,
                        'suite_index': i
                    },
                    priority=coordinated_task.priority,
                    timeout=coordinated_task.timeout / len(test_suites)
                )
                subtasks.append(subtask)
        
        elif coordinated_task.task_type == TaskType.DEBUGGING:
            # Decompose debugging workflow
            error_data = coordinated_task.data.get('error_data', {})
            debugging_steps = coordinated_task.data.get('debugging_steps', [])
            
            for i, step in enumerate(debugging_steps):
                subtask = Task(
                    task_id=f"{coordinated_task.task_id}_debug_{i}",
                    task_type="debugging",
                    data={
                        'error_data': error_data,
                        'debugging_step': step,
                        'step_index': i
                    },
                    priority=coordinated_task.priority,
                    timeout=coordinated_task.timeout / len(debugging_steps)
                )
                subtasks.append(subtask)
        
        else:
            # Default decomposition - single subtask
            subtask = Task(
                task_id=f"{coordinated_task.task_id}_sub_0",
                task_type=coordinated_task.task_type.value,
                data=coordinated_task.data,
                priority=coordinated_task.priority,
                timeout=coordinated_task.timeout
            )
            subtasks.append(subtask)
        
        return subtasks
    
    async def _execute_sequential(self, coordinated_task: CoordinatedTask) -> List[TaskResult]:
        """
        Execute subtasks sequentially
        """
        results = []
        
        for subtask in coordinated_task.subtasks:
            result = await self.worker_manager.execute_task_sync(subtask)
            results.append(result)
            
            # Stop if a task fails and it's critical
            if not result.success and coordinated_task.task_type == TaskType.DEBUGGING:
                break
        
        return results
    
    async def _execute_parallel(self, coordinated_task: CoordinatedTask) -> List[TaskResult]:
        """
        Execute subtasks in parallel
        """
        # Submit all tasks
        task_ids = []
        for subtask in coordinated_task.subtasks:
            task_id = await self.worker_manager.submit_task(subtask)
            task_ids.append(task_id)
        
        # Collect results
        results = []
        for task_id in task_ids:
            result = await self.worker_manager.get_result(task_id, coordinated_task.timeout)
            if result:
                results.append(result)
        
        return results
    
    async def _execute_pipeline(self, coordinated_task: CoordinatedTask) -> List[TaskResult]:
        """
        Execute subtasks in pipeline fashion
        """
        results = []
        pipeline_data = coordinated_task.data.copy()
        
        for subtask in coordinated_task.subtasks:
            # Update subtask data with pipeline results
            subtask.data.update(pipeline_data)
            
            result = await self.worker_manager.execute_task_sync(subtask)
            results.append(result)
            
            # Pass result to next stage
            if result.success and result.result:
                pipeline_data.update(result.result)
            else:
                break  # Pipeline broken
        
        return results
    
    async def _execute_map_reduce(self, coordinated_task: CoordinatedTask) -> List[TaskResult]:
        """
        Execute subtasks using map-reduce pattern
        """
        # Map phase - execute all subtasks in parallel
        map_results = await self._execute_parallel(coordinated_task)
        
        # Reduce phase - aggregate results
        if map_results:
            reduce_task = Task(
                task_id=f"{coordinated_task.task_id}_reduce",
                task_type="reduce",
                data={
                    'map_results': [r.result for r in map_results if r.success],
                    'original_data': coordinated_task.data
                },
                priority=coordinated_task.priority,
                timeout=coordinated_task.timeout * 0.2  # 20% of time for reduce
            )
            
            reduce_result = await self.worker_manager.execute_task_sync(reduce_task)
            map_results.append(reduce_result)
        
        return map_results
    
    async def _aggregate_results(self, coordinated_task: CoordinatedTask, 
                                results: List[TaskResult]) -> Any:
        """
        Aggregate results based on task type
        """
        try:
            if coordinated_task.task_type == TaskType.CODE_ANALYSIS:
                # Aggregate code analysis results
                analysis_results = []
                for result in results:
                    if result.success and result.result:
                        analysis_results.append(result.result)
                
                return {
                    'analysis_type': coordinated_task.data.get('analysis_type'),
                    'total_snippets': len(coordinated_task.data.get('code_snippets', [])),
                    'analyzed_snippets': len(analysis_results),
                    'results': analysis_results,
                    'summary': self._summarize_analysis(analysis_results)
                }
            
            elif coordinated_task.task_type == TaskType.TESTING:
                # Aggregate testing results
                test_results = []
                total_tests = 0
                passed_tests = 0
                
                for result in results:
                    if result.success and result.result:
                        test_results.append(result.result)
                        total_tests += result.result.get('total_tests', 0)
                        passed_tests += result.result.get('passed_tests', 0)
                
                return {
                    'total_test_suites': len(coordinated_task.data.get('test_suites', [])),
                    'executed_suites': len(test_results),
                    'total_tests': total_tests,
                    'passed_tests': passed_tests,
                    'failed_tests': total_tests - passed_tests,
                    'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                    'results': test_results
                }
            
            elif coordinated_task.task_type == TaskType.DEBUGGING:
                # Aggregate debugging results
                debug_steps = []
                for result in results:
                    if result.success and result.result:
                        debug_steps.append(result.result)
                
                return {
                    'debugging_steps': len(debug_steps),
                    'steps_completed': len([s for s in debug_steps if s.get('completed', False)]),
                    'issue_resolved': any(s.get('issue_resolved', False) for s in debug_steps),
                    'steps': debug_steps
                }
            
            else:
                # Default aggregation
                successful_results = [r.result for r in results if r.success]
                return {
                    'total_subtasks': len(results),
                    'successful_subtasks': len(successful_results),
                    'results': successful_results
                }
                
        except Exception as e:
            logger.error(f"🟣 Error aggregating results: {e}")
            return {'error': str(e)}
    
    def _summarize_analysis(self, analysis_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Summarize code analysis results
        """
        try:
            if not analysis_results:
                return {}
            
            # Calculate averages and totals
            total_issues = sum(r.get('issues_found', 0) for r in analysis_results)
            avg_quality_score = sum(r.get('quality_score', 0) for r in analysis_results) / len(analysis_results)
            
            issue_types = {}
            for result in analysis_results:
                for issue_type in result.get('issue_types', []):
                    issue_types[issue_type] = issue_types.get(issue_type, 0) + 1
            
            return {
                'total_issues': total_issues,
                'avg_quality_score': avg_quality_score,
                'issue_types': issue_types,
                'snippets_analyzed': len(analysis_results)
            }
            
        except Exception as e:
            logger.error(f"🟣 Error summarizing analysis: {e}")
            return {}
    
    async def cleanup(self) -> None:
        """
        Cleanup task coordinator
        """
        try:
            self.active_tasks.clear()
            self.completed_tasks.clear()
            self.task_dependencies.clear()
            
            logger.info("🟣 Task Coordinator cleanup completed")
            
        except Exception as e:
            logger.error(f"🟣 Error during cleanup: {e}")