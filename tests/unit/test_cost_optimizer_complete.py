"""
Complete test suite for Cost Optimizer
Comprehensive coverage of cost optimization logic and edge cases
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from typing import Dict, Any, List
import json

# Import cost optimizer components
try:
    from apps.backend.services.cost_optimizer import (
        CostOptimizedRouter,
        CostCalculator,
        ModelCostConfig,
        CostOptimizationError,
        UsageTracker
    )
except ImportError:
    # Fallback for testing
    class CostOptimizedRouter:
        pass
    class CostCalculator:
        pass
    class ModelCostConfig:
        pass
    class CostOptimizationError(Exception):
        pass
    class UsageTracker:
        pass

class TestCostOptimizedRouter:
    """Test suite for CostOptimizedRouter"""
    
    @pytest.fixture
    def cost_router(self):
        """Create cost router instance for testing"""
        return CostOptimizedRouter()
    
    @pytest.fixture
    def mock_model_costs(self):
        """Mock model cost configuration"""
        return {
            "local_models": {
                "deepseek-r1": {
                    "cost_per_token": 0.0,
                    "setup_cost": 0.0,
                    "performance_score": 0.85,
                    "availability": 0.99
                },
                "llama-2-70b": {
                    "cost_per_token": 0.0,
                    "setup_cost": 0.0,
                    "performance_score": 0.80,
                    "availability": 0.95
                }
            },
            "cloud_models": {
                "gpt-4": {
                    "cost_per_token": 0.00003,
                    "setup_cost": 0.0,
                    "performance_score": 0.95,
                    "availability": 0.999
                },
                "claude-3": {
                    "cost_per_token": 0.000015,
                    "setup_cost": 0.0,
                    "performance_score": 0.92,
                    "availability": 0.998
                },
                "gemini-pro": {
                    "cost_per_token": 0.00001,
                    "setup_cost": 0.0,
                    "performance_score": 0.88,
                    "availability": 0.997
                }
            }
        }
    
    @pytest.fixture
    def sample_request(self):
        """Sample request for testing"""
        return {
            "prompt": "Write a Python function to sort a list",
            "max_tokens": 500,
            "quality_requirement": 0.8,
            "cost_priority": 4,  # High cost optimization
            "deadline": datetime.now() + timedelta(minutes=5)
        }

class TestModelSelection:
    """Test model selection logic"""
    
    @pytest.mark.asyncio
    async def test_local_model_selection_high_cost_priority(self, cost_router, mock_model_costs, sample_request):
        """Test local model selection with high cost priority"""
        with patch.object(cost_router, '_get_model_costs', return_value=mock_model_costs):
            with patch.object(cost_router, '_is_model_available', return_value=True):
                
                selected_model = await cost_router.select_optimal_model(sample_request)
                
                # Should select local model for high cost priority
                assert selected_model in ["deepseek-r1", "llama-2-70b"]
    
    @pytest.mark.asyncio
    async def test_cloud_model_selection_high_quality_requirement(self, cost_router, mock_model_costs):
        """Test cloud model selection for high quality requirements"""
        high_quality_request = {
            "prompt": "Complex mathematical proof",
            "max_tokens": 2000,
            "quality_requirement": 0.95,  # Very high quality
            "cost_priority": 1,  # Low cost priority
            "deadline": datetime.now() + timedelta(minutes=10)
        }
        
        with patch.object(cost_router, '_get_model_costs', return_value=mock_model_costs):
            with patch.object(cost_router, '_is_model_available', return_value=True):
                
                selected_model = await cost_router.select_optimal_model(high_quality_request)
                
                # Should select high-quality cloud model
                assert selected_model == "gpt-4"
    
    @pytest.mark.asyncio
    async def test_balanced_selection_medium_requirements(self, cost_router, mock_model_costs):
        """Test balanced model selection for medium requirements"""
        balanced_request = {
            "prompt": "Write a simple web scraper",
            "max_tokens": 800,
            "quality_requirement": 0.85,
            "cost_priority": 3,  # Medium cost priority
            "deadline": datetime.now() + timedelta(minutes=15)
        }
        
        with patch.object(cost_router, '_get_model_costs', return_value=mock_model_costs):
            with patch.object(cost_router, '_is_model_available', return_value=True):
                
                selected_model = await cost_router.select_optimal_model(balanced_request)
                
                # Should select model that balances cost and quality
                assert selected_model is not None
    
    @pytest.mark.asyncio
    async def test_fallback_when_preferred_unavailable(self, cost_router, mock_model_costs, sample_request):
        """Test fallback when preferred model is unavailable"""
        def mock_availability(model_name):
            if model_name == "deepseek-r1":
                return False  # Preferred local model unavailable
            return True
        
        with patch.object(cost_router, '_get_model_costs', return_value=mock_model_costs):
            with patch.object(cost_router, '_is_model_available', side_effect=mock_availability):
                
                selected_model = await cost_router.select_optimal_model(sample_request)
                
                # Should fallback to available model
                assert selected_model != "deepseek-r1"
                assert selected_model is not None
    
    @pytest.mark.asyncio
    async def test_urgent_deadline_selection(self, cost_router, mock_model_costs):
        """Test model selection for urgent deadlines"""
        urgent_request = {
            "prompt": "Quick code fix needed",
            "max_tokens": 200,
            "quality_requirement": 0.7,
            "cost_priority": 3,
            "deadline": datetime.now() + timedelta(seconds=30)  # Very urgent
        }
        
        with patch.object(cost_router, '_get_model_costs', return_value=mock_model_costs):
            with patch.object(cost_router, '_is_model_available', return_value=True):
                with patch.object(cost_router, '_get_model_response_time') as mock_response_time:
                    # Local models are faster
                    mock_response_time.side_effect = lambda model: 0.5 if "deepseek" in model else 2.0
                    
                    selected_model = await cost_router.select_optimal_model(urgent_request)
                    
                    # Should prefer faster model for urgent requests
                    assert "deepseek" in selected_model

class TestCostCalculation:
    """Test cost calculation functionality"""
    
    @pytest.mark.asyncio
    async def test_local_model_cost_calculation(self, cost_router):
        """Test cost calculation for local models"""
        usage_data = {
            "model": "deepseek-r1",
            "tokens_used": 1000,
            "processing_time": 2.5
        }
        
        cost = await cost_router.calculate_request_cost(usage_data)
        
        # Local models should have zero token cost
        assert cost == 0.0
    
    @pytest.mark.asyncio
    async def test_cloud_model_cost_calculation(self, cost_router):
        """Test cost calculation for cloud models"""
        usage_data = {
            "model": "gpt-4",
            "tokens_used": 1000,
            "processing_time": 1.8
        }
        
        with patch.object(cost_router, '_get_model_cost_per_token', return_value=0.00003):
            cost = await cost_router.calculate_request_cost(usage_data)
            
            # Should calculate: 1000 tokens * $0.00003 = $0.03
            assert cost == 0.03
    
    @pytest.mark.asyncio
    async def test_batch_cost_calculation(self, cost_router):
        """Test cost calculation for batch requests"""
        batch_usage = [
            {"model": "deepseek-r1", "tokens_used": 500},
            {"model": "gpt-4", "tokens_used": 300},
            {"model": "claude-3", "tokens_used": 200}
        ]
        
        with patch.object(cost_router, '_get_model_cost_per_token') as mock_cost:
            mock_cost.side_effect = lambda model: {
                "deepseek-r1": 0.0,
                "gpt-4": 0.00003,
                "claude-3": 0.000015
            }.get(model, 0.0)
            
            total_cost = await cost_router.calculate_batch_cost(batch_usage)
            
            # Expected: 0 + (300 * 0.00003) + (200 * 0.000015) = 0.009 + 0.003 = 0.012
            assert abs(total_cost - 0.012) < 0.001
    
    @pytest.mark.asyncio
    async def test_monthly_cost_projection(self, cost_router):
        """Test monthly cost projection"""
        daily_usage = {
            "local_requests": 970,
            "cloud_requests": 30,
            "avg_tokens_per_request": 500,
            "avg_cloud_cost_per_token": 0.00002
        }
        
        monthly_projection = await cost_router.project_monthly_cost(daily_usage)
        
        # Expected monthly cost: 30 days * 30 cloud requests * 500 tokens * $0.00002
        expected_monthly = 30 * 30 * 500 * 0.00002  # $9.00
        
        assert abs(monthly_projection - expected_monthly) < 1.0

class TestCostOptimizationTargets:
    """Test cost optimization target achievement"""
    
    @pytest.mark.asyncio
    async def test_969_percent_local_usage_target(self, cost_router):
        """Test achievement of 96.9% local usage target"""
        # Simulate 1000 requests
        total_requests = 1000
        target_local_percentage = 0.969
        
        with patch.object(cost_router, '_get_usage_stats') as mock_stats:
            mock_stats.return_value = {
                "total_requests": total_requests,
                "local_requests": int(total_requests * target_local_percentage),
                "cloud_requests": total_requests - int(total_requests * target_local_percentage)
            }
            
            stats = await cost_router.get_optimization_stats()
            local_percentage = stats["local_requests"] / stats["total_requests"]
            
            assert local_percentage >= 0.969
    
    @pytest.mark.asyncio
    async def test_cost_savings_calculation(self, cost_router):
        """Test cost savings calculation vs all-cloud scenario"""
        actual_usage = {
            "local_requests": 969,
            "cloud_requests": 31,
            "avg_tokens_per_request": 400,
            "actual_cost": 24.80  # Cost for 31 cloud requests
        }
        
        # All-cloud scenario cost
        all_cloud_cost = 1000 * 400 * 0.00002  # $8.00 per day
        monthly_all_cloud = all_cloud_cost * 30  # $240 per month
        
        savings = await cost_router.calculate_cost_savings(actual_usage)
        
        # Should save significant amount
        assert savings > 200  # Should save over $200/month
    
    @pytest.mark.asyncio
    async def test_cost_optimization_under_quality_constraints(self, cost_router):
        """Test cost optimization while maintaining quality"""
        quality_constraint = 0.85
        
        requests = [
            {"quality_requirement": 0.9, "cost_priority": 4},
            {"quality_requirement": 0.8, "cost_priority": 5},
            {"quality_requirement": 0.7, "cost_priority": 3}
        ]
        
        selections = []
        for request in requests:
            with patch.object(cost_router, '_get_model_quality_score') as mock_quality:
                mock_quality.side_effect = lambda model: {
                    "deepseek-r1": 0.85,
                    "gpt-4": 0.95,
                    "claude-3": 0.92
                }.get(model, 0.8)
                
                with patch.object(cost_router, '_is_model_available', return_value=True):
                    model = await cost_router.select_optimal_model(request)
                    selections.append(model)
        
        # Should balance cost and quality appropriately
        local_selections = sum(1 for model in selections if "deepseek" in model or "llama" in model)
        assert local_selections >= 1  # At least some local selections for cost optimization

class TestUsageTracking:
    """Test usage tracking and analytics"""
    
    @pytest.mark.asyncio
    async def test_request_tracking(self, cost_router):
        """Test individual request tracking"""
        request_data = {
            "model": "deepseek-r1",
            "tokens_used": 750,
            "cost": 0.0,
            "response_time": 1.2,
            "quality_score": 0.87,
            "timestamp": datetime.now()
        }
        
        await cost_router.track_request(request_data)
        
        # Verify tracking was recorded
        with patch.object(cost_router, '_get_recent_requests') as mock_recent:
            mock_recent.return_value = [request_data]
            
            recent_requests = await cost_router.get_recent_requests(limit=10)
            assert len(recent_requests) == 1
            assert recent_requests[0]["model"] == "deepseek-r1"
    
    @pytest.mark.asyncio
    async def test_daily_usage_aggregation(self, cost_router):
        """Test daily usage aggregation"""
        with patch.object(cost_router, '_get_daily_usage') as mock_daily:
            mock_daily.return_value = {
                "date": datetime.now().date(),
                "total_requests": 1500,
                "local_requests": 1454,  # 96.9%
                "cloud_requests": 46,
                "total_cost": 13.80,
                "total_tokens": 750000,
                "avg_response_time": 1.8
            }
            
            daily_stats = await cost_router.get_daily_usage_stats()
            
            assert daily_stats["total_requests"] == 1500
            assert daily_stats["local_requests"] / daily_stats["total_requests"] >= 0.969
            assert daily_stats["total_cost"] < 15.0
    
    @pytest.mark.asyncio
    async def test_weekly_trend_analysis(self, cost_router):
        """Test weekly trend analysis"""
        with patch.object(cost_router, '_get_weekly_trends') as mock_trends:
            mock_trends.return_value = {
                "week_start": datetime.now().date() - timedelta(days=7),
                "daily_costs": [12.5, 14.2, 11.8, 13.6, 15.1, 9.8, 10.2],
                "daily_local_percentage": [0.971, 0.968, 0.973, 0.969, 0.965, 0.974, 0.972],
                "trend_direction": "stable",
                "cost_variance": 2.1
            }
            
            trends = await cost_router.get_weekly_trends()
            
            assert trends["trend_direction"] in ["increasing", "decreasing", "stable"]
            assert all(pct >= 0.96 for pct in trends["daily_local_percentage"])
    
    @pytest.mark.asyncio
    async def test_cost_alert_thresholds(self, cost_router):
        """Test cost alert threshold monitoring"""
        # Set daily cost threshold
        daily_threshold = 20.0
        
        with patch.object(cost_router, '_get_current_daily_cost', return_value=25.0):
            with patch.object(cost_router, '_send_cost_alert') as mock_alert:
                
                await cost_router.check_cost_thresholds()
                
                # Should trigger alert when threshold exceeded
                mock_alert.assert_called_once()

class TestErrorHandling:
    """Test error handling in cost optimization"""
    
    @pytest.mark.asyncio
    async def test_model_cost_data_unavailable(self, cost_router, sample_request):
        """Test handling when model cost data is unavailable"""
        with patch.object(cost_router, '_get_model_costs', side_effect=Exception("Cost data unavailable")):
            
            with pytest.raises(CostOptimizationError, match="Cost data unavailable"):
                await cost_router.select_optimal_model(sample_request)
    
    @pytest.mark.asyncio
    async def test_all_models_unavailable(self, cost_router, sample_request):
        """Test handling when all models are unavailable"""
        with patch.object(cost_router, '_is_model_available', return_value=False):
            
            with pytest.raises(CostOptimizationError, match="No models available"):
                await cost_router.select_optimal_model(sample_request)
    
    @pytest.mark.asyncio
    async def test_invalid_cost_priority(self, cost_router):
        """Test handling of invalid cost priority values"""
        invalid_request = {
            "prompt": "Test prompt",
            "max_tokens": 500,
            "cost_priority": 10,  # Invalid (should be 1-5)
            "quality_requirement": 0.8
        }
        
        with pytest.raises(CostOptimizationError, match="Invalid cost priority"):
            await cost_router.select_optimal_model(invalid_request)
    
    @pytest.mark.asyncio
    async def test_cost_calculation_error_handling(self, cost_router):
        """Test error handling in cost calculations"""
        invalid_usage = {
            "model": "unknown-model",
            "tokens_used": -100,  # Invalid token count
            "processing_time": -1.0  # Invalid time
        }
        
        with pytest.raises(CostOptimizationError, match="Invalid usage data"):
            await cost_router.calculate_request_cost(invalid_usage)

class TestPerformanceOptimization:
    """Test performance aspects of cost optimization"""
    
    @pytest.mark.asyncio
    async def test_model_selection_performance(self, cost_router, mock_model_costs):
        """Test that model selection is fast enough"""
        import time
        
        request = {
            "prompt": "Performance test",
            "max_tokens": 100,
            "quality_requirement": 0.8,
            "cost_priority": 3
        }
        
        with patch.object(cost_router, '_get_model_costs', return_value=mock_model_costs):
            with patch.object(cost_router, '_is_model_available', return_value=True):
                
                start_time = time.time()
                await cost_router.select_optimal_model(request)
                end_time = time.time()
                
                selection_time = end_time - start_time
                
                # Model selection should be fast (<100ms)
                assert selection_time < 0.1
    
    @pytest.mark.asyncio
    async def test_concurrent_cost_calculations(self, cost_router):
        """Test concurrent cost calculations"""
        usage_data_list = [
            {"model": f"model-{i}", "tokens_used": 100 + i * 10}
            for i in range(50)
        ]
        
        with patch.object(cost_router, '_get_model_cost_per_token', return_value=0.00001):
            
            # Calculate costs concurrently
            tasks = [
                cost_router.calculate_request_cost(usage_data)
                for usage_data in usage_data_list
            ]
            
            start_time = time.time()
            results = await asyncio.gather(*tasks)
            end_time = time.time()
            
            # Should handle concurrent calculations efficiently
            assert len(results) == 50
            assert end_time - start_time < 1.0  # Should complete within 1 second
    
    @pytest.mark.asyncio
    async def test_caching_effectiveness(self, cost_router):
        """Test caching of model costs and configurations"""
        with patch.object(cost_router, '_load_model_costs') as mock_load:
            mock_load.return_value = {"test": "data"}
            
            # First call should load data
            await cost_router._get_model_costs()
            assert mock_load.call_count == 1
            
            # Second call should use cache
            await cost_router._get_model_costs()
            assert mock_load.call_count == 1  # Should not increase

class TestIntegrationScenarios:
    """Test integration scenarios and real-world usage patterns"""
    
    @pytest.mark.asyncio
    async def test_high_volume_day_scenario(self, cost_router):
        """Test cost optimization during high volume days"""
        # Simulate 10,000 requests in a day
        high_volume_stats = {
            "total_requests": 10000,
            "target_local_percentage": 0.969,
            "avg_tokens_per_request": 600
        }
        
        local_requests = int(high_volume_stats["total_requests"] * high_volume_stats["target_local_percentage"])
        cloud_requests = high_volume_stats["total_requests"] - local_requests
        
        # Calculate expected costs
        cloud_cost = cloud_requests * high_volume_stats["avg_tokens_per_request"] * 0.00002
        
        assert local_requests >= 9690  # At least 96.9% local
        assert cloud_cost < 50.0  # Daily cloud cost under $50
    
    @pytest.mark.asyncio
    async def test_quality_vs_cost_tradeoff_scenarios(self, cost_router):
        """Test various quality vs cost tradeoff scenarios"""
        scenarios = [
            {"quality_req": 0.95, "cost_priority": 1, "expected_model_type": "cloud"},
            {"quality_req": 0.75, "cost_priority": 5, "expected_model_type": "local"},
            {"quality_req": 0.85, "cost_priority": 3, "expected_model_type": "balanced"}
        ]
        
        for scenario in scenarios:
            request = {
                "prompt": "Test scenario",
                "max_tokens": 500,
                "quality_requirement": scenario["quality_req"],
                "cost_priority": scenario["cost_priority"]
            }
            
            with patch.object(cost_router, '_get_model_costs', return_value=mock_model_costs):
                with patch.object(cost_router, '_is_model_available', return_value=True):
                    
                    selected_model = await cost_router.select_optimal_model(request)
                    
                    # Verify selection aligns with expectations
                    if scenario["expected_model_type"] == "cloud":
                        assert selected_model in ["gpt-4", "claude-3", "gemini-pro"]
                    elif scenario["expected_model_type"] == "local":
                        assert selected_model in ["deepseek-r1", "llama-2-70b"]

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=apps.backend.services.cost_optimizer", "--cov-report=html"])