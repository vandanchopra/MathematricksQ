#!/bin/bash

# Script to install and run the Yahoo Finance MCP server

# Set the port for the server
PORT=8001

# Create the data directory if it doesn't exist
mkdir -p "./data/yahoo-finance"

# Check if yahoo-finance-mcp is installed
if ! command -v yahoo-finance-mcp &> /dev/null; then
    echo "Yahoo Finance MCP server is not installed. Installing..."
    npm install -g yahoo-finance-mcp
fi

# Run the Yahoo Finance MCP server
echo "Starting Yahoo Finance MCP server on port $PORT..."
yahoo-finance-mcp --port $PORT
