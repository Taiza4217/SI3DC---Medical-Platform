"""SI3DC — Rotas de Autenticação.

Endpoints de autenticação: login, refresh token, logout, perfil do profissional.

SEGURANÇA:
- Login usa timing-safe comparison para prevenir enumeração de usuários.
- Hash dummy é usado quando o usuário não existe para manter tempo constante.
- Tokens JWT incluem role e institution_id para RBAC.
- Refresh tokens são armazenados no banco com hash SHA-256.
- Logout revoga o refresh token (blacklist).
- Rotação de refresh token a cada refresh (previne reutilização).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.models.professional import HealthProfessionalORM, ProfessionalResponse
from backend.domain.models.institution import InstitutionORM  # noqa: F401 — needed for relationship()
from backend.infrastructure.auth.jwt_handler import (
    create_access_token,
    create_refresh_token,
    decode_token,
    is_token_revoked,
    revoke_all_user_tokens,
    revoke_refresh_token,
    store_refresh_token,
)
from backend.infrastructure.auth.oauth2 import get_current_user
from backend.infrastructure.database.session import get_db

logger = structlog.get_logger(__name__)
router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash dummy para timing-safe comparison quando o usuário não existe (SEC-4 fix)
# Gerado uma vez no startup para evitar overhead por requisição
_DUMMY_HASH = pwd_context.hash("__dummy_password_for_timing_safety__")


# ── Schemas de Requisição/Resposta ───────────────────────────────────


class LoginRequest(BaseModel):
    """Schema de login — identificação por registro profissional."""
    registration_type: str = Field(..., description="CRM, CRP, COREN, ou ADMIN")
    registration_number: str = Field(..., description="Número do registro profissional")
    password: str = Field(..., min_length=8)
    institution_id: Optional[str] = Field(None, description="ID da instituição (opcional)")


class TokenResponse(BaseModel):
    """Resposta com tokens JWT e dados do profissional."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: ProfessionalResponse


class RefreshRequest(BaseModel):
    """Schema para renovação de token."""
    refresh_token: str


class LogoutRequest(BaseModel):
    """Schema para logout — requer o refresh token para revogação."""
    refresh_token: str


class LogoutResponse(BaseModel):
    """Resposta de logout."""
    detail: str
    revoked: bool


# ── Endpoints ────────────────────────────────────────────────────────


