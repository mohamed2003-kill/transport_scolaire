from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class NotificationHistory(Base):
    __tablename__ = "notification_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)  # ID of the user receiving the notification
    message = Column(Text, nullable=False)  # The notification message content
    status = Column(String, nullable=False)  # 'sent', 'failed', 'pending'
    timestamp = Column(DateTime(timezone=True), server_default=func.now())  # Time when notification was sent


class NotificationType(Base):
    __tablename__ = "notification_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)  # Name of the notification type (e.g., "eta_update", "bus_arrived")
    description = Column(Text)  # Description of the notification type
    is_active = Column(Boolean, default=True)  # Whether this notification type is active
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class NotificationSubscription(Base):
    __tablename__ = "notification_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)  # ID of the user
    notification_type_id = Column(Integer, ForeignKey("notification_types.id"), nullable=False)  # Type of notification
    is_subscribed = Column(Boolean, default=True)  # Whether the user is subscribed to this notification type
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship
    notification_type = relationship("NotificationType", back_populates="subscriptions")


# Add back_populates to NotificationType
NotificationType.subscriptions = relationship("NotificationSubscription", back_populates="notification_type")