# AI Agent Task: Generate Microservices with Kafka and Firebase

## **Objective**

Generate the complete Python code for two distinct microservices using the FastAPI framework: `location_service` and `notification_service`. The notification service must use **Apache Kafka** for message consumption and the official **Firebase Admin SDK** for sending push notifications. The code must be production-ready, containerized, and follow the specified file structure and logic.

---

## **Part 1: Microservice 3 - Location Service**

*(This service is independent of the Kafka/Firebase change and remains the same.)*

### **1.1. Goal**

Create a FastAPI service responsible for ingesting and providing the last known GPS location of entities (students or buses). Use a PostgreSQL database with the PostGIS extension for efficient geospatial queries.

### **1.2. Directory Structure**

location_service/
├── app/
│ ├── init.py
│ ├── main.py
│ ├── models.py
│ ├── crud.py
│ ├── database.py
│ └── schemas.py
├── Dockerfile
├── requirements.txt
└── .env.example

code
Code
download
content_copy
expand_less
### **1.3. File Implementation Details**

#### **`requirements.txt`**

fastapi
uvicorn[standard]
sqlalchemy
psycopg2-binary
geoalchemy2
pydantic[email]
python-dotenv

code
Code
download
content_copy
expand_less
#### **`.env.example`**

DATABASE_URL=postgresql://user:password@db-host:5432/location_db

code
Code
download
content_copy
expand_less
#### **`app/database.py`**
- Configure the SQLAlchemy engine using `DATABASE_URL`.
- Create `SessionLocal` for database sessions and a `Base` declarative class.

#### **`app/models.py`**
- Define a SQLAlchemy model `Location`.
- Columns: `id` (PK), `entity_id` (String, Indexed), `entity_type` (String), `coordinates` (GeoAlchemy2 `Geometry(geometry_type='POINT', srid=4326)`), `timestamp` (DateTime).

#### **`app/schemas.py`**
- Define Pydantic schemas:
    - `LocationCreate`: `latitude: float`, `longitude: float`.
    - `LocationResponse`: `entity_id: str`, `entity_type: str`, `latitude: float`, `longitude: float`, `timestamp: datetime`.

#### **`app/crud.py`**
- Implement functions:
    1.  `create_location(db: Session, ...)`: Converts lat/lon to a WKT POINT string (`'POINT(lon lat)'`), creates a `models.Location` instance, and saves it to the DB.
    2.  `get_latest_location_by_entity_id(db: Session, entity_id: str)`: Queries for the most recent location record for the given `entity_id`.

#### **`app/main.py`**
- Create the FastAPI app.
- Implement endpoints:
    - `POST /locations/{entity_type}/{entity_id}`: Validates `entity_type` ("student" or "bus"), calls `crud.create_location`. Returns 201.
    - `GET /locations/{entity_id}`: Calls `crud.get_latest_location_by_entity_id`, transforms the geometry back to lat/lon, and returns a `LocationResponse`. Raise 404 if not found.

#### **`Dockerfile`**
- Use `python:3.10-slim`.
- Install dependencies from `requirements.txt`.
- Copy the `app` directory.
- Expose port 8000.
- `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]`

---

## **Part 2: Microservice 4 - Notification Service (with Kafka & Firebase Admin)**

### **2.1. Goal**

Create a service with two components:
1.  A background worker that consumes messages from an Apache Kafka topic, calls other services for data, and sends push notifications via the **Firebase Admin SDK**.
2.  A FastAPI API to provide a history of sent notifications.

### **2.2. Directory Structure**

notification_service/
├── app/
│ ├── init.py
│ ├── api.py
│ ├── models.py
│ ├── crud.py
│ ├── database.py
│ └── schemas.py
├── worker/
│ ├── init.py
│ └── consumer.py
├── firebase-service-account.json <-- IMPORTANT: Add this file
├── Dockerfile
├── requirements.txt
└── .env.example

code
Code
download
content_copy
expand_less
### **2.3. File Implementation Details**

#### **`requirements.txt`**

```fastapi
uvicorn[standard]
sqlalchemy
psycopg2-binary
pydantic[email]
python-dotenv
kafka-python
httpx
firebase-admin
.env.example
code
# Database for notification history
download
content_copy
expand_less
DATABASE_URL=postgresql://user:password@db-host:5432/notification_db

# Kafka Connection
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_NOTIFICATIONS_TOPIC=eta_notifications

# External Services URLs
STUDENT_SERVICE_URL=http://student-service:8000
AUTH_SERVICE_URL=http://auth-service:8000

# Firebase Admin SDK
# This file must be present in the root directory.
GOOGLE_APPLICATION_CREDENTIALS=./firebase-service-account.json
firebase-service-account.json

This is a credentials file you must download from your Firebase project settings (Service Accounts -> Generate new private key).

Place this file in the root of the notification_service directory.

app/ directory (api.py, models.py, etc.)

This part remains unchanged from the previous description. Its purpose is solely to serve notification history from a database.

Implement the standard CRUD pattern for a NotificationHistory table (id, user_id, message, status, timestamp).

The main file app/api.py will expose a single endpoint: GET /notifications/history/{user_id}.

worker/consumer.py

Goal: Continuously listen to a Kafka topic and process messages.

Implementation:

Import necessary libraries: os, json, httpx, kafka, firebase_admin.

Load environment variables.

Initialize Firebase Admin:

cred = credentials.Certificate(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))

firebase_admin.initialize_app(cred)

Define the Main Logic:

Create a KafkaConsumer instance.

topic = os.getenv("KAFKA_NOTIFICATIONS_TOPIC")

servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS").split(',')

consumer = KafkaConsumer(topic, bootstrap_servers=servers, value_deserializer=lambda m: json.loads(m.decode('utf-8')))

Start an infinite loop to process messages: for message in consumer:.

Inside the loop:

Extract the student ID from message.value (e.g., student_id = message.value.get('student_id')).

Use a synchronous httpx.Client to perform the following calls inside a try/except block.

GET request to STUDENT_SERVICE_URL/students/{student_id} to get the parent_id.

GET request to AUTH_SERVICE_URL/auth/users/{parent_id}/device_token to get the device registration_token.

If successful:

Construct a firebase_admin.messaging.Message object.

Set the notification property: messaging.Notification(title="Bus Alert", body="Your bus will arrive in approximately 10 minutes.").

Set the token property to the registration_token received.

Send the message: messaging.send(message_to_send).

Log the success to your notification history database.

If any step fails:

Log the error.

Log the failure to your notification history database.

Dockerfile

Use python:3.10-slim.

Install dependencies.

Copy the app directory, the worker directory, and firebase-service-account.json.

Use a startup script (start.sh) to run both processes.

start.sh content:

code
Sh
download
content_copy
expand_less
#!/bin/bash
# Start the API in the background
uvicorn app.api:app --host 0.0.0.0 --port 8000 &

# Start the Kafka consumer in the foreground
echo "Starting Kafka consumer..."
python worker/consumer.py

Make the script executable: RUN chmod +x start.sh.

Set the CMD to ["./start.sh"].