import os
import time
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from app.database import close_db_pool, init_db_pool
from app.routers import fares, routes, schedule, stops, vehicle
from app.security import verify_api_key

load_dotenv()

# ponto de entrada da api, monta routers e middleware
app = FastAPI(title="Metro Porto", description="1.0.0")

# 60/min por IP é suficiente para uma app normal
_rate_limit = os.getenv("RATE_LIMIT", "60/minute")
limiter = Limiter(key_func=get_remote_address, default_limits=[_rate_limit])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
# middleware que aplica o limite em todos os endpoints
app.add_middleware(SlowAPIMiddleware)

# abre pool postgres ao arrancar
@app.on_event("startup")
async def startup_event():
    await init_db_pool()
    
# fecha ligacoes ao desligar, evita lixo no neon
@app.on_event("shutdown")
async def shutdown_event():
    await close_db_pool()
    
# cors para o frontend chamar a api noutro dominio
origins_raw = os.getenv("ALLOWED_ORIGINS", "*")
origins = [o.strip() for o in origins_raw.split(",")] if origins_raw else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# valida X-API-Key quando API_KEY estiver no .env (exceto /health e /docs)
@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    auth_error = verify_api_key(request)
    if auth_error is not None:
        return auth_error
    return await call_next(request)


# log simples no terminal com tempo de cada pedido
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    print(f"{request.method} {request.url.path} -> {response.status_code} [{elapsed_ms:.2f}ms]")
    return response


# health check para deploy nao tem rate limit para o railway nao falhar probes
@app.get("/health", tags=["system"])
@limiter.exempt
async def health(request: Request):
    return {"status": "ok"}


# agrupa endpoints por tema, paragens linhas horarios etc
app.include_router(stops.router)
app.include_router(routes.router)
app.include_router(schedule.router)
app.include_router(vehicle.router)
app.include_router(fares.router)