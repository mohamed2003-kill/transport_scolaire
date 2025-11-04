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