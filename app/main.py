"""Ponto de entrada da API e configuracao global da aplicacao."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .config import settings
from .logging_config import setup_logging
from .routers import auth, plans, users
from .time_utils import utc_now

logger = setup_logging()


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Registra eventos de ciclo de vida para facilitar observabilidade operacional."""
    logger.info(
        "Aplicacao iniciando. environment=%s docs_enabled=%s",
        settings.environment,
        settings.docs_enabled,
    )
    yield
    logger.info("Aplicacao finalizando")


app = FastAPI(
    title=settings.app_name,
    description="API para gerenciamento de usuarios e planos de telecomunicacoes",
    version=settings.app_version,
    docs_url="/docs" if settings.docs_enabled else None,
    redoc_url="/redoc" if settings.docs_enabled else None,
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """Retorna o estado basico da API para monitoramento externo."""
    return {
        "status": "healthy",
        "timestamp": utc_now().isoformat(),
        "service": "telecom-api",
        "version": settings.app_version,
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
    allow_origins=settings.effective_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Padroniza erros inesperados sem expor detalhes sensiveis ao cliente."""
    logger.exception("Erro nao tratado ao processar %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Erro interno do servidor"},
    )


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(plans.router)
