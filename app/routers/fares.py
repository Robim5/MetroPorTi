from fastapi import APIRouter, HTTPException, Query
from app.database import get_pool
from app.models.schemas import FareOut

router = APIRouter(tags=["fares"])

# usado para tarifas zona a zona
@router.get("/fare", response_model=FareOut)
async def fare(from_zone: str = Query(...), to_zone: str = Query(...)):
    pool = get_pool()
    async with pool.acquire() as conn:
        # junta regras de zona com preco em fare_attributes
        row = await conn.fetchrow(
            """
            SELECT fr.fare_id, fr.origin_id, fr.destination_id, fa.price, fa.currency_type
            FROM metro_fare_rules fr
            JOIN metro_fare_attributes fa ON fa.fare_id = fr.fare_id
            WHERE fr.origin_id = $1 AND fr.destination_id = $2
            LIMIT 1
            """,
            from_zone,
            to_zone,
        )
    if not row:
        raise HTTPException(status_code=404, detail="Tarifa não encontrada.")
    return FareOut(
        fare_id=row["fare_id"],
        origin_zone=row["origin_id"],
        destination_zone=row["destination_id"],
        price=row["price"],
        currency_type=row["currency_type"],
    )