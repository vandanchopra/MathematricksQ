#!/bin/bash

# Script to install and run the Pandas AI MCP server

# Set the port for the server
PORT=8003

# Set the storage path for data
STORAGE_PATH="./data/pandas-ai"

# Create the storage directory if it doesn't exist
mkdir -p "$STORAGE_PATH"

# Check if pandas-ai-mcp-server is installed
if ! command -v pandas-ai-mcp-server &> /dev/null; then
    echo "Pandas AI MCP server is not installed. Installing..."
    pip install pandas-ai-mcp-server pandas numpy matplotlib seaborn scikit-learn yfinance
fi

# Run the Pandas AI MCP server
echo "Starting Pandas AI MCP server on port $PORT..."
pandas-ai-mcp-server --port $PORT --storage-path "$STORAGE_PATH"
