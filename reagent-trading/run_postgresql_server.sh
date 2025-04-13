#!/bin/bash

# Script to install and run the PostgreSQL MCP server

# Set the port for the server
PORT=8006

# Set the storage path for data
STORAGE_PATH="./data/postgresql"

# Create the storage directory if it doesn't exist
mkdir -p "$STORAGE_PATH"
mkdir -p "$STORAGE_PATH/db"

# Check if postgresql-mcp-server is installed
if ! command -v postgresql-mcp-server &> /dev/null; then
    echo "PostgreSQL MCP server is not installed. Installing..."
    pip install postgresql-mcp-server psycopg2-binary pandas
fi

# Run the PostgreSQL MCP server
echo "Starting PostgreSQL MCP server on port $PORT..."
postgresql-mcp-server --port $PORT --storage-path "$STORAGE_PATH"
