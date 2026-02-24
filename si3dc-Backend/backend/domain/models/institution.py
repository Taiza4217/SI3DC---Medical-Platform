"""SI3DC — Domain Model: Institution (Instituição de Saúde).

Hospitals, UBS, clinics, convênios.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field
from sqlalchemy import Boolean, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.domain.models.base import AuditMixin, Base


class InstitutionORM(AuditMixin, Base):
    __tablename__ = "institutions"
    __table_args__ = (
        Index("ix_institution_cnes", "cnes", unique=True),
    )

    cnes: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    cnpj: Mapped[Optional[str]] = mapped_column(String(18), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    professionals = relationship("HealthProfessionalORM", back_populates="institution")


class InstitutionType(str, Enum):
    HOSPITAL = "hospital"
    UBS = "ubs"
    CLINICA = "clinica"
    CONVENIO = "convenio"
    LABORATORIO = "laboratorio"
    UPA = "upa"


class InstitutionCreate(BaseModel):
    cnes: str = Field(..., min_length=3, max_length=20)
    name: str = Field(..., min_length=3, max_length=255)
    type: InstitutionType
    cnpj: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = Field(None, max_length=2)
    phone: Optional[str] = None
    email: Optional[str] = None


class InstitutionResponse(BaseModel):
    id: str
    cnes: str
    name: str
    type: str
    city: Optional[str] = None
    state: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
