"""SI3DC — JWT Token Handler.

JWT access and refresh token creation, validation, and blacklist management.

SEGURANÇA:
- Refresh tokens incluem 'jti' (JWT ID) para rastreabilidade.
- Tokens revogados são verificados via banco de dados.
- Hash SHA-256 do token é armazenado (nunca o token em texto).
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import structlog
from jose import JWTError, jwt
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings

logger = structlog.get_logger(__name__)


def _hash_token(token: str) -> str:
    """Gera hash SHA-256 do token JWT para armazenamento seguro."""
    return hashlib.sha256(token.encode()).hexdigest()


def create_access_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token."""
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict[str, Any]) -> tuple[str, str, datetime]:
    """Cria um refresh token JWT com JTI para rastreabilidade.

    Retorna:
        tuple: (token_jwt, jti, expires_at)
    """
    settings = get_settings()
    to_encode = data.copy()
    jti = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_REFRESH_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expires_at, "type": "refresh", "jti": jti})
    token = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, jti, expires_at


def decode_token(token: str) -> Optional[dict[str, Any]]:
    """Decode and validate a JWT token. Returns None on failure."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        logger.warning("jwt_decode_error", error=str(e))
        return None


async def store_refresh_token(
    db: AsyncSession, user_id: str, jti: str, token: str, expires_at: datetime
) -> None:
    """Armazena um refresh token no banco para controle de revogação.

    SEGURANÇA: Armazena apenas o hash SHA-256 do token, nunca o token em texto.
    """
    from backend.domain.models.refresh_token import RefreshTokenORM

    rt = RefreshTokenORM(
        jti=jti,
        user_id=user_id,
        token_hash=_hash_token(token),
        expires_at=expires_at,
    )
    db.add(rt)
    # Não fazemos commit aqui — o commit é gerenciado pelo get_db() context
    logger.info("refresh_token_stored", user_id=user_id, jti=jti)


async def revoke_refresh_token(db: AsyncSession, jti: str) -> bool:
    """Revoga um refresh token pelo JTI, marcando revoked_at.

    Retorna True se o token foi encontrado e revogado.
    """
    from backend.domain.models.refresh_token import RefreshTokenORM

    result = await db.execute(
        update(RefreshTokenORM)
        .where(RefreshTokenORM.jti == jti, RefreshTokenORM.revoked_at.is_(None))
        .values(revoked_at=datetime.now(timezone.utc))
    )
    if result.rowcount > 0:  # type: ignore[union-attr]
        logger.info("refresh_token_revoked", jti=jti)
        return True
    return False


async def revoke_all_user_tokens(db: AsyncSession, user_id: str) -> int:
    """Revoga TODOS os refresh tokens de um usuário (logout total).

    Usado em casos de:
    - Logout de todos os dispositivos
    - Conta comprometida
    - Desativação de usuário

    Retorna o número de tokens revogados.
    """
    from backend.domain.models.refresh_token import RefreshTokenORM

    result = await db.execute(
        update(RefreshTokenORM)
        .where(
            RefreshTokenORM.user_id == user_id,
            RefreshTokenORM.revoked_at.is_(None),
        )
        .values(revoked_at=datetime.now(timezone.utc))
    )
    count = result.rowcount  # type: ignore[union-attr]
    if count > 0:
        logger.info("all_user_tokens_revoked", user_id=user_id, count=count)
    return count


async def is_token_revoked(db: AsyncSession, jti: str) -> bool:
    """Verifica se um refresh token foi revogado.

    Retorna True se o token NÃO existe ou se foi revogado.
    Um token que não existe no banco é considerado inválido por segurança.
    """
    from backend.domain.models.refresh_token import RefreshTokenORM

    result = await db.execute(
        select(RefreshTokenORM).where(RefreshTokenORM.jti == jti)
    )
    rt = result.scalar_one_or_none()

    # Token não encontrado no banco = considerado inválido
    if rt is None:
        logger.warning("refresh_token_not_found", jti=jti)
        return True

    return rt.is_revoked
