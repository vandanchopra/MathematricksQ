#!/bin/bash

# Script to run Lean CLI in Docker for the ReAgent Trading System

# Set the base directory for the ReAgent Trading System
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STRATEGIES_DIR="$BASE_DIR/strategies"
DATA_DIR="$BASE_DIR/data"
RESULTS_DIR="$BASE_DIR/results"

# Create necessary directories if they don't exist
mkdir -p "$STRATEGIES_DIR"
mkdir -p "$DATA_DIR"
mkdir -p "$RESULTS_DIR"

# Function to display help
show_help() {
    echo "ReAgent Trading System - Lean CLI Runner"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  create-strategy NAME   Create a new strategy with the given name"
    echo "  backtest STRATEGY      Run a backtest on the specified strategy"
    echo "  list                   List all available strategies"
    echo "  browse                 Start the web browser for market research"
    echo "  help                   Show this help message"
    echo ""
}

# Function to create a strategy
create_strategy() {
    if [ -z "$1" ]; then
        echo "Error: Strategy name is required"
        show_help
        exit 1
    fi

    STRATEGY_NAME="$1"
    STRATEGY_DIR="$STRATEGIES_DIR/$STRATEGY_NAME"

    echo "Creating strategy: $STRATEGY_NAME"

    # Check if strategy already exists
    if [ -d "$STRATEGY_DIR" ]; then
        echo "Error: Strategy '$STRATEGY_NAME' already exists"
        exit 1
    fi

    # Create strategy directory
    mkdir -p "$STRATEGY_DIR"

    # Run Lean CLI to create a project
    lean create-project "$STRATEGY_DIR" -l python

    echo "Strategy created successfully: $STRATEGY_NAME"
    echo "Strategy files are available in: $STRATEGY_DIR"
}

# Function to run a backtest
run_backtest() {
    if [ -z "$1" ]; then
        echo "Error: Strategy name is required"
        show_help
        exit 1
    fi

    STRATEGY_NAME="$1"
    STRATEGY_DIR="$STRATEGIES_DIR/$STRATEGY_NAME"

    # Check if strategy exists
    if [ ! -d "$STRATEGY_DIR" ]; then
        echo "Error: Strategy '$STRATEGY_NAME' does not exist"
        exit 1
    fi

    echo "Running backtest for strategy: $STRATEGY_NAME"

    # Create a Docker container for Lean engine
    docker run --rm \
        -v "$STRATEGY_DIR":/Algorithm \
        -v "$DATA_DIR":/Data \
        -v "$RESULTS_DIR":/Results \
        quantconnect/lean:latest \
        --data-folder=/Data \
        --results-destination-folder=/Results \
        --algorithm-location=/Algorithm/main.py \
        --algorithm-language=Python

    echo "Backtest completed for strategy: $STRATEGY_NAME"
    echo "Results are available in: $RESULTS_DIR"
}

# Function to list all strategies
list_strategies() {
    echo "Available strategies:"
    echo ""

    if [ -z "$(ls -A "$STRATEGIES_DIR")" ]; then
        echo "No strategies found"
    else
        for strategy in "$STRATEGIES_DIR"/*; do
            if [ -d "$strategy" ]; then
                strategy_name=$(basename "$strategy")
                echo "- $strategy_name"
            fi
        done
    fi
}

# Function to start the web browser for market research
start_browser() {
    echo "Starting web browser for market research..."

    # Start the browser container
    docker run -d --rm \
        --name reagent-browser \
        -p 3000:3000 \
        browserless/chrome:latest

    echo "Browser started successfully"
    echo "Browser is available at: http://localhost:3000"
    echo "Press Ctrl+C to stop the browser"

    # Wait for user to press Ctrl+C
    trap "docker stop reagent-browser" INT
    while true; do
        sleep 1
    done
}

# Main script logic
case "$1" in
    create-strategy)
        create_strategy "$2"
        ;;
    backtest)
        run_backtest "$2"
        ;;
    list)
        list_strategies
        ;;
    browse)
        start_browser
        ;;
    help|*)
        show_help
        ;;
esac

exit 0
