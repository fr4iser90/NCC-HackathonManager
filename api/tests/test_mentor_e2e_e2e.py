import httpx
import os
import uuid

BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
MENTOR_EMAIL = os.environ.get("MENTOR_EMAIL", "mentor@example.com")
MENTOR_PASSWORD = os.environ.get("MENTOR_PASSWORD", "mentor123")

def test_mentor_login_and_permissions():
    # Login als Mentor
    r = httpx.post(f"{BASE_URL}/users/login", data={"email": MENTOR_EMAIL, "password": MENTOR_PASSWORD})
    assert r.status_code == 200, f"Login failed: {r.text}"
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Mentor darf keine Judging- oder Voting-Aktionen durchführen
    r = httpx.get(f"{BASE_URL}/judging/criteria/", headers=headers)
    assert r.status_code == 200
    # Versuch zu bewerten
    r = httpx.get(f"{BASE_URL}/projects/", headers=headers)
    if r.json():
        project_id = r.json()[0]["id"]
        r2 = httpx.get(f"{BASE_URL}/judging/criteria/", headers=headers)
        if r2.json():
            criterion_id = r2.json()[0]["id"]
            score_payload = {"project_id": project_id, "criteria_id": criterion_id, "score": 5, "notes": "Mentor darf nicht bewerten"}
            r3 = httpx.post(f"{BASE_URL}/judging/scores/", headers=headers, json=score_payload)
            assert r3.status_code == 403
    # Mentor darf keinen Hackathon anlegen
    hackathon_data = {"name": "MentorHack", "description": "desc", "start_date": "2030-01-01T00:00:00Z", "end_date": "2030-01-02T00:00:00Z", "status": "upcoming", "location": "", "organizer_id": str(uuid.uuid4())}
    r = httpx.post(f"{BASE_URL}/hackathons/", headers=headers, json=hackathon_data)
    assert r.status_code == 403
    # Mentor darf kein Team löschen
    r = httpx.get(f"{BASE_URL}/teams/", headers=headers)
    if r.json():
        team_id = r.json()[0]["id"]
        r2 = httpx.delete(f"{BASE_URL}/teams/{team_id}", headers=headers)
        assert r2.status_code == 403
