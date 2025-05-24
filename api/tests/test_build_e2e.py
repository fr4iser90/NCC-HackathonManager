import httpx
import os

BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

EXAMPLE_ZIP = os.path.join(os.path.dirname(__file__), "example_projects", "SimpleSecCheck-main.zip")
assert os.path.exists(EXAMPLE_ZIP), f"ZIP not found: {EXAMPLE_ZIP}"

def test_build_logs_e2e():
    # 1. Login
    r = httpx.post(f"{BASE_URL}/users/login", data={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, f"Login failed: {r.text}"
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Hackathon-ID holen
    r = httpx.get(f"{BASE_URL}/hackathons/", headers=headers)
    assert r.status_code == 200, f"Could not fetch hackathons: {r.text}"
    hackathons = r.json()
    assert hackathons, "No hackathons found in system!"
    hackathon_id = hackathons[0]["id"]

    # 3. Projekt anlegen
    project_data = {
        "name": "E2E BuildLogTest",
        "description": "E2E Test project for build log",
        "hackathon_id": hackathon_id,
        "status": "active",
        "storage_type": "github"
    }
    r = httpx.post(f"{BASE_URL}/projects/", json=project_data, headers=headers)
    assert r.status_code == 201, f"Project creation failed: {r.text}"
    project_id = r.json()["id"]

    # 4. ZIP hochladen
    with open(EXAMPLE_ZIP, "rb") as f:
        files = {"file": (os.path.basename(EXAMPLE_ZIP), f, "application/zip")}
        r = httpx.post(f"{BASE_URL}/projects/{project_id}/submit_version", files=files, headers=headers)
        assert r.status_code == 200, f"Submit failed: {r.text}"
        print("Submit response:", r.json())  # Debug-Ausgabe
        version_id = r.json()["id"]

    # 4a. Alle Versionen für das Projekt abrufen und prüfen, ob die hochgeladene Version dabei ist
    r = httpx.get(f"{BASE_URL}/projects/{project_id}/versions", headers=headers)
    assert r.status_code == 200, f"Could not fetch versions: {r.text}"
    versions = r.json()
    print("Project versions:", versions)
    assert any(v["id"] == version_id for v in versions), f"Uploaded version {version_id} not found in project versions!"

    # 5. Build-Logs abfragen
    r = httpx.get(f"{BASE_URL}/projects/{project_id}/versions/{version_id}/build_logs", headers=headers)
    if r.status_code == 200:
        logs = r.json()["build_logs"]
        print("Build logs (endpoint):", logs)
        assert "Starte Build" in logs or "Build erfolgreich" in logs, "Build logs do not contain expected output!"
    else:
        print("Build-Log-Endpoint liefert 404, prüfe Build-Logs direkt aus Version-Liste!")
        # Fallback: Build-Logs direkt aus Version-Liste prüfen
        logs = next((v["build_logs"] for v in versions if v["id"] == version_id), None)
        print("Build logs (list):", logs)
        assert logs is not None, "Build logs missing in version list!"
        assert "Starte Build" in logs or "Build erfolgreich" in logs, "Build logs do not contain expected output!"

def main():
    test_build_logs_e2e()
    print("E2E Build-Log-Test erfolgreich!")

if __name__ == "__main__":
    main() 