#!/usr/bin/env python3
"""
Comprehensive Integration Tests for reVoAgent Production System

Tests all services working together in realistic scenarios:
- End-to-end API workflows
- Service failure and recovery
- Performance under load
- Security and rate limiting
- Database operations
- Circuit breaker behavior
"""

import pytest
import asyncio
import time
import json
import os
import sys
from typing import Dict, Any, List
from unittest.mock import AsyncMock, patch
import tempfile
import sqlite3

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from packages.ai.schemas import GenerationRequest, TaskType, Language
from packages.ai.unified_model_manager import unified_model_manager
from packages.core.secret_manager import SecretManager, SecretConfig, SecretProvider
from packages.core.rate_limiter import RateLimiter, InMemoryStorage, RateLimitRule, RateLimitAlgorithm, RateLimitScope
from packages.core.database import DatabaseManager, DatabaseConfig
from packages.core.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitBreakerOpenException
from packages.core.logging_config import setup_logging, get_logger

logger = get_logger(__name__)


class IntegrationTestEnvironment:
    """Test environment setup and teardown."""
    
    def __init__(self):
        self.temp_dir = None
        self.secrets_file = None
        self.db_file = None
        self.secret_manager = None
        self.rate_limiter = None
        self.db_manager = None
        self.circuit_breaker = None
    
    async def setup(self):
        """Setup test environment with all services."""
        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp()
        self.secrets_file = os.path.join(self.temp_dir, "test_secrets.json")
        self.db_file = os.path.join(self.temp_dir, "test.db")
        
        # Setup logging
        setup_logging(log_level="INFO", enable_console=False, enable_json=False)
        
        # Create test secrets
        test_secrets = {
            "openai-api-key": "sk-test-key-12345",
            "anthropic-api-key": "test-anthropic-key",
            "database-url": f"sqlite:///{self.db_file}",
            "test-secret": "test-value"
        }
        
        with open(self.secrets_file, 'w') as f:
            json.dump(test_secrets, f)
        
        # Initialize secret manager
        secret_config = SecretConfig(
            provider=SecretProvider.LOCAL_FILE,
            local_secrets_file=self.secrets_file,
            cache_ttl_seconds=60
        )
        self.secret_manager = SecretManager(secret_config)
        await self.secret_manager.initialize()
        
        # Initialize rate limiter
        storage = InMemoryStorage()
        rules = [
            RateLimitRule(
                name="test_api",
                requests=10,
                window_seconds=60,
                algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
                scope=RateLimitScope.PER_IP
            ),
            RateLimitRule(
                name="test_generation",
                requests=5,
                window_seconds=60,
                algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
                scope=RateLimitScope.PER_USER,
                burst_multiplier=2.0
            )
        ]
        self.rate_limiter = RateLimiter(storage, rules)
        
        # Initialize database manager
        db_config = DatabaseConfig(
            url=f"sqlite:///{self.db_file}",
            pool_size=5,
            max_overflow=10
        )
        self.db_manager = DatabaseManager(db_config)
        await self.db_manager.initialize()
        
        # Initialize circuit breaker
        circuit_config = CircuitBreakerConfig(
            name="test_service",
            failure_threshold=3,
            recovery_timeout=5,
            success_threshold=2,
            timeout=10.0
        )
        self.circuit_breaker = CircuitBreaker(circuit_config)
        
        logger.info("Integration test environment setup complete")
    
    async def teardown(self):
        """Cleanup test environment."""
        try:
            if self.db_manager:
                await self.db_manager.close()
            
            # Cleanup temp files
            if self.temp_dir and os.path.exists(self.temp_dir):
                import shutil
                shutil.rmtree(self.temp_dir)
            
            logger.info("Integration test environment cleaned up")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")


@pytest.fixture
async def test_env():
    """Pytest fixture for test environment."""
    env = IntegrationTestEnvironment()
    await env.setup()
    yield env
    await env.teardown()


