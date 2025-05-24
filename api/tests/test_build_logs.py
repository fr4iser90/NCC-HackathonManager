import os
import io
import pytest

@pytest.mark.usefixtures("client", "db_session", "test_hackathon", "created_regular_user", "auth_headers_for_regular_user")
def test_build_logs_end_to_end(client, db_session, test_hackathon, created_regular_user, auth_headers_for_regular_user):
    """
    End-to-end test: Upload ZIP, trigger build, check logs.
    """
    # 1. Create a test project via API
    project_data = {
        "name": "BuildLogTestProject",
        "description": "Test project for build log",
        "hackathon_id": str(test_hackathon.id),
        "status": "active",
        "storage_type": "github"
    }
    res = client.post("/projects/", json=project_data, headers=auth_headers_for_regular_user)
    assert res.status_code == 201, f"Project creation failed: {res.text}"
    project = res.json()
    project_id = project["id"]

    # 2. Upload ZIP to /submit_version
    zip_path = os.path.join(os.path.dirname(__file__), "magic-genie-explainer-main.zip")
    assert os.path.exists(zip_path), "Test ZIP not found"
    with open(zip_path, "rb") as f:
        file_bytes = f.read()
    file_obj = io.BytesIO(file_bytes)
    files = {"file": ("magic-genie-explainer-main.zip", file_obj, "application/zip")}
    data = {"project_id": str(project_id)}  # Pass as string
    print("DEBUG: About to POST to /projects/{}/submit_version".format(project_id))
    print("DEBUG: files =", files)
    print("DEBUG: data =", data)
    res = client.post(f"/projects/{project_id}/submit_version", files=files, data=data, headers=auth_headers_for_regular_user)
    print("DEBUG: POST response status_code =", res.status_code)
    print("DEBUG: POST response text =", res.text)
    assert res.status_code == 200, f"Submit failed: {res.text}"
    resp = res.json()
    version_id = resp.get("version_id") or resp.get("id")
    assert version_id, f"No version_id in response: {resp}"

    # 3. Fetch build logs
    logs_res = client.get(f"/projects/{project.id}/versions/{version_id}/build_logs", headers=auth_headers_for_regular_user)
    assert logs_res.status_code == 200, f"Build logs fetch failed: {logs_res.text}"
    logs_data = logs_res.json()
    logs = logs_data.get("build_logs", "")
    assert logs, "Build logs are empty"
    print("Build logs:\n", logs)
