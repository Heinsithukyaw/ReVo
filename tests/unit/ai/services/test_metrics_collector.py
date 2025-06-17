"""
Unit tests for MetricsCollector service.
"""

import pytest
import time
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from packages.ai.services.metrics_collector import MetricsCollector, ModelMetrics, SystemMetrics


class TestMetricsCollector:
    """Test cases for MetricsCollector service."""
    
    @pytest.fixture
    def metrics_collector(self):
        """Create MetricsCollector instance for testing."""
        return MetricsCollector(retention_hours=1)  # Short retention for testing
    
    def test_initialization(self, metrics_collector):
        """Test MetricsCollector initialization."""
        assert isinstance(metrics_collector.model_metrics, dict)
        assert len(metrics_collector.model_metrics) == 0
        assert metrics_collector.retention_hours == 1
        assert len(metrics_collector.system_metrics_history) == 0
        assert len(metrics_collector.request_timestamps) == 0
    
    def test_record_request_start(self, metrics_collector):
        """Test recording request start."""
        request_id = metrics_collector.record_request_start("test-model")
        
        assert request_id.startswith("test-model_")
        assert "test-model" in metrics_collector.model_metrics
        assert metrics_collector.model_metrics["test-model"].total_requests == 1
        assert len(metrics_collector.request_timestamps) == 1
    
    def test_record_request_completion_success(self, metrics_collector):
        """Test recording successful request completion."""
        # Start a request first
        metrics_collector.record_request_start("test-model")
        
        # Complete the request
        metrics_collector.record_request_completion(
            "test-model", 
            response_time=2.5, 
            tokens_generated=100, 
            success=True
        )
        
        metrics = metrics_collector.model_metrics["test-model"]
        assert metrics.successful_requests == 1
        assert metrics.failed_requests == 0
        assert metrics.total_response_time == 2.5
        assert metrics.total_tokens_generated == 100
        assert metrics.last_used is not None
        assert len(metrics.recent_response_times) == 1
        assert metrics.recent_response_times[0] == 2.5
        
        # Check calculated metrics
        assert metrics.error_rate == 0.0
        assert metrics.avg_response_time == 2.5
        assert metrics.tokens_per_second == 100 / 2.5
    
    def test_record_request_completion_failure(self, metrics_collector):
        """Test recording failed request completion."""
        # Start a request first
        metrics_collector.record_request_start("test-model")
        
        # Complete the request with failure
        metrics_collector.record_request_completion(
            "test-model", 
            response_time=1.0, 
            tokens_generated=0, 
            success=False,
            error="Test error"
        )
        
        metrics = metrics_collector.model_metrics["test-model"]
        assert metrics.successful_requests == 0
        assert metrics.failed_requests == 1
        assert metrics.total_response_time == 0.0  # Not added for failed requests
        assert metrics.total_tokens_generated == 0
        assert len(metrics.recent_response_times) == 0  # Not added for failed requests
        
        # Check calculated metrics
        assert metrics.error_rate == 100.0  # 1 failure out of 1 total
    
    def test_update_model_resource_usage(self, metrics_collector):
        """Test updating model resource usage."""
        metrics_collector.update_model_resource_usage("test-model", 4.5, 2.1)
        
        assert "test-model" in metrics_collector.model_metrics
        metrics = metrics_collector.model_metrics["test-model"]
        assert metrics.memory_usage_gb == 4.5
        assert metrics.gpu_memory_gb == 2.1
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('torch.cuda.is_available')
    def test_collect_system_metrics_no_gpu(self, mock_cuda, mock_memory, mock_cpu, metrics_collector):
        """Test collecting system metrics without GPU."""
        # Mock system metrics
        mock_cpu.return_value = 45.2
        mock_memory.return_value = Mock(
            percent=67.8,
            used=8 * 1024**3,  # 8GB
            total=16 * 1024**3  # 16GB
        )
        mock_cuda.return_value = False
        
        # Add some request timestamps
        now = datetime.now()
        metrics_collector.request_timestamps.extend([
            now - timedelta(seconds=30),
            now - timedelta(seconds=45),
            now - timedelta(seconds=50)
        ])
        
        system_metrics = metrics_collector.collect_system_metrics()
        
        assert isinstance(system_metrics, SystemMetrics)
        assert system_metrics.cpu_percent == 45.2
        assert system_metrics.memory_percent == 67.8
        assert system_metrics.memory_used_gb == 8.0
        assert system_metrics.memory_total_gb == 16.0
        assert system_metrics.gpu_memory_used_gb == 0.0
        assert system_metrics.gpu_memory_total_gb == 0.0
        assert system_metrics.gpu_utilization == 0.0
        assert system_metrics.total_requests_per_minute == 3  # All 3 requests within last minute
        
        # Check that metrics were stored in history
        assert len(metrics_collector.system_metrics_history) == 1
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('torch.cuda.is_available')
    @patch('torch.cuda.memory_allocated')
    @patch('torch.cuda.get_device_properties')
    def test_collect_system_metrics_with_gpu(self, mock_props, mock_allocated, mock_cuda, 
                                           mock_memory, mock_cpu, metrics_collector):
        """Test collecting system metrics with GPU."""
        # Mock system metrics
        mock_cpu.return_value = 55.0
        mock_memory.return_value = Mock(percent=75.0, used=12 * 1024**3, total=16 * 1024**3)
        mock_cuda.return_value = True
        mock_allocated.return_value = 6 * 1024**3  # 6GB
        mock_props.return_value = Mock(total_memory=8 * 1024**3)  # 8GB total
        
        with patch.object(metrics_collector, '_get_gpu_utilization', return_value=80.5):
            system_metrics = metrics_collector.collect_system_metrics()
        
        assert system_metrics.gpu_memory_used_gb == 6.0
        assert system_metrics.gpu_memory_total_gb == 8.0
        assert system_metrics.gpu_utilization == 80.5
    
    def test_get_model_metrics_specific(self, metrics_collector):
        """Test getting metrics for specific model."""
        # Add some metrics
        metrics_collector.record_request_start("test-model")
        metrics_collector.record_request_completion("test-model", 1.5, 50, True)
        
        model_metrics = metrics_collector.get_model_metrics("test-model")
        
        assert isinstance(model_metrics, dict)
        assert model_metrics["model_id"] == "test-model"
        assert model_metrics["total_requests"] == 1
        assert model_metrics["successful_requests"] == 1
        assert model_metrics["avg_response_time"] == 1.5
        assert model_metrics["total_tokens_generated"] == 50
    
    def test_get_model_metrics_all(self, metrics_collector):
        """Test getting metrics for all models."""
        # Add metrics for multiple models
        metrics_collector.record_request_start("model1")
        metrics_collector.record_request_completion("model1", 1.0, 25, True)
        
        metrics_collector.record_request_start("model2")
        metrics_collector.record_request_completion("model2", 2.0, 75, True)
        
        all_metrics = metrics_collector.get_model_metrics()
        
        assert isinstance(all_metrics, dict)
        assert len(all_metrics) == 2
        assert "model1" in all_metrics
        assert "model2" in all_metrics
        assert all_metrics["model1"]["avg_response_time"] == 1.0
        assert all_metrics["model2"]["avg_response_time"] == 2.0
    
    def test_get_model_metrics_nonexistent(self, metrics_collector):
        """Test getting metrics for non-existent model."""
        model_metrics = metrics_collector.get_model_metrics("nonexistent")
        assert model_metrics == {}
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('torch.cuda.is_available')
    def test_get_performance_summary(self, mock_cuda, mock_memory, mock_cpu, metrics_collector):
        """Test getting performance summary."""
        # Mock system metrics
        mock_cpu.return_value = 50.0
        mock_memory.return_value = Mock(percent=60.0, used=8 * 1024**3, total=16 * 1024**3)
        mock_cuda.return_value = False
        
        # Add some test data
        metrics_collector.record_request_start("model1")
        metrics_collector.record_request_completion("model1", 1.5, 100, True)
        
        metrics_collector.record_request_start("model2")
        metrics_collector.record_request_completion("model2", 2.0, 50, False, "Error")
        
        summary = metrics_collector.get_performance_summary()
        
        assert isinstance(summary, dict)
        assert summary["total_requests"] == 2
        assert summary["successful_requests"] == 1
        assert summary["failed_requests"] == 1
        assert summary["overall_error_rate"] == 50.0
        assert summary["average_response_time"] == 1.5  # Only successful requests
        assert summary["active_models"] == 2
        
        assert "system_metrics" in summary
        assert summary["system_metrics"]["cpu_percent"] == 50.0
        assert summary["system_metrics"]["memory_percent"] == 60.0
        
        assert "top_performing_models" in summary
        assert isinstance(summary["top_performing_models"], list)
    
    def test_get_alerts_high_memory(self, metrics_collector):
        """Test alerts for high memory usage."""
        with patch.object(metrics_collector, 'collect_system_metrics') as mock_collect:
            mock_collect.return_value = SystemMetrics(
                cpu_percent=50.0,
                memory_percent=90.0,  # High memory
                memory_used_gb=14.4,
                memory_total_gb=16.0,
                gpu_memory_used_gb=0.0,
                gpu_memory_total_gb=0.0,
                gpu_utilization=0.0,
                active_models=1,
                total_requests_per_minute=10
            )
            
            alerts = metrics_collector.get_alerts()
        
        assert len(alerts) >= 1
        memory_alert = next((a for a in alerts if a["type"] == "high_memory_usage"), None)
        assert memory_alert is not None
        assert memory_alert["severity"] == "warning"
        assert "90.0%" in memory_alert["message"]
    
    def test_get_alerts_high_cpu(self, metrics_collector):
        """Test alerts for high CPU usage."""
        with patch.object(metrics_collector, 'collect_system_metrics') as mock_collect:
            mock_collect.return_value = SystemMetrics(
                cpu_percent=95.0,  # High CPU
                memory_percent=50.0,
                memory_used_gb=8.0,
                memory_total_gb=16.0,
                gpu_memory_used_gb=0.0,
                gpu_memory_total_gb=0.0,
                gpu_utilization=0.0,
                active_models=1,
                total_requests_per_minute=10
            )
            
            alerts = metrics_collector.get_alerts()
        
        cpu_alert = next((a for a in alerts if a["type"] == "high_cpu_usage"), None)
        assert cpu_alert is not None
        assert cpu_alert["severity"] == "warning"
        assert "95.0%" in cpu_alert["message"]
    
    def test_get_alerts_high_error_rate(self, metrics_collector):
        """Test alerts for high error rate."""
        # Create model with high error rate
        metrics_collector.record_request_start("error-model")
        metrics_collector.record_request_completion("error-model", 1.0, 0, False, "Error 1")
        metrics_collector.record_request_start("error-model")
        metrics_collector.record_request_completion("error-model", 1.0, 0, False, "Error 2")
        metrics_collector.record_request_start("error-model")
        metrics_collector.record_request_completion("error-model", 1.0, 50, True)  # 1 success, 2 failures = 66% error rate
        
        with patch.object(metrics_collector, 'collect_system_metrics') as mock_collect:
            mock_collect.return_value = SystemMetrics(
                cpu_percent=50.0, memory_percent=50.0, memory_used_gb=8.0, memory_total_gb=16.0,
                gpu_memory_used_gb=0.0, gpu_memory_total_gb=0.0, gpu_utilization=0.0,
                active_models=1, total_requests_per_minute=10
            )
            
            alerts = metrics_collector.get_alerts()
        
        error_alert = next((a for a in alerts if a["type"] == "high_error_rate"), None)
        assert error_alert is not None
        assert error_alert["severity"] == "critical"
        assert error_alert["model_id"] == "error-model"
    
    def test_get_alerts_slow_response(self, metrics_collector):
        """Test alerts for slow response times."""
        # Create model with slow response time
        metrics_collector.record_request_start("slow-model")
        metrics_collector.record_request_completion("slow-model", 35.0, 100, True)  # 35 seconds
        
        with patch.object(metrics_collector, 'collect_system_metrics') as mock_collect:
            mock_collect.return_value = SystemMetrics(
                cpu_percent=50.0, memory_percent=50.0, memory_used_gb=8.0, memory_total_gb=16.0,
                gpu_memory_used_gb=0.0, gpu_memory_total_gb=0.0, gpu_utilization=0.0,
                active_models=1, total_requests_per_minute=10
            )
            
            alerts = metrics_collector.get_alerts()
        
        slow_alert = next((a for a in alerts if a["type"] == "slow_response_time"), None)
        assert slow_alert is not None
        assert slow_alert["severity"] == "warning"
        assert slow_alert["model_id"] == "slow-model"
    
    def test_cleanup_old_metrics(self, metrics_collector):
        """Test cleanup of old metrics."""
        # Add old request timestamps
        old_time = datetime.now() - timedelta(hours=2)
        recent_time = datetime.now() - timedelta(minutes=30)
        
        metrics_collector.request_timestamps.extend([old_time, recent_time])
        
        # Run cleanup
        metrics_collector.cleanup_old_metrics()
        
        # Old timestamp should be removed, recent one should remain
        assert len(metrics_collector.request_timestamps) == 1
        assert metrics_collector.request_timestamps[0] == recent_time
    
    def test_get_top_performing_models(self, metrics_collector):
        """Test getting top performing models."""
        # Add models with different performance
        metrics_collector.record_request_start("fast-model")
        metrics_collector.record_request_completion("fast-model", 1.0, 100, True)  # 100 tokens/sec
        
        metrics_collector.record_request_start("slow-model")
        metrics_collector.record_request_completion("slow-model", 2.0, 100, True)  # 50 tokens/sec
        
        top_models = metrics_collector._get_top_performing_models(limit=2)
        
        assert len(top_models) == 2
        assert top_models[0]["model_id"] == "fast-model"
        assert top_models[0]["tokens_per_second"] == 100.0
        assert top_models[1]["model_id"] == "slow-model"
        assert top_models[1]["tokens_per_second"] == 50.0
    
    def test_multiple_requests_same_model(self, metrics_collector):
        """Test multiple requests for the same model."""
        model_id = "test-model"
        
        # First request
        metrics_collector.record_request_start(model_id)
        metrics_collector.record_request_completion(model_id, 1.0, 50, True)
        
        # Second request
        metrics_collector.record_request_start(model_id)
        metrics_collector.record_request_completion(model_id, 2.0, 100, True)
        
        metrics = metrics_collector.model_metrics[model_id]
        
        assert metrics.total_requests == 2
        assert metrics.successful_requests == 2
        assert metrics.failed_requests == 0
        assert metrics.total_response_time == 3.0
        assert metrics.total_tokens_generated == 150
        assert metrics.avg_response_time == 1.5
        assert metrics.tokens_per_second == 150 / 3.0
        assert len(metrics.recent_response_times) == 2