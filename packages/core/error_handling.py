# packages/core/error_handling.py
"""
Comprehensive Error Handling & Retry System for reVoAgent
Handles AI provider failures, network issues, and system errors
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, Callable, List, Union
from dataclasses import dataclass
from enum import Enum
import random
import traceback
from datetime import datetime, timedelta

class ErrorType(Enum):
    AI_PROVIDER_ERROR = "ai_provider_error"
    NETWORK_ERROR = "network_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    VALIDATION_ERROR = "validation_error"
    TIMEOUT_ERROR = "timeout_error"
    SYSTEM_ERROR = "system_error"
    WEBSOCKET_ERROR = "websocket_error"
    AUTHENTICATION_ERROR = "authentication_error"

class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ErrorContext:
    error_type: ErrorType
    severity: ErrorSeverity
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    component: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    stack_trace: Optional[str] = None

class RetryConfig:
    """Configuration for retry behavior"""
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_errors: Optional[List[ErrorType]] = None
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_errors = retryable_errors or [
            ErrorType.NETWORK_ERROR,
            ErrorType.TIMEOUT_ERROR,
            ErrorType.RATE_LIMIT_ERROR
        ]

class ErrorHandler:
    """Central error handling system"""
    
    def __init__(self):
        self.error_history: List[ErrorContext] = []
        self.error_callbacks: Dict[ErrorType, List[Callable]] = {}
        self.logger = self._setup_logger()
        self.fallback_handlers: Dict[str, Callable] = {}
        
    def _setup_logger(self) -> logging.Logger:
        """Setup structured logging"""
        logger = logging.getLogger("reVoAgent.errors")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def register_callback(self, error_type: ErrorType, callback: Callable):
        """Register callback for specific error type"""
        if error_type not in self.error_callbacks:
            self.error_callbacks[error_type] = []
        self.error_callbacks[error_type].append(callback)
    
    def register_fallback(self, component: str, handler: Callable):
        """Register fallback handler for component"""
        self.fallback_handlers[component] = handler
    
    async def handle_error(self, error: Exception, context: Dict[str, Any]) -> ErrorContext:
        """Handle error with context and trigger callbacks"""
        
        # Classify error
        error_type, severity = self._classify_error(error)
        
        # Create error context
        error_context = ErrorContext(
            error_type=error_type,
            severity=severity,
            message=str(error),
            details=context,
            timestamp=datetime.now(),
            component=context.get("component", "unknown"),
            user_id=context.get("user_id"),
            session_id=context.get("session_id"),
            request_id=context.get("request_id"),
            stack_trace=traceback.format_exc() if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL] else None
        )
        
        # Log error
        self._log_error(error_context)
        
        # Store in history
        self.error_history.append(error_context)
        
        # Trigger callbacks
        await self._trigger_callbacks(error_context)
        
        # Check for fallback
        if error_context.component in self.fallback_handlers:
            try:
                await self.fallback_handlers[error_context.component](error_context)
            except Exception as fallback_error:
                self.logger.error(f"Fallback handler failed: {fallback_error}")
        
        return error_context
    
    def _classify_error(self, error: Exception) -> tuple[ErrorType, ErrorSeverity]:
        """Classify error type and severity"""
        
        error_str = str(error).lower()
        
        # AI Provider Errors
        if any(term in error_str for term in ["api key", "authentication", "unauthorized"]):
            return ErrorType.AUTHENTICATION_ERROR, ErrorSeverity.HIGH
        
        if any(term in error_str for term in ["rate limit", "quota", "too many requests"]):
            return ErrorType.RATE_LIMIT_ERROR, ErrorSeverity.MEDIUM
        
        if any(term in error_str for term in ["openai", "anthropic", "model", "completion"]):
            return ErrorType.AI_PROVIDER_ERROR, ErrorSeverity.MEDIUM
        
        # Network Errors
        if any(term in error_str for term in ["connection", "network", "dns", "timeout"]):
            return ErrorType.NETWORK_ERROR, ErrorSeverity.MEDIUM
        
        if "timeout" in error_str:
            return ErrorType.TIMEOUT_ERROR, ErrorSeverity.MEDIUM
        
        # WebSocket Errors
        if any(term in error_str for term in ["websocket", "ws", "connection closed"]):
            return ErrorType.WEBSOCKET_ERROR, ErrorSeverity.LOW
        
        # Validation Errors
        if any(term in error_str for term in ["validation", "invalid", "missing"]):
            return ErrorType.VALIDATION_ERROR, ErrorSeverity.LOW
        
        # Default
        return ErrorType.SYSTEM_ERROR, ErrorSeverity.MEDIUM
    
    def _log_error(self, context: ErrorContext):
        """Log error with appropriate level"""
        
        log_data = {
            "error_type": context.error_type.value,
            "severity": context.severity.value,
            "component": context.component,
            "message": context.message,
            "user_id": context.user_id,
            "request_id": context.request_id,
            "timestamp": context.timestamp.isoformat()
        }
        
        if context.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(f"Critical error: {context.message}", extra=log_data)
        elif context.severity == ErrorSeverity.HIGH:
            self.logger.error(f"High severity error: {context.message}", extra=log_data)
        elif context.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(f"Medium severity error: {context.message}", extra=log_data)
        else:
            self.logger.info(f"Low severity error: {context.message}", extra=log_data)
    
    async def _trigger_callbacks(self, context: ErrorContext):
        """Trigger registered callbacks for error type"""
        
        callbacks = self.error_callbacks.get(context.error_type, [])
        
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(context)
                else:
                    callback(context)
            except Exception as callback_error:
                self.logger.error(f"Error callback failed: {callback_error}")
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics"""
        
        total_errors = len(self.error_history)
        if total_errors == 0:
            return {"total_errors": 0}
        
        # Count by type
        by_type = {}
        by_severity = {}
        by_component = {}
        
        recent_errors = [
            error for error in self.error_history 
            if error.timestamp > datetime.now() - timedelta(hours=24)
        ]
        
        for error in self.error_history:
            # By type
            error_type = error.error_type.value
            by_type[error_type] = by_type.get(error_type, 0) + 1
            
            # By severity
            severity = error.severity.value
            by_severity[severity] = by_severity.get(severity, 0) + 1
            
            # By component
            component = error.component
            by_component[component] = by_component.get(component, 0) + 1
        
        return {
            "total_errors": total_errors,
            "recent_errors_24h": len(recent_errors),
            "by_type": by_type,
            "by_severity": by_severity,
            "by_component": by_component,
            "error_rate": len(recent_errors) / 24 if recent_errors else 0  # errors per hour
        }

