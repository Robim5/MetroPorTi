from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import APIRouter, HTTPException, Query
from app.database import get_pool
from app.models.schemas import NextArrivalOut, StopScheduleGroupOut
from app.utils.cache import cache
from app.utils.schedule_logic import (
    build_upcoming_arrivals,
    fetch_upcoming_at_stop,
    weekday_column,
)
from app.utils.time_helpers import now_local_seconds

router = APIRouter(tags=["schedule"])
LISBON_TZ = ZoneInfo("Europe/Lisbon")


@router.get("/stops/{stop_id}/schedule", response_model=list[StopScheduleGroupOut])
async def stop_schedule(stop_id: str):
    pool = get_pool()
    async with pool.acquire() as conn:
        exists = await conn.fetchval("SELECT 1 FROM stops WHERE stop_id = $1", stop_id)
        if not exists:
            raise HTTPException(status_code=404, detail="Paragem não encontrada.")
        rows = await conn.fetch(
            """
            SELECT r.route_id, r.route_short_name, t.direction_id, t.trip_headsign, st.departure_time
            FROM stop_times st
            JOIN trips t ON t.trip_id = st.trip_id
            JOIN routes r ON r.route_id = t.route_id
            WHERE st.stop_id = $1
            ORDER BY r.route_short_name, t.direction_id, st.departure_time
            """,
            stop_id,
        )
    grouped = defaultdict(list)
    for row in rows:
        key = (row["route_id"], row["route_short_name"], row["direction_id"], row["trip_headsign"])
        grouped[key].append(row["departure_time"])
    return [
        StopScheduleGroupOut(
            route_id=k[0], route_short_name=k[1], direction_id=k[2], destination=k[3], departures=v
        )
        for k, v in grouped.items()
    ]


@router.get("/stops/{stop_id}/next", response_model=list[NextArrivalOut])
async def next_arrivals(
    stop_id: str,
    limit: int = Query(5, ge=1, le=20),
    route_id: str | None = Query(None, description="Filtrar por linha, ex: C"),
):
    now = datetime.now(LISBON_TZ)
    today = now.date()
    now_seconds = now_local_seconds()
    cache_key = f"next:{stop_id}:{limit}:{route_id}:{today}:{now.hour}:{now.minute}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    rows = await fetch_upcoming_at_stop(stop_id, today, weekday_column(now))
    result = build_upcoming_arrivals(
        rows, limit=limit, now_seconds=now_seconds, route_id=route_id
    )
    cache.set(cache_key, result, ttl_seconds=20)
    return result


@router.get("/stops/{stop_id}/arrivals", response_model=list[NextArrivalOut])
async def arrivals_filtered(
    stop_id: str,
    destination: str = Query(..., min_length=2, max_length=120),
    route_id: str | None = Query(None, description="Filtrar por linha, ex: C"),
    limit: int = Query(10, ge=1, le=20),
):
    now = datetime.now(LISBON_TZ)
    today = now.date()
    now_seconds = now_local_seconds()
    rows = await fetch_upcoming_at_stop(stop_id, today, weekday_column(now))
    return build_upcoming_arrivals(
        rows,
        limit=limit,
        now_seconds=now_seconds,
        route_id=route_id,
        destination_contains=destination,
    )
