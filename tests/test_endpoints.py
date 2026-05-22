import os
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from app.database import close_db_pool, init_db_pool
from app.main import app


def _auth_params() -> dict:
    key = os.getenv("API_KEY", "").strip()
    return {"api_key": key} if key else {}


@pytest_asyncio.fixture
async def client():
    await init_db_pool()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    await close_db_pool()


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_search_stops(client):
    response = await client.get("/search/stops", params={**_auth_params(), "q": "Maia"})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any("Maia" in s["stop_name"] for s in data)


@pytest.mark.asyncio
async def test_next_with_route_filter(client):
    response = await client.get(
        "/stops/5756/next", params={**_auth_params(), "limit": 5, "route_id": "C"}
    )
    assert response.status_code == 200
    data = response.json()
    assert all(item["route_short_name"] == "C" for item in data)


@pytest.mark.asyncio
async def test_line_stops(client):
    response = await client.get(
        "/lines/C/stops", params={**_auth_params(), "direction_id": 0}
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["route_id"] == "C"
    assert len(payload["stops"]) > 0


@pytest.mark.asyncio
async def test_nearby_stops(client):
    response = await client.get(
        "/stops/nearby",
        params={**_auth_params(), "lat": 41.2346, "lon": -8.6239, "radius_m": 2000, "limit": 5},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert "distance_m" in data[0]


@pytest.mark.asyncio
async def test_departure_board(client):
    response = await client.get(
        "/stops/5760/board", params={**_auth_params(), "per_line": 2}
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["stop_id"] == "5760"
    assert "departures" in payload


@pytest.mark.asyncio
async def test_journey(client):
    response = await client.get(
        "/journey",
        params={**_auth_params(), "from_stop_id": "5760", "to_stop_id": "5726"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["from_stop_id"] == "5760"
    assert payload["to_stop_id"] == "5726"
