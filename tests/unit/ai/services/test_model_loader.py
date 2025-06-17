"""
Unit tests for ModelLoader service.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import torch

from packages.ai.services.model_loader import ModelLoader
from packages.ai.schemas import ModelConfig, ModelInfo, ModelType, ModelStatus


class TestModelLoader:
    """Test cases for ModelLoader service."""
    
    @pytest.fixture
    def model_loader(self):
        """Create a ModelLoader instance for testing."""
        return ModelLoader()
    
    @pytest.fixture
    def sample_config(self):
        """Sample model configuration."""
        return ModelConfig(
            model_id="test-model",
            model_path="test/path",
            model_type=ModelType.DEEPSEEK_R1,
            max_length=2048,
            temperature=0.7
        )
    
    @pytest.fixture
    def sample_model_info(self):
        """Sample model information."""
        return ModelInfo(
            id="test-model",
            name="Test Model",
            type=ModelType.DEEPSEEK_R1,
            size="8B",
            status=ModelStatus.UNLOADED
        )
    
    def test_initialization(self, model_loader):
        """Test ModelLoader initialization."""
        assert isinstance(model_loader.models, dict)
        assert isinstance(model_loader.model_info, dict)
        assert len(model_loader.models) == 0
        assert len(model_loader.model_info) == 0
    
    def test_register_model_info(self, model_loader, sample_model_info):
        """Test registering model information."""
        model_loader.register_model_info("test-model", sample_model_info)
        
        assert "test-model" in model_loader.model_info
        assert model_loader.model_info["test-model"] == sample_model_info
    
    def test_is_model_loaded(self, model_loader):
        """Test checking if model is loaded."""
        # Model not loaded
        assert not model_loader.is_model_loaded("test-model")
        
        # Add mock model
        model_loader.models["test-model"] = Mock()
        assert model_loader.is_model_loaded("test-model")
    
    def test_get_model_status(self, model_loader, sample_model_info):
        """Test getting model status."""
        # No model info
        assert model_loader.get_model_status("test-model") is None
        
        # With model info
        model_loader.register_model_info("test-model", sample_model_info)
        assert model_loader.get_model_status("test-model") == ModelStatus.UNLOADED
    
    @pytest.mark.asyncio
    async def test_load_model_already_loaded(self, model_loader, sample_config):
        """Test loading a model that's already loaded."""
        # Mock already loaded model
        model_loader.models["test-model"] = Mock()
        
        result = await model_loader.load_model("test-model", sample_config)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_load_model_deepseek_success(self, model_loader, sample_config, sample_model_info):
        """Test successful DeepSeek model loading."""
        model_loader.register_model_info("test-model", sample_model_info)
        
        # Mock the DeepSeek model
        mock_model = AsyncMock()
        mock_model.load.return_value = True
        
        with patch('packages.ai.services.model_loader.CPUOptimizedDeepSeek', return_value=mock_model):
            result = await model_loader.load_model("test-model", sample_config)
        
        assert result is True
        assert "test-model" in model_loader.models
        assert model_loader.model_info["test-model"].status == ModelStatus.LOADED
        mock_model.load.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_load_model_deepseek_failure(self, model_loader, sample_config, sample_model_info):
        """Test failed DeepSeek model loading."""
        model_loader.register_model_info("test-model", sample_model_info)
        
        # Mock the DeepSeek model that fails to load
        mock_model = AsyncMock()
        mock_model.load.return_value = False
        
        with patch('packages.ai.services.model_loader.CPUOptimizedDeepSeek', return_value=mock_model):
            result = await model_loader.load_model("test-model", sample_config)
        
        assert result is False
        assert "test-model" not in model_loader.models
        assert model_loader.model_info["test-model"].status == ModelStatus.ERROR
    
    @pytest.mark.asyncio
    async def test_load_model_llama_success(self, model_loader, sample_model_info):
        """Test successful Llama model loading."""
        config = ModelConfig(
            model_id="test-llama",
            model_path="test/llama/path",
            model_type=ModelType.LLAMA
        )
        
        llama_info = ModelInfo(
            id="test-llama",
            name="Test Llama",
            type=ModelType.LLAMA,
            size="8B",
            status=ModelStatus.UNLOADED
        )
        
        model_loader.register_model_info("test-llama", llama_info)
        
        # Mock the Llama model
        mock_model = AsyncMock()
        mock_model.load.return_value = True
        
        with patch('packages.ai.services.model_loader.LlamaModel', return_value=mock_model):
            result = await model_loader.load_model("test-llama", config)
        
        assert result is True
        assert "test-llama" in model_loader.models
        assert model_loader.model_info["test-llama"].status == ModelStatus.LOADED
    
    @pytest.mark.asyncio
    async def test_load_model_unsupported_type(self, model_loader, sample_model_info):
        """Test loading unsupported model type."""
        config = ModelConfig(
            model_id="test-model",
            model_path="test/path",
            model_type=ModelType.CUSTOM  # Unsupported in current implementation
        )
        
        model_loader.register_model_info("test-model", sample_model_info)
        
        result = await model_loader.load_model("test-model", config)
        
        assert result is False
        assert model_loader.model_info["test-model"].status == ModelStatus.ERROR
        assert "Unsupported model type" in model_loader.model_info["test-model"].error_message
    
    @pytest.mark.asyncio
    async def test_load_model_exception(self, model_loader, sample_config, sample_model_info):
        """Test model loading with exception."""
        model_loader.register_model_info("test-model", sample_model_info)
        
        # Mock that raises exception
        with patch('packages.ai.services.model_loader.CPUOptimizedDeepSeek', side_effect=Exception("Test error")):
            result = await model_loader.load_model("test-model", sample_config)
        
        assert result is False
        assert model_loader.model_info["test-model"].status == ModelStatus.ERROR
        assert "Test error" in model_loader.model_info["test-model"].error_message
    
    @pytest.mark.asyncio
    async def test_unload_model_not_loaded(self, model_loader):
        """Test unloading a model that's not loaded."""
        result = await model_loader.unload_model("test-model")
        assert result is True  # Should succeed even if not loaded
    
    @pytest.mark.asyncio
    async def test_unload_model_success(self, model_loader, sample_model_info):
        """Test successful model unloading."""
        # Setup loaded model
        mock_model = AsyncMock()
        model_loader.models["test-model"] = mock_model
        model_loader.register_model_info("test-model", sample_model_info)
        model_loader.model_info["test-model"].status = ModelStatus.LOADED
        
        with patch('torch.cuda.is_available', return_value=True), \
             patch('torch.cuda.empty_cache') as mock_empty_cache, \
             patch('gc.collect') as mock_gc:
            
            result = await model_loader.unload_model("test-model")
        
        assert result is True
        assert "test-model" not in model_loader.models
        assert model_loader.model_info["test-model"].status == ModelStatus.UNLOADED
        assert model_loader.model_info["test-model"].memory_usage == 0.0
        assert model_loader.model_info["test-model"].gpu_memory == 0.0
        
        mock_model.unload.assert_called_once()
        mock_empty_cache.assert_called_once()
        mock_gc.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_unload_model_exception(self, model_loader):
        """Test model unloading with exception."""
        # Setup model that raises exception on unload
        mock_model = AsyncMock()
        mock_model.unload.side_effect = Exception("Unload error")
        model_loader.models["test-model"] = mock_model
        
        result = await model_loader.unload_model("test-model")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_cleanup_gpu_memory(self, model_loader):
        """Test GPU memory cleanup."""
        with patch('torch.cuda.is_available', return_value=True), \
             patch('torch.cuda.empty_cache') as mock_empty_cache, \
             patch('torch.cuda.synchronize') as mock_sync:
            
            await model_loader._cleanup_gpu_memory()
            
            mock_empty_cache.assert_called_once()
            mock_sync.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_gpu_memory_no_cuda(self, model_loader):
        """Test GPU memory cleanup when CUDA not available."""
        with patch('torch.cuda.is_available', return_value=False):
            # Should not raise exception
            await model_loader._cleanup_gpu_memory()
    
    def test_get_model_memory_usage(self, model_loader):
        """Test getting model memory usage."""
        # Model with get_memory_usage method
        mock_model = Mock()
        mock_model.get_memory_usage.return_value = 4.5
        
        usage = model_loader._get_model_memory_usage(mock_model)
        assert usage == 4.5
        
        # Model without get_memory_usage method
        mock_model_no_method = Mock(spec=[])
        usage = model_loader._get_model_memory_usage(mock_model_no_method)
        assert usage == 0.0
        
        # Model that raises exception
        mock_model_error = Mock()
        mock_model_error.get_memory_usage.side_effect = Exception("Error")
        usage = model_loader._get_model_memory_usage(mock_model_error)
        assert usage == 0.0
    
    def test_get_model_gpu_memory(self, model_loader):
        """Test getting model GPU memory usage."""
        mock_model = Mock()
        mock_model.model = Mock()  # Has model attribute
        
        with patch('torch.cuda.is_available', return_value=True), \
             patch('torch.cuda.memory_allocated', return_value=4 * 1024**3):  # 4GB
            
            usage = model_loader._get_model_gpu_memory(mock_model)
            assert usage == 4.0
        
        # No CUDA available
        with patch('torch.cuda.is_available', return_value=False):
            usage = model_loader._get_model_gpu_memory(mock_model)
            assert usage == 0.0
        
        # Model without model attribute
        mock_model_no_attr = Mock(spec=[])
        usage = model_loader._get_model_gpu_memory(mock_model_no_attr)
        assert usage == 0.0
    
    def test_get_loaded_models(self, model_loader):
        """Test getting loaded models."""
        # Empty initially
        models = model_loader.get_loaded_models()
        assert models == {}
        
        # Add some models
        model_loader.models["model1"] = Mock()
        model_loader.models["model2"] = Mock()
        
        models = model_loader.get_loaded_models()
        assert len(models) == 2
        assert "model1" in models
        assert "model2" in models
        
        # Should be a copy, not the original dict
        assert models is not model_loader.models