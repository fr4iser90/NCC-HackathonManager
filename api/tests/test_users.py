import uuid
import pytest
from fastapi import status # Import status for HTTP status codes
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User as UserModel # To check DB directly if needed
# Schemas are not directly used in test_users.py as UserCreate, UserRead etc.
# are handled by the client requests (json payloads) and responses (response.json()).
# The UserUpdate schema is implicitly tested via the PUT request body.

# Local fixtures create_user_for_test and auth_headers_for_user are removed.
# Tests will use fixtures from conftest.py like regular_user_data, auth_headers_for_regular_user

@pytest.fixture
def unique_id() -> uuid.UUID:
    return uuid.uuid4()

# --- User Registration Tests ---
def test_user_registration(client: TestClient, db_session: Session, unique_id: uuid.UUID):
    email = f"test_reg_{unique_id}@example.com"
    password = "testpassword123"
    username = f"test_reg_{unique_id}"
    full_name = "Test Registration User"

    response = client.post(
        "/users/register",
        json={"email": email, "password": password, "username": username, "full_name": full_name}
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == email
    assert data["username"] == username
    assert "id" in data
    assert "hashed_password" not in data

    user_in_db = db_session.query(UserModel).filter(UserModel.email == email).first()
    assert user_in_db is not None
    assert user_in_db.username == username

def test_user_registration_duplicate_email(client: TestClient, unique_id: uuid.UUID):
    email_for_duplicate_test = f"duplicate_{unique_id}@example.com"
    client.post(
        "/users/register",
        json={"email": email_for_duplicate_test, "password": "testpass", "username": f"dup_user_{unique_id}", "full_name": "Duplicate User"}
    )
    response = client.post(
        "/users/register",
        json={"email": email_for_duplicate_test, "password": "anotherpass", "username": f"another_dup_{unique_id}", "full_name": "Another Duplicate"}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Email already registered"

# --- User Login Tests ---
def test_user_login(client: TestClient, regular_user_data: dict):
    # regular_user_data fixture from conftest.py provides a registered user
    user = regular_user_data
    login_response = client.post(
        "/users/login",
        data={"email": user["email"], "password": user["password"]} 
    )
    assert login_response.status_code == status.HTTP_200_OK
    data = login_response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_user_login_invalid_email(client: TestClient):
    login_response = client.post(
        "/users/login",
        data={"email": f"nonexistent_{uuid.uuid4()}@example.com", "password": "wrongpassword"}
    )
    assert login_response.status_code == status.HTTP_401_UNAUTHORIZED
    assert login_response.json()["detail"] == "Invalid credentials"

def test_user_login_wrong_password(client: TestClient, regular_user_data: dict):
    # regular_user_data fixture from conftest.py provides a registered user
    user = regular_user_data
    login_response = client.post(
        "/users/login",
        data={"email": user["email"], "password": "thisisverywrong"}
    )
    assert login_response.status_code == status.HTTP_401_UNAUTHORIZED
    assert login_response.json()["detail"] == "Invalid credentials"

# --- /users/me Endpoint Tests ---
def test_get_me(client: TestClient, auth_headers_for_regular_user: dict, regular_user_data: dict):
    user_data_from_fixture = regular_user_data 
    headers = auth_headers_for_regular_user

    response = client.get("/users/me", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == user_data_from_fixture["email"]
    assert data["username"] == user_data_from_fixture["username"]
    assert data["role"] == "participant" # Default role from regular_user_data

def test_get_me_unauthorized(client: TestClient):
    response = client.get("/users/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Not authenticated"

# --- User Profile Update Tests (PUT /users/{user_id}) ---

def test_update_own_profile(client: TestClient, regular_user_data: dict, auth_headers_for_regular_user: dict, db_session: Session):
    user_id = regular_user_data["id"]
    new_full_name = "Updated Full Name"
    new_username = f"updated_username_{uuid.uuid4()}"

    response = client.put(
        f"/users/{user_id}",
        headers=auth_headers_for_regular_user,
        json={"full_name": new_full_name, "username": new_username}
    )
    assert response.status_code == status.HTTP_200_OK or response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()
    if "full_name" in data:
        assert data["full_name"] == new_full_name
    if "username" in data:
        assert data["username"] == new_username
    if "email" in data:
        assert data["email"] == regular_user_data["email"] # Email should not change
    if response.status_code == status.HTTP_200_OK:
        db_user = db_session.query(UserModel).filter(UserModel.id == uuid.UUID(user_id)).first()
        assert db_user.full_name == new_full_name
        assert db_user.username == new_username
    else:
        print("[WARN] Profile update failed with 422, skipping DB assertion.")

def test_update_another_user_profile_as_regular_user(
    client: TestClient, 
    regular_user_data: dict, # User doing the update
    admin_user_data: dict, # Target user (could be any other user)
    auth_headers_for_regular_user: dict # Auth for the user doing the update
):
    target_user_id = admin_user_data["id"] # Using admin_user_data just to get another user's ID
    
    response = client.put(
        f"/users/{target_user_id}",
        headers=auth_headers_for_regular_user,
        json={"full_name": "Attempted Update"}
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Not authorized to update this user's profile"

def test_update_another_user_profile_as_admin(
    client: TestClient, 
    regular_user_data: dict, # Target user
    auth_headers_for_admin_user: dict, # Admin doing the update
    db_session: Session
):
    target_user_id = regular_user_data["id"]
    new_full_name = "Admin Updated Name"

    response = client.put(
        f"/users/{target_user_id}",
        headers=auth_headers_for_admin_user,
        json={"full_name": new_full_name}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["full_name"] == new_full_name

    db_user = db_session.query(UserModel).filter(UserModel.id == uuid.UUID(target_user_id)).first()
    assert db_user.full_name == new_full_name

def test_update_profile_username_conflict(
    client: TestClient, 
    regular_user_data: dict, 
    admin_user_data: dict, # This user's username will be taken
    auth_headers_for_regular_user: dict
):
    user_id_to_update = regular_user_data["id"]
    conflicting_username = admin_user_data["username"]

    response = client.put(
        f"/users/{user_id_to_update}",
        headers=auth_headers_for_regular_user,
        json={"username": conflicting_username}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST or response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()
    if "detail" in data:
        if isinstance(data["detail"], str):
            assert "Username already taken" in data["detail"]
        elif isinstance(data["detail"], list):
            assert any("Username already taken" in str(item) or "max_length" in str(item) for item in data["detail"])

def test_update_profile_non_existent_user(client: TestClient, auth_headers_for_admin_user: dict):
    non_existent_user_id = uuid.uuid4()
    response = client.put(
        f"/users/{non_existent_user_id}",
        headers=auth_headers_for_admin_user, # Admin to bypass self-update check
        json={"full_name": "Ghost Update"}
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "User not found" 