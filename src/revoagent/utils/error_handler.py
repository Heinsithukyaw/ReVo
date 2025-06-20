"""
Enhanced Error Handling Module

Provides standardized error handling for the reVoAgent platform.
Features:
- Structured error responses
- Detailed error logging
- Error categorization
- Client-friendly error messages
"""

import logging
import traceback
import json
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, Union, List

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

# Configure logging
logger = logging.getLogger("revoagent.error_handler")

class ErrorCategory(Enum):
    """Categorization of errors for better client handling"""
    VALIDATION = "validation_error"
    AUTHENTICATION = "authentication_error"
    AUTHORIZATION = "authorization_error"
    RESOURCE = "resource_error"
    LLM = "llm_error"
    SYSTEM = "system_error"
    EXTERNAL = "external_service_error"
    NETWORK = "network_error"
    INPUT = "input_error"
    UNKNOWN = "unknown_error"

class ErrorSeverity(Enum):
    """Severity levels for error tracking"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorDetails:
    """Structured error details for consistent error handling"""
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
        client_message: Optional[str] = None
    ):
        self.message = message
        self.category = category
        self.severity = severity
        self.status_code = status_code
        self.error_code = error_code or f"ERR_{category.value.upper()}"
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()
        self.exception = exception
        self.client_message = client_message or self._get_client_message(message)
        
        # Log the error based on severity
        self._log_error()
    
    def _log_error(self) -> None:
        """Log the error with appropriate level based on severity"""
        log_message = f"{self.error_code}: {self.message}"
        
        # Include exception traceback if available
        if self.exception:
            log_message += f"\nException: {str(self.exception)}"
            if self.severity.value in ["high", "critical"]:
                log_message += f"\nTraceback: {''.join(traceback.format_exception(type(self.exception), self.exception, self.exception.__traceback__))}"
        
        # Log with appropriate level
        if self.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message)
        elif self.severity == ErrorSeverity.HIGH:
            logger.error(log_message)
        elif self.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    def _get_client_message(self, message: str) -> str:
        """Generate a client-friendly message from the internal message"""
        # For security, don't expose internal details in client messages
        if self.category == ErrorCategory.SYSTEM:
            return "An internal system error occurred. Our team has been notified."
        elif self.category == ErrorCategory.EXTERNAL:
            return "We're experiencing issues with an external service. Please try again later."
        elif self.category == ErrorCategory.NETWORK:
            return "Network connectivity issue detected. Please check your connection and try again."
        else:
            return message
    
    def to_dict(self, include_internal: bool = False) -> Dict[str, Any]:
        """Convert to dictionary for response"""
        response = {
            "error": {
                "code": self.error_code,
                "message": self.client_message,
                "category": self.category.value,
                "timestamp": self.timestamp
            }
        }
        
        # Include additional details for debugging if requested
        if include_internal:
            response["error"]["internal_message"] = self.message
            response["error"]["severity"] = self.severity.value
            response["error"]["details"] = self.details
            
            if self.exception:
                response["error"]["exception"] = str(self.exception)
        
        return response
    
    def to_response(self, include_internal: bool = False) -> JSONResponse:
        """Convert to FastAPI JSON response"""
        return JSONResponse(
            status_code=self.status_code,
            content=self.to_dict(include_internal)
        )

# Specific error handlers
def handle_validation_error(
    request: Request,
    exc: Union[RequestValidationError, ValidationError]
) -> JSONResponse:
    """Handle validation errors from request data"""
    errors = []
    
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error.get("loc", []))
        message = error.get("msg", "Validation error")
        error_type = error.get("type", "unknown_error_type")
        
        errors.append({
            "field": field,
            "message": message,
            "type": error_type
        })
    
    error_details = ErrorDetails(
        message=f"Request validation failed with {len(errors)} errors",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.MEDIUM,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details={"validation_errors": errors},
        exception=exc,
        client_message="The request contains invalid data. Please check the error details and try again."
    )
    
    return error_details.to_response(include_internal=True)

def handle_llm_error(
    request: Request,
    error_message: str,
    original_exception: Optional[Exception] = None,
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """Handle errors related to LLM operations"""
    error_details = ErrorDetails(
        message=f"LLM operation failed: {error_message}",
        category=ErrorCategory.LLM,
        severity=ErrorSeverity.HIGH,
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        details=details or {},
        exception=original_exception,
        client_message="The AI model is currently unavailable. Please try again later."
    )
    
    return error_details.to_response()

def handle_auth_error(
    request: Request,
    error_message: str,
    status_code: int = status.HTTP_401_UNAUTHORIZED
) -> JSONResponse:
    """Handle authentication and authorization errors"""
    error_details = ErrorDetails(
        message=error_message,
        category=ErrorCategory.AUTHENTICATION if status_code == 401 else ErrorCategory.AUTHORIZATION,
        severity=ErrorSeverity.MEDIUM,
        status_code=status_code,
        client_message="Authentication failed. Please check your credentials and try again."
    )
    
    return error_details.to_response()

def handle_general_exception(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """Handle general exceptions"""
    # Determine if this is a known type of error
    if "timeout" in str(exc).lower() or "timed out" in str(exc).lower():
        category = ErrorCategory.NETWORK
        status_code = status.HTTP_504_GATEWAY_TIMEOUT
        client_message = "The operation timed out. Please try again later."
    elif "not found" in str(exc).lower():
        category = ErrorCategory.RESOURCE
        status_code = status.HTTP_404_NOT_FOUND
        client_message = "The requested resource was not found."
    else:
        category = ErrorCategory.SYSTEM
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        client_message = "An unexpected error occurred. Our team has been notified."
    
    error_details = ErrorDetails(
        message=f"Unhandled exception: {str(exc)}",
        category=category,
        severity=ErrorSeverity.HIGH,
        status_code=status_code,
        exception=exc,
        client_message=client_message
    )
    
    return error_details.to_response()

# Function to register all error handlers with a FastAPI app
def register_error_handlers(app):
    """Register all error handlers with a FastAPI application"""
    from fastapi import HTTPException
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc):
        return handle_validation_error(request, exc)
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc):
        # For HTTP exceptions, pass through the status code and detail
        error_details = ErrorDetails(
            message=exc.detail,
            category=ErrorCategory.INPUT,  # Default category, could be refined
            severity=ErrorSeverity.MEDIUM,
            status_code=exc.status_code,
            client_message=exc.detail
        )
        return error_details.to_response()
    
    @app.exception_handler(Exception)
    async def exception_handler(request, exc):
        return handle_general_exception(request, exc)
    
    return app