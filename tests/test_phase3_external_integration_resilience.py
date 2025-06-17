#!/usr/bin/env python3
"""
Comprehensive Test Suite for Phase 3 External Integration Resilience
Tests API Gateway, Webhook Manager, Integration Monitor, and Phase 3 Integration System
"""

import asyncio
import pytest
import json
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

# Import Phase 3 components
from packages.integrations.api_gateway import (
    APIGateway, IntegrationType, IntegrationConfig, APIRequest, APIResponse,
    RequestMethod, RetryStrategy, RateLimitConfig, RetryConfig, TimeoutConfig
)
from packages.integrations.webhook_manager import (
    WebhookManager, WebhookEventType, WebhookConfig, WebhookHandler, WebhookEvent
)
from packages.integrations.integration_monitor import (
    IntegrationMonitor, HealthCheck, AlertRule, AlertSeverity, Metric, MetricType
)
from packages.integrations.phase3_integration import (
    Phase3IntegrationSystem, IntegrationEndpoint
)

class TestAPIGateway:
    """Test API Gateway functionality"""
    
    @pytest.fixture
    async def api_gateway(self):
        """Create API Gateway instance for testing"""
        gateway = APIGateway()
        await gateway.start()
        yield gateway
        await gateway.stop()
        
    @pytest.fixture
    def github_config(self):
        """GitHub integration configuration"""
        return IntegrationConfig(
            integration_type=IntegrationType.GITHUB,
            base_url="https://api.github.com",
            api_key="test_token",
            headers={"Authorization": "token test_token"},
            rate_limit=RateLimitConfig(requests_per_minute=60),
            retry=RetryConfig(max_attempts=3),
            timeout=TimeoutConfig(total_timeout=30.0)
        )
        
    async def test_integration_registration(self, api_gateway, github_config):
        """Test integration registration"""
        api_gateway.register_integration(github_config)
        
        assert IntegrationType.GITHUB in api_gateway.integrations
        assert IntegrationType.GITHUB in api_gateway.rate_limiters
        assert IntegrationType.GITHUB in api_gateway.circuit_breakers
        
    async def test_rate_limiting(self, api_gateway, github_config):
        """Test rate limiting functionality"""
        # Configure very low rate limit for testing
        github_config.rate_limit.requests_per_minute = 2
        github_config.rate_limit.burst_limit = 1
        
        api_gateway.register_integration(github_config)
        rate_limiter = api_gateway.rate_limiters[IntegrationType.GITHUB]
        
        # First request should succeed
        assert await rate_limiter.acquire() == True
        
        # Second request should fail (burst limit exceeded)
        assert await rate_limiter.acquire() == False
        
        # Check wait time
        wait_time = rate_limiter.get_wait_time()
        assert wait_time > 0
        
    async def test_circuit_breaker(self, api_gateway, github_config):
        """Test circuit breaker functionality"""
        api_gateway.register_integration(github_config)
        circuit_breaker = api_gateway.circuit_breakers[IntegrationType.GITHUB]
        
        # Simulate failures to trigger circuit breaker
        for _ in range(github_config.circuit_breaker.failure_threshold):
            circuit_breaker._on_failure()
            
        # Circuit breaker should be open
        from packages.integrations.api_gateway import CircuitBreakerState
        assert circuit_breaker.state == CircuitBreakerState.OPEN
        
        # Requests should fail
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            await circuit_breaker.call(lambda: None)
            
    @patch('aiohttp.ClientSession.request')
    async def test_successful_request(self, mock_request, api_gateway, github_config):
        """Test successful API request"""
        # Mock successful response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text.return_value = '{"test": "data"}'
        mock_request.return_value.__aenter__.return_value = mock_response
        
        api_gateway.register_integration(github_config)
        
        request = APIRequest(
            method=RequestMethod.GET,
            endpoint="/test"
        )
        
        response = await api_gateway.make_request(IntegrationType.GITHUB, request)
        
        assert response.status_code == 200
        assert response.data == {"test": "data"}
        assert response.retry_count == 0
        
    @patch('aiohttp.ClientSession.request')
    async def test_retry_logic(self, mock_request, api_gateway, github_config):
        """Test retry logic on failures"""
        # Configure for quick testing
        github_config.retry.max_attempts = 2
        github_config.retry.base_delay = 0.1
        
        # Mock failing then successful response
        mock_response_fail = AsyncMock()
        mock_response_fail.status = 500
        mock_response_fail.headers = {}
        mock_response_fail.text.return_value = "Server Error"
        
        mock_response_success = AsyncMock()
        mock_response_success.status = 200
        mock_response_success.headers = {"Content-Type": "application/json"}
        mock_response_success.text.return_value = '{"test": "data"}'
        
        mock_request.return_value.__aenter__.side_effect = [
            mock_response_fail,
            mock_response_success
        ]
        
        api_gateway.register_integration(github_config)
        
        request = APIRequest(
            method=RequestMethod.GET,
            endpoint="/test"
        )
        
        response = await api_gateway.make_request(IntegrationType.GITHUB, request)
        
        assert response.status_code == 200
        assert response.retry_count == 1
        
    async def test_health_status(self, api_gateway, github_config):
        """Test integration health status"""
        api_gateway.register_integration(github_config)
        
        health = await api_gateway.get_integration_health(IntegrationType.GITHUB)
        
        assert "status" in health
        assert "circuit_breaker_state" in health
        assert "rate_limit_tokens" in health
        assert "total_requests" in health

