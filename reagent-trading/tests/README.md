# ReAgent Trading System Integration Tests

This directory contains integration tests for the ReAgent trading system. These tests verify that all components of the system work together correctly.

## Test Files

- `integration_tests.py`: Comprehensive integration tests for the entire system
- `test_lean_cli.py`: Tests for the Lean CLI integration
- `test_web_browsing.py`: Tests for the web browsing capabilities
- `test_reagent_system.py`: Tests for the full ReAgent system

## Running the Tests

To run all the integration tests, use the `run_integration_tests.sh` script in the root directory:

```bash
./run_integration_tests.sh
```

To run a specific test file, use Python directly:

```bash
python3 tests/integration_tests.py -v
python3 tests/test_lean_cli.py -v
python3 tests/test_web_browsing.py -v
python3 tests/test_reagent_system.py -v
```

## Test Requirements

The integration tests require the following:

1. Docker and Docker Compose installed
2. Node.js and npm installed
3. Python 3 installed
4. The `requests` Python package installed

## Test Environment

The tests will:

1. Start Docker containers for Lean CLI and web browsing
2. Create test strategies
3. Run backtests on the test strategies
4. Verify that the results are correct
5. Clean up the test environment

## Adding New Tests

To add new tests, create a new test file in this directory and add it to the `run_integration_tests.sh` script.

## Troubleshooting

If the tests fail, check the following:

1. Make sure Docker is running
2. Make sure the Docker containers are built correctly
3. Make sure the TypeScript code is built correctly
4. Check the logs for any errors
