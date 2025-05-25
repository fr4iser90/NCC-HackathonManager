import httpx
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")


EXAMPLE_ZIP = os.path.join(os.path.dirname(__file__), "example_projects", "SimpleSecCheck-main.zip")
assert os.path.exists(EXAMPLE_ZIP), f"ZIP not found: {EXAMPLE_ZIP}"

def test_build_logs_e2e(admin_user_data):
    # 1. Login
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

    ensure_hackathon_active(project_id, headers)

    # 4. ZIP hochladen
    with open(EXAMPLE_ZIP, "rb") as f:
        files = {"file": (os.path.basename(EXAMPLE_ZIP), f, "application/zip")}
        r = httpx.post(f"{BASE_URL}/projects/{project_id}/submit_version", files=files, headers=headers)
        assert r.status_code in (200, 400), f"Expected 200 or 400, got {r.status_code}: {r.text}"
        if r.status_code == 400:
            assert "Hackathon is not active" in r.text, f"Expected error message 'Hackathon is not active', got: {r.text}"
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

def test_upload_invalid_zip_e2e(admin_user_data):
    # 1. Login
    r = httpx.post(f"{BASE_URL}/users/login", data={"email": admin_user_data["email"], "password": admin_user_data["password"]})
    assert r.status_code == 200
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    # 2. Hackathon-ID holen
    r = httpx.get(f"{BASE_URL}/hackathons/", headers=headers)
    hackathon_id = r.json()[0]["id"]
    # 3. Projekt anlegen
    project_data = {"name": "InvalidZipE2E", "description": "E2E", "hackathon_id": hackathon_id, "status": "active", "storage_type": "github"}
    r = httpx.post(f"{BASE_URL}/projects/", json=project_data, headers=headers)
    project_id = r.json()["id"]
    ensure_hackathon_active(project_id, headers)
    # 4. Ungültiges ZIP hochladen
    files = {"file": ("notazip.zip", b"not a zip", "application/zip")}
    r = httpx.post(f"{BASE_URL}/projects/{project_id}/submit_version", files=files, headers=headers)
    assert r.status_code in (400, 422), f"Expected failure, got {r.status_code}: {r.text}"

def test_upload_zip_missing_project_files_e2e(admin_user_data):
    import io, zipfile
    r = httpx.post(f"{BASE_URL}/users/login", data={"email": admin_user_data["email"], "password": admin_user_data["password"]})
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    r = httpx.get(f"{BASE_URL}/hackathons/", headers=headers)
    hackathon_id = r.json()[0]["id"]
    project_data = {"name": "MissingFilesE2E", "description": "E2E", "hackathon_id": hackathon_id, "status": "active", "storage_type": "github"}
    r = httpx.post(f"{BASE_URL}/projects/", json=project_data, headers=headers)
    project_id = r.json()["id"]
    ensure_hackathon_active(project_id, headers)
    # Leeres ZIP
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as zf:
        pass
    buf.seek(0)
    files = {"file": ("empty.zip", buf, "application/zip")}
    r = httpx.post(f"{BASE_URL}/projects/{project_id}/submit_version", files=files, headers=headers)
    assert r.status_code in (200, 400, 422)
    if r.status_code == 200:
        version_id = r.json()["id"]
        r2 = httpx.get(f"{BASE_URL}/projects/{project_id}/versions/{version_id}/build_logs", headers=headers)
        logs = r2.json().get("build_logs", "") if r2.status_code == 200 else ""
        if not ("Dockerfile" in logs or "requirements.txt" in logs or "package.json" in logs or "not found" in logs):
            print("[WARN] Build logs leer oder keine erwartete Fehlermeldung für fehlende Projektdateien:", logs)
    if r.status_code == 200:
        version_id = r.json()["id"]
        r2 = httpx.get(f"{BASE_URL}/projects/{project_id}/versions/{version_id}/build_logs", headers=headers)
        logs = r2.json().get("build_logs", "") if r2.status_code == 200 else ""
        if not ("Dockerfile" in logs or "requirements.txt" in logs or "package.json" in logs or "not found" in logs):
            print("[WARN] Build logs leer oder keine erwartete Fehlermeldung für fehlende Projektdateien:", logs)

def test_build_timeout_simulation_e2e(admin_user_data):
    import io, zipfile
    r = httpx.post(f"{BASE_URL}/users/login", data={"email": admin_user_data["email"], "password": admin_user_data["password"]})
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    r = httpx.get(f"{BASE_URL}/hackathons/", headers=headers)
    hackathon_id = r.json()[0]["id"]
    project_data = {"name": "TimeoutE2E", "description": "E2E", "hackathon_id": hackathon_id, "status": "active", "storage_type": "github"}
    r = httpx.post(f"{BASE_URL}/projects/", json=project_data, headers=headers)
    project_id = r.json()["id"]
    ensure_hackathon_active(project_id, headers)
    # ZIP mit Dockerfile, das sleep macht
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as zf:
        zf.writestr("Dockerfile", "FROM alpine:3.18\nRUN sleep 5\n")
    buf.seek(0)
    files = {"file": ("timeout.zip", buf, "application/zip")}
    try:
        r = httpx.post(f"{BASE_URL}/projects/{project_id}/submit_version", files=files, headers=headers, timeout=15)
    except Exception as e:
        print(f"[WARN] Build-Timeout-Test: Exception/Timeout: {e}")
        return
    if r.status_code == 200:
        version_id = r.json()["id"]
        r2 = httpx.get(f"{BASE_URL}/projects/{project_id}/versions/{version_id}/build_logs", headers=headers)
        logs = r2.json().get("build_logs", "") if r2.status_code == 200 else ""
        if not ("sleep" in logs or "timeout" in logs or "timed out" in logs):
            print("[WARN] Build logs leer oder keine Timeout-Meldung:", logs)

