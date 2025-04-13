#!/bin/bash

# Script to install and run the Alpha Vantage MCP server

# Check if ALPHA_VANTAGE_API_KEY is set
if [ -z "$ALPHA_VANTAGE_API_KEY" ]; then
    echo "Error: ALPHA_VANTAGE_API_KEY environment variable is not set."
    echo "Please set it by running: export ALPHA_VANTAGE_API_KEY=your_api_key"
    exit 1
fi

# Set the port for the server
PORT=8002

# Set the storage path for data
STORAGE_PATH="./data/alpha-vantage"

# Create the storage directory if it doesn't exist
mkdir -p "$STORAGE_PATH"

# Run the Alpha Vantage MCP server using Docker
echo "Starting Alpha Vantage MCP server on port $PORT..."
docker-compose -f docker/docker-compose.alpha-vantage.yml up -d

echo "Alpha Vantage MCP server is running in the background."
echo "To stop it, run: docker-compose -f docker/docker-compose.alpha-vantage.yml down"
