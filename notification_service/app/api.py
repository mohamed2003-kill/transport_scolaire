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


@app.get("/")
def read_root():
    return {"service": "Notification Service", "status": "running"}