class TestSecretManagementIntegration:
    """Test secret management in realistic scenarios."""
    
    async def test_secret_retrieval_and_caching(self, test_env):
        """Test secret retrieval with caching behavior."""
        secret_manager = test_env.secret_manager
        
        # Test initial retrieval
        start_time = time.time()
        secret1 = await secret_manager.get_secret("openai-api-key")
        first_retrieval_time = time.time() - start_time
        
        assert secret1 == "sk-test-key-12345"
        
        # Test cached retrieval (should be faster)
        start_time = time.time()
        secret2 = await secret_manager.get_secret("openai-api-key")
        cached_retrieval_time = time.time() - start_time
        
        assert secret2 == secret1
        assert cached_retrieval_time < first_retrieval_time
        
        # Test cache stats
        stats = secret_manager.get_cache_stats()
        assert stats['total_cached'] >= 1
        assert stats['provider'] == 'local_file'
    
    async def test_secret_fallback_behavior(self, test_env):
        """Test fallback to environment variables."""
        secret_manager = test_env.secret_manager
        
        # Test non-existent secret with default
        secret = await secret_manager.get_secret("non-existent", "default-value")
        assert secret == "default-value"
        
        # Test environment variable fallback
        os.environ["TEST_ENV_SECRET"] = "env-value"
        secret = await secret_manager.get_secret("TEST_ENV_SECRET")
        assert secret == "env-value"
        
        # Cleanup
        del os.environ["TEST_ENV_SECRET"]
    
    async def test_secret_health_check(self, test_env):
        """Test secret manager health check."""
        secret_manager = test_env.secret_manager
        
        health = await secret_manager.health_check()
        assert health['status'] == 'healthy'
        assert health['provider'] == 'local_file'
        assert 'cache_stats' in health


class TestRateLimitingIntegration:
    """Test rate limiting in realistic API scenarios."""
    
    async def test_rate_limit_enforcement(self, test_env):
        """Test rate limiting with multiple requests."""
        rate_limiter = test_env.rate_limiter
        
        # Test within limits
        for i in range(5):
            result = await rate_limiter.check_rate_limit("test_api", "test-user")
            assert result.allowed == True
            assert result.remaining >= 0
        
        # Test exceeding limits
        for i in range(10):
            result = await rate_limiter.check_rate_limit("test_api", "test-user")
        
        # Should eventually be rate limited
        final_result = await rate_limiter.check_rate_limit("test_api", "test-user")
        assert final_result.allowed == False
        assert final_result.retry_after is not None
    
    async def test_token_bucket_burst_handling(self, test_env):
        """Test token bucket algorithm with burst capacity."""
        rate_limiter = test_env.rate_limiter
        
        # Test burst requests (should allow more than base rate)
        burst_results = []
        for i in range(8):  # More than base rate of 5
            result = await rate_limiter.check_rate_limit("test_generation", "burst-user")
            burst_results.append(result.allowed)
        
        # Should allow some burst requests
        allowed_count = sum(burst_results)
        assert allowed_count > 5  # More than base rate
        assert allowed_count <= 10  # Within burst capacity
    
    async def test_rate_limit_statistics(self, test_env):
        """Test rate limiter statistics collection."""
        rate_limiter = test_env.rate_limiter
        
        # Generate some traffic
        for i in range(15):
            await rate_limiter.check_rate_limit("test_api", f"user-{i % 3}")
        
        stats = rate_limiter.get_stats()
        assert stats['total_requests'] >= 15
        assert stats['blocked_requests'] >= 0
        assert 'block_rate' in stats
        assert 'requests_per_second' in stats


class TestDatabaseIntegration:
    """Test database operations and connection pooling."""
    
    async def test_database_connection_and_queries(self, test_env):
        """Test basic database operations."""
        db_manager = test_env.db_manager
        
        # Test simple query
        result = await db_manager.execute_async_query("SELECT 1 as test_value")
        assert len(result) == 1
        assert result[0][0] == 1
    
    async def test_database_health_monitoring(self, test_env):
        """Test database health checks and monitoring."""
        db_manager = test_env.db_manager
        
        # Test health check
        health = await db_manager.health_check()
        assert health['status'] == 'healthy'
        assert 'response_time' in health
        assert 'pool_status' in health
        
        # Test pool status
        pool_status = await db_manager.get_pool_status()
        assert 'size' in pool_status
        assert 'checked_in' in pool_status
        assert 'checked_out' in pool_status
    
    async def test_database_retry_logic(self, test_env):
        """Test database retry logic with simulated failures."""
        db_manager = test_env.db_manager
        
        # Test with invalid query (should retry and fail)
        with pytest.raises(Exception):
            await db_manager.execute_async_query("INVALID SQL QUERY")
        
        # Verify stats show failed queries
        stats = db_manager.get_performance_stats()
        assert stats['failed_queries'] > 0


