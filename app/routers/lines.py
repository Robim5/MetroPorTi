from fastapi import APIRouter, HTTPException, Query
from app.database import get_pool
from app.models.schemas import JourneyLegOut, JourneyOut, LineStopsOut, StopOnLineOut
from app.utils.cache import cache

router = APIRouter(tags=["lines"])

@router.get("/lines/{route_id}/stops", response_model=LineStopsOut)
async def line_stops(
    route_id: str,
    direction_id: int = Query(0, ge=0, le=1, description="0=ida, 1=volta"),
):
    cache_key = f"line_stops:{route_id}:{direction_id}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    pool = get_pool()
    async with pool.acquire() as conn:
        route = await conn.fetchrow(
            """
            SELECT route_id, route_short_name
            FROM metro_routes WHERE route_id = $1
            """,
            route_id,
        )
        if not route:
            raise HTTPException(status_code=404, detail="Linha não encontrada.")

        trip = await conn.fetchrow(
            """
            SELECT trip_id, trip_headsign
            FROM metro_trips
            WHERE route_id = $1 AND direction_id = $2
            ORDER BY trip_id
            LIMIT 1
            """,
            route_id,
            direction_id,
        )
        if not trip:
            trip = await conn.fetchrow(
                """
                SELECT trip_id, trip_headsign
                FROM metro_trips WHERE route_id = $1
                ORDER BY trip_id LIMIT 1
                """,
                route_id,
            )
        if not trip:
            raise HTTPException(status_code=404, detail="Sem viagens para esta linha.")

        rows = await conn.fetch(
            """
            SELECT st.stop_id, s.stop_name, s.stop_lat, s.stop_lon, s.zone_id, st.stop_sequence
            FROM metro_stop_times st
            JOIN metro_stops s ON s.stop_id = st.stop_id
            WHERE st.trip_id = $1
            ORDER BY st.stop_sequence
            """,
            trip["trip_id"],
        )

    payload = LineStopsOut(
        route_id=route["route_id"],
        route_short_name=route["route_short_name"],
        direction_id=direction_id,
        destination=trip["trip_headsign"],
        stops=[StopOnLineOut(**dict(r)) for r in rows],
    )
    cache.set(cache_key, payload, ttl_seconds=300)
    return payload


@router.get("/journey", response_model=JourneyOut)
async def plan_journey(
    from_stop_id: str = Query(..., description="Paragem de origem"),
    to_stop_id: str = Query(..., description="Paragem de destino"),
):
    if from_stop_id == to_stop_id:
        raise HTTPException(status_code=400, detail="Origem e destino devem ser diferentes.")

    pool = get_pool()
    async with pool.acquire() as conn:
        stops = await conn.fetch(
            """
            SELECT stop_id, stop_name FROM metro_stops
            WHERE stop_id = ANY($1::text[])
            """,
            [from_stop_id, to_stop_id],
        )
        if len(stops) != 2:
            raise HTTPException(status_code=404, detail="Paragem de origem ou destino não encontrada.")

        names = {s["stop_id"]: s["stop_name"] for s in stops}

        rows = await conn.fetch(
            """
            SELECT r.route_id, r.route_short_name,
                   st1.stop_id AS from_stop, st2.stop_id AS to_stop,
                   st1.departure_time, st2.arrival_time,
                   (st2.stop_sequence - st1.stop_sequence) AS stops_between
            FROM metro_stop_times st1
            JOIN metro_stop_times st2
              ON st1.trip_id = st2.trip_id AND st1.stop_sequence < st2.stop_sequence
            JOIN metro_trips t ON t.trip_id = st1.trip_id
            JOIN metro_routes r ON r.route_id = t.route_id
            WHERE st1.stop_id = $1 AND st2.stop_id = $2
            ORDER BY st1.departure_time
            LIMIT 10
            """,
            from_stop_id,
            to_stop_id,
        )

    legs = [
        JourneyLegOut(
            route_id=row["route_id"],
            route_short_name=row["route_short_name"],
            from_stop_id=row["from_stop"],
            from_stop_name=names[row["from_stop"]],
            to_stop_id=row["to_stop"],
            to_stop_name=names[row["to_stop"]],
            departure_time=row["departure_time"],
            arrival_time=row["arrival_time"],
            stops_between=row["stops_between"],
        )
        for row in rows
    ]

    return JourneyOut(
        from_stop_id=from_stop_id,
        to_stop_id=to_stop_id,
        direct=len(legs) > 0,
        legs=legs,
    )
