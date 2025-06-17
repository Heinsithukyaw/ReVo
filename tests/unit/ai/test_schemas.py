"""
Unit tests for AI schemas and validation.
"""

import pytest
from pydantic import ValidationError
from datetime import datetime

from packages.ai.schemas import (
    GenerationRequest, GenerationResponse, CodeGenerationRequest,
    SecurityValidationRequest, SecurityValidationResponse,
    ModelLoadRequest, ModelUnloadRequest, ModelSwitchRequest,
    ModelType, AIServiceConfig
)


class TestGenerationRequest:
    """Test cases for GenerationRequest validation."""
    
    def test_valid_request(self):
        """Test valid generation request."""
        request = GenerationRequest(
            prompt="Test prompt",
            max_tokens=100,
            temperature=0.7,
            task_type="general"
        )
        
        assert request.prompt == "Test prompt"
        assert request.max_tokens == 100
        assert request.temperature == 0.7
        assert request.task_type == "general"
        assert request.language == "python"  # default
        assert request.framework == "fastapi"  # default
    
    def test_prompt_validation_empty(self):
        """Test prompt validation with empty string."""
        with pytest.raises(ValidationError) as exc_info:
            GenerationRequest(prompt="")
        
        # Check for either the custom validator message or Pydantic's built-in message
        error_str = str(exc_info.value)
        assert ("Prompt cannot be empty" in error_str or 
                "String should have at least 1 character" in error_str)
    
    def test_prompt_validation_whitespace(self):
        """Test prompt validation with whitespace only."""
        with pytest.raises(ValidationError) as exc_info:
            GenerationRequest(prompt="   ")
        
        assert "Prompt cannot be empty" in str(exc_info.value)
    
    def test_prompt_too_long(self):
        """Test prompt validation with too long string."""
        long_prompt = "x" * 10001  # Exceeds max_length=10000
        
        with pytest.raises(ValidationError) as exc_info:
            GenerationRequest(prompt=long_prompt)
        
        # Check for either old or new Pydantic error message format
        error_str = str(exc_info.value)
        assert ("ensure this value has at most 10000 characters" in error_str or 
                "String should have at most 10000 characters" in error_str)
    
    def test_max_tokens_validation(self):
        """Test max_tokens validation."""
        # Too low
        with pytest.raises(ValidationError):
            GenerationRequest(prompt="test", max_tokens=0)
        
        # Too high
        with pytest.raises(ValidationError):
            GenerationRequest(prompt="test", max_tokens=10000)
        
        # Valid range
        request = GenerationRequest(prompt="test", max_tokens=2048)
        assert request.max_tokens == 2048
    
    def test_temperature_validation(self):
        """Test temperature validation."""
        # Too low
        with pytest.raises(ValidationError):
            GenerationRequest(prompt="test", temperature=-0.1)
        
        # Too high
        with pytest.raises(ValidationError):
            GenerationRequest(prompt="test", temperature=2.1)
        
        # Valid range
        request = GenerationRequest(prompt="test", temperature=1.5)
        assert request.temperature == 1.5
    
    def test_top_p_validation(self):
        """Test top_p validation."""
        # Too low
        with pytest.raises(ValidationError):
            GenerationRequest(prompt="test", top_p=-0.1)
        
        # Too high
        with pytest.raises(ValidationError):
            GenerationRequest(prompt="test", top_p=1.1)
        
        # Valid range
        request = GenerationRequest(prompt="test", top_p=0.95)
        assert request.top_p == 0.95
    
    def test_task_type_validation(self):
        """Test task_type validation."""
        # Invalid task type
        with pytest.raises(ValidationError) as exc_info:
            GenerationRequest(prompt="test", task_type="invalid_type")
        
        assert "Task type must be one of" in str(exc_info.value)
        
        # Valid task types
        valid_types = ["general", "code_generation", "debugging", "analysis", "documentation"]
        for task_type in valid_types:
            request = GenerationRequest(prompt="test", task_type=task_type)
            assert request.task_type == task_type
    
    def test_language_validation(self):
        """Test language validation."""
        # Invalid language
        with pytest.raises(ValidationError) as exc_info:
            GenerationRequest(prompt="test", language="invalid_lang")
        
        assert "Language must be one of" in str(exc_info.value)
        
        # Valid languages
        valid_languages = ["python", "javascript", "java", "go", "rust"]
        for language in valid_languages:
            request = GenerationRequest(prompt="test", language=language)
            assert request.language == language
    
    def test_language_case_insensitive(self):
        """Test language validation is case insensitive."""
        request = GenerationRequest(prompt="test", language="PYTHON")
        assert request.language == "python"
    
    def test_prompt_whitespace_trimming(self):
        """Test prompt whitespace trimming."""
        request = GenerationRequest(prompt="  test prompt  ")
        assert request.prompt == "test prompt"


