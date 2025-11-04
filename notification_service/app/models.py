from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base


class NotificationHistory(Base):
    __tablename__ = "notification_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)  # ID of the user receiving the notification
    message = Column(Text, nullable=False)  # The notification message content
    status = Column(String, nullable=False)  # 'sent', 'failed', 'pending'
    timestamp = Column(DateTime(timezone=True), server_default=func.now())  # Time when notification was sent