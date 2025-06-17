"""
Unit tests for ResponseGenerator service.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from packages.ai.services.response_generator import ResponseGenerator
from packages.ai.services.fallback_manager import FallbackManager
from packages.ai.schemas import GenerationRequest, GenerationResponse


class TestResponseGenerator:
    """Test cases for ResponseGenerator service."""
    
    @pytest.fixture
    def mock_model_loader(self):
        """Mock ModelLoader for testing."""
        loader = Mock()
        loader.is_model_loaded.return_value = True
        loader.get_loaded_models.return_value = {"test-model": Mock()}
        return loader
    
    @pytest.fixture
    def mock_fallback_manager(self):
        """Mock FallbackManager for testing."""
        return Mock(spec=FallbackManager)
    
    @pytest.fixture
    def response_generator(self, mock_model_loader, mock_fallback_manager):
        """Create ResponseGenerator instance for testing."""
        return ResponseGenerator(mock_model_loader, mock_fallback_manager)
    
    @pytest.fixture
    def sample_request(self):
        """Sample generation request."""
        return GenerationRequest(
            prompt="Test prompt",
            max_tokens=100,
            temperature=0.7,
            task_type="general"
        )
    
    @pytest.fixture
    def code_request(self):
        """Sample code generation request."""
        return GenerationRequest(
            prompt="Create a function to calculate fibonacci",
            max_tokens=200,
            temperature=0.1,
            task_type="code_generation",
            language="python"
        )
    
    def test_initialization(self, mock_model_loader, mock_fallback_manager):
        """Test ResponseGenerator initialization."""
        generator = ResponseGenerator(mock_model_loader, mock_fallback_manager)
        
        assert generator.model_loader == mock_model_loader
        assert generator.fallback_manager == mock_fallback_manager
        assert generator.active_model is None
    
    def test_set_active_model_success(self, response_generator, mock_model_loader):
        """Test setting active model successfully."""
        mock_model_loader.is_model_loaded.return_value = True
        
        response_generator.set_active_model("test-model")
        
        assert response_generator.active_model == "test-model"
        mock_model_loader.is_model_loaded.assert_called_with("test-model")
    
    def test_set_active_model_not_loaded(self, response_generator, mock_model_loader):
        """Test setting active model when model not loaded."""
        mock_model_loader.is_model_loaded.return_value = False
        
        response_generator.set_active_model("test-model")
        
        # Should not set active model if not loaded
        assert response_generator.active_model is None
    
    def test_get_active_model(self, response_generator):
        """Test getting active model."""
        assert response_generator.get_active_model() is None
        
        response_generator.active_model = "test-model"
        assert response_generator.get_active_model() == "test-model"
    
    @pytest.mark.asyncio
    async def test_generate_text_no_active_model(self, response_generator, sample_request):
        """Test text generation with no active model."""
        response_generator.active_model = None
        
        response = await response_generator.generate_text(sample_request)
        
        assert isinstance(response, GenerationResponse)
        assert response.status == "error"
        assert response.error == "No active model available"
        assert response.model_used == "none"
    
    @pytest.mark.asyncio
    async def test_generate_text_model_not_loaded(self, response_generator, sample_request, mock_model_loader, mock_fallback_manager):
        """Test text generation when model not loaded."""
        response_generator.active_model = "test-model"
        mock_model_loader.is_model_loaded.return_value = False
        
        # Mock fallback response
        fallback_response = GenerationResponse(
            content="Fallback response",
            model_used="fallback",
            status="completed",
            response_time=1.0,
            fallback_used=True
        )
        mock_fallback_manager.handle_model_unavailable.return_value = fallback_response
        
        response = await response_generator.generate_text(sample_request)
        
        assert response == fallback_response
        mock_fallback_manager.handle_model_unavailable.assert_called_once_with("test-model", sample_request)
    
    @pytest.mark.asyncio
    async def test_generate_text_success(self, response_generator, sample_request, mock_model_loader):
        """Test successful text generation."""
        response_generator.active_model = "test-model"
        
        # Mock model with generate method
        mock_model = AsyncMock()
        mock_model.generate.return_value = "Generated text response"
        mock_model_loader.get_loaded_models.return_value = {"test-model": mock_model}
        
        response = await response_generator.generate_text(sample_request)
        
        assert isinstance(response, GenerationResponse)
        assert response.status == "completed"
        assert response.content == "Generated text response"
        assert response.model_used == "test-model"
        assert response.response_time > 0
        assert response.tokens_used > 0
        
        mock_model.generate.assert_called_once_with(
            sample_request.prompt,
            max_tokens=sample_request.max_tokens,
            temperature=sample_request.temperature,
            top_p=sample_request.top_p,
            top_k=sample_request.top_k
        )
    
    @pytest.mark.asyncio
    async def test_generate_code_success(self, response_generator, code_request, mock_model_loader):
        """Test successful code generation."""
        response_generator.active_model = "test-model"
        
        # Mock model with generate_code method
        mock_model = AsyncMock()
        mock_model.generate_code.return_value = {"generated_code": "def fibonacci(n): return n"}
        mock_model_loader.get_loaded_models.return_value = {"test-model": mock_model}
        
        response = await response_generator.generate_text(code_request)
        
        assert isinstance(response, GenerationResponse)
        assert response.status == "completed"
        assert "def fibonacci" in response.content
        assert response.model_used == "test-model"
        
        # Verify generate_code was called with proper format
        mock_model.generate_code.assert_called_once()
        call_args = mock_model.generate_code.call_args[0][0]
        assert call_args["task_description"] == code_request.prompt
        assert call_args["language"] == "python"
    
    @pytest.mark.asyncio
    async def test_generate_code_fallback_to_text(self, response_generator, code_request, mock_model_loader):
        """Test code generation fallback to text generation."""
        response_generator.active_model = "test-model"
        
        # Mock model without generate_code method
        mock_model = AsyncMock()
        mock_model.generate.return_value = "# Generated code via text generation"
        # Remove generate_code method
        del mock_model.generate_code
        
        mock_model_loader.get_loaded_models.return_value = {"test-model": mock_model}
        
        response = await response_generator.generate_text(code_request)
        
        assert isinstance(response, GenerationResponse)
        assert response.status == "completed"
        assert "Generated code via text generation" in response.content
        
        # Should have called generate with modified prompt
        mock_model.generate.assert_called_once()
        call_args = mock_model.generate.call_args[0][0]
        assert "Generate python code for:" in call_args
    
    @pytest.mark.asyncio
    async def test_generate_text_with_exception(self, response_generator, sample_request, mock_model_loader, mock_fallback_manager):
        """Test text generation with exception."""
        response_generator.active_model = "test-model"
        
        # Mock model that raises exception
        mock_model = AsyncMock()
        mock_model.generate.side_effect = Exception("Model error")
        mock_model_loader.get_loaded_models.return_value = {"test-model": mock_model}
        
        # Mock fallback response
        fallback_response = GenerationResponse(
            content="Error fallback response",
            model_used="fallback",
            status="completed",
            response_time=1.0,
            fallback_used=True
        )
        mock_fallback_manager.handle_generation_error.return_value = fallback_response
        
        response = await response_generator.generate_text(sample_request)
        
        assert response == fallback_response
        mock_fallback_manager.handle_generation_error.assert_called_once_with(
            "test-model", sample_request, "Model error"
        )
    
    @pytest.mark.asyncio
    async def test_generate_text_exception_no_fallback(self, response_generator, sample_request, mock_model_loader, mock_fallback_manager):
        """Test text generation with exception and no fallback."""
        response_generator.active_model = "test-model"
        
        # Mock model that raises exception
        mock_model = AsyncMock()
        mock_model.generate.side_effect = Exception("Model error")
        mock_model_loader.get_loaded_models.return_value = {"test-model": mock_model}
        
        # Mock fallback that returns None
        mock_fallback_manager.handle_generation_error.return_value = None
        
        response = await response_generator.generate_text(sample_request)
        
        assert isinstance(response, GenerationResponse)
        assert response.status == "error"
        assert response.error == "Model error"
        assert response.model_used == "test-model"
    
    @pytest.mark.asyncio
    async def test_generate_code_method(self, response_generator, sample_request):
        """Test generate_code method sets correct task type."""
        response_generator.active_model = "test-model"
        
        # Mock the generate_text method
        expected_response = GenerationResponse(
            content="Generated code",
            model_used="test-model",
            status="completed",
            response_time=1.0
        )
        
        with patch.object(response_generator, 'generate_text', return_value=expected_response) as mock_generate:
            response = await response_generator.generate_code(sample_request)
        
        assert response == expected_response
        
        # Verify generate_text was called with modified request
        mock_generate.assert_called_once()
        call_args = mock_generate.call_args[0][0]
        assert call_args.task_type == "code_generation"
    
    def test_estimate_tokens(self, response_generator):
        """Test token estimation."""
        text = "This is a test with ten words total here"
        tokens = response_generator._estimate_tokens(text)
        
        # Should be approximately 1.3 * word count
        expected = int(len(text.split()) * 1.3)
        assert tokens == expected
    
    @pytest.mark.asyncio
    async def test_health_check(self, response_generator, mock_model_loader):
        """Test health check."""
        response_generator.active_model = "test-model"
        mock_model_loader.get_loaded_models.return_value = {"test-model": Mock(), "model2": Mock()}
        
        health = await response_generator.health_check()
        
        assert isinstance(health, dict)
        assert health["active_model"] == "test-model"
        assert health["loaded_models"] == ["test-model", "model2"]
        assert health["fallback_available"] is True
        assert health["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_health_check_no_active_model(self, response_generator, mock_model_loader):
        """Test health check with no active model."""
        response_generator.active_model = None
        mock_model_loader.get_loaded_models.return_value = {}
        
        health = await response_generator.health_check()
        
        assert health["active_model"] is None
        assert health["loaded_models"] == []
        assert health["status"] == "no_active_model"
    
    @pytest.mark.asyncio
    async def test_generate_text_specific_model(self, response_generator, sample_request, mock_model_loader):
        """Test text generation with specific model ID."""
        # Mock model
        mock_model = AsyncMock()
        mock_model.generate.return_value = "Specific model response"
        mock_model_loader.get_loaded_models.return_value = {"specific-model": mock_model}
        mock_model_loader.is_model_loaded.return_value = True
        
        response = await response_generator.generate_text(sample_request, model_id="specific-model")
        
        assert response.content == "Specific model response"
        assert response.model_used == "specific-model"
        mock_model_loader.is_model_loaded.assert_called_with("specific-model")