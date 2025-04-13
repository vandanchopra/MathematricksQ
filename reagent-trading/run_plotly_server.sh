#!/bin/bash

# Script to install and run the Plotly MCP server

# Set the port for the server
PORT=8004

# Set the storage path for data
STORAGE_PATH="./data/plotly"

# Create the storage directory if it doesn't exist
mkdir -p "$STORAGE_PATH"

# Check if plotly-mcp-server is installed
if ! command -v plotly-mcp-server &> /dev/null; then
    echo "Plotly MCP server is not installed. Installing..."
    pip install plotly-mcp-server plotly pandas numpy matplotlib
fi

# Run the Plotly MCP server
echo "Starting Plotly MCP server on port $PORT..."
plotly-mcp-server --port $PORT --storage-path "$STORAGE_PATH"
