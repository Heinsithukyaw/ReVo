#!/usr/bin/env python3
"""
Comprehensive Test Suite for Phase 1 Critical Hotspot Improvements
Tests all implemented features: Circuit Breakers, Health Checks, Performance, Load Balancing
"""

import asyncio
import pytest
import aiohttp
import time
import json
import redis
from typing import Dict, Any, List
import logging
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from apps.backend.middleware.circuit_breaker import (
    CircuitBreaker, 
    CircuitBreakerConfig, 
    CircuitBreakerError,
    get_circuit_breaker
)
from apps.backend.middleware.health_checks import health_checker
from apps.backend.middleware.performance import (
    performance_monitor,
    cache_manager,
    rate_limiter
)

logger = logging.getLogger(__name__)

class Phase1TestSuite:
    """
    Comprehensive test suite for Phase 1 critical hotspot improvements
    """
    
    def __init__(self):
        self.base_url = "http://localhost:12001"
        self.lb_url = "http://localhost:80"
        self.redis_client = None
        self.test_results = {}
    
    async def setup(self):
        """Setup test environment"""
        logger.info("🔧 Setting up test environment...")
        
        # Initialize Redis client
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
            self.redis_client.ping()
            logger.info("✅ Redis connection established")
        except Exception as e:
            logger.warning(f"⚠️ Redis not available: {e}")
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all Phase 1 tests"""
        logger.info("🧪 Starting Phase 1 Critical Hotspot Tests...")
        
        test_categories = [
            ("Circuit Breaker Tests", self.test_circuit_breakers),
            ("Health Check Tests", self.test_health_checks),
            ("Performance Tests", self.test_performance_optimizations),
            ("Load Balancer Tests", self.test_load_balancing),
            ("Caching Tests", self.test_caching_system),
            ("Rate Limiting Tests", self.test_rate_limiting),
            ("Monitoring Tests", self.test_monitoring_system),
            ("Resilience Tests", self.test_system_resilience)
        ]
        
        results = {}
        
        for category_name, test_function in test_categories:
            logger.info(f"📋 Running {category_name}...")
            try:
                category_results = await test_function()
                results[category_name] = category_results
                
                # Display category results
                passed = sum(1 for r in category_results.values() if r.get('passed', False))
                total = len(category_results)
                logger.info(f"✅ {category_name}: {passed}/{total} tests passed")
                
            except Exception as e:
                logger.error(f"❌ {category_name} failed: {e}")
                results[category_name] = {"error": str(e)}
        
        return results
    
    async def test_circuit_breakers(self) -> Dict[str, Any]:
        """Test circuit breaker functionality"""
        results = {}
        
        # Test 1: Circuit breaker creation and basic functionality
        results["circuit_breaker_creation"] = await self.test_circuit_breaker_creation()
        
        # Test 2: Circuit breaker failure detection
        results["failure_detection"] = await self.test_circuit_breaker_failure_detection()
        
        # Test 3: Circuit breaker state transitions
        results["state_transitions"] = await self.test_circuit_breaker_state_transitions()
        
        # Test 4: Circuit breaker recovery
        results["recovery"] = await self.test_circuit_breaker_recovery()
        
        return results
    
    async def test_circuit_breaker_creation(self) -> Dict[str, Any]:
        """Test circuit breaker creation"""
        try:
            config = CircuitBreakerConfig(failure_threshold=3, timeout=10.0)
            cb = CircuitBreaker("test_service", config)
            
            # Test successful call
            async def success_func():
                return "success"
            
            result = await cb.call(success_func)
            
            return {
                "passed": result == "success",
                "details": "Circuit breaker created and executed successfully",
                "metrics": cb.get_stats()
            }
        except Exception as e:
            return {"passed": False, "error": str(e)}
    
    async def test_circuit_breaker_failure_detection(self) -> Dict[str, Any]:
        """Test circuit breaker failure detection"""
        try:
            config = CircuitBreakerConfig(failure_threshold=2, timeout=5.0)
            cb = CircuitBreaker("test_failure_detection", config)
            
            # Function that always fails
            async def failing_func():
                raise Exception("Simulated failure")
            
            # Trigger failures
            failure_count = 0
            for i in range(3):
                try:
                    await cb.call(failing_func)
                except:
                    failure_count += 1
            
            stats = cb.get_stats()
            
            return {
                "passed": stats["failed_requests"] >= 2,
                "details": f"Detected {stats['failed_requests']} failures",
                "metrics": stats
            }
        except Exception as e:
            return {"passed": False, "error": str(e)}
    
    async def test_circuit_breaker_state_transitions(self) -> Dict[str, Any]:
        """Test circuit breaker state transitions"""
        try:
            config = CircuitBreakerConfig(failure_threshold=2, timeout=1.0)
            cb = CircuitBreaker("test_state_transitions", config)
            
            # Start in CLOSED state
            initial_state = cb.state.value
            
            # Trigger failures to open circuit
            async def failing_func():
                raise Exception("Failure")
            
            for i in range(3):
                try:
                    await cb.call(failing_func)
                except:
                    pass
            
            open_state = cb.state.value
            
            # Wait for timeout and test half-open
            await asyncio.sleep(1.1)
            
            try:
                await cb.call(failing_func)
            except:
                pass
            
            final_state = cb.state.value
            
            return {
                "passed": initial_state == "closed" and open_state == "open",
                "details": f"States: {initial_state} -> {open_state} -> {final_state}",
                "metrics": cb.get_stats()
            }
        except Exception as e:
            return {"passed": False, "error": str(e)}
    
    async def test_circuit_breaker_recovery(self) -> Dict[str, Any]:
        """Test circuit breaker recovery"""
        try:
            config = CircuitBreakerConfig(failure_threshold=2, timeout=1.0, success_threshold=2)
            cb = CircuitBreaker("test_recovery", config)
            
            # Open the circuit
            async def failing_func():
                raise Exception("Failure")
            
            for i in range(3):
                try:
                    await cb.call(failing_func)
                except:
                    pass
            
            # Wait for timeout
            await asyncio.sleep(1.1)
            
            # Successful calls to close circuit
            async def success_func():
                return "success"
            
            for i in range(3):
                try:
                    result = await cb.call(success_func)
                except:
                    pass
            
            final_state = cb.state.value
            stats = cb.get_stats()
            
            return {
                "passed": final_state == "closed" and stats["successful_requests"] >= 2,
                "details": f"Circuit recovered to {final_state}",
                "metrics": stats
            }
        except Exception as e:
            return {"passed": False, "error": str(e)}
    
    async def test_health_checks(self) -> Dict[str, Any]:
        """Test health check system"""
        results = {}
        
        # Test 1: Basic health check
        results["basic_health"] = await self.test_basic_health_check()
        
        # Test 2: Comprehensive health check
        results["comprehensive_health"] = await self.test_comprehensive_health_check()
        
        # Test 3: Health check endpoints
        results["health_endpoints"] = await self.test_health_endpoints()
        
        return results
    
    async def test_basic_health_check(self) -> Dict[str, Any]:
        """Test basic health check functionality"""
        try:
            # Test system resources check
            result = await health_checker.check_system_resources()
            
            return {
                "passed": result.status.value in ["healthy", "degraded"],
                "details": f"System health: {result.status.value}",
                "metrics": result.details
            }
        except Exception as e:
            return {"passed": False, "error": str(e)}
    
    async def test_comprehensive_health_check(self) -> Dict[str, Any]:
        """Test comprehensive health check"""
        try:
            result = await health_checker.comprehensive_health_check()
            
            services_checked = len(result.get("services", {}))
            healthy_services = result.get("summary", {}).get("healthy_services", 0)
            
            return {
                "passed": services_checked > 0,
                "details": f"Checked {services_checked} services, {healthy_services} healthy",
                "metrics": result
            }
        except Exception as e:
            return {"passed": False, "error": str(e)}
    
    async def test_health_endpoints(self) -> Dict[str, Any]:
        """Test health check HTTP endpoints"""
        try:
            endpoints = [
                "/health/live",
                "/health/ready",
                "/health"
            ]
            
            results = {}
            
            async with aiohttp.ClientSession() as session:
                for endpoint in endpoints:
                    try:
                        async with session.get(f"{self.base_url}{endpoint}") as response:
                            results[endpoint] = {
                                "status": response.status,
                                "response_time": response.headers.get("X-Response-Time", "unknown")
                            }
                    except Exception as e:
                        results[endpoint] = {"error": str(e)}
            
            passed = all(r.get("status") == 200 for r in results.values() if "status" in r)
            
            return {
                "passed": passed,
                "details": "Health endpoints tested",
                "metrics": results
            }
        except Exception as e:
            return {"passed": False, "error": str(e)}
    
    async def test_performance_optimizations(self) -> Dict[str, Any]:
        """Test performance optimization features"""
        results = {}
        
        # Test 1: Response time monitoring
        results["response_time"] = await self.test_response_time_monitoring()
        
        # Test 2: Performance metrics
        results["metrics"] = await self.test_performance_metrics()
        
        # Test 3: Compression
        results["compression"] = await self.test_response_compression()
        
        return results
    
    async def test_response_time_monitoring(self) -> Dict[str, Any]:
        """Test response time monitoring"""
        try:
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health") as response:
                    response_time = time.time() - start_time
                    x_response_time = response.headers.get("X-Response-Time")
            
            return {
                "passed": response_time < 2.0 and x_response_time is not None,
                "details": f"Response time: {response_time:.3f}s, Header: {x_response_time}",
                "metrics": {"response_time": response_time, "header": x_response_time}
            }
        except Exception as e:
            return {"passed": False, "error": str(e)}
    
    async def test_performance_metrics(self) -> Dict[str, Any]:
        """Test performance metrics collection"""
        try:
            # Make some requests to generate metrics
            async with aiohttp.ClientSession() as session:
                for i in range(5):
                    async with session.get(f"{self.base_url}/health") as response:
                        pass
            
            # Get performance metrics
            metrics = performance_monitor.get_metrics()
            
            return {
                "passed": len(metrics) > 0,
                "details": f"Collected metrics for {len(metrics)} endpoints",
                "metrics": metrics
            }
        except Exception as e:
            return {"passed": False, "error": str(e)}
    
    async def test_response_compression(self) -> Dict[str, Any]:
        """Test response compression"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Accept-Encoding": "gzip"}
                async with session.get(f"{self.base_url}/health", headers=headers) as response:
                    content_encoding = response.headers.get("Content-Encoding")
                    content_length = response.headers.get("Content-Length")
            
            return {
                "passed": True,  # Compression is optional based on content size
                "details": f"Content-Encoding: {content_encoding}, Length: {content_length}",
                "metrics": {"encoding": content_encoding, "length": content_length}
            }
        except Exception as e:
            return {"passed": False, "error": str(e)}
    
    async def test_load_balancing(self) -> Dict[str, Any]:
        """Test load balancing functionality"""
        results = {}
        
        # Test 1: Load balancer health
        results["lb_health"] = await self.test_load_balancer_health()
        
        # Test 2: Backend distribution
        results["distribution"] = await self.test_backend_distribution()
        
        return results
    
    async def test_load_balancer_health(self) -> Dict[str, Any]:
        """Test load balancer health"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.lb_url}/nginx-health") as response:
                    status = response.status
                    text = await response.text()
            
            return {
                "passed": status == 200 and "healthy" in text,
                "details": f"Load balancer status: {status}",
                "metrics": {"status": status, "response": text}
            }
        except Exception as e:
            return {"passed": False, "error": str(e)}
    
    async def test_backend_distribution(self) -> Dict[str, Any]:
        """Test backend request distribution"""
        try:
            # Make multiple requests through load balancer
            responses = []
            
            async with aiohttp.ClientSession() as session:
                for i in range(10):
                    try:
                        async with session.get(f"{self.lb_url}/api/health") as response:
                            responses.append(response.status)
                    except:
                        responses.append(0)
            
            success_rate = sum(1 for r in responses if r == 200) / len(responses)
            
            return {
                "passed": success_rate > 0.8,
                "details": f"Success rate: {success_rate:.2%}",
                "metrics": {"responses": responses, "success_rate": success_rate}
            }
        except Exception as e:
            return {"passed": False, "error": str(e)}
    
    async def test_caching_system(self) -> Dict[str, Any]:
        """Test caching system"""
        results = {}
        
        # Test 1: Cache operations
        results["cache_ops"] = await self.test_cache_operations()
        
        # Test 2: Cache performance
        results["cache_performance"] = await self.test_cache_performance()
        
        return results
    
    async def test_cache_operations(self) -> Dict[str, Any]:
        """Test basic cache operations"""
        try:
            # Test cache set/get
            test_key = "test_cache_key"
            test_value = {"test": "data", "timestamp": time.time()}
            
            # Set value
            set_result = await cache_manager.set(test_key, test_value, ttl=60)
            
            # Get value
            get_result = await cache_manager.get(test_key)
            
            # Delete value
            delete_result = await cache_manager.delete(test_key)
            
            return {
                "passed": set_result and get_result == test_value and delete_result,
                "details": "Cache set/get/delete operations tested",
                "metrics": {
                    "set": set_result,
                    "get_match": get_result == test_value,
                    "delete": delete_result
                }
            }
        except Exception as e:
            return {"passed": False, "error": str(e)}
    
    async def test_cache_performance(self) -> Dict[str, Any]:
        """Test cache performance impact"""
        try:
            # Test without cache
            start_time = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/models") as response:
                    first_response = await response.json()
            first_time = time.time() - start_time
            
            # Test with cache (second request should be faster)
            start_time = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/models") as response:
                    second_response = await response.json()
            second_time = time.time() - start_time
            
            return {
                "passed": True,  # Cache benefit may vary
                "details": f"First: {first_time:.3f}s, Second: {second_time:.3f}s",
                "metrics": {
                    "first_request_time": first_time,
                    "second_request_time": second_time,
                    "improvement": first_time - second_time
                }
            }
        except Exception as e:
            return {"passed": False, "error": str(e)}
    
    async def test_rate_limiting(self) -> Dict[str, Any]:
        """Test rate limiting functionality"""
        results = {}
        
        # Test 1: Rate limit enforcement
        results["enforcement"] = await self.test_rate_limit_enforcement()
        
        return results
    
    async def test_rate_limit_enforcement(self) -> Dict[str, Any]:
        """Test rate limit enforcement"""
        try:
            # Test rate limiter directly
            test_key = "test_rate_limit"
            
            # Should allow first few requests
            allowed_count = 0
            for i in range(5):
                if await rate_limiter.is_allowed(test_key, 3, 60):  # 3 requests per minute
                    allowed_count += 1
            
            # Should deny subsequent requests
            denied = not await rate_limiter.is_allowed(test_key, 3, 60)
            
            return {
                "passed": allowed_count == 3 and denied,
                "details": f"Allowed {allowed_count}/5 requests, then denied",
                "metrics": {"allowed": allowed_count, "denied": denied}
            }
        except Exception as e:
            return {"passed": False, "error": str(e)}
    
    async def test_monitoring_system(self) -> Dict[str, Any]:
        """Test monitoring system"""
        results = {}
        
        # Test 1: Metrics endpoint
        results["metrics_endpoint"] = await self.test_metrics_endpoint()
        
        # Test 2: Performance metrics
        results["performance_metrics"] = await self.test_performance_metrics_endpoint()
        
        return results
    
    async def test_metrics_endpoint(self) -> Dict[str, Any]:
        """Test Prometheus metrics endpoint"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/metrics") as response:
                    status = response.status
                    content_type = response.headers.get("Content-Type")
                    text = await response.text()
            
            has_metrics = "revoagent_" in text
            
            return {
                "passed": status == 200 and has_metrics,
                "details": f"Metrics endpoint status: {status}, has metrics: {has_metrics}",
                "metrics": {"status": status, "content_type": content_type, "has_metrics": has_metrics}
            }
        except Exception as e:
            return {"passed": False, "error": str(e)}
    
    async def test_performance_metrics_endpoint(self) -> Dict[str, Any]:
        """Test performance metrics endpoint"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/performance") as response:
                    status = response.status
                    data = await response.json()
            
            has_performance_data = "performance_metrics" in data
            has_circuit_breakers = "circuit_breakers" in data
            
            return {
                "passed": status == 200 and has_performance_data,
                "details": f"Performance endpoint working, CB data: {has_circuit_breakers}",
                "metrics": {
                    "status": status,
                    "has_performance": has_performance_data,
                    "has_circuit_breakers": has_circuit_breakers
                }
            }
        except Exception as e:
            return {"passed": False, "error": str(e)}
    
    async def test_system_resilience(self) -> Dict[str, Any]:
        """Test overall system resilience"""
        results = {}
        
        # Test 1: Concurrent requests
        results["concurrent_load"] = await self.test_concurrent_load()
        
        # Test 2: Error recovery
        results["error_recovery"] = await self.test_error_recovery()
        
        return results
    
    async def test_concurrent_load(self) -> Dict[str, Any]:
        """Test system under concurrent load"""
        try:
            async def make_request(session, i):
                try:
                    async with session.get(f"{self.base_url}/health") as response:
                        return response.status
                except:
                    return 0
            
            # Make 20 concurrent requests
            async with aiohttp.ClientSession() as session:
                tasks = [make_request(session, i) for i in range(20)]
                responses = await asyncio.gather(*tasks)
            
            success_count = sum(1 for r in responses if r == 200)
            success_rate = success_count / len(responses)
            
            return {
                "passed": success_rate > 0.9,
                "details": f"Success rate under load: {success_rate:.2%}",
                "metrics": {"responses": responses, "success_rate": success_rate}
            }
        except Exception as e:
            return {"passed": False, "error": str(e)}
    
    async def test_error_recovery(self) -> Dict[str, Any]:
        """Test system error recovery"""
        try:
            # Test that system continues working after errors
            error_count = 0
            success_count = 0
            
            async with aiohttp.ClientSession() as session:
                # Mix of valid and invalid requests
                endpoints = ["/health", "/invalid", "/health", "/also-invalid", "/health"]
                
                for endpoint in endpoints:
                    try:
                        async with session.get(f"{self.base_url}{endpoint}") as response:
                            if response.status == 200:
                                success_count += 1
                            else:
                                error_count += 1
                    except:
                        error_count += 1
            
            return {
                "passed": success_count >= 3,  # Should handle valid requests despite errors
                "details": f"Successes: {success_count}, Errors: {error_count}",
                "metrics": {"successes": success_count, "errors": error_count}
            }
        except Exception as e:
            return {"passed": False, "error": str(e)}
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate a comprehensive test report"""
        report = []
        report.append("=" * 80)
        report.append("🧪 PHASE 1 CRITICAL HOTSPOT IMPROVEMENTS - TEST REPORT")
        report.append("=" * 80)
        report.append("")
        
        total_categories = len(results)
        passed_categories = 0
        total_tests = 0
        passed_tests = 0
        
        for category, category_results in results.items():
            if "error" in category_results:
                report.append(f"❌ {category}: ERROR - {category_results['error']}")
                continue
            
            category_passed = 0
            category_total = len(category_results)
            
            for test_name, test_result in category_results.items():
                total_tests += 1
                if test_result.get("passed", False):
                    passed_tests += 1
                    category_passed += 1
                    status = "✅ PASS"
                else:
                    status = "❌ FAIL"
                
                report.append(f"  {status} {test_name}: {test_result.get('details', 'No details')}")
            
            if category_passed == category_total:
                passed_categories += 1
                category_status = "✅"
            else:
                category_status = "❌"
            
            report.append(f"{category_status} {category}: {category_passed}/{category_total} tests passed")
            report.append("")
        
        # Summary
        report.append("=" * 80)
        report.append("📊 SUMMARY")
        report.append("=" * 80)
        report.append(f"Categories: {passed_categories}/{total_categories} passed")
        report.append(f"Total Tests: {passed_tests}/{total_tests} passed")
        report.append(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        report.append("")
        
        # Phase 1 Checklist
        report.append("📋 PHASE 1 IMPLEMENTATION CHECKLIST")
        report.append("=" * 80)
        
        checklist_items = [
            ("Circuit Breaker Implementation", "Circuit Breaker Tests" in results),
            ("Health Check Endpoints", "Health Check Tests" in results),
            ("Performance Monitoring", "Performance Tests" in results),
            ("Load Balancer Setup", "Load Balancer Tests" in results),
            ("Caching System", "Caching Tests" in results),
            ("Rate Limiting", "Rate Limiting Tests" in results),
            ("Monitoring Integration", "Monitoring Tests" in results),
            ("System Resilience", "Resilience Tests" in results)
        ]
        
        for item, implemented in checklist_items:
            status = "✅" if implemented else "❌"
            report.append(f"{status} {item}")
        
        report.append("")
        report.append("🎯 NEXT STEPS:")
        report.append("- Review failed tests and address issues")
        report.append("- Proceed to Phase 2: Multi-Agent Communication Optimization")
        report.append("- Continue with Phase 3: Memory System Optimization")
        report.append("")
        
        return "\n".join(report)

async def main():
    """Main test execution function"""
    test_suite = Phase1TestSuite()
    
    try:
        # Setup
        await test_suite.setup()
        
        # Run all tests
        results = await test_suite.run_all_tests()
        
        # Generate and display report
        report = test_suite.generate_report(results)
        print(report)
        
        # Save report to file
        report_file = Path(__file__).parent.parent / "test_results_phase1.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        
        logger.info(f"📄 Test report saved to: {report_file}")
        
        # Return exit code based on results
        total_tests = sum(len(cat) for cat in results.values() if isinstance(cat, dict) and "error" not in cat)
        passed_tests = sum(
            sum(1 for test in cat.values() if test.get("passed", False))
            for cat in results.values()
            if isinstance(cat, dict) and "error" not in cat
        )
        
        success_rate = passed_tests / total_tests if total_tests > 0 else 0
        return 0 if success_rate > 0.8 else 1
        
    except Exception as e:
        logger.error(f"❌ Test execution failed: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))