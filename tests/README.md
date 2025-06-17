# Tests Directory

This directory contains the test suite for reVoAgent, organized by test type for better maintainability and execution speed.

## Directory Structure

```
tests/
├── unit/          # Fast, isolated unit tests
├── integration/   # Cross-component integration tests  
├── e2e/          # End-to-end system tests
└── fixtures/     # Test data and mock objects
```

## Test Categories

### Unit Tests (`unit/`)
- **Purpose**: Test individual functions and classes in isolation
- **Speed**: Very fast (< 1 second each)
- **Scope**: Single function or class
- **Dependencies**: Minimal, use mocks for external dependencies
- **Run**: `pytest tests/unit/`

### Integration Tests (`integration/`)
- **Purpose**: Test component interactions and API integrations
- **Speed**: Moderate (1-10 seconds each)
- **Scope**: Multiple components working together
- **Dependencies**: May use real services in test mode
- **Run**: `pytest tests/integration/`

### End-to-End Tests (`e2e/`)
- **Purpose**: Test complete user workflows
- **Speed**: Slow (10+ seconds each)
- **Scope**: Full system functionality
- **Dependencies**: Real or staging environment
- **Run**: `pytest tests/e2e/`

### Fixtures (`fixtures/`)
- **Purpose**: Shared test data, mock objects, and test utilities
- **Contents**: JSON files, sample data, mock classes
- **Usage**: Imported by test files across all categories

## Running Tests

```bash
# Run all tests
pytest tests/

# Run by category
pytest tests/unit/         # Fast feedback during development
pytest tests/integration/  # Before commits
pytest tests/e2e/          # Before releases

# Run with coverage
pytest tests/ --cov=revoagent --cov-report=html

# Run specific test file
pytest tests/unit/test_core.py

# Run tests matching pattern
pytest tests/ -k "test_agent"
```

## Test Guidelines

1. **Unit tests** should be fast and isolated
2. **Integration tests** should test realistic scenarios  
3. **E2E tests** should cover critical user journeys
4. Use descriptive test names: `test_agent_generates_code_when_given_valid_prompt`
5. Keep test files near their corresponding source files in naming
6. Use fixtures for common test data
7. Mock external dependencies in unit tests
8. Test both success and failure scenarios

## Migration Status

✅ Directory structure created  
⏳ Moving existing integration tests from root  
⏳ Creating unit test examples  
⏳ Setting up fixtures and utilities  

The existing test files from the repository root will be moved here and categorized appropriately.
