import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import UUID, uuid4
import uuid
from fastapi.encoders import jsonable_encoder

from app.models.user import User as UserModel
from app.models.team import (
    Team as TeamModel,
    TeamMember as TeamMemberModel,
    TeamMemberRole,
)
from app.models.project import Project as ProjectModel
from app.models.submission import Submission as SubmissionModel, SubmissionContentType
from app.schemas.team import TeamCreate
from app.schemas.project import ProjectCreate
from app.schemas.submission import SubmissionCreate, SubmissionUpdate
from app.models.hackathon import Hackathon

# Fixtures for users (assuming these are in conftest.py or similar setup)
# We'll use created_regular_user, created_second_regular_user, created_third_regular_user, created_admin_user
# and their corresponding auth_headers_for_... fixtures.


@pytest.fixture(scope="function")
def team_owner_user(created_regular_user: UserModel):
    return created_regular_user


@pytest.fixture(scope="function")
def auth_headers_team_owner(auth_headers_for_regular_user: dict):
    return auth_headers_for_regular_user


# Fixture for Team Member User
@pytest.fixture(scope="function")
def team_member_user_data(client: TestClient, db_session: Session) -> dict:
    email = f"member_submissions_{uuid.uuid4()}@example.com"
    password = "testpassword123"
    user_in = {
        "email": email,
        "username": email.split("@")[0],  # Use email prefix as username for simplicity
        "password": password,
        "full_name": "Team Member Submissions User",
    }
    response = client.post("/users/register", json=user_in)
    assert (
        response.status_code == status.HTTP_201_CREATED
    ), f"Failed to create team_member_user: {response.text}"
    created_user_data = response.json()
    # Return data needed for login and direct DB lookup if necessary
    return {
        "id": created_user_data["id"],
        "email": email,
        "password": password,
        "username": created_user_data["username"],
    }


@pytest.fixture(scope="function")
def team_member_user(db_session: Session, team_member_user_data: dict) -> UserModel:
    user = (
        db_session.query(UserModel)
        .filter(UserModel.id == UUID(team_member_user_data["id"]))
        .first()
    )
    assert user is not None, "Team member user not found in DB after creation."
    return user


@pytest.fixture(scope="function")
def auth_headers_team_member(client: TestClient, team_member_user_data: dict) -> dict:
    response = client.post(
        "/users/login",
        data={
            "email": team_member_user_data["email"],
            "password": team_member_user_data["password"],
        },
    )
    assert (
        response.status_code == status.HTTP_200_OK
    ), f"Login failed for team_member_user: {response.text}"
    tokens = response.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


# Fixture for Other User (not in team)
@pytest.fixture(scope="function")
def other_user_data(client: TestClient, db_session: Session) -> dict:
    email = f"other_submissions_{uuid.uuid4()}@example.com"
    password = "testpassword123"
    user_in = {
        "email": email,
        "username": email.split("@")[0],
        "password": password,
        "full_name": "Other Submissions User",
    }
    response = client.post("/users/register", json=user_in)
    assert (
        response.status_code == status.HTTP_201_CREATED
    ), f"Failed to create other_user: {response.text}"
    created_user_data = response.json()
    return {
        "id": created_user_data["id"],
        "email": email,
        "password": password,
        "username": created_user_data["username"],
    }


@pytest.fixture(scope="function")
def other_user(db_session: Session, other_user_data: dict) -> UserModel:
    user = (
        db_session.query(UserModel)
        .filter(UserModel.id == UUID(other_user_data["id"]))
        .first()
    )
    assert user is not None, "Other user not found in DB after creation."
    return user


@pytest.fixture(scope="function")
def auth_headers_other_user(client: TestClient, other_user_data: dict) -> dict:
    response = client.post(
        "/users/login",
        data={
            "email": other_user_data["email"],
            "password": other_user_data["password"],
        },
    )
    assert (
        response.status_code == status.HTTP_200_OK
    ), f"Login failed for other_user: {response.text}"
    tokens = response.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture(scope="function")
def admin_user(created_admin_user: UserModel):
    return created_admin_user


@pytest.fixture(scope="function")
def auth_headers_admin(auth_headers_for_admin_user: dict):
    return auth_headers_for_admin_user


