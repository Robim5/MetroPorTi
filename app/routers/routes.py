from fastapi import APIRouter, Query
from app.database import get_pool
from app.models.schemas import PaginationMeta, RouteOut, RoutesPageOut
from app.utils.cache import cache

router = APIRouter(tags = ["routes"])

# usado para listar todas as linhas
@router.get("/routes", response_model=RoutesPageOut)
async def list_routes(page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=200)):
    cache_key = f"routes:{page}:{limit}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    offset = (page - 1) * limit
    pool = get_pool()
    async with pool.acquire() as conn:
        # conta total para paginacao
        total = await conn.fetchval("SELECT COUNT(*) FROM metro_routes")
        rows = await conn.fetch(
            """
            SELECT route_id, route_short_name, route_long_name, route_color, route_text_color
            FROM metro_routes
            ORDER BY route_short_name
            LIMIT $1 OFFSET $2
            """,
            limit,
            offset,
        )
        payload = RoutesPageOut(
            meta = PaginationMeta(page = page, limit = limit, total = total),
            items = [RouteOut(**dict(row)) for row in rows],
        )
        cache.set(cache_key, payload, ttl_seconds = 30)
        return payload
    