@router.post("/login", response_model=TokenResponse, summary="Login de profissional de saúde")
async def login(
    request: Request,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Autenticar um profissional de saúde com CRM/CRP/ID administrativo.

    Retorna tokens JWT de acesso e refresh.

    SEGURANÇA:
    - Timing-safe: executa hash mesmo quando o usuário não existe,
      prevenindo enumeração de usuários por diferença de tempo.
    - Logs de tentativa falha são registrados com IP para auditoria.
    - Refresh token é armazenado no banco com hash SHA-256.
    """
    # Buscar o profissional pelo tipo e número de registro
    result = await db.execute(
        select(HealthProfessionalORM).where(
            HealthProfessionalORM.registration_type == body.registration_type.upper(),
            HealthProfessionalORM.registration_number == body.registration_number,
        )
    )
    user = result.scalar_one_or_none()

    # SEC-4 fix: Timing-safe — sempre executar verificação de hash
    if not user:
        pwd_context.verify(body.password, _DUMMY_HASH)
        logger.warning(
            "login_failed",
            reason="user_not_found",
            registration=body.registration_number,
            ip=request.client.host if request.client else None,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Registro ou senha inválidos",
        )

    if not pwd_context.verify(body.password, user.password_hash):
        logger.warning(
            "login_failed",
            reason="invalid_password",
            registration=body.registration_number,
            ip=request.client.host if request.client else None,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Registro ou senha inválidos",
        )

    # Verificar se a conta está ativa
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta desativada. Contate o administrador.",
        )

    # Validar instituição se fornecida
    if body.institution_id and user.institution_id != body.institution_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Profissional não vinculado a esta instituição.",
        )

    # Gerar tokens JWT com dados do profissional
    token_data = {
        "sub": user.id,
        "role": user.role,
        "institution_id": user.institution_id,
        "registration_type": user.registration_type,
    }

    access_token = create_access_token(token_data)
    refresh_token, jti, expires_at = create_refresh_token(token_data)

    # Armazenar refresh token no banco para controle de blacklist
    await store_refresh_token(db, user.id, jti, refresh_token, expires_at)

    logger.info(
        "login_success",
        user_id=user.id,
        role=user.role,
        ip=request.client.host if request.client else None,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=ProfessionalResponse.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse, summary="Renovar token de acesso")
async def refresh_token_endpoint(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """Renovar o token de acesso usando um refresh token válido.

    SEGURANÇA:
    - Verifica se o token foi revogado (blacklist).
    - Revoga o token antigo ao emitir um novo par (rotação de token).
    - Previne reutilização de tokens roubados: se o token já foi usado,
      revoga TODOS os tokens do usuário (family rotation).
    """
    payload = decode_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido ou expirado",
        )

    jti = payload.get("jti")
    user_id = payload.get("sub")

    if not jti or not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido (claims ausentes)",
        )

    # Verificar se o token foi revogado
    if await is_token_revoked(db, jti):
        # Token já foi usado ou revogado — possível roubo!
        # Revogar TODOS os tokens do usuário por segurança (family rotation)
        await revoke_all_user_tokens(db, user_id)
        logger.warning(
            "refresh_token_reuse_detected",
            user_id=user_id,
            jti=jti,
            action="all_tokens_revoked",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token reutilizado — todos os tokens foram revogados por segurança",
        )

    # Buscar o usuário no banco
    result = await db.execute(
        select(HealthProfessionalORM).where(HealthProfessionalORM.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado ou desativado",
        )

    # Revogar o token antigo (rotação de token)
    await revoke_refresh_token(db, jti)

    # Emitir novo par de tokens
    token_data = {
        "sub": user.id,
        "role": user.role,
        "institution_id": user.institution_id,
        "registration_type": user.registration_type,
    }

    new_access = create_access_token(token_data)
    new_refresh, new_jti, new_expires = create_refresh_token(token_data)

    # Armazenar novo refresh token
    await store_refresh_token(db, user.id, new_jti, new_refresh, new_expires)

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        user=ProfessionalResponse.model_validate(user),
    )


@router.post("/logout", response_model=LogoutResponse, summary="Logout seguro")
async def logout(
    body: LogoutRequest,
    db: AsyncSession = Depends(get_db),
    current_user: HealthProfessionalORM = Depends(get_current_user),
):
    """Revogar o refresh token atual (logout seguro).

    SEGURANÇA:
    - Requer autenticação (access token válido).
    - Revoga o refresh token fornecido no body.
    - Para logout de todos os dispositivos, use /logout-all.
    """
    payload = decode_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token inválido",
        )

    jti = payload.get("jti")
    if not jti:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token sem JTI",
        )

    revoked = await revoke_refresh_token(db, jti)

    logger.info("user_logout", user_id=current_user.id, jti=jti, revoked=revoked)

    return LogoutResponse(
        detail="Logout realizado com sucesso" if revoked else "Token já revogado ou inválido",
        revoked=revoked,
    )


@router.post("/logout-all", response_model=LogoutResponse, summary="Logout de todos os dispositivos")
async def logout_all(
    db: AsyncSession = Depends(get_db),
    current_user: HealthProfessionalORM = Depends(get_current_user),
):
    """Revogar TODOS os refresh tokens do usuário (logout global).

    Usado quando o usuário suspeita que sua conta foi comprometida.
    """
    count = await revoke_all_user_tokens(db, current_user.id)

    logger.info("user_logout_all", user_id=current_user.id, tokens_revoked=count)

    return LogoutResponse(
        detail=f"{count} token(s) revogado(s)",
        revoked=count > 0,
    )


@router.get("/me", response_model=ProfessionalResponse, summary="Perfil do usuário autenticado")
async def get_me(
    current_user: HealthProfessionalORM = Depends(get_current_user),
):
    """Retornar o perfil do profissional autenticado."""
    return ProfessionalResponse.model_validate(current_user)