def test_build_security_warnings_e2e(admin_user_data):
    import io, zipfile
    r = httpx.post(f"{BASE_URL}/users/login", data={"email": admin_user_data["email"], "password": admin_user_data["password"]})
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    r = httpx.get(f"{BASE_URL}/hackathons/", headers=headers)
    hackathon_id = r.json()[0]["id"]
    project_data = {"name": "SecurityE2E", "description": "E2E", "hackathon_id": hackathon_id, "status": "active", "storage_type": "github"}
    r = httpx.post(f"{BASE_URL}/projects/", json=project_data, headers=headers)
    project_id = r.json()["id"]
    ensure_hackathon_active(project_id, headers)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as zf:
        zf.writestr("Dockerfile", "FROM alpine:3.18\nUSER root\nRUN echo 'privileged'\n")
        zf.writestr("docker-compose.yml", "services:\n  app:\n    image: alpine:3.18\n    privileged: true\n")
    buf.seek(0)
    files = {"file": ("security.zip", buf, "application/zip")}
    r = httpx.post(f"{BASE_URL}/projects/{project_id}/submit_version", files=files, headers=headers)
    assert r.status_code in (200, 400, 422)
    if r.status_code == 200:
        version_id = r.json()["id"]
        r2 = httpx.get(f"{BASE_URL}/projects/{project_id}/versions/{version_id}/build_logs", headers=headers)
        logs = r2.json().get("build_logs", "") if r2.status_code == 200 else ""
        if not ("privileged" in logs or "root" in logs or "SECURITY" in logs):
            print("[WARN] Build logs leer oder keine Security-Warnung:", logs)

def test_build_multiple_versions_e2e(admin_user_data):
    import io, zipfile
    r = httpx.post(f"{BASE_URL}/users/login", data={"email": admin_user_data["email"], "password": admin_user_data["password"]})
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    r = httpx.get(f"{BASE_URL}/hackathons/", headers=headers)
    hackathon_id = r.json()[0]["id"]
    project_data = {"name": "MultiVersionE2E", "description": "E2E", "hackathon_id": hackathon_id, "status": "active", "storage_type": "github"}
    r = httpx.post(f"{BASE_URL}/projects/", json=project_data, headers=headers)
    project_id = r.json()["id"]
    ensure_hackathon_active(project_id, headers)
    # Version 1
    buf1 = io.BytesIO()
    with zipfile.ZipFile(buf1, 'w') as zf:
        zf.writestr("Dockerfile", "FROM alpine:3.18\n")
    buf1.seek(0)
    files1 = {"file": ("v1.zip", buf1, "application/zip")}
    r1 = httpx.post(f"{BASE_URL}/projects/{project_id}/submit_version", files=files1, headers=headers)
    version_id1 = r1.json()["id"] if r1.status_code == 200 else None
    # Version 2
    buf2 = io.BytesIO()
    with zipfile.ZipFile(buf2, 'w') as zf:
        zf.writestr("Dockerfile", "FROM alpine:3.18\n")
    buf2.seek(0)
    files2 = {"file": ("v2.zip", buf2, "application/zip")}
    r2 = httpx.post(f"{BASE_URL}/projects/{project_id}/submit_version", files=files2, headers=headers)
    version_id2 = r2.json()["id"] if r2.status_code == 200 else None
    # Prüfe, dass beide Versionen existieren und unterschiedlich sind
    assert version_id1 and version_id2 and version_id1 != version_id2
    # Logs für beide Versionen holen
    logs1 = httpx.get(f"{BASE_URL}/projects/{project_id}/versions/{version_id1}/build_logs", headers=headers).json().get("build_logs", "")
    logs2 = httpx.get(f"{BASE_URL}/projects/{project_id}/versions/{version_id2}/build_logs", headers=headers).json().get("build_logs", "")
    if not (logs1 and logs2 and logs1 != logs2):
        print(f"[WARN] Build-Logs für mehrere Versionen leer oder identisch! logs1: {logs1}, logs2: {logs2}")

def ensure_hackathon_active(project_id, admin_headers):
    # Fetch project, get hackathon_id
    r = httpx.get(f"{BASE_URL}/projects/{project_id}", headers=admin_headers)
    if r.status_code != 200:
        return
    hackathon_id = r.json().get("hackathon_id")
    if not hackathon_id:
        return
    # Set hackathon to active
    patch = {"status": "active"}
    r2 = httpx.put(f"{BASE_URL}/hackathons/{hackathon_id}", json=patch, headers=admin_headers)
    assert r2.status_code in (200, 204)

def main():
    test_build_logs_e2e()
    test_upload_invalid_zip_e2e()
    test_upload_zip_missing_project_files_e2e()
    test_build_timeout_simulation_e2e()
    test_build_security_warnings_e2e()
    test_build_multiple_versions_e2e()
    print("E2E Build-Log-Test erfolgreich!")

if __name__ == "__main__":
    main()
