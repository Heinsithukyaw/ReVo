# LLM Response Validation

This module provides validation utilities for LLM-generated responses, ensuring quality, correctness, and security.

## Features

### 1. Code Syntax Validation

Validates generated code for syntax correctness. For Python code, this uses the `ast` module to check syntax without executing the code.

### 2. Relevance Validation

Checks if the response is relevant to the original prompt by analyzing keyword overlap and content structure.

### 3. Structure Validation

Verifies the structure of responses, such as checking if JSON is valid or if markdown formatting is correct.

### 4. Hallucination Detection

Basic detection of potential hallucinations in responses by looking for uncertainty markers and inconsistencies.

### 5. Security Validation

Identifies potential security issues in generated code, such as:
- Command injection vulnerabilities
- Hardcoded credentials
- Potential SQL injection patterns
- Other common security anti-patterns

## Usage

```python
from src.revoagent.validation.llm_validator import llm_validator, ValidationType

# Validate a response with specific validation types
validation_result = await llm_validator.validate_response(
    response_text,
    original_prompt,
    [ValidationType.CODE_SYNTAX, ValidationType.SECURITY]
)

# Check validation result
if validation_result.is_valid:
    # Response passed validation
    quality_score = validation_result.score  # 0.0-1.0 quality score
else:
    # Response had issues
    issues = validation_result.issues  # List of issues found
```

## Validation Types

The following validation types are available:

- `CODE_SYNTAX`: Checks code for syntax errors
- `RELEVANCE`: Verifies the response is relevant to the prompt
- `STRUCTURE`: Validates response structure (JSON, markdown, etc.)
- `HALLUCINATION`: Attempts to detect hallucinations
- `SECURITY`: Checks for security issues
- `ALL`: Performs all validation types

## Extending

To add new validation types:

1. Add a new value to the `ValidationType` enum
2. Implement a validation method in the `LLMValidator` class
3. Update the `validate_response` method to call your new validation method