from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
# from fastapi.security import OAuth2PasswordBearer # No longer needed here if not defining scheme
from fastapi.staticfiles import StaticFiles
import os
import time
from app.logger import get_logger

# Import app components
from app.database import get_db
from app.routers import (
    users_router,
    hackathons_router,
    projects_router,
    teams_router,
    judging_router,
    submissions_router,
    ping_router,
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

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(id(request))
    start_time = time.time()
    
    logger.info(f"Request {request_id} started: {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(f"Request {request_id} completed: {response.status_code} in {process_time:.4f}s")
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"Request {request_id} failed in {process_time:.4f}s: {str(e)}")
        raise

static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
else:
    import warnings
    warnings.warn(f"Static directory {static_dir} does not exist. Static files will not be served.")

# Router einbinden
app.include_router(users_router, prefix="/users", tags=["users"])
app.include_router(hackathons_router, prefix="/hackathons", tags=["hackathons"])
app.include_router(projects_router, prefix="/projects", tags=["projects"])
app.include_router(teams_router, prefix="/teams", tags=["teams"])
app.include_router(judging_router, prefix="/judging", tags=["judging"])
app.include_router(submissions_router, prefix="/submissions", tags=["submissions"])
app.include_router(ping_router, prefix="/ping", tags=["ping"])

# Initialize logger
logger = get_logger("hackathon_api")

@app.get("/")
def read_root():
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to the Hackathon Platform API"}

@app.get("/health")
def health_check():
    logger.info("Health check endpoint accessed")
    return {"status": "healthy"}

@app.get("/logs/error")
def get_error_log():
    log_path = os.path.join(os.path.dirname(__file__), "../logs/error.log")
    try:
        with open(log_path, "r") as f:
            lines = f.readlines()
        # Return the last 50 lines
        return {"error_log": "".join(lines[-50:])}
    except Exception as e:
        return {"error": str(e)}

# Log application startup
@app.on_event("startup")
async def startup_event():
    logger.info("Application startup")
    logger.info(f"FastAPI application '{app.title}' version {app.version} starting up")

# Log application shutdown
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown")
