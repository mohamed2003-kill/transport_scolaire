from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database import Base
from geoalchemy2 import Geometry
from sqlalchemy import Index


class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(String, index=True, nullable=False)  # ID of the student or bus
    entity_type = Column(String, nullable=False)  # 'student' or 'bus'
    coordinates = Column(Geometry(geometry_type='POINT', srid=4326), nullable=False)  # GPS coordinates
    timestamp = Column(DateTime(timezone=True), server_default=func.now())  # Time when location was recorded


# Create index on entity_id for faster queries
Index('idx_locations_entity_id', Location.entity_id)