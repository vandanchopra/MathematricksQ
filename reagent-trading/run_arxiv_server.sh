#!/bin/bash

# Script to install and run the ArXiv MCP server

# Set the storage path for papers
STORAGE_PATH="./data/papers"

# Create the storage directory if it doesn't exist
mkdir -p "$STORAGE_PATH"

# Check if arxiv-mcp-server is installed
if ! command -v arxiv-mcp-server &> /dev/null; then
    echo "ArXiv MCP server is not installed. Installing..."
    pip install arxiv-mcp-server
fi

# Run the ArXiv MCP server
echo "Starting ArXiv MCP server..."
arxiv-mcp-server --storage-path "$STORAGE_PATH"
