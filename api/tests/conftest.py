import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env.test", override=True)
import pytest
import uuid
from typing import Generator, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger("conftest")

# Set TESTING environment variable
os.environ["TESTING"] = "1"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text, StaticPool, event
from sqlalchemy.orm import sessionmaker, Session
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from app.main import app
from app.database import Base, get_db
from app.models.user import User, UserRoleAssociation
from app.auth import get_password_hash
from app.models.hackathon import Hackathon
from app.schemas.hackathon import HackathonStatus, HackathonMode

# --- Test Database Setup (PostgreSQL) ---
import pprint

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg2://testuser:testpass@localhost:5433/testdb"
)

engine_test = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)

EXAMPLE_PROJECTS_DIR = os.path.join(os.path.dirname(__file__), "example_projects")


@pytest.fixture(scope="session", autouse=True)
def setup_test_db_schemas():
    # This event listener will attach schemas when a connection is first made.
    # It only runs once per engine (due to StaticPool and single connection for tests)
    @event.listens_for(engine_test, "connect")
    def connect(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("CREATE SCHEMA IF NOT EXISTS auth;")
        cursor.execute("CREATE SCHEMA IF NOT EXISTS teams;")
        cursor.execute("CREATE SCHEMA IF NOT EXISTS projects;")
        cursor.execute("CREATE SCHEMA IF NOT EXISTS judging;")
        cursor.execute("CREATE SCHEMA IF NOT EXISTS hackathons;")
        # Cleanup: Remove any hackathon_registrations with NULL project_id (legacy/orphaned)
        try:
            cursor.execute(
                "DELETE FROM hackathons.hackathon_registrations WHERE project_id IS NULL;"
            )
        except Exception as e:
            print(
                f"[DB CLEANUP] Failed to delete orphaned hackathon_registrations: {e}"
            )
        cursor.close()


@pytest.fixture(scope="session")
def db_session(setup_test_db_schemas) -> Generator[Session, None, None]:
    Base.metadata.create_all(bind=engine_test)  # Create tables once for the session
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session")
def client() -> TestClient:
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


@pytest.fixture
def unique_id() -> (
    uuid.UUID
):  # This can still be used by tests for other unique elements
    return uuid.uuid4()


# --- User Helper Function (not a fixture itself) ---
def _create_user_in_db_helper(db_session, role="participant"):
    # Feste Testdaten für Kernrollen
    if role == "admin":
        email = os.environ.get("ADMIN_EMAIL", "admin@example.com")
        username = os.environ.get("ADMIN_USERNAME", "admin")
        password = os.environ.get("ADMIN_PASSWORD", "adminpass")
    elif role == "judge":
        email = "judge@example.com"
        username = "judge"
        password = "judgepass"
    elif role == "mentor":
        email = "mentor@example.com"
        username = "mentor"
        password = "mentorpass"
    elif role == "participant":
        email = "participant@example.com"
        username = "participant"
        password = "participant123"
    else:
        user_id_to_use = uuid.uuid4()
        email = f"testuser_{role}_{user_id_to_use}@example.com"
        username = f"testuser_{role}_{user_id_to_use}"
        password = "testpassword"
    # Idempotenz: Vorher löschen, falls vorhanden
    existing = db_session.query(User).filter_by(email=email).first()
    if existing:
        # Vor dem Löschen: alle referenzierenden Registrations löschen
        db_session.execute(
            text(
                "DELETE FROM hackathons.hackathon_registrations WHERE user_id = :user_id OR team_id IN (SELECT id FROM teams.teams WHERE id IN (SELECT team_id FROM teams.members WHERE user_id = :user_id))"
            ),
            {"user_id": existing.id},
        )
        # Vor dem Löschen: alle referenzierenden Hackathons löschen
        db_session.execute(
            text("DELETE FROM hackathons.hackathons WHERE organizer_id = :user_id"),
            {"user_id": existing.id},
        )
        db_session.query(UserRoleAssociation).filter_by(user_id=existing.id).delete()
        db_session.delete(existing)
        db_session.commit()
    user = User(
        email=email,
        username=username,
        hashed_password=get_password_hash(password),
        full_name="Test User",
        github_id=None,
        avatar_url=None,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    db_session.add(UserRoleAssociation(user_id=user.id, role=role))
    db_session.commit()
    return {
        "id": str(user.id),
        "email": email,
        "username": username,
        "password": password,
        "role": role,
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
def created_regular_user(
    db_session: Session, regular_user_data: Dict[str, Any]
) -> User:
    user = (
        db_session.query(User)
        .filter(User.id == uuid.UUID(regular_user_data["id"]))
        .first()
    )
    assert (
        user is not None
    ), f"Regular user with id {regular_user_data['id']} not found in DB for fixture."
    return user


@pytest.fixture(scope="function")
def created_admin_user(db_session: Session, admin_user_data: Dict[str, Any]) -> User:
    user = (
        db_session.query(User)
        .filter(User.id == uuid.UUID(admin_user_data["id"]))
        .first()
    )
    assert (
        user is not None
    ), f"Admin user with id {admin_user_data['id']} not found in DB for fixture."
    return user


@pytest.fixture(scope="function")
def created_judge_user(db_session: Session, judge_user_data: Dict[str, Any]) -> User:
    user = (
        db_session.query(User)
        .filter(User.id == uuid.UUID(judge_user_data["id"]))
        .first()
    )
    assert (
        user is not None
    ), f"Judge user with id {judge_user_data['id']} not found in DB for fixture."
    return user


# Auth Helper function (not a fixture)
def _get_auth_headers_helper(
    client: TestClient, user_data: Dict[str, Any]
) -> Dict[str, str]:
    response = client.post(
        "/users/login",
        data={"email": user_data["email"], "password": user_data["password"]},
    )
    if response.status_code != status.HTTP_200_OK:
        logger.warning(
            f"Login failed for user {user_data.get('email')} during auth header generation. Status: {response.status_code}, Response: {response.text}"
        )
    assert (
        response.status_code == status.HTTP_200_OK
    ), "Failed to log in user for getting auth headers"
    tokens = response.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


# Fixtures for specific user role auth headers
@pytest.fixture(scope="function")
def auth_headers_for_regular_user(
    client: TestClient, regular_user_data: Dict[str, Any]
) -> Dict[str, str]:
    return _get_auth_headers_helper(client, regular_user_data)


@pytest.fixture(scope="function")
def auth_headers_for_admin_user(
    client: TestClient, admin_user_data: Dict[str, Any]
) -> Dict[str, str]:
    return _get_auth_headers_helper(client, admin_user_data)


@pytest.fixture(scope="function")
def auth_headers_for_judge_user(
    client: TestClient, judge_user_data: Dict[str, Any]
) -> Dict[str, str]:
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
        mode=HackathonMode.TEAM_ONLY,
        max_team_size=4,
        min_team_size=1,
        is_public=True,
        allow_individuals=True,
        allow_multiple_projects_per_team=True,
    )
    db_session.add(hackathon)
    db_session.commit()
    db_session.refresh(hackathon)
    return hackathon
