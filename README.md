# Transport Scolaire - Microservices Architecture

This project implements a school transportation management system using a microservices architecture with Docker containers.

## Overview

The system consists of the following microservices:

1. **Location Service** - Tracks GPS locations of students and buses using PostgreSQL with PostGIS
2. **Notification Service** - Sends push notifications using Kafka and Firebase
3. **Student Service** - Manages student profiles and parent associations (external service)
4. **Auth Service** - Handles user authentication and device token management (external service)

## Architecture Components

- PostgreSQL database with PostGIS extension for geospatial data
- Apache Kafka for message queuing
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


## Service Endpoints

- Location Service: http://localhost:8001
- Notification Service: http://localhost:8002

### Location Service API

- `POST /locations/{entity_type}/{entity_id}` - Create a new location entry
  - `entity_type`: "student" or "bus"  
  - `entity_id`: Unique identifier for the student or bus
  - Request body: `{"latitude": 36.7783, "longitude": 3.0652}`
  - Example: `POST /locations/student/12345`
  - Response: `{"message": "Location for student 12345 created successfully"}`

- `GET /locations/{entity_id}` - Get the latest location for an entity
  - Response: `{"entity_id": "12345", "entity_type": "student", "latitude": 36.7783, "longitude": 3.0652, "timestamp": "2023-01-01T10:00:00Z"}`

- `GET /locations/` - Get multiple locations with optional filtering
  - Query parameters: `entity_id`, `entity_type`, `skip` (default: 0), `limit` (default: 100)
  - Example: `/locations/?entity_type=bus&limit=50`
  - Response: Array of location objects

- `GET /locations/entity/{entity_type}/{entity_id}` - Get all locations for a specific entity
  - Query parameters: `skip` (default: 0), `limit` (default: 100)
  - Response: Array of location objects for the specified entity

- `GET /entities/locations` - Get the latest location for all entities
  - Query parameter: `entity_type` (optional filter)
  - Response: Array of entity location objects

### Notification Service API

#### Notification History Endpoints

- `GET /notifications/history/{user_id}` - Get notification history for a specific user
  - Response: Array of notification history objects
  - Example response:
    ```json
    [
      {
        "id": 1,
        "user_id": "user123",
        "message": "Bus arrival: 5 minutes",
        "status": "sent",
        "timestamp": "2023-01-01T10:00:00Z"
      }
    ]
    ```

- `GET /notifications/history/` - Get all notification history with optional filtering
  - Query parameters: `skip`, `limit`, `status` (optional filter)
  - Response: Array of notification history objects

- `GET /notifications/history/id/{notification_id}` - Get a specific notification by ID
  - Response: Single notification history object

#### Notification Types Management

- `GET /notifications/types` - Get all notification types with optional filtering
  - Query parameters: `skip`, `limit`, `is_active` (optional filter)
  - Response: Array of notification type objects
  - Example response:
    ```json
    [
      {
        "id": 1,
        "name": "eta_update",
        "description": "Estimated time of arrival updates",
        "is_active": true,
        "created_at": "2023-01-01T10:00:00Z",
        "updated_at": "2023-01-01T10:00:00Z"
      }
    ]
    ```

- `GET /notifications/types/{notification_type_id}` - Get a specific notification type by ID
  - Response: Single notification type object

- `POST /notifications/types` - Create a new notification type
  - Request body: `{"name": "bus_arrived", "description": "Bus arrival notifications", "is_active": true}`
  - Response: Created notification type object

- `PUT /notifications/types/{notification_type_id}` - Update an existing notification type
  - Request body: `{"name": "updated_name", "description": "Updated description", "is_active": true}`
  - Response: Updated notification type object

- `DELETE /notifications/types/{notification_type_id}` - Delete a notification type

#### Notification Subscription Management

- `GET /notifications/subscriptions/{user_id}` - Get all notification subscriptions for a user
  - Response: Array of subscription objects
  - Example response:
    ```json
    [
      {
        "id": 1,
        "user_id": "user123",
        "notification_type_id": 1,
        "is_subscribed": true,
        "created_at": "2023-01-01T10:00:00Z",
        "updated_at": "2023-01-01T10:00:00Z",
        "notification_type": {
          "id": 1,
          "name": "eta_update",
          "description": "Estimated time of arrival updates",
          "is_active": true,
          "created_at": "2023-01-01T10:00:00Z",
          "updated_at": "2023-01-01T10:00:00Z"
        }
      }
    ]
    ```

- `GET /notifications/subscription/{user_id}/{notification_type_id}` - Get a specific subscription
  - Response: Single subscription object

- `POST /notifications/subscribe` - Subscribe a user to a notification type
  - Request body: `{"user_id": "user123", "notification_type_id": 1}`
  - Response: Created/updated subscription object

- `POST /notifications/unsubscribe` - Unsubscribe a user from a notification type
  - Request body: `{"user_id": "user123", "notification_type_id": 1}`
  - Response: Updated subscription object

#### Sending Notifications

- `POST /notifications/send` - Send a notification to one or more users via HTTP API
  - Request body: 
    ```json
    {
      "user_ids": ["user123", "user456"],
      "notification_type_id": 1,
      "title": "Bus Notification",
      "body": "Your bus is arriving soon",
      "data": {"eta": 5, "bus_id": "B001"}
    }
    ```
  - Response: 
    ```json
    {
      "success": true,
      "message": "Notification sent to 2 users",
      "notification_ids": [1, 2]
    }
    ```

## Other Microservices Integration

### Student Service (External Service)
The Student Service is responsible for managing student profiles and parent associations. The Location Service and Notification Service interact with this service to retrieve parent information when sending notifications.

- **Endpoint**: `http://student-service:8000/students/{student_id}`
- **Purpose**: Retrieve student information including parent_id to determine notification recipients
- **Expected Response**:
  ```json
  {
    "id": "student123",
    "name": "John Doe",
    "parent_id": "parent123",
    "bus_id": "bus001"
  }
  ```

### Auth Service (External Service)
The Auth Service manages user authentication and device token management. The Notification Service calls this service to retrieve device tokens for push notifications.

- **Endpoint**: `http://auth-service:8000/auth/users/{user_id}/device_token`
- **Purpose**: Retrieve device token for a user to send push notifications
- **Expected Response**:
  ```json
  {
    "user_id": "user123",
    "device_token": "firebase_device_token_here",
    "platform": "android|ios"
  }
  ```

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
5. **External service connection issues**: Verify that Student Service and Auth Service are running and accessible

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