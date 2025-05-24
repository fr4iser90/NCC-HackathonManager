import uuid
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from uuid import UUID

from app.models.project import Project, ProjectTemplate, ProjectStatus
from app.models.team import Team, TeamMember, TeamMemberRole # Ensure TeamMemberRole is imported
from app.models.user import User # Ensure User is imported
from app.models.hackathon import Hackathon
from app.models.team import Team as TeamModel # Fix: Import Team as TeamModel
from app.models.user import User as UserModel
from app.models.project import Project as ProjectModel
from app.schemas.project import ProjectCreate

# --- Fixtures for User Management (from conftest.py, ensure they are available or replicate if needed) ---
# Assuming regular_user_data_payload, auth_headers_for_regular_user, created_regular_user (provides id),
# admin_user_data_payload, auth_headers_for_admin_user, created_admin_user (provides id)
# are available from conftest.py. We will use created_regular_user.id.

# --- New Fixtures for a Second Regular User ---
@pytest.fixture(scope="function")
def second_regular_user_data_payload(unique_id: uuid.UUID) -> dict:
    return {
        "email": f"second_user_{unique_id}@example.com",
        "username": f"second_user_{unique_id}",
        "password": "strongpassword",
        "full_name": "Second Test User"
    }

@pytest.fixture(scope="function")
def created_second_regular_user(client: TestClient, second_regular_user_data_payload: dict, db_session: Session) -> User:
    response = client.post("/users/register", json=second_regular_user_data_payload)
    assert response.status_code == status.HTTP_201_CREATED
    user = db_session.query(User).filter(User.email == second_regular_user_data_payload["email"]).first()
    assert user is not None
    return user

@pytest.fixture(scope="function")
def auth_headers_for_second_regular_user(client: TestClient, created_second_regular_user: User, second_regular_user_data_payload: dict) -> dict:
    login_data = {"email": second_regular_user_data_payload["email"], "password": second_regular_user_data_payload["password"]}
    response = client.post("/users/login", data=login_data)
    assert response.status_code == status.HTTP_200_OK
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# --- Fixtures for Project Tests ---

@pytest.fixture(scope="function")
def created_team(client: TestClient, auth_headers_for_regular_user, created_regular_user: User, unique_id: uuid.UUID, db_session: Session, test_hackathon: Hackathon) -> Team: # Uses created_regular_user
    team_name = f"ProjectTeam_{unique_id}"
    response = client.post(
        "/teams/",
        headers=auth_headers_for_regular_user,
        json={"name": team_name, "description": "A team for projects", "hackathon_id": str(test_hackathon.id)}
    )
    assert response.status_code == status.HTTP_201_CREATED
    team_id_str = response.json()["id"]
    team_uuid = UUID(team_id_str)
    return db_session.query(Team).filter(Team.id == team_uuid).first()

@pytest.fixture(scope="function")
def another_team_created_by_second_user(client: TestClient, auth_headers_for_second_regular_user, created_second_regular_user: User, unique_id: uuid.UUID, db_session: Session) -> Team:
    team_name = f"AnotherTeam_{unique_id}"
    response = client.post(
        "/teams/",
        headers=auth_headers_for_second_regular_user,
        json={"name": team_name, "description": "A team for the second user"}
    )
    assert response.status_code == status.HTTP_201_CREATED
    team_data = response.json()
    team_id_str = team_data["id"]
    team_instance = db_session.query(Team).filter(Team.id == uuid.UUID(team_id_str)).first()
    assert team_instance is not None, "Second team not found in DB after creation"
    
    member_check = db_session.query(TeamMember).filter(
        TeamMember.team_id == team_instance.id,
        TeamMember.user_id == created_second_regular_user.id
    ).first()
    assert member_check is not None, "Second team creator not found as member"
    assert member_check.role == TeamMemberRole.owner, "Second team creator is not an owner"

    return team_instance


