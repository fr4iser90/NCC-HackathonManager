from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
# from fastapi.security import OAuth2PasswordBearer # No longer needed here if not defining scheme

# Import app components
from app.database import get_db
from app.routers import (
    users_router,
    hackathons_router,
    projects_router,
    teams_router,
    judging_router,
    submissions_router
)

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
app.include_router(users_router, prefix="/users", tags=["users"])
app.include_router(hackathons_router, prefix="/hackathons", tags=["hackathons"])
app.include_router(projects_router, prefix="/projects", tags=["projects"])
app.include_router(teams_router, prefix="/teams", tags=["teams"])
app.include_router(judging_router, prefix="/judging", tags=["judging"])
app.include_router(submissions_router, tags=["submissions"])

# Define oauth2_scheme AFTER all routers are included in the app
# This allows the tokenUrl to be resolvable against the app's routing table
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login") # REMOVED - defined in app.security_schemes.py

@app.get("/")
def read_root():
    return {"message": "Welcome to the Hackathon Platform API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
