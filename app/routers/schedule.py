from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import APIRouter, HTTPException, Query
from app.database import get_pool
from app.models.schemas import NextArrivalOut, StopScheduleGroupOut
from app.utils.cache import cache
from app.utils.time_helpers import gtfs_time_to_seconds, minutes_until, now_local_seconds

router = APIRouter(tags = ["schedule"])
LISBON_TZ = ZoneInfo("Europe/Lisbon")

# nome da coluna no calendar conforme o dia da semana
def _weekday_col(now: datetime) -> str:
    return ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"][now.weekday()]

# usado para horários de paragens
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
    # agrupa partidas por linha e sentido para o json
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

# usado para próximos horários de paragens
@router.get("/stops/{stop_id}/next", response_model=list[NextArrivalOut])
async def next_arrivals(stop_id: str, limit: int = Query(5, ge=1, le=20)):
    now = datetime.now(LISBON_TZ)
    weekday_col = _weekday_col(now)
    today = now.date()
    now_seconds = now_local_seconds()
    cache_key = f"next:{stop_id}:{limit}:{today}:{now.hour}:{now.minute}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    pool = get_pool()
    async with pool.acquire() as conn:
        # cte filtra servicos que correm hoje, feriados e excepcoes gtfs
        rows = await conn.fetch(
            f"""
            WITH service_base AS (
              SELECT c.service_id, c.{weekday_col} AS runs_today
              FROM calendar c
              WHERE $1 BETWEEN c.start_date AND c.end_date
            ),
            service_active AS (
              SELECT sb.service_id
              FROM service_base sb
              LEFT JOIN calendar_dates cd
                ON cd.service_id = sb.service_id
               AND cd.date = $1
              WHERE (cd.exception_type = 1) OR (cd.exception_type IS NULL AND sb.runs_today = TRUE)
              EXCEPT
              SELECT cd2.service_id FROM calendar_dates cd2
              WHERE cd2.date = $1 AND cd2.exception_type = 2
            )
            SELECT r.route_id, r.route_short_name, t.trip_id, t.trip_headsign, st.departure_time
            FROM stop_times st
            JOIN trips t ON t.trip_id = st.trip_id
            JOIN routes r ON r.route_id = t.route_id
            JOIN service_active sa ON sa.service_id = t.service_id
            WHERE st.stop_id = $2
            ORDER BY st.departure_time
            LIMIT 250
            """,
            today,
            stop_id,
        )

    result: list[NextArrivalOut] = []
    for row in rows:
        dep_seconds = gtfs_time_to_seconds(row["departure_time"])
        # so partidas ainda por vir, compara com hora local
        if dep_seconds >= now_seconds:
            result.append(
                NextArrivalOut(
                    route_id=row["route_id"],
                    route_short_name=row["route_short_name"],
                    trip_id=row["trip_id"],
                    destination=row["trip_headsign"],
                    departure_time=row["departure_time"],
                    eta_minutes=minutes_until(dep_seconds, now_seconds),
                )
            )
        if len(result) >= limit:
            break
    cache.set(cache_key, result, ttl_seconds=20)
    return result

# usado para horários de paragens filtrados por destino
@router.get("/stops/{stop_id}/arrivals", response_model=list[NextArrivalOut])
async def arrivals_filtered(stop_id: str, destination: str = Query(..., min_length=2, max_length=120)):
    # reutiliza next e filtra por texto no destino
    upcoming = await next_arrivals(stop_id=stop_id, limit=25)
    needle = destination.lower()
    return [item for item in upcoming if needle in (item.destination or "").lower()]