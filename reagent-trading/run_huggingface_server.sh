#!/bin/bash

# Script to install and run the Huggingface MCP server

# Set the port for the server
PORT=8005

# Set the storage path for data
STORAGE_PATH="./data/huggingface"

# Create the storage directory if it doesn't exist
mkdir -p "$STORAGE_PATH"

# Check if huggingface-mcp-server is installed
if ! command -v huggingface-mcp-server &> /dev/null; then
    echo "Huggingface MCP server is not installed. Installing..."
    pip install huggingface-mcp-server transformers torch pandas numpy scikit-learn
fi

# Run the Huggingface MCP server
echo "Starting Huggingface MCP server on port $PORT..."
huggingface-mcp-server --port $PORT --storage-path "$STORAGE_PATH"
