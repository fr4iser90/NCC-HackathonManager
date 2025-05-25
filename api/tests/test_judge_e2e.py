import httpx
import os
import uuid

BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
def test_judge_login_and_judging_flow(admin_user_data):
    # Step 1: Register a new user to be promoted to judge
    unique_email = f"judge_{uuid.uuid4()}@example.com"
    unique_username = f"judge_{uuid.uuid4().hex[:8]}"
    judge_password = "testjudgepw"
    register_payload = {
        "email": unique_email,
        "username": unique_username,
        "password": judge_password,
        "full_name": "Judge User"
    }
    r = httpx.post(f"{BASE_URL}/users/register", json=register_payload)
    assert r.status_code in (200, 201), f"Judge registration failed: {r.text}"

    # Step 2: Login as Admin
    r = httpx.post(f"{BASE_URL}/users/login", data={"email": admin_user_data["email"], "password": admin_user_data["password"]})
    assert r.status_code == 200, f"Admin login failed: {r.text}"
    admin_token = r.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Step 3: Find the new judge user by email
    r = httpx.get(f"{BASE_URL}/users", headers=admin_headers)
    assert r.status_code == 200, f"Admin could not list users: {r.text}"
    users = r.json()
    judge_user = next((u for u in users if u["email"] == unique_email), None)
    assert judge_user, "Judge user not found"
    judge_id = judge_user["id"]

    # Step 4: Assign judge role to judge user
    r = httpx.post(f"{BASE_URL}/users/{judge_id}/roles", headers=admin_headers, json={"role": "judge"})
    assert r.status_code in (200, 201), f"Admin could not assign judge role: {r.text}"

    # Step 5: Login as Judge
    r = httpx.post(f"{BASE_URL}/users/login", data={"email": unique_email, "password": judge_password})
    assert r.status_code == 200, f"Judge login failed: {r.text}"
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Judge darf Kriterien sehen, aber nicht anlegen
    r = httpx.get(f"{BASE_URL}/judging/criteria/", headers=headers)
    assert r.status_code == 200
    r = httpx.post(f"{BASE_URL}/judging/criteria/", headers=headers, json={"name": "Test", "description": "desc", "max_score": 10, "weight": 1.0})
    assert r.status_code == 403

    # Judge darf bewerten (Score abgeben)
    # Hole ein Projekt und ein Kriterium
    r = httpx.get(f"{BASE_URL}/projects/", headers=headers)
    assert r.status_code == 200 and r.json(), "No projects found!"
    project_id = r.json()[0]["id"]
    r = httpx.get(f"{BASE_URL}/judging/criteria/", headers=headers)
    assert r.status_code == 200 and r.json(), "No criteria found!"
    criterion_id = r.json()[0]["id"]
    score_payload = {"project_id": project_id, "criteria_id": criterion_id, "score": 8, "notes": "Gut!"}
    r = httpx.post(f"{BASE_URL}/judging/scores/", headers=headers, json=score_payload)
    assert r.status_code == 201, f"Judge could not submit score: {r.text}"
    # Judge darf nicht doppelt bewerten
    r2 = httpx.post(f"{BASE_URL}/judging/scores/", headers=headers, json=score_payload)
    assert r2.status_code == 400

    # Judge darf keinen Hackathon anlegen
    hackathon_data = {"name": "JudgeHack", "description": "desc", "start_date": "2030-01-01T00:00:00Z", "end_date": "2030-01-02T00:00:00Z", "status": "upcoming", "location": "", "organizer_id": str(uuid.uuid4())}
    r = httpx.post(f"{BASE_URL}/hackathons/", headers=headers, json=hackathon_data)
    assert r.status_code == 403

    # Judge darf kein Team löschen
    r = httpx.get(f"{BASE_URL}/teams/", headers=headers)
    if r.json():
        team_id = r.json()[0]["id"]
        r2 = httpx.delete(f"{BASE_URL}/teams/{team_id}", headers=headers)
        assert r2.status_code == 403
