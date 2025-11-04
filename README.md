# Transport Scolaire - Microservices Architecture

This project implements a school transportation management system using a microservices architecture with Docker containers.

## Overview

The system consists of two main microservices:

1. **Location Service** - Tracks GPS locations of students and buses using PostgreSQL with PostGIS
2. **Notification Service** - Sends push notifications using Kafka and Firebase

## Architecture Components

- PostgreSQL database with PostGIS extension for geospatial data
- Apache Kafka for message queuing
- Redis for caching (optional)
- FastAPI for microservice APIs
- Firebase Admin SDK for push notifications

## Prerequisites

- Docker and Docker Compose
- Firebase project with service account key

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd transport-scolaire
```

### 2. Configure Firebase (Optional but Required for Notifications)

1. Create a Firebase project at [Firebase Console](https://console.firebase.google.com/)
2. Go to Project Settings > Service Accounts
3. Generate a new private key (JSON format)
4. Rename the file to `firebase-service-account.json`
5. Place it in the `notification_service` directory

If you don't have a real Firebase account, a placeholder file is provided, but notifications won't work.

### 3. Set Up Environment Variables

Environment variables are handled through the docker-compose.yml file. You can customize them there.

### 4. Start the Services

```bash
docker-compose up --build
```

This will start all required services:
- PostgreSQL with PostGIS
- ZooKeeper (for Kafka)
- Kafka
- Location Service (on port 8001)
- Notification Service (on port 8002)
- Redis (optional, on port 6379)

## Service Endpoints

- Location Service: http://localhost:8001
- Notification Service: http://localhost:8002

### Location Service API

- `POST /locations/{entity_type}/{entity_id}` - Create a new location entry
  - `entity_type`: "student" or "bus"
  - `entity_id`: Unique identifier for the student or bus
  - Request body: `{"latitude": 36.7783, "longitude": 3.0652}`

- `GET /locations/{entity_id}` - Get the latest location for an entity

### Notification Service API

- `GET /notifications/history/{user_id}` - Get notification history for a user

## Database Schema

The system uses PostgreSQL with PostGIS extension for geospatial operations:

### Locations Table
- `id`: Primary key
- `entity_id`: Id of the student or bus
- `entity_type`: "student" or "bus"
- `coordinates`: Geometry point (PostGIS)
- `timestamp`: Time when the location was recorded

### Notification History Table
- `id`: Primary key
- `user_id`: Id of the user receiving the notification
- `message`: Notification message content
- `status`: "sent", "failed", or "pending"
- `timestamp`: Time when notification was processed

## Kafka Configuration

The notification service listens on the `eta_notifications` topic. Messages should be in the format:
```json
{
  "student_id": "string",
  "eta": "integer (minutes)"
}
```

## Development

To work on individual services:

### Location Service
```bash
cd location_service
# Make changes to the service
docker build -t transport-scolaire/location-service .
```

### Notification Service
```bash
cd notification_service
# Make changes to the service
docker build -t transport-scolaire/notification-service .
```

## Troubleshooting

1. **Database connection issues**: Ensure PostgreSQL is running and credentials are correct
2. **Kafka connection issues**: Verify Kafka and ZooKeeper are running
3. **Firebase initialization errors**: Check that `firebase-service-account.json` is in the correct location
4. **Docker build failures**: Ensure all required system dependencies are installed

## Production Deployment

For production deployments:
1. Use secure environment variables for sensitive data
2. Implement proper logging and monitoring
3. Set up database backups
4. Use a reverse proxy (like Nginx) for routing
5. Implement proper health checks
6. Set up proper security measures

## Data Storage Strategy

- **PostgreSQL with PostGIS**: Used for location data due to its superior geospatial capabilities required for GPS tracking and route optimization
- **Firebase**: Used for real-time notification delivery and device token management
- **Notification History**: Stored in PostgreSQL for data consistency and analytics

This hybrid approach leverages the strengths of both technologies while meeting all functional requirements for the school transportation management system.