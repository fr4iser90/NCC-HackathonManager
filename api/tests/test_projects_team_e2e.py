import httpx
import os
import uuid

BASE_URL = "http://localhost:8000"



def test_admin_crud_project_e2e(admin_user_data):
    unique = str(uuid.uuid4())[:8]
    # 1. Login als Admin
    r = httpx.post(f"{BASE_URL}/users/login", data={"email": admin_user_data["email"], "password": admin_user_data["password"]})
    assert r.status_code == 200, f"Login failed: {r.text}"
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Hackathon-ID holen
    r = httpx.get(f"{BASE_URL}/hackathons/", headers=headers)
    assert r.status_code == 200, f"Could not fetch hackathons: {r.text}"
    hackathons = r.json()
    assert hackathons, "No hackathons found in system!"
    hackathon_id = hackathons[0]["id"]
    # Patch: Activate hackathon if not active
    if hackathons[0].get("status") != "active":
        patch = {"status": "active"}
        r2 = httpx.put(f"{BASE_URL}/hackathons/{hackathon_id}", json=patch, headers=headers)
        assert r2.status_code in (200, 204), f"Failed to activate hackathon: {r2.text}"

    # 3. Projekt anlegen (mit Team)
    # Team anlegen
    team_data = {"name": f"E2E Admin Team {unique}", "description": "E2E Admin Team", "hackathon_id": hackathon_id}
    r = httpx.post(f"{BASE_URL}/teams/", json=team_data, headers=headers)
    assert r.status_code == 201, f"Team creation failed: {r.text}"
    team_id = r.json()["id"]
    # Projekt mit Team anlegen
    project_data = {
        "name": "E2E Admin Team Project",
        "description": "E2E Admin Team Test",
        "hackathon_id": hackathon_id,
        "status": "active",
        "storage_type": "github",
        "team_id": team_id
    }
    r = httpx.post(f"{BASE_URL}/projects/", json=project_data, headers=headers)
    assert r.status_code == 201, f"Project creation failed: {r.text}"
    project_id = r.json()["id"]

    # 4. Projekt bearbeiten
    update_data = {"name": "E2E Admin Team Project Updated", "description": "Updated by admin"}
    r = httpx.put(f"{BASE_URL}/projects/{project_id}", json=update_data, headers=headers)
    assert r.status_code == 200, f"Project update failed: {r.text}"
    assert r.json()["name"] == "E2E Admin Team Project Updated"

    # 5. Projekt abrufen
    r = httpx.get(f"{BASE_URL}/projects/{project_id}", headers=headers)
    assert r.status_code == 200, f"Project fetch failed: {r.text}"
    assert r.json()["id"] == project_id

    # 6. Projekt löschen
    r = httpx.delete(f"{BASE_URL}/projects/{project_id}", headers=headers)
    assert r.status_code == 204, f"Project delete failed: {r.text}"

    # 7. Projekt darf nicht mehr existieren
    r = httpx.get(f"{BASE_URL}/projects/{project_id}", headers=headers)
    assert r.status_code == 404, f"Deleted project still exists: {r.text}"

def test_user_crud_project_e2e(admin_user_data):
    unique = str(uuid.uuid4())[:8]
    # 1. User registrieren
    user_email = f"e2euser_{unique}@example.com"
    user_password = "e2euserpass123"
    r = httpx.post(f"{BASE_URL}/users/register", json={
        "email": user_email,
        "username": f"e2euser_{unique}",
        "password": user_password,
        "full_name": "E2E User"
    })
    assert r.status_code == 201, f"User registration failed: {r.text}"
    # 2. Login
    r = httpx.post(f"{BASE_URL}/users/login", data={"email": user_email, "password": user_password})
    assert r.status_code == 200, f"Login failed: {r.text}"
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    # 3. Hackathon-ID holen
    r = httpx.get(f"{BASE_URL}/hackathons/", headers=headers)
    hackathon = r.json()[0]
    hackathon_id = hackathon["id"]
    # Patch: Activate hackathon if not active
    if hackathon.get("status") != "active":
        admin_r = httpx.post(f"{BASE_URL}/users/login", data={"email": admin_user_data["email"], "password": admin_user_data["password"]})
        admin_token = admin_r.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        patch = {"status": "active"}
        r2 = httpx.put(f"{BASE_URL}/hackathons/{hackathon_id}", json=patch, headers=admin_headers)
        assert r2.status_code in (200, 204), f"Failed to activate hackathon: {r2.text}"

    # --- TEAM HACKATHON: Projekt mit Team ---
    # Team anlegen
    team_data = {"name": f"E2E Team {unique}", "description": "E2E Team", "hackathon_id": hackathon_id}
    r = httpx.post(f"{BASE_URL}/teams/", json=team_data, headers=headers)
    assert r.status_code == 201, f"Team creation failed: {r.text}"
    team_id = r.json()["id"]
    # Projekt mit Team anlegen
    project_data = {
        "name": "E2E User Team Project",
        "description": "E2E User Team Test",
        "hackathon_id": hackathon_id,
        "status": "active",
        "storage_type": "github",
        "team_id": team_id
    }
    r = httpx.post(f"{BASE_URL}/projects/", json=project_data, headers=headers)
    assert r.status_code == 201, f"Team project creation failed: {r.text}"
    team_project_id = r.json()["id"]
    # Bearbeiten
    update_data = {"name": "E2E User Team Project Updated", "description": "Updated by user"}
    r = httpx.put(f"{BASE_URL}/projects/{team_project_id}", json=update_data, headers=headers)
    assert r.status_code == 200, f"Team project update failed: {r.text}"
    # Löschen
    r = httpx.delete(f"{BASE_URL}/projects/{team_project_id}", headers=headers)
    assert r.status_code == 204, f"Team project delete failed: {r.text}"

    # --- Fremdes Projekt (Admin) testen wie gehabt ---
    admin_r = httpx.post(f"{BASE_URL}/users/login", data={"email": admin_user_data["email"], "password": admin_user_data["password"]})
    admin_token = admin_r.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    # Create a different team for the foreign project
    foreign_team_data = {"name": f"E2E Foreign Team {unique}", "description": "Foreign Team", "hackathon_id": hackathon_id}
    r = httpx.post(f"{BASE_URL}/teams/", json=foreign_team_data, headers=admin_headers)
    assert r.status_code == 201, f"Foreign team creation failed: {r.text}"
    foreign_team_id = r.json()["id"]
    r = httpx.post(f"{BASE_URL}/projects/", json={"name": "Fremdprojekt", "description": "Fremd", "hackathon_id": hackathon_id, "status": "active", "storage_type": "github", "team_id": foreign_team_id}, headers=admin_headers)
    fremd_id = r.json()["id"]
    # User versucht fremdes Projekt zu bearbeiten
    r = httpx.put(f"{BASE_URL}/projects/{fremd_id}", json={"name": "Hacked"}, headers=headers)
    assert r.status_code in (403, 404), f"User konnte fremdes Projekt bearbeiten! {r.text}"
    # User versucht fremdes Projekt zu löschen
    r = httpx.delete(f"{BASE_URL}/projects/{fremd_id}", headers=headers)
    assert r.status_code in (403, 404), f"User konnte fremdes Projekt löschen! {r.text}"

