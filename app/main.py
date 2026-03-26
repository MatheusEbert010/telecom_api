"""Ponto de entrada da API e configuracao global da aplicacao."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .config import settings
from .logging_config import setup_logging
from .routers import admin, auth, plans, users
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


ERROR_CODES = {
    400: "requisicao_invalida",
    401: "nao_autorizado",
    403: "acesso_negado",
    404: "recurso_nao_encontrado",
    409: "conflito",
    422: "erro_validacao",
    500: "erro_interno",
}


def build_error_payload(status_code: int, detail: str, errors: list[dict] | None = None) -> dict:
    """Monta um payload de erro consistente para clientes HTTP."""
    payload = {
        "code": ERROR_CODES.get(status_code, "erro_http"),
        "detail": detail,
    }

    if errors:
        payload["errors"] = errors

    return payload


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    """Padroniza erros HTTP esperados mantendo o status e os headers originais."""
    return JSONResponse(
        status_code=exc.status_code,
        content=build_error_payload(exc.status_code, str(exc.detail)),
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    """Traduz erros de validacao para um contrato estavel para o frontend."""
    return JSONResponse(
        status_code=422,
        content=build_error_payload(
            422,
            "Dados de entrada invalidos",
            errors=exc.errors(),
        ),
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Padroniza erros inesperados sem expor detalhes sensiveis ao cliente."""
    logger.exception("Erro nao tratado ao processar %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content=build_error_payload(500, "Erro interno do servidor"),
    )


app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(plans.router)
