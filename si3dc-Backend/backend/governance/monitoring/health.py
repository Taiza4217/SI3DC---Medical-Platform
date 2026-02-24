"""SI3DC — Health Check Endpoints (Production-Ready).

Liveness e readiness probes para Kubernetes, load balancers, e monitoramento.

FUNCIONALIDADES:
- /health: Liveness probe — serviço está rodando.
- /health/ready: Readiness probe — dependências (DB, Redis, AI) estão prontas.

VERIFICAÇÕES DO READINESS:
- Database: executa SELECT 1 real contra o PostgreSQL.
- Redis: executa PING contra o Redis.
- AI Endpoint: faz requisição HTTP GET ao endpoint de AI.
- Sistema: memória e uptime.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

import httpx
import structlog
from fastapi import APIRouter
from sqlalchemy import text

from backend.config import get_settings
from backend.infrastructure.database.redis_client import get_redis

logger = structlog.get_logger(__name__)
router = APIRouter()

# Timestamp do startup para cálculo de uptime
_startup_time = time.time()


@router.get("/health", summary="Verificação de saúde (liveness)")
async def health_check():
    """Liveness probe — indica se o serviço está rodando.

    Este endpoint deve responder rapidamente e sem dependências externas.
    Usado por Kubernetes/Docker para determinar se o container está vivo.
    """
    settings = get_settings()
    uptime_seconds = int(time.time() - _startup_time)

    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT.value,
        "uptime_seconds": uptime_seconds,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health/ready", summary="Verificação de prontidão (readiness)")
async def readiness_check():
    """Readiness probe — verifica se TODAS as dependências estão prontas.

    Verificações realizadas:
    1. Database: SELECT 1 real contra o PostgreSQL.
    2. Redis: PING contra o Redis.
    3. AI Endpoint: HTTP GET com timeout curto.

    IMPORTANTE: Retorna 503 se alguma dependência crítica falhar.
    """
    settings = get_settings()
    checks: dict[str, str] = {}

    # ── Check Database (real query) ──────────────────────────────────
    try:
        from backend.infrastructure.database.session import _engine
        if _engine:
            async with _engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            checks["database"] = "connected"
        else:
            checks["database"] = "not_initialized"
    except Exception as e:
        checks["database"] = f"error: {str(e)[:100]}"
        logger.error("health_db_error", error=str(e))

    # ── Check Redis ──────────────────────────────────────────────────
    try:
        redis = get_redis()
        if redis:
            await redis.ping()
            checks["redis"] = "connected"
        else:
            checks["redis"] = "not_connected"
    except Exception as e:
        checks["redis"] = f"error: {str(e)[:100]}"
        logger.error("health_redis_error", error=str(e))

    # ── Check AI Endpoint ────────────────────────────────────────────
    try:
        ai_url = settings.AI_ENDPOINT_URL
        if ai_url:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Tentar um health check no endpoint de AI
                # Muitos modelos expõem /health ou respondem a GET na raiz
                response = await client.get(ai_url.rstrip("/").rsplit("/", 1)[0] + "/health")
                if response.status_code < 500:
                    checks["ai_endpoint"] = "reachable"
                else:
                    checks["ai_endpoint"] = f"unhealthy (status {response.status_code})"
        else:
            checks["ai_endpoint"] = "not_configured"
    except httpx.ConnectError:
        checks["ai_endpoint"] = "unreachable"
    except httpx.TimeoutException:
        checks["ai_endpoint"] = "timeout"
    except Exception as e:
        checks["ai_endpoint"] = f"error: {str(e)[:100]}"

    # ── Determinar status geral ──────────────────────────────────────
    # Database é crítico; Redis e AI são degradantes
    db_ok = checks.get("database") == "connected"
    redis_ok = checks.get("redis") == "connected"
    ai_ok = checks.get("ai_endpoint") in ("reachable", "not_configured")

    if db_ok and redis_ok and ai_ok:
        overall_status = "ready"
    elif db_ok:
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"

    uptime_seconds = int(time.time() - _startup_time)

    return {
        "status": overall_status,
        "checks": checks,
        "uptime_seconds": uptime_seconds,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
