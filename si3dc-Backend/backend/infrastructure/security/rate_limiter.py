"""SI3DC — Middleware de Rate Limiting (Production-Ready).

Limitador de taxa usando Redis (ou fallback em memória).
Protege contra abuso de API e ataques de força bruta.

DECISÕES DE ARQUITETURA:
- Redis é o backend primário (compartilhado entre instâncias).
- Fallback em memória para quando o Redis estiver indisponível.
- O store em memória limpa chaves expiradas periodicamente (SEC-6 fix).
- Health checks são excluídos do rate limiting.
- RATE LIMIT POR TOKEN: Requisições autenticadas usam user_id como chave.
- FALLBACK POR IP: Requisições não autenticadas usam IP do cliente.
- PROXY SUPPORT: Detecta IP real via X-Forwarded-For / X-Real-IP.
"""

from __future__ import annotations

import ipaddress
import time
from collections import defaultdict
from typing import Optional

import structlog
from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from backend.config import get_settings
from backend.infrastructure.database.redis_client import get_redis

logger = structlog.get_logger(__name__)

# Fallback em memória quando Redis está indisponível
_memory_store: dict[str, list[float]] = defaultdict(list)

# Controle periódico de limpeza do store em memória (SEC-6 fix)
_last_cleanup: float = 0.0
_CLEANUP_INTERVAL: float = 60.0  # Limpar a cada 60 segundos


def _cleanup_memory_store(window: int) -> None:
    """Remove chaves expiradas do store em memória.

    SEC-6 fix: previne memory leak removendo periodicamente
    as entradas cujos timestamps são mais antigos que a janela de rate limit.
    """
    global _last_cleanup
    now = time.time()

    if now - _last_cleanup < _CLEANUP_INTERVAL:
        return

    _last_cleanup = now
    expired_keys = []

    for key, timestamps in _memory_store.items():
        valid = [t for t in timestamps if now - t < window]
        if not valid:
            expired_keys.append(key)
        else:
            _memory_store[key] = valid

    for key in expired_keys:
        del _memory_store[key]

    if expired_keys:
        logger.debug("rate_limit_memory_cleanup", removed_keys=len(expired_keys))


def _get_real_client_ip(request: Request) -> str:
    """Extrai o IP real do cliente considerando proxies reversos.

    Ordem de precedência:
    1. X-Real-IP (definido pelo Nginx/proxy)
    2. X-Forwarded-For (primeiro IP da cadeia, se proxy confiável)
    3. request.client.host (conexão direta)

    SEGURANÇA:
    - Valida que o IP do proxy está na lista de CIDRs confiáveis
      antes de confiar nos headers X-Forwarded-For / X-Real-IP.
    - Previne spoofing de IP por clientes maliciosos.
    """
    settings = get_settings()
    client_ip = request.client.host if request.client else "unknown"

    # Se não há proxies confiáveis configurados, usar IP direto
    if not settings.TRUSTED_PROXY_CIDRS:
        return client_ip

    # Verificar se o IP de conexão está em um CIDR de proxy confiável
    is_trusted_proxy = False
    try:
        client_addr = ipaddress.ip_address(client_ip)
        for cidr in settings.TRUSTED_PROXY_CIDRS:
            if client_addr in ipaddress.ip_network(cidr, strict=False):
                is_trusted_proxy = True
                break
    except ValueError:
        return client_ip

    if not is_trusted_proxy:
        return client_ip

    # Proxy confiável — extrair IP real do header
    # X-Real-IP tem precedência (definido pelo proxy mais próximo)
    x_real_ip = request.headers.get("X-Real-IP")
    if x_real_ip:
        return x_real_ip.strip()

    # X-Forwarded-For: lista de IPs separados por vírgula
    # O primeiro IP é o cliente original (mais confiável)
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        # Pegar o primeiro IP (cliente original)
        first_ip = x_forwarded_for.split(",")[0].strip()
        return first_ip

    return client_ip


def _extract_user_id_from_request(request: Request) -> Optional[str]:
    """Tenta extrair o user_id do token JWT no header Authorization.

    Usado para rate limiting por usuário autenticado.
    Se o token for inválido ou ausente, retorna None (fallback para IP).

    NOTA: Apenas decodifica o token para extrair o 'sub' claim.
    NÃO valida o token completamente (isso é feito pela dependência).
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split(" ", 1)[1]
    try:
        from backend.infrastructure.auth.jwt_handler import decode_token
        payload = decode_token(token)
        if payload and payload.get("type") == "access":
            return payload.get("sub")
    except Exception:
        pass
    return None


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware que limita requisições por usuário (JWT) ou IP do cliente.

    Para requisições autenticadas: usa user_id como chave de rate limit.
    Para requisições não autenticadas: usa IP do cliente (com suporte a proxy).

    Usa Redis para ambientes distribuídos (múltiplas instâncias).
    Se Redis estiver indisponível, usa fallback em memória local.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Excluir health checks e docs do rate limiting
        if request.url.path in ("/health", "/health/ready", "/docs", "/redoc", "/openapi.json"):
            return await call_next(request)

        settings = get_settings()

        # Identificar o cliente: preferir user_id (JWT), fallback para IP
        user_id = _extract_user_id_from_request(request)
        client_ip = _get_real_client_ip(request)

        if user_id:
            # Rate limit por usuário autenticado
            key = f"rl:user:{user_id}"
        else:
            # Rate limit por IP (requisições sem autenticação)
            key = f"rl:ip:{client_ip}"

        redis = get_redis()
        if redis:
            # Rate limiting via Redis (ambiente distribuído)
            try:
                current = await redis.incr(key)
                if current == 1:
                    await redis.expire(key, settings.RATE_LIMIT_WINDOW_SECONDS)
                if current > settings.RATE_LIMIT_REQUESTS:
                    logger.warning(
                        "rate_limit_exceeded",
                        key=key,
                        ip=client_ip,
                        user_id=user_id,
                        count=current,
                    )
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Limite de requisições excedido. Tente novamente em breve.",
                    )
            except HTTPException:
                raise
            except Exception as e:
                logger.warning("rate_limit_redis_error", error=str(e))
        else:
            # Fallback em memória local (instância única)
            now = time.time()
            window = settings.RATE_LIMIT_WINDOW_SECONDS

            # Limpeza periódica para evitar memory leak (SEC-6 fix)
            _cleanup_memory_store(window)

            # Filtrar timestamps válidos dentro da janela
            _memory_store[key] = [t for t in _memory_store[key] if now - t < window]

            if len(_memory_store[key]) >= settings.RATE_LIMIT_REQUESTS:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Limite de requisições excedido. Tente novamente em breve.",
                )
            _memory_store[key].append(now)

        response = await call_next(request)

        # Adicionar headers de rate limit na resposta para visibilidade do cliente
        remaining = max(0, settings.RATE_LIMIT_REQUESTS - len(_memory_store.get(key, [])))
        response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_REQUESTS)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Window"] = str(settings.RATE_LIMIT_WINDOW_SECONDS)

        return response