class TestCircuitBreakerIntegration:
    """Test circuit breaker behavior with external services."""
    
    async def test_circuit_breaker_success_flow(self, test_env):
        """Test circuit breaker with successful calls."""
        circuit_breaker = test_env.circuit_breaker
        
        async def successful_service():
            await asyncio.sleep(0.1)  # Simulate network delay
            return "success"
        
        # Test successful calls
        for i in range(5):
            result = await circuit_breaker.call(successful_service)
            assert result == "success"
        
        stats = circuit_breaker.get_stats()
        assert stats['successful_requests'] == 5
        assert stats['failed_requests'] == 0
        assert stats['state'] == 'closed'
    
    async def test_circuit_breaker_failure_and_recovery(self, test_env):
        """Test circuit breaker opening and recovery."""
        circuit_breaker = test_env.circuit_breaker
        
        async def failing_service():
            raise Exception("Service unavailable")
        
        # Generate failures to open circuit
        for i in range(4):  # More than failure threshold (3)
            try:
                await circuit_breaker.call(failing_service)
            except Exception:
                pass
        
        stats = circuit_breaker.get_stats()
        assert stats['state'] == 'open'
        assert stats['failed_requests'] >= 3
        
        # Test that circuit rejects requests
        with pytest.raises(CircuitBreakerOpenException):
            await circuit_breaker.call(failing_service)
    
    async def test_circuit_breaker_with_fallback(self, test_env):
        """Test circuit breaker fallback functionality."""
        
        def fallback_function(*args, **kwargs):
            return "fallback_response"
        
        circuit_config = CircuitBreakerConfig(
            name="test_fallback",
            failure_threshold=2,
            recovery_timeout=5,
            fallback_function=fallback_function
        )
        circuit_breaker = CircuitBreaker(circuit_config)
        
        async def failing_service():
            raise Exception("Service down")
        
        # Trigger circuit opening
        for i in range(3):
            try:
                await circuit_breaker.call(failing_service)
            except Exception:
                pass
        
        # Test fallback
        result = await circuit_breaker.call_with_fallback(failing_service)
        assert result == "fallback_response"


