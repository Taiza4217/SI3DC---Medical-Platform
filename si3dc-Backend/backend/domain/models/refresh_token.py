"""SI3DC — Domain Model: Refresh Token (Blacklist/Invalidação).

Tabela de refresh tokens para controle de revogação, expiração,
e prevenção de reutilização de tokens roubados.

SEGURANÇA:
- Armazena hash SHA-256 do token (nunca o token em texto).
- Cada login gera um novo registro; refresh gera um par rotacionado.
- Token revogado (revoked_at != None) é rejeitado imediatamente.
- Tokens expirados são limpos periodicamente via tarefa agendada.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.domain.models.base import AuditMixin, Base


class RefreshTokenORM(AuditMixin, Base):
    """Tabela 'refresh_tokens' — Controle de refresh tokens emitidos.

    Cada refresh token emitido pelo sistema é registrado aqui com seu hash.
    Na renovação (refresh), o token antigo é revogado e um novo é criado.
    No logout, o token é revogado explicitamente.

    Campos:
        jti: JWT ID único do token (UUID gerado na criação do JWT).
        user_id: FK para o profissional de saúde dono do token.
        token_hash: Hash SHA-256 do token JWT (para lookup sem armazenar o token).
        expires_at: Data de expiração do token.
        revoked_at: Data de revogação (None = token válido).
    """

    __tablename__ = "refresh_tokens"
    __table_args__ = (
        Index("ix_rt_jti", "jti", unique=True),
        Index("ix_rt_user", "user_id"),
        Index("ix_rt_token_hash", "token_hash"),
        Index("ix_rt_expires", "expires_at"),
    )

    jti: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, comment="JWT ID — identificador único do token"
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("health_professionals.id", ondelete="CASCADE"),
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="SHA-256 hash do token JWT"
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="Expiração do token"
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        comment="Null = ativo; preenchido = revogado",
    )

    @property
    def is_revoked(self) -> bool:
        """Verifica se o token foi revogado."""
        return self.revoked_at is not None

    @property
    def is_expired(self) -> bool:
        """Verifica se o token expirou."""
        from datetime import timezone
        return datetime.now(timezone.utc) > self.expires_at
