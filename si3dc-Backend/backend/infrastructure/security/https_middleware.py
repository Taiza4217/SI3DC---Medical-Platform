"""SI3DC — HTTPS Enforcement Middleware.

Redireciona HTTP → HTTPS em ambientes de produção/staging.
Confia no header X-Forwarded-Proto de proxies reversos.

DECISÕES DE ARQUITETURA:
- Em desenvolvimento, o middleware NÃO redireciona (permite HTTP local).
- Health checks são excluídos do redirecionamento.
- Adiciona header Strict-Transport-Security (HSTS) em todas as respostas HTTPS.
- O HSTS max-age é de 1 ano (31536000 segundos), incluindo subdomínios.
"""

from __future__ import annotations

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

logger = structlog.get_logger(__name__)

# HSTS max-age: 1 ano (recomendação OWASP para produção)
_HSTS_MAX_AGE = 31536000


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """Middleware para forçar HTTPS em produção.

    Comportamento:
    1. Verifica o protocolo via X-Forwarded-Proto (proxy) ou scheme da URL.
    2. Se HTTP em produção/staging → redireciona 301 para HTTPS.
    3. Adiciona HSTS header em respostas HTTPS.
    4. Health checks são isentos (para load balancers que usam HTTP).

    IMPORTANTE:
    - Configurar o proxy reverso (Nginx, CloudFlare, etc.) para enviar
      o header X-Forwarded-Proto corretamente.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Health checks não redirecionam (load balancers usam HTTP)
        if request.url.path in ("/health", "/health/ready"):
            return await call_next(request)

        # Determinar o protocolo real (considerando proxy reverso)
        # X-Forwarded-Proto é definido pelo proxy (Nginx, ALB, CloudFlare)
        forwarded_proto = request.headers.get("X-Forwarded-Proto", "").lower()
        is_https = forwarded_proto == "https" or request.url.scheme == "https"

        if not is_https:
            # Redirecionar HTTP → HTTPS (301 Permanent Redirect)
            https_url = str(request.url).replace("http://", "https://", 1)
            logger.info(
                "https_redirect",
                from_url=str(request.url),
                to_url=https_url,
            )
            return RedirectResponse(url=https_url, status_code=301)

        # Processar a requisição normalmente
        response = await call_next(request)

        # Adicionar HSTS header (Strict-Transport-Security)
        # Instrui o navegador a SEMPRE usar HTTPS para este domínio
        response.headers["Strict-Transport-Security"] = (
            f"max-age={_HSTS_MAX_AGE}; includeSubDomains; preload"
        )

        return response
