"""
Structured Logging Configuration

Provides structured logging with proper formatting, security filtering, and performance tracking.
"""

import logging
import logging.config
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional
import structlog
from pathlib import Path


class SecurityFilter(logging.Filter):
    """Filter to remove sensitive information from logs."""
    
    SENSITIVE_PATTERNS = [
        'password', 'token', 'key', 'secret', 'auth', 'credential',
        'api_key', 'access_token', 'refresh_token', 'bearer',
        'authorization', 'x-api-key'
    ]
    
    def filter(self, record):
        """Filter sensitive information from log records."""
        if hasattr(record, 'msg'):
            msg = str(record.msg)
            for pattern in self.SENSITIVE_PATTERNS:
                if pattern.lower() in msg.lower():
                    # Replace sensitive values with [REDACTED]
                    record.msg = self._redact_sensitive_data(msg)
        
        # Filter sensitive data from args
        if hasattr(record, 'args') and record.args:
            record.args = tuple(
                self._redact_sensitive_data(str(arg)) if isinstance(arg, str) else arg
                for arg in record.args
            )
        
        return True
    
    def _redact_sensitive_data(self, text: str) -> str:
        """Redact sensitive data from text."""
        import re
        
        # Pattern to match key=value or "key": "value" patterns
        patterns = [
            r'(\w*(?:' + '|'.join(self.SENSITIVE_PATTERNS) + r')\w*["\']?\s*[:=]\s*["\']?)([^"\s,}]+)',
            r'(Bearer\s+)([A-Za-z0-9\-._~+/]+=*)',
            r'(token["\']?\s*[:=]\s*["\']?)([^"\s,}]+)'
        ]
        
        result = text
        for pattern in patterns:
            result = re.sub(pattern, r'\1[REDACTED]', result, flags=re.IGNORECASE)
        
        return result


