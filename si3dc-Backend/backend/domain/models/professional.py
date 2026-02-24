"""SI3DC — Domain Model: Health Professional (Profissional de Saúde).

Represents doctors, nurses, psychologists, and other health professionals.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field
from sqlalchemy import Boolean, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.domain.models.base import AuditMixin, Base


class HealthProfessionalORM(AuditMixin, Base):
    __tablename__ = "health_professionals"
    __table_args__ = (
        Index("ix_hp_registration", "registration_number", unique=True),
        Index("ix_hp_institution", "institution_id"),
    )

    registration_type: Mapped[str] = mapped_column(String(10), nullable=False)  # CRM, CRP, COREN...
    registration_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    registration_state: Mapped[str] = mapped_column(String(2), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    specialty: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="BASIC")
    institution_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("institutions.id"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    institution = relationship("InstitutionORM", back_populates="professionals")
    access_logs = relationship("AccessLogORM", back_populates="professional", lazy="selectin")


# ── Pydantic Schemas ─────────────────────────────────────────────────


class RegistrationType(str, Enum):
    CRM = "CRM"
    CRP = "CRP"
    COREN = "COREN"
    CRF = "CRF"
    ADMIN = "ADMIN"


class AccessRole(str, Enum):
    BASIC = "BASIC"       # Read-only clinical data
    MEDIUM = "MEDIUM"     # Read + write clinical data
    ADMIN = "ADMIN"       # Full access including system config


class ProfessionalCreate(BaseModel):
    registration_type: RegistrationType
    registration_number: str = Field(..., min_length=3, max_length=20)
    registration_state: str = Field(..., min_length=2, max_length=2)
    full_name: str = Field(..., min_length=3, max_length=255)
    specialty: Optional[str] = None
    email: str
    phone: Optional[str] = None
    password: str = Field(..., min_length=8)
    role: AccessRole = AccessRole.BASIC
    institution_id: str


class ProfessionalResponse(BaseModel):
    id: str
    registration_type: str
    registration_number: str
    registration_state: str
    full_name: str
    specialty: Optional[str] = None
    email: str
    role: str
    institution_id: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
