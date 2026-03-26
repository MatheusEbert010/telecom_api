"""Ponto de entrada da API e configuracao global da aplicacao."""

from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .config import settings
from .logging_config import setup_logging
from .request_context import get_request_id, reset_request_id, set_request_id
from .routers import admin, auth, plans, users
from .time_utils import utc_now

logger = setup_logging()
api_v1_router = APIRouter(prefix="/api/v1")


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


@api_v1_router.get("/health", tags=["Observabilidade"])
@app.get("/health", tags=["Observabilidade"], deprecated=True)
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


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Gera e propaga um identificador de requisicao para logs e clientes HTTP."""

    async def dispatch(self, request: Request, call_next):
        """Mantem o mesmo `request_id` ao longo de toda a requisicao."""
        request_id = request.headers.get("X-Request-ID") or uuid4().hex
        token = set_request_id(request_id)
        request.state.request_id = request_id

        try:
            response = await call_next(request)
        finally:
            reset_request_id(token)

        response.headers["X-Request-ID"] = request_id
        return response


app.add_middleware(RequestContextMiddleware)
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


def build_error_payload(
    status_code: int,
    detail: str,
    errors: list[dict] | None = None,
    request_id: str | None = None,
) -> dict:
    """Monta um payload de erro consistente para clientes HTTP."""
    payload = {
        "code": ERROR_CODES.get(status_code, "erro_http"),
        "detail": detail,
    }

    if errors:
        payload["errors"] = errors
    if request_id:
        payload["request_id"] = request_id

    return payload


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Padroniza erros HTTP esperados mantendo o status e os headers originais."""
    return JSONResponse(
        status_code=exc.status_code,
        content=build_error_payload(
            exc.status_code,
            str(exc.detail),
            request_id=getattr(request.state, "request_id", get_request_id()),
        ),
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Traduz erros de validacao para um contrato estavel para o frontend."""
    return JSONResponse(
        status_code=422,
        content=build_error_payload(
            422,
            "Dados de entrada invalidos",
            errors=exc.errors(),
            request_id=getattr(request.state, "request_id", get_request_id()),
        ),
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Padroniza erros inesperados sem expor detalhes sensiveis ao cliente."""
    logger.exception("Erro nao tratado ao processar %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content=build_error_payload(
            500,
            "Erro interno do servidor",
            request_id=getattr(request.state, "request_id", get_request_id()),
        ),
    )


def include_domain_routers(target, *, deprecated: bool = False) -> None:
    """Registra os routers da aplicacao com politica opcional de obsolescencia."""
    target.include_router(admin.router, deprecated=deprecated)
    target.include_router(auth.router, deprecated=deprecated)
    target.include_router(users.router, deprecated=deprecated)
    target.include_router(plans.router, deprecated=deprecated)


include_domain_routers(api_v1_router)
app.include_router(api_v1_router)
include_domain_routers(app, deprecated=True)
