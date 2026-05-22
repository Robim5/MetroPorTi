from datetime import date, datetime
from fastapi import HTTPException
from app.database import get_pool
from app.models.schemas import NextArrivalOut
from app.utils.time_helpers import gtfs_time_to_seconds, minutes_until, now_local_seconds

LISBON_WEEKDAYS = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]


def weekday_column(now: datetime) -> str:
    return LISBON_WEEKDAYS[now.weekday()]


def build_upcoming_arrivals(
    rows: list,
    *,
    limit: int,
    now_seconds: int,
    route_id: str | None = None,
    destination_contains: str | None = None,
) -> list[NextArrivalOut]:
    result: list[NextArrivalOut] = []
    needle = destination_contains.lower() if destination_contains else None

    for row in rows:
        if route_id and row["route_id"] != route_id:
            continue
        if needle and needle not in (row["trip_headsign"] or "").lower():
            continue

        dep_seconds = gtfs_time_to_seconds(row["departure_time"])
        if dep_seconds < now_seconds:
            continue

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
    return result


ACTIVE_SERVICES_SQL = """
WITH service_base AS (
  SELECT c.service_id, c.{weekday_col} AS runs_today
  FROM calendar c
  WHERE $1::date BETWEEN c.start_date AND c.end_date
),
service_active AS (
  SELECT sb.service_id
  FROM service_base sb
  LEFT JOIN calendar_dates cd
    ON cd.service_id = sb.service_id AND cd.date = $1::date
  WHERE (cd.exception_type = 1) OR (cd.exception_type IS NULL AND sb.runs_today = TRUE)
  EXCEPT
  SELECT cd2.service_id FROM calendar_dates cd2
  WHERE cd2.date = $1::date AND cd2.exception_type = 2
)
SELECT r.route_id, r.route_short_name, r.route_color, t.trip_id, t.trip_headsign, st.departure_time
FROM stop_times st
JOIN trips t ON t.trip_id = st.trip_id
JOIN routes r ON r.route_id = t.route_id
JOIN service_active sa ON sa.service_id = t.service_id
WHERE st.stop_id = $2
ORDER BY st.departure_time
LIMIT 300
"""


async def fetch_upcoming_at_stop(stop_id: str, today: date, weekday_col: str):
    pool = get_pool()
    async with pool.acquire() as conn:
        exists = await conn.fetchval("SELECT 1 FROM stops WHERE stop_id = $1", stop_id)
        if not exists:
            raise HTTPException(status_code=404, detail="Paragem não encontrada.")
        sql = ACTIVE_SERVICES_SQL.format(weekday_col=weekday_col)
        return await conn.fetch(sql, today, stop_id)
