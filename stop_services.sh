#!/bin/bash

# Script to properly stop Transport Scolaire Docker services

echo "Stopping Transport Scolaire services..."

# Stop all services gracefully
docker-compose stop

echo "Waiting for services to stop..."
sleep 5

# Check if any services are still running
RUNNING_SERVICES=$(docker-compose ps -q)

if [ -n "$RUNNING_SERVICES" ]; then
    echo "Some services didn't stop gracefully. Force stopping..."
    docker-compose kill
    
    # Remove the stopped containers
    docker-compose rm -f
else
    echo "All services stopped gracefully."
fi

# Optional: Clean up unused resources
echo "Cleaning up unused Docker resources..."
docker system prune -f

echo "Transport Scolaire services stopped successfully."