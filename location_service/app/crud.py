from sqlalchemy.orm import Session
from app.models import Location
from geoalchemy2 import WKTElement
from sqlalchemy import desc
from typing import Optional


def create_location(db: Session, entity_id: str, entity_type: str, latitude: float, longitude: float):
    # Convert latitude and longitude to WKT POINT format
    wkt_point = f'POINT({longitude} {latitude})'
    
    # Create a new location record
    db_location = Location(
        entity_id=entity_id,
        entity_type=entity_type,
        coordinates=WKTElement(wkt_point, srid=4326)
    )
    
    # Add to database session and commit
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    
    return db_location


def get_latest_location_by_entity_id(db: Session, entity_id: str):
    # Query for the most recent location record for the given entity_id
    return db.query(Location).filter(Location.entity_id == entity_id).order_by(
        desc(Location.timestamp)
    ).first()


def get_location_by_id(db: Session, location_id: int):
    return db.query(Location).filter(Location.id == location_id).first()


def get_locations_by_entity(db: Session, entity_type: str, entity_id: str, skip: int = 0, limit: int = 100):
    # Query for all location records for the given entity_type and entity_id
    return db.query(Location).filter(
        Location.entity_type == entity_type,
        Location.entity_id == entity_id
    ).order_by(
        Location.timestamp.desc()
    ).offset(skip).limit(limit).all()