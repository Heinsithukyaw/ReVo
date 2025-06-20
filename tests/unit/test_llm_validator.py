"""
Unit tests for LLM Validator module
"""

import sys
import os
import unittest
import asyncio
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.revoagent.validation.llm_validator import (
    llm_validator,
    ValidationType,
    ValidationLevel,
    ValidationResult
)

class TestLLMValidator(unittest.TestCase):
    """Test cases for LLM Validator"""
    
    def setUp(self):
        """Set up test cases"""
        self.validator = llm_validator
        
        # Sample data for testing
        self.valid_code = """
def hello_world():
    \"\"\"Return a hello world message\"\"\"
    return "Hello, World!"
    
if __name__ == "__main__":
    print(hello_world())
"""
        
        self.invalid_code = """
def hello_world():
    \"\"\"Return a hello world message\"\"\"
    return "Hello, World!
    
if __name__ == "__main__":
    print(hello_world())
"""
        
        self.prompt = "Write a hello world function in Python"
        self.relevant_response = "Here's a simple hello world function in Python:\n\n```python\ndef hello_world():\n    return \"Hello, World!\"\n```\n\nYou can call this function to print the greeting."
        self.irrelevant_response = "The capital of France is Paris. It's a beautiful city with many historic landmarks like the Eiffel Tower."

    def test_code_syntax_validation(self):
        """Test code syntax validation"""
        # Test valid code
        result = self.validator.validate_code_syntax(self.valid_code)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.validation_type, ValidationType.CODE_SYNTAX)
        self.assertGreaterEqual(result.score, 0.9)
        
        # Test invalid code
        result = self.validator.validate_code_syntax(self.invalid_code)
        self.assertFalse(result.is_valid)
        self.assertEqual(result.validation_type, ValidationType.CODE_SYNTAX)
        self.assertLess(result.score, 0.5)
        self.assertGreater(len(result.issues), 0)
    
    def test_relevance_validation(self):
        """Test relevance validation"""
        # Test relevant response
        result = self.validator.validate_relevance(self.relevant_response, self.prompt)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.validation_type, ValidationType.RELEVANCE)
        self.assertGreaterEqual(result.score, 0.5)
        
        # Test irrelevant response
        result = self.validator.validate_relevance(self.irrelevant_response, self.prompt)
        self.assertFalse(result.is_valid)
        self.assertEqual(result.validation_type, ValidationType.RELEVANCE)
        self.assertLess(result.score, 0.5)
    
    def test_security_validation(self):
        """Test security validation"""
        # Test secure code
        result = self.validator.validate_security(self.valid_code)
        self.assertTrue(result.is_valid)
        
        # Test code with security issues
        insecure_code = """
import os
def run_command(cmd):
    os.system(cmd)  # Potential command injection
    
password = "supersecret123"  # Hardcoded credential
"""
        result = self.validator.validate_security(insecure_code)
        self.assertFalse(result.is_valid)
        self.assertGreaterEqual(len(result.issues), 2)  # At least 2 issues
    
    def test_async_validate_response(self):
        """Test the async validate_response method"""
        # Run the async test using asyncio
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            self.validator.validate_response(
                self.relevant_response,
                self.prompt,
                [ValidationType.RELEVANCE, ValidationType.CODE_SYNTAX]
            )
        )
        
        # Check result
        self.assertTrue(isinstance(result, ValidationResult))
        self.assertEqual(result.validation_type, ValidationType.ALL)
        
        # Run with invalid data
        result = loop.run_until_complete(
            self.validator.validate_response(
                self.invalid_code,
                self.prompt,
                [ValidationType.CODE_SYNTAX]
            )
        )
        
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.issues), 0)

if __name__ == "__main__":
    unittest.main()