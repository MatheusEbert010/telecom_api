"""Ponto de entrada da API e configuracao global da aplicacao."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .config import settings
from .logging_config import setup_logging
from .routers import auth, plans, users
from .time_utils import utc_now

logger = setup_logging()

app = FastAPI(
    title="Telecom API",
    description="API para gerenciamento de usuarios e planos de telecomunicacoes",
    version="1.0.0",
    docs_url=None if settings.environment == "production" else "/docs",
    redoc_url=None if settings.environment == "production" else "/redoc",
)


@app.get("/health")
async def health_check():
    """Retorna o estado basico da API para monitoramento externo."""
    return {
        "status": "healthy",
        "timestamp": utc_now().isoformat(),
        "service": "telecom-api",
        "version": "1.0.0",
    }


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adiciona cabecalhos HTTP que reforcam a seguranca do navegador."""

    async def dispatch(self, request, call_next):
        """Aplica cabecalhos defensivos a todas as respostas da API."""
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Em producao a politica e mais restritiva para reduzir a superficie de ataque.
        if settings.environment == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com; "
                "img-src 'self' data: https:; "
                "font-src 'self' https://fonts.googleapis.com https://fonts.gstatic.com"
            )

        return response


app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Padroniza erros inesperados sem expor detalhes sensiveis ao cliente."""
    if settings.environment == "development":
        import traceback

        traceback.print_exc()

    return JSONResponse(
        status_code=500,
        content={"detail": "Erro interno do servidor"},
    )


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(plans.router)
