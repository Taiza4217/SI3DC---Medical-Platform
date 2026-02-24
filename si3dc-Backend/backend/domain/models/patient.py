"""SI3DC — Modelo de Domínio: Paciente.

Entidade central representando um paciente no sistema SI3DC.
Inclui dados demográficos, contato, e identificadores clínicos.

DECISÕES DE ARQUITETURA:
- CPF é validado com dígitos verificadores (módulo 11) no schema Pydantic.
- Relationships usam lazy="select" por padrão para evitar N+1 queries.
  Usar selectinload() explicitamente nas queries que precisam de eager loading.
- UUID é armazenado como String(36) (vide AuditMixin).
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import Boolean, Date, DateTime, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.domain.models.base import AuditMixin, Base


# ── Modelo ORM (SQLAlchemy) ──────────────────────────────────────────


class PatientORM(AuditMixin, Base):
    """Tabela 'patients' — Dados do paciente com índices para busca rápida."""

    __tablename__ = "patients"
    __table_args__ = (
        Index("ix_patients_cpf", "cpf", unique=True),
        Index("ix_patients_name", "full_name"),
        Index("ix_patients_birth", "birth_date"),
    )

    # ── Dados pessoais ───────────────────────────────────────────────
    cpf: Mapped[str] = mapped_column(String(14), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    social_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[str] = mapped_column(String(20), nullable=False)
    blood_type: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    rh_factor: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)

    # ── Identificadores clínicos ─────────────────────────────────────
    cns: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # Cartão Nacional de Saúde

    # ── Contato ──────────────────────────────────────────────────────
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    zip_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # ── Contato de emergência ────────────────────────────────────────
    emergency_contact_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    emergency_contact_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # ── Status ───────────────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    deceased_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # ── Relacionamentos ──────────────────────────────────────────────
    # NOTA: lazy="select" evita N+1 queries automáticas.
    # Usar selectinload() explicitamente quando precisar do eager loading.
    medical_records = relationship("MedicalRecordORM", back_populates="patient", lazy="select")
    allergies = relationship("AllergyORM", back_populates="patient", lazy="select")
    prescriptions = relationship("PrescriptionORM", back_populates="patient", lazy="select")
    exams = relationship("ExamORM", back_populates="patient", lazy="select")
    medication_history = relationship("MedicationHistoryORM", back_populates="patient", lazy="select")
    ai_summaries = relationship("AIClinicalSummaryORM", back_populates="patient", lazy="select")
    consent_records = relationship("ConsentRecordORM", back_populates="patient", lazy="select")


# ── Schemas Pydantic (validação de entrada/saída) ────────────────────


class Gender(str, Enum):
    """Gênero do paciente — compatível com padrões do SUS."""
    MALE = "masculino"
    FEMALE = "feminino"
    OTHER = "outro"
    NOT_INFORMED = "nao_informado"


class BloodType(str, Enum):
    """Tipos sanguíneos com fator Rh."""
    A_POS = "A+"
    A_NEG = "A-"
    B_POS = "B+"
    B_NEG = "B-"
    AB_POS = "AB+"
    AB_NEG = "AB-"
    O_POS = "O+"
    O_NEG = "O-"


class PatientCreate(BaseModel):
    """Schema de criação de paciente com validação completa de CPF."""

    cpf: str = Field(..., min_length=11, max_length=14, description="CPF do paciente (com ou sem máscara)")
    full_name: str = Field(..., min_length=3, max_length=255)
    social_name: Optional[str] = None
    birth_date: date
    gender: Gender
    blood_type: Optional[BloodType] = None
    cns: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = Field(None, max_length=2)
    zip_code: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

    @field_validator("cpf")
    @classmethod
    def validate_cpf(cls, v: str) -> str:
        """Validação completa de CPF com dígitos verificadores (módulo 11).

        Rejeita:
        - CPFs com menos/mais de 11 dígitos
        - CPFs com todos os dígitos iguais (111.111.111-11, etc.)
        - CPFs com dígito verificador inválido
        """
        # Extrair apenas os dígitos numéricos
        digits = "".join(c for c in v if c.isdigit())

        if len(digits) != 11:
            raise ValueError("CPF deve conter 11 dígitos")

        # Rejeitar CPFs com todos os dígitos iguais (ex: 111.111.111-11)
        if digits == digits[0] * 11:
            raise ValueError("CPF inválido")

        # Cálculo do primeiro dígito verificador (módulo 11)
        soma = sum(int(digits[i]) * (10 - i) for i in range(9))
        d1 = 11 - (soma % 11)
        d1 = 0 if d1 >= 10 else d1
        if int(digits[9]) != d1:
            raise ValueError("CPF inválido (dígito verificador)")

        # Cálculo do segundo dígito verificador (módulo 11)
        soma = sum(int(digits[i]) * (11 - i) for i in range(10))
        d2 = 11 - (soma % 11)
        d2 = 0 if d2 >= 10 else d2
        if int(digits[10]) != d2:
            raise ValueError("CPF inválido (dígito verificador)")

        return v


class PatientResponse(BaseModel):
    """Schema de resposta — dados visíveis na API."""

    id: str
    cpf: str
    full_name: str
    social_name: Optional[str] = None
    birth_date: date
    gender: str
    blood_type: Optional[str] = None
    cns: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PatientSummary(BaseModel):
    """Referência leve do paciente para listagens e buscas."""

    id: str
    full_name: str
    cpf: str
    birth_date: date
    gender: str

    model_config = {"from_attributes": True}
