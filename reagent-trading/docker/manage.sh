#!/bin/bash

# Script to manage Docker containers for ReAgent

# Function to display help
show_help() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start       Start all containers"
    echo "  stop        Stop all containers"
    echo "  restart     Restart all containers"
    echo "  status      Show status of containers"
    echo "  logs        Show logs from containers"
    echo "  build       Build all containers"
    echo "  clean       Remove all containers and volumes"
    echo "  help        Show this help message"
    echo ""
}

# Function to start containers
start_containers() {
    echo "Starting containers..."
    docker-compose up -d
    echo "Containers started. Web interface available at http://localhost:8080"
    echo "Puppeteer browser available at ws://localhost:3000"
}

# Function to stop containers
stop_containers() {
    echo "Stopping containers..."
    docker-compose down
    echo "Containers stopped."
}

# Function to restart containers
restart_containers() {
    echo "Restarting containers..."
    docker-compose restart
    echo "Containers restarted."
}

# Function to show status
show_status() {
    echo "Container status:"
    docker-compose ps
}

# Function to show logs
show_logs() {
    echo "Container logs:"
    docker-compose logs
}

# Function to build containers
build_containers() {
    echo "Building containers..."
    docker-compose build
    echo "Containers built."
}

# Function to clean up
clean_up() {
    echo "Cleaning up containers and volumes..."
    docker-compose down -v
    echo "Cleanup complete."
}

# Main script logic
case "$1" in
    start)
        start_containers
        ;;
    stop)
        stop_containers
        ;;
    restart)
        restart_containers
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    build)
        build_containers
        ;;
    clean)
        clean_up
        ;;
    help|*)
        show_help
        ;;
esac

exit 0
