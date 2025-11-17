from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class NotificationHistoryBase(BaseModel):
    user_id: str
    message: str
    status: str


class NotificationHistoryCreate(NotificationHistoryBase):
    pass


class NotificationHistoryResponse(BaseModel):
    id: int
    user_id: str
    message: str
    status: str
    timestamp: datetime

    class Config:
        from_attributes = True


class NotificationTypeBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True


class NotificationTypeCreate(NotificationTypeBase):
    pass


class NotificationTypeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class NotificationTypeResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationSubscriptionBase(BaseModel):
    user_id: str
    notification_type_id: int
    is_subscribed: bool = True


class NotificationSubscriptionCreate(NotificationSubscriptionBase):
    pass


class NotificationSubscriptionUpdate(BaseModel):
    is_subscribed: Optional[bool] = None


class NotificationSubscriptionResponse(BaseModel):
    id: int
    user_id: str
    notification_type_id: int
    is_subscribed: bool
    created_at: datetime
    updated_at: datetime

    # Include the notification type details
    notification_type: Optional[NotificationTypeResponse] = None

    class Config:
        from_attributes = True


class NotificationRequest(BaseModel):
    user_ids: list[str]  # List of user IDs to send notification to
    notification_type_id: int
    title: str
    body: str
    data: Optional[dict] = None  # Additional data to include in notification


class NotificationResponse(BaseModel):
    success: bool
    message: str
    notification_ids: list[int]  # IDs of created notification history records