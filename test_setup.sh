#!/bin/bash

# Test script to validate the Transport Scolaire Docker setup

echo "Starting Transport Scolaire services..."
echo

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "Error: docker-compose is not installed or not in PATH"
    exit 1
fi

# Check if docker is running
if ! docker info &> /dev/null; then
    echo "Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if required files exist
REQUIRED_FILES=(
    "docker-compose.yml"
    "init-postgis.sql"
    "location_service/Dockerfile"
    "notification_service/Dockerfile"
    "location_service/app/main.py"
    "notification_service/app/api.py"
    "notification_service/worker/consumer.py"
)

echo "Checking required files..."
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "Error: Required file $file is missing"
        exit 1
    fi
done

echo "All required files are present."
echo

# Check if notification_service has firebase config file
if [ ! -f "notification_service/firebase-service-account.json" ]; then
    echo "Warning: notification_service/firebase-service-account.json is missing."
    echo "Firebase notifications will not work without this file."
    echo "See README.md for instructions on how to obtain this file from Firebase Console."
    echo
fi

# Build and start services
echo "Building and starting Docker services..."
echo "Note: This may take a few minutes on first run as images are downloaded and built."
echo

docker-compose up --build -d

if [ $? -ne 0 ]; then
    echo "Error: Failed to start Docker services"
    exit 1
fi

echo
echo "Services started successfully. Waiting for services to be ready..."
sleep 30

# Check service status
echo
echo "Checking service status..."
docker-compose ps

echo
echo "Testing service endpoints..."

# Test Location Service
echo
echo "Testing Location Service (http://localhost:8001/)..."
LOCATION_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/)
if [ $LOCATION_RESPONSE -eq 200 ]; then
    echo "✓ Location Service is running (HTTP $LOCATION_RESPONSE)"
else
    echo "✗ Location Service is not responding (HTTP $LOCATION_RESPONSE)"
fi

# Test Notification Service
echo
echo "Testing Notification Service (http://localhost:8002/)..."
NOTIF_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8002/)
if [ $NOTIF_RESPONSE -eq 200 ]; then
    echo "✓ Notification Service is running (HTTP $NOTIF_RESPONSE)"
else
    echo "✗ Notification Service is not responding (HTTP $NOTIF_RESPONSE)"
fi

echo
echo "Setup validation completed."
echo
echo "To test the services manually:"
echo "1. Location Service: http://localhost:8001/"
echo "2. Notification Service: http://localhost:8002/"
echo
echo "To stop the services, run: docker-compose down"