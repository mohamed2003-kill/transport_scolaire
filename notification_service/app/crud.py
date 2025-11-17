from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models import NotificationHistory, NotificationType, NotificationSubscription
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


# CRUD operations for notification types
def get_notification_type_by_id(db: Session, notification_type_id: int):
    return db.query(NotificationType).filter(
        NotificationType.id == notification_type_id
    ).first()


def get_notification_type_by_name(db: Session, name: str):
    return db.query(NotificationType).filter(
        NotificationType.name == name
    ).first()


def get_all_notification_types(db: Session, skip: int = 0, limit: int = 100, is_active: Optional[bool] = None):
    query = db.query(NotificationType).order_by(NotificationType.name)

    if is_active is not None:
        query = query.filter(NotificationType.is_active == is_active)

    return query.offset(skip).limit(limit).all()


def create_notification_type(db: Session, name: str, description: str = None, is_active: bool = True):
    db_notification_type = NotificationType(
        name=name,
        description=description,
        is_active=is_active
    )
    db.add(db_notification_type)
    db.commit()
    db.refresh(db_notification_type)
    return db_notification_type


def update_notification_type(db: Session, notification_type_id: int, name: str = None, description: str = None, is_active: bool = None):
    db_notification_type = get_notification_type_by_id(db, notification_type_id)
    if not db_notification_type:
        return None

    if name is not None:
        db_notification_type.name = name
    if description is not None:
        db_notification_type.description = description
    if is_active is not None:
        db_notification_type.is_active = is_active

    db.commit()
    db.refresh(db_notification_type)
    return db_notification_type


def delete_notification_type(db: Session, notification_type_id: int):
    db_notification_type = get_notification_type_by_id(db, notification_type_id)
    if not db_notification_type:
        return False

    db.delete(db_notification_type)
    db.commit()
    return True


# CRUD operations for notification subscriptions
def get_user_subscriptions(db: Session, user_id: str):
    return db.query(NotificationSubscription).filter(
        NotificationSubscription.user_id == user_id
    ).all()


def get_user_subscription_by_type(db: Session, user_id: str, notification_type_id: int):
    return db.query(NotificationSubscription).filter(
        and_(
            NotificationSubscription.user_id == user_id,
            NotificationSubscription.notification_type_id == notification_type_id
        )
    ).first()


def get_users_subscribed_to_type(db: Session, notification_type_id: int):
    return db.query(NotificationSubscription).filter(
        and_(
            NotificationSubscription.notification_type_id == notification_type_id,
            NotificationSubscription.is_subscribed == True
        )
    ).all()


def create_or_update_notification_subscription(db: Session, user_id: str, notification_type_id: int, is_subscribed: bool = True):
    # Check if subscription already exists
    existing_subscription = get_user_subscription_by_type(db, user_id, notification_type_id)
    
    if existing_subscription:
        # Update existing subscription
        existing_subscription.is_subscribed = is_subscribed
        db.commit()
        db.refresh(existing_subscription)
        return existing_subscription
    else:
        # Create new subscription
        db_subscription = NotificationSubscription(
            user_id=user_id,
            notification_type_id=notification_type_id,
            is_subscribed=is_subscribed
        )
        db.add(db_subscription)
        db.commit()
        db.refresh(db_subscription)
        return db_subscription


def subscribe_user_to_notification_type(db: Session, user_id: str, notification_type_id: int):
    return create_or_update_notification_subscription(db, user_id, notification_type_id, is_subscribed=True)


def unsubscribe_user_from_notification_type(db: Session, user_id: str, notification_type_id: int):
    return create_or_update_notification_subscription(db, user_id, notification_type_id, is_subscribed=False)