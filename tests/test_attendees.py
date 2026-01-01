import pytest
from httpx import AsyncClient
import uuid

@pytest.mark.asyncio
async def test_register_and_waitlist_logic(client: AsyncClient, auth_headers: dict):
    """Test registration and waitlist enforcement"""
    event_data = {
        "title": f"Limited Capacity Event {uuid.uuid4()}",
        "start_date": "2026-07-01T10:00:00",
        "end_date": "2026-07-01T11:00:00",
        "capacity": 1
    }
    event_res = await client.post("/events", json=event_data, headers=auth_headers)
    assert event_res.status_code == 201
    event_id = event_res.json()["id"]

    reg_url = f"/events/{event_id}/register"
    res1 = await client.post(reg_url, headers=auth_headers)
    assert res1.status_code == 201
    assert res1.json()["attendee"]["status"] == "registered"

    user2_email = f"user2_{uuid.uuid4().hex[:8]}@example.com"
    user2 = {"email": user2_email, "full_name": "User Two", "password": "PassPassword123!", "role": "user"}
    signup_res = await client.post("/auth/signup", json=user2)
    assert signup_res.status_code == 201, f"User2 signup failed: {signup_res.json()}"
    login2_res = await client.post("/auth/login", json={"email": user2_email, "password": "PassPassword123!"})
    assert login2_res.status_code == 200, f"User2 login failed: {login2_res.json()}"
    token2 = login2_res.json()["access_token"]
    
    res2 = await client.post(reg_url, headers={"Authorization": f"Bearer {token2}"})
    assert res2.status_code == 201
    assert res2.json()["attendee"]["status"] == "waitlisted"
    assert res2.json()["waitlist_position"] == 1
    assert "waitlist" in res2.json()["message"].lower()
