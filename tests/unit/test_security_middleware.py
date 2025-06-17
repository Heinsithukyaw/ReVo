"""
Comprehensive test suite for security middleware
Ensures enterprise-grade security headers and protection
"""

import pytest
import asyncio
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import time

from apps.backend.middleware.security_middleware import (
    SecurityHeadersMiddleware,
    CORSSecurityMiddleware,
    RateLimitingMiddleware
)

class TestSecurityHeadersMiddleware:
    """Test suite for SecurityHeadersMiddleware"""
    
    @pytest.fixture
    def app_with_security_headers(self):
        """Create FastAPI app with security headers middleware"""
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware)
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        @app.get("/error")
        async def error_endpoint():
            raise Exception("Test error")
        
        return app
    
    @pytest.fixture
    def client(self, app_with_security_headers):
        """Create test client"""
        return TestClient(app_with_security_headers)
    
    def test_security_headers_applied_to_successful_response(self, client):
        """Test that all security headers are applied to successful responses"""
        response = client.get("/test")
        
        assert response.status_code == 200
        
        # Check all required security headers
        expected_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Server": "reVoAgent-Enterprise"
        }
        
        for header_name, expected_value in expected_headers.items():
            assert header_name in response.headers
            assert response.headers[header_name] == expected_value
    
    def test_content_security_policy_header(self, client):
        """Test Content Security Policy header is properly set"""
        response = client.get("/test")
        
        csp_header = response.headers.get("Content-Security-Policy")
        assert csp_header is not None
        
        # Check key CSP directives
        assert "default-src 'self'" in csp_header
        assert "frame-ancestors 'none'" in csp_header
        assert "base-uri 'self'" in csp_header
    
    def test_permissions_policy_header(self, client):
        """Test Permissions Policy header restricts dangerous features"""
        response = client.get("/test")
        
        permissions_policy = response.headers.get("Permissions-Policy")
        assert permissions_policy is not None
        
        # Check that dangerous features are disabled
        dangerous_features = ["geolocation", "microphone", "camera", "payment"]
        for feature in dangerous_features:
            assert f"{feature}=()" in permissions_policy
    
    def test_cache_control_headers(self, client):
        """Test cache control headers for sensitive data protection"""
        response = client.get("/test")
        
        assert response.headers.get("Cache-Control") == "no-store, no-cache, must-revalidate, private"
        assert response.headers.get("Pragma") == "no-cache"
        assert response.headers.get("Expires") == "0"
    
    def test_cross_origin_headers(self, client):
        """Test Cross-Origin security headers"""
        response = client.get("/test")
        
        assert response.headers.get("Cross-Origin-Embedder-Policy") == "require-corp"
        assert response.headers.get("Cross-Origin-Opener-Policy") == "same-origin"
        assert response.headers.get("Cross-Origin-Resource-Policy") == "same-origin"
    
    def test_security_headers_applied_to_error_responses(self, client):
        """Test that security headers are applied even to error responses"""
        response = client.get("/error")
        
        assert response.status_code == 500
        
        # Security headers should still be present
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "X-XSS-Protection" in response.headers

class TestCORSSecurityMiddleware:
    """Test suite for CORSSecurityMiddleware"""
    
    @pytest.fixture
    def app_with_cors_security(self):
        """Create FastAPI app with CORS security middleware"""
        app = FastAPI()
        app.add_middleware(
            CORSSecurityMiddleware,
            allowed_origins=["http://localhost:3000", "https://app.example.com"],
            allowed_methods=["GET", "POST", "PUT", "DELETE"]
        )
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        @app.post("/test")
        async def test_post_endpoint():
            return {"message": "post test"}
        
        return app
    
    @pytest.fixture
    def cors_client(self, app_with_cors_security):
        """Create test client for CORS testing"""
        return TestClient(app_with_cors_security)
    
    def test_preflight_request_allowed_origin(self, cors_client):
        """Test preflight request with allowed origin"""
        response = cors_client.options(
            "/test",
            headers={"Origin": "http://localhost:3000"}
        )
        
        assert response.status_code == 200
        assert response.headers.get("Access-Control-Allow-Origin") == "http://localhost:3000"
        assert "GET" in response.headers.get("Access-Control-Allow-Methods", "")
        assert response.headers.get("Access-Control-Allow-Credentials") == "true"
    
    def test_preflight_request_disallowed_origin(self, cors_client):
        """Test preflight request with disallowed origin"""
        response = cors_client.options(
            "/test",
            headers={"Origin": "http://malicious-site.com"}
        )
        
        assert response.status_code == 200
        assert "Access-Control-Allow-Origin" not in response.headers
    
    def test_actual_request_allowed_origin(self, cors_client):
        """Test actual request with allowed origin"""
        response = cors_client.get(
            "/test",
            headers={"Origin": "https://app.example.com"}
        )
        
        assert response.status_code == 200
        assert response.headers.get("Access-Control-Allow-Origin") == "https://app.example.com"
        assert response.headers.get("Access-Control-Allow-Credentials") == "true"
        assert response.headers.get("Vary") == "Origin"
    
    def test_actual_request_disallowed_origin(self, cors_client):
        """Test actual request with disallowed origin"""
        response = cors_client.get(
            "/test",
            headers={"Origin": "http://evil-site.com"}
        )
        
        assert response.status_code == 200
        assert "Access-Control-Allow-Origin" not in response.headers