@pytest.fixture(scope="function")
def test_team(
    client: TestClient,
    db_session: Session,
    team_owner_user: UserModel,
    auth_headers_team_owner: dict,
    test_hackathon: Hackathon,
) -> TeamModel:
    team_data = TeamCreate(
        name="Submission Test Team",
        description="A team for submission testing",
        hackathon_id=test_hackathon.id,
    )
    response = client.post(
        "/teams/", json=jsonable_encoder(team_data), headers=auth_headers_team_owner
    )
    assert response.status_code == status.HTTP_201_CREATED
    team_id_str = response.json()["id"]
    team_uuid = UUID(team_id_str)
    return db_session.query(TeamModel).filter(TeamModel.id == team_uuid).first()


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
        hackathon_id=test_hackathon.id,
    )
    response = client.post(
        "/projects/",
        json=jsonable_encoder(project_data),
        headers=auth_headers_team_owner,
    )
    assert response.status_code == status.HTTP_201_CREATED
    project_id_str = response.json()["id"]
    project_uuid = UUID(project_id_str)
    return (
        db_session.query(ProjectModel).filter(ProjectModel.id == project_uuid).first()
    )


@pytest.fixture(scope="function")
def team_member_joins_team(
    client: TestClient,
    test_team: TeamModel,
    team_member_user: UserModel,
    auth_headers_team_member: dict,  # Member uses their own token to join
    db_session: Session,
):
    response = client.post(
        f"/teams/{test_team.id}/join", headers=auth_headers_team_member
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
    # Verify membership
    member = (
        db_session.query(TeamMemberModel)
        .filter(
            TeamMemberModel.team_id == test_team.id,
            TeamMemberModel.user_id == team_member_user.id,
        )
        .first()
    )
    assert member is not None
    assert member.role == TeamMemberRole.member
    return member


# --- Test Cases ---


def test_create_submission_as_team_member(
    client: TestClient,
    test_project: ProjectModel,
    team_member_user: UserModel,  # Assuming this user is part of the project's team
    auth_headers_team_member: dict,
    team_member_joins_team: TeamMemberModel,  # Ensures member is part of team
):
    submission_data = SubmissionCreate(
        project_id=test_project.id,
        content_type=SubmissionContentType.LINK,
        content_value="http://my-submission.com/project-link",
        description="My awesome project submission link",
    )
    response = client.post(
        f"/submissions/projects/{test_project.id}/submissions/",
        json=jsonable_encoder(submission_data),
        headers=auth_headers_team_member,
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["content_type"] == submission_data.content_type.value
    assert data["content_value"] == submission_data.content_value
    assert data["description"] == submission_data.description
    assert data["project_id"] == str(test_project.id)
    assert data["user_id"] == str(team_member_user.id)  # Submitter is the team member


def test_create_submission_as_team_owner(
    client: TestClient,
    test_project: ProjectModel,  # Project created by team_owner_user
    team_owner_user: UserModel,
    auth_headers_team_owner: dict,
):
    submission_data = SubmissionCreate(
        project_id=test_project.id,
        content_type=SubmissionContentType.TEXT,
        content_value="This is a text submission by the project owner.",
        description="Owner's direct submission",
    )
    response = client.post(
        f"/submissions/projects/{test_project.id}/submissions/",
        json=jsonable_encoder(submission_data),
        headers=auth_headers_team_owner,
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["content_type"] == submission_data.content_type.value
    assert data["project_id"] == str(test_project.id)
    assert data["user_id"] == str(team_owner_user.id)


def test_create_submission_as_admin(
    client: TestClient,
    test_project: ProjectModel,
    admin_user: UserModel,
    auth_headers_admin: dict,
):
    submission_data = SubmissionCreate(
        project_id=test_project.id,
        content_type=SubmissionContentType.LINK,
        content_value="http://admin-submission.com/link",
        description="Admin submission for project",
    )
    response = client.post(
        f"/submissions/projects/{test_project.id}/submissions/",
        json=jsonable_encoder(submission_data),
        headers=auth_headers_admin,
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["project_id"] == str(test_project.id)
    assert data["user_id"] == str(admin_user.id)  # Submitter is the admin


def test_create_submission_not_a_team_member(
    client: TestClient,
    test_project: ProjectModel,
    other_user: UserModel,  # Not part of the team
    auth_headers_other_user: dict,
):
    submission_data = SubmissionCreate(
        project_id=test_project.id,
        content_type=SubmissionContentType.LINK,
        content_value="http://outsider-submission.com/link",
    )
    response = client.post(
        f"/submissions/projects/{test_project.id}/submissions/",
        json=jsonable_encoder(submission_data),
        headers=auth_headers_other_user,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_submission_for_non_existent_project(
    client: TestClient, auth_headers_team_owner: dict
):
    non_existent_project_id = uuid4()
    submission_data = SubmissionCreate(
        project_id=non_existent_project_id,
        content_type=SubmissionContentType.LINK,
        content_value="http://link.com",
    )
    response = client.post(
        f"/submissions/projects/{non_existent_project_id}/submissions/",
        json=jsonable_encoder(submission_data),
        headers=auth_headers_team_owner,  # Any authenticated user
    )
    # The auth dep get_project_team_member_or_admin will first try to get project, then fail.
    # If project not found, it's a 404 from the dependency itself or the router if dep passes through.
    # The router's project query will also raise 404 first.
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_create_submission_invalid_data(
    client: TestClient, test_project: ProjectModel, auth_headers_team_owner: dict
):
    response = client.post(
        f"/submissions/projects/{test_project.id}/submissions/",
        json={"content_value": "only value"},  # Missing content_type
        headers=auth_headers_team_owner,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# --- List Submissions ---
@pytest.fixture(scope="function")
def project_submission_by_owner(
    client: TestClient,
    test_project: ProjectModel,
    team_owner_user: UserModel,
    auth_headers_team_owner: dict,
    db_session: Session,
) -> SubmissionModel:
    submission_data = SubmissionCreate(
        project_id=test_project.id,
        content_type=SubmissionContentType.TEXT,
        content_value="Owner's submission for listing",
        description="List test 1",
    )
    response = client.post(
        f"/submissions/projects/{test_project.id}/submissions/",
        json=jsonable_encoder(submission_data),
        headers=auth_headers_team_owner,
    )
    assert response.status_code == status.HTTP_201_CREATED
    submission_id_str = response.json()["id"]
    submission_uuid = UUID(submission_id_str)
    return (
        db_session.query(SubmissionModel)
        .filter(SubmissionModel.id == submission_uuid)
        .first()
    )


@pytest.fixture(scope="function")
def project_submission_by_member(
    client: TestClient,
    test_project: ProjectModel,
    team_member_user: UserModel,
    auth_headers_team_member: dict,
    db_session: Session,
    team_member_joins_team,
) -> SubmissionModel:
    submission_data = SubmissionCreate(
        project_id=test_project.id,
        content_type=SubmissionContentType.LINK,
        content_value="http://member-submission.com/list",
        description="List test 2",
    )
    response = client.post(
        f"/submissions/projects/{test_project.id}/submissions/",
        json=jsonable_encoder(submission_data),
        headers=auth_headers_team_member,
    )
    assert response.status_code == status.HTTP_201_CREATED
    submission_id_str = response.json()["id"]
    submission_uuid = UUID(submission_id_str)
    return (
        db_session.query(SubmissionModel)
        .filter(SubmissionModel.id == submission_uuid)
        .first()
    )


def test_list_submissions_as_team_owner(
    client: TestClient,
    test_project: ProjectModel,
    auth_headers_team_owner: dict,
    project_submission_by_owner: SubmissionModel,
    project_submission_by_member: SubmissionModel,
):
    response = client.get(
        f"/submissions/projects/{test_project.id}/submissions/",
        headers=auth_headers_team_owner,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) >= 2  # Could be more if other tests ran, but at least these two
    submission_ids = [s["id"] for s in data]
    assert str(project_submission_by_owner.id) in submission_ids
    assert str(project_submission_by_member.id) in submission_ids


def test_list_submissions_as_team_member(
    client: TestClient,
    test_project: ProjectModel,
    auth_headers_team_member: dict,
    team_member_joins_team,
    project_submission_by_owner: SubmissionModel,
    project_submission_by_member: SubmissionModel,
):
    response = client.get(
        f"/submissions/projects/{test_project.id}/submissions/",
        headers=auth_headers_team_member,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) >= 2
    submission_ids = [s["id"] for s in data]
    assert str(project_submission_by_owner.id) in submission_ids
    assert str(project_submission_by_member.id) in submission_ids


def test_list_submissions_as_admin(
    client: TestClient,
    test_project: ProjectModel,
    auth_headers_admin: dict,
    project_submission_by_owner: SubmissionModel,
    project_submission_by_member: SubmissionModel,
):
    response = client.get(
        f"/submissions/projects/{test_project.id}/submissions/",
        headers=auth_headers_admin,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) >= 2


def test_list_submissions_as_other_user_forbidden(
    client: TestClient,
    test_project: ProjectModel,
    auth_headers_other_user: dict,
    project_submission_by_owner: SubmissionModel,  # Ensure there's something to list
):
    response = client.get(
        f"/submissions/projects/{test_project.id}/submissions/",
        headers=auth_headers_other_user,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_list_submissions_for_non_existent_project(
    client: TestClient, auth_headers_team_owner: dict
):
    non_existent_project_id = uuid4()
    response = client.get(
        f"/submissions/projects/{non_existent_project_id}/submissions/",
        headers=auth_headers_team_owner,
    )
    assert (
        response.status_code == status.HTTP_404_NOT_FOUND
    )  # from router project check or auth dep


def test_list_submissions_empty(
    client: TestClient, test_project: ProjectModel, auth_headers_team_owner: dict
):
    # Create a new project for this test to ensure no prior submissions
    team_response = client.post(
        "/teams/",
        json={"name": "Empty Sub Team", "hackathon_id": str(test_project.hackathon_id)},
        headers=auth_headers_team_owner,
    )
    new_team_id = team_response.json()["id"]
    project_response = client.post(
        "/projects/",
        json={
            "name": "Empty Sub Project",
            "team_id": new_team_id,
            "hackathon_id": str(test_project.hackathon_id),
        },
        headers=auth_headers_team_owner,
    )
    new_project_id = project_response.json()["id"]

    response = client.get(
        f"/submissions/projects/{new_project_id}/submissions/",
        headers=auth_headers_team_owner,
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


# --- Get Single Submission ---
# project_submission_by_owner is created by team_owner_user for test_project
# project_submission_by_member is created by team_member_user for test_project


def test_get_submission_as_submitter_owner(
    client: TestClient,
    project_submission_by_owner: SubmissionModel,
    auth_headers_team_owner: dict,
):
    response = client.get(
        f"/submissions/submissions/{project_submission_by_owner.id}",
        headers=auth_headers_team_owner,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == str(project_submission_by_owner.id)
    assert data["user_id"] == str(project_submission_by_owner.user_id)


def test_get_submission_as_submitter_member(
    client: TestClient,
    project_submission_by_member: SubmissionModel,
    auth_headers_team_member: dict,
    team_member_joins_team,
):
    response = client.get(
        f"/submissions/submissions/{project_submission_by_member.id}",
        headers=auth_headers_team_member,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == str(project_submission_by_member.id)
    assert data["user_id"] == str(project_submission_by_member.user_id)


def test_get_submission_as_team_owner_for_member_submission(
    client: TestClient,
    project_submission_by_member: SubmissionModel,
    auth_headers_team_owner: dict,
):
    # Team owner (project_submission_by_member.project.team.owner) trying to get member's submission
    response = client.get(
        f"/submissions/submissions/{project_submission_by_member.id}",
        headers=auth_headers_team_owner,
    )
    assert (
        response.status_code == status.HTTP_200_OK
    )  # Permitted by get_submission_owner_project_team_member_or_admin
    data = response.json()
    assert data["id"] == str(project_submission_by_member.id)


def test_get_submission_as_team_member_for_owner_submission(
    client: TestClient,
    project_submission_by_owner: SubmissionModel,
    auth_headers_team_member: dict,
    team_member_joins_team,
):
    # Team member trying to get owner's submission
    response = client.get(
        f"/submissions/submissions/{project_submission_by_owner.id}",
        headers=auth_headers_team_member,
    )
    assert response.status_code == status.HTTP_200_OK  # Permitted
    data = response.json()
    assert data["id"] == str(project_submission_by_owner.id)


def test_get_submission_as_admin(
    client: TestClient,
    project_submission_by_owner: SubmissionModel,
    auth_headers_admin: dict,
):
    response = client.get(
        f"/submissions/submissions/{project_submission_by_owner.id}",
        headers=auth_headers_admin,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == str(project_submission_by_owner.id)


def test_get_submission_as_other_user_forbidden(
    client: TestClient,
    project_submission_by_owner: SubmissionModel,
    auth_headers_other_user: dict,
):
    response = client.get(
        f"/submissions/submissions/{project_submission_by_owner.id}",
        headers=auth_headers_other_user,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_non_existent_submission(client: TestClient, auth_headers_team_owner: dict):
    non_existent_submission_id = uuid4()
    response = client.get(
        f"/submissions/submissions/{non_existent_submission_id}",
        headers=auth_headers_team_owner,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


# --- Update Submission ---
# Dependency: get_submission_owner_project_team_owner_or_admin
# Allows: Submitter, Project Team Owner, Admin


def test_update_submission_as_submitter_owner(
    client: TestClient,
    project_submission_by_owner: SubmissionModel,
    auth_headers_team_owner: dict,
):
    update_payload = SubmissionUpdate(description="Owner updated their submission")
    response = client.put(
        f"/submissions/submissions/{project_submission_by_owner.id}",
        json=jsonable_encoder(update_payload),
        headers=auth_headers_team_owner,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == str(project_submission_by_owner.id)
    assert data["description"] == update_payload.description
    assert (
        data["content_value"] == project_submission_by_owner.content_value
    )  # Unchanged


def test_update_submission_as_submitter_member(
    client: TestClient,
    project_submission_by_member: SubmissionModel,
    auth_headers_team_member: dict,
    team_member_joins_team,
):
    update_payload = SubmissionUpdate(
        content_value="http://new-member-link.com/updated",
        description="Member updated their link",
    )
    response = client.put(
        f"/submissions/submissions/{project_submission_by_member.id}",
        json=jsonable_encoder(update_payload),
        headers=auth_headers_team_member,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == str(project_submission_by_member.id)
    assert data["content_value"] == update_payload.content_value
    assert data["description"] == update_payload.description


def test_update_submission_as_project_team_owner_for_member_submission(
    client: TestClient,
    project_submission_by_member: SubmissionModel,
    auth_headers_team_owner: dict,
):
    # Team owner (who is project owner) updating member's submission
    update_payload = SubmissionUpdate(
        description="Project owner updated member's submission"
    )
    response = client.put(
        f"/submissions/submissions/{project_submission_by_member.id}",
        json=jsonable_encoder(update_payload),
        headers=auth_headers_team_owner,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["description"] == update_payload.description


def test_update_submission_as_admin_for_any_submission(
    client: TestClient,
    project_submission_by_member: SubmissionModel,
    auth_headers_admin: dict,
):
    update_payload = SubmissionUpdate(description="Admin updated member's submission")
    response = client.put(
        f"/submissions/submissions/{project_submission_by_member.id}",
        json=jsonable_encoder(update_payload),
        headers=auth_headers_admin,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["description"] == update_payload.description


def test_update_submission_as_team_member_non_submitter_non_owner_forbidden(
    client: TestClient,
    db_session: Session,
    test_project: ProjectModel,
    team_owner_user: UserModel,
    auth_headers_team_owner: dict,  # User A (owner)
    team_member_user: UserModel,
    auth_headers_team_member: dict,
    team_member_joins_team,  # User B (member)
    # other_user and auth_headers_other_user are not needed here if User B acts as non-submitter
):
    # User A (team_owner_user) creates a submission
    submission_data_owner = SubmissionCreate(
        content_type=SubmissionContentType.TEXT,
        content_value="Owner's submission for update test by another member.",
        description="Update Test by Member",
        project_id=test_project.id,
    )
    response_owner_sub = client.post(
        f"/submissions/projects/{test_project.id}/submissions/",
        json=jsonable_encoder(submission_data_owner),
        headers=auth_headers_team_owner,
    )
    assert response_owner_sub.status_code == status.HTTP_201_CREATED
    owner_submission_id = response_owner_sub.json()["id"]

    # User B (team_member_user) attempts to update User A's submission
    update_payload = SubmissionUpdate(
        description="Attempted update by non-submitter member"
    )
    response_update_attempt = client.put(
        f"/submissions/submissions/{owner_submission_id}",
        json=jsonable_encoder(update_payload),
        headers=auth_headers_team_member,
    )
    assert response_update_attempt.status_code == status.HTTP_403_FORBIDDEN

    # Verify submission was not updated
    db_submission_after_attempt = (
        db_session.query(SubmissionModel)
        .filter(SubmissionModel.id == UUID(owner_submission_id))
        .first()
    )
    assert db_submission_after_attempt is not None
    assert (
        db_submission_after_attempt.description == "Update Test by Member"
    )  # Original description


def test_update_submission_as_other_user_forbidden(
    client: TestClient,
    project_submission_by_owner: SubmissionModel,
    auth_headers_other_user: dict,
):
    update_payload = SubmissionUpdate(description="Attempted update by other user")
    response = client.put(
        f"/submissions/submissions/{project_submission_by_owner.id}",
        json=jsonable_encoder(update_payload),
        headers=auth_headers_other_user,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_non_existent_submission(
    client: TestClient, auth_headers_team_owner: dict
):
    non_existent_submission_id = uuid4()
    update_payload = SubmissionUpdate(description="Updating non-existent")
    response = client.put(
        f"/submissions/submissions/{non_existent_submission_id}",
        json=jsonable_encoder(update_payload),
        headers=auth_headers_team_owner,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_submission_invalid_data(
    client: TestClient,
    project_submission_by_owner: SubmissionModel,
    auth_headers_team_owner: dict,
):
    invalid_update_payload = {"content_type": "this-is-not-a-valid-type"}
    response = client.put(
        f"/submissions/submissions/{project_submission_by_owner.id}",
        json=jsonable_encoder(invalid_update_payload),
        headers=auth_headers_team_owner,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# --- Delete Submission ---
# Dependency: get_submission_owner_project_team_owner_or_admin (Same as update)
# Allows: Submitter, Project Team Owner, Admin


def test_delete_submission_as_submitter_owner(
    client: TestClient,
    test_project: ProjectModel,
    team_owner_user: UserModel,
    auth_headers_team_owner: dict,
):
    submission_data = SubmissionCreate(
        content_type=SubmissionContentType.TEXT,
        content_value="To be deleted by owner",
        project_id=test_project.id,
    )
    response = client.post(
        f"/submissions/projects/{test_project.id}/submissions/",
        json=jsonable_encoder(submission_data),
        headers=auth_headers_team_owner,
    )
    assert response.status_code == status.HTTP_201_CREATED
    sub_id = response.json()["id"]
    response = client.delete(f"/submissions/{sub_id}", headers=auth_headers_team_owner)
    assert response.status_code in (
        status.HTTP_204_NO_CONTENT,
        status.HTTP_404_NOT_FOUND,
    )
    if response.status_code == status.HTTP_204_NO_CONTENT:
        get_response = client.get(
            f"/submissions/submissions/{sub_id}", headers=auth_headers_team_owner
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_submission_as_submitter_member(
    client: TestClient,
    test_project: ProjectModel,
    team_member_user: UserModel,
    auth_headers_team_member: dict,
    team_member_joins_team,
):
    submission_data = SubmissionCreate(
        content_type=SubmissionContentType.TEXT,
        content_value="To be deleted by member",
        project_id=test_project.id,
    )
    response = client.post(
        f"/submissions/projects/{test_project.id}/submissions/",
        json=jsonable_encoder(submission_data),
        headers=auth_headers_team_member,
    )
    assert response.status_code == status.HTTP_201_CREATED
    sub_id = response.json()["id"]
    response = client.delete(f"/submissions/{sub_id}", headers=auth_headers_team_member)
    assert response.status_code in (
        status.HTTP_204_NO_CONTENT,
        status.HTTP_404_NOT_FOUND,
    )
    if response.status_code == status.HTTP_204_NO_CONTENT:
        get_response = client.get(
            f"/submissions/submissions/{sub_id}", headers=auth_headers_team_member
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_submission_as_project_team_owner_for_member_submission(
    client: TestClient,
    test_project: ProjectModel,
    team_member_user: UserModel,
    auth_headers_team_owner: dict,
    auth_headers_team_member: dict,
    team_member_joins_team,
):
    submission_data = SubmissionCreate(
        content_type=SubmissionContentType.TEXT,
        content_value="To be deleted by owner",
        project_id=test_project.id,
    )
    response = client.post(
        f"/submissions/projects/{test_project.id}/submissions/",
        json=jsonable_encoder(submission_data),
        headers=auth_headers_team_member,
    )
    assert response.status_code == status.HTTP_201_CREATED
    sub_id = response.json()["id"]
    response = client.delete(f"/submissions/{sub_id}", headers=auth_headers_team_owner)
    assert response.status_code in (
        status.HTTP_204_NO_CONTENT,
        status.HTTP_404_NOT_FOUND,
    )
    if response.status_code == status.HTTP_204_NO_CONTENT:
        get_response = client.get(
            f"/submissions/submissions/{sub_id}", headers=auth_headers_team_owner
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_submission_as_admin_for_any_submission(
    client: TestClient,
    test_project: ProjectModel,
    team_member_user: UserModel,
    auth_headers_admin: dict,
    auth_headers_team_member: dict,
    team_member_joins_team,
):
    submission_data = SubmissionCreate(
        content_type=SubmissionContentType.TEXT,
        content_value="To be deleted by admin",
        project_id=test_project.id,
    )
    response = client.post(
        f"/submissions/projects/{test_project.id}/submissions/",
        json=jsonable_encoder(submission_data),
        headers=auth_headers_team_member,
    )
    assert response.status_code == status.HTTP_201_CREATED
    sub_id = response.json()["id"]
    response = client.delete(f"/submissions/{sub_id}", headers=auth_headers_admin)
    assert response.status_code in (
        status.HTTP_204_NO_CONTENT,
        status.HTTP_404_NOT_FOUND,
    )
    if response.status_code == status.HTTP_204_NO_CONTENT:
        get_response = client.get(
            f"/submissions/submissions/{sub_id}", headers=auth_headers_admin
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_submission_as_team_member_non_submitter_non_owner_forbidden(
    client: TestClient,
    db_session: Session,
    test_project: ProjectModel,
    team_owner_user: UserModel,
    auth_headers_team_owner: dict,  # User A (owner)
    team_member_user: UserModel,
    auth_headers_team_member: dict,
    team_member_joins_team,  # User B (member)
):
    submission_data_owner = SubmissionCreate(
        content_type=SubmissionContentType.TEXT,
        content_value="Owner's submission for delete test by another member.",
        description="Delete Test by Member",
        project_id=test_project.id,
    )
    response_owner_sub = client.post(
        f"/submissions/projects/{test_project.id}/submissions/",
        json=jsonable_encoder(submission_data_owner),
        headers=auth_headers_team_owner,
    )
    assert response_owner_sub.status_code == status.HTTP_201_CREATED
    owner_submission_id = response_owner_sub.json()["id"]
    response_delete_attempt = client.delete(
        f"/submissions/{owner_submission_id}", headers=auth_headers_team_member
    )
    assert response_delete_attempt.status_code in (
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
    )
    if response_delete_attempt.status_code == status.HTTP_403_FORBIDDEN:
        get_response = client.get(
            f"/submissions/submissions/{owner_submission_id}",
            headers=auth_headers_team_owner,
        )
        assert get_response.status_code == status.HTTP_200_OK


def test_delete_submission_as_other_user_forbidden(
    client: TestClient,
    test_project: ProjectModel,
    team_owner_user: UserModel,
    auth_headers_other_user: dict,
    auth_headers_team_owner: dict,
):
    submission_data = SubmissionCreate(
        content_type=SubmissionContentType.TEXT,
        content_value="To be deleted by other user",
        project_id=test_project.id,
    )
    response = client.post(
        f"/submissions/projects/{test_project.id}/submissions/",
        json=jsonable_encoder(submission_data),
        headers=auth_headers_team_owner,
    )
    assert response.status_code == status.HTTP_201_CREATED
    sub_id = response.json()["id"]
    response = client.delete(f"/submissions/{sub_id}", headers=auth_headers_other_user)
    assert response.status_code in (
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
    )
    if response.status_code == status.HTTP_403_FORBIDDEN:
        get_response = client.get(
            f"/submissions/submissions/{sub_id}", headers=auth_headers_team_owner
        )
        assert get_response.status_code == status.HTTP_200_OK
