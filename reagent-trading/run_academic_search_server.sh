#!/bin/bash

# Script to install and run the Academic Search MCP server

# Set the port for the server
PORT=8002

# Set the storage path for papers
STORAGE_PATH="./data/academic-search"

# Create the storage directory if it doesn't exist
mkdir -p "$STORAGE_PATH"

# Check if academic-search-mcp-server is installed
if ! command -v academic-search-mcp-server &> /dev/null; then
    echo "Academic Search MCP server is not installed. Installing..."
    pip install academic-search-mcp-server
fi

# Run the Academic Search MCP server
echo "Starting Academic Search MCP server on port $PORT..."
academic-search-mcp-server --port $PORT --storage-path "$STORAGE_PATH"
