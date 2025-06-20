"""
Unit tests for Enhanced Error Handler module
"""

import sys
import os
import unittest
import json
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.testclient import TestClient
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.revoagent.utils.error_handler import (
    ErrorDetails,
    ErrorCategory,
    ErrorSeverity,
    register_error_handlers,
    handle_validation_error,
    handle_llm_error
)

# Create a test FastAPI app
app = FastAPI()
register_error_handlers(app)

# Define a model for testing validation
class TestModel(BaseModel):
    name: str = Field(..., min_length=3)
    age: int = Field(..., gt=0, lt=150)

# Test endpoint with validation
@app.post("/test/validation")
async def test_validation_endpoint(data: TestModel):
    return {"message": "Valid data received", "data": data.dict()}

# Test endpoint with HTTP exception
@app.get("/test/http-error")
async def test_http_error():
    raise HTTPException(status_code=404, detail="Resource not found")

# Test endpoint with general exception
@app.get("/test/general-error")
async def test_general_error():
    # Intentionally raise an exception
    raise ValueError("This is a test error")

# Test endpoint with LLM error
@app.get("/test/llm-error")
async def test_llm_error(request: Request):
    return handle_llm_error(
        request,
        "Failed to generate LLM response",
        original_exception=Exception("Model timeout"),
        details={"model": "test-model"}
    )

class TestErrorHandler(unittest.TestCase):
    """Test cases for Enhanced Error Handler"""
    
    def setUp(self):
        """Set up test client"""
        self.client = TestClient(app)
    
    def test_error_details_class(self):
        """Test ErrorDetails class functionality"""
        # Create an error details object
        error = ErrorDetails(
            message="Test error message",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            status_code=400,
            error_code="TEST_001",
            details={"field": "test_field"},
            client_message="User-friendly error message"
        )
        
        # Test properties
        self.assertEqual(error.message, "Test error message")
        self.assertEqual(error.category, ErrorCategory.VALIDATION)
        self.assertEqual(error.severity, ErrorSeverity.MEDIUM)
        self.assertEqual(error.status_code, 400)
        self.assertEqual(error.error_code, "TEST_001")
        self.assertEqual(error.details, {"field": "test_field"})
        self.assertEqual(error.client_message, "User-friendly error message")
        
        # Test to_dict method
        error_dict = error.to_dict()
        self.assertIn("error", error_dict)
        self.assertEqual(error_dict["error"]["message"], "User-friendly error message")
        self.assertEqual(error_dict["error"]["code"], "TEST_001")
        self.assertEqual(error_dict["error"]["category"], "validation_error")
        
        # Test internal details
        error_dict_internal = error.to_dict(include_internal=True)
        self.assertIn("internal_message", error_dict_internal["error"])
        self.assertEqual(error_dict_internal["error"]["internal_message"], "Test error message")
    
    def test_validation_error_handling(self):
        """Test validation error handling"""
        # Send invalid data to trigger validation error
        response = self.client.post(
            "/test/validation",
            json={"name": "A", "age": 200}  # Invalid: name too short, age too high
        )
        
        # Check response
        self.assertEqual(response.status_code, 422)
        data = response.json()
        self.assertIn("error", data)
        self.assertEqual(data["error"]["category"], "validation_error")
        
        # Send another invalid request
        response = self.client.post(
            "/test/validation",
            json={"name": "Alice"}  # Missing required field: age
        )
        
        # Check response
        self.assertEqual(response.status_code, 422)
        data = response.json()
        self.assertIn("error", data)
    
    def test_http_exception_handling(self):
        """Test HTTP exception handling"""
        response = self.client.get("/test/http-error")
        
        # Check response
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn("error", data)
        self.assertEqual(data["error"]["message"], "Resource not found")
    
    def test_general_exception_handling(self):
        """Test general exception handling"""
        response = self.client.get("/test/general-error")
        
        # Check response
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn("error", data)
        # General exceptions should have a generic client message
        self.assertIn("occurred", data["error"]["message"])
    
    def test_llm_error_handling(self):
        """Test LLM error handling"""
        response = self.client.get("/test/llm-error")
        
        # Check response
        self.assertEqual(response.status_code, 503)  # Service Unavailable
        data = response.json()
        self.assertIn("error", data)
        self.assertEqual(data["error"]["category"], "llm_error")
        # Should have a user-friendly message
        self.assertIn("AI model", data["error"]["message"])

if __name__ == "__main__":
    unittest.main()