@pytest.fixture(scope="function")
def created_project_template(client: TestClient, auth_headers_for_admin_user, unique_id: uuid.UUID, db_session: Session) -> ProjectTemplate:
    template_name = f"Test Template {unique_id}"
    response = client.post(
        "/projects/templates/",
        headers=auth_headers_for_admin_user,
        json={
            "name": template_name,
            "description": "A template for testing.",
            "tech_stack": ["python", "fastapi"],
            "repository_url": f"https://example.com/template_repo/{unique_id}", # Corrected URL
            "live_url": f"https://example.com/template_live/{unique_id}" # Corrected URL
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    template_data = response.json()
    template_id_str = template_data["id"]
    template_instance = db_session.query(ProjectTemplate).filter(ProjectTemplate.id == uuid.UUID(template_id_str)).first()
    assert template_instance is not None, "ProjectTemplate not found in DB after creation in fixture"
    return template_instance

# --- Project Helper Fixtures ---
@pytest.fixture(scope="function")
def project_in_created_team(client: TestClient, auth_headers_for_regular_user, created_team: Team, unique_id: uuid.UUID, db_session: Session) -> Project:
    project_name = f"ProjectInTeam1_{unique_id}"
    response = client.post(
        "/projects/",
        headers=auth_headers_for_regular_user, 
        json={"name": project_name, "team_id": str(created_team.id), "description": "Initial project in created_team"}
    )
    assert response.status_code == status.HTTP_201_CREATED, response.json()
    project_data = response.json()
    project_instance = db_session.query(Project).filter(Project.id == uuid.UUID(project_data["id"])).first()
    assert project_instance is not None
    return project_instance

@pytest.fixture(scope="function")
def project_in_another_team(client: TestClient, auth_headers_for_second_regular_user, another_team_created_by_second_user: Team, unique_id: uuid.UUID, db_session: Session) -> Project:
    project_name = f"ProjectInTeam2_{unique_id}"
    response = client.post(
        "/projects/",
        headers=auth_headers_for_second_regular_user, 
        json={"name": project_name, "team_id": str(another_team_created_by_second_user.id)}
    )
    assert response.status_code == status.HTTP_201_CREATED, response.json()
    project_data = response.json()
    project_instance = db_session.query(Project).filter(Project.id == uuid.UUID(project_data["id"])).first()
    assert project_instance is not None
    return project_instance


# --- Project Template Tests ---
def test_create_project_template_as_admin(client: TestClient, auth_headers_for_admin_user, unique_id: uuid.UUID, db_session: Session):
    template_name = f"Admin Template {unique_id}"
    repo_url = f"https://example.com/admin_repo/{unique_id}" # Corrected URL
    live_url = f"https://example.com/admin_live/{unique_id}" # Corrected URL
    response = client.post(
        "/projects/templates/",
        headers=auth_headers_for_admin_user,
        json={
            "name": template_name,
            "description": "Admin created template.",
            "tech_stack": ["react", "nodejs"],
            "repository_url": repo_url,
            "live_url": live_url
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == template_name
    template_in_db = db_session.query(ProjectTemplate).filter(ProjectTemplate.id == uuid.UUID(data["id"])).first()
    assert template_in_db is not None
    assert template_in_db.name == template_name
    assert template_in_db.repository_url == repo_url # Added assertion

def test_create_project_template_as_regular_user(client: TestClient, auth_headers_for_regular_user, unique_id: uuid.UUID):
    template_name = f"User Template {unique_id}"
    response = client.post(
        "/projects/templates/",
        headers=auth_headers_for_regular_user,
        json={
            "name": template_name,
            "description": "User attempt to create template.",
            "tech_stack": [],
            "repository_url": f"https://example.com/user_repo/{unique_id}", # Corrected URL
            "live_url": f"https://example.com/user_live/{unique_id}" # Corrected URL
        }
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_list_project_templates(client: TestClient, auth_headers_for_regular_user, created_project_template: ProjectTemplate):
    response = client.get("/projects/templates/", headers=auth_headers_for_regular_user)
    assert response.status_code == status.HTTP_200_OK
    templates = response.json()
    assert isinstance(templates, list)
    assert any(t["id"] == str(created_project_template.id) for t in templates)

# --- Project CRUD Tests ---
def test_create_project_as_team_member( 
    client: TestClient, 
    auth_headers_for_regular_user,
    created_team: Team,
    unique_id: uuid.UUID,
    db_session: Session,
    test_hackathon: Hackathon
):
    project_name = f"My Awesome Project {unique_id}"
    response = client.post(
        "/projects/",
        headers=auth_headers_for_regular_user, # User is owner/member of created_team
        json={
            "name": project_name,
            "description": "A groundbreaking project.",
            "hackathon_id": str(test_hackathon.id)
        }
    )
    assert response.status_code == status.HTTP_201_CREATED, response.json()
    data = response.json()
    assert data["name"] == project_name
    assert data["hackathon_id"] == str(test_hackathon.id)
    assert data["status"] == ProjectStatus.DRAFT.value 

    project_in_db = db_session.query(Project).filter(Project.id == uuid.UUID(data["id"])).first()
    assert project_in_db is not None
    assert project_in_db.name == project_name
    assert str(project_in_db.hackathon_id) == str(test_hackathon.id)

def test_create_project_as_admin_for_any_team(
    client: TestClient,
    auth_headers_for_admin_user, 
    created_team: Team, # Team created by regular_user
    unique_id: uuid.UUID,
    db_session: Session
):
    project_name = f"AdminProjectForTeam_{unique_id}"
    response = client.post(
        "/projects/",
        headers=auth_headers_for_admin_user,
        json={
            "name": project_name,
            "description": "Admin creating project for another user's team.",
            "team_id": str(created_team.id)
        }
    )
    assert response.status_code == status.HTTP_201_CREATED, response.json()
    data = response.json()
    assert data["name"] == project_name
    assert data["team_id"] == str(created_team.id)
    project_in_db = db_session.query(Project).filter(Project.id == uuid.UUID(data["id"])).first()
    assert project_in_db is not None
    assert project_in_db.name == project_name

def test_create_project_as_non_member_non_admin(
    client: TestClient,
    auth_headers_for_second_regular_user, # This user is not part of created_team
    created_team: Team, # Team created by regular_user
    unique_id: uuid.UUID
):
    project_name = f"NonMemberAttemptProject_{unique_id}"
    response = client.post(
        "/projects/",
        headers=auth_headers_for_second_regular_user,
        json={
            "name": project_name,
            "team_id": str(created_team.id)
        }
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert "User is not a member of the specified team and not an admin." in data["detail"]


def test_create_project_with_template(
    client: TestClient, 
    auth_headers_for_regular_user, 
    created_team: Team, 
    created_project_template: ProjectTemplate, 
    unique_id: uuid.UUID,
    db_session: Session,
    test_hackathon: Hackathon
):
    project_name = f"Templated Project {unique_id}"
    response = client.post(
        "/projects/",
        headers=auth_headers_for_regular_user,
        json={
            "name": project_name,
            "description": "Project from template.",
            "hackathon_id": str(test_hackathon.id),
            "project_template_id": str(created_project_template.id)
        }
    )
    assert response.status_code == status.HTTP_201_CREATED, response.json()
    data = response.json()
    assert data["name"] == project_name
    assert str(data["project_template_id"]) == str(created_project_template.id)

    project_in_db = db_session.query(Project).filter(Project.id == uuid.UUID(data["id"])).first()
    assert project_in_db is not None
    assert str(project_in_db.project_template_id) == str(created_project_template.id)

def test_create_project_invalid_team(client: TestClient, auth_headers_for_regular_user, unique_id: uuid.UUID, test_hackathon: Hackathon):
    non_existent_team_id = uuid.uuid4()
    response = client.post(
        "/projects/",
        headers=auth_headers_for_regular_user,
        json={
            "name": f"Project Invalid Team {unique_id}",
            "hackathon_id": str(test_hackathon.id)
        }
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Team not found" in response.json()["detail"]

def test_list_projects(client: TestClient, auth_headers_for_regular_user, project_in_created_team: Project):
    response = client.get("/projects/", headers=auth_headers_for_regular_user)
    assert response.status_code == status.HTTP_200_OK
    projects = response.json()
    assert isinstance(projects, list)
    assert any(p["id"] == str(project_in_created_team.id) for p in projects)


def test_get_project(
    client: TestClient, 
    auth_headers_for_regular_user, 
    project_in_created_team: Project 
):
    response = client.get(f"/projects/{project_in_created_team.id}", headers=auth_headers_for_regular_user)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == project_in_created_team.name
    assert data["id"] == str(project_in_created_team.id)

# --- Update Project Tests ---
def test_update_project_as_team_member(
    client: TestClient, 
    auth_headers_for_regular_user, 
    project_in_created_team: Project, 
    unique_id: uuid.UUID, 
    db_session: Session
):
    updated_name = f"Updated Project by Member {unique_id}"
    updated_description = "This project has been updated by a team member."
    response = client.put(
        f"/projects/{project_in_created_team.id}",
        headers=auth_headers_for_regular_user, # regular_user is owner/member of the team
        json={"name": updated_name, "description": updated_description, "status": ProjectStatus.ACTIVE.value}
    )
    assert response.status_code == status.HTTP_200_OK, response.json()
    data = response.json()
    assert data["name"] == updated_name
    assert data["description"] == updated_description
    assert data["status"] == ProjectStatus.ACTIVE.value

    db_session.refresh(project_in_created_team) 
    assert project_in_created_team.name == updated_name
    assert project_in_created_team.description == updated_description
    assert project_in_created_team.status == ProjectStatus.ACTIVE

def test_update_project_as_admin(
    client: TestClient,
    auth_headers_for_admin_user,
    project_in_created_team: Project, # Project in team of regular_user
    unique_id: uuid.UUID,
    db_session: Session
):
    updated_name = f"Admin Updated Project {unique_id}"
    response = client.put(
        f"/projects/{project_in_created_team.id}",
        headers=auth_headers_for_admin_user,
        json={"name": updated_name, "status": ProjectStatus.COMPLETED.value}
    )
    assert response.status_code == status.HTTP_200_OK, response.json()
    data = response.json()
    assert data["name"] == updated_name
    assert data["status"] == ProjectStatus.COMPLETED.value

    db_session.refresh(project_in_created_team)
    assert project_in_created_team.name == updated_name
    assert project_in_created_team.status == ProjectStatus.COMPLETED

def test_update_project_as_non_member_non_admin(
    client: TestClient,
    auth_headers_for_second_regular_user, # Not a member of project's team
    project_in_created_team: Project, # Project in team of regular_user
    unique_id: uuid.UUID
):
    updated_name = f"Illegal Update Attempt {unique_id}"
    response = client.put(
        f"/projects/{project_in_created_team.id}",
        headers=auth_headers_for_second_regular_user,
        json={"name": updated_name}
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert "User is not a member of the project's team or an administrator." in data["detail"]

def test_update_project_member_of_different_team(
    client: TestClient,
    auth_headers_for_second_regular_user, # Member/owner of another_team
    project_in_created_team: Project, # Project in team of regular_user
    another_team_created_by_second_user: Team, # Ensures second user has their own team context
    unique_id: uuid.UUID
):
    updated_name = f"Cross Team Update Attempt {unique_id}"
    response = client.put(
        f"/projects/{project_in_created_team.id}", # Target project in created_team
        headers=auth_headers_for_second_regular_user, # User from another_team
        json={"name": updated_name}
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert "User is not a member of the project's team or an administrator." in data["detail"]


def test_update_non_existent_project(client: TestClient, auth_headers_for_admin_user, unique_id: uuid.UUID):
    non_existent_project_id = uuid.uuid4()
    response = client.put(
        f"/projects/{non_existent_project_id}",
        headers=auth_headers_for_admin_user, # Admin to bypass member checks for a project that doesn't exist
        json={"name": "Update Non Existent"}
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert "Project not found" in data["detail"]

# --- Delete Project Tests ---
def test_delete_project_as_team_owner( 
    client: TestClient, 
    auth_headers_for_regular_user, # This user is the owner of created_team (verified by created_team fixture)
    project_in_created_team: Project, 
    db_session: Session
):
    project_id_str = str(project_in_created_team.id)
    response = client.delete(f"/projects/{project_id_str}", headers=auth_headers_for_regular_user)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    project_in_db = db_session.query(Project).filter(Project.id == uuid.UUID(project_id_str)).first()
    assert project_in_db is None

def test_delete_project_as_admin(
    client: TestClient,
    auth_headers_for_admin_user,
    project_in_created_team: Project, # Project in team of regular_user
    db_session: Session
):
    project_id_str = str(project_in_created_team.id)
    response = client.delete(f"/projects/{project_id_str}", headers=auth_headers_for_admin_user)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    project_in_db = db_session.query(Project).filter(Project.id == uuid.UUID(project_id_str)).first()
    assert project_in_db is None

def test_delete_project_as_team_member_non_owner(
    client: TestClient,
    auth_headers_for_second_regular_user, 
    created_second_regular_user: User, # This user will join the team
    created_team: Team, # Team owned by regular_user
    project_in_created_team: Project, # Project in created_team, created by regular_user
    db_session: Session
):
    # second_regular_user (authenticated by auth_headers_for_second_regular_user) joins the created_team
    response_join = client.post(
        f"/teams/{created_team.id}/join",
        headers=auth_headers_for_second_regular_user 
        # No request body or role needed for /join, it defaults to 'member'
    )
    # The /join endpoint returns 204 No Content on success
    assert response_join.status_code == status.HTTP_204_NO_CONTENT, response_join.text

    # Verify second_regular_user is now a member
    member_check = db_session.query(TeamMember).filter(
        TeamMember.team_id == created_team.id,
        TeamMember.user_id == created_second_regular_user.id,
        TeamMember.role == TeamMemberRole.member # Default role for join is 'member'
    ).first()
    assert member_check is not None, "Second user failed to join team as member for the test setup."

    # Attempt delete by the non-owner member (second_regular_user)
    response_delete = client.delete(
        f"/projects/{project_in_created_team.id}",
        headers=auth_headers_for_second_regular_user
    )
    assert response_delete.status_code == status.HTTP_403_FORBIDDEN
    data = response_delete.json()
    assert "User is not an owner of the project's team or an administrator." in data["detail"]

    project_still_in_db = db_session.query(Project).filter(Project.id == project_in_created_team.id).first()
    assert project_still_in_db is not None


def test_delete_project_as_non_member_non_admin(
    client: TestClient,
    auth_headers_for_second_regular_user, # Not a member of project's team
    project_in_created_team: Project 
):
    response = client.delete(
        f"/projects/{project_in_created_team.id}",
        headers=auth_headers_for_second_regular_user
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert "User is not an owner of the project's team or an administrator." in data["detail"]


def test_delete_project_owner_of_different_team(
    client: TestClient,
    auth_headers_for_second_regular_user, # Owner of another_team
    project_in_created_team: Project, 
    another_team_created_by_second_user: Team # Ensures second user is an owner of their own team
):
    response = client.delete(
        f"/projects/{project_in_created_team.id}", # Target project in created_team
        headers=auth_headers_for_second_regular_user # User is owner, but of another_team
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert "User is not an owner of the project's team or an administrator." in data["detail"]

def test_delete_non_existent_project(client: TestClient, auth_headers_for_admin_user, unique_id: uuid.UUID):
    non_existent_project_id = uuid.uuid4()
    response = client.delete(
        f"/projects/{non_existent_project_id}",
        headers=auth_headers_for_admin_user 
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert "Project not found" in data["detail"]

# Comments about old test names have been integrated or removed as tests were updated.
# All original functionality should now be covered by more specific and descriptive tests.

# Add tests for non-leader trying to update/delete, non-member trying to get/list (if restricted)
# Add tests for invalid project_template_id

# Add tests for non-leader trying to delete, non-member trying to update/delete, etc. 

@pytest.fixture(scope="function")
def test_project(
    client: TestClient,
    db_session: Session,
    test_team: TeamModel,
    team_owner_user: UserModel,
    auth_headers_team_owner: dict,
    test_hackathon: Hackathon,
) -> ProjectModel:
    project_data = ProjectCreate(
        name="Submission Test Project",
        description="A project for submission testing",
        team_id=test_team.id,
        hackathon_id=test_hackathon.id
    )
    response = client.post(
        "/projects/",
        json=jsonable_encoder(project_data),
        headers=auth_headers_team_owner,
    )
    assert response.status_code == status.HTTP_201_CREATED
    project_id_str = response.json()["id"]
    project_uuid = UUID(project_id_str)
    return db_session.query(ProjectModel).filter(ProjectModel.id == project_uuid).first() 