def test_team_project_forbidden_when_hackathon_not_active(admin_user_data):
    unique = str(uuid.uuid4())[:8]
    # Register and login user
    user_email = f"forbiddenteam_{unique}@example.com"
    user_password = "forbiddenteampass123"
    r = httpx.post(f"{BASE_URL}/users/register", json={
        "email": user_email,
        "username": f"forbiddenteam_{unique}",
        "password": user_password,
        "full_name": "Forbidden Team User"
    })
    assert r.status_code == 201
    r = httpx.post(f"{BASE_URL}/users/login", data={"email": user_email, "password": user_password})
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    # Get hackathon
    r = httpx.get(f"{BASE_URL}/hackathons/", headers=headers)
    hackathon = r.json()[0]
    hackathon_id = hackathon["id"]
    # Ensure hackathon is active
    if hackathon.get("status") != "active":
        admin_r = httpx.post(f"{BASE_URL}/users/login", data={"email": admin_user_data["email"], "password": admin_user_data["password"]})
        admin_token = admin_r.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        patch = {"status": "active"}
        r2 = httpx.put(f"{BASE_URL}/hackathons/{hackathon_id}", json=patch, headers=admin_headers)
        assert r2.status_code in (200, 204)
    # Create team
    team_data = {"name": f"Forbidden Team {unique}", "description": "Forbidden Team", "hackathon_id": hackathon_id}
    r = httpx.post(f"{BASE_URL}/teams/", json=team_data, headers=headers)
    assert r.status_code == 201
    team_id = r.json()["id"]
    # Create project with team
    project_data = {
        "name": f"Forbidden Team Project {unique}",
        "description": "Should not be editable after hackathon ends",
        "hackathon_id": hackathon_id,
        "status": "active",
        "storage_type": "github",
        "team_id": team_id
    }
    r = httpx.post(f"{BASE_URL}/projects/", json=project_data, headers=headers)
    assert r.status_code == 201
    project_id = r.json()["id"]
    # Set hackathon to archived
    admin_r = httpx.post(f"{BASE_URL}/users/login", data={"email": admin_user_data["email"], "password": admin_user_data["password"]})
    admin_token = admin_r.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    patch = {"status": "archived"}
    r2 = httpx.put(f"{BASE_URL}/hackathons/{hackathon_id}", json=patch, headers=admin_headers)
    assert r2.status_code in (200, 204)
    # Try to update project
    update_data = {"name": "Should Fail"}
    r = httpx.put(f"{BASE_URL}/projects/{project_id}", json=update_data, headers=headers)
    assert r.status_code in (400, 403), f"Update should be forbidden: {r.text}"
    # Try to delete project
    r = httpx.delete(f"{BASE_URL}/projects/{project_id}", headers=headers)
    assert r.status_code in (400, 403), f"Delete should be forbidden: {r.text}"
    # Try to upload version
    import io
    import zipfile
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        zf.writestr("dummy.txt", "dummy content")
    zip_buffer.seek(0)
    files = {"file": ("dummy.zip", zip_buffer, "application/zip")}
    r = httpx.post(f"{BASE_URL}/projects/{project_id}/submit_version", headers=headers, files=files)
    assert r.status_code in (400, 403), f"Upload should be forbidden: {r.text}"

def main():
    test_admin_crud_project_e2e()
    print("E2E Admin-CRUD-Test erfolgreich!")
    test_user_crud_project_e2e()
    print("E2E User-CRUD-Test erfolgreich!")
    test_team_project_forbidden_when_hackathon_not_active()
    print("E2E Team Project Forbidden Test erfolgreich!")

if __name__ == "__main__":
    main()
