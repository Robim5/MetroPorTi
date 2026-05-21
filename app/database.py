import os
from typing import Optional
import asyncpg
from dotenv import load_dotenv

load_dotenv()

# uma instancia de pool para toda a app, reutiliza ligacoes
_pool: Optional[asyncpg.Pool] = None

def _get_database_url() -> str:
    # tenta nao arrancar sem ligação valida
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL nao esta defenida")
    # neon precisa de ssl entao valida-se cedo para erro legivel
    if "sslmode=require" not in database_url:
        raise RuntimeError("DATABASE_URL nao esta configurada para ssl")
    return database_url

# cria ligacoes reutilizaveis, min 1 max 10 por pedido
async def init_db_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            dsn = _get_database_url(),
            min_size = 1,
            max_size = 10,
            command_timeout = 30,
        )
    return _pool

# devolve pool ja criado, os routers chamam isto
def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Pool nao foi inicializado. Executa init_db_pool primeiro")
    return _pool

# encerra todas as ligacoes ao desligar a app
async def close_db_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None