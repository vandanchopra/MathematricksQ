#!/bin/bash

# Script to start a web server to view the results

# Set the base directory for the ReAgent Trading System
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="$BASE_DIR/results"

# Check if the results directory exists
if [ ! -d "$RESULTS_DIR" ]; then
    echo "Error: Results directory does not exist"
    exit 1
fi

# Start a simple HTTP server
echo "Starting web server on port 8080..."
echo "Results will be available at: http://localhost:8080/"
echo "Press Ctrl+C to stop the server"

# Start the server
cd "$RESULTS_DIR" && python3 -m http.server 8080
