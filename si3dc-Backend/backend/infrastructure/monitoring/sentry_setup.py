"""SI3DC — Integração com Sentry para Monitoramento de Erros em Produção.

Inicializa o Sentry SDK com filtros de dados sensíveis,
contexto de usuário, e suporte a performance monitoring.

SEGURANÇA:
- before_send filtra dados sensíveis (senhas, tokens, chaves).
- Sentry é inicializado APENAS se SENTRY_DSN estiver configurado.
- Em desenvolvimento, Sentry é opcional e silencioso.
"""

from __future__ import annotations

import structlog

logger = structlog.get_logger(__name__)

# Campos que NUNCA devem ser enviados ao Sentry
_SENSITIVE_KEYS = {
    "password", "password_hash", "token", "access_token", "refresh_token",
    "jwt_secret_key", "encryption_key", "secret", "authorization",
    "cookie", "set-cookie", "x-api-key", "api_key", "sentry_dsn",
}


def _scrub_sensitive_data(data: dict) -> dict:
    """Remove dados sensíveis de um dicionário recursivamente.

    SEGURANÇA: Previne que senhas, tokens, e chaves criptográficas
    sejam enviados ao Sentry inadvertidamente.
    """
    if not isinstance(data, dict):
        return data

    scrubbed = {}
    for key, value in data.items():
        if key.lower() in _SENSITIVE_KEYS:
            scrubbed[key] = "[FILTERED]"
        elif isinstance(value, dict):
            scrubbed[key] = _scrub_sensitive_data(value)
        elif isinstance(value, list):
            scrubbed[key] = [
                _scrub_sensitive_data(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            scrubbed[key] = value

    return scrubbed


def _before_send(event: dict, hint: dict) -> dict | None:
    """Callback executado antes de enviar cada evento ao Sentry.

    Filtra dados sensíveis dos headers, body, e extra data.
    """
    # Filtrar headers da requisição
    if "request" in event:
        request_data = event["request"]
        if "headers" in request_data:
            request_data["headers"] = _scrub_sensitive_data(
                dict(request_data["headers"]) if isinstance(request_data["headers"], dict)
                else {h[0]: h[1] for h in request_data.get("headers", []) if isinstance(h, (list, tuple))}
            )
        if "data" in request_data and isinstance(request_data["data"], dict):
            request_data["data"] = _scrub_sensitive_data(request_data["data"])

    # Filtrar extra data
    if "extra" in event:
        event["extra"] = _scrub_sensitive_data(event["extra"])

    return event


def init_sentry() -> None:
    """Inicializa o Sentry SDK para monitoramento de erros.

    REQUISITOS:
    - SENTRY_DSN deve estar configurado como variável de ambiente.
    - Se vazio ou ausente, Sentry NÃO é inicializado (sem erro).

    FUNCIONALIDADES:
    - Captura automática de exceções não tratadas.
    - Performance monitoring com traces_sample_rate configurável.
    - Integração nativa com FastAPI e SQLAlchemy.
    - Filtro de dados sensíveis via before_send.
    """
    from backend.config import get_settings

    settings = get_settings()

    if not settings.SENTRY_DSN:
        logger.info("sentry_skipped", reason="SENTRY_DSN não configurado")
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration

        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENVIRONMENT.value,
            release=f"si3dc@{settings.APP_VERSION}",
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            before_send=_before_send,
            send_default_pii=False,  # NÃO enviar dados PII automaticamente
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration(),
                LoggingIntegration(
                    level=None,       # Não capturar breadcrumbs de logs
                    event_level="ERROR",  # Capturar eventos para logs ERROR+
                ),
            ],
        )

        logger.info(
            "sentry_initialized",
            environment=settings.ENVIRONMENT.value,
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        )

    except ImportError:
        logger.warning("sentry_import_error", detail="sentry-sdk não instalado")
    except Exception as e:
        logger.error("sentry_init_error", error=str(e))


def set_sentry_user_context(user_id: str, role: str, institution_id: str) -> None:
    """Define o contexto de usuário no Sentry para rastreabilidade.

    Chamado após autenticação bem-sucedida para associar erros ao usuário.
    """
    try:
        import sentry_sdk
        sentry_sdk.set_user({
            "id": user_id,
            "role": role,
            "institution_id": institution_id,
        })
    except ImportError:
        pass
    except Exception:
        pass
