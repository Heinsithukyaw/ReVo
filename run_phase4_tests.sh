#!/bin/bash
# Run Phase 4 tests (unit tests and integration tests)

echo "Running Phase 4 tests..."
echo "======================================"

# Change to project directory
cd "$(dirname "$0")"

# Ensure Python environment is available
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
else
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    else
        source venv/bin/activate
    fi
fi

# Run unit tests first
echo "Running unit tests..."
echo "--------------------"
python -m unittest discover -s tests/unit -p "test_*.py"

# Store unit test result
UNIT_TEST_RESULT=$?

# Run the full stack integration test
echo ""
echo "Running full stack integration test..."
echo "--------------------"
python tests/integration/test_full_stack_fallback.py --start-servers

# Store integration test result
INTEGRATION_TEST_RESULT=$?

echo "======================================"
echo "Test Results:"
echo "--------------------"

if [ $UNIT_TEST_RESULT -eq 0 ]; then
    echo "✅ Unit tests: PASSED"
else
    echo "❌ Unit tests: FAILED"
fi

if [ $INTEGRATION_TEST_RESULT -eq 0 ]; then
    echo "✅ Integration tests: PASSED"
else
    echo "❌ Integration tests: FAILED"
fi

if [ $UNIT_TEST_RESULT -eq 0 ] && [ $INTEGRATION_TEST_RESULT -eq 0 ]; then
    echo "--------------------"
    echo "✅ All tests passed successfully!"
else
    echo "--------------------"
    echo "❌ Some tests failed. See output above for details."
fi

echo "======================================"
echo "Integration test report: full_stack_test_report.json"