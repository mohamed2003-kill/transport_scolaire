from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app import schemas, models
from app.database import SessionLocal, engine

# Create the database tables automatically
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Notification Service (Simplified)")

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
@app.post("/notifications/send", response_model=schemas.NotificationResponse)
def send_notification(
    notification: schemas.NotificationCreate, 
    db: Session = Depends(get_db)
):
    db_notification = models.Notification(
        user_id=notification.user_id,
        entity_type=notification.entity_type,
        title=notification.title,
        body=notification.body,
        status="sent" 
    )
    
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)


    return db_notification

@app.get("/notifications/history/{entity_type}/{user_id}", response_model=List[schemas.NotificationResponse])
def get_notification_history(
    entity_type: str, 
    user_id: str, 
    db: Session = Depends(get_db)
):
    notifications = db.query(models.Notification).filter(
        models.Notification.user_id == user_id,
        models.Notification.entity_type == entity_type
    ).order_by(models.Notification.created_at.desc()).all()
    
    return notifications
@app.get("/")
def api_overview():
    return {
        "service": "Notification Microservice",
        "status": "running",
        "description": "Handles sending notifications and retrieving history for users/entities.",
        "endpoints": {
            "send_notification": {
                "method": "POST",
                "path": "/notifications/send",
                "description": "Records and sends a notification.",
                "body_format": {
                    "user_id": "string",
                    "entity_type": "string ('Bus', 'Student', 'Bus')",
                    "title": "string",
                    "body": "string"
                }
            },
            "get_history": {
                "method": "GET",
                "path": "/notifications/history/{entity_type}/{user_id}",
                "description": "Fetches notification history filtered by entity type and user ID."
            }
        },
        "documentation": "/docs"
    }