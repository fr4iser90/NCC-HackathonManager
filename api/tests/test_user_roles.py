import pytest

@pytest.fixture
def admin_token(client, admin_user_data):
    response = client.post("/users/login", data={"email": admin_user_data["email"], "password": admin_user_data["password"]})
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    return response.json()["access_token"]

@pytest.fixture
def participant_token(client, regular_user_data):
    response = client.post("/users/login", data={"email": regular_user_data["email"], "password": regular_user_data["password"]})
    assert response.status_code == 200, f"Participant login failed: {response.text}"
    return response.json()["access_token"]

@pytest.fixture
def participant_id(client, admin_token, regular_user_data):
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get("/users", headers=headers)
    assert response.status_code == 200
    users = response.json()
    for u in users:
        if u["email"] == regular_user_data["email"]:
            return u["id"]
    pytest.fail("Participant user not found")

def test_admin_assign_and_remove_roles(client, admin_token, participant_id):
    headers = {"Authorization": f"Bearer {admin_token}"}
    # Assign judge role
    r = client.post(f"/users/{participant_id}/roles", headers=headers, json={"role": "judge"})
    assert r.status_code in (200, 201), r.text
    # Assign mentor role
    r = client.post(f"/users/{participant_id}/roles", headers=headers, json={"role": "mentor"})
    assert r.status_code in (200, 201), r.text
    # Get user and check roles
    r = client.get(f"/users/{participant_id}", headers=headers)
    assert r.status_code == 200
    roles = r.json()["roles"]
    # Should have at least participant, judge, mentor
    assert set(roles) >= {"participant", "judge", "mentor"}
    # Remove judge role
    import json
    r = client.request("DELETE", f"/users/{participant_id}/roles", headers={**headers, "Content-Type": "application/json"}, data=json.dumps({"role": "judge"}))
    assert r.status_code in (200, 204), r.text
    # Check roles again
    r = client.get(f"/users/{participant_id}", headers=headers)
    assert r.status_code == 200
    roles = r.json()["roles"]
    assert "judge" not in roles
    assert "mentor" in roles
    assert "participant" in roles

def test_participant_rights_update(client, admin_token, participant_token, participant_id):
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    user_headers = {"Authorization": f"Bearer {participant_token}"}
    # Assign judge role
    r = client.post(f"/users/{participant_id}/roles", headers=admin_headers, json={"role": "judge"})
    assert r.status_code in (200, 201)
    # Now participant should have judge rights (access /judging/check-judge)
    r = client.get("/judging/check-judge", headers=user_headers)
    assert r.status_code == 200  # Should succeed if judge role is present
    # Remove judge role
    import json
    r = client.request("DELETE", f"/users/{participant_id}/roles", headers={**admin_headers, "Content-Type": "application/json"}, data=json.dumps({"role": "judge"}))
    assert r.status_code in (200, 204)
    # Now participant should NOT have judge rights
    r = client.get("/judging/check-judge", headers=user_headers)
    assert r.status_code == 403  # Should fail if judge role is removed
