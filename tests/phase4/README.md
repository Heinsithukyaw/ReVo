# Phase 4 Testing

This directory contains tests for Phase 4 of the reVoAgent platform: Clean Architecture & Testing.

## Overview

Phase 4 focuses on improving the platform's architecture, error handling, and validation. The tests in this directory validate these improvements and ensure all components work together correctly.

## Tests

### 1. Full Stack Integration Test

The `test_full_stack_fallback.py` script performs a comprehensive test of the entire system:

- Starts the backend and frontend servers
- Tests all API endpoints
- Validates error handling
- Tests LLM fallback mechanism
- Verifies response validation

### Running the Tests

You can run the full test suite using the provided script:

```bash
./run_phase4_tests.sh
```

This script will:
1. Set up the necessary environment
2. Start the required servers
3. Run all Phase 4 tests
4. Generate a detailed test report

### Test Results

Test results are saved to `full_stack_test_report.json` in the project root directory. This file contains:

- Overall test summary
- Individual test results
- Details about any failures
- Performance metrics

## Manual Testing

You can also run individual tests manually:

```bash
# Run the full stack test without starting servers (if they're already running)
python tests/integration/test_full_stack_fallback.py

# Run with server startup
python tests/integration/test_full_stack_fallback.py --start-servers
```

## Troubleshooting

If you encounter issues:

1. Check that the backend and frontend servers are running
2. Verify that all dependencies are installed
3. Check the error logs in the test output
4. Ensure the correct ports are available (12000 for frontend, 12001 for backend)