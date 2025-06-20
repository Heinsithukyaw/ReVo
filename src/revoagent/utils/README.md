# Enhanced Error Handling

This module provides a comprehensive error handling system for the reVoAgent platform, ensuring consistent, informative, and user-friendly error responses.

## Features

### 1. Structured Error Responses

All errors follow a consistent structure with:
- Error code
- Client-friendly message
- Error category
- Timestamp
- (Optional) Detailed information for debugging

### 2. Error Categorization

Errors are categorized by type:
- `VALIDATION`: Input validation errors
- `AUTHENTICATION`: Authentication-related errors
- `AUTHORIZATION`: Permission-related errors
- `RESOURCE`: Resource not found or unavailable
- `LLM`: LLM-related errors
- `SYSTEM`: Internal system errors
- `EXTERNAL`: Errors from external services
- `NETWORK`: Network connectivity issues
- `INPUT`: General input errors
- `UNKNOWN`: Uncategorized errors

### 3. Severity Levels

Each error has a severity level that determines logging behavior:
- `LOW`: Informational issues
- `MEDIUM`: Standard errors
- `HIGH`: Significant errors requiring attention
- `CRITICAL`: Critical errors requiring immediate action

### 4. Client-Friendly Messages

The system automatically generates appropriate user-facing messages while logging detailed information for debugging.

## Usage

### FastAPI Integration

```python
from fastapi import FastAPI
from src.revoagent.utils.error_handler import register_error_handlers

app = FastAPI()

# Register all error handlers
register_error_handlers(app)
```

### Custom Error Handling

```python
from src.revoagent.utils.error_handler import ErrorDetails, ErrorCategory, ErrorSeverity

# Create a detailed error response
error_details = ErrorDetails(
    message="Internal error processing the request",
    category=ErrorCategory.SYSTEM,
    severity=ErrorSeverity.HIGH,
    status_code=500,
    error_code="ERR_SYSTEM_001",
    details={"operation": "data_processing", "component": "parser"},
    exception=original_exception,
    client_message="We're experiencing technical difficulties. Please try again later."
)

# Convert to FastAPI response
return error_details.to_response()
```

### Specific Error Handlers

The module provides specific handlers for common error types:

```python
from src.revoagent.utils.error_handler import handle_validation_error, handle_llm_error, handle_auth_error

# Handle validation error
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return handle_validation_error(request, exc)

# Handle LLM error
@app.exception_handler(LLMException)
async def llm_exception_handler(request, exc):
    return handle_llm_error(request, str(exc), original_exception=exc)
```

## Error Logging

Errors are automatically logged based on their severity level:
- `CRITICAL`: Uses `logger.critical()`
- `HIGH`: Uses `logger.error()`
- `MEDIUM`: Uses `logger.warning()`
- `LOW`: Uses `logger.info()`

Higher severity errors include more detailed information, including exception tracebacks.