from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class NotificationCreate(BaseModel):
    user_id: str
    entity_type: str 
    title: str
    body: str

class NotificationResponse(BaseModel):
    id: int
    user_id: str
    entity_type: str
    title: str
    body: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True