from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime

from .routers import users, plans, auth
from .config import settings
from .logging_config import setup_logging

# Configurar logging seguro
logger = setup_logging()

# Criação da instância do FastAPI
app = FastAPI(
    title="Telecom API",
    description="API para gerenciamento de usuários e planos de telecomunicações",
    version="1.0.0",
    docs_url=None if settings.environment == "production" else "/docs",  # Desabilitar docs em produção
    redoc_url=None if settings.environment == "production" else "/redoc"
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Endpoint de health check para monitoramento"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "telecom-api",
        "version": "1.0.0"
    }

# Middleware para headers de segurança
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        
        # Headers de segurança para produção
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response

# Adicionar middleware de segurança
app.add_middleware(SecurityHeadersMiddleware)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],  # Adicionar origens permitidas
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Exception handler para produção (sem expor stack traces)
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    # Em produção, não expor detalhes do erro
    if settings.environment == "development":
        import traceback
        traceback.print_exc()
    
    return JSONResponse(
        status_code=500,
        content={"detail": "Erro interno do servidor"}
    )

# Inclusão das rotas
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(plans.router)
