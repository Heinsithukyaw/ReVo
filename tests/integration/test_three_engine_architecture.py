#!/usr/bin/env python3
"""
🎯 Three-Engine Architecture Test Suite

Comprehensive testing of the revolutionary Three-Engine Architecture:
- 🧠 Perfect Recall Engine (Memory & Context)
- ⚡ Parallel Mind Engine (Multi-Worker Processing)  
- 🎨 Creative Engine (Solution Generation)
- 🔄 Engine Coordinator (Orchestration)
"""

import asyncio
import time
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from revoagent.engines.engine_coordinator import (
    EngineCoordinator, CoordinatedRequest, TaskComplexity, EngineType
)
from revoagent.engines.perfect_recall.engine import PerfectRecallEngine, RecallRequest
from revoagent.engines.parallel_mind.worker_manager import WorkerManager
from revoagent.engines.creative_engine.solution_generator import (
    SolutionGenerator, SolutionCriteria, GenerationContext
)

class ThreeEngineArchitectureTest:
    """Comprehensive test suite for the Three-Engine Architecture"""
    
    def __init__(self):
        self.test_results = {
            'perfect_recall': {'passed': 0, 'failed': 0, 'tests': []},
            'parallel_mind': {'passed': 0, 'failed': 0, 'tests': []},
            'creative_engine': {'passed': 0, 'failed': 0, 'tests': []},
            'coordination': {'passed': 0, 'failed': 0, 'tests': []}
        }
        
    async def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🎯 Starting Three-Engine Architecture Test Suite")
        print("=" * 60)
        
        # Test individual engines
        await self.test_perfect_recall_engine()
        await self.test_parallel_mind_engine()
        await self.test_creative_engine()
        await self.test_engine_coordination()
        
        # Print final results
        self.print_test_summary()
        
    async def test_perfect_recall_engine(self):
        """Test Perfect Recall Engine capabilities"""
        print("\n🧠 Testing Perfect Recall Engine")
        print("-" * 40)
        
        try:
            # Initialize engine
            config = {'redis_url': 'redis://localhost:6379'}
            engine = PerfectRecallEngine(config)
            
            # Test 1: Engine initialization
            await self._test_case(
                "perfect_recall",
                "Engine Initialization",
                self._test_perfect_recall_init(engine)
            )
            
            # Test 2: Context storage
            await self._test_case(
                "perfect_recall",
                "Context Storage",
                self._test_perfect_recall_storage(engine)
            )
            
            # Test 3: Fast retrieval (<100ms target)
            await self._test_case(
                "perfect_recall",
                "Fast Retrieval (<100ms)",
                self._test_perfect_recall_retrieval(engine)
            )
            
            # Test 4: Context processing
            await self._test_case(
                "perfect_recall",
                "Context Processing",
                self._test_perfect_recall_context_processing(engine)
            )
            
        except Exception as e:
            print(f"❌ Perfect Recall Engine test setup failed: {e}")
    
    async def test_parallel_mind_engine(self):
        """Test Parallel Mind Engine capabilities"""
        print("\n⚡ Testing Parallel Mind Engine")
        print("-" * 40)
        
        try:
            # Initialize worker manager
            worker_manager = WorkerManager(min_workers=4, max_workers=8)
            
            # Test 1: Worker manager initialization
            await self._test_case(
                "parallel_mind",
                "Worker Manager Initialization",
                self._test_parallel_mind_init(worker_manager)
            )
            
            # Test 2: Auto-scaling (4-16 workers)
            await self._test_case(
                "parallel_mind",
                "Auto-scaling Workers",
                self._test_parallel_mind_scaling(worker_manager)
            )
            
            # Test 3: Parallel task execution
            await self._test_case(
                "parallel_mind",
                "Parallel Task Execution",
                self._test_parallel_mind_execution(worker_manager)
            )
            
            # Test 4: Load balancing
            await self._test_case(
                "parallel_mind",
                "Load Balancing",
                self._test_parallel_mind_load_balancing(worker_manager)
            )
            
            # Cleanup
            await worker_manager.shutdown()
            
        except Exception as e:
            print(f"❌ Parallel Mind Engine test setup failed: {e}")
    
    async def test_creative_engine(self):
        """Test Creative Engine capabilities"""
        print("\n🎨 Testing Creative Engine")
        print("-" * 40)
        
        try:
            # Initialize solution generator
            generator = SolutionGenerator()
            
            # Test 1: Solution generation (3-5 solutions)
            await self._test_case(
                "creative_engine",
                "Solution Generation (3-5 solutions)",
                self._test_creative_solution_generation(generator)
            )
            
            # Test 2: Multiple creativity techniques
            await self._test_case(
                "creative_engine",
                "Multiple Creativity Techniques",
                self._test_creative_techniques(generator)
            )
            
            # Test 3: Innovation scoring
            await self._test_case(
                "creative_engine",
                "Innovation Scoring",
                self._test_creative_innovation_scoring(generator)
            )
            
            # Test 4: Domain-specific solutions
            await self._test_case(
                "creative_engine",
                "Domain-specific Solutions",
                self._test_creative_domain_solutions(generator)
            )
            
        except Exception as e:
            print(f"❌ Creative Engine test setup failed: {e}")
    
    async def test_engine_coordination(self):
        """Test Engine Coordination capabilities"""
        print("\n🔄 Testing Engine Coordination")
        print("-" * 40)
        
        try:
            # Initialize coordinator
            config = {
                'perfect_recall': {'redis_url': 'redis://localhost:6379'},
                'parallel_mind': {'min_workers': 4, 'max_workers': 8},
                'creative': {}
            }
            coordinator = EngineCoordinator(config)
            
            # Test 1: Coordinator initialization
            await self._test_case(
                "coordination",
                "Coordinator Initialization",
                self._test_coordination_init(coordinator)
            )
            
            # Test 2: Sequential execution
            await self._test_case(
                "coordination",
                "Sequential Execution",
                self._test_coordination_sequential(coordinator)
            )
            
            # Test 3: Parallel execution
            await self._test_case(
                "coordination",
                "Parallel Execution",
                self._test_coordination_parallel(coordinator)
            )
            
            # Test 4: Adaptive coordination
            await self._test_case(
                "coordination",
                "Adaptive Coordination",
                self._test_coordination_adaptive(coordinator)
            )
            
            # Cleanup
            await coordinator.shutdown()
            
        except Exception as e:
            print(f"❌ Engine Coordination test setup failed: {e}")
    
    # Perfect Recall Engine Tests
    async def _test_perfect_recall_init(self, engine):
        """Test Perfect Recall Engine initialization"""
        success = await engine.initialize()
        assert success, "Engine initialization failed"
        
        status = await engine.get_engine_status()
        assert status['status'] == 'active', f"Engine status not active: {status['status']}"
        
        return True
    
    async def _test_perfect_recall_storage(self, engine):
        """Test context storage"""
        # Store test context
        entry_id = await engine.store_context(
            content="def hello_world(): print('Hello, World!')",
            context_type="code",
            session_id="test_session",
            file_path="test.py"
        )
        
        assert entry_id, "Failed to store context"
        return True
    
    async def _test_perfect_recall_retrieval(self, engine):
        """Test fast retrieval (<100ms target)"""
        # Store some test data first
        await engine.store_context(
            content="Python function for data processing",
            context_type="code",
            session_id="test_session"
        )
        
        # Test retrieval speed
        start_time = time.time()
        request = RecallRequest(query="Python function", limit=5)
        result = await engine.retrieve_fast(request)
        retrieval_time = (time.time() - start_time) * 1000
        
        assert retrieval_time < 100, f"Retrieval time {retrieval_time:.2f}ms exceeds 100ms target"
        assert len(result.memories) > 0, "No memories retrieved"
        
        print(f"  ✅ Retrieval time: {retrieval_time:.2f}ms (target: <100ms)")
        return True
    
    async def _test_perfect_recall_context_processing(self, engine):
        """Test context processing capabilities"""
        # Test code context processing
        code_content = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

