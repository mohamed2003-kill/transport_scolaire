#!/bin/bash
# Start the API in the background
echo "Starting Notification Service API..."
python -m uvicorn app.api:app --host 0.0.0.0 --port 8000 &

# Wait a bit for the API to start
sleep 5

# Start the Kafka consumer in the foreground
echo "Starting Kafka consumer..."
python worker/consumer.py