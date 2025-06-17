"""
Parallel Mind Engine - Parallel Processor
Concurrent execution and intelligent load balancing
"""

import asyncio
import time
import uuid
from typing import Dict, List, Any, Optional, Callable, Awaitable
from dataclasses import dataclass
from datetime import datetime
import logging

from .worker_manager import WorkerManager, Task, TaskResult
from .task_coordinator import TaskCoordinator, CoordinatedTask, CoordinationResult, TaskType

logger = logging.getLogger(__name__)

@dataclass
class ProcessingRequest:
    """Request for parallel processing"""
    request_id: str
    processing_type: str
    data: Dict[str, Any]
    parallelization_strategy: str
    max_workers: Optional[int] = None
    timeout: float = 60.0
    priority: int = 1

@dataclass
class ProcessingResult:
    """Result of parallel processing"""
    request_id: str
    success: bool
    results: List[Any]
    aggregated_result: Any
    execution_time: float
    workers_used: int
    processing_strategy: str
    completed_at: datetime

class ParallelProcessor:
    """
    High-level parallel processing interface
    Provides intelligent concurrent execution and load balancing
    """
    
    def __init__(self, worker_manager: WorkerManager, task_coordinator: TaskCoordinator):
        self.worker_manager = worker_manager
        self.task_coordinator = task_coordinator
        self.processing_strategies = {
            'data_parallel': self._process_data_parallel,
            'task_parallel': self._process_task_parallel,
            'pipeline_parallel': self._process_pipeline_parallel,
            'batch_parallel': self._process_batch_parallel,
            'streaming_parallel': self._process_streaming_parallel
        }
        self.active_requests: Dict[str, ProcessingRequest] = {}
        self.completed_requests: Dict[str, ProcessingResult] = {}
        
    async def initialize(self) -> bool:
        """Initialize parallel processor"""
        try:
            logger.info("🟣 Parallel Mind Engine: Parallel Processor initialized")
            return True
        except Exception as e:
            logger.error(f"🟣 Failed to initialize Parallel Processor: {e}")
            return False
    
    async def process_parallel(self, processing_type: str, data: Dict[str, Any],
                             strategy: str = 'data_parallel',
                             max_workers: Optional[int] = None,
                             timeout: float = 60.0,
                             priority: int = 1) -> ProcessingResult:
        """
        Execute parallel processing with specified strategy
        """
        request_id = f"proc_{uuid.uuid4().hex[:8]}"
        start_time = time.time()
        
        try:
            # Create processing request
            request = ProcessingRequest(
                request_id=request_id,
                processing_type=processing_type,
                data=data,
                parallelization_strategy=strategy,
                max_workers=max_workers,
                timeout=timeout,
                priority=priority
            )
            
            self.active_requests[request_id] = request
            
            # Execute based on strategy
            if strategy not in self.processing_strategies:
                raise ValueError(f"Unknown processing strategy: {strategy}")
            
            strategy_func = self.processing_strategies[strategy]
            results, aggregated_result, workers_used = await strategy_func(request)
            
            execution_time = time.time() - start_time
            
            # Create result
            processing_result = ProcessingResult(
                request_id=request_id,
                success=True,
                results=results,
                aggregated_result=aggregated_result,
                execution_time=execution_time,
                workers_used=workers_used,
                processing_strategy=strategy,
                completed_at=datetime.now()
            )
            
            # Store completed request
            self.completed_requests[request_id] = processing_result
            
            # Remove from active requests
            if request_id in self.active_requests:
                del self.active_requests[request_id]
            
            logger.info(f"🟣 Parallel processing {request_id} completed in {execution_time:.3f}s using {workers_used} workers")
            return processing_result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"🟣 Error in parallel processing {request_id}: {e}")
            
            # Create error result
            error_result = ProcessingResult(
                request_id=request_id,
                success=False,
                results=[],
                aggregated_result=None,
                execution_time=execution_time,
                workers_used=0,
                processing_strategy=strategy,
                completed_at=datetime.now()
            )
            
            self.completed_requests[request_id] = error_result
            
            if request_id in self.active_requests:
                del self.active_requests[request_id]
            
            return error_result
    
    async def process_code_analysis_parallel(self, code_files: List[str],
                                           analysis_types: List[str] = None) -> ProcessingResult:
        """
        Parallel code analysis across multiple files
        """
        if analysis_types is None:
            analysis_types = ['syntax', 'quality', 'security', 'performance']
        
        data = {
            'code_files': code_files,
            'analysis_types': analysis_types,
            'parallel_analysis': True
        }
        
        return await self.process_parallel(
            processing_type='code_analysis',
            data=data,
            strategy='data_parallel'
        )
    
    async def process_testing_parallel(self, test_suites: List[Dict[str, Any]],
                                     test_types: List[str] = None) -> ProcessingResult:
        """
        Parallel test execution across multiple test suites
        """
        if test_types is None:
            test_types = ['unit', 'integration', 'performance']
        
        data = {
            'test_suites': test_suites,
            'test_types': test_types,
            'parallel_execution': True
        }
        
        return await self.process_parallel(
            processing_type='testing',
            data=data,
            strategy='task_parallel'
        )
    
    async def process_data_transformation_parallel(self, datasets: List[Dict[str, Any]],
                                                 transformations: List[str]) -> ProcessingResult:
        """
        Parallel data transformation across multiple datasets
        """
        data = {
            'datasets': datasets,
            'transformations': transformations,
            'parallel_processing': True
        }
        
        return await self.process_parallel(
            processing_type='data_transformation',
            data=data,
            strategy='pipeline_parallel'
        )
    
    async def process_optimization_parallel(self, optimization_targets: List[Dict[str, Any]],
                                          algorithms: List[str]) -> ProcessingResult:
        """
        Parallel optimization using multiple algorithms
        """
        data = {
            'optimization_targets': optimization_targets,
            'algorithms': algorithms,
            'parallel_optimization': True
        }
        
        return await self.process_parallel(
            processing_type='optimization',
            data=data,
            strategy='batch_parallel'
        )
    
    async def get_processing_stats(self) -> Dict[str, Any]:
        """
        Get parallel processing statistics
        """
        try:
            completed_requests = list(self.completed_requests.values())
            
            if not completed_requests:
                return {
                    'total_requests': 0,
                    'active_requests': len(self.active_requests),
                    'success_rate': 0,
                    'avg_execution_time': 0,
                    'avg_workers_used': 0,
                    'strategy_usage': {}
                }
            
            successful_requests = [r for r in completed_requests if r.success]
            
            # Strategy usage statistics
            strategy_usage = {}
            for request in completed_requests:
                strategy = request.processing_strategy
                strategy_usage[strategy] = strategy_usage.get(strategy, 0) + 1
            
            # Worker utilization statistics
            total_workers_used = sum(r.workers_used for r in completed_requests)
            avg_workers_used = total_workers_used / len(completed_requests)
            
            stats = {
                'total_requests': len(completed_requests),
                'active_requests': len(self.active_requests),
                'successful_requests': len(successful_requests),
                'failed_requests': len(completed_requests) - len(successful_requests),
                'success_rate': len(successful_requests) / len(completed_requests) * 100,
                'avg_execution_time': sum(r.execution_time for r in completed_requests) / len(completed_requests),
                'avg_workers_used': avg_workers_used,
                'total_workers_used': total_workers_used,
                'strategy_usage': strategy_usage,
                'processing_types': self._get_processing_type_stats(completed_requests)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"🟣 Error getting processing stats: {e}")
            return {}
    
    async def _process_data_parallel(self, request: ProcessingRequest) -> tuple:
        """
        Data parallel processing - split data across workers
        """
        try:
            # Determine data to split
            if request.processing_type == 'code_analysis':
                code_files = request.data.get('code_files', [])
                analysis_types = request.data.get('analysis_types', ['quality'])
                
                # Create tasks for each file
                tasks = []
                for i, code_file in enumerate(code_files):
                    for analysis_type in analysis_types:
                        task = Task(
                            task_id=f"{request.request_id}_analysis_{i}_{analysis_type}",
                            task_type="code_analysis",
                            data={
                                'code_file': code_file,
                                'analysis_type': analysis_type,
                                'file_index': i
                            },
                            priority=request.priority,
                            timeout=request.timeout / len(code_files)
                        )
                        tasks.append(task)
                
                # Execute tasks in parallel
                task_results = await self._execute_tasks_parallel(tasks, request.max_workers)
                
                # Aggregate results
                aggregated_result = self._aggregate_code_analysis_results(task_results)
                
                return task_results, aggregated_result, len(set(r.worker_id for r in task_results))
            
            else:
                # Generic data parallel processing
                data_items = request.data.get('items', [])
                
                tasks = []
                for i, item in enumerate(data_items):
                    task = Task(
                        task_id=f"{request.request_id}_item_{i}",
                        task_type=request.processing_type,
                        data={'item': item, 'item_index': i},
                        priority=request.priority,
                        timeout=request.timeout / len(data_items)
                    )
                    tasks.append(task)
                
                task_results = await self._execute_tasks_parallel(tasks, request.max_workers)
                aggregated_result = [r.result for r in task_results if r.success]
                
                return task_results, aggregated_result, len(set(r.worker_id for r in task_results))
                
        except Exception as e:
            logger.error(f"🟣 Error in data parallel processing: {e}")
            return [], None, 0
    
    async def _process_task_parallel(self, request: ProcessingRequest) -> tuple:
        """
        Task parallel processing - different tasks in parallel
        """
        try:
            if request.processing_type == 'testing':
                test_suites = request.data.get('test_suites', [])
                
                # Create tasks for each test suite
                tasks = []
                for i, test_suite in enumerate(test_suites):
                    task = Task(
                        task_id=f"{request.request_id}_test_suite_{i}",
                        task_type="testing",
                        data={
                            'test_suite': test_suite,
                            'suite_index': i
                        },
                        priority=request.priority,
                        timeout=request.timeout / len(test_suites)
                    )
                    tasks.append(task)
                
                # Execute tasks in parallel
                task_results = await self._execute_tasks_parallel(tasks, request.max_workers)
                
                # Aggregate test results
                aggregated_result = self._aggregate_test_results(task_results)
                
                return task_results, aggregated_result, len(set(r.worker_id for r in task_results))
            
            else:
                # Generic task parallel processing
                task_definitions = request.data.get('tasks', [])
                
                tasks = []
                for i, task_def in enumerate(task_definitions):
                    task = Task(
                        task_id=f"{request.request_id}_task_{i}",
                        task_type=task_def.get('type', request.processing_type),
                        data=task_def.get('data', {}),
                        priority=request.priority,
                        timeout=request.timeout / len(task_definitions)
                    )
                    tasks.append(task)
                
                task_results = await self._execute_tasks_parallel(tasks, request.max_workers)
                aggregated_result = [r.result for r in task_results if r.success]
                
                return task_results, aggregated_result, len(set(r.worker_id for r in task_results))
                
        except Exception as e:
            logger.error(f"🟣 Error in task parallel processing: {e}")
            return [], None, 0
    
    async def _process_pipeline_parallel(self, request: ProcessingRequest) -> tuple:
        """
        Pipeline parallel processing - stages in pipeline
        """
        try:
            pipeline_stages = request.data.get('pipeline_stages', [])
            input_data = request.data.get('input_data', {})
            
            # Execute pipeline stages
            stage_results = []
            current_data = input_data
            workers_used = set()
            
            for i, stage in enumerate(pipeline_stages):
                task = Task(
                    task_id=f"{request.request_id}_stage_{i}",
                    task_type=stage.get('type', 'pipeline_stage'),
                    data={
                        'stage_config': stage,
                        'input_data': current_data,
                        'stage_index': i
                    },
                    priority=request.priority,
                    timeout=request.timeout / len(pipeline_stages)
                )
                
                result = await self.worker_manager.execute_task_sync(task)
                stage_results.append(result)
                workers_used.add(result.worker_id)
                
                # Pass result to next stage
                if result.success and result.result:
                    current_data = result.result
                else:
                    break  # Pipeline broken
            
            aggregated_result = {
                'pipeline_stages': len(pipeline_stages),
                'completed_stages': len([r for r in stage_results if r.success]),
                'final_result': current_data,
                'stage_results': [r.result for r in stage_results if r.success]
            }
            
            return stage_results, aggregated_result, len(workers_used)
            
        except Exception as e:
            logger.error(f"🟣 Error in pipeline parallel processing: {e}")
            return [], None, 0
    
    async def _process_batch_parallel(self, request: ProcessingRequest) -> tuple:
        """
        Batch parallel processing - process in batches
        """
        try:
            items = request.data.get('items', [])
            batch_size = request.data.get('batch_size', 10)
            
            # Split items into batches
            batches = [items[i:i + batch_size] for i in range(0, len(items), batch_size)]
            
            # Create tasks for each batch
            tasks = []
            for i, batch in enumerate(batches):
                task = Task(
                    task_id=f"{request.request_id}_batch_{i}",
                    task_type=request.processing_type,
                    data={
                        'batch': batch,
                        'batch_index': i,
                        'batch_size': len(batch)
                    },
                    priority=request.priority,
                    timeout=request.timeout / len(batches)
                )
                tasks.append(task)
            
            # Execute batches in parallel
            task_results = await self._execute_tasks_parallel(tasks, request.max_workers)
            
            # Aggregate batch results
            aggregated_result = {
                'total_batches': len(batches),
                'processed_batches': len([r for r in task_results if r.success]),
                'total_items': len(items),
                'batch_results': [r.result for r in task_results if r.success]
            }
            
            return task_results, aggregated_result, len(set(r.worker_id for r in task_results))
            
        except Exception as e:
            logger.error(f"🟣 Error in batch parallel processing: {e}")
            return [], None, 0
    
    async def _process_streaming_parallel(self, request: ProcessingRequest) -> tuple:
        """
        Streaming parallel processing - continuous processing
        """
        try:
            stream_data = request.data.get('stream_data', [])
            window_size = request.data.get('window_size', 5)
            
            # Process stream in windows
            results = []
            workers_used = set()
            
            for i in range(0, len(stream_data), window_size):
                window = stream_data[i:i + window_size]
                
                task = Task(
                    task_id=f"{request.request_id}_window_{i // window_size}",
                    task_type=request.processing_type,
                    data={
                        'window': window,
                        'window_index': i // window_size,
                        'window_size': len(window)
                    },
                    priority=request.priority,
                    timeout=request.timeout / (len(stream_data) // window_size)
                )
                
                result = await self.worker_manager.execute_task_sync(task)
                results.append(result)
                workers_used.add(result.worker_id)
            
            aggregated_result = {
                'total_windows': len(results),
                'processed_windows': len([r for r in results if r.success]),
                'stream_length': len(stream_data),
                'window_results': [r.result for r in results if r.success]
            }
            
            return results, aggregated_result, len(workers_used)
            
        except Exception as e:
            logger.error(f"🟣 Error in streaming parallel processing: {e}")
            return [], None, 0
    
    async def _execute_tasks_parallel(self, tasks: List[Task], 
                                    max_workers: Optional[int] = None) -> List[TaskResult]:
        """
        Execute multiple tasks in parallel
        """
        # Submit all tasks
        task_ids = []
        for task in tasks:
            task_id = await self.worker_manager.submit_task(task)
            task_ids.append(task_id)
        
        # Collect results
        results = []
        for task_id in task_ids:
            result = await self.worker_manager.get_result(task_id, 60.0)
            if result:
                results.append(result)
        
        return results
    
    def _aggregate_code_analysis_results(self, task_results: List[TaskResult]) -> Dict[str, Any]:
        """
        Aggregate code analysis results
        """
        try:
            successful_results = [r.result for r in task_results if r.success and r.result]
            
            if not successful_results:
                return {'error': 'No successful analysis results'}
            
            # Aggregate by analysis type
            analysis_by_type = {}
            for result in successful_results:
                analysis_type = result.get('analysis_type', 'unknown')
                if analysis_type not in analysis_by_type:
                    analysis_by_type[analysis_type] = []
                analysis_by_type[analysis_type].append(result)
            
            # Calculate overall metrics
            total_issues = sum(r.get('issues_found', 0) for r in successful_results)
            avg_quality_score = sum(r.get('quality_score', 0) for r in successful_results) / len(successful_results)
            
            return {
                'total_files_analyzed': len(set(r.get('file_index') for r in successful_results)),
                'analysis_types': list(analysis_by_type.keys()),
                'total_issues': total_issues,
                'avg_quality_score': avg_quality_score,
                'analysis_by_type': analysis_by_type,
                'execution_summary': {
                    'total_tasks': len(task_results),
                    'successful_tasks': len(successful_results),
                    'failed_tasks': len(task_results) - len(successful_results)
                }
            }
            
        except Exception as e:
            logger.error(f"🟣 Error aggregating code analysis results: {e}")
            return {'error': str(e)}
    
    def _aggregate_test_results(self, task_results: List[TaskResult]) -> Dict[str, Any]:
        """
        Aggregate test results
        """
        try:
            successful_results = [r.result for r in task_results if r.success and r.result]
            
            if not successful_results:
                return {'error': 'No successful test results'}
            
            total_tests = sum(r.get('total_tests', 0) for r in successful_results)
            passed_tests = sum(r.get('passed_tests', 0) for r in successful_results)
            failed_tests = total_tests - passed_tests
            
            return {
                'total_test_suites': len(successful_results),
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                'test_suites': successful_results,
                'execution_summary': {
                    'total_tasks': len(task_results),
                    'successful_tasks': len(successful_results),
                    'failed_tasks': len(task_results) - len(successful_results)
                }
            }
            
        except Exception as e:
            logger.error(f"🟣 Error aggregating test results: {e}")
            return {'error': str(e)}
    
    def _get_processing_type_stats(self, completed_requests: List[ProcessingResult]) -> Dict[str, int]:
        """
        Get statistics by processing type
        """
        type_stats = {}
        for request in completed_requests:
            # Extract processing type from request_id or use a default
            processing_type = 'unknown'
            if hasattr(request, 'processing_type'):
                processing_type = request.processing_type
            
            type_stats[processing_type] = type_stats.get(processing_type, 0) + 1
        
        return type_stats
    
    async def cleanup(self) -> None:
        """
        Cleanup parallel processor
        """
        try:
            self.active_requests.clear()
            self.completed_requests.clear()
            
            logger.info("🟣 Parallel Processor cleanup completed")
            
        except Exception as e:
            logger.error(f"🟣 Error during cleanup: {e}")