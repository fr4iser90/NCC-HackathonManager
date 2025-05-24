import httpx
import os
import uuid

BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
ADMIN_EMAIL = os.environ["ADMIN_EMAIL"]
ADMIN_PASSWORD = os.environ["ADMIN_PASSWORD"]

def test_admin_full_crud_and_security():
    # Login als Admin
    r = httpx.post(f"{BASE_URL}/users/login", data={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, f"Login failed: {r.text}"
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Admin kann Hackathon anlegen
    hackathon_data = {"name": f"AdminHack_{uuid.uuid4()}", "description": "desc", "start_date": "2030-01-01T00:00:00Z", "end_date": "2030-01-02T00:00:00Z", "status": "upcoming", "location": "", "organizer_id": str(uuid.uuid4())}
    r = httpx.post(f"{BASE_URL}/hackathons/", headers=headers, json=hackathon_data)
    assert r.status_code == 201
    hackathon_id = r.json()["id"]
    # Admin kann Hackathon updaten
    patch = {"status": "active"}
    r = httpx.put(f"{BASE_URL}/hackathons/{hackathon_id}", headers=headers, json=patch)
    assert r.status_code in (200, 204)
    # Admin kann Team anlegen und löschen
    team_data = {"name": f"AdminTeam_{uuid.uuid4()}", "description": "desc", "hackathon_id": hackathon_id}
    r = httpx.post(f"{BASE_URL}/teams/", headers=headers, json=team_data)
    assert r.status_code == 201
    team_id = r.json()["id"]
    r = httpx.delete(f"{BASE_URL}/teams/{team_id}", headers=headers)
    assert r.status_code == 204
    # Admin kann Projekt anlegen und löschen
    project_data = {"name": f"AdminProject_{uuid.uuid4()}", "description": "desc", "hackathon_id": hackathon_id, "status": "active", "storage_type": "github"}
    r = httpx.post(f"{BASE_URL}/projects/", headers=headers, json=project_data)
    assert r.status_code == 201
    project_id = r.json()["id"]
    r = httpx.delete(f"{BASE_URL}/projects/{project_id}", headers=headers)
    assert r.status_code == 204
    # Admin kann Judging-Kriterien anlegen
    criterion = {"name": "AdminKriterium", "description": "desc", "max_score": 10, "weight": 1.0}
    r = httpx.post(f"{BASE_URL}/judging/criteria/", headers=headers, json=criterion)
    assert r.status_code == 201
    # Admin kann Voting/Deadlines setzen (z.B. Hackathon auf voting setzen)
    patch = {"status": "voting"}
    r = httpx.put(f"{BASE_URL}/hackathons/{hackathon_id}", headers=headers, json=patch)
    assert r.status_code in (200, 204)
    # Admin kann Security-Fehler erkennen (z.B. doppeltes Team löschen)
    r = httpx.delete(f"{BASE_URL}/teams/{team_id}", headers=headers)
    assert r.status_code in (404, 400, 403)
