"""
🔄 Engine Coordinator

Revolutionary coordination system for the Three-Engine Architecture.
Orchestrates Perfect Recall, Parallel Mind, and Creative engines for optimal performance.
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum

from .perfect_recall.engine import PerfectRecallEngine, RecallRequest
from .parallel_mind.worker_manager import WorkerManager
from .creative_engine.solution_generator import SolutionGenerator
from .base_engine import BaseEngine

class EngineType(Enum):
    PERFECT_RECALL = "perfect_recall"
    PARALLEL_MIND = "parallel_mind"
    CREATIVE = "creative"

class TaskComplexity(Enum):
    SIMPLE = "simple"
    MODERATE = "moderate" 
    COMPLEX = "complex"
    ENTERPRISE = "enterprise"

@dataclass
class CoordinatedRequest:
    """Request that may require multiple engines"""
    task_id: str
    task_type: str
    description: str
    input_data: Any
    complexity: TaskComplexity
    required_engines: List[EngineType]
    coordination_strategy: str  # "sequential", "parallel", "adaptive"
    timeout_seconds: int = 60

@dataclass
class EngineResponse:
    """Response from a single engine"""
    engine_type: EngineType
    success: bool
    result: Any
    execution_time_ms: float
    metadata: Dict[str, Any]

@dataclass
class CoordinatedResponse:
    """Final coordinated response"""
    task_id: str
    success: bool
    primary_result: Any
    engine_responses: List[EngineResponse]
    coordination_summary: Dict[str, Any]
    total_execution_time_ms: float

class EngineCoordinator(BaseEngine):
    """Coordinates tasks across the three engines"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("engine_coordinator", config)
        self.config = config
        self.engines = {}
        self.coordination_strategies = {
            "sequential": self._execute_sequential,
            "parallel": self._execute_parallel,
            "adaptive": self._execute_adaptive
        }
        
        # Performance metrics
        self.coordination_metrics = {
            'total_coordinated_tasks': 0,
            'avg_coordination_time': 0.0,
            'engine_utilization': {
                'perfect_recall': 0.0,
                'parallel_mind': 0.0,
                'creative': 0.0
            },
            'coordination_success_rate': 0.0
        }
    
    async def initialize(self) -> bool:
        """Initialize all engines"""
        try:
            # Initialize Perfect Recall Engine
            self.engines[EngineType.PERFECT_RECALL] = PerfectRecallEngine(
                self.config.get('perfect_recall', {})
            )
            
            # Initialize Parallel Mind Engine (Worker Manager)
            self.engines[EngineType.PARALLEL_MIND] = WorkerManager(
                min_workers=self.config.get('parallel_mind', {}).get('min_workers', 4),
                max_workers=self.config.get('parallel_mind', {}).get('max_workers', 16)
            )
            
            # Initialize Creative Engine (Solution Generator)
            self.engines[EngineType.CREATIVE] = SolutionGenerator()
            
            # Start all engines
            initialization_results = []
            
            # Initialize Perfect Recall
            recall_init = await self.engines[EngineType.PERFECT_RECALL].initialize()
            initialization_results.append(recall_init)
            
            # Initialize Parallel Mind
            parallel_init = await self.engines[EngineType.PARALLEL_MIND].start()
            initialization_results.append(parallel_init)
            
            # Creative engine doesn't need async initialization
            initialization_results.append(True)
            
            if all(initialization_results):
                self.status = "active"
                self.logger.info("🎉 All three engines initialized successfully!")
                return True
            else:
                self.status = "error"
                self.logger.error("❌ Some engines failed to initialize")
                return False
                
        except Exception as e:
            self.status = "error"
            self.logger.error(f"❌ Engine coordination initialization failed: {e}")
            return False
    
    async def execute_coordinated_task(self, request: CoordinatedRequest) -> CoordinatedResponse:
        """Execute a task across multiple engines"""
        request_id = request.task_id
        start_time = self._start_request_tracking(request_id, request)
        
        try:
            # Select coordination strategy
            strategy = self.coordination_strategies.get(
                request.coordination_strategy, 
                self._execute_adaptive
            )
            
            # Execute using selected strategy
            engine_responses = await strategy(request)
            
            # Synthesize final result
            primary_result = await self._synthesize_results(request, engine_responses)
            
            # Calculate metrics
            total_time = self._end_request_tracking(request_id, True, primary_result)
            success = any(response.success for response in engine_responses)
            
            # Update performance metrics
            self._update_coordination_metrics(request, engine_responses, total_time, success)
            
            # Create coordination summary
            coordination_summary = {
                'strategy_used': request.coordination_strategy,
                'engines_utilized': [r.engine_type.value for r in engine_responses],
                'total_engines': len(engine_responses),
                'success_rate': sum(r.success for r in engine_responses) / len(engine_responses),
                'avg_engine_time': sum(r.execution_time_ms for r in engine_responses) / len(engine_responses),
                'complexity_handled': request.complexity.value
            }
            
            response = CoordinatedResponse(
                task_id=request.task_id,
                success=success,
                primary_result=primary_result,
                engine_responses=engine_responses,
                coordination_summary=coordination_summary,
                total_execution_time_ms=total_time
            )
            
            self.logger.info(f"🔄 Coordinated task completed in {total_time:.2f}ms")
            return response
            
        except Exception as e:
            self._end_request_tracking(request_id, False)
            self.logger.error(f"Failed to execute coordinated task: {e}")
            raise
    
    async def _execute_sequential(self, request: CoordinatedRequest) -> List[EngineResponse]:
        """Execute engines sequentially, passing results forward"""
        responses = []
        current_data = request.input_data
        
        for engine_type in request.required_engines:
            if engine_type not in self.engines:
                continue
                
            start_time = asyncio.get_event_loop().time()
            
            try:
                # Execute engine with current data
                result = await self._execute_single_engine(
                    engine_type, request.task_type, current_data
                )
                
                execution_time = (asyncio.get_event_loop().time() - start_time) * 1000
                
                response = EngineResponse(
                    engine_type=engine_type,
                    success=True,
                    result=result,
                    execution_time_ms=execution_time,
                    metadata={"execution_order": len(responses) + 1}
                )
                
                responses.append(response)
                
                # Update data for next engine (if applicable)
                if hasattr(result, 'output_data'):
                    current_data = result.output_data
                
            except Exception as e:
                execution_time = (asyncio.get_event_loop().time() - start_time) * 1000
                
                response = EngineResponse(
                    engine_type=engine_type,
                    success=False,
                    result=None,
                    execution_time_ms=execution_time,
                    metadata={"error": str(e)}
                )
                
                responses.append(response)
        
        return responses
    
    async def _execute_parallel(self, request: CoordinatedRequest) -> List[EngineResponse]:
        """Execute engines in parallel"""
        tasks = []
        
        for engine_type in request.required_engines:
            if engine_type not in self.engines:
                continue
                
            task = asyncio.create_task(
                self._execute_engine_with_timing(engine_type, request.task_type, request.input_data)
            )
            tasks.append((engine_type, task))
        
        # Wait for all engines to complete
        responses = []
        results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
        
        for (engine_type, _), result in zip(tasks, results):
            if isinstance(result, Exception):
                response = EngineResponse(
                    engine_type=engine_type,
                    success=False,
                    result=None,
                    execution_time_ms=0.0,
                    metadata={"error": str(result)}
                )
            else:
                response = result
            
            responses.append(response)
        
        return responses
    
    async def _execute_adaptive(self, request: CoordinatedRequest) -> List[EngineResponse]:
        """Adaptive execution based on task complexity and engine capabilities"""
        responses = []
        
        # For complex tasks, start with Perfect Recall for context
        if request.complexity in [TaskComplexity.COMPLEX, TaskComplexity.ENTERPRISE]:
            if EngineType.PERFECT_RECALL in request.required_engines:
                recall_response = await self._execute_engine_with_timing(
                    EngineType.PERFECT_RECALL, request.task_type, request.input_data
                )
                responses.append(recall_response)
                
                # Use recall results to enhance other engine inputs
                if recall_response.success:
                    enhanced_data = {
                        **request.input_data,
                        'context': recall_response.result
                    }
                else:
                    enhanced_data = request.input_data
            else:
                enhanced_data = request.input_data
        else:
            enhanced_data = request.input_data
        
        # Execute remaining engines based on task type
        remaining_engines = [e for e in request.required_engines if e != EngineType.PERFECT_RECALL]
        
        if request.task_type in ['debugging', 'analysis', 'optimization']:
            # For analytical tasks, use Parallel Mind for processing
            if EngineType.PARALLEL_MIND in remaining_engines:
                parallel_response = await self._execute_engine_with_timing(
                    EngineType.PARALLEL_MIND, request.task_type, enhanced_data
                )
                responses.append(parallel_response)
                remaining_engines.remove(EngineType.PARALLEL_MIND)
        
        # Execute Creative Engine last for innovative solutions
        if EngineType.CREATIVE in remaining_engines:
            creative_response = await self._execute_engine_with_timing(
                EngineType.CREATIVE, request.task_type, enhanced_data
            )
            responses.append(creative_response)
        
        return responses
    
    async def _execute_engine_with_timing(self, engine_type: EngineType, task_type: str, data: Any) -> EngineResponse:
        """Execute single engine with timing"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            result = await self._execute_single_engine(engine_type, task_type, data)
            execution_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            return EngineResponse(
                engine_type=engine_type,
                success=True,
                result=result,
                execution_time_ms=execution_time,
                metadata={"task_type": task_type}
            )
            
        except Exception as e:
            execution_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            return EngineResponse(
                engine_type=engine_type,
                success=False,
                result=None,
                execution_time_ms=execution_time,
                metadata={"error": str(e), "task_type": task_type}
            )
    
    async def _execute_single_engine(self, engine_type: EngineType, task_type: str, data: Any) -> Any:
        """Execute a specific engine"""
        engine = self.engines[engine_type]
        
        if engine_type == EngineType.PERFECT_RECALL:
            if task_type == "recall":
                request = RecallRequest(query=data.get('query', ''))
                return await engine.retrieve_fast(request)
            elif task_type == "store":
                return await engine.store_context(
                    data.get('content', ''),
                    data.get('context_type', 'general'),
                    data.get('session_id', 'default')
                )
        
        elif engine_type == EngineType.PARALLEL_MIND:
            # Submit task to worker manager
            task_id = await engine.submit_task(
                self._dummy_task_function,
                data,
                priority=data.get('priority', 5)
            )
            return await engine.get_task_result(task_id, timeout=30)
        
        elif engine_type == EngineType.CREATIVE:
            # Use solution generator
            from .creative_engine.solution_generator import SolutionCriteria, GenerationContext
            
            criteria = SolutionCriteria(
                problem_domain=data.get('domain', 'general'),
                constraints=data.get('constraints', []),
                innovation_level=data.get('innovation_level', 0.7)
            )
            
            context = GenerationContext(
                problem_statement=data.get('problem', ''),
                existing_solutions=[],
                domain_knowledge={},
                user_preferences={},
                constraints=data.get('constraints', [])
            )
            
            return await engine.generate_solutions(criteria, context)
        
        else:
            raise ValueError(f"Unknown engine type: {engine_type}")
    
    def _dummy_task_function(self, data: Any) -> Dict[str, Any]:
        """Dummy task function for parallel mind testing"""
        import time
        time.sleep(0.1)  # Simulate work
        return {"processed": True, "data": data}
    
    async def _synthesize_results(self, request: CoordinatedRequest, responses: List[EngineResponse]) -> Any:
        """Synthesize results from multiple engines into final result"""
        successful_responses = [r for r in responses if r.success]
        
        if not successful_responses:
            return {"error": "All engines failed", "task_id": request.task_id}
        
        # Simple synthesis strategy based on task type
        if request.task_type == "creative_debugging":
            return self._synthesize_creative_debugging(successful_responses)
        elif request.task_type == "comprehensive_analysis":
            return self._synthesize_comprehensive_analysis(successful_responses)
        elif request.task_type == "intelligent_generation":
            return self._synthesize_intelligent_generation(successful_responses)
        else:
            # Default: return results from all engines
            return {
                "synthesized_result": True,
                "individual_results": {
                    response.engine_type.value: response.result 
                    for response in successful_responses
                },
                "primary_source": successful_responses[0].engine_type.value
            }
    
    def _synthesize_creative_debugging(self, responses: List[EngineResponse]) -> Dict[str, Any]:
        """Synthesize results for creative debugging tasks"""
        recall_data = None
        parallel_analysis = None
        creative_solutions = None
        
        for response in responses:
            if response.engine_type == EngineType.PERFECT_RECALL:
                recall_data = response.result
            elif response.engine_type == EngineType.PARALLEL_MIND:
                parallel_analysis = response.result
            elif response.engine_type == EngineType.CREATIVE:
                creative_solutions = response.result
        
        return {
            "debugging_approach": "creative_multi_engine",
            "context_analysis": recall_data,
            "parallel_diagnosis": parallel_analysis,
            "creative_solutions": creative_solutions,
            "recommended_action": self._recommend_debugging_action(recall_data, parallel_analysis, creative_solutions)
        }
    
    def _synthesize_comprehensive_analysis(self, responses: List[EngineResponse]) -> Dict[str, Any]:
        """Synthesize results for comprehensive analysis"""
        return {
            "analysis_type": "comprehensive",
            "insights": {
                response.engine_type.value: self._extract_insights(response.result)
                for response in responses
            },
            "confidence_score": sum(r.success for r in responses) / len(responses),
            "recommendations": self._generate_recommendations(responses)
        }
    
    def _synthesize_intelligent_generation(self, responses: List[EngineResponse]) -> Dict[str, Any]:
        """Synthesize results for intelligent generation tasks"""
        return {
            "generation_type": "intelligent_multi_engine",
            "final_output": self._merge_generation_results(responses),
            "quality_metrics": self._calculate_generation_quality(responses),
            "source_attribution": {
                response.engine_type.value: response.execution_time_ms
                for response in responses
            }
        }
    
    def _recommend_debugging_action(self, recall_data: Any, parallel_analysis: Any, creative_solutions: Any) -> str:
        """Recommend debugging action based on engine results"""
        if creative_solutions and hasattr(creative_solutions, 'solutions'):
            if len(creative_solutions.solutions) > 0:
                return f"Try creative solution: {creative_solutions.solutions[0].title}"
        
        if parallel_analysis and hasattr(parallel_analysis, 'result'):
            return f"Use parallel analysis result"
        
        return "Standard debugging approach recommended"
    
    def _extract_insights(self, result: Any) -> Dict[str, Any]:
        """Extract insights from engine result"""
        if hasattr(result, 'context_summary'):
            return {"type": "context", "summary": result.context_summary}
        elif hasattr(result, 'solutions'):
            return {"type": "solutions", "count": len(result.solutions)}
        else:
            return {"type": "generic", "data": str(result)[:100]}
    
    def _generate_recommendations(self, responses: List[EngineResponse]) -> List[str]:
        """Generate recommendations based on all engine responses"""
        recommendations = []
        
        for response in responses:
            if response.engine_type == EngineType.CREATIVE:
                recommendations.append("Consider innovative approaches")
            elif response.engine_type == EngineType.PARALLEL_MIND:
                recommendations.append("Leverage parallel processing capabilities")
            elif response.engine_type == EngineType.PERFECT_RECALL:
                recommendations.append("Utilize historical context and patterns")
        
        return recommendations
    
    def _merge_generation_results(self, responses: List[EngineResponse]) -> Dict[str, Any]:
        """Merge generation results from multiple engines"""
        merged = {"components": {}}
        
        for response in responses:
            merged["components"][response.engine_type.value] = {
                "result": response.result,
                "quality_score": getattr(response.result, 'quality_score', 0.8)
            }
        
        return merged
    
    def _calculate_generation_quality(self, responses: List[EngineResponse]) -> Dict[str, float]:
        """Calculate overall generation quality"""
        return {
            "overall_quality": sum(r.success for r in responses) / len(responses),
            "avg_execution_time": sum(r.execution_time_ms for r in responses) / len(responses),
            "engine_consensus": 0.8  # Simplified metric
        }
    
    def _update_coordination_metrics(self, request: CoordinatedRequest, 
                                   responses: List[EngineResponse], 
                                   total_time: float, success: bool):
        """Update coordination performance metrics"""
        self.coordination_metrics['total_coordinated_tasks'] += 1
        self.coordination_metrics['avg_coordination_time'] = (
            self.coordination_metrics['avg_coordination_time'] * 0.9 + total_time * 0.1
        )
        
        # Update engine utilization
        for response in responses:
            engine_name = response.engine_type.value
            self.coordination_metrics['engine_utilization'][engine_name] = (
                self.coordination_metrics['engine_utilization'][engine_name] * 0.9 + 
                (1.0 if response.success else 0.0) * 0.1
            )
        
        # Update success rate
        current_success_rate = self.coordination_metrics['coordination_success_rate']
        self.coordination_metrics['coordination_success_rate'] = (
            current_success_rate * 0.9 + (1.0 if success else 0.0) * 0.1
        )
    
    async def get_engine_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        engine_statuses = {}
        
        for engine_type, engine in self.engines.items():
            try:
                if engine_type == EngineType.PERFECT_RECALL:
                    status = await engine.get_engine_status()
                elif engine_type == EngineType.PARALLEL_MIND:
                    status = await engine.get_status()
                else:
                    status = {"status": "active", "engine_type": engine_type.value}
                
                engine_statuses[engine_type.value] = status
            except Exception as e:
                engine_statuses[engine_type.value] = {
                    "status": "error",
                    "error": str(e)
                }
        
        performance_summary = self.get_performance_summary()
        
        return {
            "coordinator_status": self.status,
            "engine_statuses": engine_statuses,
            "coordination_metrics": self.coordination_metrics,
            "performance_summary": performance_summary,
            "coordination_capabilities": {
                "sequential_execution": True,
                "parallel_execution": True,
                "adaptive_coordination": True,
                "result_synthesis": True
            }
        }
    
    async def shutdown(self):
        """Shutdown all engines"""
        shutdown_tasks = []
        
        for engine_type, engine in self.engines.items():
            try:
                if engine_type == EngineType.PERFECT_RECALL:
                    if hasattr(engine, 'shutdown'):
                        shutdown_tasks.append(engine.shutdown())
                elif engine_type == EngineType.PARALLEL_MIND:
                    shutdown_tasks.append(engine.shutdown())
                # Creative engine doesn't need shutdown
            except Exception as e:
                self.logger.error(f"Error shutting down {engine_type.value}: {e}")
        
        if shutdown_tasks:
            await asyncio.gather(*shutdown_tasks, return_exceptions=True)
        
        self.status = "shutdown"
        self.logger.info("🛑 Engine Coordinator shutdown complete")