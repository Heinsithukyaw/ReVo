#!/usr/bin/env python3
"""
Unit tests for Quality Gates
Tests the multi-layer validation system for AI-generated content
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from apps.backend.services.quality_gates import QualityGates, QualityReport, QualityMetrics


class TestQualityGates:
    """Test suite for QualityGates"""
    
    @pytest.fixture
    def quality_gates(self):
        """Create quality gates instance for testing"""
        return QualityGates()
    
    @pytest.mark.unit
    def test_quality_gates_initialization(self, quality_gates):
        """Test quality gates initializes with correct thresholds"""
        # Check quality thresholds
        thresholds = quality_gates.quality_thresholds
        
        assert thresholds["syntax_minimum"] == 95.0
        assert thresholds["security_minimum"] == 85.0
        assert thresholds["performance_minimum"] == 70.0
        assert thresholds["test_coverage_minimum"] == 80.0
        assert thresholds["documentation_minimum"] == 75.0
        assert thresholds["overall_minimum"] == 80.0
        
        # Check validation history is initialized
        assert quality_gates.validation_history == {}
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_code_validation_success(self, quality_gates):
        """Test successful code validation with high quality score"""
        good_code = '''
def calculate_fibonacci(n: int) -> int:
    """
    Calculate the nth Fibonacci number using dynamic programming.
    
    Args:
        n (int): The position in the Fibonacci sequence
        
    Returns:
        int: The nth Fibonacci number
        
    Raises:
        ValueError: If n is negative
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    
    if n <= 1:
        return n
    
    # Use dynamic programming for efficiency
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    
    return b
'''
        
        report = await quality_gates.validate_generated_code(
            good_code, 
            "claude-001", 
            "code"
        )
        
        # Verify high quality scores
        assert report.quality_metrics.syntax_score >= 0.95
        assert report.quality_metrics.security_score >= 0.85
        assert report.quality_metrics.documentation_score >= 0.90
        assert report.quality_metrics.overall_score >= 0.80
        assert report.validation_passed is True
        
        # Verify report structure
        assert report.agent_id == "claude-001"
        assert report.validation_type == "code"
        assert report.validation_id is not None
        assert report.timestamp is not None
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_security_vulnerability_detection(self, quality_gates):
        """Test detection of security vulnerabilities in code"""
        vulnerable_code = '''
def get_user_data(user_id):
    # SQL injection vulnerability
    query = "SELECT * FROM users WHERE id = " + user_id
    result = execute_query(query)
    
    # Password in plain text
    password = "admin123"
    
    # Unsafe eval usage
    user_input = request.get('code')
    eval(user_input)
    
    return result
'''
        
        report = await quality_gates.validate_generated_code(
            vulnerable_code,
            "claude-002", 
            "code"
        )
        
        # Should detect security issues
        assert report.quality_metrics.security_score < 0.5
        assert report.validation_passed is False
        
        # Check security issues are identified
        assert len(report.security_issues) > 0
        security_types = [issue["type"] for issue in report.security_issues]
        assert "sql_injection" in security_types
        assert "hardcoded_password" in security_types
        assert "unsafe_eval" in security_types
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_syntax_error_detection(self, quality_gates):
        """Test detection of syntax errors in code"""
        syntax_error_code = '''
