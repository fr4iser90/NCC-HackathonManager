import httpx
import os
import uuid

BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
def test_mentor_login_and_permissions(admin_user_data):
    # Step 1: Register a new user to be promoted to mentor
    unique_email = f"mentor_{uuid.uuid4()}@example.com"
    unique_username = f"mentor_{uuid.uuid4().hex[:8]}"
    mentor_password = "testmentorpw"
    register_payload = {
        "email": unique_email,
        "username": unique_username,
        "password": mentor_password,
        "full_name": "Mentor User"
    }
    r = httpx.post(f"{BASE_URL}/users/register", json=register_payload)
    assert r.status_code in (200, 201), f"Mentor registration failed: {r.text}"

    # Step 2: Login as Admin
    r = httpx.post(
        f"{BASE_URL}/users/login",
        data={"email": admin_user_data["email"], "password": admin_user_data["password"]}
    )
    assert r.status_code == 200, f"Admin login failed: {r.text}"
    admin_token = r.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Step 3: Find the new mentor user by email
    r = httpx.get(f"{BASE_URL}/users/", headers=admin_headers)
    assert r.status_code == 200, f"Admin could not list users: {r.text}"
    users = r.json()
    mentor_user = next((u for u in users if u["email"] == unique_email), None)
    assert mentor_user, "Mentor user not found"
    mentor_id = mentor_user["id"]

    # Step 4: Assign mentor role to mentor user
    r = httpx.post(f"{BASE_URL}/users/{mentor_id}/roles", headers=admin_headers, json={"role": "mentor"})
    assert r.status_code in (200, 201), f"Admin could not assign mentor role: {r.text}"

    # Step 5: Login as Mentor
    r = httpx.post(f"{BASE_URL}/users/login", data={"email": unique_email, "password": mentor_password})
    assert r.status_code == 200, f"Login failed: {r.text}"
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create a hackathon first
    hackathon_data = {
        "name": f"Test Hackathon {uuid.uuid4()}",
        "description": "Test hackathon for mentoring",
        "start_date": "2030-01-01T00:00:00Z",
        "end_date": "2030-01-02T00:00:00Z",
        "status": "upcoming",
        "location": "Test Location"
    }
    r = httpx.post(f"{BASE_URL}/hackathons/", headers=admin_headers, json=hackathon_data)
    assert r.status_code == 201, f"Hackathon creation failed: {r.text}"
    hackathon_id = r.json()["id"]

    # Create a team for testing
    team_data = {
        "name": f"Test Team {uuid.uuid4()}",
        "description": "Test team for mentoring",
        "hackathon_id": hackathon_id
    }
    r = httpx.post(f"{BASE_URL}/teams/", headers=headers, json=team_data)
    assert r.status_code == 201, f"Team creation failed: {r.text}"

    # Mentor darf keine Judging- oder Voting-Aktionen durchführen
    r = httpx.get(f"{BASE_URL}/judging/criteria/", headers=headers)
    assert r.status_code == 200
    # Versuch zu bewerten
    r = httpx.get(f"{BASE_URL}/projects/", headers=headers)
    projects = r.json() if r.status_code == 200 else []
    if isinstance(projects, list) and projects:
        project_id = projects[0]["id"]
        r2 = httpx.get(f"{BASE_URL}/judging/criteria/", headers=headers)
        criteria = r2.json() if r2.status_code == 200 else []
        if isinstance(criteria, list) and criteria:
            criterion_id = criteria[0]["id"]
            score_payload = {"project_id": project_id, "criteria_id": criterion_id, "score": 5, "notes": "Mentor darf nicht bewerten"}
            r3 = httpx.post(f"{BASE_URL}/judging/scores/", headers=headers, json=score_payload)
            assert r3.status_code == 403
    # Mentor darf keinen Hackathon anlegen
    hackathon_data = {"name": "MentorHack", "description": "desc", "start_date": "2030-01-01T00:00:00Z", "end_date": "2030-01-02T00:00:00Z", "status": "upcoming", "location": "", "organizer_id": str(uuid.uuid4())}
    r = httpx.post(f"{BASE_URL}/hackathons/", headers=headers, json=hackathon_data)
    assert r.status_code == 403
    # Mentor darf kein Team löschen
    r = httpx.get(f"{BASE_URL}/teams/", headers=headers)
    assert r.status_code == 200
    teams = r.json()
    assert len(teams) > 0, "No teams found after creation"
    team_id = teams[0]["id"]
    r2 = httpx.delete(f"{BASE_URL}/teams/{team_id}", headers=headers)
    assert r2.status_code == 403
