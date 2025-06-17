"""
Integration test for the refactored AI architecture.

This test demonstrates the new service-oriented architecture with:
- Focused services (ModelLoader, ResponseGenerator, MetricsCollector, etc.)
- Input validation with Pydantic
- Structured logging
- Proper error handling
- Resource management
"""

import pytest
import asyncio
import sys
import os
from unittest.mock import Mock, AsyncMock, patch

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from packages.ai.schemas import (
    GenerationRequest, ModelLoadRequest, ModelType, 
    ModelConfig, ModelInfo, ModelStatus
)
from packages.ai.services import (
    ModelLoader, ResponseGenerator, MetricsCollector,
    FallbackManager, ResourceManager
)
from packages.core.logging_config import setup_logging, get_logger


class TestRefactoredArchitecture:
    """Integration tests for the refactored AI architecture."""
    
    @classmethod
    def setup_class(cls):
        """Setup logging for tests."""
        setup_logging(
            log_level="INFO",
            enable_console=True,
            enable_json=False,
            enable_security_filter=True,
            enable_performance_filter=False
        )
        cls.logger = get_logger(__name__)
        cls.logger.info("Starting refactored architecture integration tests")
    
    @pytest.fixture
    def model_loader(self):
        """Create ModelLoader instance."""
        return ModelLoader()
    
    @pytest.fixture
    def metrics_collector(self):
        """Create MetricsCollector instance."""
        return MetricsCollector()
    
    @pytest.fixture
    def fallback_manager(self):
        """Create FallbackManager instance."""
        return FallbackManager()
    
    @pytest.fixture
    def resource_manager(self):
        """Create ResourceManager instance."""
        return ResourceManager()
    
    @pytest.fixture
    def response_generator(self, model_loader, fallback_manager):
        """Create ResponseGenerator instance."""
        return ResponseGenerator(model_loader, fallback_manager)
    
    def test_input_validation_success(self):
        """Test successful input validation with Pydantic."""
        self.logger.info("Testing input validation - success case")
        
        # Valid request
        request = GenerationRequest(
            prompt="Create a Python function to calculate fibonacci numbers",
            max_tokens=500,
            temperature=0.7,
            task_type="code_generation",
            language="python"
        )
        
        assert request.prompt == "Create a Python function to calculate fibonacci numbers"
        assert request.max_tokens == 500
        assert request.temperature == 0.7
        assert request.task_type == "code_generation"
        assert request.language == "python"
        
        self.logger.info("Input validation successful", extra={
            'prompt_length': len(request.prompt),
            'task_type': request.task_type,
            'language': request.language
        })
    
    def test_input_validation_failure(self):
        """Test input validation failures."""
        self.logger.info("Testing input validation - failure cases")
        
        # Empty prompt
        with pytest.raises(ValueError, match="Prompt cannot be empty"):
            GenerationRequest(prompt="")
        
        # Invalid temperature
        with pytest.raises(ValueError):
            GenerationRequest(prompt="test", temperature=3.0)
        
        # Invalid task type
        with pytest.raises(ValueError, match="Task type must be one of"):
            GenerationRequest(prompt="test", task_type="invalid_type")
        
        # Invalid language
        with pytest.raises(ValueError, match="Language must be one of"):
            GenerationRequest(prompt="test", language="invalid_lang")
        
        self.logger.info("Input validation failures caught correctly")
    
    def test_security_filtering(self):
        """Test security filtering in logging."""
        self.logger.info("Testing security filtering")
        
        # This should be filtered
        self.logger.info("User login with password=secret123 and api_key=sk-1234567890")
        
        # This should also be filtered
        self.logger.warning("Authentication failed", extra={
            'user_token': 'bearer_token_12345',
            'api_key': 'secret_api_key'
        })
        
        self.logger.info("Security filtering test completed")
    
    def test_metrics_collection(self, metrics_collector):
        """Test metrics collection functionality."""
        self.logger.info("Testing metrics collection")
        
        # Record multiple requests
        request_id1 = metrics_collector.record_request_start("model-1")
        metrics_collector.record_request_completion("model-1", 1.5, 100, True)
        
        request_id2 = metrics_collector.record_request_start("model-1")
        metrics_collector.record_request_completion("model-1", 2.0, 150, True)
        
        request_id3 = metrics_collector.record_request_start("model-2")
        metrics_collector.record_request_completion("model-2", 0.8, 50, False, "Test error")
        
        # Get metrics
        model1_metrics = metrics_collector.get_model_metrics("model-1")
        model2_metrics = metrics_collector.get_model_metrics("model-2")
        all_metrics = metrics_collector.get_model_metrics()
        
        # Verify model-1 metrics
        assert model1_metrics["total_requests"] == 2
        assert model1_metrics["successful_requests"] == 2
        assert model1_metrics["failed_requests"] == 0
        assert model1_metrics["error_rate"] == 0.0
        assert model1_metrics["avg_response_time"] == 1.75  # (1.5 + 2.0) / 2
        assert model1_metrics["total_tokens_generated"] == 250
        
        # Verify model-2 metrics
        assert model2_metrics["total_requests"] == 1
        assert model2_metrics["successful_requests"] == 0
        assert model2_metrics["failed_requests"] == 1
        assert model2_metrics["error_rate"] == 100.0
        
        # Verify all metrics
        assert len(all_metrics) == 2
        assert "model-1" in all_metrics
        assert "model-2" in all_metrics
        
        # Get performance summary
        summary = metrics_collector.get_performance_summary()
        assert summary["total_requests"] == 3
        assert summary["successful_requests"] == 2
        assert summary["failed_requests"] == 1
        assert summary["overall_error_rate"] == 33.33333333333333  # 1/3
        
        self.logger.info("Metrics collection test completed", extra={
            'total_requests': summary["total_requests"],
            'error_rate': summary["overall_error_rate"]
        })
    
    def test_resource_management(self, resource_manager):
        """Test resource management functionality."""
        self.logger.info("Testing resource management")
        
        # Get current usage
        usage = resource_manager.get_current_usage()
        assert usage.cpu_percent >= 0
        assert usage.memory_percent >= 0
        assert usage.memory_used_gb >= 0
        assert usage.memory_available_gb >= 0
        
        # Check resource availability
        available, reason = asyncio.run(
            resource_manager.check_resource_availability(
                required_memory_gb=1.0,
                required_gpu_memory_gb=0.0
            )
        )
        
        # Should be available for reasonable requirements
        assert available is True
        assert reason == "Resources available"
        
        # Test with unreasonable requirements
        available, reason = asyncio.run(
            resource_manager.check_resource_availability(
                required_memory_gb=1000.0  # 1TB - unreasonable
            )
        )
        
        assert available is False
        assert "Insufficient memory" in reason
        
        # Test resource optimization
        optimization_result = asyncio.run(resource_manager.optimize_memory_usage())
        assert "before" in optimization_result
        assert "after" in optimization_result
        assert "actions_taken" in optimization_result
        
        self.logger.info("Resource management test completed", extra={
            'memory_percent': usage.memory_percent,
            'cpu_percent': usage.cpu_percent
        })
    
    @pytest.mark.asyncio
    async def test_fallback_manager(self, fallback_manager):
        """Test fallback manager functionality."""
        self.logger.info("Testing fallback manager")
        
        # Test model unavailable fallback
        request = GenerationRequest(prompt="Test prompt")
        
        fallback_response = await fallback_manager.handle_model_unavailable("test-model", request)
        
        # Should return a fallback response
        assert fallback_response is not None
        assert fallback_response.fallback_used is True
        assert fallback_response.status in ["completed", "cached_fallback", "degraded"]
        
        # Test generation error fallback
        error_response = await fallback_manager.handle_generation_error(
            "test-model", request, "Test error"
        )
        
        assert error_response is not None
        assert error_response.fallback_used is True
        
        # Test health status
        health = fallback_manager.get_health_status()
        assert "model_health" in health
        assert "circuit_breakers" in health
        assert "cache_size" in health
        
        self.logger.info("Fallback manager test completed")
    
    def test_model_loader_registration(self, model_loader):
        """Test model loader registration functionality."""
        self.logger.info("Testing model loader registration")
        
        # Register model info
        model_info = ModelInfo(
            id="test-model",
            name="Test Model",
            type=ModelType.DEEPSEEK_R1,
            size="8B",
            status=ModelStatus.UNLOADED
        )
        
        model_loader.register_model_info("test-model", model_info)
        
        # Verify registration
        assert model_loader.is_model_loaded("test-model") is False
        assert model_loader.get_model_status("test-model") == ModelStatus.UNLOADED
        
        # Test loaded models
        loaded_models = model_loader.get_loaded_models()
        assert len(loaded_models) == 0
        
        self.logger.info("Model loader registration test completed")
    
    @pytest.mark.asyncio
    async def test_response_generator_no_model(self, response_generator):
        """Test response generator with no active model."""
        self.logger.info("Testing response generator with no active model")
        
        request = GenerationRequest(prompt="Test prompt")
        
        response = await response_generator.generate_text(request)
        
        assert response.status == "error"
        assert response.error == "No active model available"
        assert response.model_used == "none"
        assert response.content == ""
        
        self.logger.info("Response generator no-model test completed")
    
    @pytest.mark.asyncio
    async def test_response_generator_with_mock_model(self, response_generator, model_loader):
        """Test response generator with mock model."""
        self.logger.info("Testing response generator with mock model")
        
        # Create mock model
        mock_model = AsyncMock()
        mock_model.generate.return_value = "Generated response from mock model"
        
        # Add mock model to loader
        model_loader.models["mock-model"] = mock_model
        
        # Set active model
        response_generator.set_active_model("mock-model")
        
        # Generate response
        request = GenerationRequest(prompt="Test prompt")
        response = await response_generator.generate_text(request)
        
        assert response.status == "completed"
        assert response.content == "Generated response from mock model"
        assert response.model_used == "mock-model"
        assert response.response_time > 0
        
        # Verify mock was called correctly
        mock_model.generate.assert_called_once_with(
            "Test prompt",
            max_tokens=2048,
            temperature=0.7,
            top_p=0.9,
            top_k=50
        )
        
        self.logger.info("Response generator mock model test completed")
    
    @pytest.mark.asyncio
    async def test_code_generation_request(self, response_generator, model_loader):
        """Test code generation with specialized request."""
        self.logger.info("Testing code generation request")
        
        # Create mock model with code generation capability
        mock_model = AsyncMock()
        mock_model.generate_code.return_value = {
            "generated_code": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)"
        }
        
        # Add mock model to loader
        model_loader.models["code-model"] = mock_model
        response_generator.set_active_model("code-model")
        
        # Create code generation request
        request = GenerationRequest(
            prompt="Create a fibonacci function",
            task_type="code_generation",
            language="python",
            max_tokens=500
        )
        
        response = await response_generator.generate_text(request)
        
        assert response.status == "completed"
        assert "def fibonacci" in response.content
        assert response.model_used == "code-model"
        
        # Verify code generation method was called
        mock_model.generate_code.assert_called_once()
        
        self.logger.info("Code generation test completed")
    
    def test_end_to_end_workflow(self, model_loader, metrics_collector, response_generator, fallback_manager):
        """Test complete end-to-end workflow."""
        self.logger.info("Testing end-to-end workflow")
        
        # 1. Register model
        model_info = ModelInfo(
            id="workflow-model",
            name="Workflow Test Model",
            type=ModelType.LLAMA,
            size="8B",
            status=ModelStatus.UNLOADED
        )
        model_loader.register_model_info("workflow-model", model_info)
        
        # 2. Create mock model
        mock_model = AsyncMock()
        mock_model.generate.return_value = "Workflow test response"
        model_loader.models["workflow-model"] = mock_model
        
        # 3. Set active model
        response_generator.set_active_model("workflow-model")
        
        # 4. Create and validate request
        request = GenerationRequest(
            prompt="Generate a test response",
            max_tokens=100,
            temperature=0.5
        )
        
        # 5. Record metrics start
        request_id = metrics_collector.record_request_start("workflow-model")
        
        # 6. Generate response
        response = asyncio.run(response_generator.generate_text(request))
        
        # 7. Record metrics completion
        metrics_collector.record_request_completion(
            "workflow-model", 
            response.response_time, 
            response.tokens_used or 0, 
            response.status == "completed"
        )
        
        # 8. Cache response for fallback
        fallback_manager.cache_response(request, response)
        
        # 9. Verify workflow
        assert response.status == "completed"
        assert response.content == "Workflow test response"
        assert response.model_used == "workflow-model"
        
        # 10. Verify metrics
        metrics = metrics_collector.get_model_metrics("workflow-model")
        assert metrics["total_requests"] == 1
        assert metrics["successful_requests"] == 1
        assert metrics["error_rate"] == 0.0
        
        self.logger.info("End-to-end workflow test completed successfully", extra={
            'request_id': request_id,
            'response_time': response.response_time,
            'model_used': response.model_used
        })
    
    def test_structured_logging_context(self):
        """Test structured logging with context."""
        self.logger.info("Testing structured logging context")
        
        # Log with structured data
        self.logger.info(
            "Processing AI request",
            extra={
                'request_id': 'req_12345',
                'user_id': 'user_67890',
                'model_id': 'test-model',
                'prompt_length': 150,
                'max_tokens': 500,
                'temperature': 0.7
            }
        )
        
        # Log performance metrics
        self.logger.info(
            "Request completed",
            extra={
                'request_id': 'req_12345',
                'response_time': 2.5,
                'tokens_generated': 234,
                'success': True,
                'model_used': 'test-model'
            }
        )
        
        # Log error with context
        self.logger.error(
            "Model loading failed",
            extra={
                'model_id': 'failed-model',
                'error_type': 'ResourceError',
                'memory_required': '8GB',
                'memory_available': '4GB'
            }
        )
        
        self.logger.info("Structured logging context test completed")


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])