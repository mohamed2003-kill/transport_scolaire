from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app import schemas, crud, models
from app.database import SessionLocal, engine
from typing import List, Optional
import os

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Notification Service", description="Service for managing notifications and history")

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/notifications/history/{user_id}", response_model=List[schemas.NotificationHistoryResponse])
def get_notification_history(user_id: str, db: Session = Depends(get_db)):
    # Get notification history for the given user_id
    notifications = crud.get_notification_history_by_user_id(db=db, user_id=user_id)

    if not notifications:
        # Return empty list if no notifications found
        return []

    return notifications


@app.get("/notifications/history/", response_model=List[schemas.NotificationHistoryResponse])
def get_all_notification_history(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    # Get all notification history with optional filtering
    notifications = crud.get_all_notifications(db=db, skip=skip, limit=limit, status=status)

    return notifications


@app.get("/notifications/history/id/{notification_id}", response_model=schemas.NotificationHistoryResponse)
def get_notification_by_id(notification_id: int, db: Session = Depends(get_db)):
    # Get specific notification by ID
    notification = crud.get_notification_by_id(db=db, notification_id=notification_id)

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    return notification


# Endpoints for notification types
@app.get("/notifications/types", response_model=List[schemas.NotificationTypeResponse])
def get_notification_types(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get all notification types with optional filtering"""
    return crud.get_all_notification_types(db=db, skip=skip, limit=limit, is_active=is_active)


@app.get("/notifications/types/{notification_type_id}", response_model=schemas.NotificationTypeResponse)
def get_notification_type(notification_type_id: int, db: Session = Depends(get_db)):
    """Get a specific notification type by ID"""
    notification_type = crud.get_notification_type_by_id(db=db, notification_type_id=notification_type_id)
    
    if not notification_type:
        raise HTTPException(status_code=404, detail="Notification type not found")
    
    return notification_type


@app.post("/notifications/types", response_model=schemas.NotificationTypeResponse)
def create_notification_type(
    notification_type: schemas.NotificationTypeCreate,
    db: Session = Depends(get_db)
):
    """Create a new notification type"""
    # Check if notification type with this name already exists
    existing_type = crud.get_notification_type_by_name(db=db, name=notification_type.name)
    if existing_type:
        raise HTTPException(status_code=400, detail="Notification type with this name already exists")
    
    return crud.create_notification_type(
        db=db,
        name=notification_type.name,
        description=notification_type.description,
        is_active=notification_type.is_active
    )


@app.put("/notifications/types/{notification_type_id}", response_model=schemas.NotificationTypeResponse)
def update_notification_type(
    notification_type_id: int,
    notification_type: schemas.NotificationTypeUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing notification type"""
    updated_type = crud.update_notification_type(
        db=db,
        notification_type_id=notification_type_id,
        name=notification_type.name,
        description=notification_type.description,
        is_active=notification_type.is_active
    )
    
    if not updated_type:
        raise HTTPException(status_code=404, detail="Notification type not found")
    
    return updated_type


@app.delete("/notifications/types/{notification_type_id}")
def delete_notification_type(notification_type_id: int, db: Session = Depends(get_db)):
    """Delete a notification type"""
    success = crud.delete_notification_type(db=db, notification_type_id=notification_type_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Notification type not found")
    
    return {"message": "Notification type deleted successfully"}


# Endpoints for notification subscriptions
@app.get("/notifications/subscriptions/{user_id}", response_model=List[schemas.NotificationSubscriptionResponse])
def get_user_subscriptions(user_id: str, db: Session = Depends(get_db)):
    """Get all notification subscriptions for a user"""
    return crud.get_user_subscriptions(db=db, user_id=user_id)


@app.get("/notifications/subscription/{user_id}/{notification_type_id}", response_model=schemas.NotificationSubscriptionResponse)
def get_user_subscription(user_id: str, notification_type_id: int, db: Session = Depends(get_db)):
    """Get a specific notification subscription for a user"""
    subscription = crud.get_user_subscription_by_type(db=db, user_id=user_id, notification_type_id=notification_type_id)
    
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    return subscription


@app.post("/notifications/subscribe", response_model=schemas.NotificationSubscriptionResponse)
def subscribe_to_notification(notification_subscription: schemas.NotificationSubscriptionCreate, db: Session = Depends(get_db)):
    """Subscribe a user to a notification type"""
    return crud.subscribe_user_to_notification_type(
        db=db,
        user_id=notification_subscription.user_id,
        notification_type_id=notification_subscription.notification_type_id
    )


@app.post("/notifications/unsubscribe", response_model=schemas.NotificationSubscriptionResponse)
def unsubscribe_from_notification(notification_subscription: schemas.NotificationSubscriptionCreate, db: Session = Depends(get_db)):
    """Unsubscribe a user from a notification type"""
    return crud.unsubscribe_user_from_notification_type(
        db=db,
        user_id=notification_subscription.user_id,
        notification_type_id=notification_subscription.notification_type_id
    )


# Endpoint to send notifications
@app.post("/notifications/send", response_model=schemas.NotificationResponse)
def send_notification(notification_request: schemas.NotificationRequest, db: Session = Depends(get_db)):
    """Send a notification to users"""
    # For now, just store notification in history
    # In a real implementation, this would send to Firebase or another notification service
    notification_ids = []
    
    for user_id in notification_request.user_ids:
        # Check if user is subscribed to this notification type
        subscription = crud.get_user_subscription_by_type(
            db=db,
            user_id=user_id,
            notification_type_id=notification_request.notification_type_id
        )
        
        # If user is subscribed or if we don't have a subscription record (default behavior)
        if not subscription or subscription.is_subscribed:
            # Create notification history record
            history_record = crud.create_notification_history(
                db=db,
                user_id=user_id,
                message=f"{notification_request.title}: {notification_request.body}",
                status="pending"
            )
            notification_ids.append(history_record.id)
        else:
            # User unsubscribed, skip
            continue
    
    return schemas.NotificationResponse(
        success=True,
        message=f"Notification sent to {len(notification_ids)} users",
        notification_ids=notification_ids
    )


@app.get("/")
def read_root():
    return {"service": "Notification Service", "status": "running"}