class TestGenerationResponse:
    """Test cases for GenerationResponse validation."""
    
    def test_valid_response(self):
        """Test valid generation response."""
        response = GenerationResponse(
            content="Generated content",
            model_used="test-model",
            status="completed",
            response_time=1.5,
            tokens_used=100,
            timestamp="2024-01-01T12:00:00Z"
        )
        
        assert response.content == "Generated content"
        assert response.model_used == "test-model"
        assert response.status == "completed"
        assert response.response_time == 1.5
        assert response.tokens_used == 100
        assert response.fallback_used is False  # default
    
    def test_negative_response_time(self):
        """Test validation of negative response time."""
        with pytest.raises(ValidationError):
            GenerationResponse(
                content="test",
                model_used="test-model",
                status="completed",
                response_time=-1.0
            )
    
    def test_negative_tokens_used(self):
        """Test validation of negative tokens used."""
        with pytest.raises(ValidationError):
            GenerationResponse(
                content="test",
                model_used="test-model",
                status="completed",
                response_time=1.0,
                tokens_used=-10
            )
    
    def test_optional_fields(self):
        """Test optional fields in response."""
        response = GenerationResponse(
            content="test",
            model_used="test-model",
            status="completed",
            response_time=1.0
        )
        
        assert response.tokens_used is None
        assert response.timestamp is None
        assert response.error is None
        assert response.metadata is None


class TestCodeGenerationRequest:
    """Test cases for CodeGenerationRequest validation."""
    
    def test_valid_code_request(self):
        """Test valid code generation request."""
        request = CodeGenerationRequest(
            prompt="Create a function",
            language="python",
            max_tokens=500
        )
        
        assert request.task_type == "code_generation"
        assert request.language == "python"
        assert request.testing_framework == "pytest"  # default
        assert request.documentation_style == "google"  # default
    
    def test_language_required(self):
        """Test that language is required for code generation."""
        with pytest.raises(ValidationError):
            CodeGenerationRequest(prompt="Create a function")
    
    def test_task_type_immutable(self):
        """Test that task_type is fixed for code generation."""
        request = CodeGenerationRequest(
            prompt="Create a function",
            language="python"
        )
        
        assert request.task_type == "code_generation"
        
        # Should not be able to change it
        with pytest.raises(ValidationError):
            CodeGenerationRequest(
                prompt="Create a function",
                language="python",
                task_type="general"
            )


class TestSecurityValidationRequest:
    """Test cases for SecurityValidationRequest validation."""
    
    def test_valid_security_request(self):
        """Test valid security validation request."""
        request = SecurityValidationRequest(
            content="SELECT * FROM users",
            validation_type="sql"
        )
        
        assert request.content == "SELECT * FROM users"
        assert request.validation_type == "sql"
        assert request.strict_mode is True  # default
    
    def test_content_too_long(self):
        """Test content length validation."""
        long_content = "x" * 50001  # Exceeds max_length=50000
        
        with pytest.raises(ValidationError):
            SecurityValidationRequest(
                content=long_content,
                validation_type="input"
            )
    
    def test_invalid_validation_type(self):
        """Test invalid validation type."""
        with pytest.raises(ValidationError) as exc_info:
            SecurityValidationRequest(
                content="test",
                validation_type="invalid"
            )
        
        assert "Validation type must be one of" in str(exc_info.value)
    
    def test_valid_validation_types(self):
        """Test all valid validation types."""
        valid_types = ["input", "output", "code", "sql", "script"]
        
        for validation_type in valid_types:
            request = SecurityValidationRequest(
                content="test content",
                validation_type=validation_type
            )
            assert request.validation_type == validation_type


