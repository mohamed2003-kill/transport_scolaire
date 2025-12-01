from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import requests
from app import schemas, models
from app.database import SessionLocal, engine

# Create the database tables automatically
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Notification Service (Simplified)")

# -------------------------------------------------------------
# 🔐 Auth Service Integration
# -------------------------------------------------------------
AUTH_BASE_URL = "http://172.30.80.11:31006/auth/"
ADMIN_EMAIL = "admin@test.com"
ADMIN_PASS = "password"

def get_auth_token() -> str:
    """Helper to get the admin token from the auth service."""
    url = AUTH_BASE_URL + "login"
    data = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASS
    }
    try:
        resp = requests.post(url, json=data, timeout=5)
        if resp.ok:
            return resp.json()["accessToken"]
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Auth Service Login Failed: {resp.text}"
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail="Auth Service is unreachable"
        )

def validate_user_and_role(user_id: str, role: str):
    """
    Checks if user exists and matches the role/entity_type via Auth Service.
    Raises HTTPException if validation fails.
    """
    # 1. Convert ID to int (Auth service expects int based on your snippet)
    try:
        uid_int = int(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="User ID must be a valid integer")

    # 2. Get Token
    token = get_auth_token()

    # 3. Check User
    url = AUTH_BASE_URL + f"user/{uid_int}"
    headers = {"Authorization": "Bearer " + token}
    
    try:
        resp = requests.get(url, headers=headers, timeout=5)
    except requests.exceptions.RequestException:
         raise HTTPException(status_code=503, detail="Auth Service unreachable during user check")

    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail=f"User {user_id} does not exist")
    
    if not resp.ok:
        raise HTTPException(status_code=resp.status_code, detail=f"Auth Check Failed: {resp.text}")

    # 4. Verify Role
    data = resp.json()
    # Handle case sensitivity (e.g., 'Student' vs 'student')
    user_role_db = data.get("role", "").lower()
    target_role = role.lower()

    if user_role_db != target_role:
        raise HTTPException(
            status_code=400, 
            detail=f"Role mismatch: User {user_id} is '{user_role_db}', but notification is for '{target_role}'"
        )
    
    return True

# -------------------------------------------------------------
# 🗄️ Database Dependency
# -------------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------------------------------------------------
# 🚀 Endpoints
# -------------------------------------------------------------

@app.post("/notifications/send", response_model=schemas.NotificationResponse)
def send_notification(
    notification: schemas.NotificationCreate, 
    db: Session = Depends(get_db)
):
    # Validate User and Role with External Service
    validate_user_and_role(notification.user_id, notification.entity_type)

    # If validation passes, create record
    db_notification = models.Notification(
        user_id=notification.user_id,
        entity_type=notification.entity_type,
        title=notification.title,
        body=notification.body,
        status="sent" 
    )
    
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)

    return db_notification

@app.get("/notifications/history/{entity_type}/{user_id}", response_model=List[schemas.NotificationResponse])
def get_notification_history(
    entity_type: str, 
    user_id: str, 
    db: Session = Depends(get_db)
):
    validate_user_and_role(user_id, entity_type)

    notifications = db.query(models.Notification).filter(
        models.Notification.user_id == user_id,
        models.Notification.entity_type == entity_type
    ).order_by(models.Notification.created_at.desc()).all()
    
    return notifications

@app.get("/")
def api_overview():
    return {
        "service": "Notification Microservice",
        "status": "running",
        "description": "Handles sending notifications and retrieving history for users/entities with Auth verification.",
        "endpoints": {
            "send_notification": {
                "method": "POST",
                "path": "/notifications/send",
                "description": "Validates user via Auth Service, then records notification.",
                "body_format": {
                    "user_id": "string (numeric)",
                    "entity_type": "string ('Student', 'Driver', etc.)",
                    "title": "string",
                    "body": "string"
                }
            },
            "get_history": {
                "method": "GET",
                "path": "/notifications/history/{entity_type}/{user_id}",
                "description": "Fetches notification history filtered by entity type and user ID."
            }
        },
        "documentation": "/docs"
    }