class TestRateLimitingMiddleware:
    """Test suite for RateLimitingMiddleware"""
    
    @pytest.fixture
    def app_with_rate_limiting(self):
        """Create FastAPI app with rate limiting middleware"""
        app = FastAPI()
        app.add_middleware(
            RateLimitingMiddleware,
            requests_per_minute=5  # Low limit for testing
        )
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        return app
    
    @pytest.fixture
    def rate_limit_client(self, app_with_rate_limiting):
        """Create test client for rate limiting testing"""
        return TestClient(app_with_rate_limiting)
    
    def test_requests_within_limit(self, rate_limit_client):
        """Test that requests within limit are allowed"""
        # Make 3 requests (within limit of 5)
        for i in range(3):
            response = rate_limit_client.get("/test")
            assert response.status_code == 200
            
            # Check rate limit headers
            assert "X-RateLimit-Limit" in response.headers
            assert "X-RateLimit-Remaining" in response.headers
            assert "X-RateLimit-Reset" in response.headers
            
            assert response.headers["X-RateLimit-Limit"] == "5"
            remaining = int(response.headers["X-RateLimit-Remaining"])
            assert remaining == 5 - (i + 1)
    
    def test_rate_limit_exceeded(self, rate_limit_client):
        """Test that requests exceeding limit are blocked"""
        # Make requests up to the limit
        for i in range(5):
            response = rate_limit_client.get("/test")
            assert response.status_code == 200
        
        # Next request should be rate limited
        response = rate_limit_client.get("/test")
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.text
        assert "Retry-After" in response.headers
        assert response.headers["Retry-After"] == "60"
    
    def test_rate_limit_headers_present(self, rate_limit_client):
        """Test that rate limit headers are always present"""
        response = rate_limit_client.get("/test")
        
        assert response.status_code == 200
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
        
        assert response.headers["X-RateLimit-Limit"] == "5"
        assert int(response.headers["X-RateLimit-Remaining"]) >= 0
    
    @patch('time.time')
    def test_rate_limit_window_reset(self, mock_time, rate_limit_client):
        """Test that rate limit window resets after time period"""
        # Start at time 0
        mock_time.return_value = 0
        
        # Make requests up to limit
        for i in range(5):
            response = rate_limit_client.get("/test")
            assert response.status_code == 200
        
        # Next request should be blocked
        response = rate_limit_client.get("/test")
        assert response.status_code == 429
        
        # Advance time by 61 seconds (past the window)
        mock_time.return_value = 61
        
        # Request should now be allowed (new window)
        response = rate_limit_client.get("/test")
        assert response.status_code == 200

class TestIntegratedSecurityMiddleware:
    """Test suite for integrated security middleware stack"""
    
    @pytest.fixture
    def app_with_all_security(self):
        """Create FastAPI app with all security middleware"""
        app = FastAPI()
        
        # Add all security middleware in correct order
        app.add_middleware(SecurityHeadersMiddleware)
        app.add_middleware(RateLimitingMiddleware, requests_per_minute=10)
        app.add_middleware(
            CORSSecurityMiddleware,
            allowed_origins=["http://localhost:3000"]
        )
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        return app
    
    @pytest.fixture
    def integrated_client(self, app_with_all_security):
        """Create test client for integrated testing"""
        return TestClient(app_with_all_security)
    
    def test_all_security_features_work_together(self, integrated_client):
        """Test that all security middleware work together correctly"""
        response = integrated_client.get(
            "/test",
            headers={"Origin": "http://localhost:3000"}
        )
        
        assert response.status_code == 200
        
        # Check security headers are present
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        
        # Check CORS headers are present
        assert response.headers.get("Access-Control-Allow-Origin") == "http://localhost:3000"
        
        # Check rate limit headers are present
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
    
    def test_security_middleware_order_preserved(self, integrated_client):
        """Test that middleware order is preserved and all features work"""
        # Make multiple requests to test rate limiting
        for i in range(3):
            response = integrated_client.get(
                "/test",
                headers={"Origin": "http://localhost:3000"}
            )
            
            assert response.status_code == 200
            
            # All security features should be present
            assert "X-Content-Type-Options" in response.headers
            assert "Access-Control-Allow-Origin" in response.headers
            assert "X-RateLimit-Remaining" in response.headers
            
            # Rate limit should decrease
            remaining = int(response.headers["X-RateLimit-Remaining"])
            assert remaining == 10 - (i + 1)

class TestSecurityMiddlewarePerformance:
    """Test suite for security middleware performance"""
    
    @pytest.fixture
    def performance_app(self):
        """Create app for performance testing"""
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware)
        app.add_middleware(RateLimitingMiddleware)
        app.add_middleware(CORSSecurityMiddleware)
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        return app
    
    @pytest.fixture
    def performance_client(self, performance_app):
        """Create client for performance testing"""
        return TestClient(performance_app)
    
    def test_middleware_performance_overhead(self, performance_client):
        """Test that security middleware doesn't add significant overhead"""
        import time
        
        # Measure response time with security middleware
        start_time = time.time()
        for _ in range(100):
            response = performance_client.get("/test")
            assert response.status_code == 200
        end_time = time.time()
        
        total_time = end_time - start_time
        avg_time_per_request = total_time / 100
        
        # Security middleware should add minimal overhead (<10ms per request)
        assert avg_time_per_request < 0.01, f"Average time per request: {avg_time_per_request:.4f}s"
    
    def test_concurrent_requests_handling(self, performance_client):
        """Test that security middleware handles concurrent requests properly"""
        import concurrent.futures
        import threading
        
        def make_request():
            response = performance_client.get("/test")
            return response.status_code == 200
        
        # Make 50 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(50)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All requests should succeed (within rate limit)
        success_count = sum(results)
        assert success_count >= 10, f"Only {success_count} out of 50 requests succeeded"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])