import asyncio
import csv
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterable

import asyncpg
from dotenv import load_dotenv

load_dotenv()
DATA_DIR = Path("gtfs_data")
# inserções em lote reduzem drasticamente o tempo
BATCH_SIZE = 1000


def parse_date(v: str | None):
    if not v:
        return None
    return datetime.strptime(v.strip(), "%Y%m%d").date()


def to_int(v: str | None):
    if v is None or str(v).strip() == "":
        return None
    return int(v)


def to_float(v: str | None):
    if v is None or str(v).strip() == "":
        return None
    return float(v)


def to_bool(v: str | None) -> bool:
    return str(v or "").strip() in {"1", "true", "True"}


def read_rows(filename: str) -> list[dict[str, str]]:
    path = DATA_DIR / filename
    if not path.exists():
        print(f"[AVISO] Ficheiro em falta: {filename}")
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    print(f"  Lido {filename}: {len(rows)} linhas")
    return rows


async def ensure_calendar_service(conn: asyncpg.Connection, service_id: str) -> None:
    """GTFS pode referenciar service_id só em calendar_dates; criamos entrada mínima."""
    await conn.execute(
        """
        INSERT INTO metro_calendar(
          service_id, monday, tuesday, wednesday, thursday, friday, saturday, sunday,
          start_date, end_date
        )
        VALUES($1, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, '2000-01-01', '2099-12-31')
        ON CONFLICT(service_id) DO NOTHING
        """,
        service_id,
    )


async def insert_batches(
    conn: asyncpg.Connection,
    label: str,
    sql: str,
    records: Iterable[tuple[Any, ...]],
    batch_size: int = BATCH_SIZE,
) -> int:
    """Executa INSERT/UPSERT em lotes e mostra progresso."""
    batch: list[tuple[Any, ...]] = []
    total = 0
    started = time.perf_counter()

    async def flush() -> None:
        nonlocal total
        if not batch:
            return
        await conn.executemany(sql, batch)
        total += len(batch)
        batch.clear()
        elapsed = time.perf_counter() - started
        print(f"    {label}: {total} linhas ({elapsed:.1f}s)")

    for record in records:
        batch.append(record)
        if len(batch) >= batch_size:
            await flush()

    await flush()
    return total


