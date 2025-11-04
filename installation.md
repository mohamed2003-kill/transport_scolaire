# Installation Instructions for Transport Scolaire Microservices

This document provides comprehensive instructions for installing and setting up the Transport Scolaire microservices application.

## System Requirements

- Python 3.10 or higher
- Docker and Docker Compose
- PostgreSQL with PostGIS extension
- Apache Kafka
- Firebase project setup
- Google Cloud Service Account Key

## Microservice 1: Location Service (Microservice 3)

### Description
The Location Service is responsible for:
- Ingesting and providing the last known GPS location of entities (students or buses)
- Using PostgreSQL database with PostGIS extension for efficient geospatial queries

### Dependencies Installation

#### 1. Using pip (Python Package Manager)

Create a virtual environment first:
```bash
python -m venv location_service_env
source location_service_env/bin/activate  # On Windows: location_service_env\Scripts\activate
```

Install required packages:
```bash
pip install fastapi
pip install uvicorn[standard]
pip install sqlalchemy
pip install psycopg2-binary
pip install geoalchemy2
pip install pydantic[email]
pip install python-dotenv
```

#### 2. Using requirements.txt

Create a file named `requirements.txt` in the location_service directory with:
```
fastapi
uvicorn[standard]
sqlalchemy
psycopg2-binary
geoalchemy2
pydantic[email]
python-dotenv
```

Then install:
```bash
pip install -r requirements.txt
```

#### 3. Environment Configuration

Create an `.env` file in the location_service directory:
```
DATABASE_URL=postgresql://user:password@localhost:5432/location_db
```

### Database Setup (PostgreSQL with PostGIS)

1. Install PostgreSQL with PostGIS extension:
   - For Ubuntu/Debian: `sudo apt-get install postgresql postgis`
   - For CentOS/RHEL: `sudo yum install postgresql postgis`
   - For macOS: `brew install postgresql postgis`

2. Create and configure database:
   ```sql
   CREATE DATABASE location_db;
   \c location_db;
   CREATE EXTENSION IF NOT EXISTS postgis;
   ```

## Microservice 2: Notification Service (Microservice 4)

### Description
The Notification Service has two components:
1. A background worker that consumes messages from an Apache Kafka topic
2. A FastAPI API to provide a history of sent notifications
3. Uses Firebase Admin SDK for sending push notifications

### Dependencies Installation

#### 1. Using pip (Python Package Manager)

Create a virtual environment first:
```bash
python -m venv notification_service_env
source notification_service_env/bin/activate  # On Windows: notification_service_env\Scripts\activate
```

Install required packages:
```bash
pip install fastapi
pip install uvicorn[standard]
pip install sqlalchemy
pip install psycopg2-binary
pip install pydantic[email]
pip install python-dotenv
pip install kafka-python
pip install httpx
pip install firebase-admin
```

#### 2. Using requirements.txt

Create a file named `requirements.txt` in the notification_service directory with:
```
fastapi
uvicorn[standard]
sqlalchemy
psycopg2-binary
pydantic[email]
python-dotenv
kafka-python
httpx
firebase-admin
```

Then install:
```bash
pip install -r requirements.txt
```

#### 3. Environment Configuration

Create an `.env` file in the notification_service directory:
```
# Database for notification history
DATABASE_URL=postgresql://user:password@localhost:5432/notification_db

# Kafka Connection
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_NOTIFICATIONS_TOPIC=eta_notifications

# External Services URLs
STUDENT_SERVICE_URL=http://student-service:8000
AUTH_SERVICE_URL=http://auth-service:8000

# Firebase Admin SDK
GOOGLE_APPLICATION_CREDENTIALS=./firebase-service-account.json
```

### Kafka Setup

1. Download Apache Kafka from https://kafka.apache.org/downloads
2. Extract and run:
   ```bash
   # Start ZooKeeper (required by Kafka)
   bin/zookeeper-server-start.sh config/zookeeper.properties
   
   # Start Kafka Server
   bin/kafka-server-start.sh config/server.properties
   ```
3. Create the notifications topic:
   ```bash
   bin/kafka-topics.sh --create --topic eta_notifications --bootstrap-server localhost:9092
   ```

### Firebase Setup

1. Go to Firebase Console (https://console.firebase.google.com/)
2. Create a new project or select an existing one
3. Go to Project Settings > Service Accounts
4. Click "Generate New Private Key" and download the JSON file
5. Rename the file to `firebase-service-account.json` and place it in the root directory of notification_service

## Docker Setup (Optional but Recommended)

### For Location Service

Create a Dockerfile in the location_service directory:
```
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### For Notification Service

Create a Dockerfile in the notification_service directory:
```
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x start.sh

EXPOSE 8000

CMD ["./start.sh"]
```

Create a start.sh script in the notification_service directory:
```bash
#!/bin/bash
# Start the API in the background
uvicorn app.api:app --host 0.0.0.0 --port 8000 &

# Start the Kafka consumer in the foreground
echo "Starting Kafka consumer..."
python worker/consumer.py
```

Make the script executable:
```bash
chmod +x start.sh
```

## Docker Compose Setup (For Multiple Services)

Create a docker-compose.yml file to run all services together:

```yaml
version: '3.8'

services:
  zookeeper:
    image: confluentinc/cp-zookeeper:latest
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000

  kafka:
    image: confluentinc/cp-kafka:latest
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1

  postgres-location:
    image: postgis/postgis:13-3.1
    environment:
      POSTGRES_DB: location_db
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  location-service:
    build: ./location_service
    ports:
      - "8001:8000"
    depends_on:
      - postgres-location
    environment:
      - DATABASE_URL=postgresql://user:password@postgres-location:5432/location_db

  notification-service:
    build: ./notification_service
    ports:
      - "8002:8000"
    depends_on:
      - kafka
      - postgres-location
    environment:
      - DATABASE_URL=postgresql://user:password@postgres-location:5432/notification_db
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
      - KAFKA_NOTIFICATIONS_TOPIC=eta_notifications
      - STUDENT_SERVICE_URL=http://student-service:8000
      - AUTH_SERVICE_URL=http://auth-service:8000

volumes:
  postgres_data:
```

## Running the Services

### Without Docker:
1. Start the database services (PostgreSQL)
2. Start Kafka
3. Activate and run the location service:
   ```bash
   cd location_service
   source location_service_env/bin/activate
   uvicorn app.main:app --reload
   ```
4. Activate and run the notification service:
   ```bash
   cd notification_service
   source notification_service_env/bin/activate
   # Run API in one terminal
   uvicorn app.api:app --reload
   # Run consumer in another terminal
   python worker/consumer.py
   ```

### With Docker:
```bash
docker-compose up --build
```

## Testing the Installation

### Location Service API Test:
```bash
# Add a location for a student
curl -X POST http://localhost:8001/locations/student/123 -H "Content-Type: application/json" -d '{"latitude": 36.7783, "longitude": 3.0652}'

# Get the latest location for an entity
curl -X GET http://localhost:8001/locations/123
```

### Notification Service API Test:
```bash
# Get notification history
curl -X GET http://localhost:8002/notifications/history/123
```

## Troubleshooting

1. **Database connection issues**: Ensure PostgreSQL is running and credentials in the .env file are correct
2. **Kafka connection issues**: Ensure Kafka is running and the topic exists
3. **Firebase authentication issues**: Ensure the service account file is correctly placed and configured
4. **Port conflicts**: Ensure required ports (8000, 8001, 5432, 9092) are not in use by other applications