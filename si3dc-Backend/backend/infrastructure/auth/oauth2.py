"""SI3DC — OAuth2 Scheme e Dependência de Usuário Atual.

Extrai e valida o profissional de saúde autenticado a partir do token JWT.

DECISÃO DE ARQUITETURA:
- O log de acesso a dados de pacientes é feito individualmente em cada rota
  usando log_patient_access(), NÃO nesta dependência global.
- Esta dependência apenas valida o token e retorna o usuário.
"""

from __future__ import annotations

from typing import Optional

import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.models.professional import HealthProfessionalORM
from backend.domain.models.institution import InstitutionORM  # noqa: F401 — needed for relationship()
from backend.infrastructure.auth.jwt_handler import decode_token
from backend.infrastructure.database.session import get_db

logger = structlog.get_logger(__name__)

# HTTPBearer — Swagger mostra campo simples para colar o token
_bearer_scheme = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> HealthProfessionalORM:
    """Extrai e valida o usuário atual a partir do token JWT.

    Validações realizadas:
    1. Token é decodificável e não expirado
    2. Token é do tipo 'access' (não refresh)
    3. Usuário existe no banco de dados
    4. Usuário está ativo (is_active=True)

    Raises:
        HTTPException 401: Se qualquer validação falhar.
    """
    # Exceção padrão para credenciais inválidas
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas ou token expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Decodificar e validar o JWT
    token = credentials.credentials
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    user_id: Optional[str] = payload.get("sub")
    token_type: Optional[str] = payload.get("type")

    # Garantir que é um access token (não refresh)
    if user_id is None or token_type != "access":
        raise credentials_exception

    # Buscar o profissional no banco
    result = await db.execute(
        select(HealthProfessionalORM).where(HealthProfessionalORM.id == user_id)
    )
    user = result.scalar_one_or_none()

    # Verificar existência e status ativo
    if user is None or not user.is_active:
        raise credentials_exception

    # NOTA: Log de acesso a dados de pacientes é feito nas rotas específicas
    # usando log_patient_access() — NÃO aqui para evitar FK violation
    # (AccessLogORM.patient_id é FK para patients.id).

    return user
