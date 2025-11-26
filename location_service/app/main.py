from fastapi.routing import APIRoute
from fastapi import FastAPI, HTTPException, Depends, Path
from sqlalchemy.orm import Session
from sqlalchemy import text
from app import schemas, crud, models
from app.database import SessionLocal, engine
from typing import List, Optional
from .get_auth import check_user_exists
import os


models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Location Service", description="Service for tracking GPS locations of students and buses")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post(
    "/locations/{entity_type}/{entity_id}",
    status_code=201,
    summary="Create a location",
    description="Add a GPS location for a student or a bus..."
)
def create_location(
    entity_type: str = Path(..., regex="^(student|bus)$"),
    entity_id: str = Path(...),
    location: schemas.LocationCreate = Depends(),
    db: Session = Depends(get_db)
):
    
    if entity_type not in ["student", "bus"]:
        raise HTTPException(status_code=400, detail="entity_type must be 'student' or 'bus'")
    
    
    
    
    try:
        
        exists, error_msg = check_user_exists(int(entity_id), entity_type)
        
        if not exists:
            
            raise HTTPException(status_code=404, detail=f"Auth Service Error: {error_msg}")
            
    except ValueError:
        raise HTTPException(status_code=400, detail="Entity ID must be an integer to check against Auth service")
    except Exception as e:
        
        raise HTTPException(status_code=503, detail=f"Could not connect to Auth Service: {str(e)}")
    

    
    db_location = crud.create_location(
        db=db,
        entity_id=entity_id,
        entity_type=entity_type,
        latitude=location.latitude,
        longitude=location.longitude
    )
    
    return {"message": f"Location for {entity_type} {entity_id} created successfully"}

@app.get(
    "/locations/{entity_id}",
    response_model=schemas.LocationResponse,
    summary="Get latest location",
    description="Retrieve the latest GPS location (latitude and longitude) for a given entity ID."
)
def get_latest_location_by_entity_id(entity_id: str, db: Session = Depends(get_db)):
    try:
        exists, error_msg = check_user_exists(int(entity_id),"")
        if not exists:
            raise HTTPException(status_code=404, detail=f"User not found: {error_msg}")
    except ValueError:
        pass
    db_location = crud.get_latest_location_by_entity_id(db=db, entity_id=entity_id)
    
    if not db_location:
        raise HTTPException(status_code=404, detail="Location not found")

    result = db.execute(
        text("SELECT ST_X(coordinates::geometry) as longitude, ST_Y(coordinates::geometry) as latitude FROM locations WHERE id = :location_id"),
        {"location_id": db_location.id}
    ).first()
    
    if result:
        longitude, latitude = result
    else:
        
        longitude, latitude = 0.0, 0.0
    
    
    response = schemas.LocationResponse(
        entity_id=db_location.entity_id,
        entity_type=db_location.entity_type,
        latitude=latitude,
        longitude=longitude,
        timestamp=db_location.timestamp
    )
    
    return response


@app.get(
    "/locations/",
    response_model=List[schemas.LocationResponse],
    summary="Get locations",
    description="Retrieve a list of locations. You can optionally filter by entity ID or entity type and paginate with skip/limit."
)
def get_locations(
    entity_id: Optional[str] = None,
    entity_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    
    query = db.query(models.Location)
    
    if entity_id:
        query = query.filter(models.Location.entity_id == entity_id)
    if entity_type:
        query = query.filter(models.Location.entity_type == entity_type)
    
    locations = query.order_by(models.Location.timestamp.desc()).offset(skip).limit(limit).all()
    
    result = []
    for location in locations:
        
        result_query = db.execute(
            text("SELECT ST_X(coordinates::geometry) as longitude, ST_Y(coordinates::geometry) as latitude FROM locations WHERE id = :location_id"),
            {"location_id": location.id}
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


@app.get(
    "/locations/entity/{entity_type}/{entity_id}",
    response_model=List[schemas.LocationResponse],
    summary="Get locations by entity",
    description="Retrieve all locations for a specific entity (student or bus) with optional pagination using skip and limit."
)
def get_locations_by_entity(
    entity_type: str = Path(..., regex="^(student|bus)$"),
    entity_id: str = Path(...),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    try:
        exists, error_msg = check_user_exists(int(entity_id), entity_type)
        if not exists:
            raise HTTPException(status_code=404, detail=f"User not found: {error_msg}")
    except ValueError:
        pass
    locations = crud.get_locations_by_entity(db=db, entity_type=entity_type, entity_id=entity_id, skip=skip, limit=limit)
    
    result = []
    for location in locations:
        result_query = db.execute(
            text("SELECT ST_X(coordinates::geometry) as longitude, ST_Y(coordinates::geometry) as latitude FROM locations WHERE id = :location_id"),
            {"location_id": location.id}
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


@app.get(
    "/entities/locations",
    response_model=List[schemas.EntityLocationResponse],
    summary="Get latest locations of all entities",
    description="Retrieve the latest GPS locations for all entities, optionally filtered by entity type."
)
def get_all_entities_latest_locations(
    entity_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    locations = crud.get_latest_locations_by_entities(db=db, entity_type=entity_type)
    
    result = []
    for location in locations:
        result_query = db.execute(
            text("SELECT ST_X(coordinates::geometry) as longitude, ST_Y(coordinates::geometry) as latitude FROM locations WHERE id = :location_id"),
            {"location_id": location.id}
        ).first()
        
        if result_query:
            longitude, latitude = result_query
        else:
            longitude, latitude = 0.0, 0.0
            
        result.append(schemas.EntityLocationResponse(
            entity_id=location.entity_id,
            entity_type=location.entity_type,
            latitude=latitude,
            longitude=longitude,
            timestamp=location.timestamp
        ))
        
    return result



@app.get("/", summary="Root endpoint", description=" All endpoints and their descriptions")
def read_root():
    routes_info = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            routes_info.append({
                "path": route.path,
                "methods": list(route.methods),
                "name": route.name,
                "summary": route.summary,
                "description": route.description
            })
    return {"service": "Location Service", "status": "running", "endpoints": routes_info}
