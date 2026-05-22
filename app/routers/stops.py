from fastapi import APIRouter, HTTPException, Query
from app.database import get_pool
from app.models.schemas import PaginationMeta, StopOut, StopsPageOut
from app.utils.cache import cache

router = APIRouter()

# usado para listar todas as paragens
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
        total = await conn.fetchval("SELECT COUNT(*) FROM stops")
        rows = await conn.fetch(
            """
            SELECT stop_id, stop_name, stop_lat, stop_lon, zone_id
            FROM stops
            ORDER BY stop_name
            LIMIT $1 OFFSET $2
            """,
            limit,
            offset,
        )
        
    payload = StopsPageOut(
        meta = PaginationMeta(page = page, limit = limit, total = total),
        items = [StopOut(**dict(row)) for row in rows],
    )
    # guarda 30s, listas mudam pouco
    cache.set(cache_key, payload, ttl_seconds = 30)
    return payload

# usado para obter uma paragem específica
@router.get("/stops/{stop_id}", response_model=StopOut)
async def get_stop(stop_id: str):
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT stop_id, stop_name, stop_lat, stop_lon, zone_id
            FROM stops
            WHERE stop_id = $1
            """,
            stop_id,
        )
    if not row:
        raise HTTPException(status_code = 404, detail = "Paragem nao encontrada")
    return StopOut(**dict(row))

# usado para pesquisar paragens
@router.get("/search/stops", response_model=list[StopOut])
async def search_stops(q: str = Query(..., min_length = 2, max_length = 100)):
    cache_key = f"search_stops:{q.lower()}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT stop_id, stop_name, stop_lat, stop_lon, zone_id
            FROM stops
            WHERE stop_name ILIKE '%' || $1 || '%'
            ORDER BY stop_name
            LIMIT 30
            """,
            q,
        )
    items = [StopOut(**dict(row)) for row in rows]
    cache.set(cache_key, items, ttl_seconds = 30)
    return items