"""
Enterprise Security Headers Middleware
Implements comprehensive security headers for production deployment
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Enterprise-grade security headers middleware
    Implements OWASP security header recommendations
    """
    
    def __init__(self, app, config: Dict[str, Any] = None):
        super().__init__(app)
        self.config = config or {}
        self.security_headers = self._get_security_headers()
    
    def _get_security_headers(self) -> Dict[str, str]:
        """Get comprehensive security headers configuration"""
        return {
            # Prevent MIME type sniffing
            "X-Content-Type-Options": "nosniff",
            
            # Prevent clickjacking attacks
            "X-Frame-Options": "DENY",
            
            # Enable XSS protection
            "X-XSS-Protection": "1; mode=block",
            
            # Enforce HTTPS
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
            
            # Content Security Policy
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' https:; "
                "connect-src 'self' ws: wss:; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            ),
            
            # Referrer policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Permissions policy
            "Permissions-Policy": (
                "geolocation=(), "
                "microphone=(), "
                "camera=(), "
                "payment=(), "
                "usb=(), "
                "magnetometer=(), "
                "gyroscope=(), "
                "speaker=()"
            ),
            
            # Cross-Origin policies
            "Cross-Origin-Embedder-Policy": "require-corp",
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Resource-Policy": "same-origin",
            
            # Cache control for sensitive data
            "Cache-Control": "no-store, no-cache, must-revalidate, private",
            "Pragma": "no-cache",
            "Expires": "0",
            
            # Server information hiding
            "Server": "reVoAgent-Enterprise"
        }
    
    async def dispatch(self, request: Request, call_next):
        """Apply security headers to all responses"""
        try:
            # Process the request
            response = await call_next(request)
            
            # Apply security headers
            for header_name, header_value in self.security_headers.items():
                response.headers[header_name] = header_value
            
            # Log security header application for audit
            logger.debug(f"Applied security headers to {request.url.path}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error in security middleware: {str(e)}")
            # Create error response with security headers
            response = Response(
                content="Internal Server Error",
                status_code=500,
                media_type="text/plain"
            )
            
            # Still apply security headers to error responses
            for header_name, header_value in self.security_headers.items():
                response.headers[header_name] = header_value
            
            return response

class CORSSecurityMiddleware(BaseHTTPMiddleware):
    """
    Secure CORS middleware with enterprise configuration
    """
    
    def __init__(self, app, allowed_origins: list = None, allowed_methods: list = None):
        super().__init__(app)
        self.allowed_origins = allowed_origins or ["http://localhost:12000", "https://app.revoagent.dev"]
        self.allowed_methods = allowed_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.allowed_headers = [
            "Accept",
            "Accept-Language",
            "Content-Language",
            "Content-Type",
            "Authorization",
            "X-Requested-With",
            "X-API-Key"
        ]
    
    async def dispatch(self, request: Request, call_next):
        """Handle CORS with security considerations"""
        
        # Handle preflight requests
        if request.method == "OPTIONS":
            response = Response()
            origin = request.headers.get("origin")
            
            if origin in self.allowed_origins:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allowed_methods)
                response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allowed_headers)
                response.headers["Access-Control-Max-Age"] = "86400"  # 24 hours
                response.headers["Access-Control-Allow-Credentials"] = "true"
            
            return response
        
        # Process normal requests
        response = await call_next(request)
        
        # Add CORS headers to response
        origin = request.headers.get("origin")
        if origin in self.allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Vary"] = "Origin"
        
        return response

class RateLimitingMiddleware(BaseHTTPMiddleware):
    """
    Enterprise rate limiting middleware
    """
    
    def __init__(self, app, requests_per_minute: int = 100):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts = {}
        self.window_start = {}
    
    async def dispatch(self, request: Request, call_next):
        """Apply rate limiting"""
        import time
        
        client_ip = self._get_client_ip(request)
        current_time = time.time()
        window_start = self.window_start.get(client_ip, current_time)
        
        # Reset window if more than 60 seconds have passed
        if current_time - window_start > 60:
            self.request_counts[client_ip] = 0
            self.window_start[client_ip] = current_time
        
        # Increment request count
        self.request_counts[client_ip] = self.request_counts.get(client_ip, 0) + 1
        
        # Check rate limit
        if self.request_counts[client_ip] > self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            response = Response(
                content="Rate limit exceeded. Please try again later.",
                status_code=429,
                media_type="text/plain"
            )
            response.headers["Retry-After"] = "60"
            return response
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = max(0, self.requests_per_minute - self.request_counts[client_ip])
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(window_start + 60))
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address with proxy support"""
        # Check for forwarded headers (common in production)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        return request.client.host if request.client else "unknown"