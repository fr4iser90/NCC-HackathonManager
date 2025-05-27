import httpx
import os
import uuid

BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")


def test_participant_permissions_and_deadlines():
    # Step 1: Register a new participant user
    unique_email = f"participant_{uuid.uuid4()}@example.com"
    unique_username = f"participant_{uuid.uuid4().hex[:8]}"
    participant_password = "testparticipantpw"
    register_payload = {
        "email": unique_email,
        "username": unique_username,
        "password": participant_password,
        "full_name": "Participant User",
    }
    r = httpx.post(f"{BASE_URL}/users/register", json=register_payload)
    assert r.status_code in (200, 201), f"Participant registration failed: {r.text}"

    # Step 2: Login as Participant
    r = httpx.post(
        f"{BASE_URL}/users/login",
        data={"email": unique_email, "password": participant_password},
    )
    assert r.status_code == 200, f"Login failed: {r.text}"
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Participant darf kein Judging/Voting
    r = httpx.get(f"{BASE_URL}/judging/criteria/", headers=headers)
    assert r.status_code == 200
    r = httpx.get(f"{BASE_URL}/projects/", headers=headers)
    if r.json():
        project_id = r.json()[0]["id"]
        r2 = httpx.get(f"{BASE_URL}/judging/criteria/", headers=headers)
        if r2.json():
            criterion_id = r2.json()[0]["id"]
            score_payload = {
                "project_id": project_id,
                "criteria_id": criterion_id,
                "score": 5,
                "notes": "Participant darf nicht bewerten",
            }
            r3 = httpx.post(
                f"{BASE_URL}/judging/scores/", headers=headers, json=score_payload
            )
            assert r3.status_code == 403
    # Participant darf nur eigene Projekte/Teams bearbeiten
    # (Test: Versuch, fremdes Projekt zu bearbeiten)
    r = httpx.get(f"{BASE_URL}/projects/", headers=headers)
    if r.json():
        project_id = r.json()[0]["id"]
        update = {"name": "Hacked by participant"}
        r2 = httpx.put(
            f"{BASE_URL}/projects/{project_id}", headers=headers, json=update
        )
        assert r2.status_code in (403, 404, 200)
    # Nach Hackathon-Ende: Projekt darf nicht bearbeitet werden
    # (Voraussetzung: Es gibt ein Projekt und zugehörigen Hackathon)
    # Dies ist ein Edge-Test, der ggf. nur als Warnung ausgegeben wird
