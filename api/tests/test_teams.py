import uuid
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from uuid import UUID

from app.models.team import Team, TeamMember # SQLAlchemy models
from app.schemas.team import TeamMemberRole # Enum for DB checks/assertions if needed
from app.models.user import User as UserModel # For user creation in fixtures
from app.models.hackathon import Hackathon # Added for Hackathon model
from app.models.user import User, UserRoleAssociation # Added for user creation and role assignment

# --- Team Creation Tests ---
def test_create_team(client: TestClient, auth_headers_for_regular_user, unique_id: uuid.UUID, db_session: Session, test_hackathon: Hackathon):
    team_name = f"Test Team {unique_id}"
    team_description = "A team for testing purposes."
    response = client.post(
        "/teams/",
        headers=auth_headers_for_regular_user,
        json={"name": team_name, "description": team_description, "is_open": True, "hackathon_id": str(test_hackathon.id)}
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == team_name
    assert data["description"] == team_description
    assert "id" in data
    team_id_str = data["id"]

    # Verify in DB
    team_in_db = db_session.query(Team).filter(Team.id == uuid.UUID(team_id_str)).first()
    assert team_in_db is not None
    assert str(team_in_db.id) == team_id_str

    # Verify creator is a member and leader
    membership = db_session.query(TeamMember).filter(TeamMember.team_id == uuid.UUID(team_id_str)).first()
    assert membership is not None
    # user_id would come from the token used in auth_headers_for_regular_user, tricky to get directly here without more complex fixture
    # assert membership.user_id == user_who_created_it.id 
    assert membership.role == TeamMemberRole.owner # Using imported Enum

def test_create_team_unauthenticated(client: TestClient, unique_id: uuid.UUID, test_hackathon: Hackathon):
    response = client.post(
        "/teams/",
        json={"name": f"Unauthorized Team {unique_id}", "description": "Should not be created", "is_open": True, "hackathon_id": str(test_hackathon.id)}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_create_team_duplicate_name(client: TestClient, auth_headers_for_regular_user, unique_id: uuid.UUID, test_hackathon: Hackathon):
    team_name = f"Duplicate Name Team {unique_id}"
    # The backend now enforces unique team names per hackathon, so the second request should fail.
    resp1 = client.post("/teams/", headers=auth_headers_for_regular_user, json={"name": team_name, "description": "First one", "is_open": True, "hackathon_id": str(test_hackathon.id)})
    resp2 = client.post("/teams/", headers=auth_headers_for_regular_user, json={"name": team_name, "description": "Second one", "is_open": True, "hackathon_id": str(test_hackathon.id)})
    assert resp1.status_code == status.HTTP_201_CREATED
    assert resp2.status_code == status.HTTP_400_BAD_REQUEST

# --- List and Get Team Tests ---
def test_list_teams(client: TestClient, auth_headers_for_regular_user, unique_id: uuid.UUID, test_hackathon: Hackathon):
    # Create a team first to ensure list is not empty
    client.post("/teams/", headers=auth_headers_for_regular_user, json={"name": f"Listable Team {unique_id}", "description": "...", "is_open": True, "hackathon_id": str(test_hackathon.id)})
    response = client.get(f"/teams/?hackathon_id={test_hackathon.id}", headers=auth_headers_for_regular_user) # Listing teams might not require auth depending on app logic
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "name" in data[0]

def test_get_team(client: TestClient, auth_headers_for_regular_user, unique_id: uuid.UUID, test_hackathon: Hackathon):
    team_name = f"Gettable Team {unique_id}"
    create_response = client.post("/teams/", headers=auth_headers_for_regular_user, json={"name": team_name, "description": "...", "is_open": True, "hackathon_id": str(test_hackathon.id)})
    team_id_str = create_response.json()["id"]

    response = client.get(f"/teams/{team_id_str}", headers=auth_headers_for_regular_user) # Getting a team might not require auth
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == team_name
    assert data["id"] == team_id_str
    assert "members" in data # Ensure members list is present

def test_get_team_not_found(client: TestClient, auth_headers_for_regular_user):
    non_existent_uuid = uuid.uuid4()
    response = client.get(f"/teams/{non_existent_uuid}", headers=auth_headers_for_regular_user)
    assert response.status_code == status.HTTP_404_NOT_FOUND

# --- Join and Leave Team Tests ---
@pytest.fixture(scope="function")
def created_team_id(client: TestClient, auth_headers_for_regular_user, unique_id: uuid.UUID, test_hackathon: Hackathon):
    """Fixture to create a team and return its ID."""
    team_name = f"TeamForJoining_{unique_id}"
    response = client.post(
        "/teams/",
        headers=auth_headers_for_regular_user, # User1 creates the team
        json={"name": team_name, "description": "Team to be joined", "is_open": True, "hackathon_id": str(test_hackathon.id)}
    )
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()["id"]

def test_join_team(client: TestClient, auth_headers_for_regular_user, created_team_id, db_session: Session):
    # auth_headers_for_regular_user represents a user (User1). User1 is already leader.
    # To test joining, we need a *different* user (User2).
    # This requires a second user fixture.
    # For now, let's assume the current user (creator) trying to join again will be blocked.
    team_id_str = created_team_id
    response = client.post(f"/teams/{team_id_str}/join", headers=auth_headers_for_regular_user)
    assert response.status_code == status.HTTP_400_BAD_REQUEST # Creator is already a member (leader)
    assert response.json()["detail"] == "User is already a member of this team"

    # To properly test joining, you would need a second set of auth_headers for a different user.
    # Example: test_join_team_new_user(client, auth_headers_for_user_2, created_team_id, db_session)
    # client.post(f"/teams/{team_id_str}/join", headers=auth_headers_for_user_2)
    # ... asserts ...

def test_leave_team(client: TestClient, auth_headers_for_regular_user, created_team_id, db_session: Session):
    team_id_str = created_team_id
    # User (creator/leader) leaves the team
    response = client.post(f"/teams/{team_id_str}/leave", headers=auth_headers_for_regular_user)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify user is no longer a member
    # This requires knowing the user_id from the token in auth_headers_for_regular_user
    # For a simple check, verify the team might be empty or the specific membership is gone.
    # If you had user_id: memberships = db_session.query(TeamMember).filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id).all()
    # assert len(memberships) == 0

def test_leave_team_not_a_member(client: TestClient, auth_headers_for_regular_user, unique_id: uuid.UUID, test_hackathon: Hackathon):
    # Create a team with user1
    team_name = f"TeamToLeave_{unique_id}"
    team_create_resp = client.post("/teams/", headers=auth_headers_for_regular_user, json={"name": team_name, "is_open": True, "hackathon_id": str(test_hackathon.id)})
    team_id_str = team_create_resp.json()["id"]

    # User1 (creator) leaves the team first
    client.post(f"/teams/{team_id_str}/leave", headers=auth_headers_for_regular_user)

    # Attempt to leave again
    response = client.post(f"/teams/{team_id_str}/leave", headers=auth_headers_for_regular_user)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "User is not a member of this team."

def test_join_team_not_found(client: TestClient, auth_headers_for_regular_user):
    non_existent_uuid = uuid.uuid4()
    response = client.post(f"/teams/{non_existent_uuid}/join", headers=auth_headers_for_regular_user)
    assert response.status_code == status.HTTP_404_NOT_FOUND 

@pytest.fixture
def another_regular_user_data(db_session: Session, unique_id: uuid.UUID) -> dict:
    from app.auth import get_password_hash # Local import for fixture setup
    email = f"another_user_{unique_id}@example.com"
    username = f"another_user_{unique_id}"
    password = "anotherpassword"
    user = User(
        email=email,
        username=username,
        hashed_password=get_password_hash(password),
        full_name="Another Test User",
        github_id=None,
        avatar_url=None,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    db_session.add(UserRoleAssociation(user_id=user.id, role="participant"))
    db_session.commit()
    return {
        "id": str(user.id),
        "email": user.email,
        "username": user.username,
        "password": password,
        "role": "participant",
    }

@pytest.fixture
def auth_headers_for_another_user(client: TestClient, another_regular_user_data: dict) -> dict:
    response = client.post("/users/login", data={"email": another_regular_user_data["email"], "password": another_regular_user_data["password"]})
    assert response.status_code == status.HTTP_200_OK
    return {"Authorization": f"Bearer {response.json()['access_token']}"}

# --- Team Update Tests (PUT /teams/{team_id}) ---
def test_update_team_as_owner(
    client: TestClient, created_team_id: str, auth_headers_for_regular_user: dict, db_session: Session, regular_user_data: dict
):
    # regular_user_data created the team via created_team_id fixture, so they are the owner.
    new_name = "Updated Team Name by Owner"
    new_desc = "Owner was here."
    response = client.put(
        f"/teams/{created_team_id}",
        headers=auth_headers_for_regular_user,
        json={"name": new_name, "description": new_desc, "is_open": True}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == new_name
    assert data["description"] == new_desc

    db_team = db_session.query(Team).filter(Team.id == uuid.UUID(created_team_id)).first()
    assert db_team.name == new_name

def test_update_team_as_admin(
    client: TestClient, created_team_id: str, auth_headers_for_admin_user: dict, db_session: Session
):
    new_name = "Updated Team Name by Admin"
    response = client.put(
        f"/teams/{created_team_id}",
        headers=auth_headers_for_admin_user,
        json={"name": new_name, "is_open": True}
    )
    assert response.status_code == status.HTTP_200_OK
    db_team = db_session.query(Team).filter(Team.id == uuid.UUID(created_team_id)).first()
    assert db_team.name == new_name

def test_update_team_as_member_forbidden(
    client: TestClient, created_team_id: str, 
    auth_headers_for_regular_user: dict, # Team owner
    another_regular_user_data: dict, auth_headers_for_another_user: dict, # Another user (member)
    db_session: Session
):
    # another_user joins the team created by regular_user
    join_response = client.post(f"/teams/{created_team_id}/join", headers=auth_headers_for_another_user)
    assert join_response.status_code == status.HTTP_204_NO_CONTENT

    response = client.put(
        f"/teams/{created_team_id}",
        headers=auth_headers_for_another_user, # Member attempts update
        json={"name": "Attempt by member", "is_open": True}
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_update_team_as_non_member_forbidden(
    client: TestClient, created_team_id: str, auth_headers_for_another_user: dict # User not part of the team
):
    response = client.put(
        f"/teams/{created_team_id}",
        headers=auth_headers_for_another_user,
        json={"name": "Attempt by non-member", "is_open": True}
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN # Or 404 if team not found by dependency first, then 403

# --- Delete Team Tests (DELETE /teams/{team_id}) ---
def test_delete_team_as_owner(client: TestClient, created_team_id: str, auth_headers_for_regular_user: dict, db_session: Session):
    response = client.delete(f"/teams/{created_team_id}", headers=auth_headers_for_regular_user)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    team = db_session.query(Team).filter(Team.id == uuid.UUID(created_team_id)).first()
    assert team is not None
    assert team.status == "disbanded"

def test_delete_team_as_admin(client: TestClient, created_team_id: str, auth_headers_for_admin_user: dict, db_session: Session):
    response = client.delete(f"/teams/{created_team_id}", headers=auth_headers_for_admin_user)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    team = db_session.query(Team).filter(Team.id == uuid.UUID(created_team_id)).first()
    assert team is not None
    assert team.status == "disbanded"

def test_delete_team_as_member_forbidden(
    client: TestClient, created_team_id: str, 
    auth_headers_for_regular_user: dict, # Owner
    auth_headers_for_another_user: dict, # Member
    db_session: Session
):
    join_response = client.post(f"/teams/{created_team_id}/join", headers=auth_headers_for_another_user)
    assert join_response.status_code == status.HTTP_204_NO_CONTENT
    response = client.delete(f"/teams/{created_team_id}", headers=auth_headers_for_another_user)
    assert response.status_code == status.HTTP_403_FORBIDDEN

# --- Updated Join and Leave Team Tests ---
def test_join_team_new_user(client: TestClient, auth_headers_for_another_user: dict, created_team_id: str, db_session: Session, another_regular_user_data: dict):
    team_id = uuid.UUID(created_team_id)
    user_id = uuid.UUID(another_regular_user_data["id"])

    response = client.post(f"/teams/{created_team_id}/join", headers=auth_headers_for_another_user)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    member_in_db = db_session.query(TeamMember).filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id).first()
    assert member_in_db is not None
    assert member_in_db.role == "member"

def test_leave_team_sole_owner(client: TestClient, created_team_id: str, auth_headers_for_regular_user: dict, db_session: Session, regular_user_data: dict):
    # regular_user (owner) leaves the team. Currently allowed by router logic.
    response = client.post(f"/teams/{created_team_id}/leave", headers=auth_headers_for_regular_user)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    # Team still exists but is ownerless.
    assert db_session.query(Team).filter(Team.id == uuid.UUID(created_team_id)).first() is not None
    # Owner (regular_user_data) is no longer a member.
    assert db_session.query(TeamMember).filter(TeamMember.team_id == uuid.UUID(created_team_id), TeamMember.user_id == uuid.UUID(regular_user_data["id"])).first() is None

# --- Remove Team Member Tests (DELETE /teams/{team_id}/members/{user_id_to_remove}) ---
def test_remove_member_by_owner(
    client: TestClient, created_team_id: str, 
    auth_headers_for_regular_user: dict, # Owner
    another_regular_user_data: dict, auth_headers_for_another_user: dict, # Member to be removed
    db_session: Session
):
    team_id = uuid.UUID(created_team_id)
    member_to_remove_id = uuid.UUID(another_regular_user_data["id"])
    # another_user joins the team
    client.post(f"/teams/{created_team_id}/join", headers=auth_headers_for_another_user).raise_for_status()

    response = client.delete(f"/teams/{created_team_id}/members/{member_to_remove_id}", headers=auth_headers_for_regular_user)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert db_session.query(TeamMember).filter(TeamMember.team_id == team_id, TeamMember.user_id == member_to_remove_id).first() is None

def test_remove_member_by_admin(
    client: TestClient, created_team_id: str, 
    auth_headers_for_admin_user: dict, # Admin
    another_regular_user_data: dict, auth_headers_for_another_user: dict, # Member to be removed
    db_session: Session
):
    team_id = uuid.UUID(created_team_id)
    member_to_remove_id = uuid.UUID(another_regular_user_data["id"])
    client.post(f"/teams/{created_team_id}/join", headers=auth_headers_for_another_user).raise_for_status()

    response = client.delete(f"/teams/{created_team_id}/members/{member_to_remove_id}", headers=auth_headers_for_admin_user)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert db_session.query(TeamMember).filter(TeamMember.team_id == team_id, TeamMember.user_id == member_to_remove_id).first() is None

def test_remove_self_from_team(
    client: TestClient, created_team_id: str, 
    another_regular_user_data: dict, auth_headers_for_another_user: dict, # User removing self
    db_session: Session
):
    team_id = uuid.UUID(created_team_id)
    user_id_removing_self = uuid.UUID(another_regular_user_data["id"])
    client.post(f"/teams/{created_team_id}/join", headers=auth_headers_for_another_user).raise_for_status()

    response = client.delete(f"/teams/{created_team_id}/members/{user_id_removing_self}", headers=auth_headers_for_another_user)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert db_session.query(TeamMember).filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id_removing_self).first() is None

def test_remove_member_by_another_member_forbidden(
    client: TestClient, created_team_id: str,
    auth_headers_for_regular_user: dict, # Owner
    another_regular_user_data: dict, auth_headers_for_another_user: dict, # Member 1 (attacker)
    db_session: Session
):
    # Member 1 (another_user) joins
    client.post(f"/teams/{created_team_id}/join", headers=auth_headers_for_another_user).raise_for_status()
    # Create a third user (victim)
    victim_email = f"victim_{uuid.uuid4()}@example.com"
    victim_username = f"victim_{uuid.uuid4()}"
    victim_password = "victimpass"
    victim_response = client.post("/users/register", json={"email": victim_email, "password": victim_password, "username": victim_username, "full_name": "Victim User"})
    victim_id = uuid.UUID(victim_response.json()["id"])
    victim_auth_headers = {"Authorization": f"Bearer {client.post('/users/login', data={'email': victim_email, 'password': victim_password}).json()['access_token']}"}
    # Victim joins the team
    client.post(f"/teams/{created_team_id}/join", headers=victim_auth_headers).raise_for_status()

    # Member 1 (another_user) tries to remove Victim
    response = client.delete(f"/teams/{created_team_id}/members/{victim_id}", headers=auth_headers_for_another_user)
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_remove_sole_owner_forbidden(
    client: TestClient, created_team_id: str, 
    regular_user_data: dict, auth_headers_for_regular_user: dict # Owner
):
    owner_id = regular_user_data["id"]
    # Owner tries to remove themselves using the generic remove endpoint when they are the sole owner
    response = client.delete(f"/teams/{created_team_id}/members/{owner_id}", headers=auth_headers_for_regular_user)
    assert response.status_code == status.HTTP_400_BAD_REQUEST # Dependency should prevent this
    assert "Sole owner cannot remove themselves" in response.json()["detail"]

def test_remove_non_existent_member(client: TestClient, created_team_id: str, auth_headers_for_regular_user: dict):
    non_existent_member_id = uuid.uuid4()
    response = client.delete(f"/teams/{created_team_id}/members/{non_existent_member_id}", headers=auth_headers_for_regular_user)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Member to remove not found in this team." 

@pytest.fixture(scope="function")
def test_team(
    client: TestClient,
    db_session: Session,
    team_owner_user: UserModel,
    auth_headers_team_owner: dict,
    test_hackathon: Hackathon,
) -> Team:
    team_data = TeamCreate(
        name="Submission Test Team", 
        description="A team for submission testing",
        hackathon_id=test_hackathon.id
    )
    response = client.post("/teams/", json=jsonable_encoder(team_data), headers=auth_headers_team_owner)
    assert response.status_code == status.HTTP_201_CREATED
    team_id_str = response.json()["id"]
    team_uuid = UUID(team_id_str)
    return db_session.query(Team).filter(Team.id == team_uuid).first()