class TestWebhookManager:
    """Test Webhook Manager functionality"""
    
    @pytest.fixture
    async def webhook_manager(self):
        """Create Webhook Manager instance for testing"""
        manager = WebhookManager()
        await manager.start(num_workers=1)
        yield manager
        await manager.stop()
        
    @pytest.fixture
    def github_webhook_config(self):
        """GitHub webhook configuration"""
        return WebhookConfig(
            event_type=WebhookEventType.GITHUB_PUSH,
            endpoint="/webhooks/github",
            secret="test_secret",
            max_retries=2,
            retry_delay=0.1,
            timeout=5.0
        )
        
    async def test_webhook_registration(self, webhook_manager, github_webhook_config):
        """Test webhook registration"""
        webhook_manager.register_webhook(github_webhook_config)
        
        assert WebhookEventType.GITHUB_PUSH in webhook_manager.configs
        assert WebhookEventType.GITHUB_PUSH in webhook_manager.rate_limiters
        
    async def test_signature_verification(self, webhook_manager, github_webhook_config):
        """Test webhook signature verification"""
        webhook_manager.register_webhook(github_webhook_config)
        
        # Create test payload
        payload = {"test": "data"}
        payload_str = json.dumps(payload, separators=(',', ':'))
        
        # Generate correct signature
        import hmac
        import hashlib
        signature = hmac.new(
            github_webhook_config.secret.encode('utf-8'),
            payload_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        signature = f"sha256={signature}"
        
        # Test with correct signature
        event_id = await webhook_manager.receive_webhook(
            event_type=WebhookEventType.GITHUB_PUSH,
            source="github",
            headers={"X-Hub-Signature-256": signature},
            payload=payload,
            signature=signature
        )
        
        assert event_id is not None
        
        # Test with incorrect signature
        with pytest.raises(ValueError, match="Invalid webhook signature"):
            await webhook_manager.receive_webhook(
                event_type=WebhookEventType.GITHUB_PUSH,
                source="github",
                headers={"X-Hub-Signature-256": "sha256=invalid"},
                payload=payload,
                signature="sha256=invalid"
            )
            
    async def test_webhook_processing(self, webhook_manager, github_webhook_config):
        """Test webhook event processing"""
        webhook_manager.register_webhook(github_webhook_config)
        
        # Register test handler
        processed_events = []
        
        async def test_handler(event):
            processed_events.append(event)
            
        handler = WebhookHandler(
            event_type=WebhookEventType.GITHUB_PUSH,
            handler_func=test_handler,
            async_handler=True
        )
        webhook_manager.register_handler(handler)
        
        # Send webhook
        payload = {"test": "data"}
        event_id = await webhook_manager.receive_webhook(
            event_type=WebhookEventType.GITHUB_PUSH,
            source="github",
            headers={},
            payload=payload
        )
        
        # Wait for processing
        await asyncio.sleep(0.2)
        
        assert len(processed_events) == 1
        assert processed_events[0].id == event_id
        assert processed_events[0].payload == payload
        
    async def test_webhook_retry(self, webhook_manager, github_webhook_config):
        """Test webhook retry mechanism"""
        github_webhook_config.max_retries = 2
        github_webhook_config.retry_delay = 0.1
        
        webhook_manager.register_webhook(github_webhook_config)
        
        # Register failing handler
        call_count = 0
        
        async def failing_handler(event):
            nonlocal call_count
            call_count += 1
            if call_count < 3:  # Fail first 2 times
                raise Exception("Handler failed")
                
        handler = WebhookHandler(
            event_type=WebhookEventType.GITHUB_PUSH,
            handler_func=failing_handler,
            async_handler=True
        )
        webhook_manager.register_handler(handler)
        
        # Send webhook
        await webhook_manager.receive_webhook(
            event_type=WebhookEventType.GITHUB_PUSH,
            source="github",
            headers={},
            payload={"test": "data"}
        )
        
        # Wait for retries
        await asyncio.sleep(0.5)
        
        assert call_count == 3  # Initial + 2 retries
        
    async def test_webhook_stats(self, webhook_manager, github_webhook_config):
        """Test webhook statistics"""
        webhook_manager.register_webhook(github_webhook_config)
        
        # Register simple handler
        async def simple_handler(event):
            pass
            
        handler = WebhookHandler(
            event_type=WebhookEventType.GITHUB_PUSH,
            handler_func=simple_handler,
            async_handler=True
        )
        webhook_manager.register_handler(handler)
        
        # Send webhook
        await webhook_manager.receive_webhook(
            event_type=WebhookEventType.GITHUB_PUSH,
            source="github",
            headers={},
            payload={"test": "data"}
        )
        
        # Wait for processing
        await asyncio.sleep(0.2)
        
        stats = await webhook_manager.get_webhook_stats(WebhookEventType.GITHUB_PUSH)
        
        assert stats["processed"] >= 1
        assert "success_rate" in stats
        assert "avg_processing_time" in stats

class TestIntegrationMonitor:
    """Test Integration Monitor functionality"""
    
    @pytest.fixture
    async def integration_monitor(self):
        """Create Integration Monitor instance for testing"""
        monitor = IntegrationMonitor()
        await monitor.start()
        yield monitor
        await monitor.stop()
        
    @pytest.fixture
    def test_health_check(self):
        """Test health check configuration"""
        return HealthCheck(
            name="test_service",
            endpoint="https://httpbin.org/status/200",
            method="GET",
            timeout=5.0,
            interval=10.0,
            expected_status=200
        )
        
    async def test_health_check_registration(self, integration_monitor, test_health_check):
        """Test health check registration"""
        integration_monitor.register_health_check(test_health_check)
        
        assert test_health_check.name in integration_monitor.health_checker.health_checks
        
    async def test_metric_recording(self, integration_monitor):
        """Test metric recording and retrieval"""
        metric = Metric(
            name="test_metric",
            value=42.0,
            metric_type=MetricType.GAUGE,
            labels={"test": "label"}
        )
        
        await integration_monitor.record_metric(metric)
        
        # Get metrics
        metrics = await integration_monitor.metric_collector.get_metrics("test_metric", 10)
        
        assert len(metrics) >= 1
        assert metrics[-1].value == 42.0
        assert metrics[-1].labels == {"test": "label"}
        
    async def test_metric_summary(self, integration_monitor):
        """Test metric summary calculation"""
        # Record multiple metrics
        for i in range(5):
            metric = Metric(
                name="test_summary",
                value=float(i + 1),
                metric_type=MetricType.GAUGE
            )
            await integration_monitor.record_metric(metric)
            
        summary = await integration_monitor.metric_collector.get_metric_summary("test_summary", 60)
        
        assert summary["count"] == 5
        assert summary["min"] == 1.0
        assert summary["max"] == 5.0
        assert summary["avg"] == 3.0
        assert summary["latest"] == 5.0
        
    async def test_alert_rules(self, integration_monitor):
        """Test alert rule registration and checking"""
        # Register alert rule
        alert_rule = AlertRule(
            name="test_alert",
            metric_name="test_alert_metric",
            condition="> 10",
            severity=AlertSeverity.WARNING,
            description="Test alert"
        )
        
        integration_monitor.register_alert_rule(alert_rule)
        
        assert alert_rule.name in integration_monitor.alert_manager.alert_rules
        
        # Record metric that should trigger alert
        metric = Metric(
            name="test_alert_metric",
            value=15.0,
            metric_type=MetricType.GAUGE
        )
        await integration_monitor.record_metric(metric)
        
        # Check alerts
        await integration_monitor.alert_manager.check_alerts()
        
        active_alerts = await integration_monitor.alert_manager.get_active_alerts()
        assert len(active_alerts) >= 1
        
        # Find our alert
        test_alert = next((a for a in active_alerts if a.rule_name == "test_alert"), None)
        assert test_alert is not None
        assert test_alert.current_value == 15.0
        
    async def test_system_status(self, integration_monitor):
        """Test system status reporting"""
        status = await integration_monitor.get_system_status()
        
        assert "status" in status
        assert "timestamp" in status
        assert "health_checks" in status
        assert "active_alerts" in status

class TestPhase3IntegrationSystem:
    """Test Phase 3 Integration System"""
    
    @pytest.fixture
    async def phase3_system(self):
        """Create Phase 3 Integration System for testing"""
        system = Phase3IntegrationSystem()
        await system.start()
        yield system
        await system.stop()
        
    @pytest.fixture
    def test_integration_endpoint(self):
        """Test integration endpoint"""
        return IntegrationEndpoint(
            name="test_api",
            integration_type=IntegrationType.CUSTOM,
            base_url="https://httpbin.org",
            health_endpoint="https://httpbin.org/status/200",
            rate_limit_per_minute=60,
            timeout_seconds=10.0,
            cache_ttl_seconds=300
        )
        
    async def test_integration_registration(self, phase3_system, test_integration_endpoint):
        """Test integration registration"""
        await phase3_system.register_integration(test_integration_endpoint)
        
        assert test_integration_endpoint.name in phase3_system.integrations
        
        # Check that components were configured
        assert IntegrationType.CUSTOM in phase3_system.api_gateway.integrations
        
    async def test_integration_enable_disable(self, phase3_system, test_integration_endpoint):
        """Test enabling and disabling integrations"""
        await phase3_system.register_integration(test_integration_endpoint)
        
        # Disable integration
        await phase3_system.disable_integration(test_integration_endpoint.name)
        assert not phase3_system.integrations[test_integration_endpoint.name].enabled
        
        # Enable integration
        await phase3_system.enable_integration(test_integration_endpoint.name)
        assert phase3_system.integrations[test_integration_endpoint.name].enabled
        
    @patch('aiohttp.ClientSession.request')
    async def test_make_request(self, mock_request, phase3_system, test_integration_endpoint):
        """Test making requests through the system"""
        # Mock successful response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text.return_value = '{"test": "response"}'
        mock_request.return_value.__aenter__.return_value = mock_response
        
        await phase3_system.register_integration(test_integration_endpoint)
        
        request = APIRequest(
            method=RequestMethod.GET,
            endpoint="/get"
        )
        
        response = await phase3_system.make_request(test_integration_endpoint.name, request)
        
        assert response.status_code == 200
        assert response.data == {"test": "response"}
        
    async def test_webhook_receiving(self, phase3_system, test_integration_endpoint):
        """Test receiving webhooks through the system"""
        test_integration_endpoint.webhook_secret = "test_secret"
        await phase3_system.register_integration(test_integration_endpoint)
        
        event_id = await phase3_system.receive_webhook(
            integration_name=test_integration_endpoint.name,
            event_type=WebhookEventType.CUSTOM,
            headers={},
            payload={"test": "webhook"}
        )
        
        assert event_id is not None
        
    async def test_system_status(self, phase3_system, test_integration_endpoint):
        """Test system status reporting"""
        await phase3_system.register_integration(test_integration_endpoint)
        
        status = await phase3_system.get_system_status()
        
        assert "status" in status
        assert "components" in status
        assert "integrations" in status
        assert "metrics" in status
        assert status["registered_integrations"] >= 1
        
    async def test_integration_status(self, phase3_system, test_integration_endpoint):
        """Test individual integration status"""
        await phase3_system.register_integration(test_integration_endpoint)
        
        status = await phase3_system.get_integration_status(test_integration_endpoint.name)
        
        assert status["name"] == test_integration_endpoint.name
        assert status["type"] == test_integration_endpoint.integration_type.value
        assert status["enabled"] == test_integration_endpoint.enabled
        assert "health" in status
        assert "api_gateway" in status
        assert "configuration" in status

class TestIntegrationResilience:
    """Test integration resilience patterns"""
    
    @pytest.fixture
    async def resilient_system(self):
        """Create system for resilience testing"""
        system = Phase3IntegrationSystem()
        await system.start()
        
        # Register test integration
        endpoint = IntegrationEndpoint(
            name="resilience_test",
            integration_type=IntegrationType.CUSTOM,
            base_url="https://httpbin.org",
            health_endpoint="https://httpbin.org/status/200",
            rate_limit_per_minute=10,  # Low limit for testing
            timeout_seconds=5.0
        )
        await system.register_integration(endpoint)
        
        yield system
        await system.stop()
        
    @patch('aiohttp.ClientSession.request')
    async def test_rate_limit_resilience(self, mock_request, resilient_system):
        """Test rate limiting resilience"""
        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {}
        mock_response.text.return_value = '{"success": true}'
        mock_request.return_value.__aenter__.return_value = mock_response
        
        # Make requests up to rate limit
        request = APIRequest(method=RequestMethod.GET, endpoint="/get")
        
        # First few requests should succeed
        for _ in range(3):
            response = await resilient_system.make_request("resilience_test", request)
            assert response.status_code == 200
            
        # Eventually should hit rate limit
        with pytest.raises(Exception, match="Rate limit exceeded"):
            for _ in range(20):  # Try many requests
                await resilient_system.make_request("resilience_test", request)
                
    @patch('aiohttp.ClientSession.request')
    async def test_timeout_resilience(self, mock_request, resilient_system):
        """Test timeout resilience"""
        # Mock timeout
        mock_request.side_effect = asyncio.TimeoutError("Request timeout")
        
        request = APIRequest(method=RequestMethod.GET, endpoint="/slow")
        
        with pytest.raises(Exception):
            await resilient_system.make_request("resilience_test", request)
            
    @patch('aiohttp.ClientSession.request')
    async def test_circuit_breaker_resilience(self, mock_request, resilient_system):
        """Test circuit breaker resilience"""
        # Mock server errors
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.headers = {}
        mock_response.text.return_value = "Server Error"
        mock_request.return_value.__aenter__.return_value = mock_response
        
        request = APIRequest(method=RequestMethod.GET, endpoint="/error")
        
        # Make requests to trigger circuit breaker
        for _ in range(6):  # More than failure threshold
            try:
                await resilient_system.make_request("resilience_test", request)
            except Exception:
                pass  # Expected failures
                
        # Circuit breaker should now be open
        gateway_health = await resilient_system.api_gateway.get_integration_health(IntegrationType.CUSTOM)
        assert gateway_health["circuit_breaker_state"] == "open"

# Performance and Load Tests
class TestPerformanceAndLoad:
    """Test performance and load handling"""
    
    @pytest.fixture
    async def performance_system(self):
        """Create system for performance testing"""
        system = Phase3IntegrationSystem()
        await system.start()
        
        endpoint = IntegrationEndpoint(
            name="performance_test",
            integration_type=IntegrationType.CUSTOM,
            base_url="https://httpbin.org",
            health_endpoint="https://httpbin.org/status/200",
            rate_limit_per_minute=1000,  # High limit for performance testing
            timeout_seconds=30.0
        )
        await system.register_integration(endpoint)
        
        yield system
        await system.stop()
        
    @patch('aiohttp.ClientSession.request')
    async def test_concurrent_requests(self, mock_request, performance_system):
        """Test handling concurrent requests"""
        # Mock fast response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {}
        mock_response.text.return_value = '{"success": true}'
        mock_request.return_value.__aenter__.return_value = mock_response
        
        request = APIRequest(method=RequestMethod.GET, endpoint="/get")
        
        # Make concurrent requests
        tasks = []
        for _ in range(50):
            task = asyncio.create_task(
                performance_system.make_request("performance_test", request)
            )
            tasks.append(task)
            
        # Wait for all requests to complete
        start_time = time.time()
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        # Check results
        successful_responses = [r for r in responses if isinstance(r, APIResponse)]
        assert len(successful_responses) >= 40  # Most should succeed
        
        # Check performance
        total_time = end_time - start_time
        assert total_time < 10.0  # Should complete within 10 seconds
        
    async def test_webhook_load(self, performance_system):
        """Test webhook processing under load"""
        # Configure webhook
        endpoint = performance_system.integrations["performance_test"]
        endpoint.webhook_secret = "test_secret"
        
        # Send many webhooks
        webhook_tasks = []
        for i in range(100):
            task = asyncio.create_task(
                performance_system.receive_webhook(
                    integration_name="performance_test",
                    event_type=WebhookEventType.CUSTOM,
                    headers={},
                    payload={"test": f"webhook_{i}"}
                )
            )
            webhook_tasks.append(task)
            
        # Wait for all webhooks to be queued
        event_ids = await asyncio.gather(*webhook_tasks)
        
        assert len(event_ids) == 100
        assert all(event_id is not None for event_id in event_ids)
        
    async def test_metric_collection_performance(self, performance_system):
        """Test metric collection performance"""
        monitor = performance_system.monitor
        
        # Record many metrics
        start_time = time.time()
        
        tasks = []
        for i in range(1000):
            metric = Metric(
                name="performance_metric",
                value=float(i),
                metric_type=MetricType.COUNTER,
                labels={"batch": str(i // 100)}
            )
            task = asyncio.create_task(monitor.record_metric(metric))
            tasks.append(task)
            
        await asyncio.gather(*tasks)
        end_time = time.time()
        
        # Check performance
        total_time = end_time - start_time
        assert total_time < 5.0  # Should complete within 5 seconds
        
        # Verify metrics were recorded
        summary = await monitor.metric_collector.get_metric_summary("performance_metric", 60)
        assert summary["count"] >= 900  # Most should be recorded

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])