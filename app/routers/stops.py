from fastapi import APIRouter, HTTPException, Query
from app.database import get_pool
from app.models.schemas import (
    BoardDepartureOut,
    DepartureBoardOut,
    NearbyStopOut,
    PaginationMeta,
    StopOut,
    StopsPageOut,
)
from app.utils.cache import cache
from app.utils.schedule_logic import build_upcoming_arrivals, fetch_upcoming_at_stop, weekday_column
from app.utils.time_helpers import now_local_seconds
from datetime import datetime
from zoneinfo import ZoneInfo

router = APIRouter(tags=["stops"])
LISBON_TZ = ZoneInfo("Europe/Lisbon")


@router.get("/stops", response_model=StopsPageOut)
async def list_stops(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
):
    cache_key = f"stops:{page}:{limit}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    offset = (page - 1) * limit
    pool = get_pool()
    async with pool.acquire() as conn:
        total = await conn.fetchval("SELECT COUNT(*) FROM metro_stops")
        rows = await conn.fetch(
            """
            SELECT stop_id, stop_name, stop_lat, stop_lon, zone_id
            FROM metro_stops
            ORDER BY stop_name
            LIMIT $1 OFFSET $2
            """,
            limit,
            offset,
        )

    payload = StopsPageOut(
        meta=PaginationMeta(page=page, limit=limit, total=total),
        items=[StopOut(**dict(row)) for row in rows],
    )
    cache.set(cache_key, payload, ttl_seconds=30)
    return payload


@router.get("/search/stops", response_model=list[StopOut])
async def search_stops(q: str = Query(..., min_length=2, max_length=100)):
    cache_key = f"search_stops:{q.lower()}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT stop_id, stop_name, stop_lat, stop_lon, zone_id
            FROM metro_stops
            WHERE stop_name ILIKE '%' || $1 || '%'
            ORDER BY stop_name
            LIMIT 30
            """,
            q,
        )
    items = [StopOut(**dict(row)) for row in rows]
    cache.set(cache_key, items, ttl_seconds=30)
    return items


@router.get("/stops/nearby", response_model=list[NearbyStopOut])
async def nearby_stops(
    lat: float = Query(..., ge=-90, le=90, description="Latitude GPS"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude GPS"),
    radius_m: int = Query(800, ge=100, le=5000, description="Raio em metros"),
    limit: int = Query(10, ge=1, le=30),
):
    cache_key = f"nearby:{lat:.5f}:{lon:.5f}:{radius_m}:{limit}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT stop_id, stop_name, stop_lat, stop_lon, zone_id,
              ROUND(
                6371000 * acos(
                  LEAST(1.0, GREATEST(-1.0,
                    cos(radians($1)) * cos(radians(stop_lat))
                    * cos(radians(stop_lon) - radians($2))
                    + sin(radians($1)) * sin(radians(stop_lat))
                  ))
                )
              )::int AS distance_m
            FROM metro_stops
            WHERE (
              6371000 * acos(
                LEAST(1.0, GREATEST(-1.0,
                  cos(radians($1)) * cos(radians(stop_lat))
                  * cos(radians(stop_lon) - radians($2))
                  + sin(radians($1)) * sin(radians(stop_lat))
                ))
              )
            ) <= $3
            ORDER BY distance_m
            LIMIT $4
            """,
            lat,
            lon,
            radius_m,
            limit,
        )

    items = [NearbyStopOut(**dict(row)) for row in rows]
    cache.set(cache_key, items, ttl_seconds=60)
    return items


@router.get("/stops/{stop_id}/board", response_model=DepartureBoardOut)
async def departure_board(
    stop_id: str,
    per_line: int = Query(2, ge=1, le=5, description="Próximas partidas por linha/sentido"),
):
    now = datetime.now(LISBON_TZ)
    today = now.date()
    now_seconds = now_local_seconds()

    pool = get_pool()
    async with pool.acquire() as conn:
        stop = await conn.fetchrow(
            "SELECT stop_id, stop_name FROM metro_stops WHERE stop_id = $1",
            stop_id,
        )
        if not stop:
            raise HTTPException(status_code=404, detail="Paragem não encontrada.")

    rows = await fetch_upcoming_at_stop(stop_id, today, weekday_column(now))
    upcoming = build_upcoming_arrivals(rows, limit=80, now_seconds=now_seconds)

    seen: dict[tuple, int] = {}
    board: list[BoardDepartureOut] = []
    for item in upcoming:
        key = (item.route_short_name, item.destination)
        if seen.get(key, 0) >= per_line:
            continue
        seen[key] = seen.get(key, 0) + 1
        color = next((r["route_color"] for r in rows if r["route_id"] == item.route_id), None)
        board.append(
            BoardDepartureOut(
                route_id=item.route_id,
                route_short_name=item.route_short_name,
                route_color=color,
                destination=item.destination,
                departure_time=item.departure_time,
                eta_minutes=item.eta_minutes,
            )
        )

    return DepartureBoardOut(
        stop_id=stop["stop_id"],
        stop_name=stop["stop_name"],
        departures=board,
    )


@router.get("/stops/{stop_id}", response_model=StopOut)
async def get_stop(stop_id: str):
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT stop_id, stop_name, stop_lat, stop_lon, zone_id
            FROM metro_stops WHERE stop_id = $1
            """,
            stop_id,
        )
    if not row:
        raise HTTPException(status_code=404, detail="Paragem não encontrada.")
    return StopOut(**dict(row))
