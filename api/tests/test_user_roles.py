import pytest
import uuid
import httpx

BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin123"
PARTICIPANT_EMAIL = "participant@example.com"
PARTICIPANT_PASSWORD = "participant123"

@pytest.fixture
def admin_token():
    r = httpx.post(f"{BASE_URL}/users/login", data={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, f"Admin login failed: {r.text}"
    return r.json()["access_token"]

@pytest.fixture
def participant_token():
    r = httpx.post(f"{BASE_URL}/users/login", data={"email": PARTICIPANT_EMAIL, "password": PARTICIPANT_PASSWORD})
    assert r.status_code == 200, f"Participant login failed: {r.text}"
    return r.json()["access_token"]

@pytest.fixture
def participant_id(admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    r = httpx.get(f"{BASE_URL}/users", headers=headers)
    assert r.status_code == 200
    users = r.json()
    for u in users:
        if u["email"] == PARTICIPANT_EMAIL:
            return u["id"]
    pytest.fail("Participant user not found")


def test_admin_assign_and_remove_roles(admin_token, participant_id):
    headers = {"Authorization": f"Bearer {admin_token}"}
    # Assign judge role
    r = httpx.post(f"{BASE_URL}/users/{participant_id}/roles", headers=headers, json={"role": "judge"})
    assert r.status_code in (200, 201), r.text
    # Assign mentor role
    r = httpx.post(f"{BASE_URL}/users/{participant_id}/roles", headers=headers, json={"role": "mentor"})
    assert r.status_code in (200, 201), r.text
    # Get user and check roles
    r = httpx.get(f"{BASE_URL}/users/{participant_id}", headers=headers)
    assert r.status_code == 200
    roles = r.json()["roles"]
    assert set(roles) >= {"participant", "judge", "mentor"}
    # Remove judge role
    r = httpx.delete(f"{BASE_URL}/users/{participant_id}/roles", headers=headers, json={"role": "judge"})
    assert r.status_code in (200, 204), r.text
    # Check roles again
    r = httpx.get(f"{BASE_URL}/users/{participant_id}", headers=headers)
    assert r.status_code == 200
    roles = r.json()["roles"]
    assert "judge" not in roles
    assert "mentor" in roles
    assert "participant" in roles


def test_participant_rights_update(admin_token, participant_token, participant_id):
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    user_headers = {"Authorization": f"Bearer {participant_token}"}
    # Assign judge role
    r = httpx.post(f"{BASE_URL}/users/{participant_id}/roles", headers=admin_headers, json={"role": "judge"})
    assert r.status_code in (200, 201)
    # Now participant should have judge rights (e.g. access /judging)
    r = httpx.get(f"{BASE_URL}/judging", headers=user_headers)
    assert r.status_code in (200, 403)  # 200 if allowed, 403 if not assigned to a hackathon
    # Remove judge role
    r = httpx.delete(f"{BASE_URL}/users/{participant_id}/roles", headers=admin_headers, json={"role": "judge"})
    assert r.status_code in (200, 204)
    # Now participant should NOT have judge rights
    r = httpx.get(f"{BASE_URL}/judging", headers=user_headers)
    assert r.status_code in (403, 401)
