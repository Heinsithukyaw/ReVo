"""
AI Schemas

Pydantic models for input validation and data structures.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Dict, List, Optional, Any, Union, Literal
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class ModelType(Enum):
    """Supported model types."""
    DEEPSEEK_R1 = "deepseek-r1"
    LLAMA = "llama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    CUSTOM = "custom"


class ModelStatus(Enum):
    """Model loading status."""
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    ERROR = "error"


class TaskType(Enum):
    """Task types for AI generation."""
    CODE_GENERATION = "code_generation"
    TEXT_GENERATION = "text_generation"
    ANALYSIS = "analysis"
    DEBUGGING = "debugging"
    OPTIMIZATION = "optimization"
    TESTING = "testing"
    DOCUMENTATION = "documentation"


class Language(Enum):
    """Programming languages."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CPP = "cpp"
    CSHARP = "csharp"
    GO = "go"
    RUST = "rust"
    PHP = "php"
    RUBY = "ruby"
    SWIFT = "swift"
    KOTLIN = "kotlin"
    SCALA = "scala"
    HTML = "html"
    CSS = "css"
    SQL = "sql"
    BASH = "bash"
    POWERSHELL = "powershell"
    OTHER = "other"


@dataclass
class ModelInfo:
    """Model information and metadata."""
    id: str
    name: str
    type: ModelType
    size: str
    status: ModelStatus
    memory_usage: float = 0.0
    gpu_memory: float = 0.0
    performance_score: float = 0.0
    last_used: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class ModelConfig:
    """Model configuration settings."""
    model_id: str
    model_path: str
    model_type: ModelType
    device: str = "auto"
    max_length: int = 4096
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 50
    do_sample: bool = True
    quantization: Optional[str] = None
    trust_remote_code: bool = True


