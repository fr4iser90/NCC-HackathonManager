from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers import users, hackathons, projects
from app.models.user import User
from app.auth import get_current_user

app = FastAPI(
    title="Hackathon Platform API",
    description="API for managing hackathons, participants, and projects",
    version="1.0.0"
)

# CORS-Konfiguration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In Produktion einschränken
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router einbinden
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(hackathons.router, prefix="/hackathons", tags=["hackathons"])
app.include_router(projects.router, prefix="/projects", tags=["projects"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Hackathon Platform API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/me", response_model=dict)
def read_users_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "role": current_user.role,
        "is_active": current_user.is_active
    }
