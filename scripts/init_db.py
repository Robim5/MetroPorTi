import asyncio
import os
from pathlib import Path
import asyncpg
from dotenv import load_dotenv

load_dotenv()

# corre o sql inicial contra o neon, uso manual ou ci
async def main() -> None:
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError("Database URL nao esta defenida")
    
    schema_path = Path("sql/database_tables.sql")
    if not schema_path.exists():
        raise FileNotFoundError(f"Ficheiro nao encontrado: {schema_path}")
    
    sql = schema_path.read_text(encoding="utf-8")
    
    # ligacao directa, nao precisa de pool para script one shot
    conn = await asyncpg.connect(dsn=database_url)
    try:
        # cria tabelas, indices, se nao existe torna o script seguro em rerun
        await conn.execute(sql)
        print("Tabelas e indices criados com sucesso")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())