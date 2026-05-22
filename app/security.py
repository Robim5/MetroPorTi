import os
from fastapi import Request
from fastapi.responses import JSONResponse

# rotas públicas sem API key
PUBLIC_PATHS = {
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
}


def is_api_key_required() -> bool:
    """ só exige chave quando API_KEY está definida no ambiente """
    return bool(os.getenv("API_KEY", "").strip())


def verify_api_key(request: Request) -> JSONResponse | None:
    """ devolve resposta 401 se a chave for inválida; None se o pedido for aceite """
    expected = os.getenv("API_KEY", "").strip()
    if not expected:
        return None

    path = request.url.path
    if path in PUBLIC_PATHS or path.startswith("/testar"):
        return None

    # header (postman, apps) ou ?api_key= (testar no browser)
    provided = (
        request.headers.get("X-API-Key", "").strip()
        or request.query_params.get("api_key", "").strip()
    )
    if provided != expected:
        return JSONResponse(
            status_code=401,
            content={
                "detail": "API key inválida ou em falta. Usa o header X-API-Key ou ?api_key= no URL.",
            },
        )
    return None
