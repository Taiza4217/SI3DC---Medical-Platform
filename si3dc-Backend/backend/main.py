"""SI3DC — Main FastAPI Application (Production-Ready).

Application factory with CORS, exception handlers, OpenAPI metadata,
router registration, lifecycle events, and production middleware.

MIDDLEWARE ORDER (de cima para baixo na stack):
1. HTTPSRedirectMiddleware — Redireciona HTTP → HTTPS (produção)
2. CORSMiddleware — Headers CORS
3. RateLimitMiddleware — Limita requisições por usuário/IP
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from backend.config import Environment, get_settings

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup and shutdown lifecycle events."""
    settings = get_settings()
    logger.info("si3dc_starting", environment=settings.ENVIRONMENT.value, version=settings.APP_VERSION)

    # Inicializar Sentry ANTES de qualquer outra coisa (para capturar erros de startup)
    from backend.infrastructure.monitoring.sentry_setup import init_sentry
    init_sentry()

    # Import here to avoid circular imports
    from backend.infrastructure.database.session import init_db, close_db
    from backend.infrastructure.database.redis_client import init_redis, close_redis

    await init_db()
    await init_redis()

    logger.info("si3dc_ready")
    yield

    await close_redis()
    await close_db()
    logger.info("si3dc_shutdown")


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()

    app = FastAPI(
        title="SI3DC — Sistema Inteligente de Integração, Interpretação e Apoio à Decisão Clínica",
        description=(
            "Plataforma clínica baseada em nuvem com IA médica multimodal. "
            "Camada inteligente sobre prontuários eletrônicos para hospitais, "
            "convênios e redes públicas de saúde."
        ),
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )

    # ── HTTPS Enforcement (produção/staging) ─────────────────────────
    # NOTA: O middleware é adicionado PRIMEIRO para garantir que todas
    # as requisições HTTP sejam redirecionadas antes de qualquer processamento.
    if settings.ENVIRONMENT in (Environment.PRODUCTION, Environment.STAGING):
        from backend.infrastructure.security.https_middleware import HTTPSRedirectMiddleware
        app.add_middleware(HTTPSRedirectMiddleware)
        logger.info("https_enforcement_enabled")

    # ── CORS ─────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Rate Limiting ────────────────────────────────────────────────
    from backend.infrastructure.security.rate_limiter import RateLimitMiddleware
    app.add_middleware(RateLimitMiddleware)

    # ── Exception handlers ───────────────────────────────────────────
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> ORJSONResponse:
        import traceback
        traceback.print_exc()
        logger.error("unhandled_exception", path=request.url.path, error=str(exc))

        # Capturar exceção no Sentry com contexto
        try:
            import sentry_sdk
            sentry_sdk.capture_exception(exc)
        except ImportError:
            pass

        return ORJSONResponse(
            status_code=500,
            content={"detail": "Erro interno do servidor. Contate o administrador."},
        )

    # ── Register routers ─────────────────────────────────────────────
    from backend.api.routes.auth import router as auth_router
    from backend.api.routes.patients import router as patients_router
    from backend.api.routes.clinical import router as clinical_router
    from backend.api.routes.emergency import router as emergency_router
    from backend.api.routes.ai import router as ai_router
    from backend.governance.monitoring.health import router as health_router

    app.include_router(health_router, tags=["Health"])
    app.include_router(auth_router, prefix="/auth", tags=["Autenticação"])
    app.include_router(patients_router, prefix="/patients", tags=["Pacientes"])
    app.include_router(clinical_router, prefix="/clinical", tags=["Prontuário Clínico"])
    app.include_router(emergency_router, prefix="/emergency", tags=["Emergência"])
    app.include_router(ai_router, prefix="/ai", tags=["Inteligência Artificial"])

    return app


app = create_app()
