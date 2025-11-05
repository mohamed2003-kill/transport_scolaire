from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class LocationBase(BaseModel):
    latitude: float
    longitude: float


class LocationCreate(LocationBase):
    pass


class LocationResponse(BaseModel):
    entity_id: str
    entity_type: str
    latitude: float
    longitude: float
    timestamp: datetime

    class Config:
        from_attributes = True


class EntityLocationResponse(BaseModel):
    entity_id: str
    entity_type: str
    latitude: float
    longitude: float
    timestamp: datetime

    class Config:
        from_attributes = True