class GenerationRequest(BaseModel):
    """Request for AI text/code generation with validation."""
    
    prompt: str = Field(..., min_length=1, max_length=10000, description="Input prompt for generation")
    max_tokens: int = Field(default=2048, ge=1, le=8192, description="Maximum tokens to generate")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    top_p: float = Field(default=0.9, ge=0.0, le=1.0, description="Top-p sampling parameter")
    top_k: int = Field(default=50, ge=1, le=100, description="Top-k sampling parameter")
    task_type: str = Field(default="general", description="Type of task: general, code_generation, debugging")
    
    # Optional code generation specific fields
    language: Optional[str] = Field(default="python", description="Programming language for code generation")
    framework: Optional[str] = Field(default="fastapi", description="Framework to use")
    database: Optional[str] = Field(default="postgresql", description="Database type")
    features: Optional[List[str]] = Field(default=["auth", "tests"], description="Features to include")
    
    @field_validator('prompt')
    @classmethod
    def validate_prompt(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Prompt cannot be empty')
        return v.strip()
    
    @field_validator('task_type')
    @classmethod
    def validate_task_type(cls, v):
        allowed_types = ["general", "code_generation", "debugging", "analysis", "documentation"]
        if v not in allowed_types:
            raise ValueError(f'Task type must be one of: {allowed_types}')
        return v
    
    @field_validator('language')
    @classmethod
    def validate_language(cls, v):
        if v:
            allowed_languages = ["python", "javascript", "typescript", "java", "go", "rust", "cpp", "c", "sql"]
            if v.lower() not in allowed_languages:
                raise ValueError(f'Language must be one of: {allowed_languages}')
            return v.lower()
        return v


class GenerationResponse(BaseModel):
    """Response from AI generation with metadata."""
    
    content: str = Field(..., description="Generated content")
    model_used: str = Field(..., description="Model that generated the response")
    status: str = Field(..., description="Generation status: completed, error, cached, degraded")
    response_time: float = Field(..., ge=0.0, description="Response time in seconds")
    tokens_used: Optional[int] = Field(default=None, ge=0, description="Number of tokens used")
    timestamp: Optional[str] = Field(default=None, description="ISO timestamp of generation")
    error: Optional[str] = Field(default=None, description="Error message if generation failed")
    fallback_used: bool = Field(default=False, description="Whether fallback strategy was used")
    
    # Metadata
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class CodeGenerationRequest(GenerationRequest):
    """Specialized request for code generation."""
    
    task_type: Literal["code_generation"] = Field(default="code_generation", description="Task type (fixed for code generation)")
    language: str = Field(..., description="Programming language (required for code generation)")
    
    # Code-specific fields
    project_structure: Optional[Dict[str, Any]] = Field(default=None, description="Project structure requirements")
    dependencies: Optional[List[str]] = Field(default=None, description="Required dependencies")
    testing_framework: Optional[str] = Field(default="pytest", description="Testing framework to use")
    documentation_style: Optional[str] = Field(default="google", description="Documentation style")


class ModelHealthCheck(BaseModel):
    """Model health check response."""
    
    model_id: str
    status: str  # healthy, unhealthy, unknown
    last_check: datetime
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    memory_usage_gb: Optional[float] = None
    gpu_memory_gb: Optional[float] = None


class SystemStatus(BaseModel):
    """System status response."""
    
    status: str  # healthy, degraded, critical
    timestamp: datetime
    active_models: int
    total_requests: int
    error_rate: float
    avg_response_time: float
    
    # Resource usage
    cpu_percent: float
    memory_percent: float
    gpu_utilization: Optional[float] = None
    
    # Health checks
    model_health: List[ModelHealthCheck]
    alerts: List[Dict[str, Any]] = []


class SecurityValidationRequest(BaseModel):
    """Request for security validation."""
    
    content: str = Field(..., max_length=50000, description="Content to validate")
    validation_type: str = Field(..., description="Type of validation: input, output, code")
    strict_mode: bool = Field(default=True, description="Whether to use strict validation")
    
    @field_validator('validation_type')
    @classmethod
    def validate_type(cls, v):
        allowed_types = ["input", "output", "code", "sql", "script"]
        if v not in allowed_types:
            raise ValueError(f'Validation type must be one of: {allowed_types}')
        return v


class SecurityValidationResponse(BaseModel):
    """Response from security validation."""
    
    is_safe: bool = Field(..., description="Whether content is considered safe")
    risk_level: str = Field(..., description="Risk level: low, medium, high, critical")
    issues_found: List[Dict[str, str]] = Field(default=[], description="Security issues found")
    sanitized_content: Optional[str] = Field(default=None, description="Sanitized version if applicable")
    recommendations: List[str] = Field(default=[], description="Security recommendations")


class RateLimitInfo(BaseModel):
    """Rate limiting information."""
    
    requests_remaining: int = Field(..., ge=0, description="Requests remaining in current window")
    reset_time: datetime = Field(..., description="When the rate limit resets")
    limit_per_window: int = Field(..., ge=1, description="Total requests allowed per window")
    window_size_seconds: int = Field(..., ge=1, description="Size of rate limit window in seconds")


class APIKeyInfo(BaseModel):
    """API key information and limits."""
    
    key_id: str = Field(..., description="API key identifier")
    tier: str = Field(..., description="API tier: free, pro, enterprise")
    requests_per_minute: int = Field(..., ge=1, description="Requests per minute limit")
    requests_per_day: int = Field(..., ge=1, description="Requests per day limit")
    features_enabled: List[str] = Field(default=[], description="Enabled features")
    expires_at: Optional[datetime] = Field(default=None, description="Key expiration date")


# Error response models
class ErrorResponse(BaseModel):
    """Standard error response."""
    
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    request_id: Optional[str] = Field(default=None, description="Request ID for tracking")


class ValidationError(BaseModel):
    """Validation error details."""
    
    field: str = Field(..., description="Field that failed validation")
    message: str = Field(..., description="Validation error message")
    invalid_value: Any = Field(..., description="The invalid value")
    allowed_values: Optional[List[Any]] = Field(default=None, description="Allowed values if applicable")


# Configuration models
class AIServiceConfig(BaseModel):
    """Configuration for AI services."""
    
    default_model: str = Field(..., description="Default model to use")
    max_concurrent_requests: int = Field(default=10, ge=1, le=100, description="Max concurrent requests")
    request_timeout_seconds: int = Field(default=30, ge=5, le=300, description="Request timeout")
    enable_caching: bool = Field(default=True, description="Enable response caching")
    cache_ttl_seconds: int = Field(default=3600, ge=60, description="Cache TTL in seconds")
    
    # Resource limits
    max_memory_percent: float = Field(default=85.0, ge=50.0, le=95.0, description="Max memory usage percent")
    max_gpu_memory_percent: float = Field(default=90.0, ge=50.0, le=95.0, description="Max GPU memory percent")
    
    # Security settings
    enable_input_validation: bool = Field(default=True, description="Enable input validation")
    enable_output_filtering: bool = Field(default=True, description="Enable output filtering")
    max_prompt_length: int = Field(default=10000, ge=100, le=50000, description="Max prompt length")


class ModelLoadRequest(BaseModel):
    """Request to load a model."""
    
    model_id: str = Field(..., min_length=1, description="Model identifier")
    model_path: str = Field(..., min_length=1, description="Path to model")
    model_type: ModelType = Field(..., description="Type of model")
    config: Optional[Dict[str, Any]] = Field(default=None, description="Additional model configuration")
    
    @field_validator('model_id')
    @classmethod
    def validate_model_id(cls, v):
        # Ensure model ID is safe for use as identifier
        if not v.replace('-', '').replace('_', '').replace('.', '').isalnum():
            raise ValueError('Model ID must contain only alphanumeric characters, hyphens, underscores, and dots')
        return v


class ModelUnloadRequest(BaseModel):
    """Request to unload a model."""
    
    model_id: str = Field(..., min_length=1, description="Model identifier to unload")
    force: bool = Field(default=False, description="Force unload even if model is busy")


class ModelSwitchRequest(BaseModel):
    """Request to switch active model."""
    
    model_id: str = Field(..., min_length=1, description="Model identifier to switch to")
    load_if_needed: bool = Field(default=True, description="Load model if not already loaded")