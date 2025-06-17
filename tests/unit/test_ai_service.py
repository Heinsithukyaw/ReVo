#!/usr/bin/env python3
"""
Unit tests for AI Service
Tests the ProductionAIService with cost optimization and performance tracking
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from apps.backend.services.ai_service import ProductionAIService, GenerationRequest


class TestProductionAIService:
    """Test suite for ProductionAIService"""
    
    @pytest.fixture
    async def ai_service(self):
        """Create AI service instance for testing"""
        service = ProductionAIService()
        await service.initialize()
        return service
    
    @pytest.mark.unit
    def test_ai_service_initialization(self):
        """Test AI service initializes with all required components"""
        service = ProductionAIService()
        
        # Check core components exist
        assert service.enhanced_manager is not None
        assert service.cost_tracker is not None
        assert service.performance_metrics is not None
        assert service.local_preference == 0.7  # 70% local preference
        
        # Check initial metrics
        assert service.performance_metrics["total_requests"] == 0
        assert service.performance_metrics["local_requests"] == 0
        assert service.performance_metrics["cloud_requests"] == 0
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_cost_optimization_local_preference(self, ai_service):
        """Test cost optimization prefers local models for simple tasks"""
        # Create simple request that should use local model
        request = GenerationRequest(
            prompt="Write a simple hello world function",
            complexity="low",
            force_local=True
        )
        
        # Mock the enhanced manager to return local response
        with patch.object(ai_service.enhanced_manager, 'generate_response', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = {
                "content": "def hello_world():\n    print('Hello, World!')",
                "model": "deepseek_r1",
                "cost": 0.0,
                "success": True
            }
            
            response = await ai_service.generate_with_cost_optimization(request)
            
            # Verify local model was used
            assert response["cost"] == 0.0
            assert response["model"] == "deepseek_r1"
            assert response["success"] is True
            
            # Verify metrics updated
            assert ai_service.performance_metrics["local_requests"] == 1
            assert ai_service.performance_metrics["total_requests"] == 1
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_cloud_fallback_mechanism(self, ai_service):
        """Test cloud fallback when local models fail"""
        request = GenerationRequest(
            prompt="Complex analysis task",
            complexity="high"
        )
        
        # Mock local failure and cloud success
        with patch.object(ai_service.enhanced_manager, 'generate_response', new_callable=AsyncMock) as mock_generate:
            # First call (local) fails, second call (cloud) succeeds
            mock_generate.side_effect = [
                Exception("Local model unavailable"),
                {
                    "content": "Detailed analysis result",
                    "model": "claude-3-sonnet",
                    "cost": 0.05,
                    "success": True
                }
            ]
            
            response = await ai_service.generate_with_cost_optimization(request)
            
            # Verify cloud fallback worked
            assert response["cost"] > 0.0
            assert response["model"] == "claude-3-sonnet"
            assert response["success"] is True
            
            # Verify both attempts were made
            assert mock_generate.call_count == 2
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_performance_metrics_tracking(self, ai_service):
        """Test performance metrics are properly tracked"""
        # Make multiple requests
        requests = [
            GenerationRequest(prompt=f"Task {i}", complexity="low")
            for i in range(5)
        ]
        
        with patch.object(ai_service.enhanced_manager, 'generate_response', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = {
                "content": "Generated content",
                "model": "deepseek_r1",
                "cost": 0.0,
                "success": True
            }
            
            # Process all requests
            for request in requests:
                await ai_service.generate_with_cost_optimization(request)
            
            # Verify metrics
            metrics = ai_service.get_performance_summary()
            assert metrics["total_requests"] == 5
            assert metrics["local_usage_percentage"] == 100.0  # All local
            assert metrics["total_cost"] == 0.0
            assert metrics["average_response_time"] >= 0.0
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_cost_tracking_accuracy(self, ai_service):
        """Test cost tracking is accurate across different models"""
        # Mix of local and cloud requests
        local_request = GenerationRequest(prompt="Simple task", force_local=True)
        cloud_request = GenerationRequest(prompt="Complex task", force_cloud=True)
        
        with patch.object(ai_service.enhanced_manager, 'generate_response', new_callable=AsyncMock) as mock_generate:
            # Configure different responses for local vs cloud
            def side_effect(*args, **kwargs):
                if kwargs.get('model_preference') == 'local':
                    return {
                        "content": "Local response",
                        "model": "deepseek_r1",
                        "cost": 0.0,
                        "success": True
                    }
                else:
                    return {
                        "content": "Cloud response",
                        "model": "claude-3-sonnet",
                        "cost": 0.03,
                        "success": True
                    }
            
            mock_generate.side_effect = side_effect
            
            # Make requests
            local_response = await ai_service.generate_with_cost_optimization(local_request)
            cloud_response = await ai_service.generate_with_cost_optimization(cloud_request)
            
            # Verify cost tracking
            assert local_response["cost"] == 0.0
            assert cloud_response["cost"] == 0.03
            
            summary = ai_service.get_performance_summary()
            assert summary["total_cost"] == 0.03
            assert summary["local_usage_percentage"] == 50.0  # 1 out of 2 requests
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, ai_service):
        """Test error handling and recovery mechanisms"""
        request = GenerationRequest(prompt="Test prompt")
        
        with patch.object(ai_service.enhanced_manager, 'generate_response', new_callable=AsyncMock) as mock_generate:
            # Simulate complete failure
            mock_generate.side_effect = Exception("All models unavailable")
            
            response = await ai_service.generate_with_cost_optimization(request)
            
            # Verify graceful failure handling
            assert response["success"] is False
            assert "error" in response
            assert response["cost"] == 0.0  # No cost for failed requests
    
    @pytest.mark.unit
    def test_cost_optimization_thresholds(self, ai_service):
        """Test cost optimization threshold logic"""
        # Test different complexity levels
        simple_request = GenerationRequest(prompt="Simple", complexity="low")
        complex_request = GenerationRequest(prompt="Complex", complexity="high")
        
        # Simple requests should prefer local
        assert ai_service._should_use_local_model(simple_request) is True
        
        # Complex requests might use cloud
        # This depends on the specific implementation logic
        result = ai_service._should_use_local_model(complex_request)
        assert isinstance(result, bool)  # Should return a boolean decision
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_concurrent_request_handling(self, ai_service):
        """Test handling of concurrent requests"""
        # Create multiple concurrent requests
        requests = [
            GenerationRequest(prompt=f"Concurrent task {i}")
            for i in range(10)
        ]
        
        with patch.object(ai_service.enhanced_manager, 'generate_response', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = {
                "content": "Generated content",
                "model": "deepseek_r1",
                "cost": 0.0,
                "success": True
            }
            
            # Process requests concurrently
            tasks = [
                ai_service.generate_with_cost_optimization(request)
                for request in requests
            ]
            responses = await asyncio.gather(*tasks)
            
            # Verify all requests completed successfully
            assert len(responses) == 10
            assert all(response["success"] for response in responses)
            
            # Verify metrics are consistent
            summary = ai_service.get_performance_summary()
            assert summary["total_requests"] == 10
    
    @pytest.mark.unit
    def test_performance_summary_format(self, ai_service):
        """Test performance summary returns correct format"""
        summary = ai_service.get_performance_summary()
        
        # Check required fields
        required_fields = [
            "total_requests",
            "local_requests", 
            "cloud_requests",
            "local_usage_percentage",
            "total_cost",
            "average_response_time",
            "success_rate"
        ]
        
        for field in required_fields:
            assert field in summary
            assert isinstance(summary[field], (int, float))
        
        # Check percentage calculations
        if summary["total_requests"] > 0:
            calculated_local_percentage = (summary["local_requests"] / summary["total_requests"]) * 100
            assert abs(summary["local_usage_percentage"] - calculated_local_percentage) < 0.01


class TestGenerationRequest:
    """Test suite for GenerationRequest model"""
    
    @pytest.mark.unit
    def test_generation_request_creation(self):
        """Test GenerationRequest can be created with required fields"""
        request = GenerationRequest(
            prompt="Test prompt",
            complexity="medium",
            max_tokens=1000
        )
        
        assert request.prompt == "Test prompt"
        assert request.complexity == "medium"
        assert request.max_tokens == 1000
    
    @pytest.mark.unit
    def test_generation_request_defaults(self):
        """Test GenerationRequest has sensible defaults"""
        request = GenerationRequest(prompt="Test prompt")
        
        # Check defaults are set
        assert request.complexity == "medium"
        assert request.max_tokens == 1000
        assert request.temperature == 0.7
        assert request.force_local is False
        assert request.force_cloud is False
    
    @pytest.mark.unit
    def test_generation_request_validation(self):
        """Test GenerationRequest validates input parameters"""
        # Test invalid complexity
        with pytest.raises(ValueError):
            GenerationRequest(prompt="Test", complexity="invalid")
        
        # Test invalid temperature
        with pytest.raises(ValueError):
            GenerationRequest(prompt="Test", temperature=2.0)  # Should be 0-1
        
        # Test conflicting force flags
        with pytest.raises(ValueError):
            GenerationRequest(prompt="Test", force_local=True, force_cloud=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])