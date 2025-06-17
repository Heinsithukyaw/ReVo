"""
Comprehensive test suite for Circuit Breaker Service
Tests resilience patterns and error handling
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock

from apps.backend.services.circuit_breaker_service import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    CircuitBreakerError,
    CircuitBreakerRegistry,
    ExternalAPIService,
    RetryWithExponentialBackoff,
    circuit_breaker,
    retry_with_backoff
)

class TestCircuitBreaker:
    """Test suite for CircuitBreaker class"""
    
    @pytest.fixture
    def circuit_config(self):
        """Circuit breaker configuration for testing"""
        return CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=5,
            success_threshold=2,
            timeout=1.0
        )
    
    @pytest.fixture
    def circuit_breaker_instance(self, circuit_config):
        """Circuit breaker instance for testing"""
        return CircuitBreaker("test_circuit", circuit_config)
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_initialization(self, circuit_breaker_instance):
        """Test circuit breaker initialization"""
        assert circuit_breaker_instance.name == "test_circuit"
        assert circuit_breaker_instance.stats.state == CircuitState.CLOSED
        assert circuit_breaker_instance.stats.failure_count == 0
        assert circuit_breaker_instance.stats.success_count == 0
    
    @pytest.mark.asyncio
    async def test_successful_request(self, circuit_breaker_instance):
        """Test successful request handling"""
        async def successful_function():
            return "success"
        
        result = await circuit_breaker_instance.call(successful_function)
        
        assert result == "success"
        assert circuit_breaker_instance.stats.state == CircuitState.CLOSED
        assert circuit_breaker_instance.stats.total_successes == 1
        assert circuit_breaker_instance.stats.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_failed_request(self, circuit_breaker_instance):
        """Test failed request handling"""
        async def failing_function():
            raise Exception("Test failure")
        
        with pytest.raises(CircuitBreakerError):
            await circuit_breaker_instance.call(failing_function)
        
        assert circuit_breaker_instance.stats.state == CircuitState.CLOSED
        assert circuit_breaker_instance.stats.total_failures == 1
        assert circuit_breaker_instance.stats.failure_count == 1
    
    @pytest.mark.asyncio
    async def test_circuit_opens_after_threshold_failures(self, circuit_breaker_instance):
        """Test that circuit opens after reaching failure threshold"""
        async def failing_function():
            raise Exception("Test failure")
        
        # Make failures up to threshold
        for i in range(3):
            with pytest.raises(CircuitBreakerError):
                await circuit_breaker_instance.call(failing_function)
        
        # Circuit should now be open
        assert circuit_breaker_instance.stats.state == CircuitState.OPEN
        
        # Next request should fail fast
        with pytest.raises(CircuitBreakerError, match="Circuit breaker .* is OPEN"):
            await circuit_breaker_instance.call(failing_function)
    
    @pytest.mark.asyncio
    async def test_circuit_half_open_after_timeout(self, circuit_breaker_instance):
        """Test circuit transitions to half-open after recovery timeout"""
        async def failing_function():
            raise Exception("Test failure")
        
        # Open the circuit
        for i in range(3):
            with pytest.raises(CircuitBreakerError):
                await circuit_breaker_instance.call(failing_function)
        
        assert circuit_breaker_instance.stats.state == CircuitState.OPEN
        
        # Simulate time passing
        circuit_breaker_instance.stats.last_failure_time = time.time() - 10  # 10 seconds ago
        
        # Next request should transition to half-open
        async def successful_function():
            return "success"
        
        result = await circuit_breaker_instance.call(successful_function)
        assert result == "success"
        assert circuit_breaker_instance.stats.state == CircuitState.HALF_OPEN
    
    @pytest.mark.asyncio
    async def test_circuit_closes_after_successful_half_open(self, circuit_breaker_instance):
        """Test circuit closes after successful requests in half-open state"""
        # Manually set to half-open state
        circuit_breaker_instance.stats.state = CircuitState.HALF_OPEN
        circuit_breaker_instance.stats.success_count = 0
        
        async def successful_function():
            return "success"
        
        # Make successful requests to close circuit
        for i in range(2):  # success_threshold = 2
            result = await circuit_breaker_instance.call(successful_function)
            assert result == "success"
        
        # Circuit should now be closed
        assert circuit_breaker_instance.stats.state == CircuitState.CLOSED
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, circuit_breaker_instance):
        """Test request timeout handling"""
        async def slow_function():
            await asyncio.sleep(2.0)  # Longer than timeout (1.0s)
            return "slow_result"
        
        with pytest.raises(CircuitBreakerError, match="Request timeout"):
            await circuit_breaker_instance.call(slow_function)
        
        assert circuit_breaker_instance.stats.failure_count == 1
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_stats(self, circuit_breaker_instance):
        """Test circuit breaker statistics"""
        async def test_function(should_fail=False):
            if should_fail:
                raise Exception("Test failure")
            return "success"
        
        # Make some successful and failed requests
        await circuit_breaker_instance.call(test_function, False)
        await circuit_breaker_instance.call(test_function, False)
        
        try:
            await circuit_breaker_instance.call(test_function, True)
        except CircuitBreakerError:
            pass
        
        stats = circuit_breaker_instance.get_stats()
        
        assert stats["name"] == "test_circuit"
        assert stats["total_requests"] == 3
        assert stats["total_successes"] == 2
        assert stats["total_failures"] == 1
        assert stats["success_rate"] == 2/3
        assert stats["failure_rate"] == 1/3
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_reset(self, circuit_breaker_instance):
        """Test circuit breaker reset functionality"""
        async def failing_function():
            raise Exception("Test failure")
        
        # Make some failures
        for i in range(2):
            try:
                await circuit_breaker_instance.call(failing_function)
            except CircuitBreakerError:
                pass
        
        assert circuit_breaker_instance.stats.failure_count == 2
        
        # Reset the circuit breaker
        circuit_breaker_instance.reset()
        
        assert circuit_breaker_instance.stats.state == CircuitState.CLOSED
        assert circuit_breaker_instance.stats.failure_count == 0
        assert circuit_breaker_instance.stats.total_requests == 0

class TestCircuitBreakerRegistry:
    """Test suite for CircuitBreakerRegistry"""
    
    @pytest.fixture
    def registry(self):
        """Circuit breaker registry for testing"""
        return CircuitBreakerRegistry()
    
    @pytest.mark.asyncio
    async def test_get_circuit_breaker(self, registry):
        """Test getting circuit breaker from registry"""
        config = CircuitBreakerConfig(failure_threshold=5)
        circuit = await registry.get_circuit_breaker("test_service", config)
        
        assert circuit.name == "test_service"
        assert circuit.config.failure_threshold == 5
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_reuse(self, registry):
        """Test that same circuit breaker is reused"""
        circuit1 = await registry.get_circuit_breaker("test_service")
        circuit2 = await registry.get_circuit_breaker("test_service")
        
        assert circuit1 is circuit2
    
    @pytest.mark.asyncio
    async def test_get_all_stats(self, registry):
        """Test getting all circuit breaker stats"""
        await registry.get_circuit_breaker("service1")
        await registry.get_circuit_breaker("service2")
        
        all_stats = await registry.get_all_stats()
        
        assert "service1" in all_stats
        assert "service2" in all_stats
        assert len(all_stats) == 2
    
    @pytest.mark.asyncio
    async def test_health_summary(self, registry):
        """Test health summary generation"""
        circuit1 = await registry.get_circuit_breaker("healthy_service")
        circuit2 = await registry.get_circuit_breaker("unhealthy_service")
        
        # Make unhealthy_service circuit open
        circuit2.stats.state = CircuitState.OPEN
        
        health_summary = await registry.get_health_summary()
        
        assert health_summary["total_circuits"] == 2
        assert health_summary["open_circuits"] == 1
        assert health_summary["closed_circuits"] == 1
        assert health_summary["overall_health"] == "degraded"
    
    @pytest.mark.asyncio
    async def test_reset_all(self, registry):
        """Test resetting all circuit breakers"""
        circuit1 = await registry.get_circuit_breaker("service1")
        circuit2 = await registry.get_circuit_breaker("service2")
        
        # Modify circuit states
        circuit1.stats.failure_count = 5
        circuit2.stats.state = CircuitState.OPEN
        
        await registry.reset_all()
        
        assert circuit1.stats.failure_count == 0
        assert circuit1.stats.state == CircuitState.CLOSED
        assert circuit2.stats.state == CircuitState.CLOSED

class TestCircuitBreakerDecorator:
    """Test suite for circuit breaker decorator"""
    
    @pytest.mark.asyncio
    async def test_decorator_basic_functionality(self):
        """Test basic circuit breaker decorator functionality"""
        call_count = 0
        
        @circuit_breaker("test_decorator", CircuitBreakerConfig(failure_threshold=2))
        async def test_function(should_fail=False):
            nonlocal call_count
            call_count += 1
            if should_fail:
                raise Exception("Test failure")
            return f"success_{call_count}"
        
        # Successful call
        result = await test_function(False)
        assert result == "success_1"
        
        # Failed calls
        with pytest.raises(CircuitBreakerError):
            await test_function(True)
        
        with pytest.raises(CircuitBreakerError):
            await test_function(True)
        
        # Circuit should be open now, next call should fail fast
        with pytest.raises(CircuitBreakerError, match="Circuit breaker .* is OPEN"):
            await test_function(False)
        
        # Function should not have been called
        assert call_count == 3  # 1 success + 2 failures

class TestExternalAPIService:
    """Test suite for ExternalAPIService"""
    
    @pytest.fixture
    async def api_service(self):
        """External API service for testing"""
        service = ExternalAPIService()
        await service.initialize()
        return service
    
    @pytest.mark.asyncio
    async def test_openai_api_success(self, api_service):
        """Test successful OpenAI API call"""
        mock_response = {
            "choices": [{"message": {"content": "Test response"}}],
            "model": "gpt-4",
            "usage": {"total_tokens": 50}
        }
        
        with patch.object(api_service.session, 'post') as mock_post:
            mock_post.return_value.__aenter__.return_value.status = 200
            mock_post.return_value.__aenter__.return_value.json = AsyncMock(return_value=mock_response)
            
            result = await api_service.call_openai_api({
                "model": "gpt-4",
                "messages": [{"role": "user", "content": "test"}],
                "api_key": "test-key"
            })
            
            assert result == mock_response
    
    @pytest.mark.asyncio
    async def test_openai_api_failure_fallback(self, api_service):
        """Test OpenAI API failure with fallback"""
        with patch.object(api_service.session, 'post') as mock_post:
            mock_post.return_value.__aenter__.return_value.status = 500
            mock_post.return_value.__aenter__.return_value.text = AsyncMock(return_value="Server Error")
            
            result = await api_service.call_openai_api({
                "model": "gpt-4",
                "messages": [{"role": "user", "content": "test"}]
            })
            
            # Should fallback to local model
            assert result["fallback"] is True
            assert "local-fallback" in result["model"]
    
    @pytest.mark.asyncio
    async def test_database_query_success(self, api_service):
        """Test successful database query"""
        with patch('asyncio.sleep'):  # Mock the sleep
            with patch('random.random', return_value=0.9):  # Ensure no failure
                result = await api_service.query_database("SELECT * FROM users")
                
                assert result[0]["result"] == "success"
    
    @pytest.mark.asyncio
    async def test_database_query_failure(self, api_service):
        """Test database query failure"""
        with patch('asyncio.sleep'):
            with patch('random.random', return_value=0.01):  # Force failure
                with pytest.raises(CircuitBreakerError):
                    await api_service.query_database("SELECT * FROM users")

class TestRetryWithExponentialBackoff:
    """Test suite for RetryWithExponentialBackoff"""
    
    @pytest.fixture
    def retry_handler(self):
        """Retry handler for testing"""
        return RetryWithExponentialBackoff(max_retries=3, base_delay=0.1, max_delay=1.0)
    
    @pytest.mark.asyncio
    async def test_successful_execution(self, retry_handler):
        """Test successful execution without retries"""
        async def successful_function():
            return "success"
        
        result = await retry_handler.execute(successful_function)
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_retry_on_failure(self, retry_handler):
        """Test retry mechanism on failures"""
        call_count = 0
        
        async def failing_then_succeeding_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception(f"Failure {call_count}")
            return "success_after_retries"
        
        with patch('asyncio.sleep'):  # Mock sleep to speed up test
            result = await retry_handler.execute(failing_then_succeeding_function)
        
        assert result == "success_after_retries"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, retry_handler):
        """Test behavior when max retries are exceeded"""
        call_count = 0
        
        async def always_failing_function():
            nonlocal call_count
            call_count += 1
            raise Exception(f"Failure {call_count}")
        
        with patch('asyncio.sleep'):
            with pytest.raises(Exception, match="Failure 4"):
                await retry_handler.execute(always_failing_function)
        
        assert call_count == 4  # Initial call + 3 retries
    
    @pytest.mark.asyncio
    async def test_exponential_backoff_delays(self):
        """Test exponential backoff delay calculation"""
        retry_handler = RetryWithExponentialBackoff(max_retries=3, base_delay=1.0, max_delay=10.0)
        
        call_count = 0
        sleep_delays = []
        
        async def always_failing_function():
            nonlocal call_count
            call_count += 1
            raise Exception(f"Failure {call_count}")
        
        async def mock_sleep(delay):
            sleep_delays.append(delay)
        
        with patch('asyncio.sleep', side_effect=mock_sleep):
            with pytest.raises(Exception):
                await retry_handler.execute(always_failing_function)
        
        # Check exponential backoff: 1.0, 2.0, 4.0
        assert len(sleep_delays) == 3
        assert sleep_delays[0] == 1.0
        assert sleep_delays[1] == 2.0
        assert sleep_delays[2] == 4.0

class TestRetryDecorator:
    """Test suite for retry decorator"""
    
    @pytest.mark.asyncio
    async def test_retry_decorator_success(self):
        """Test retry decorator with successful function"""
        call_count = 0
        
        @retry_with_backoff(max_retries=2, base_delay=0.1)
        async def test_function():
            nonlocal call_count
            call_count += 1
            return f"success_{call_count}"
        
        result = await test_function()
        assert result == "success_1"
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_retry_decorator_with_failures(self):
        """Test retry decorator with initial failures"""
        call_count = 0
        
        @retry_with_backoff(max_retries=2, base_delay=0.1)
        async def test_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception(f"Failure {call_count}")
            return "success_after_retries"
        
        with patch('asyncio.sleep'):
            result = await test_function()
        
        assert result == "success_after_retries"
        assert call_count == 3

class TestIntegratedResilience:
    """Test suite for integrated resilience patterns"""
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_with_retry(self):
        """Test circuit breaker combined with retry logic"""
        call_count = 0
        
        @circuit_breaker("integrated_test", CircuitBreakerConfig(failure_threshold=5))
        @retry_with_backoff(max_retries=2, base_delay=0.1)
        async def resilient_function(should_fail=False):
            nonlocal call_count
            call_count += 1
            if should_fail:
                raise Exception(f"Failure {call_count}")
            return f"success_{call_count}"
        
        # Test successful execution
        with patch('asyncio.sleep'):
            result = await resilient_function(False)
            assert result == "success_1"
        
        # Test with retries
        call_count = 0
        with patch('asyncio.sleep'):
            try:
                await resilient_function(True)
            except CircuitBreakerError:
                pass  # Expected after retries fail
        
        # Should have tried 3 times (initial + 2 retries)
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_performance_under_load(self):
        """Test performance of resilience patterns under load"""
        import time
        
        @circuit_breaker("performance_test", CircuitBreakerConfig(failure_threshold=10))
        async def fast_function():
            await asyncio.sleep(0.001)  # 1ms
            return "fast_result"
        
        # Measure time for 100 calls
        start_time = time.time()
        
        tasks = [fast_function() for _ in range(100)]
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete quickly (under 1 second for 100 calls)
        assert total_time < 1.0
        assert len(results) == 100
        assert all(result == "fast_result" for result in results)

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=apps.backend.services.circuit_breaker_service", "--cov-report=html"])