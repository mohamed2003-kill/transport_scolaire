import os
import sys
import json
import httpx
import logging
from kafka import KafkaConsumer
from sqlalchemy.orm import Session


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine
from app import models, crud
import firebase_admin
from firebase_admin import credentials, messaging
from typing import Optional



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)




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


def send_firebase_notification(device_token: str, title: str, body: str, data: Optional[dict] = None):
    """Send a notification via Firebase"""
    try:
        notification = messaging.Notification(
            title=title,
            body=body
        )

        message = messaging.Message(
            notification=notification,
            data=data or {},
            token=device_token,
        )

        response = messaging.send(message)
        logger.info(f"Successfully sent Firebase message: {response}")
        return True
    except Exception as e:
        logger.error(f"Error sending Firebase notification: {e}")
        return False


def process_notification_message(message_value: dict, db: Session):
    """Process a notification message from Kafka"""
    logger.info(f"Processing message: {message_value}")
    
    
    notification_type_name = message_value.get('notification_type', 'eta_update')
    
    
    notification_type = crud.get_notification_type_by_name(db=db, name=notification_type_name)
    if not notification_type or not notification_type.is_active:
        logger.error(f"Notification type '{notification_type_name}' not found or inactive")
        
        
        notification_type_id = 1  
    else:
        notification_type_id = notification_type.id
    
    
    user_id = message_value.get('user_id') or message_value.get('student_id') or message_value.get('parent_id')
    if not user_id:
        logger.error("No user identifier found in message")
        return False
    
    
    student_service_url = os.getenv("STUDENT_SERVICE_URL", "http://student-service:8000")
    auth_service_url = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")
    
    
    try:
        
        with httpx.Client() as client:
            
            parent_id = user_id
            if message_value.get('student_id'):
                
                student_response = client.get(f"{student_service_url}/students/{message_value['student_id']}")
                
                if student_response.status_code == 200:
                    student_data = student_response.json()
                    parent_id = student_data.get('parent_id', user_id)  
                else:
                    logger.warning(f"Could not get student info: {student_response.status_code}")
            
            
            token_response = client.get(f"{auth_service_url}/auth/users/{parent_id}/device_token")
            
            if token_response.status_code != 200:
                logger.error(f"Failed to get device token for user {parent_id}: {token_response.status_code}")
                
                crud.create_notification_history(
                    db=db,
                    user_id=parent_id,
                    message="Failed to retrieve device token",
                    status="failed"
                )
                return False
            
            device_token = token_response.json().get('device_token')
            
            if not device_token:
                logger.error(f"No device token found for user {parent_id}")
                
                crud.create_notification_history(
                    db=db,
                    user_id=parent_id,
                    message="No device token found",
                    status="failed"
                )
                return False
            
            
            subscription = crud.get_user_subscription_by_type(
                db=db,
                user_id=parent_id,
                notification_type_id=notification_type_id
            )
            
            
            if subscription and not subscription.is_subscribed:
                logger.info(f"User {parent_id} unsubscribed from notification type {notification_type_name}, skipping")
                
                crud.create_notification_history(
                    db=db,
                    user_id=parent_id,
                    message=f"Notification not sent: user unsubscribed from {notification_type_name}",
                    status="skipped"
                )
                return True  
            
            
            title = message_value.get('title', 'Bus Alert')
            body = message_value.get('body', 'You have received a notification.')
            data = message_value.get('data', {})
            
            
            if notification_type_name == 'eta_update':
                eta = message_value.get('eta', '10')
                title = "Bus Arrival Update"
                body = f"Your child's bus will arrive in approximately {eta} minutes."
            
            
            success = send_firebase_notification(device_token, title, body, data)
            
            
            status = "sent" if success else "failed"
            crud.create_notification_history(
                db=db,
                user_id=parent_id,
                message=f"Notification {status}: {title} - {body}",
                status=status
            )
            
            return success
            
    except Exception as e:
        logger.error(f"Error processing notification message: {e}")
        
        
        crud.create_notification_history(
            db=db,
            user_id=user_id,
            message=f"Error processing notification: {str(e)}",
            status="failed"
        )
        return False


def main():
    """Main function to start the Kafka consumer"""
    logger.info("Starting Kafka consumer...")

    
    try:
        models.Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return

    
    try:
        initialize_firebase()
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")
        return

    
    kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092").split(',')
    topic = os.getenv("KAFKA_NOTIFICATIONS_TOPIC", "eta_notifications")
    
    topics = [topic] + os.getenv("KAFKA_ADDITIONAL_TOPICS", "").split(",") if os.getenv("KAFKA_ADDITIONAL_TOPICS") else [topic]
    topics = [t.strip() for t in topics if t.strip()]  

    
    consumer = KafkaConsumer(
        *topics,
        bootstrap_servers=kafka_bootstrap_servers,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='notification-group'
    )

    logger.info(f"Connected to Kafka, listening on topics: {topics}")

    
    for message in consumer:
        try:
            logger.info(f"Received message: {message.value}")

            
            db = get_db_session()

            try:
                
                success = process_notification_message(message.value, db)
                
                if success:
                    logger.info("Message processed successfully")
                else:
                    logger.error("Failed to process message")
                    
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")

                
                user_id = message.value.get('user_id', message.value.get('student_id', 'unknown'))

                
                crud.create_notification_history(
                    db=db,
                    user_id=user_id,
                    message=f"Error processing notification: {str(e)}",
                    status="failed"
                )

            finally:
                
                db.close()

        except json.JSONDecodeError:
            logger.error("Failed to decode JSON message")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()