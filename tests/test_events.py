import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_event_success(client: AsyncClient, auth_headers: dict):
    """Test successful event creation by an organizer"""
    import uuid
    unique_title = f"Senior Workshop {uuid.uuid4().hex[:8]}"
    event_data = {
        "title": unique_title,
        "description": "A deep dive into scalable backend design",
        "start_date": "2026-06-01T10:00:00",
        "end_date": "2026-06-01T18:00:00",
        "location": "Remote",
        "capacity": 50
    }
    
    response = await client.post("/events", json=event_data, headers=auth_headers)
    
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == event_data["title"]
    assert data["capacity"] == 50
    assert "id" in data
    assert len(data["organizer_ids"]) > 0

@pytest.mark.asyncio
async def test_create_event_unauthorized(client: AsyncClient):
    """Test that event creation fails without authentication"""
    import uuid
    event_data = {
        "title": f"Unauth Event {uuid.uuid4().hex[:8]}",
        "start_date": "2026-06-01T10:00:00",
        "end_date": "2026-06-01T18:00:00"
    }
    response = await client.post("/events", json=event_data)
    assert response.status_code == 403