class PerformanceFilter(logging.Filter):
    """Filter to add performance metrics to log records."""
    
    def filter(self, record):
        """Add performance context to log records."""
        import psutil
        import time
        
        # Add timestamp
        record.timestamp = datetime.utcnow().isoformat()
        
        # Add performance metrics for WARNING and ERROR levels
        if record.levelno >= logging.WARNING:
            try:
                record.cpu_percent = psutil.cpu_percent()
                record.memory_percent = psutil.virtual_memory().percent
                record.process_memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
            except Exception:
                # Don't fail logging if performance metrics can't be gathered
                pass
        
        return True


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record):
        """Format log record as JSON."""
        log_entry = {
            'timestamp': getattr(record, 'timestamp', datetime.utcnow().isoformat()),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'thread': record.thread,
            'thread_name': record.threadName,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add performance metrics if present
        if hasattr(record, 'cpu_percent'):
            log_entry['performance'] = {
                'cpu_percent': record.cpu_percent,
                'memory_percent': record.memory_percent,
                'process_memory_mb': record.process_memory_mb
            }
        
        # Add custom fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'exc_info', 'exc_text', 'stack_info',
                          'timestamp', 'cpu_percent', 'memory_percent', 'process_memory_mb']:
                log_entry[key] = value
        
        return json.dumps(log_entry, default=str)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output."""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record):
        """Format log record with colors."""
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # Format the message
        formatted = f"{color}[{timestamp}] {record.levelname:8} {record.name:20} {record.getMessage()}{reset}"
        
        # Add exception info if present
        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"
        
        return formatted


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    enable_json: bool = True,
    enable_console: bool = True,
    enable_security_filter: bool = True,
    enable_performance_filter: bool = True,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> None:
    """
    Setup structured logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        enable_json: Enable JSON formatting for file logs
        enable_console: Enable console logging
        enable_security_filter: Enable security filtering
        enable_performance_filter: Enable performance metrics
        max_file_size: Maximum log file size in bytes
        backup_count: Number of backup files to keep
    """
    
    # Create logs directory if it doesn't exist
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if enable_json else structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Build logging configuration
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'json': {
                '()': JSONFormatter,
            },
            'colored': {
                '()': ColoredFormatter,
            },
            'standard': {
                'format': '%(asctime)s [%(levelname)8s] %(name)20s: %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            }
        },
        'filters': {},
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': log_level,
                'formatter': 'colored' if enable_console else 'standard',
                'stream': sys.stdout,
                'filters': []
            }
        },
        'loggers': {
            '': {  # Root logger
                'level': log_level,
                'handlers': ['console'] if enable_console else [],
                'propagate': False
            },
            'packages.ai': {
                'level': log_level,
                'handlers': ['console'] if enable_console else [],
                'propagate': False
            },
            'packages.core': {
                'level': log_level,
                'handlers': ['console'] if enable_console else [],
                'propagate': False
            },
            'packages.agents': {
                'level': log_level,
                'handlers': ['console'] if enable_console else [],
                'propagate': False
            }
        }
    }
    
    # Add security filter
    if enable_security_filter:
        config['filters']['security'] = {
            '()': SecurityFilter,
        }
        config['handlers']['console']['filters'].append('security')
    
    # Add performance filter
    if enable_performance_filter:
        config['filters']['performance'] = {
            '()': PerformanceFilter,
        }
        config['handlers']['console']['filters'].append('performance')
    
    # Add file handler if log file specified
    if log_file:
        config['handlers']['file'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': log_level,
            'formatter': 'json' if enable_json else 'standard',
            'filename': log_file,
            'maxBytes': max_file_size,
            'backupCount': backup_count,
            'filters': []
        }
        
        # Add filters to file handler
        if enable_security_filter:
            config['handlers']['file']['filters'].append('security')
        if enable_performance_filter:
            config['handlers']['file']['filters'].append('performance')
        
        # Add file handler to all loggers
        for logger_config in config['loggers'].values():
            if 'file' not in logger_config['handlers']:
                logger_config['handlers'].append('file')
    
    # Apply configuration
    logging.config.dictConfig(config)
    
    # Set up specific logger levels for noisy libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    
    # Log configuration success
    logger = logging.getLogger(__name__)
    logger.info(
        "Logging configured successfully",
        extra={
            'log_level': log_level,
            'log_file': log_file,
            'json_enabled': enable_json,
            'console_enabled': enable_console,
            'security_filter': enable_security_filter,
            'performance_filter': enable_performance_filter
        }
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def log_function_call(func):
    """
    Decorator to log function calls with parameters and execution time.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    import functools
    import time
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()
        
        # Log function entry
        logger.debug(
            f"Entering {func.__name__}",
            extra={
                'function': func.__name__,
                'module': func.__module__,
                'args_count': len(args),
                'kwargs_count': len(kwargs)
            }
        )
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Log successful completion
            logger.debug(
                f"Completed {func.__name__}",
                extra={
                    'function': func.__name__,
                    'module': func.__module__,
                    'execution_time': execution_time,
                    'success': True
                }
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Log error
            logger.error(
                f"Error in {func.__name__}: {str(e)}",
                extra={
                    'function': func.__name__,
                    'module': func.__module__,
                    'execution_time': execution_time,
                    'success': False,
                    'error_type': type(e).__name__
                },
                exc_info=True
            )
            
            raise
    
    return wrapper


def log_async_function_call(func):
    """
    Decorator to log async function calls with parameters and execution time.
    
    Args:
        func: Async function to decorate
        
    Returns:
        Decorated async function
    """
    import functools
    import asyncio
    import time
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()
        
        # Log function entry
        logger.debug(
            f"Entering async {func.__name__}",
            extra={
                'function': func.__name__,
                'module': func.__module__,
                'args_count': len(args),
                'kwargs_count': len(kwargs),
                'async': True
            }
        )
        
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Log successful completion
            logger.debug(
                f"Completed async {func.__name__}",
                extra={
                    'function': func.__name__,
                    'module': func.__module__,
                    'execution_time': execution_time,
                    'success': True,
                    'async': True
                }
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Log error
            logger.error(
                f"Error in async {func.__name__}: {str(e)}",
                extra={
                    'function': func.__name__,
                    'module': func.__module__,
                    'execution_time': execution_time,
                    'success': False,
                    'error_type': type(e).__name__,
                    'async': True
                },
                exc_info=True
            )
            
            raise
    
    return wrapper


# Context manager for request tracking
class RequestContext:
    """Context manager for tracking request-specific logging context."""
    
    def __init__(self, request_id: str, user_id: Optional[str] = None, 
                 operation: Optional[str] = None):
        self.request_id = request_id
        self.user_id = user_id
        self.operation = operation
        self.start_time = time.time()
        self.logger = get_logger(__name__)
    
    def __enter__(self):
        self.logger.info(
            f"Request started: {self.operation or 'unknown'}",
            extra={
                'request_id': self.request_id,
                'user_id': self.user_id,
                'operation': self.operation,
                'request_start': True
            }
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        execution_time = time.time() - self.start_time
        
        if exc_type is None:
            self.logger.info(
                f"Request completed: {self.operation or 'unknown'}",
                extra={
                    'request_id': self.request_id,
                    'user_id': self.user_id,
                    'operation': self.operation,
                    'execution_time': execution_time,
                    'request_end': True,
                    'success': True
                }
            )
        else:
            self.logger.error(
                f"Request failed: {self.operation or 'unknown'} - {str(exc_val)}",
                extra={
                    'request_id': self.request_id,
                    'user_id': self.user_id,
                    'operation': self.operation,
                    'execution_time': execution_time,
                    'request_end': True,
                    'success': False,
                    'error_type': exc_type.__name__ if exc_type else None
                },
                exc_info=True
            )


# Initialize logging with default configuration
def init_default_logging():
    """Initialize logging with default configuration."""
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_file = os.getenv('LOG_FILE', '/workspace/reVoAgent/logs/revoagent.log')
    
    setup_logging(
        log_level=log_level,
        log_file=log_file,
        enable_json=True,
        enable_console=True,
        enable_security_filter=True,
        enable_performance_filter=True
    )