async def main() -> None:
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL não definida no .env")

    if not DATA_DIR.exists():
        raise FileNotFoundError(f"Pasta {DATA_DIR} não existe.")

    conn = await asyncpg.connect(dsn=database_url)
    try:
        print("[1/10] metro_routes")
        await insert_batches(
            conn,
            "metro_routes",
            """
            INSERT INTO metro_routes(route_id, route_short_name, route_long_name, route_color, route_text_color)
            VALUES($1,$2,$3,$4,$5)
            ON CONFLICT(route_id) DO UPDATE SET
              route_short_name=EXCLUDED.route_short_name,
              route_long_name=EXCLUDED.route_long_name,
              route_color=EXCLUDED.route_color,
              route_text_color=EXCLUDED.route_text_color
            """,
            (
                (
                    r.get("route_id"),
                    r.get("route_short_name"),
                    r.get("route_long_name"),
                    r.get("route_color"),
                    r.get("route_text_color"),
                )
                for r in read_rows("routes.txt")
            ),
        )

        print("[2/10] metro_calendar")
        await insert_batches(
            conn,
            "metro_calendar",
            """
            INSERT INTO metro_calendar(
              service_id, monday, tuesday, wednesday, thursday, friday, saturday, sunday,
              start_date, end_date
            )
            VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
            ON CONFLICT(service_id) DO UPDATE SET
              monday=EXCLUDED.monday, tuesday=EXCLUDED.tuesday, wednesday=EXCLUDED.wednesday,
              thursday=EXCLUDED.thursday, friday=EXCLUDED.friday, saturday=EXCLUDED.saturday,
              sunday=EXCLUDED.sunday, start_date=EXCLUDED.start_date, end_date=EXCLUDED.end_date
            """,
            (
                (
                    r.get("service_id"),
                    to_bool(r.get("monday")),
                    to_bool(r.get("tuesday")),
                    to_bool(r.get("wednesday")),
                    to_bool(r.get("thursday")),
                    to_bool(r.get("friday")),
                    to_bool(r.get("saturday")),
                    to_bool(r.get("sunday")),
                    parse_date(r.get("start_date")),
                    parse_date(r.get("end_date")),
                )
                for r in read_rows("calendar.txt")
            ),
        )

        print("[3/10] metro_stops")
        await insert_batches(
            conn,
            "metro_stops",
            """
            INSERT INTO metro_stops(stop_id, stop_code, stop_name, stop_lat, stop_lon, zone_id)
            VALUES($1,$2,$3,$4,$5,$6)
            ON CONFLICT(stop_id) DO UPDATE SET
              stop_code=EXCLUDED.stop_code, stop_name=EXCLUDED.stop_name,
              stop_lat=EXCLUDED.stop_lat, stop_lon=EXCLUDED.stop_lon, zone_id=EXCLUDED.zone_id
            """,
            (
                (
                    r.get("stop_id"),
                    r.get("stop_code"),
                    r.get("stop_name"),
                    to_float(r.get("stop_lat")),
                    to_float(r.get("stop_lon")),
                    r.get("zone_id"),
                )
                for r in read_rows("stops.txt")
            ),
        )

        print("[4/10] metro_shapes")
        await insert_batches(
            conn,
            "metro_shapes",
            """
            INSERT INTO metro_shapes(shape_id, shape_pt_lat, shape_pt_lon, shape_pt_sequence)
            VALUES($1,$2,$3,$4)
            ON CONFLICT(shape_id, shape_pt_sequence) DO NOTHING
            """,
            (
                (
                    r.get("shape_id"),
                    to_float(r.get("shape_pt_lat")),
                    to_float(r.get("shape_pt_lon")),
                    to_int(r.get("shape_pt_sequence")),
                )
                for r in read_rows("shapes.txt")
            ),
        )

        print("[5/10] metro_fare_attributes")
        await insert_batches(
            conn,
            "metro_fare_attributes",
            """
            INSERT INTO metro_fare_attributes(fare_id, price, currency_type, payment_method, transfers)
            VALUES($1,$2,$3,$4,$5)
            ON CONFLICT(fare_id) DO UPDATE SET
              price=EXCLUDED.price,
              currency_type=EXCLUDED.currency_type,
              payment_method=EXCLUDED.payment_method,
              transfers=EXCLUDED.transfers
            """,
            (
                (
                    r.get("fare_id"),
                    float(r.get("price") or 0),
                    r.get("currency_type") or "EUR",
                    to_int(r.get("payment_method")),
                    to_int(r.get("transfers")),
                )
                for r in read_rows("fare_attributes.txt")
            ),
        )

        print("[6/10] metro_calendar_dates")
        calendar_date_rows = read_rows("calendar_dates.txt")
        known_services = {
            r["service_id"]
            for r in await conn.fetch("SELECT service_id FROM metro_calendar")
        }
        for row in calendar_date_rows:
            sid = row.get("service_id")
            if sid and sid not in known_services:
                await ensure_calendar_service(conn, sid)
                known_services.add(sid)
                print(f"  [INFO] calendar criado para service_id em falta: {sid}")

        await insert_batches(
            conn,
            "metro_calendar_dates",
            """
            INSERT INTO metro_calendar_dates(service_id, date, exception_type)
            VALUES($1,$2,$3)
            ON CONFLICT(service_id, date) DO UPDATE SET
              exception_type=EXCLUDED.exception_type
            """,
            (
                (
                    r.get("service_id"),
                    parse_date(r.get("date")),
                    to_int(r.get("exception_type")),
                )
                for r in calendar_date_rows
            ),
        )

        print("[7/10] metro_trips")
        await insert_batches(
            conn,
            "metro_trips",
            """
            INSERT INTO metro_trips(
              trip_id, route_id, service_id, trip_headsign, direction_id, shape_id, wheelchair_accessible
            )
            VALUES($1,$2,$3,$4,$5,$6,$7)
            ON CONFLICT(trip_id) DO UPDATE SET
              route_id=EXCLUDED.route_id, service_id=EXCLUDED.service_id,
              trip_headsign=EXCLUDED.trip_headsign, direction_id=EXCLUDED.direction_id,
              shape_id=EXCLUDED.shape_id, wheelchair_accessible=EXCLUDED.wheelchair_accessible
            """,
            (
                (
                    r.get("trip_id"),
                    r.get("route_id"),
                    r.get("service_id"),
                    r.get("trip_headsign"),
                    to_int(r.get("direction_id")),
                    r.get("shape_id"),
                    to_int(r.get("wheelchair_accessible")) or 0,
                )
                for r in read_rows("trips.txt")
            ),
        )

        print("[8/10] metro_fare_rules")
        await insert_batches(
            conn,
            "metro_fare_rules",
            """
            INSERT INTO metro_fare_rules(fare_id, origin_id, destination_id)
            VALUES($1,$2,$3)
            ON CONFLICT(fare_id, origin_id, destination_id) DO NOTHING
            """,
            (
                (
                    r.get("fare_id"),
                    r.get("origin_id") or None,
                    r.get("destination_id") or None,
                )
                for r in read_rows("fare_rules.txt")
            ),
        )

        print("[9/10] metro_transfers")
        await insert_batches(
            conn,
            "metro_transfers",
            """
            INSERT INTO metro_transfers(from_stop_id, to_stop_id, transfer_type)
            VALUES($1,$2,$3)
            ON CONFLICT(from_stop_id, to_stop_id) DO UPDATE SET
              transfer_type=EXCLUDED.transfer_type
            """,
            (
                (
                    r.get("from_stop_id"),
                    r.get("to_stop_id"),
                    to_int(r.get("transfer_type")) or 0,
                )
                for r in read_rows("transfers.txt")
            ),
        )

        print("[10/10] metro_stop_times (ficheiro grande — pode demorar 1-3 min)")
        await insert_batches(
            conn,
            "metro_stop_times",
            """
            INSERT INTO metro_stop_times(
              trip_id, stop_id, arrival_time, departure_time, stop_sequence, stop_headsign
            )
            VALUES($1,$2,$3,$4,$5,$6)
            ON CONFLICT(trip_id, stop_sequence) DO UPDATE SET
              stop_id=EXCLUDED.stop_id,
              arrival_time=EXCLUDED.arrival_time,
              departure_time=EXCLUDED.departure_time,
              stop_headsign=EXCLUDED.stop_headsign
            """,
            (
                (
                    r.get("trip_id"),
                    r.get("stop_id"),
                    r.get("arrival_time"),
                    r.get("departure_time"),
                    to_int(r.get("stop_sequence")),
                    r.get("stop_headsign"),
                )
                for r in read_rows("stop_times.txt")
            ),
        )

        print("\n[OK] Importação GTFS concluída.")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
