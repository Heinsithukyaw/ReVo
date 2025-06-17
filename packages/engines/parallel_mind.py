"""
Three-Engine Architecture for reVoAgent Enterprise
Parallel Mind Engine - Multi-threaded reasoning and parallel processing
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass
from enum import Enum
import time
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json

logger = logging.getLogger(__name__)

class ReasoningType(Enum):
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    LOGICAL = "logical"
    INTUITIVE = "intuitive"
    CRITICAL = "critical"
    STRATEGIC = "strategic"

class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class ReasoningTask:
    id: str
    prompt: str
    reasoning_type: ReasoningType
    priority: TaskPriority
    context: Dict[str, Any]
    created_at: float
    timeout: float = 30.0
    dependencies: List[str] = None
    callback: Optional[Callable] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

@dataclass
class ReasoningResult:
    task_id: str
    result: Any
    reasoning_path: List[str]
    confidence: float
    processing_time: float
    status: TaskStatus
    metadata: Dict[str, Any]

class ParallelMindEngine:
    """
    Parallel Mind Engine - Enables simultaneous multi-perspective reasoning
    Features:
    - Parallel task execution
    - Multi-perspective analysis
    - Reasoning pipeline management
    - Context-aware processing
    - Dynamic load balancing
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Configuration
        self.max_workers = self.config.get('max_workers', 4)
        self.max_concurrent_tasks = self.config.get('max_concurrent_tasks', 10)
        self.default_timeout = self.config.get('default_timeout', 30.0)
        
        # Thread pool for CPU-bound tasks
        self.thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)
        
        # Task management
        self.active_tasks: Dict[str, ReasoningTask] = {}
        self.completed_tasks: Dict[str, ReasoningResult] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        
        # Reasoning engines (different perspectives)
        self.reasoning_engines = {
            ReasoningType.ANALYTICAL: self._analytical_reasoning,
            ReasoningType.CREATIVE: self._creative_reasoning,
            ReasoningType.LOGICAL: self._logical_reasoning,
            ReasoningType.INTUITIVE: self._intuitive_reasoning,
            ReasoningType.CRITICAL: self._critical_reasoning,
            ReasoningType.STRATEGIC: self._strategic_reasoning
        }
        
        # Statistics
        self.stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'avg_processing_time': 0.0,
            'concurrent_peak': 0
        }
        
        # Start background task processor
        self._processor_task = None
        
        logger.info("🧠 Parallel Mind Engine initialized")
    
    async def start(self):
        """Start the parallel processing engine"""
        if self._processor_task is None:
            self._processor_task = asyncio.create_task(self._process_tasks())
            logger.info("✅ Parallel Mind Engine started")
    
    async def stop(self):
        """Stop the parallel processing engine"""
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
            self._processor_task = None
        
        # Shutdown thread pool
        self.thread_pool.shutdown(wait=True)
        logger.info("🛑 Parallel Mind Engine stopped")
    
    def _generate_task_id(self, prompt: str, reasoning_type: ReasoningType) -> str:
        """Generate unique task ID"""
        hash_input = f"{prompt}{reasoning_type.value}{time.time()}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]
    
    async def submit_task(
        self,
        prompt: str,
        reasoning_type: ReasoningType = ReasoningType.ANALYTICAL,
        priority: TaskPriority = TaskPriority.MEDIUM,
        context: Dict[str, Any] = None,
        timeout: float = None,
        dependencies: List[str] = None,
        callback: Callable = None
    ) -> str:
        """Submit a reasoning task for parallel processing"""
        try:
            task_id = self._generate_task_id(prompt, reasoning_type)
            
            task = ReasoningTask(
                id=task_id,
                prompt=prompt,
                reasoning_type=reasoning_type,
                priority=priority,
                context=context or {},
                created_at=time.time(),
                timeout=timeout or self.default_timeout,
                dependencies=dependencies or [],
                callback=callback
            )
            
            # Add to active tasks
            self.active_tasks[task_id] = task
            
            # Add to queue
            await self.task_queue.put(task)
            
            self.stats['total_tasks'] += 1
            
            logger.debug(f"Submitted task {task_id}: {reasoning_type.value}")
            return task_id
            
        except Exception as e:
            logger.error(f"Error submitting task: {e}")
            raise
    
    async def submit_multi_perspective_task(
        self,
        prompt: str,
        perspectives: List[ReasoningType] = None,
        context: Dict[str, Any] = None,
        timeout: float = None
    ) -> List[str]:
        """Submit the same task for multiple reasoning perspectives"""
        if perspectives is None:
            perspectives = [
                ReasoningType.ANALYTICAL,
                ReasoningType.CREATIVE,
                ReasoningType.LOGICAL,
                ReasoningType.CRITICAL
            ]
        
        task_ids = []
        for perspective in perspectives:
            task_id = await self.submit_task(
                prompt=prompt,
                reasoning_type=perspective,
                context=context,
                timeout=timeout
            )
            task_ids.append(task_id)
        
        logger.info(f"Submitted multi-perspective task with {len(perspectives)} perspectives")
        return task_ids
    
    async def _process_tasks(self):
        """Background task processor"""
        while True:
            try:
                # Get task from queue
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                
                # Check dependencies
                if not await self._check_dependencies(task):
                    # Re-queue task if dependencies not met
                    await self.task_queue.put(task)
                    await asyncio.sleep(0.1)
                    continue
                
                # Check concurrent task limit
                running_count = len([t for t in self.active_tasks.values() 
                                   if t.id in self.active_tasks])
                
                if running_count >= self.max_concurrent_tasks:
                    await self.task_queue.put(task)
                    await asyncio.sleep(0.5)
                    continue
                
                # Process task
                asyncio.create_task(self._execute_task(task))
                
            except asyncio.TimeoutError:
                # No tasks in queue, continue
                continue
            except Exception as e:
                logger.error(f"Error in task processor: {e}")
                await asyncio.sleep(1.0)
    
    async def _check_dependencies(self, task: ReasoningTask) -> bool:
        """Check if task dependencies are completed"""
        for dep_id in task.dependencies:
            if dep_id not in self.completed_tasks:
                return False
        return True
    
    async def _execute_task(self, task: ReasoningTask):
        """Execute a single reasoning task"""
        start_time = time.time()
        
        try:
            logger.debug(f"Executing task {task.id}: {task.reasoning_type.value}")
            
            # Get reasoning engine
            reasoning_engine = self.reasoning_engines.get(task.reasoning_type)
            if not reasoning_engine:
                raise ValueError(f"Unknown reasoning type: {task.reasoning_type}")
            
            # Execute reasoning with timeout
            reasoning_result = await asyncio.wait_for(
                reasoning_engine(task),
                timeout=task.timeout
            )
            
            processing_time = time.time() - start_time
            
            # Create result
            result = ReasoningResult(
                task_id=task.id,
                result=reasoning_result['result'],
                reasoning_path=reasoning_result.get('reasoning_path', []),
                confidence=reasoning_result.get('confidence', 0.5),
                processing_time=processing_time,
                status=TaskStatus.COMPLETED,
                metadata={
                    'reasoning_type': task.reasoning_type.value,
                    'priority': task.priority.value,
                    'context': task.context
                }
            )
            
            # Store result
            self.completed_tasks[task.id] = result
            
            # Remove from active tasks
            if task.id in self.active_tasks:
                del self.active_tasks[task.id]
            
            # Update statistics
            self.stats['completed_tasks'] += 1
            self.stats['avg_processing_time'] = (
                (self.stats['avg_processing_time'] * (self.stats['completed_tasks'] - 1) + processing_time) /
                self.stats['completed_tasks']
            )
            
            # Execute callback if provided
            if task.callback:
                try:
                    await task.callback(result)
                except Exception as e:
                    logger.warning(f"Callback execution failed for task {task.id}: {e}")
            
            logger.debug(f"Completed task {task.id} in {processing_time:.2f}s")
            
        except asyncio.TimeoutError:
            logger.warning(f"Task {task.id} timed out")
            await self._handle_task_failure(task, "Timeout")
        except Exception as e:
            logger.error(f"Task {task.id} failed: {e}")
            await self._handle_task_failure(task, str(e))
    
    async def _handle_task_failure(self, task: ReasoningTask, error: str):
        """Handle task failure"""
        result = ReasoningResult(
            task_id=task.id,
            result=None,
            reasoning_path=[],
            confidence=0.0,
            processing_time=time.time() - task.created_at,
            status=TaskStatus.FAILED,
            metadata={'error': error}
        )
        
        self.completed_tasks[task.id] = result
        
        if task.id in self.active_tasks:
            del self.active_tasks[task.id]
        
        self.stats['failed_tasks'] += 1
    
    # Reasoning Engines - Different cognitive approaches
    
    async def _analytical_reasoning(self, task: ReasoningTask) -> Dict[str, Any]:
        """Analytical reasoning - structured, step-by-step analysis"""
        reasoning_path = [
            "Breaking down the problem into components",
            "Analyzing each component systematically", 
            "Identifying patterns and relationships",
            "Drawing logical conclusions",
            "Validating results"
        ]
        
        # Simulate analytical processing
        await asyncio.sleep(0.1)
        
        # Simple analytical approach
        prompt = task.prompt.lower()
        analytical_keywords = ['analyze', 'structure', 'components', 'systematic']
        confidence = sum(1 for kw in analytical_keywords if kw in prompt) / len(analytical_keywords)
        
        result = {
            'result': f"Analytical analysis of: {task.prompt}",
            'reasoning_path': reasoning_path,
            'confidence': max(0.3, confidence),
            'approach': 'systematic_analysis'
        }
        
        return result
    
    async def _creative_reasoning(self, task: ReasoningTask) -> Dict[str, Any]:
        """Creative reasoning - innovative, non-linear thinking"""
        reasoning_path = [
            "Exploring unconventional perspectives",
            "Generating multiple creative alternatives",
            "Combining disparate concepts",
            "Challenging assumptions",
            "Synthesizing novel solutions"
        ]
        
        await asyncio.sleep(0.1)
        
        prompt = task.prompt.lower()
        creative_keywords = ['creative', 'innovative', 'unique', 'original', 'new']
        confidence = sum(1 for kw in creative_keywords if kw in prompt) / len(creative_keywords)
        
        result = {
            'result': f"Creative exploration of: {task.prompt}",
            'reasoning_path': reasoning_path,
            'confidence': max(0.4, confidence),
            'approach': 'divergent_thinking'
        }
        
        return result
    
    async def _logical_reasoning(self, task: ReasoningTask) -> Dict[str, Any]:
        """Logical reasoning - formal logic and deduction"""
        reasoning_path = [
            "Establishing premises",
            "Applying logical rules",
            "Following deductive chains",
            "Checking logical consistency",
            "Reaching valid conclusions"
        ]
        
        await asyncio.sleep(0.1)
        
        prompt = task.prompt.lower()
        logical_keywords = ['logic', 'reason', 'proof', 'valid', 'conclude']
        confidence = sum(1 for kw in logical_keywords if kw in prompt) / len(logical_keywords)
        
        result = {
            'result': f"Logical analysis of: {task.prompt}",
            'reasoning_path': reasoning_path,
            'confidence': max(0.5, confidence),
            'approach': 'deductive_logic'
        }
        
        return result
    
    async def _intuitive_reasoning(self, task: ReasoningTask) -> Dict[str, Any]:
        """Intuitive reasoning - pattern recognition and gut feeling"""
        reasoning_path = [
            "Recognizing implicit patterns",
            "Accessing experiential knowledge",
            "Generating intuitive insights",
            "Testing gut feelings",
            "Integrating holistic understanding"
        ]
        
        await asyncio.sleep(0.1)
        
        prompt = task.prompt.lower()
        intuitive_keywords = ['feel', 'sense', 'intuition', 'pattern', 'experience']
        confidence = sum(1 for kw in intuitive_keywords if kw in prompt) / len(intuitive_keywords)
        
        result = {
            'result': f"Intuitive insights on: {task.prompt}",
            'reasoning_path': reasoning_path,
            'confidence': max(0.3, confidence),
            'approach': 'pattern_recognition'
        }
        
        return result
    
    async def _critical_reasoning(self, task: ReasoningTask) -> Dict[str, Any]:
        """Critical reasoning - questioning and evaluating"""
        reasoning_path = [
            "Questioning assumptions",
            "Identifying potential biases",
            "Evaluating evidence quality",
            "Considering alternative viewpoints",
            "Forming balanced judgments"
        ]
        
        await asyncio.sleep(0.1)
        
        prompt = task.prompt.lower()
        critical_keywords = ['evaluate', 'question', 'critique', 'bias', 'evidence']
        confidence = sum(1 for kw in critical_keywords if kw in prompt) / len(critical_keywords)
        
        result = {
            'result': f"Critical evaluation of: {task.prompt}",
            'reasoning_path': reasoning_path,
            'confidence': max(0.4, confidence),
            'approach': 'critical_evaluation'
        }
        
        return result
    
    async def _strategic_reasoning(self, task: ReasoningTask) -> Dict[str, Any]:
        """Strategic reasoning - long-term planning and optimization"""
        reasoning_path = [
            "Defining strategic objectives",
            "Analyzing current situation",
            "Identifying key constraints",
            "Developing strategic options",
            "Optimizing for long-term success"
        ]
        
        await asyncio.sleep(0.1)
        
        prompt = task.prompt.lower()
        strategic_keywords = ['strategy', 'plan', 'goal', 'optimize', 'long-term']
        confidence = sum(1 for kw in strategic_keywords if kw in prompt) / len(strategic_keywords)
        
        result = {
            'result': f"Strategic analysis of: {task.prompt}",
            'reasoning_path': reasoning_path,
            'confidence': max(0.4, confidence),
            'approach': 'strategic_planning'
        }
        
        return result
    
    # Public API Methods
    
    async def get_task_result(self, task_id: str) -> Optional[ReasoningResult]:
        """Get result of a completed task"""
        return self.completed_tasks.get(task_id)
    
    async def get_task_status(self, task_id: str) -> TaskStatus:
        """Get current status of a task"""
        if task_id in self.completed_tasks:
            return self.completed_tasks[task_id].status
        elif task_id in self.active_tasks:
            return TaskStatus.RUNNING
        else:
            return TaskStatus.PENDING
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or running task"""
        if task_id in self.active_tasks:
            del self.active_tasks[task_id]
            
            # Create cancelled result
            result = ReasoningResult(
                task_id=task_id,
                result=None,
                reasoning_path=[],
                confidence=0.0,
                processing_time=0.0,
                status=TaskStatus.CANCELLED,
                metadata={'reason': 'cancelled_by_user'}
            )
            
            self.completed_tasks[task_id] = result
            return True
        
        return False
    
    async def get_multi_perspective_results(self, task_ids: List[str]) -> Dict[str, ReasoningResult]:
        """Get results from multiple perspective tasks"""
        results = {}
        for task_id in task_ids:
            result = await self.get_task_result(task_id)
            if result:
                results[result.metadata.get('reasoning_type', task_id)] = result
        return results
    
    async def synthesize_perspectives(self, task_ids: List[str]) -> Dict[str, Any]:
        """Synthesize results from multiple reasoning perspectives"""
        results = await self.get_multi_perspective_results(task_ids)
        
        if not results:
            return {'error': 'No results to synthesize'}
        
        synthesis = {
            'perspectives': {},
            'consensus': [],
            'conflicts': [],
            'confidence_scores': {},
            'synthesis_summary': ''
        }
        
        # Collect perspectives
        for perspective_type, result in results.items():
            synthesis['perspectives'][perspective_type] = {
                'result': result.result,
                'confidence': result.confidence,
                'reasoning_path': result.reasoning_path
            }
            synthesis['confidence_scores'][perspective_type] = result.confidence
        
        # Find consensus and conflicts (simplified)
        all_results = [r.result for r in results.values()]
        if len(set(all_results)) == 1:
            synthesis['consensus'] = ['All perspectives agree']
        else:
            synthesis['conflicts'] = ['Perspectives show different viewpoints']
        
        # Generate synthesis summary
        avg_confidence = sum(synthesis['confidence_scores'].values()) / len(synthesis['confidence_scores'])
        synthesis['synthesis_summary'] = f"Multi-perspective analysis with {len(results)} viewpoints, average confidence: {avg_confidence:.2f}"
        
        return synthesis
    
    async def get_engine_stats(self) -> Dict[str, Any]:
        """Get engine statistics"""
        current_active = len(self.active_tasks)
        if current_active > self.stats['concurrent_peak']:
            self.stats['concurrent_peak'] = current_active
        
        stats = self.stats.copy()
        stats['current_active_tasks'] = current_active
        stats['queue_size'] = self.task_queue.qsize()
        stats['success_rate'] = (
            stats['completed_tasks'] / max(1, stats['total_tasks'])
        ) if stats['total_tasks'] > 0 else 0.0
        
        return stats
