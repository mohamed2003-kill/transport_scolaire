from sqlalchemy.orm import Session
from app.models import NotificationHistory
from typing import List, Optional


def create_notification_history(db: Session, user_id: str, message: str, status: str):
    # Create a new notification history record
    db_notification = NotificationHistory(
        user_id=user_id,
        message=message,
        status=status
    )
    
    # Add to database session and commit
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    
    return db_notification


def get_notification_history_by_user_id(db: Session, user_id: str):
    # Query for all notification history records for the given user_id
    return db.query(NotificationHistory).filter(
        NotificationHistory.user_id == user_id
    ).order_by(NotificationHistory.timestamp.desc()).all()


def get_notification_by_id(db: Session, notification_id: int):
    return db.query(NotificationHistory).filter(
        NotificationHistory.id == notification_id
    ).first()


def get_all_notifications(db: Session, skip: int = 0, limit: int = 100, status: Optional[str] = None):
    # Query for all notification records with optional status filter
    query = db.query(NotificationHistory).order_by(NotificationHistory.timestamp.desc())
    
    if status:
        query = query.filter(NotificationHistory.status == status)
    
    return query.offset(skip).limit(limit).all()