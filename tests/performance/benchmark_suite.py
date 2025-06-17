#!/usr/bin/env python3
"""
Performance Benchmarking Suite for reVoAgent

Comprehensive performance testing including:
- Load testing with concurrent requests
- Memory usage profiling
- Response time analysis
- Throughput measurement
- Resource utilization monitoring
- Stress testing scenarios
"""

import asyncio
import time
import statistics
import sys
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import json
import psutil
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from packages.core.logging_config import setup_logging, get_logger

logger = get_logger(__name__)


@dataclass
class BenchmarkResult:
    """Benchmark test result."""
    test_name: str
    duration: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    requests_per_second: float
    errors: List[str] = field(default_factory=list)
    memory_usage: Dict[str, float] = field(default_factory=dict)
    cpu_usage: float = 0.0


class SimpleBenchmarkSuite:
    """Simplified benchmark suite for testing core services."""
    
    def __init__(self):
        self.results = []
        setup_logging(log_level="INFO", enable_console=True, enable_json=False)
    
    async def run_service_benchmarks(self) -> List[BenchmarkResult]:
        """Run benchmarks for core services."""
        logger.info("🚀 Starting service benchmark suite")
        
        # Import services
        from packages.core.secret_manager import SecretManager, SecretConfig, SecretProvider
        from packages.core.rate_limiter import RateLimiter, InMemoryStorage, RateLimitRule, RateLimitAlgorithm
        from packages.core.circuit_breaker import CircuitBreaker, CircuitBreakerConfig
        
        # Setup test environment
        import tempfile
        temp_dir = tempfile.mkdtemp()
        secrets_file = os.path.join(temp_dir, 'test_secrets.json')
        
        secrets = {'test-secret': 'test-value', 'api-key': 'test-api-key'}
        with open(secrets_file, 'w') as f:
            json.dump(secrets, f)
        
        try:
            # Test 1: Secret Manager Performance
            result = await self._benchmark_secret_manager(secrets_file)
            self.results.append(result)
            
            # Test 2: Rate Limiter Performance
            result = await self._benchmark_rate_limiter()
            self.results.append(result)
            
            # Test 3: Circuit Breaker Performance
            result = await self._benchmark_circuit_breaker()
            self.results.append(result)
            
            # Test 4: Combined Service Performance
            result = await self._benchmark_combined_services(secrets_file)
            self.results.append(result)
            
        finally:
            # Cleanup
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        
        self._generate_summary_report()
        return self.results
    
    async def _benchmark_secret_manager(self, secrets_file: str) -> BenchmarkResult:
        """Benchmark secret manager performance."""
        logger.info("Testing Secret Manager performance...")
        
        from packages.core.secret_manager import SecretManager, SecretConfig, SecretProvider
        
        config = SecretConfig(
            provider=SecretProvider.LOCAL_FILE,
            local_secrets_file=secrets_file
        )
        secret_manager = SecretManager(config)
        await secret_manager.initialize()
        
        # Benchmark parameters
        num_requests = 1000
        start_time = time.time()
        successful = 0
        failed = 0
        response_times = []
        
        # Monitor system resources
        process = psutil.Process()
        start_memory = process.memory_info().rss / (1024**2)  # MB
        start_cpu = process.cpu_percent()
        
        # Run benchmark
        for i in range(num_requests):
            request_start = time.time()
            try:
                secret = await secret_manager.get_secret('test-secret')
                if secret == 'test-value':
                    successful += 1
                else:
                    failed += 1
                response_time = time.time() - request_start
                response_times.append(response_time)
            except Exception as e:
                failed += 1
                response_times.append(time.time() - request_start)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Calculate final resource usage
        end_memory = process.memory_info().rss / (1024**2)  # MB
        end_cpu = process.cpu_percent()
        
        return BenchmarkResult(
            test_name="secret_manager_performance",
            duration=duration,
            total_requests=num_requests,
            successful_requests=successful,
            failed_requests=failed,
            avg_response_time=statistics.mean(response_times) if response_times else 0,
            min_response_time=min(response_times) if response_times else 0,
            max_response_time=max(response_times) if response_times else 0,
            requests_per_second=num_requests / duration,
            memory_usage={'start_mb': start_memory, 'end_mb': end_memory, 'delta_mb': end_memory - start_memory},
            cpu_usage=(start_cpu + end_cpu) / 2
        )
    
    async def _benchmark_rate_limiter(self) -> BenchmarkResult:
        """Benchmark rate limiter performance."""
        logger.info("Testing Rate Limiter performance...")
        
        from packages.core.rate_limiter import RateLimiter, InMemoryStorage, RateLimitRule, RateLimitAlgorithm
        
        storage = InMemoryStorage()
        rule = RateLimitRule(
            name='benchmark-test',
            requests=1000,  # High limit for benchmark
            window_seconds=60,
            algorithm=RateLimitAlgorithm.SLIDING_WINDOW
        )
        rate_limiter = RateLimiter(storage, [rule])
        
        # Benchmark parameters
        num_requests = 1000
        start_time = time.time()
        successful = 0
        failed = 0
        response_times = []
        
        # Monitor system resources
        process = psutil.Process()
        start_memory = process.memory_info().rss / (1024**2)  # MB
        
        # Run benchmark
        for i in range(num_requests):
            request_start = time.time()
            try:
                result = await rate_limiter.check_rate_limit('benchmark-test', f'user-{i}')
                if result.allowed:
                    successful += 1
                else:
                    failed += 1
                response_time = time.time() - request_start
                response_times.append(response_time)
            except Exception as e:
                failed += 1
                response_times.append(time.time() - request_start)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Calculate final resource usage
        end_memory = process.memory_info().rss / (1024**2)  # MB
        
        return BenchmarkResult(
            test_name="rate_limiter_performance",
            duration=duration,
            total_requests=num_requests,
            successful_requests=successful,
            failed_requests=failed,
            avg_response_time=statistics.mean(response_times) if response_times else 0,
            min_response_time=min(response_times) if response_times else 0,
            max_response_time=max(response_times) if response_times else 0,
            requests_per_second=num_requests / duration,
            memory_usage={'start_mb': start_memory, 'end_mb': end_memory, 'delta_mb': end_memory - start_memory}
        )
    
    async def _benchmark_circuit_breaker(self) -> BenchmarkResult:
        """Benchmark circuit breaker performance."""
        logger.info("Testing Circuit Breaker performance...")
        
        from packages.core.circuit_breaker import CircuitBreaker, CircuitBreakerConfig
        
        config = CircuitBreakerConfig(
            name='benchmark-service',
            failure_threshold=100,  # High threshold for benchmark
            recovery_timeout=60
        )
        circuit_breaker = CircuitBreaker(config)
        
        # Benchmark parameters
        num_requests = 500
        start_time = time.time()
        successful = 0
        failed = 0
        response_times = []
        
        # Monitor system resources
        process = psutil.Process()
        start_memory = process.memory_info().rss / (1024**2)  # MB
        
        # Mock service function
        async def mock_service():
            await asyncio.sleep(0.001)  # 1ms simulated work
            return "success"
        
        # Run benchmark
        for i in range(num_requests):
            request_start = time.time()
            try:
                result = await circuit_breaker.call(mock_service)
                if result == "success":
                    successful += 1
                else:
                    failed += 1
                response_time = time.time() - request_start
                response_times.append(response_time)
            except Exception as e:
                failed += 1
                response_times.append(time.time() - request_start)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Calculate final resource usage
        end_memory = process.memory_info().rss / (1024**2)  # MB
        
        return BenchmarkResult(
            test_name="circuit_breaker_performance",
            duration=duration,
            total_requests=num_requests,
            successful_requests=successful,
            failed_requests=failed,
            avg_response_time=statistics.mean(response_times) if response_times else 0,
            min_response_time=min(response_times) if response_times else 0,
            max_response_time=max(response_times) if response_times else 0,
            requests_per_second=num_requests / duration,
            memory_usage={'start_mb': start_memory, 'end_mb': end_memory, 'delta_mb': end_memory - start_memory}
        )
    
    async def _benchmark_combined_services(self, secrets_file: str) -> BenchmarkResult:
        """Benchmark combined service performance."""
        logger.info("Testing Combined Services performance...")
        
        from packages.core.secret_manager import SecretManager, SecretConfig, SecretProvider
        from packages.core.rate_limiter import RateLimiter, InMemoryStorage, RateLimitRule, RateLimitAlgorithm
        from packages.core.circuit_breaker import CircuitBreaker, CircuitBreakerConfig
        
        # Setup services
        secret_config = SecretConfig(
            provider=SecretProvider.LOCAL_FILE,
            local_secrets_file=secrets_file
        )
        secret_manager = SecretManager(secret_config)
        await secret_manager.initialize()
        
        storage = InMemoryStorage()
        rule = RateLimitRule(
            name='combined-test',
            requests=500,
            window_seconds=60,
            algorithm=RateLimitAlgorithm.TOKEN_BUCKET
        )
        rate_limiter = RateLimiter(storage, [rule])
        
        circuit_config = CircuitBreakerConfig(
            name='combined-service',
            failure_threshold=50,
            recovery_timeout=30
        )
        circuit_breaker = CircuitBreaker(circuit_config)
        
        # Benchmark parameters
        num_requests = 200
        start_time = time.time()
        successful = 0
        failed = 0
        response_times = []
        
        # Monitor system resources
        process = psutil.Process()
        start_memory = process.memory_info().rss / (1024**2)  # MB
        
        # Combined service simulation
        async def combined_service_call(request_id: int):
            # 1. Check rate limit
            rate_result = await rate_limiter.check_rate_limit('combined-test', f'user-{request_id % 10}')
            if not rate_result.allowed:
                return False, "rate_limited"
            
            # 2. Get secret
            secret = await secret_manager.get_secret('api-key')
            if not secret:
                return False, "no_secret"
            
            # 3. Call service through circuit breaker
            async def mock_api_call():
                await asyncio.sleep(0.002)  # 2ms simulated API call
                return {"status": "success", "data": "response"}
            
            try:
                result = await circuit_breaker.call(mock_api_call)
                return True, result
            except Exception as e:
                return False, str(e)
        
        # Run benchmark
        for i in range(num_requests):
            request_start = time.time()
            try:
                success, result = await combined_service_call(i)
                if success:
                    successful += 1
                else:
                    failed += 1
                response_time = time.time() - request_start
                response_times.append(response_time)
            except Exception as e:
                failed += 1
                response_times.append(time.time() - request_start)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Calculate final resource usage
        end_memory = process.memory_info().rss / (1024**2)  # MB
        
        return BenchmarkResult(
            test_name="combined_services_performance",
            duration=duration,
            total_requests=num_requests,
            successful_requests=successful,
            failed_requests=failed,
            avg_response_time=statistics.mean(response_times) if response_times else 0,
            min_response_time=min(response_times) if response_times else 0,
            max_response_time=max(response_times) if response_times else 0,
            requests_per_second=num_requests / duration,
            memory_usage={'start_mb': start_memory, 'end_mb': end_memory, 'delta_mb': end_memory - start_memory}
        )
    
    def _generate_summary_report(self):
        """Generate comprehensive summary report."""
        if not self.results:
            return
        
        logger.info("📊 PERFORMANCE BENCHMARK SUMMARY")
        logger.info("=" * 50)
        
        for result in self.results:
            success_rate = (result.successful_requests / result.total_requests * 100) if result.total_requests > 0 else 0
            
            logger.info(f"\n🔧 {result.test_name.upper()}:")
            logger.info(f"   Duration: {result.duration:.2f}s")
            logger.info(f"   Requests: {result.total_requests} ({result.successful_requests} success, {result.failed_requests} failed)")
            logger.info(f"   Success Rate: {success_rate:.1f}%")
            logger.info(f"   RPS: {result.requests_per_second:.2f}")
            logger.info(f"   Response Time: avg={result.avg_response_time:.6f}s, min={result.min_response_time:.6f}s, max={result.max_response_time:.6f}s")
            
            if 'delta_mb' in result.memory_usage:
                logger.info(f"   Memory Delta: {result.memory_usage['delta_mb']:.2f}MB")
        
        # Performance targets check
        logger.info("\n🎯 PERFORMANCE TARGETS CHECK:")
        self._check_performance_targets()
        
        # Save report
        self._save_report()
    
    def _check_performance_targets(self):
        """Check against performance targets."""
        targets = {
            'min_rps': 100,           # Minimum requests per second
            'max_avg_response_time': 0.01,  # 10ms max average response time
            'min_success_rate': 99.0,  # 99% success rate
            'max_memory_delta': 50     # 50MB max memory increase
        }
        
        for result in self.results:
            # Check RPS
            if result.requests_per_second >= targets['min_rps']:
                logger.info(f"✅ RPS ({result.test_name}): {result.requests_per_second:.2f} >= {targets['min_rps']}")
            else:
                logger.warning(f"❌ RPS ({result.test_name}): {result.requests_per_second:.2f} < {targets['min_rps']}")
            
            # Check response time
            if result.avg_response_time <= targets['max_avg_response_time']:
                logger.info(f"✅ Response Time ({result.test_name}): {result.avg_response_time:.6f}s <= {targets['max_avg_response_time']}s")
            else:
                logger.warning(f"❌ Response Time ({result.test_name}): {result.avg_response_time:.6f}s > {targets['max_avg_response_time']}s")
            
            # Check success rate
            success_rate = (result.successful_requests / result.total_requests * 100) if result.total_requests > 0 else 0
            if success_rate >= targets['min_success_rate']:
                logger.info(f"✅ Success Rate ({result.test_name}): {success_rate:.1f}% >= {targets['min_success_rate']}%")
            else:
                logger.warning(f"❌ Success Rate ({result.test_name}): {success_rate:.1f}% < {targets['min_success_rate']}%")
            
            # Check memory usage
            memory_delta = result.memory_usage.get('delta_mb', 0)
            if memory_delta <= targets['max_memory_delta']:
                logger.info(f"✅ Memory Delta ({result.test_name}): {memory_delta:.2f}MB <= {targets['max_memory_delta']}MB")
            else:
                logger.warning(f"❌ Memory Delta ({result.test_name}): {memory_delta:.2f}MB > {targets['max_memory_delta']}MB")
    
    def _save_report(self):
        """Save benchmark report to file."""
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tests': len(self.results),
                'total_requests': sum(r.total_requests for r in self.results),
                'overall_success_rate': (sum(r.successful_requests for r in self.results) / 
                                       sum(r.total_requests for r in self.results) * 100) if sum(r.total_requests for r in self.results) > 0 else 0
            },
            'results': []
        }
        
        for result in self.results:
            report_data['results'].append({
                'test_name': result.test_name,
                'duration': result.duration,
                'total_requests': result.total_requests,
                'successful_requests': result.successful_requests,
                'failed_requests': result.failed_requests,
                'avg_response_time': result.avg_response_time,
                'min_response_time': result.min_response_time,
                'max_response_time': result.max_response_time,
                'requests_per_second': result.requests_per_second,
                'memory_usage': result.memory_usage,
                'cpu_usage': result.cpu_usage
            })
        
        # Save to file
        os.makedirs('benchmark_reports', exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'benchmark_reports/service_benchmark_{timestamp}.json'
        
        with open(filename, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"📄 Benchmark report saved to: {filename}")


async def main():
    """Run the benchmark suite."""
    suite = SimpleBenchmarkSuite()
    await suite.run_service_benchmarks()
    logger.info("🎉 Service benchmark suite completed!")


if __name__ == "__main__":
    asyncio.run(main())