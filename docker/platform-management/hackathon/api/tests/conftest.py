import os
import pytest
import uuid
from typing import Generator, Dict, Any, Optional
from datetime import datetime, timedelta

# Set TESTING environment variable
os.environ["TESTING"] = "1"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text, StaticPool, event
from sqlalchemy.orm import sessionmaker, Session
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from app.main import app
from app.database import Base, get_db
from app.models.user import User
from app.auth import get_password_hash
from app.models.hackathon import Hackathon
from app.schemas.hackathon import HackathonStatus, HackathonMode

# --- Test Database Setup (SQLite in-memory for speed) ---
# For full compatibility with PostgreSQL features (like schemas), a test PostgreSQL DB would be better.
# This SQLite setup will not test schema-specific SQL directly.
DATABASE_URL_TEST = "sqlite:///:memory:"

engine_test = create_engine(
    DATABASE_URL_TEST,
    connect_args={"check_same_thread": False}, # Needed for SQLite
    poolclass=StaticPool, # Needed for SQLite
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)

# --- Schemas Used ---
# Define the schemas used by your models here
# This is important for SQLite testing, as we need to "simulate" schemas.
SCHEMAS_TO_ATTACH = ["auth", "teams", "projects", "judging", "hackathons"]

@pytest.fixture(scope="session", autouse=True)
def setup_test_db_schemas():
    # This event listener will attach schemas when a connection is first made.
    # It only runs once per engine (due to StaticPool and single connection for tests)
    @event.listens_for(engine_test, "connect")
    def connect(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        for schema_name in SCHEMAS_TO_ATTACH:
            cursor.execute(f"ATTACH DATABASE ':memory:' AS {schema_name};")
        cursor.close()

@pytest.fixture(scope="function")
def db_session(setup_test_db_schemas) -> Generator[Session, None, None]: # Ensure schema setup runs before session
    Base.metadata.create_all(bind=engine_test) # Create tables for each test function
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine_test) # Drop tables after each test function

@pytest.fixture(scope="function")
def client(db_session: Session) -> TestClient:
    """Override the get_db dependency to use the test database."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass # Session is closed by db_session fixture

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)

@pytest.fixture
def unique_id() -> uuid.UUID: # This can still be used by tests for other unique elements
    return uuid.uuid4()

# --- User Helper Function (not a fixture itself) ---
def _create_user_in_db_helper(db_session: Session, role: str = "participant", specific_uuid: Optional[uuid.UUID] = None) -> Dict[str, Any]:
    user_id_to_use = specific_uuid if specific_uuid else uuid.uuid4()
    email = f"testuser_{role}_{user_id_to_use}@example.com"
    username = f"testuser_{role}_{user_id_to_use}"
    password = "testpassword123"
    full_name = f"Test {role.capitalize()} User"

    user = User(
        id=user_id_to_use, # Use the generated or provided UUID
        email=email,
        username=username, 
        hashed_password=get_password_hash(password),
        full_name=full_name,
        role=role
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return {
        "id": str(user.id),
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role,
        "password": password, # Return plain password for login tests
    }

# --- User Fixtures ---
@pytest.fixture(scope="function")
def regular_user_data(db_session: Session) -> Dict[str, Any]:
    return _create_user_in_db_helper(db_session, role="participant")

@pytest.fixture(scope="function")
def admin_user_data(db_session: Session) -> Dict[str, Any]:
    return _create_user_in_db_helper(db_session, role="admin")

@pytest.fixture(scope="function")
def judge_user_data(db_session: Session) -> Dict[str, Any]:
    return _create_user_in_db_helper(db_session, role="judge")

@pytest.fixture(scope="function")
def created_regular_user(db_session: Session, regular_user_data: Dict[str, Any]) -> User:
    user = db_session.query(User).filter(User.id == uuid.UUID(regular_user_data["id"])).first()
    assert user is not None, f"Regular user with id {regular_user_data['id']} not found in DB for fixture."
    return user

@pytest.fixture(scope="function")
def created_admin_user(db_session: Session, admin_user_data: Dict[str, Any]) -> User:
    user = db_session.query(User).filter(User.id == uuid.UUID(admin_user_data["id"])).first()
    assert user is not None, f"Admin user with id {admin_user_data['id']} not found in DB for fixture."
    return user

@pytest.fixture(scope="function")
def created_judge_user(db_session: Session, judge_user_data: Dict[str, Any]) -> User:
    user = db_session.query(User).filter(User.id == uuid.UUID(judge_user_data["id"])).first()
    assert user is not None, f"Judge user with id {judge_user_data['id']} not found in DB for fixture."
    return user

# Auth Helper function (not a fixture)
def _get_auth_headers_helper(client: TestClient, user_data: Dict[str, Any]) -> Dict[str, str]:
    response = client.post(
        "/users/login", 
        data={"email": user_data["email"], "password": user_data["password"]}
    )
    if response.status_code != status.HTTP_200_OK:
        print(f"Login failed for user {user_data.get('email')} during auth header generation. Status: {response.status_code}, Response: {response.text}")
    assert response.status_code == status.HTTP_200_OK, "Failed to log in user for getting auth headers"
    tokens = response.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}

# Fixtures for specific user role auth headers
@pytest.fixture(scope="function")
def auth_headers_for_regular_user(client: TestClient, regular_user_data: Dict[str, Any]) -> Dict[str, str]:
    return _get_auth_headers_helper(client, regular_user_data)

@pytest.fixture(scope="function")
def auth_headers_for_admin_user(client: TestClient, admin_user_data: Dict[str, Any]) -> Dict[str, str]:
    return _get_auth_headers_helper(client, admin_user_data)

@pytest.fixture(scope="function")
def auth_headers_for_judge_user(client: TestClient, judge_user_data: Dict[str, Any]) -> Dict[str, str]:
    return _get_auth_headers_helper(client, judge_user_data)

# If a generic authenticated user is needed by some tests without specific role focus,
# it can use the regular_user_data and auth_headers_for_regular_user.
# Example test: def test_some_feature(client, auth_headers_for_regular_user):
# pass

@pytest.fixture(scope="function")
def test_hackathon(db_session: Session, unique_id: uuid.UUID) -> Hackathon:
    """Creates a test hackathon for testing."""
    hackathon = Hackathon(
        id=unique_id,
        name=f"Test Hackathon {unique_id}",
        description="A test hackathon for running tests",
        start_date=datetime.now(),
        end_date=datetime.now() + timedelta(days=7),
        status=HackathonStatus.ACTIVE,
        mode=HackathonMode.TEAM_RECOMMENDED,
        max_team_size=4,
        min_team_size=1,
        is_public=True,
        allow_individuals=True,
        allow_multiple_projects_per_team=True
    )
    db_session.add(hackathon)
    db_session.commit()
    db_session.refresh(hackathon)
    return hackathon 