class RetryHandler:
    """Advanced retry mechanism with exponential backoff"""
    
    def __init__(self, error_handler: ErrorHandler):
        self.error_handler = error_handler
    
    async def retry_with_backoff(
        self,
        func: Callable,
        config: RetryConfig,
        context: Dict[str, Any],
        *args,
        **kwargs
    ) -> Any:
        """Retry function with exponential backoff"""
        
        last_error = None
        
        for attempt in range(config.max_attempts):
            try:
                # Add attempt info to context
                attempt_context = {**context, "attempt": attempt + 1}
                
                # Execute function
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
                    
            except Exception as error:
                last_error = error
                
                # Handle error
                error_context = await self.error_handler.handle_error(error, attempt_context)
                
                # Check if error is retryable
                if error_context.error_type not in config.retryable_errors:
                    raise error
                
                # Check if this was the last attempt
                if attempt == config.max_attempts - 1:
                    raise error
                
                # Calculate delay
                delay = self._calculate_delay(attempt, config)
                
                self.error_handler.logger.info(
                    f"Retrying in {delay:.2f}s (attempt {attempt + 1}/{config.max_attempts}): {error}"
                )
                
                await asyncio.sleep(delay)
        
        # Should not reach here, but just in case
        if last_error:
            raise last_error
    
    def _calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        """Calculate retry delay with exponential backoff and jitter"""
        
        # Exponential backoff
        delay = config.base_delay * (config.exponential_base ** attempt)
        
        # Apply max delay
        delay = min(delay, config.max_delay)
        
        # Add jitter to avoid thundering herd
        if config.jitter:
            jitter_range = delay * 0.1  # 10% jitter
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0, delay)

