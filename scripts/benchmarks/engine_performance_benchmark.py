#!/usr/bin/env python3
"""
📊 Three-Engine Architecture Performance Benchmark Suite

Comprehensive benchmarking system for measuring and optimizing
the performance of all three engines under various load conditions.
"""

import asyncio
import time
import statistics
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
import concurrent.futures
import psutil
import aiohttp

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from revoagent.engines.perfect_recall import PerfectRecallEngine, RecallRequest
from revoagent.engines.parallel_mind.worker_manager import WorkerManager
from revoagent.engines.creative_engine import CreativeEngine
from revoagent.engines.engine_coordinator import EngineCoordinator

@dataclass
class BenchmarkResult:
    """Result from a single benchmark test"""
    test_name: str
    engine: str
    duration_ms: float
    success: bool
    throughput: float
    latency_p50: float
    latency_p95: float
    latency_p99: float
    error_rate: float
    resource_usage: Dict[str, float]
    metadata: Dict[str, Any]

@dataclass
class BenchmarkSuite:
    """Complete benchmark suite results"""
    timestamp: str
    total_duration_sec: float
    results: List[BenchmarkResult]
    summary: Dict[str, Any]
    recommendations: List[str]

class EnginePerformanceBenchmark:
    """Comprehensive performance benchmarking for Three-Engine Architecture"""
    
    def __init__(self):
        self.results: List[BenchmarkResult] = []
        self.engines = {}
        self.test_data = self._generate_test_data()
        
    def _generate_test_data(self) -> Dict[str, Any]:
        """Generate comprehensive test data for benchmarks"""
        return {
            "perfect_recall": {
                "contexts": [
                    {
                        "content": f"def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)\n\n# Test case {i}",
                        "context_type": "code",
                        "session_id": f"benchmark_session_{i % 10}",
                        "expected_results": 1
                    }
                    for i in range(100)
                ],
                "queries": [
                    "fibonacci function",
                    "recursive algorithm",
                    "python code",
                    "mathematical function",
                    "dynamic programming"
                ] * 20
            },
            "parallel_mind": {
                "workloads": [
                    {
                        "tasks": [
                            {"type": "cpu_intensive", "duration": 0.1, "complexity": "low"},
                            {"type": "io_intensive", "duration": 0.2, "complexity": "medium"},
                            {"type": "memory_intensive", "duration": 0.15, "complexity": "high"}
                        ] * (10 + i)
                    }
                    for i in range(10)
                ]
            },
            "creative_engine": {
                "challenges": [
                    {
                        "problem": f"Design a scalable web application for {domain}",
                        "domain": domain,
                        "constraints": ["budget", "time", "scalability"],
                        "innovation_level": 0.7 + (i * 0.05)
                    }
                    for i, domain in enumerate(["e-commerce", "healthcare", "education", "finance", "gaming"])
                ] * 4
            }
        }
    
    async def run_comprehensive_benchmark(self) -> BenchmarkSuite:
        """Run complete benchmark suite"""
        print("🚀 Starting Three-Engine Architecture Performance Benchmark")
        print("=" * 70)
        
        start_time = time.time()
        
        # Initialize engines
        await self._initialize_engines()
        
        # Run benchmarks for each engine
        await self._benchmark_perfect_recall()
        await self._benchmark_parallel_mind()
        await self._benchmark_creative_engine()
        await self._benchmark_engine_coordination()
        
        # Run stress tests
        await self._run_stress_tests()
        
        # Generate comprehensive report
        total_duration = time.time() - start_time
        suite_result = self._generate_benchmark_suite(total_duration)
        
        # Cleanup
        await self._cleanup_engines()
        
        return suite_result
    
    async def _initialize_engines(self):
        """Initialize all engines for benchmarking"""
        print("🔧 Initializing engines...")
        
        # Perfect Recall Engine
        self.engines['perfect_recall'] = PerfectRecallEngine({
            'redis_url': 'redis://localhost:6379'
        })
        await self.engines['perfect_recall'].initialize()
        
        # Parallel Mind Engine
        self.engines['parallel_mind'] = WorkerManager(min_workers=4, max_workers=16)
        await self.engines['parallel_mind'].start()
        
        # Creative Engine
        self.engines['creative_engine'] = CreativeEngine({})
        
        # Engine Coordinator
        self.engines['coordinator'] = EngineCoordinator({
            'perfect_recall': {'redis_url': 'redis://localhost:6379'},
            'parallel_mind': {'min_workers': 4, 'max_workers': 16},
            'creative': {}
        })
        await self.engines['coordinator'].initialize()
        
        print("✅ All engines initialized")
    
    async def _benchmark_perfect_recall(self):
        """Benchmark Perfect Recall Engine performance"""
        print("\n🧠 Benchmarking Perfect Recall Engine...")
        
        engine = self.engines['perfect_recall']
        test_data = self.test_data['perfect_recall']
        
        # Test 1: Storage Performance
        await self._test_storage_performance(engine, test_data['contexts'])
        
        # Test 2: Retrieval Performance (<100ms target)
        await self._test_retrieval_performance(engine, test_data['queries'])
        
        # Test 3: Concurrent Access
        await self._test_concurrent_retrieval(engine, test_data['queries'])
        
        # Test 4: Memory Usage Under Load
        await self._test_memory_scaling(engine, test_data['contexts'])
    
    async def _test_storage_performance(self, engine, contexts: List[Dict]):
        """Test context storage performance"""
        print("  📝 Testing storage performance...")
        
        start_time = time.time()
        storage_times = []
        errors = 0
        
        for context in contexts[:50]:  # Test with 50 contexts
            try:
                context_start = time.time()
                await engine.store_context(
                    content=context['content'],
                    context_type=context['context_type'],
                    session_id=context['session_id']
                )
                storage_time = (time.time() - context_start) * 1000
                storage_times.append(storage_time)
            except Exception as e:
                errors += 1
                print(f"    ⚠️ Storage error: {e}")
        
        total_time = (time.time() - start_time) * 1000
        
        result = BenchmarkResult(
            test_name="storage_performance",
            engine="perfect_recall",
            duration_ms=total_time,
            success=errors == 0,
            throughput=len(storage_times) / (total_time / 1000),
            latency_p50=statistics.median(storage_times) if storage_times else 0,
            latency_p95=self._percentile(storage_times, 0.95) if storage_times else 0,
            latency_p99=self._percentile(storage_times, 0.99) if storage_times else 0,
            error_rate=errors / len(contexts[:50]),
            resource_usage=self._get_resource_usage(),
            metadata={"contexts_stored": len(storage_times), "errors": errors}
        )
        
        self.results.append(result)
        print(f"    ✅ Storage: {result.throughput:.1f} contexts/sec, P95: {result.latency_p95:.1f}ms")
    
    async def _test_retrieval_performance(self, engine, queries: List[str]):
        """Test retrieval performance with <100ms target"""
        print("  🔍 Testing retrieval performance (<100ms target)...")
        
        retrieval_times = []
        errors = 0
        sub_100ms_count = 0
        
        for query in queries[:50]:  # Test with 50 queries
            try:
                start_time = time.time()
                request = RecallRequest(query=query, limit=10)
                result = await engine.retrieve_fast(request)
                retrieval_time = (time.time() - start_time) * 1000
                
                retrieval_times.append(retrieval_time)
                if retrieval_time < 100:
                    sub_100ms_count += 1
                    
            except Exception as e:
                errors += 1
                print(f"    ⚠️ Retrieval error: {e}")
        
        sub_100ms_rate = sub_100ms_count / len(retrieval_times) if retrieval_times else 0
        
        result = BenchmarkResult(
            test_name="retrieval_performance",
            engine="perfect_recall",
            duration_ms=sum(retrieval_times),
            success=sub_100ms_rate >= 0.95,  # 95% should be under 100ms
            throughput=len(retrieval_times) / (sum(retrieval_times) / 1000),
            latency_p50=statistics.median(retrieval_times) if retrieval_times else 0,
            latency_p95=self._percentile(retrieval_times, 0.95) if retrieval_times else 0,
            latency_p99=self._percentile(retrieval_times, 0.99) if retrieval_times else 0,
            error_rate=errors / len(queries[:50]),
            resource_usage=self._get_resource_usage(),
            metadata={
                "sub_100ms_rate": sub_100ms_rate,
                "target_met": sub_100ms_rate >= 0.95,
                "queries_tested": len(retrieval_times)
            }
        )
        
        self.results.append(result)
        print(f"    ✅ Retrieval: {sub_100ms_rate*100:.1f}% under 100ms, P95: {result.latency_p95:.1f}ms")
    
    async def _test_concurrent_retrieval(self, engine, queries: List[str]):
        """Test concurrent retrieval performance"""
        print("  🔄 Testing concurrent retrieval...")
        
        async def single_retrieval(query: str) -> float:
            start_time = time.time()
            try:
                request = RecallRequest(query=query, limit=5)
                await engine.retrieve_fast(request)
                return (time.time() - start_time) * 1000
            except Exception:
                return -1  # Error indicator
        
        # Run 20 concurrent retrievals
        start_time = time.time()
        tasks = [single_retrieval(query) for query in queries[:20]]
        retrieval_times = await asyncio.gather(*tasks)
        
        # Filter out errors
        valid_times = [t for t in retrieval_times if t > 0]
        errors = len(retrieval_times) - len(valid_times)
        total_time = (time.time() - start_time) * 1000
        
        result = BenchmarkResult(
            test_name="concurrent_retrieval",
            engine="perfect_recall",
            duration_ms=total_time,
            success=errors == 0,
            throughput=len(valid_times) / (total_time / 1000),
            latency_p50=statistics.median(valid_times) if valid_times else 0,
            latency_p95=self._percentile(valid_times, 0.95) if valid_times else 0,
            latency_p99=self._percentile(valid_times, 0.99) if valid_times else 0,
            error_rate=errors / len(retrieval_times),
            resource_usage=self._get_resource_usage(),
            metadata={"concurrent_requests": 20, "errors": errors}
        )
        
        self.results.append(result)
        print(f"    ✅ Concurrent: {result.throughput:.1f} req/sec, P95: {result.latency_p95:.1f}ms")
    
    async def _benchmark_parallel_mind(self):
        """Benchmark Parallel Mind Engine performance"""
        print("\n⚡ Benchmarking Parallel Mind Engine...")
        
        engine = self.engines['parallel_mind']
        
        # Test 1: Worker Scaling
        await self._test_worker_scaling(engine)
        
        # Test 2: Task Throughput
        await self._test_task_throughput(engine)
        
        # Test 3: Load Balancing
        await self._test_load_balancing(engine)
    
    async def _test_worker_scaling(self, engine):
        """Test auto-scaling performance"""
        print("  📈 Testing worker auto-scaling...")
        
        initial_workers = (await engine.get_status())['total_workers']
        
        # Submit burst of tasks to trigger scaling
        start_time = time.time()
        task_ids = []
        
        for i in range(50):
            task_id = await engine.submit_task(self._cpu_intensive_task, f"scale_test_{i}")
            task_ids.append(task_id)
        
        # Wait for scaling to occur
        await asyncio.sleep(5)
        
        final_workers = (await engine.get_status())['total_workers']
        scaling_time = (time.time() - start_time) * 1000
        
        # Wait for tasks to complete
        completed = 0
        for task_id in task_ids:
            try:
                await engine.get_task_result(task_id, timeout=10)
                completed += 1
            except:
                pass
        
        result = BenchmarkResult(
            test_name="worker_scaling",
            engine="parallel_mind",
            duration_ms=scaling_time,
            success=final_workers > initial_workers,
            throughput=completed / (scaling_time / 1000),
            latency_p50=scaling_time,
            latency_p95=scaling_time,
            latency_p99=scaling_time,
            error_rate=(len(task_ids) - completed) / len(task_ids),
            resource_usage=self._get_resource_usage(),
            metadata={
                "initial_workers": initial_workers,
                "final_workers": final_workers,
                "scaling_factor": final_workers / initial_workers if initial_workers > 0 else 1,
                "tasks_completed": completed
            }
        )
        
        self.results.append(result)
        print(f"    ✅ Scaling: {initial_workers} → {final_workers} workers, {completed} tasks completed")
    
    async def _benchmark_creative_engine(self):
        """Benchmark Creative Engine performance"""
        print("\n🎨 Benchmarking Creative Engine...")
        
        engine = self.engines['creative_engine']
        test_data = self.test_data['creative_engine']
        
        # Test 1: Solution Generation Performance
        await self._test_solution_generation(engine, test_data['challenges'])
        
        # Test 2: Innovation Quality
        await self._test_innovation_quality(engine, test_data['challenges'])
    
    async def _test_solution_generation(self, engine, challenges: List[Dict]):
        """Test solution generation performance"""
        print("  🎯 Testing solution generation performance...")
        
        generation_times = []
        solution_counts = []
        errors = 0
        
        for challenge in challenges[:10]:  # Test with 10 challenges
            try:
                start_time = time.time()
                solutions = await engine.generate_creative_solutions(
                    problem_statement=challenge['problem'],
                    domain=challenge['domain'],
                    constraints=challenge['constraints'],
                    innovation_level=challenge['innovation_level']
                )
                generation_time = (time.time() - start_time) * 1000
                
                generation_times.append(generation_time)
                solution_counts.append(len(solutions))
                
            except Exception as e:
                errors += 1
                print(f"    ⚠️ Generation error: {e}")
        
        avg_solutions = statistics.mean(solution_counts) if solution_counts else 0
        target_met = avg_solutions >= 3 and avg_solutions <= 5
        
        result = BenchmarkResult(
            test_name="solution_generation",
            engine="creative_engine",
            duration_ms=sum(generation_times),
            success=target_met and errors == 0,
            throughput=len(generation_times) / (sum(generation_times) / 1000),
            latency_p50=statistics.median(generation_times) if generation_times else 0,
            latency_p95=self._percentile(generation_times, 0.95) if generation_times else 0,
            latency_p99=self._percentile(generation_times, 0.99) if generation_times else 0,
            error_rate=errors / len(challenges[:10]),
            resource_usage=self._get_resource_usage(),
            metadata={
                "avg_solutions_per_request": avg_solutions,
                "target_range_met": target_met,
                "challenges_tested": len(generation_times)
            }
        )
        
        self.results.append(result)
        print(f"    ✅ Generation: {avg_solutions:.1f} solutions/request, P95: {result.latency_p95:.1f}ms")
    
    async def _benchmark_engine_coordination(self):
        """Benchmark engine coordination performance"""
        print("\n🔄 Benchmarking Engine Coordination...")
        
        coordinator = self.engines['coordinator']
        
        # Test coordination strategies
        await self._test_coordination_strategies(coordinator)
    
    async def _test_coordination_strategies(self, coordinator):
        """Test different coordination strategies"""
        print("  🎭 Testing coordination strategies...")
        
        from revoagent.engines.engine_coordinator import CoordinatedRequest, TaskComplexity, EngineType
        
        strategies = ["sequential", "parallel", "adaptive"]
        strategy_results = {}
        
        for strategy in strategies:
            print(f"    Testing {strategy} strategy...")
            
            request = CoordinatedRequest(
                task_id=f"benchmark_{strategy}",
                task_type="analysis",
                description=f"Benchmark {strategy} coordination",
                input_data={
                    'query': 'test coordination performance',
                    'domain': 'general'
                },
                complexity=TaskComplexity.MODERATE,
                required_engines=[EngineType.PERFECT_RECALL, EngineType.CREATIVE],
                coordination_strategy=strategy
            )
            
            start_time = time.time()
            try:
                response = await coordinator.execute_coordinated_task(request)
                execution_time = (time.time() - start_time) * 1000
                
                strategy_results[strategy] = {
                    "execution_time_ms": execution_time,
                    "success": response.success,
                    "engines_used": len(response.engine_responses)
                }
                
            except Exception as e:
                strategy_results[strategy] = {
                    "execution_time_ms": (time.time() - start_time) * 1000,
                    "success": False,
                    "error": str(e)
                }
        
        # Create result for coordination benchmark
        avg_time = statistics.mean([r["execution_time_ms"] for r in strategy_results.values()])
        success_rate = sum(1 for r in strategy_results.values() if r["success"]) / len(strategies)
        
        result = BenchmarkResult(
            test_name="coordination_strategies",
            engine="coordinator",
            duration_ms=avg_time,
            success=success_rate >= 0.8,
            throughput=len(strategies) / (avg_time / 1000),
            latency_p50=avg_time,
            latency_p95=max(r["execution_time_ms"] for r in strategy_results.values()),
            latency_p99=max(r["execution_time_ms"] for r in strategy_results.values()),
            error_rate=1 - success_rate,
            resource_usage=self._get_resource_usage(),
            metadata={"strategy_results": strategy_results}
        )
        
        self.results.append(result)
        print(f"    ✅ Coordination: {success_rate*100:.0f}% success rate, avg: {avg_time:.1f}ms")
    
    async def _run_stress_tests(self):
        """Run stress tests on all engines"""
        print("\n🔥 Running stress tests...")
        
        # Stress test Perfect Recall with high query volume
        await self._stress_test_perfect_recall()
        
        # Stress test Parallel Mind with task bursts
        await self._stress_test_parallel_mind()
    
    async def _stress_test_perfect_recall(self):
        """Stress test Perfect Recall Engine"""
        print("  🧠 Stress testing Perfect Recall...")
        
        engine = self.engines['perfect_recall']
        
        # Generate high volume of concurrent queries
        async def stress_query(query_id: int) -> Tuple[float, bool]:
            try:
                start_time = time.time()
                request = RecallRequest(query=f"stress test query {query_id}", limit=5)
                await engine.retrieve_fast(request)
                return (time.time() - start_time) * 1000, True
            except Exception:
                return 0, False
        
        # Run 100 concurrent queries
        start_time = time.time()
        tasks = [stress_query(i) for i in range(100)]
        results = await asyncio.gather(*tasks)
        
        times = [r[0] for r in results if r[1]]
        errors = len([r for r in results if not r[1]])
        total_time = (time.time() - start_time) * 1000
        
        result = BenchmarkResult(
            test_name="stress_test_retrieval",
            engine="perfect_recall",
            duration_ms=total_time,
            success=len(times) >= 90,  # 90% success rate
            throughput=len(times) / (total_time / 1000),
            latency_p50=statistics.median(times) if times else 0,
            latency_p95=self._percentile(times, 0.95) if times else 0,
            latency_p99=self._percentile(times, 0.99) if times else 0,
            error_rate=errors / 100,
            resource_usage=self._get_resource_usage(),
            metadata={"concurrent_queries": 100, "errors": errors}
        )
        
        self.results.append(result)
        print(f"    ✅ Stress test: {len(times)}/100 successful, P95: {result.latency_p95:.1f}ms")
    
    def _cpu_intensive_task(self, task_name: str) -> Dict[str, Any]:
        """CPU intensive task for testing"""
        import time
        start = time.time()
        
        # Simulate CPU work
        total = 0
        for i in range(100000):
            total += i * i
        
        return {
            "task": task_name,
            "result": total,
            "duration": time.time() - start
        }
    
    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile of data"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def _get_resource_usage(self) -> Dict[str, float]:
        """Get current resource usage"""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "memory_used_gb": psutil.virtual_memory().used / (1024**3)
            }
        except Exception:
            return {"cpu_percent": 0, "memory_percent": 0, "memory_used_gb": 0}
    
    def _generate_benchmark_suite(self, total_duration: float) -> BenchmarkSuite:
        """Generate comprehensive benchmark suite results"""
        
        # Calculate summary statistics
        summary = {
            "total_tests": len(self.results),
            "successful_tests": len([r for r in self.results if r.success]),
            "overall_success_rate": len([r for r in self.results if r.success]) / len(self.results) if self.results else 0,
            "avg_throughput": statistics.mean([r.throughput for r in self.results if r.throughput > 0]),
            "avg_latency_p95": statistics.mean([r.latency_p95 for r in self.results if r.latency_p95 > 0]),
            "engine_performance": self._calculate_engine_performance()
        }
        
        # Generate recommendations
        recommendations = self._generate_recommendations()
        
        return BenchmarkSuite(
            timestamp=datetime.now().isoformat(),
            total_duration_sec=total_duration,
            results=self.results,
            summary=summary,
            recommendations=recommendations
        )
    
    def _calculate_engine_performance(self) -> Dict[str, Dict[str, float]]:
        """Calculate performance metrics per engine"""
        engine_performance = {}
        
        for engine in ["perfect_recall", "parallel_mind", "creative_engine", "coordinator"]:
            engine_results = [r for r in self.results if r.engine == engine]
            if engine_results:
                engine_performance[engine] = {
                    "success_rate": len([r for r in engine_results if r.success]) / len(engine_results),
                    "avg_throughput": statistics.mean([r.throughput for r in engine_results if r.throughput > 0]),
                    "avg_latency_p95": statistics.mean([r.latency_p95 for r in engine_results if r.latency_p95 > 0]),
                    "avg_error_rate": statistics.mean([r.error_rate for r in engine_results])
                }
        
        return engine_performance
    
    def _generate_recommendations(self) -> List[str]:
        """Generate performance improvement recommendations"""
        recommendations = []
        
        # Perfect Recall recommendations
        pr_results = [r for r in self.results if r.engine == "perfect_recall"]
        if pr_results:
            avg_retrieval_time = statistics.mean([r.latency_p95 for r in pr_results if "retrieval" in r.test_name])
            if avg_retrieval_time > 100:
                recommendations.append("🧠 Perfect Recall: Consider Redis cluster optimization for <100ms target")
            
            sub_100ms_tests = [r for r in pr_results if "retrieval" in r.test_name and r.metadata.get("sub_100ms_rate", 0) < 0.95]
            if sub_100ms_tests:
                recommendations.append("🧠 Perfect Recall: Optimize vector embeddings for faster similarity search")
        
        # Parallel Mind recommendations
        pm_results = [r for r in self.results if r.engine == "parallel_mind"]
        if pm_results:
            scaling_results = [r for r in pm_results if "scaling" in r.test_name]
            if scaling_results and not all(r.success for r in scaling_results):
                recommendations.append("⚡ Parallel Mind: Tune auto-scaling parameters for better responsiveness")
        
        # Creative Engine recommendations
        ce_results = [r for r in self.results if r.engine == "creative_engine"]
        if ce_results:
            generation_results = [r for r in ce_results if "generation" in r.test_name]
            if generation_results:
                avg_solutions = statistics.mean([r.metadata.get("avg_solutions_per_request", 0) for r in generation_results])
                if avg_solutions < 3:
                    recommendations.append("🎨 Creative Engine: Increase solution generation count for better diversity")
        
        # General recommendations
        overall_success = len([r for r in self.results if r.success]) / len(self.results) if self.results else 0
        if overall_success < 0.9:
            recommendations.append("🔧 General: Consider increasing resource allocation for better reliability")
        
        return recommendations
    
    async def _cleanup_engines(self):
        """Cleanup all engines"""
        print("\n🧹 Cleaning up engines...")
        
        try:
            if 'parallel_mind' in self.engines:
                await self.engines['parallel_mind'].shutdown()
            
            if 'coordinator' in self.engines:
                await self.engines['coordinator'].shutdown()
                
        except Exception as e:
            print(f"Cleanup error: {e}")