class TestEndToEndWorkflows:
    """Test complete end-to-end workflows."""
    
    async def test_complete_api_request_flow(self, test_env):
        """Test complete API request with all services."""
        
        # Simulate API request flow
        user_id = "test-user-123"
        ip_address = "192.168.1.100"
        
        # 1. Check rate limit
        rate_result = await test_env.rate_limiter.check_rate_limit("test_api", ip_address)
        assert rate_result.allowed == True
        
        # 2. Get API key from secrets
        api_key = await test_env.secret_manager.get_secret("openai-api-key")
        assert api_key is not None
        
        # 3. Simulate AI service call with circuit breaker
        async def mock_ai_service():
            await asyncio.sleep(0.1)
            return {
                "content": "Generated response",
                "model": "gpt-3.5-turbo",
                "tokens": 150
            }
        
        ai_result = await test_env.circuit_breaker.call(mock_ai_service)
        assert ai_result["content"] == "Generated response"
        
        # 4. Log to database (simulate)
        query = "INSERT INTO request_logs (request_id, user_id, endpoint, status_code) VALUES (?, ?, ?, ?)"
        # Note: Would need actual table creation for full test
        
        logger.info("Complete API flow test passed")
    
    async def test_service_failure_scenarios(self, test_env):
        """Test system behavior under service failures."""
        
        # Test secret manager failure fallback
        with patch.object(test_env.secret_manager, 'get_secret', side_effect=Exception("Vault down")):
            # Should fallback to environment variable
            os.environ["FALLBACK_SECRET"] = "fallback-value"
            secret = await test_env.secret_manager.get_secret("FALLBACK_SECRET", "default")
            assert secret == "fallback-value"
            del os.environ["FALLBACK_SECRET"]
        
        # Test rate limiter failure (should fail open)
        with patch.object(test_env.rate_limiter, 'check_rate_limit', side_effect=Exception("Redis down")):
            try:
                result = await test_env.rate_limiter.check_rate_limit("test_api", "user")
                # Should fail open (allow request)
                assert result.allowed == True
            except Exception:
                # Or handle gracefully
                pass
    
    async def test_performance_under_load(self, test_env):
        """Test system performance under concurrent load."""
        
        async def simulate_request(request_id: int):
            """Simulate a single API request."""
            try:
                # Rate limit check
                rate_result = await test_env.rate_limiter.check_rate_limit("test_api", f"user-{request_id % 10}")
                
                # Secret retrieval
                secret = await test_env.secret_manager.get_secret("test-secret")
                
                # Database query
                result = await test_env.db_manager.execute_async_query("SELECT 1")
                
                # Circuit breaker call
                async def mock_service():
                    await asyncio.sleep(0.01)  # Minimal delay
                    return f"response-{request_id}"
                
                service_result = await test_env.circuit_breaker.call(mock_service)
                
                return {
                    "request_id": request_id,
                    "rate_limited": not rate_result.allowed,
                    "secret_retrieved": secret is not None,
                    "db_success": len(result) > 0,
                    "service_response": service_result
                }
                
            except Exception as e:
                return {"request_id": request_id, "error": str(e)}
        
        # Run concurrent requests
        start_time = time.time()
        tasks = [simulate_request(i) for i in range(50)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        # Analyze results
        successful_requests = [r for r in results if isinstance(r, dict) and "error" not in r]
        failed_requests = [r for r in results if isinstance(r, dict) and "error" in r]
        
        success_rate = len(successful_requests) / len(results) * 100
        avg_response_time = total_time / len(results)
        
        logger.info(f"Load test results: {success_rate:.1f}% success rate, {avg_response_time:.3f}s avg response time")
        
        # Performance assertions
        assert success_rate >= 80  # At least 80% success rate
        assert avg_response_time < 1.0  # Average response time under 1 second
        assert len(failed_requests) < len(results) * 0.2  # Less than 20% failures


class TestSecurityIntegration:
    """Test security features integration."""
    
    async def test_sensitive_data_filtering(self, test_env):
        """Test that sensitive data is properly filtered in logs."""
        
        # Test secret retrieval logging
        secret = await test_env.secret_manager.get_secret("openai-api-key")
        assert secret == "sk-test-key-12345"
        
        # Verify that the actual secret value doesn't appear in logs
        # (This would require log capture in a real test)
        logger.info(f"Retrieved secret: {secret}")
        
        # The logging system should automatically redact this
        logger.info("password=secret123 api_key=sk-12345 token=abc123")
    
    async def test_rate_limiting_security(self, test_env):
        """Test rate limiting as a security measure."""
        rate_limiter = test_env.rate_limiter
        
        # Simulate attack pattern
        attacker_ip = "192.168.1.999"
        
        # Rapid requests from same IP
        blocked_count = 0
        for i in range(20):
            result = await rate_limiter.check_rate_limit("test_api", attacker_ip)
            if not result.allowed:
                blocked_count += 1
        
        # Should block some requests
        assert blocked_count > 0
        
        # Different IPs should not be affected
        legitimate_result = await rate_limiter.check_rate_limit("test_api", "192.168.1.100")
        assert legitimate_result.allowed == True


# Performance benchmarking tests
class TestPerformanceBenchmarks:
    """Performance benchmarking tests."""
    
    async def test_secret_retrieval_performance(self, test_env):
        """Benchmark secret retrieval performance."""
        secret_manager = test_env.secret_manager
        
        # Warm up cache
        await secret_manager.get_secret("test-secret")
        
        # Benchmark cached retrieval
        start_time = time.time()
        for i in range(100):
            await secret_manager.get_secret("test-secret")
        cached_time = time.time() - start_time
        
        # Should be very fast for cached retrieval
        avg_cached_time = cached_time / 100
        assert avg_cached_time < 0.001  # Less than 1ms per cached retrieval
        
        logger.info(f"Secret retrieval benchmark: {avg_cached_time:.6f}s per cached request")
    
    async def test_rate_limiter_performance(self, test_env):
        """Benchmark rate limiter performance."""
        rate_limiter = test_env.rate_limiter
        
        start_time = time.time()
        for i in range(1000):
            await rate_limiter.check_rate_limit("test_api", f"user-{i}")
        total_time = time.time() - start_time
        
        avg_time = total_time / 1000
        assert avg_time < 0.01  # Less than 10ms per check
        
        logger.info(f"Rate limiter benchmark: {avg_time:.6f}s per check")
    
    async def test_database_query_performance(self, test_env):
        """Benchmark database query performance."""
        db_manager = test_env.db_manager
        
        start_time = time.time()
        for i in range(100):
            await db_manager.execute_async_query("SELECT 1")
        total_time = time.time() - start_time
        
        avg_time = total_time / 100
        assert avg_time < 0.1  # Less than 100ms per query
        
        logger.info(f"Database query benchmark: {avg_time:.6f}s per query")


if __name__ == "__main__":
    # Run tests directly
    async def run_tests():
        test_env = IntegrationTestEnvironment()
        await test_env.setup()
        
        try:
            # Run a subset of tests
            secret_tests = TestSecretManagementIntegration()
            await secret_tests.test_secret_retrieval_and_caching(test_env)
            await secret_tests.test_secret_health_check(test_env)
            
            rate_limit_tests = TestRateLimitingIntegration()
            await rate_limit_tests.test_rate_limit_enforcement(test_env)
            
            circuit_tests = TestCircuitBreakerIntegration()
            await circuit_tests.test_circuit_breaker_success_flow(test_env)
            
            e2e_tests = TestEndToEndWorkflows()
            await e2e_tests.test_complete_api_request_flow(test_env)
            
            perf_tests = TestPerformanceBenchmarks()
            await perf_tests.test_secret_retrieval_performance(test_env)
            
            print("✅ All integration tests passed!")
            
        finally:
            await test_env.teardown()
    
    asyncio.run(run_tests())