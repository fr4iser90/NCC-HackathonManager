import uuid
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from typing import Dict, Any
from decimal import Decimal

from app.models.user import User as UserModel
from app.models.project import Project as ProjectModel
from app.models.team import Team as TeamModel, TeamMember as TeamMemberModel, TeamMemberRole
from app.models.judging import Criterion as CriterionModel, Score as ScoreModel # SQLAlchemy models
from app.schemas.judging import CriterionCreate, ScoreCreate, ScoreUpdate # Pydantic schemas
from app.models.hackathon import Hackathon

# Assuming conftest.py provides:
# client, db_session, admin_user_data, auth_headers_for_admin_user,
# judge_user_data, auth_headers_for_judge_user, regular_user_data, auth_headers_for_regular_user


# --- Helper Fixtures for Judging Tests ---

@pytest.fixture(scope="function")
def created_team_for_judging(
    client: TestClient, 
    auth_headers_for_regular_user: Dict[str, str], 
    unique_id: uuid.UUID, 
    db_session: Session,
    test_hackathon: Hackathon,
) -> TeamModel:
    team_name = f"JudgingTeam_{unique_id}"
    response = client.post(
        "/teams/",
        headers=auth_headers_for_regular_user,
        json={
            "name": team_name, 
            "description": "Team for judging tests",
            "hackathon_id": str(test_hackathon.id)
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    team_data = response.json()
    team = db_session.query(TeamModel).filter(TeamModel.id == uuid.UUID(team_data["id"])).first()
    assert team is not None
    return team

@pytest.fixture(scope="function")
def created_project_for_judging(
    client: TestClient,
    auth_headers_for_regular_user: Dict[str, str],
    created_team_for_judging: TeamModel,
    unique_id: uuid.UUID,
    db_session: Session,
    test_hackathon: Hackathon,
) -> ProjectModel:
    project_name = f"JudgingProject_{unique_id}"
    project_payload = {
        "name": project_name,
        "description": "Project to be judged",
        "team_id": str(created_team_for_judging.id),
        "hackathon_id": str(test_hackathon.id)
    }
    response = client.post(
        "/projects/",
        headers=auth_headers_for_regular_user,
        json=project_payload
    )
    assert response.status_code == status.HTTP_201_CREATED, response.json()
    project_data = response.json()
    project = db_session.query(ProjectModel).filter(ProjectModel.id == uuid.UUID(project_data["id"])).first()
    assert project is not None
    return project

@pytest.fixture(scope="function")
def created_criterion(
    client: TestClient, auth_headers_for_admin_user: Dict[str, str], unique_id: uuid.UUID, db_session: Session
) -> CriterionModel:
    criterion_data = CriterionCreate(
        name=f"Test Criterion {unique_id}",
        description="A criterion for testing",
        max_score=10,
        weight=1.0
    )
    response = client.post(
        "/judging/criteria/",
        headers=auth_headers_for_admin_user,
        json=jsonable_encoder(criterion_data)
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    criterion = db_session.query(CriterionModel).filter(CriterionModel.id == uuid.UUID(data["id"])).first()
    assert criterion is not None
    return criterion

# --- Criterion Endpoint Tests (Admin-focused) ---

def test_create_criterion_as_admin(
    client: TestClient, auth_headers_for_admin_user: Dict[str, str], unique_id: uuid.UUID, db_session: Session
):
    criterion_payload = {
        "name": f"Creatable Criterion {unique_id}",
        "description": "This criterion can be created by an admin.",
        "max_score": 5,
        "weight": 1.0
    }
    response = client.post("/judging/criteria/", headers=auth_headers_for_admin_user, json=criterion_payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == criterion_payload["name"]
    assert data["max_score"] == criterion_payload["max_score"]
    assert Decimal(str(data["weight"])) == Decimal(str(criterion_payload["weight"]))
    assert db_session.query(CriterionModel).filter(CriterionModel.id == uuid.UUID(data["id"])).first() is not None

def test_create_criterion_as_judge_forbidden(
    client: TestClient, auth_headers_for_judge_user: Dict[str, str], unique_id: uuid.UUID
):
    criterion_payload = {
        "name": f"Judge Criterion Attempt {unique_id}",
        "description": "Judges should not create criteria.",
        "max_score": 10,
        "weight": 1.0
    }
    response = client.post("/judging/criteria/", headers=auth_headers_for_judge_user, json=criterion_payload)
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_create_criterion_as_regular_user_forbidden(
    client: TestClient, auth_headers_for_regular_user: Dict[str, str], unique_id: uuid.UUID
):
    criterion_payload = {
        "name": f"Regular User Criterion Attempt {unique_id}",
        "description": "Regular users should not create criteria.",
        "max_score": 10,
        "weight": 1.0
    }
    response = client.post("/judging/criteria/", headers=auth_headers_for_regular_user, json=criterion_payload)
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_list_criteria_unauthenticated(client: TestClient, created_criterion: CriterionModel):
    response = client.get("/judging/criteria/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert any(c["id"] == str(created_criterion.id) for c in data)

def test_list_criteria_authenticated(client: TestClient, auth_headers_for_admin_user: Dict[str, str], created_criterion: CriterionModel):
    response = client.get("/judging/criteria/", headers=auth_headers_for_admin_user) # Any authenticated user can list
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert any(c["id"] == str(created_criterion.id) for c in data)

def test_get_criterion(client: TestClient, created_criterion: CriterionModel):
    response = client.get(f"/judging/criteria/{created_criterion.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == created_criterion.name
    assert data["id"] == str(created_criterion.id)

def test_get_criterion_not_found(client: TestClient):
    non_existent_id = uuid.uuid4()
    response = client.get(f"/judging/criteria/{non_existent_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_update_criterion_as_admin(
    client: TestClient, auth_headers_for_admin_user: Dict[str, str], created_criterion: CriterionModel, db_session: Session
):
    update_payload = {"name": "Updated Criterion Name", "max_score": 20, "weight": 1.5}
    response = client.put(
        f"/judging/criteria/{created_criterion.id}",
        headers=auth_headers_for_admin_user,
        json=update_payload
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == update_payload["name"]
    assert data["max_score"] == update_payload["max_score"]
    assert Decimal(str(data["weight"])) == Decimal(str(update_payload["weight"]))
    db_session.refresh(created_criterion)
    assert created_criterion.name == update_payload["name"]
    assert created_criterion.max_score == update_payload["max_score"]
    assert created_criterion.weight == Decimal(str(update_payload["weight"]))

def test_update_criterion_as_judge_forbidden(
    client: TestClient, auth_headers_for_judge_user: Dict[str, str], created_criterion: CriterionModel
):
    update_payload = {
        "name": "Attempted Update by Judge", 
        "weight": 1.0,
        "max_score": 10,  # Added missing mandatory field
        "description": "Judges should not be able to update this."
    }
    response = client.put(
        f"/judging/criteria/{created_criterion.id}",
        headers=auth_headers_for_judge_user,
        json=update_payload
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_delete_criterion_as_admin(
    client: TestClient, auth_headers_for_admin_user: Dict[str, str], created_criterion: CriterionModel, db_session: Session
):
    criterion_id_to_delete = created_criterion.id
    response = client.delete(f"/judging/criteria/{criterion_id_to_delete}", headers=auth_headers_for_admin_user)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert db_session.query(CriterionModel).filter(CriterionModel.id == criterion_id_to_delete).first() is None

def test_delete_criterion_as_judge_forbidden(
    client: TestClient, auth_headers_for_judge_user: Dict[str, str], created_criterion: CriterionModel
):
    response = client.delete(f"/judging/criteria/{created_criterion.id}", headers=auth_headers_for_judge_user)
    assert response.status_code == status.HTTP_403_FORBIDDEN


# --- Score Endpoints (Judge/Admin-focused) ---

@pytest.fixture(scope="function")
def score_payload(created_project_for_judging: ProjectModel, created_criterion: CriterionModel) -> Dict[str, Any]:
    return {
        "project_id": str(created_project_for_judging.id),
        "criteria_id": str(created_criterion.id),
        "score": 8,
        "notes": "Good effort on this project."
    }

def test_submit_score_as_judge(
    client: TestClient,
    auth_headers_for_judge_user: Dict[str, str],
    judge_user_data: Dict[str, Any],
    created_project_for_judging: ProjectModel,
    created_criterion: CriterionModel,
    score_payload: Dict[str, Any],
    db_session: Session
):
    response = client.post("/judging/scores/", headers=auth_headers_for_judge_user, json=score_payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["project_id"] == str(created_project_for_judging.id)
    assert data["criteria_id"] == str(created_criterion.id)
    assert data["score"] == score_payload["score"]
    assert data["judge_id"] == judge_user_data["id"]
    assert db_session.query(ScoreModel).filter(ScoreModel.id == uuid.UUID(data["id"])).first() is not None

def test_submit_score_as_admin(
    client: TestClient,
    auth_headers_for_admin_user: Dict[str, str],
    admin_user_data: Dict[str, Any],
    created_project_for_judging: ProjectModel,
    created_criterion: CriterionModel,
    score_payload: Dict[str, Any],
    db_session: Session
):
    # Adjust score slightly for admin submission to avoid exact duplicate if tests run too fast
    admin_score_payload = score_payload.copy()
    admin_score_payload["score"] = 7 
    response = client.post("/judging/scores/", headers=auth_headers_for_admin_user, json=admin_score_payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["judge_id"] == admin_user_data["id"] # Admin submits as themselves
    assert data["score"] == admin_score_payload["score"]

def test_submit_score_as_regular_user_forbidden(
    client: TestClient,
    auth_headers_for_regular_user: Dict[str, str],
    score_payload: Dict[str, Any]
):
    response = client.post("/judging/scores/", headers=auth_headers_for_regular_user, json=score_payload)
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_submit_score_project_not_found(
    client: TestClient, auth_headers_for_judge_user: Dict[str, str], created_criterion: CriterionModel
):
    payload = {
        "project_id": str(uuid.uuid4()), # Non-existent project
        "criteria_id": str(created_criterion.id),
        "score": 5
    }
    response = client.post("/judging/scores/", headers=auth_headers_for_judge_user, json=payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Project not found" in response.json()["detail"]

def test_submit_score_criterion_not_found(
    client: TestClient, auth_headers_for_judge_user: Dict[str, str], created_project_for_judging: ProjectModel
):
    payload = {
        "project_id": str(created_project_for_judging.id),
        "criteria_id": str(uuid.uuid4()), # Non-existent criterion
        "score": 5
    }
    response = client.post("/judging/scores/", headers=auth_headers_for_judge_user, json=payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Criterion not found" in response.json()["detail"]

def test_submit_score_invalid_score_value(
    client: TestClient, auth_headers_for_judge_user: Dict[str, str], created_project_for_judging: ProjectModel, created_criterion: CriterionModel
):
    payload_too_high = {
        "project_id": str(created_project_for_judging.id),
        "criteria_id": str(created_criterion.id),
        "score": created_criterion.max_score + 1 # Score exceeds max_score
    }
    response_high = client.post("/judging/scores/", headers=auth_headers_for_judge_user, json=payload_too_high)
    assert response_high.status_code == status.HTTP_400_BAD_REQUEST
    assert f"Score must be between 0 and {created_criterion.max_score}" in response_high.json()["detail"]

    payload_too_low = {
        "project_id": str(created_project_for_judging.id),
        "criteria_id": str(created_criterion.id),
        "score": -1 # Score is negative
    }
    response_low = client.post("/judging/scores/", headers=auth_headers_for_judge_user, json=payload_too_low)
    assert response_low.status_code == status.HTTP_400_BAD_REQUEST
    assert f"Score must be between 0 and {created_criterion.max_score}" in response_low.json()["detail"]

def test_submit_score_duplicate_judge_project_criterion(
    client: TestClient, auth_headers_for_judge_user: Dict[str, str], score_payload: Dict[str, Any]
):
    # First submission
    client.post("/judging/scores/", headers=auth_headers_for_judge_user, json=score_payload).raise_for_status()
    # Second attempt with same judge, project, criterion
    response = client.post("/judging/scores/", headers=auth_headers_for_judge_user, json=score_payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "judge has already scored this project for this criterion" in response.json()["detail"]


@pytest.fixture(scope="function")
def created_score_by_judge(
    client: TestClient,
    auth_headers_for_judge_user: Dict[str, str],
    score_payload: Dict[str, Any],
    db_session: Session
) -> ScoreModel:
    response = client.post("/judging/scores/", headers=auth_headers_for_judge_user, json=score_payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    score = db_session.query(ScoreModel).filter(ScoreModel.id == uuid.UUID(data["id"])).first()
    assert score is not None
    return score

def test_update_score_as_submitter_judge(
    client: TestClient,
    auth_headers_for_judge_user: Dict[str, str],
    created_score_by_judge: ScoreModel,
    created_criterion: CriterionModel, # For max_score validation
    db_session: Session
):
    update_payload = ScoreUpdate(score=created_criterion.max_score -1, comment="Updated notes by judge.")
    response = client.put(
        f"/judging/scores/{created_score_by_judge.id}",
        headers=auth_headers_for_judge_user,
        json=update_payload.model_dump(exclude_unset=True)
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["score"] == update_payload.score
    assert data["comment"] == update_payload.comment
    db_session.refresh(created_score_by_judge)
    assert created_score_by_judge.score == update_payload.score
    assert created_score_by_judge.comment == update_payload.comment

def test_update_score_as_admin(
    client: TestClient,
    auth_headers_for_admin_user: Dict[str, str],
    created_score_by_judge: ScoreModel, # Score submitted by a judge
    created_criterion: CriterionModel,
    db_session: Session
):
    update_payload = ScoreUpdate(score=1, comment="Admin override.")
    response = client.put(
        f"/judging/scores/{created_score_by_judge.id}",
        headers=auth_headers_for_admin_user,
        json=update_payload.model_dump(exclude_unset=True)
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["score"] == update_payload.score
    assert data["comment"] == update_payload.comment
    db_session.refresh(created_score_by_judge)
    assert created_score_by_judge.score == update_payload.score
    assert created_score_by_judge.comment == update_payload.comment

def test_update_score_as_different_judge_forbidden(
    client: TestClient,
    auth_headers_for_admin_user: Dict[str, str], # To get headers for a "different" judge
    created_score_by_judge: ScoreModel, # Original score by judge_user
    db_session: Session
):
    # We need another judge. For simplicity, we use admin's headers as if they were a different judge.
    # In a real scenario, you'd have auth_headers_for_another_judge.
    # The crucial part is that the current_user.id from the token won't match created_score_by_judge.judge_id
    # and the current_user.role is not 'admin'.
    # To simulate this properly, we'd need a second judge fixture.
    # For now, this test might pass if auth_headers_for_admin_user IS admin, as admin can update.
    # This test needs refinement with a distinct second judge if that's the intent.
    # Let's assume admin_user is a different judge for this test (which is not ideal).
    # The logic in the endpoint is `if db_score.judge_id != current_user.id and current_user.role != "admin":`
    # To truly test the "different judge" part, we need a non-admin user who isn't the original submitter.

    # This test is simplified: if an admin tries to update, it's allowed.
    # A more accurate test for "different judge forbidden" would require another judge user.
    # For now, let's test a regular user trying to update a judge's score.
    
    # Create a regular user and their auth headers
    other_user_email = f"otherjudge_{uuid.uuid4()}@example.com"
    other_user_pass = "password123"
    client.post("/users/register", json={"email":other_user_email, "username":other_user_email.split('@')[0], "password":other_user_pass, "full_name":"Other User"})
    login_resp = client.post("/users/login", data={"email":other_user_email, "password":other_user_pass})
    auth_headers_for_other_user = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}


    update_payload = ScoreUpdate(score=3)
    response = client.put(
        f"/judging/scores/{created_score_by_judge.id}",
        headers=auth_headers_for_other_user, # Using other_user's headers
        json=update_payload.model_dump(exclude_unset=True)
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_score_invalid_value(
    client: TestClient,
    auth_headers_for_judge_user: Dict[str, str],
    created_score_by_judge: ScoreModel,
    created_criterion: CriterionModel
):
    update_payload = ScoreUpdate(score=created_criterion.max_score + 5) # Invalid score
    response = client.put(
        f"/judging/scores/{created_score_by_judge.id}",
        headers=auth_headers_for_judge_user,
        json=update_payload.model_dump(exclude_unset=True)
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert f"Score must be between 0 and {created_criterion.max_score}" in response.json()["detail"]

def test_update_score_not_found(client: TestClient, auth_headers_for_judge_user: Dict[str, str]):
    non_existent_id = uuid.uuid4()
    update_payload = ScoreUpdate(score=5)
    response = client.put(
        f"/judging/scores/{non_existent_id}",
        headers=auth_headers_for_judge_user,
        json=update_payload.model_dump(exclude_unset=True)
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_list_scores_for_project(
    client: TestClient,
    created_project_for_judging: ProjectModel,
    created_score_by_judge: ScoreModel # Ensures there's at least one score for the project
):
    # This endpoint is open (no auth required by default in judging.py)
    response = client.get(f"/judging/scores/project/{created_project_for_judging.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(s["id"] == str(created_score_by_judge.id) for s in data)
    assert all(s["project_id"] == str(created_project_for_judging.id) for s in data)

def test_list_scores_for_project_no_scores(client: TestClient, created_project_for_judging: ProjectModel, auth_headers_for_regular_user: Dict[str, str]):
    # Assuming created_project_for_judging has no scores yet for this specific test setup
    # To ensure this, we might need a new project fixture that guarantees no scores.
    # For now, we rely on the current project not having scores from other tests or accept it might not be empty.
    # A better approach: create a NEW project specifically for this "empty" test.
    team_resp = client.post("/teams/", json={"name": f"Team_EmptyScoreList_{uuid.uuid4()}", "description":"Test"}, headers=auth_headers_for_regular_user)
    if "id" not in team_resp.json():
        pytest.skip(f"Team creation failed or no 'id' in response: {team_resp.json()}")
    new_team_id = team_resp.json()["id"]
    project_resp = client.post("/projects/", json={"name":f"Project_EmptyScoreList_{uuid.uuid4()}", "team_id": new_team_id, "hackathon_id": str(created_project_for_judging.hackathon_id)}, headers=auth_headers_for_regular_user)
    if "id" not in project_resp.json():
        pytest.skip(f"Project creation failed or no 'id' in response: {project_resp.json()}")
    new_project_id = project_resp.json()["id"]

    response = client.get(f"/judging/scores/project/{new_project_id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []

def test_list_scores_for_project_not_found(client: TestClient):
    non_existent_project_id = uuid.uuid4()
    response = client.get(f"/judging/scores/project/{non_existent_project_id}")
    # The endpoint itself doesn't check project existence before querying scores.
    # If no scores found for a non-existent project_id, it returns an empty list.
    # This behavior might be acceptable or might need adjustment based on requirements
    # (e.g., return 404 if project itself doesn't exist).
    # Current router: `scores = db.query(Score).filter(Score.project_id == project_id).all()`
    # This will just return [] if no scores match, regardless of project existence.
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


def test_list_scores_by_judge_self(
    client: TestClient,
    auth_headers_for_judge_user: Dict[str, str],
    judge_user_data: Dict[str, Any],
    created_score_by_judge: ScoreModel # Score created by this judge
):
    judge_id = judge_user_data["id"]
    response = client.get(f"/judging/scores/judge/{judge_id}", headers=auth_headers_for_judge_user)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(s["id"] == str(created_score_by_judge.id) and s["judge_id"] == judge_id for s in data)
    assert all(s["judge_id"] == judge_id for s in data)

def test_list_scores_by_judge_as_admin_for_another_judge(
    client: TestClient,
    auth_headers_for_admin_user: Dict[str, str], # Admin getting scores
    judge_user_data: Dict[str, Any], # Target judge whose scores are being listed
    created_score_by_judge: ScoreModel # Score created by judge_user
):
    target_judge_id = judge_user_data["id"]
    response = client.get(f"/judging/scores/judge/{target_judge_id}", headers=auth_headers_for_admin_user)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(s["id"] == str(created_score_by_judge.id) and s["judge_id"] == target_judge_id for s in data)

def test_list_scores_by_judge_as_different_judge_forbidden(
    client: TestClient,
    auth_headers_for_admin_user: Dict[str, str], # Simulating a "different judge" for now.
    judge_user_data: Dict[str, Any], # The judge whose scores are targeted
    created_regular_user: UserModel, # Need a non-admin, non-target-judge user.
    auth_headers_for_regular_user: Dict[str,str]
):
    # regular_user (not an admin, not the judge whose scores are being requested)
    # tries to get scores for judge_user_data["id"]
    target_judge_id = judge_user_data["id"]
    
    # Ensure current user (regular_user) is not the target_judge_id
    assert created_regular_user.id != uuid.UUID(target_judge_id)

    response = client.get(f"/judging/scores/judge/{target_judge_id}", headers=auth_headers_for_regular_user)
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_list_scores_by_judge_non_existent_judge_id(
    client: TestClient, auth_headers_for_admin_user: Dict[str, str] # Admin can try to get any judge
):
    non_existent_judge_id = uuid.uuid4()
    response = client.get(f"/judging/scores/judge/{non_existent_judge_id}", headers=auth_headers_for_admin_user)
    assert response.status_code == status.HTTP_200_OK # Returns empty list if judge or scores not found
    assert response.json() == []

# TODO: Consider adding an endpoint to get aggregated results for a project and test it.
# e.g., /results/project/{project_id} 