async def main():
    """Main benchmark execution"""
    print("🎯 Three-Engine Architecture Performance Benchmark Suite")
    print("Testing revolutionary AI system performance under load")
    print()
    
    benchmark = EnginePerformanceBenchmark()
    
    try:
        # Run comprehensive benchmark
        suite_result = await benchmark.run_comprehensive_benchmark()
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"benchmark_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(asdict(suite_result), f, indent=2, default=str)
        
        # Print summary
        print("\n" + "=" * 70)
        print("📊 BENCHMARK RESULTS SUMMARY")
        print("=" * 70)
        
        summary = suite_result.summary
        print(f"Total Duration: {suite_result.total_duration_sec:.1f} seconds")
        print(f"Tests Run: {summary['total_tests']}")
        print(f"Success Rate: {summary['overall_success_rate']*100:.1f}%")
        print(f"Average Throughput: {summary['avg_throughput']:.1f} ops/sec")
        print(f"Average P95 Latency: {summary['avg_latency_p95']:.1f}ms")
        
        print(f"\n🎯 ENGINE PERFORMANCE:")
        for engine, metrics in summary['engine_performance'].items():
            print(f"  {engine}: {metrics['success_rate']*100:.0f}% success, {metrics['avg_latency_p95']:.1f}ms P95")
        
        print(f"\n💡 RECOMMENDATIONS:")
        for rec in suite_result.recommendations:
            print(f"  • {rec}")
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        
    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())