#!/bin/bash

# Script to run integration tests for the ReAgent trading system

# Set the base directory for the ReAgent Trading System
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TESTS_DIR="$BASE_DIR/tests"

# Check if the tests directory exists
if [ ! -d "$TESTS_DIR" ]; then
    echo "Error: Tests directory does not exist"
    exit 1
fi

# Make sure the integration tests script is executable
chmod +x "$TESTS_DIR/integration_tests.py"

# Install required Python packages
echo "Installing required Python packages..."
pip install requests

# Run the integration tests
echo "Running integration tests..."

# Run the Lean CLI tests
echo "\nRunning Lean CLI integration tests..."
python3 "$TESTS_DIR/test_lean_cli.py" -v

# Run the web browsing tests
echo "\nRunning web browsing tests..."
python3 "$TESTS_DIR/test_web_browsing.py" -v

# Run the ReAgent system tests
echo "\nRunning ReAgent system tests..."
python3 "$TESTS_DIR/test_reagent_system.py" -v

# Run the comprehensive integration tests
echo "\nRunning comprehensive integration tests..."
python3 "$TESTS_DIR/integration_tests.py" -v

# Check the exit code
if [ $? -eq 0 ]; then
    echo "Integration tests passed!"
    exit 0
else
    echo "Integration tests failed!"
    exit 1
fi