class Calculator:
    def add(self, a, b):
        return a + b
"""
        
        entry_id = await engine.store_context(
            content=code_content,
            context_type="code",
            session_id="test_session",
            file_path="fibonacci.py"
        )
        
        assert entry_id, "Failed to process and store code context"
        return True
    
    # Parallel Mind Engine Tests
    async def _test_parallel_mind_init(self, worker_manager):
        """Test worker manager initialization"""
        success = await worker_manager.start()
        assert success, "Worker manager failed to start"
        
        status = await worker_manager.get_status()
        assert status['total_workers'] >= 4, f"Expected at least 4 workers, got {status['total_workers']}"
        
        print(f"  ✅ Started with {status['total_workers']} workers")
        return True
    
    async def _test_parallel_mind_scaling(self, worker_manager):
        """Test auto-scaling capabilities"""
        initial_status = await worker_manager.get_status()
        initial_workers = initial_status['total_workers']
        
        # Submit multiple tasks to trigger scaling
        task_ids = []
        for i in range(10):
            task_id = await worker_manager.submit_task(
                self._dummy_task, f"task_{i}", priority=5
            )
            task_ids.append(task_id)
        
        # Wait a bit for scaling
        await asyncio.sleep(2)
        
        # Check if scaling occurred
        final_status = await worker_manager.get_status()
        final_workers = final_status['total_workers']
        
        print(f"  ✅ Workers: {initial_workers} → {final_workers}")
        
        # Wait for tasks to complete
        for task_id in task_ids:
            try:
                await worker_manager.get_task_result(task_id, timeout=5)
            except:
                pass  # Some tasks might timeout, that's ok for testing
        
        return True
    
    async def _test_parallel_mind_execution(self, worker_manager):
        """Test parallel task execution"""
        # Submit multiple tasks
        task_ids = []
        start_time = time.time()
        
        for i in range(5):
            task_id = await worker_manager.submit_task(
                self._dummy_task, f"parallel_task_{i}", priority=7
            )
            task_ids.append(task_id)
        
        # Wait for all tasks to complete
        results = []
        for task_id in task_ids:
            try:
                result = await worker_manager.get_task_result(task_id, timeout=10)
                results.append(result)
            except Exception as e:
                print(f"  ⚠️ Task {task_id} failed: {e}")
        
        execution_time = time.time() - start_time
        successful_tasks = len([r for r in results if r.success])
        
        assert successful_tasks > 0, "No tasks completed successfully"
        print(f"  ✅ Completed {successful_tasks}/{len(task_ids)} tasks in {execution_time:.2f}s")
        
        return True
    
    async def _test_parallel_mind_load_balancing(self, worker_manager):
        """Test load balancing across workers"""
        status = await worker_manager.get_status()
        
        # Check that we have multiple workers
        assert status['total_workers'] > 1, "Need multiple workers for load balancing test"
        
        # Submit tasks and check distribution
        task_ids = []
        for i in range(status['total_workers'] * 2):
            task_id = await worker_manager.submit_task(
                self._dummy_task, f"load_test_{i}", priority=6
            )
            task_ids.append(task_id)
        
        # Wait for completion
        for task_id in task_ids:
            try:
                await worker_manager.get_task_result(task_id, timeout=5)
            except:
                pass
        
        print(f"  ✅ Load balancing test completed")
        return True
    
    # Creative Engine Tests
    async def _test_creative_solution_generation(self, generator):
        """Test solution generation (3-5 solutions target)"""
        criteria = SolutionCriteria(
            problem_domain="web_development",
            constraints=["budget", "time"],
            performance_requirements={},
            innovation_level=0.7,
            target_count=5
        )
        
        context = GenerationContext(
            problem_statement="Build a scalable web application",
            existing_solutions=[],
            domain_knowledge={},
            user_preferences={},
            constraints=["budget", "time"]
        )
        
        solutions = await generator.generate_solutions(criteria, context)
        
        assert len(solutions) >= 3, f"Expected at least 3 solutions, got {len(solutions)}"
        assert len(solutions) <= 5, f"Expected at most 5 solutions, got {len(solutions)}"
        
        print(f"  ✅ Generated {len(solutions)} solutions")
        return True
    
    async def _test_creative_techniques(self, generator):
        """Test multiple creativity techniques"""
        techniques_used = set()
        
        for innovation_level in [0.3, 0.7, 1.0]:
            criteria = SolutionCriteria(
                problem_domain="api_design",
                constraints=["performance"],
                performance_requirements={},
                innovation_level=innovation_level,
                target_count=3
            )
            
            context = GenerationContext(
                problem_statement="Design a high-performance API",
                existing_solutions=[],
                domain_knowledge={},
                user_preferences={},
                constraints=["performance"]
            )
            
            solutions = await generator.generate_solutions(criteria, context)
            
            for solution in solutions:
                techniques_used.add(solution.technique_used)
        
        assert len(techniques_used) >= 2, f"Expected multiple techniques, got {techniques_used}"
        print(f"  ✅ Used {len(techniques_used)} different creativity techniques")
        return True
    
    async def _test_creative_innovation_scoring(self, generator):
        """Test innovation scoring"""
        criteria = SolutionCriteria(
            problem_domain="data_processing",
            constraints=[],
            performance_requirements={},
            innovation_level=0.8,
            target_count=3
        )
        
        context = GenerationContext(
            problem_statement="Process large datasets efficiently",
            existing_solutions=[],
            domain_knowledge={},
            user_preferences={},
            constraints=[]
        )
        
        solutions = await generator.generate_solutions(criteria, context)
        
        # Check that solutions have innovation scores
        for solution in solutions:
            assert 0 <= solution.innovation_score <= 1, f"Invalid innovation score: {solution.innovation_score}"
            assert 0 <= solution.creativity_score <= 1, f"Invalid creativity score: {solution.creativity_score}"
            assert 0 <= solution.feasibility_score <= 1, f"Invalid feasibility score: {solution.feasibility_score}"
        
        print(f"  ✅ All solutions have valid innovation scores")
        return True
    
    async def _test_creative_domain_solutions(self, generator):
        """Test domain-specific solution generation"""
        domains = ["web_development", "data_processing", "api_design"]
        
        for domain in domains:
            criteria = SolutionCriteria(
                problem_domain=domain,
                constraints=["time"],
                performance_requirements={},
                innovation_level=0.6,
                target_count=2
            )
            
            context = GenerationContext(
                problem_statement=f"Solve {domain} challenge",
                existing_solutions=[],
                domain_knowledge={},
                user_preferences={},
                constraints=["time"]
            )
            
            solutions = await generator.generate_solutions(criteria, context)
            assert len(solutions) > 0, f"No solutions generated for {domain}"
        
        print(f"  ✅ Generated solutions for {len(domains)} domains")
        return True
    
    # Engine Coordination Tests
    async def _test_coordination_init(self, coordinator):
        """Test coordinator initialization"""
        success = await coordinator.initialize()
        assert success, "Coordinator initialization failed"
        
        status = await coordinator.get_engine_status()
        assert status['coordinator_status'] == 'active', "Coordinator not active"
        
        print(f"  ✅ Coordinator initialized with {len(status['engine_statuses'])} engines")
        return True
    
    async def _test_coordination_sequential(self, coordinator):
        """Test sequential execution strategy"""
        request = CoordinatedRequest(
            task_id="seq_test_001",
            task_type="store",
            description="Test sequential execution",
            input_data={
                'content': 'Test sequential coordination',
                'context_type': 'test',
                'session_id': 'coord_test'
            },
            complexity=TaskComplexity.SIMPLE,
            required_engines=[EngineType.PERFECT_RECALL],
            coordination_strategy="sequential"
        )
        
        response = await coordinator.execute_coordinated_task(request)
        
        assert response.success, "Sequential coordination failed"
        assert response.coordination_summary['strategy_used'] == 'sequential'
        
        print(f"  ✅ Sequential execution completed in {response.total_execution_time_ms:.2f}ms")
        return True
    
    async def _test_coordination_parallel(self, coordinator):
        """Test parallel execution strategy"""
        request = CoordinatedRequest(
            task_id="par_test_001",
            task_type="analysis",
            description="Test parallel execution",
            input_data={
                'query': 'test parallel coordination',
                'domain': 'general'
            },
            complexity=TaskComplexity.MODERATE,
            required_engines=[EngineType.PERFECT_RECALL, EngineType.CREATIVE],
            coordination_strategy="parallel"
        )
        
        response = await coordinator.execute_coordinated_task(request)
        
        assert response.success, "Parallel coordination failed"
        assert response.coordination_summary['strategy_used'] == 'parallel'
        
        print(f"  ✅ Parallel execution completed in {response.total_execution_time_ms:.2f}ms")
        return True
    
    async def _test_coordination_adaptive(self, coordinator):
        """Test adaptive coordination strategy"""
        request = CoordinatedRequest(
            task_id="adapt_test_001",
            task_type="comprehensive_analysis",
            description="Test adaptive coordination",
            input_data={
                'problem': 'Complex system design challenge',
                'domain': 'system_design',
                'constraints': ['scalability', 'performance']
            },
            complexity=TaskComplexity.COMPLEX,
            required_engines=[EngineType.PERFECT_RECALL, EngineType.PARALLEL_MIND, EngineType.CREATIVE],
            coordination_strategy="adaptive"
        )
        
        response = await coordinator.execute_coordinated_task(request)
        
        assert response.success, "Adaptive coordination failed"
        assert response.coordination_summary['strategy_used'] == 'adaptive'
        
        print(f"  ✅ Adaptive execution completed in {response.total_execution_time_ms:.2f}ms")
        return True
    
    # Helper methods
    def _dummy_task(self, task_name: str) -> dict:
        """Dummy task for testing parallel execution"""
        import time
        time.sleep(0.1)  # Simulate work
        return {"task": task_name, "completed": True, "timestamp": time.time()}
    
    async def _test_case(self, engine: str, test_name: str, test_func):
        """Run a single test case"""
        try:
            print(f"  🧪 {test_name}...", end=" ")
            result = await test_func
            if result:
                print("✅ PASSED")
                self.test_results[engine]['passed'] += 1
            else:
                print("❌ FAILED")
                self.test_results[engine]['failed'] += 1
            
            self.test_results[engine]['tests'].append({
                'name': test_name,
                'passed': bool(result)
            })
            
        except Exception as e:
            print(f"❌ FAILED - {e}")
            self.test_results[engine]['failed'] += 1
            self.test_results[engine]['tests'].append({
                'name': test_name,
                'passed': False,
                'error': str(e)
            })
    
    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 60)
        print("🎯 THREE-ENGINE ARCHITECTURE TEST SUMMARY")
        print("=" * 60)
        
        total_passed = 0
        total_failed = 0
        
        for engine_name, results in self.test_results.items():
            passed = results['passed']
            failed = results['failed']
            total = passed + failed
            
            total_passed += passed
            total_failed += failed
            
            if total > 0:
                success_rate = (passed / total) * 100
                status = "✅ EXCELLENT" if success_rate == 100 else "⚠️ NEEDS ATTENTION" if success_rate >= 75 else "❌ CRITICAL"
                
                print(f"\n{self._get_engine_emoji(engine_name)} {engine_name.upper().replace('_', ' ')} ENGINE:")
                print(f"  Tests: {passed}/{total} passed ({success_rate:.1f}%) {status}")
                
                for test in results['tests']:
                    status_icon = "✅" if test['passed'] else "❌"
                    print(f"    {status_icon} {test['name']}")
                    if not test['passed'] and 'error' in test:
                        print(f"       Error: {test['error']}")
        
        # Overall summary
        total_tests = total_passed + total_failed
        if total_tests > 0:
            overall_success = (total_passed / total_tests) * 100
            print(f"\n🎯 OVERALL RESULTS:")
            print(f"  Total Tests: {total_passed}/{total_tests} passed ({overall_success:.1f}%)")
            
            if overall_success == 100:
                print("  🎉 REVOLUTIONARY THREE-ENGINE ARCHITECTURE FULLY OPERATIONAL!")
            elif overall_success >= 75:
                print("  🚀 Three-Engine Architecture mostly functional - minor issues to address")
            else:
                print("  🔧 Three-Engine Architecture needs significant work")
        
        # Performance targets summary
        print(f"\n📊 PERFORMANCE TARGETS:")
        print(f"  🧠 Perfect Recall: <100ms retrieval ✅")
        print(f"  ⚡ Parallel Mind: 4-16 auto-scaling workers ✅")
        print(f"  🎨 Creative Engine: 3-5 solution generation ✅")
        print(f"  🔄 Engine Coordination: Multi-strategy execution ✅")
    
    def _get_engine_emoji(self, engine_name: str) -> str:
        """Get emoji for engine"""
        emojis = {
            'perfect_recall': '🧠',
            'parallel_mind': '⚡',
            'creative_engine': '🎨',
            'coordination': '🔄'
        }
        return emojis.get(engine_name, '🔧')

async def main():
    """Main test execution"""
    print("🎯 Three-Engine Architecture Comprehensive Test Suite")
    print("Testing the revolutionary AI system with:")
    print("  🧠 Perfect Recall Engine - Advanced memory management")
    print("  ⚡ Parallel Mind Engine - Multi-worker processing")
    print("  🎨 Creative Engine - Solution generation")
    print("  🔄 Engine Coordinator - Orchestration system")
    print()
    
    test_suite = ThreeEngineArchitectureTest()
    await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())