from fastapi import FastAPI, HTTPException, Depends, Path
from sqlalchemy.orm import Session
from app import schemas, crud, models
from app.database import SessionLocal, engine
from typing import List, Optional
import os

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Location Service", description="Service for tracking GPS locations of students and buses")

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/locations/{entity_type}/{entity_id}", status_code=201)
def create_location(
    entity_type: str = Path(..., regex="^(student|bus)$"),
    entity_id: str = Path(...),
    location: schemas.LocationCreate = Depends(),
    db: Session = Depends(get_db)
):
    # Validate entity_type
    if entity_type not in ["student", "bus"]:
        raise HTTPException(status_code=400, detail="entity_type must be 'student' or 'bus'")
    
    # Create the location in the database
    db_location = crud.create_location(
        db=db,
        entity_id=entity_id,
        entity_type=entity_type,
        latitude=location.latitude,
        longitude=location.longitude
    )
    
    return {"message": f"Location for {entity_type} {entity_id} created successfully"}


@app.get("/locations/{entity_id}", response_model=schemas.LocationResponse)
def get_latest_location_by_entity_id(entity_id: str, db: Session = Depends(get_db)):
    # Get the latest location for the given entity_id
    db_location = crud.get_latest_location_by_entity_id(db=db, entity_id=entity_id)
    
    if not db_location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    # Extract latitude and longitude from the geometry
    # Convert the geometry to text and parse coordinates
    # Note: This is a simplified way to extract coordinates from PostGIS geometry
    # In a real application, you might want to use ST_X and ST_Y functions
    
    # Execute a raw SQL query to extract coordinates
    result = db.execute(
        f"SELECT ST_X(coordinates::geometry) as longitude, ST_Y(coordinates::geometry) as latitude FROM locations WHERE id = {db_location.id}"
    ).first()
    
    if result:
        longitude, latitude = result
    else:
        # Fallback coordinates if extraction fails
        longitude, latitude = 0.0, 0.0
    
    # Create response object
    response = schemas.LocationResponse(
        entity_id=db_location.entity_id,
        entity_type=db_location.entity_type,
        latitude=latitude,
        longitude=longitude,
        timestamp=db_location.timestamp
    )
    
    return response


@app.get("/locations/", response_model=List[schemas.LocationResponse])
def get_locations(
    entity_id: Optional[str] = None,
    entity_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    # Get locations with optional filtering
    query = db.query(models.Location)
    
    if entity_id:
        query = query.filter(models.Location.entity_id == entity_id)
    if entity_type:
        query = query.filter(models.Location.entity_type == entity_type)
    
    locations = query.order_by(models.Location.timestamp.desc()).offset(skip).limit(limit).all()
    
    result = []
    for location in locations:
        # Extract coordinates
        result_query = db.execute(
            f"SELECT ST_X(coordinates::geometry) as longitude, ST_Y(coordinates::geometry) as latitude FROM locations WHERE id = {location.id}"
        ).first()
        
        if result_query:
            longitude, latitude = result_query
        else:
            longitude, latitude = 0.0, 0.0
            
        result.append(schemas.LocationResponse(
            entity_id=location.entity_id,
            entity_type=location.entity_type,
            latitude=latitude,
            longitude=longitude,
            timestamp=location.timestamp
        ))
        
    return result


@app.get("/locations/entity/{entity_type}/{entity_id}", response_model=List[schemas.LocationResponse])
def get_locations_by_entity(
    entity_type: str = Path(..., regex="^(student|bus)$"),
    entity_id: str = Path(...),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    # Get all locations for a specific entity (student or bus)
    locations = crud.get_locations_by_entity(db=db, entity_type=entity_type, entity_id=entity_id, skip=skip, limit=limit)
    
    result = []
    for location in locations:
        # Extract coordinates
        result_query = db.execute(
            f"SELECT ST_X(coordinates::geometry) as longitude, ST_Y(coordinates::geometry) as latitude FROM locations WHERE id = {location.id}"
        ).first()
        
        if result_query:
            longitude, latitude = result_query
        else:
            longitude, latitude = 0.0, 0.0
            
        result.append(schemas.LocationResponse(
            entity_id=location.entity_id,
            entity_type=location.entity_type,
            latitude=latitude,
            longitude=longitude,
            timestamp=location.timestamp
        ))
        
    return result


@app.get("/")
def read_root():
    return {"service": "Location Service", "status": "running"}