import os
import sys
import json
import httpx
import logging
from kafka import KafkaConsumer
from sqlalchemy.orm import Session

# Add the parent directory to the Python path to access the app module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine
from app import models, crud
import firebase_admin
from firebase_admin import credentials, messaging
from typing import Optional


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database initialization will happen in main function to avoid issues on import


def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "./firebase-service-account.json")
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)
    logger.info("Firebase initialized successfully")


def get_db_session():
    """Get a database session"""
    return SessionLocal()


def main():
    """Main function to start the Kafka consumer"""
    logger.info("Starting Kafka consumer...")
    
    # Initialize database
    try:
        models.Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return

    # Initialize Firebase
    try:
        initialize_firebase()
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")
        return

    # Get environment variables
    kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092").split(',')
    topic = os.getenv("KAFKA_NOTIFICATIONS_TOPIC", "eta_notifications")
    student_service_url = os.getenv("STUDENT_SERVICE_URL", "http://student-service:8000")
    auth_service_url = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")

    # Create Kafka consumer
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=kafka_bootstrap_servers,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='notification-group'
    )

    logger.info(f"Connected to Kafka, listening on topic: {topic}")

    # Process messages
    for message in consumer:
        try:
            logger.info(f"Received message: {message.value}")
            
            # Extract student ID from message
            student_id = message.value.get('student_id')
            if not student_id:
                logger.error("No student_id in message")
                continue
                
            # Get database session
            db = get_db_session()
            
            try:
                # Use synchronous httpx to get student parent information
                with httpx.Client() as client:
                    # Get student information to find parent_id
                    student_response = client.get(f"{student_service_url}/students/{student_id}")
                    
                    if student_response.status_code != 200:
                        logger.error(f"Failed to get student info: {student_response.status_code}")
                        # Log failure to notification history
                        crud.create_notification_history(
                            db=db,
                            user_id=student_id,
                            message="Failed to retrieve student information",
                            status="failed"
                        )
                        continue
                        
                    student_data = student_response.json()
                    parent_id = student_data.get('parent_id', student_id)  # Fallback to student_id if no parent_id
                    
                    # Get parent device token
                    token_response = client.get(f"{auth_service_url}/auth/users/{parent_id}/device_token")
                    
                    if token_response.status_code != 200:
                        logger.error(f"Failed to get device token: {token_response.status_code}")
                        # Log failure to notification history
                        crud.create_notification_history(
                            db=db,
                            user_id=parent_id,
                            message="Failed to retrieve device token",
                            status="failed"
                        )
                        continue
                        
                    device_token = token_response.json().get('device_token')
                    
                    if not device_token:
                        logger.error("No device token found")
                        # Log failure to notification history
                        crud.create_notification_history(
                            db=db,
                            user_id=parent_id,
                            message="No device token found",
                            status="failed"
                        )
                        continue

                    # Construct Firebase message
                    notification = messaging.Notification(
                        title="Bus Alert",
                        body=f"Your child's bus will arrive in approximately {message.value.get('eta', '10')} minutes."
                    )
                    
                    message_to_send = messaging.Message(
                        notification=notification,
                        token=device_token,
                    )

                    # Send the message
                    response = messaging.send(message_to_send)
                    
                    logger.info(f"Successfully sent message: {response}")
                    
                    # Log success to notification history
                    crud.create_notification_history(
                        db=db,
                        user_id=parent_id,
                        message=f"Notification sent: {message.value}",
                        status="sent"
                    )
                    
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                
                # Get parent_id for logging purposes (try to extract from message)
                parent_id = message.value.get('parent_id', student_id)
                
                # Log error to notification history
                crud.create_notification_history(
                    db=db,
                    user_id=parent_id,
                    message=f"Error processing notification: {str(e)}",
                    status="failed"
                )
                
            finally:
                # Close database session
                db.close()
                
        except json.JSONDecodeError:
            logger.error("Failed to decode JSON message")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()