class CircuitBreaker:
    """Circuit breaker pattern for preventing cascade failures"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        reset_timeout: float = 60.0,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    async def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            self._on_success()
            return result
            
        except self.expected_exception as error:
            self._on_failure()
            raise error
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset"""
        if self.last_failure_time is None:
            return True
        
        return time.time() - self.last_failure_time >= self.reset_timeout
    
    def _on_success(self):
        """Handle successful execution"""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def _on_failure(self):
        """Handle failed execution"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"

# Global instances
error_handler = ErrorHandler()
retry_handler = RetryHandler(error_handler)

# Decorator for automatic error handling
def handle_errors(component: str, retryable: bool = True):
    """Decorator for automatic error handling"""
    
    def decorator(func):
        async def wrapper(*args, **kwargs):
            context = {
                "component": component,
                "function": func.__name__,
                "timestamp": datetime.now().isoformat()
            }
            
            try:
                if retryable:
                    config = RetryConfig(max_attempts=3)
                    return await retry_handler.retry_with_backoff(
                        func, config, context, *args, **kwargs
                    )
                else:
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)
                        
            except Exception as error:
                await error_handler.handle_error(error, context)
                raise
        
        return wrapper
    return decorator

# Utility functions for integration
async def safe_ai_call(
    ai_function: Callable,
    fallback_function: Optional[Callable] = None,
    context: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Any:
    """Safely call AI function with fallback"""
    
    try:
        config = RetryConfig(
            max_attempts=3,
            retryable_errors=[
                ErrorType.AI_PROVIDER_ERROR,
                ErrorType.NETWORK_ERROR,
                ErrorType.TIMEOUT_ERROR,
                ErrorType.RATE_LIMIT_ERROR
            ]
        )
        
        return await retry_handler.retry_with_backoff(
            ai_function,
            config,
            context or {"component": "ai_provider"},
            **kwargs
        )
        
    except Exception as error:
        if fallback_function:
            try:
                return await fallback_function(**kwargs)
            except Exception as fallback_error:
                await error_handler.handle_error(
                    fallback_error, 
                    {**(context or {}), "fallback_failed": True}
                )
        
        raise error

async def safe_websocket_send(ws, message: str, context: Optional[Dict[str, Any]] = None):
    """Safely send WebSocket message with error handling"""
    
    try:
        await ws.send(message)
        
    except Exception as error:
        await error_handler.handle_error(
            error,
            {
                "component": "websocket",
                "action": "send_message",
                **(context or {})
            }
        )
        raise error

# Error monitoring endpoints
def get_error_dashboard_data() -> Dict[str, Any]:
    """Get error data for dashboard"""
    
    stats = error_handler.get_error_stats()
    recent_errors = [
        {
            "timestamp": error.timestamp.isoformat(),
            "type": error.error_type.value,
            "severity": error.severity.value,
            "component": error.component,
            "message": error.message
        }
        for error in error_handler.error_history[-10:]  # Last 10 errors
    ]
    
    return {
        "stats": stats,
        "recent_errors": recent_errors,
        "system_health": {
            "status": "healthy" if stats.get("recent_errors_24h", 0) < 10 else "degraded",
            "error_rate": stats.get("error_rate", 0)
        }
    }

# Setup error callbacks for real-time notifications
async def websocket_error_notification(error_context: ErrorContext):
    """Send error notification via WebSocket"""
    
    if error_context.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
        # This would integrate with your WebSocket manager
        notification = {
            "type": "error_alert",
            "severity": error_context.severity.value,
            "message": error_context.message,
            "component": error_context.component,
            "timestamp": error_context.timestamp.isoformat()
        }
        
        # Send to all connected admin clients
        # await websocket_manager.broadcast_to_admins(json.dumps(notification))

# Register the callback
error_handler.register_callback(ErrorType.AI_PROVIDER_ERROR, websocket_error_notification)
error_handler.register_callback(ErrorType.SYSTEM_ERROR, websocket_error_notification)