class TestModelLoadRequest:
    """Test cases for ModelLoadRequest validation."""
    
    def test_valid_load_request(self):
        """Test valid model load request."""
        request = ModelLoadRequest(
            model_id="test-model-123",
            model_path="/path/to/model",
            model_type=ModelType.DEEPSEEK_R1
        )
        
        assert request.model_id == "test-model-123"
        assert request.model_path == "/path/to/model"
        assert request.model_type == ModelType.DEEPSEEK_R1
        assert request.config is None  # default
    
    def test_model_id_validation(self):
        """Test model ID validation."""
        # Valid IDs
        valid_ids = ["model-1", "model_2", "model.3", "model123"]
        for model_id in valid_ids:
            request = ModelLoadRequest(
                model_id=model_id,
                model_path="/path",
                model_type=ModelType.LLAMA
            )
            assert request.model_id == model_id
        
        # Invalid IDs
        invalid_ids = ["model@1", "model#2", "model 3", "model/4"]
        for model_id in invalid_ids:
            with pytest.raises(ValidationError) as exc_info:
                ModelLoadRequest(
                    model_id=model_id,
                    model_path="/path",
                    model_type=ModelType.LLAMA
                )
            assert "must contain only alphanumeric characters" in str(exc_info.value)
    
    def test_empty_model_id(self):
        """Test empty model ID validation."""
        with pytest.raises(ValidationError):
            ModelLoadRequest(
                model_id="",
                model_path="/path",
                model_type=ModelType.LLAMA
            )
    
    def test_empty_model_path(self):
        """Test empty model path validation."""
        with pytest.raises(ValidationError):
            ModelLoadRequest(
                model_id="test-model",
                model_path="",
                model_type=ModelType.LLAMA
            )


class TestModelUnloadRequest:
    """Test cases for ModelUnloadRequest validation."""
    
    def test_valid_unload_request(self):
        """Test valid model unload request."""
        request = ModelUnloadRequest(
            model_id="test-model",
            force=True
        )
        
        assert request.model_id == "test-model"
        assert request.force is True
    
    def test_default_force_false(self):
        """Test default force value."""
        request = ModelUnloadRequest(model_id="test-model")
        assert request.force is False


class TestModelSwitchRequest:
    """Test cases for ModelSwitchRequest validation."""
    
    def test_valid_switch_request(self):
        """Test valid model switch request."""
        request = ModelSwitchRequest(
            model_id="new-model",
            load_if_needed=False
        )
        
        assert request.model_id == "new-model"
        assert request.load_if_needed is False
    
    def test_default_load_if_needed_true(self):
        """Test default load_if_needed value."""
        request = ModelSwitchRequest(model_id="new-model")
        assert request.load_if_needed is True


class TestAIServiceConfig:
    """Test cases for AIServiceConfig validation."""
    
    def test_valid_config(self):
        """Test valid AI service configuration."""
        config = AIServiceConfig(
            default_model="gpt-4",
            max_concurrent_requests=20,
            request_timeout_seconds=60,
            max_memory_percent=80.0
        )
        
        assert config.default_model == "gpt-4"
        assert config.max_concurrent_requests == 20
        assert config.request_timeout_seconds == 60
        assert config.max_memory_percent == 80.0
        assert config.enable_caching is True  # default
    
    def test_concurrent_requests_validation(self):
        """Test concurrent requests validation."""
        # Too low
        with pytest.raises(ValidationError):
            AIServiceConfig(
                default_model="test",
                max_concurrent_requests=0
            )
        
        # Too high
        with pytest.raises(ValidationError):
            AIServiceConfig(
                default_model="test",
                max_concurrent_requests=101
            )
    
    def test_timeout_validation(self):
        """Test timeout validation."""
        # Too low
        with pytest.raises(ValidationError):
            AIServiceConfig(
                default_model="test",
                request_timeout_seconds=4
            )
        
        # Too high
        with pytest.raises(ValidationError):
            AIServiceConfig(
                default_model="test",
                request_timeout_seconds=301
            )
    
    def test_memory_percent_validation(self):
        """Test memory percent validation."""
        # Too low
        with pytest.raises(ValidationError):
            AIServiceConfig(
                default_model="test",
                max_memory_percent=49.0
            )
        
        # Too high
        with pytest.raises(ValidationError):
            AIServiceConfig(
                default_model="test",
                max_memory_percent=96.0
            )
    
    def test_cache_ttl_validation(self):
        """Test cache TTL validation."""
        with pytest.raises(ValidationError):
            AIServiceConfig(
                default_model="test",
                cache_ttl_seconds=59  # Below minimum of 60
            )
    
    def test_prompt_length_validation(self):
        """Test max prompt length validation."""
        # Too low
        with pytest.raises(ValidationError):
            AIServiceConfig(
                default_model="test",
                max_prompt_length=99
            )
        
        # Too high
        with pytest.raises(ValidationError):
            AIServiceConfig(
                default_model="test",
                max_prompt_length=50001
            )