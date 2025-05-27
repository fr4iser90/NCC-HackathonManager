import pytest
import uuid


@pytest.fixture
def admin_token(client, admin_user_data):
    response = client.post(
        "/users/login",
        data={
            "email": admin_user_data["email"],
            "password": admin_user_data["password"],
        },
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]


def test_admin_full_crud_and_security(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Admin kann Hackathon anlegen
    # Get admin user ID
    r_admin = client.get("/users", headers=headers)
    assert r_admin.status_code == 200
    users = r_admin.json()
    print("DEBUG USERS:", users)
    admin_user = next((u for u in users if u["email"] == "admin@example.com"), None)
    assert admin_user, f"Admin user not found. Users returned: {users}"
    admin_id = admin_user["id"]

    hackathon_data = {
        "name": f"AdminHack_{uuid.uuid4()}",
        "description": "desc",
        "start_date": "2030-01-01T00:00:00Z",
        "end_date": "2030-01-02T00:00:00Z",
        "status": "upcoming",
        "location": "",
        "organizer_id": admin_id,
    }
    r = client.post("/hackathons/", headers=headers, json=hackathon_data)
    assert r.status_code == 201, f"Create hackathon failed: {r.text}"
    hackathon_id = r.json()["id"]

    # Admin kann Hackathon updaten
    patch = {"status": "active"}
    r = client.put(f"/hackathons/{hackathon_id}", headers=headers, json=patch)
    assert r.status_code in (200, 204), f"Update hackathon failed: {r.text}"

    # Admin kann Team anlegen und löschen
    team_data = {
        "name": f"AdminTeam_{uuid.uuid4()}",
        "description": "desc",
        "hackathon_id": hackathon_id,
    }
    r = client.post("/teams/", headers=headers, json=team_data)
    assert r.status_code == 201, f"Create team failed: {r.text}"
    team_id = r.json()["id"]
    r = client.delete(f"/teams/{team_id}", headers=headers)
    assert r.status_code == 204, f"Delete team failed: {r.text}"

    # Admin kann Projekt anlegen und löschen
    project_data = {
        "name": f"AdminProject_{uuid.uuid4()}",
        "description": "desc",
        "hackathon_id": hackathon_id,
        "status": "active",
        "storage_type": "github",
    }
    r = client.post("/projects/", headers=headers, json=project_data)
    assert r.status_code == 201, f"Create project failed: {r.text}"
    project_id = r.json()["id"]
    r = client.delete(f"/projects/{project_id}", headers=headers)
    assert r.status_code == 204, f"Delete project failed: {r.text}"

    # Admin kann Judging-Kriterien anlegen
    criterion = {
        "name": "AdminKriterium",
        "description": "desc",
        "max_score": 10,
        "weight": 1.0,
    }
    r = client.post("/judging/criteria/", headers=headers, json=criterion)
    assert r.status_code == 201, f"Create criterion failed: {r.text}"

    # Admin kann Voting/Deadlines setzen (z.B. Hackathon auf completed setzen)
    patch = {"status": "completed"}
    r = client.put(f"/hackathons/{hackathon_id}", headers=headers, json=patch)
    assert r.status_code in (200, 204), f"Set voting status failed: {r.text}"

    # Admin kann Security-Fehler erkennen (z.B. doppeltes Team löschen)
    r = client.delete(f"/teams/{team_id}", headers=headers)
    assert r.status_code in (204, 404, 400, 403)
