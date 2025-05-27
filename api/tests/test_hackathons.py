import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.hackathon import Hackathon  # SQLAlchemy model
from app.schemas.hackathon import HackathonStatus  # Enum for payload
from app.models.user import (
    User as UserModel,
)  # For type hinting if needed for organizer checks


# --- Helper Data ---
def get_valid_hackathon_data(
    unique_suffix: str, organizer_id: Optional[uuid.UUID] = None
) -> dict:
    return {
        "name": f"Test Hackathon {unique_suffix}",
        "description": "A fun hackathon for testing!",
        "start_date": (datetime.now(timezone.utc) + timedelta(days=10)).isoformat(),
        "end_date": (datetime.now(timezone.utc) + timedelta(days=13)).isoformat(),
        "status": HackathonStatus.UPCOMING.value,
        "location": "Virtual",
        "organizer_id": str(organizer_id) if organizer_id else None,
    }


# --- Hackathon CRUD Tests ---


def test_create_hackathon_as_admin(
    client: TestClient,
    admin_user_data: dict,
    auth_headers_for_admin_user: dict,
    unique_id: uuid.UUID,
    db_session: Session,
):
    hackathon_data = get_valid_hackathon_data(str(unique_id), admin_user_data["id"])
    response = client.post(
        "/hackathons/", headers=auth_headers_for_admin_user, json=hackathon_data
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == hackathon_data["name"]
    assert data["organizer_id"] == admin_user_data["id"]
    assert (
        db_session.query(Hackathon)
        .filter(Hackathon.id == uuid.UUID(data["id"]))
        .first()
        is not None
    )


def test_create_hackathon_as_regular_user(
    client: TestClient,
    regular_user_data: dict,
    auth_headers_for_regular_user: dict,
    unique_id: uuid.UUID,
):
    hackathon_data = get_valid_hackathon_data(str(unique_id), regular_user_data["id"])
    response = client.post(
        "/hackathons/", headers=auth_headers_for_regular_user, json=hackathon_data
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_hackathon_invalid_dates(
    client: TestClient, auth_headers_for_admin_user: dict, unique_id: uuid.UUID
):
    hackathon_data = get_valid_hackathon_data(str(unique_id))
    hackathon_data["start_date"] = (
        datetime.now(timezone.utc) + timedelta(days=13)
    ).isoformat()
    hackathon_data["end_date"] = (
        datetime.now(timezone.utc) + timedelta(days=10)
    ).isoformat()  # End before start
    response = client.post(
        "/hackathons/", headers=auth_headers_for_admin_user, json=hackathon_data
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_create_hackathon_duplicate_name(
    client: TestClient, auth_headers_for_admin_user: dict, unique_id: uuid.UUID
):
    hackathon_data = get_valid_hackathon_data(str(unique_id))
    client.post(
        "/hackathons/", headers=auth_headers_for_admin_user, json=hackathon_data
    ).raise_for_status()
    response = client.post(
        "/hackathons/", headers=auth_headers_for_admin_user, json=hackathon_data
    )
    assert (
        response.status_code == status.HTTP_400_BAD_REQUEST
    )  # Assuming name is unique


def test_list_hackathons_unauthenticated(client: TestClient, unique_id: uuid.UUID):
    response = client.get("/hackathons/")
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)


def test_list_hackathons_authenticated(
    client: TestClient,
    auth_headers_for_admin_user: dict,
    admin_user_data: dict,
    unique_id: uuid.UUID,
    db_session: Session,
):
    # Create a hackathon to ensure the list is not empty
    hackathon_data = get_valid_hackathon_data(
        f"Listable {unique_id}", admin_user_data["id"]
    )
    create_response = client.post(
        "/hackathons/", headers=auth_headers_for_admin_user, json=hackathon_data
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    created_hackathon_id = create_response.json()["id"]

    response = client.get("/hackathons/", headers=auth_headers_for_admin_user)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert any(h["id"] == created_hackathon_id for h in data)


def test_get_hackathon(
    client: TestClient,
    auth_headers_for_admin_user: dict,
    admin_user_data: dict,
    unique_id: uuid.UUID,
):
    hackathon_data = get_valid_hackathon_data(str(unique_id), admin_user_data["id"])
    create_response = client.post(
        "/hackathons/", headers=auth_headers_for_admin_user, json=hackathon_data
    )
    created_hackathon_id = create_response.json()["id"]

    response = client.get(
        f"/hackathons/{created_hackathon_id}", headers=auth_headers_for_admin_user
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == hackathon_data["name"]
    assert data["organizer"]["id"] == admin_user_data["id"]  # Check populated organizer


def test_get_hackathon_not_found(client: TestClient, auth_headers_for_admin_user: dict):
    non_existent_id = uuid.uuid4()
    response = client.get(
        f"/hackathons/{non_existent_id}", headers=auth_headers_for_admin_user
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_hackathon_as_admin(
    client: TestClient,
    auth_headers_for_admin_user: dict,
    admin_user_data: dict,
    unique_id: uuid.UUID,
    db_session: Session,
):
    hackathon_data = get_valid_hackathon_data(str(unique_id), admin_user_data["id"])
    create_response = client.post(
        "/hackathons/", headers=auth_headers_for_admin_user, json=hackathon_data
    )
    created_hackathon_id = create_response.json()["id"]

    update_payload = {
        "name": f"Updated Hackathon {unique_id}",
        "status": HackathonStatus.ACTIVE.value,
    }
    response = client.put(
        f"/hackathons/{created_hackathon_id}",
        headers=auth_headers_for_admin_user,
        json=update_payload,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == update_payload["name"]
    assert data["status"] == update_payload["status"]

    db_hackathon = (
        db_session.query(Hackathon)
        .filter(Hackathon.id == uuid.UUID(created_hackathon_id))
        .first()
    )
    assert db_hackathon.name == update_payload["name"]


def test_update_hackathon_as_regular_user(
    client: TestClient,
    auth_headers_for_admin_user: dict,  # To create the hackathon
    auth_headers_for_regular_user: dict,  # To attempt update
    admin_user_data: dict,
    unique_id: uuid.UUID,
):
    hackathon_data = get_valid_hackathon_data(str(unique_id), admin_user_data["id"])
    create_response = client.post(
        "/hackathons/", headers=auth_headers_for_admin_user, json=hackathon_data
    )
    created_hackathon_id = create_response.json()["id"]

    update_payload = {"name": f"Attempted Update {unique_id}"}
    response = client.put(
        f"/hackathons/{created_hackathon_id}",
        headers=auth_headers_for_regular_user,
        json=update_payload,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_delete_hackathon_as_admin(
    client: TestClient,
    auth_headers_for_admin_user: dict,
    admin_user_data: dict,
    unique_id: uuid.UUID,
    db_session: Session,
):
    hackathon_data = get_valid_hackathon_data(str(unique_id), admin_user_data["id"])
    create_response = client.post(
        "/hackathons/", headers=auth_headers_for_admin_user, json=hackathon_data
    )
    created_hackathon_id = uuid.UUID(create_response.json()["id"])

    delete_response = client.delete(
        f"/hackathons/{created_hackathon_id}", headers=auth_headers_for_admin_user
    )
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT
    assert (
        db_session.query(Hackathon).filter(Hackathon.id == created_hackathon_id).first()
        is None
    )


def test_delete_hackathon_as_regular_user(
    client: TestClient,
    auth_headers_for_admin_user: dict,  # To create
    auth_headers_for_regular_user: dict,  # To attempt delete
    admin_user_data: dict,
    unique_id: uuid.UUID,
):
    hackathon_data = get_valid_hackathon_data(str(unique_id), admin_user_data["id"])
    create_response = client.post(
        "/hackathons/", headers=auth_headers_for_admin_user, json=hackathon_data
    )
    created_hackathon_id = create_response.json()["id"]

    delete_response = client.delete(
        f"/hackathons/{created_hackathon_id}", headers=auth_headers_for_regular_user
    )
    assert delete_response.status_code == status.HTTP_403_FORBIDDEN
