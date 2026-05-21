from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import APIRouter, HTTPException, Query
from app.database import get_pool
from app.models.schemas import VehiclePositionOut
from app.utils.time_helpers import gtfs_time_to_seconds, now_local_seconds

router = APIRouter(tags=["vehicle"])
LISBON_TZ = ZoneInfo("Europe/Lisbon")

# usado para posição do veículo
@router.get("/vehicle/position", response_model=VehiclePositionOut)
async def vehicle_position(route_id: str = Query(..., min_length=1, max_length=20)):
    now = datetime.now(LISBON_TZ)
    now_seconds = now_local_seconds()
    today = now.date()

    pool = get_pool()
    async with pool.acquire() as conn:
        # primeira viagem activa hoje nesta linha, estimativa simples
        trip = await conn.fetchrow(
            """
            SELECT t.trip_id
            FROM trips t
            JOIN calendar c ON c.service_id = t.service_id
            WHERE t.route_id = $1 AND $2 BETWEEN c.start_date AND c.end_date
            LIMIT 1
            """,
            route_id,
            today,
        )
        if not trip:
            raise HTTPException(status_code=404, detail="Sem viagem ativa para esta linha.")

        rows = await conn.fetch(
            """
            SELECT st.stop_id, s.stop_name, st.departure_time, st.stop_sequence
            FROM stop_times st
            JOIN stops s ON s.stop_id = st.stop_id
            WHERE st.trip_id = $1
            ORDER BY st.stop_sequence
            """,
            trip["trip_id"],
        )

    # percorre paragens por ordem ate achar ultima passada e proxima
    last_stop = None
    next_stop = None
    for row in rows:
        dep_seconds = gtfs_time_to_seconds(row["departure_time"])
        if dep_seconds <= now_seconds:
            last_stop = row
        elif next_stop is None:
            next_stop = row
            break

    if last_stop is None:
        first = rows[0]
        return VehiclePositionOut(
            route_id=route_id,
            trip_id=trip["trip_id"],
            next_stop_id=first["stop_id"],
            next_stop_name=first["stop_name"],
            progress_percent=0.0,
        )

    if next_stop is None:
        return VehiclePositionOut(
            route_id=route_id,
            trip_id=trip["trip_id"],
            last_stop_id=last_stop["stop_id"],
            last_stop_name=last_stop["stop_name"],
            progress_percent=100.0,
        )

    # percentagem linear entre hora da ultima e da proxima paragem
    last_t = gtfs_time_to_seconds(last_stop["departure_time"])
    next_t = gtfs_time_to_seconds(next_stop["departure_time"])
    span = max(1, next_t - last_t)
    progress = ((now_seconds - last_t) / span) * 100
    progress = max(0.0, min(100.0, progress))
    return VehiclePositionOut(
        route_id=route_id,
        trip_id=trip["trip_id"],
        last_stop_id=last_stop["stop_id"],
        last_stop_name=last_stop["stop_name"],
        next_stop_id=next_stop["stop_id"],
        next_stop_name=next_stop["stop_name"],
        progress_percent=round(progress, 2),
    )