def broken_function(
    # Missing closing parenthesis
    print("This will cause a syntax error"
    return "incomplete"
'''
        
        report = await quality_gates.validate_generated_code(
            syntax_error_code,
            "claude-003",
            "code"
        )
        
        # Should detect syntax issues
        assert report.quality_metrics.syntax_score < 0.5
        assert report.validation_passed is False
        
        # Check syntax errors are identified
        assert len(report.syntax_errors) > 0
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_performance_analysis(self, quality_gates):
        """Test performance analysis of code"""
        inefficient_code = '''
def inefficient_fibonacci(n):
    # O(2^n) time complexity - very inefficient
    if n <= 1:
        return n
    return inefficient_fibonacci(n-1) + inefficient_fibonacci(n-2)

def nested_loops_example(data):
    # O(n^3) complexity - inefficient
    result = []
    for i in range(len(data)):
        for j in range(len(data)):
            for k in range(len(data)):
                if i + j + k < len(data):
                    result.append(data[i] + data[j] + data[k])
    return result
'''
        
        report = await quality_gates.validate_generated_code(
            inefficient_code,
            "claude-004",
            "code"
        )
        
        # Should detect performance issues
        assert report.quality_metrics.performance_score < 0.7
        
        # Check performance issues are identified
        assert len(report.performance_issues) > 0
        performance_types = [issue["type"] for issue in report.performance_issues]
        assert "high_complexity" in performance_types
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_documentation_quality_assessment(self, quality_gates):
        """Test assessment of documentation quality"""
        poorly_documented_code = '''
def func(x, y):
    z = x + y
    if z > 10:
        return z * 2
    return z
'''
        
        well_documented_code = '''
def calculate_adjusted_sum(first_number: int, second_number: int) -> int:
    """
    Calculate the sum of two numbers with adjustment based on threshold.
    
    If the sum exceeds 10, it is doubled to account for scaling factor.
    Otherwise, the original sum is returned.
    
    Args:
        first_number (int): The first number to add
        second_number (int): The second number to add
        
    Returns:
        int: The adjusted sum based on threshold logic
        
    Example:
        >>> calculate_adjusted_sum(5, 7)
        24
        >>> calculate_adjusted_sum(3, 4)
        7
    """
    total_sum = first_number + second_number
    
    # Apply scaling factor if sum exceeds threshold
    if total_sum > 10:
        return total_sum * 2
    
    return total_sum
'''
        
        # Test poorly documented code
        poor_report = await quality_gates.validate_generated_code(
            poorly_documented_code,
            "claude-005",
            "code"
        )
        
        # Test well documented code
        good_report = await quality_gates.validate_generated_code(
            well_documented_code,
            "claude-006", 
            "code"
        )
        
        # Compare documentation scores
        assert good_report.quality_metrics.documentation_score > poor_report.quality_metrics.documentation_score
        assert good_report.quality_metrics.documentation_score >= 0.8
        assert poor_report.quality_metrics.documentation_score < 0.5
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validation_history_tracking(self, quality_gates):
        """Test validation history is properly tracked"""
        code_sample = '''
def simple_function():
    return "Hello, World!"
'''
        
        # Perform multiple validations
        agent_id = "claude-007"
        for i in range(3):
            await quality_gates.validate_generated_code(
                code_sample,
                agent_id,
                "code"
            )
        
        # Check history tracking
        assert agent_id in quality_gates.validation_history
        history = quality_gates.validation_history[agent_id]
        assert len(history) == 3
        
        # Verify history entries have required fields
        for entry in history:
            assert "validation_id" in entry
            assert "timestamp" in entry
            assert "overall_score" in entry
            assert "validation_passed" in entry
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_different_validation_types(self, quality_gates):
        """Test validation of different content types"""
        # Test documentation validation
        documentation = '''
# API Documentation
This API provides user management functionality.

## Endpoints
- GET /users - List all users
- POST /users - Create new user
'''
        
        doc_report = await quality_gates.validate_generated_code(
            documentation,
            "gemini-001",
            "documentation"
        )
        
        # Test configuration validation
        config = '''
database:
  host: localhost
  port: 5432
  name: myapp
  
redis:
  host: localhost
  port: 6379
'''
        
        config_report = await quality_gates.validate_generated_code(
            config,
            "gemini-002",
            "configuration"
        )
        
        # Verify different validation logic applied
        assert doc_report.validation_type == "documentation"
        assert config_report.validation_type == "configuration"
        
        # Both should have quality metrics
        assert doc_report.quality_metrics is not None
        assert config_report.quality_metrics is not None
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_concurrent_validations(self, quality_gates):
        """Test handling of concurrent validations"""
        code_samples = [
            f'def function_{i}():\n    return {i}'
            for i in range(10)
        ]
        
        # Run concurrent validations
        validation_tasks = [
            quality_gates.validate_generated_code(
                code,
                f"agent-{i}",
                "code"
            )
            for i, code in enumerate(code_samples)
        ]
        
        reports = await asyncio.gather(*validation_tasks)
        
        # Verify all validations completed
        assert len(reports) == 10
        
        # Verify each report is valid
        for i, report in enumerate(reports):
            assert report.agent_id == f"agent-{i}"
            assert report.quality_metrics is not None
            assert report.validation_id is not None
    
    @pytest.mark.unit
    def test_quality_metrics_calculation(self, quality_gates):
        """Test quality metrics calculation logic"""
        # Test individual metric calculations
        syntax_score = quality_gates._calculate_syntax_score("def valid_function(): pass")
        assert 0.0 <= syntax_score <= 1.0
        
        security_score = quality_gates._calculate_security_score("safe_code = 'hello'")
        assert 0.0 <= security_score <= 1.0
        
        performance_score = quality_gates._calculate_performance_score("efficient_code = [1, 2, 3]")
        assert 0.0 <= performance_score <= 1.0
        
        documentation_score = quality_gates._calculate_documentation_score('"""Well documented function"""')
        assert 0.0 <= documentation_score <= 1.0
    
    @pytest.mark.unit
    def test_validation_thresholds_customization(self, quality_gates):
        """Test customization of validation thresholds"""
        # Update thresholds
        new_thresholds = {
            "syntax_minimum": 90.0,
            "security_minimum": 80.0,
            "performance_minimum": 60.0,
            "overall_minimum": 75.0
        }
        
        quality_gates.update_quality_thresholds(new_thresholds)
        
        # Verify thresholds updated
        for key, value in new_thresholds.items():
            assert quality_gates.quality_thresholds[key] == value
    
    @pytest.mark.unit
    def test_agent_performance_analytics(self, quality_gates):
        """Test agent performance analytics"""
        # Add some validation history
        agent_id = "claude-analytics"
        quality_gates.validation_history[agent_id] = [
            {"validation_id": "1", "overall_score": 0.9, "validation_passed": True, "timestamp": "2025-01-01"},
            {"validation_id": "2", "overall_score": 0.8, "validation_passed": True, "timestamp": "2025-01-02"},
            {"validation_id": "3", "overall_score": 0.7, "validation_passed": False, "timestamp": "2025-01-03"},
        ]
        
        analytics = quality_gates.get_agent_performance_analytics(agent_id)
        
        # Verify analytics
        assert analytics["total_validations"] == 3
        assert analytics["success_rate"] == 2/3  # 2 out of 3 passed
        assert analytics["average_score"] == 0.8  # (0.9 + 0.8 + 0.7) / 3
        assert analytics["trend"] in ["improving", "declining", "stable"]


class TestQualityReport:
    """Test suite for QualityReport model"""
    
    @pytest.mark.unit
    def test_quality_report_creation(self):
        """Test QualityReport can be created with required fields"""
        metrics = QualityMetrics(
            syntax_score=0.95,
            security_score=0.90,
            performance_score=0.85,
            documentation_score=0.80,
            test_coverage_score=0.75,
            overall_score=0.85
        )
        
        report = QualityReport(
            validation_id="test_123",
            agent_id="claude-test",
            validation_type="code",
            quality_metrics=metrics,
            validation_passed=True
        )
        
        assert report.validation_id == "test_123"
        assert report.agent_id == "claude-test"
        assert report.validation_type == "code"
        assert report.quality_metrics == metrics
        assert report.validation_passed is True
        assert report.timestamp is not None


class TestQualityMetrics:
    """Test suite for QualityMetrics model"""
    
    @pytest.mark.unit
    def test_quality_metrics_creation(self):
        """Test QualityMetrics can be created with scores"""
        metrics = QualityMetrics(
            syntax_score=0.95,
            security_score=0.90,
            performance_score=0.85,
            documentation_score=0.80,
            test_coverage_score=0.75,
            overall_score=0.85
        )
        
        assert metrics.syntax_score == 0.95
        assert metrics.security_score == 0.90
        assert metrics.performance_score == 0.85
        assert metrics.documentation_score == 0.80
        assert metrics.test_coverage_score == 0.75
        assert metrics.overall_score == 0.85
    
    @pytest.mark.unit
    def test_quality_metrics_validation(self):
        """Test QualityMetrics validates score ranges"""
        # Test invalid scores (should be 0.0-1.0)
        with pytest.raises(ValueError):
            QualityMetrics(syntax_score=1.5)  # Too high
        
        with pytest.raises(ValueError):
            QualityMetrics(security_score=-0.1)  # Too low


if __name__ == "__main__":
    pytest.main([__file__, "-v"])