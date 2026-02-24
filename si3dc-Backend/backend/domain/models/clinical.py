"""SI3DC — Domain Models: Clinical Records.

Medical Record, Clinical Event, Medical Document, Exam,
Prescription, Allergy, Medication History, Access Log, AI Summary, Consent.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field
from sqlalchemy import (
    Boolean, Date, DateTime, Float, ForeignKey, Index, Integer, String, Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.domain.models.base import AuditMixin, Base


# ═══════════════════════════════════════════════════════════════════════
# MEDICAL RECORD (Prontuário)
# ═══════════════════════════════════════════════════════════════════════


class MedicalRecordORM(AuditMixin, Base):
    __tablename__ = "medical_records"
    __table_args__ = (
        Index("ix_mr_patient", "patient_id"),
        Index("ix_mr_institution", "institution_id"),
    )

    patient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("patients.id"), nullable=False
    )
    institution_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("institutions.id"), nullable=False
    )
    created_by: Mapped[str] = mapped_column(
        String(36), ForeignKey("health_professionals.id"), nullable=False
    )
    record_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    patient = relationship("PatientORM", back_populates="medical_records")
    clinical_events = relationship("ClinicalEventORM", back_populates="medical_record", lazy="selectin")
    documents = relationship("MedicalDocumentORM", back_populates="medical_record", lazy="selectin")


# ═══════════════════════════════════════════════════════════════════════
# CLINICAL EVENT (Evento Clínico)
# ═══════════════════════════════════════════════════════════════════════


class ClinicalEventORM(AuditMixin, Base):
    __tablename__ = "clinical_events"
    __table_args__ = (
        Index("ix_ce_record", "record_id"),
        Index("ix_ce_date", "event_date"),
        Index("ix_ce_type", "event_type"),
    )

    record_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("medical_records.id"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    event_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    icd_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    severity: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    professional_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("health_professionals.id"), nullable=False
    )

    medical_record = relationship("MedicalRecordORM", back_populates="clinical_events")


# ═══════════════════════════════════════════════════════════════════════
# MEDICAL DOCUMENT (Documento Médico)
# ═══════════════════════════════════════════════════════════════════════


class MedicalDocumentORM(AuditMixin, Base):
    __tablename__ = "medical_documents"
    __table_args__ = (
        Index("ix_md_record", "record_id"),
    )

    record_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("medical_records.id"), nullable=False
    )
    doc_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    storage_url: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    uploaded_by: Mapped[str] = mapped_column(
        String(36), ForeignKey("health_professionals.id"), nullable=False
    )

    medical_record = relationship("MedicalRecordORM", back_populates="documents")


# ═══════════════════════════════════════════════════════════════════════
# EXAM (Exame)
# ═══════════════════════════════════════════════════════════════════════


class ExamORM(AuditMixin, Base):
    __tablename__ = "exams"
    __table_args__ = (
        Index("ix_exam_patient", "patient_id"),
        Index("ix_exam_date", "exam_date"),
    )

    patient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("patients.id"), nullable=False
    )
    exam_type: Mapped[str] = mapped_column(String(100), nullable=False)
    exam_date: Mapped[date] = mapped_column(Date, nullable=False)
    result: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    result_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    result_unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    reference_range: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    lab_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    requesting_professional_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("health_professionals.id"), nullable=False
    )
    storage_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    patient = relationship("PatientORM", back_populates="exams")


# ═══════════════════════════════════════════════════════════════════════
# PRESCRIPTION (Prescrição)
# ═══════════════════════════════════════════════════════════════════════


class PrescriptionORM(AuditMixin, Base):
    __tablename__ = "prescriptions"
    __table_args__ = (
        Index("ix_rx_patient", "patient_id"),
        Index("ix_rx_date", "prescribed_at"),
    )

    patient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("patients.id"), nullable=False
    )
    professional_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("health_professionals.id"), nullable=False
    )
    medication: Mapped[str] = mapped_column(String(255), nullable=False)
    active_ingredient: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    dosage: Mapped[str] = mapped_column(String(100), nullable=False)
    frequency: Mapped[str] = mapped_column(String(100), nullable=False)
    route: Mapped[str] = mapped_column(String(50), nullable=False)  # oral, IV, IM...
    duration_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    prescribed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    patient = relationship("PatientORM", back_populates="prescriptions")


# ═══════════════════════════════════════════════════════════════════════
# ALLERGY (Alergia)
# ═══════════════════════════════════════════════════════════════════════


class AllergyORM(AuditMixin, Base):
    __tablename__ = "allergies"
    __table_args__ = (
        Index("ix_allergy_patient", "patient_id"),
    )

    patient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("patients.id"), nullable=False
    )
    allergen: Mapped[str] = mapped_column(String(255), nullable=False)
    allergen_type: Mapped[str] = mapped_column(String(50), nullable=False)  # drug, food, env...
    severity: Mapped[str] = mapped_column(String(20), nullable=False)  # mild, moderate, severe, critical
    reaction: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    confirmed_by: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("health_professionals.id"), nullable=True
    )
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    patient = relationship("PatientORM", back_populates="allergies")


# ═══════════════════════════════════════════════════════════════════════
# MEDICATION HISTORY (Histórico Medicamentoso)
# ═══════════════════════════════════════════════════════════════════════


class MedicationHistoryORM(AuditMixin, Base):
    __tablename__ = "medication_history"
    __table_args__ = (
        Index("ix_medhist_patient", "patient_id"),
    )

    patient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("patients.id"), nullable=False
    )
    medication: Mapped[str] = mapped_column(String(255), nullable=False)
    dosage: Mapped[str] = mapped_column(String(100), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    discontinued_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    adverse_effects: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    patient = relationship("PatientORM", back_populates="medication_history")


# ═══════════════════════════════════════════════════════════════════════
# ACCESS LOG (Log de Acesso ao Prontuário)
# ═══════════════════════════════════════════════════════════════════════


class AccessLogORM(AuditMixin, Base):
    __tablename__ = "access_logs"
    __table_args__ = (
        Index("ix_access_professional", "professional_id"),
        Index("ix_access_patient", "patient_id"),
        Index("ix_access_timestamp", "accessed_at"),
    )

    professional_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("health_professionals.id"), nullable=False
    )
    patient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("patients.id"), nullable=False
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    resource: Mapped[str] = mapped_column(String(100), nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    accessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    professional = relationship("HealthProfessionalORM", back_populates="access_logs")


# ═══════════════════════════════════════════════════════════════════════
# AI CLINICAL SUMMARY (Resumo Clínico gerado por IA)
# ═══════════════════════════════════════════════════════════════════════


class AIClinicalSummaryORM(AuditMixin, Base):
    __tablename__ = "ai_clinical_summaries"
    __table_args__ = (
        Index("ix_ais_patient", "patient_id"),
        Index("ix_ais_generated", "generated_at"),
    )

    patient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("patients.id"), nullable=False
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_label: Mapped[str] = mapped_column(String(20), nullable=False)
    model_name: Mapped[str] = mapped_column(String(50), nullable=False)
    model_version: Mapped[str] = mapped_column(String(20), nullable=False)
    processing_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    clinical_alerts: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hallucination_flags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    requested_by: Mapped[str] = mapped_column(
        String(36), ForeignKey("health_professionals.id"), nullable=False
    )
    is_validated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    patient = relationship("PatientORM", back_populates="ai_summaries")


# ═══════════════════════════════════════════════════════════════════════
# CONSENT RECORD (Registro de Consentimento LGPD)
# ═══════════════════════════════════════════════════════════════════════


class ConsentRecordORM(AuditMixin, Base):
    __tablename__ = "consent_records"
    __table_args__ = (
        Index("ix_consent_patient", "patient_id"),
    )

    patient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("patients.id"), nullable=False
    )
    consent_type: Mapped[str] = mapped_column(String(50), nullable=False)
    granted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)

    patient = relationship("PatientORM", back_populates="consent_records")


# ═══════════════════════════════════════════════════════════════════════
# PYDANTIC SCHEMAS (for API requests/responses)
# ═══════════════════════════════════════════════════════════════════════


class EventType(str, Enum):
    CONSULTATION = "consulta"
    HOSPITALIZATION = "internacao"
    SURGERY = "cirurgia"
    EMERGENCY = "emergencia"
    PROCEDURE = "procedimento"
    DIAGNOSIS = "diagnostico"
    TREATMENT = "tratamento"
    DISCHARGE = "alta"


class Severity(str, Enum):
    MILD = "leve"
    MODERATE = "moderado"
    SEVERE = "grave"
    CRITICAL = "critico"


class ClinicalEventCreate(BaseModel):
    record_id: str
    event_type: EventType
    event_date: datetime
    description: str = Field(..., min_length=5)
    icd_code: Optional[str] = None
    severity: Optional[Severity] = None


class ClinicalEventResponse(BaseModel):
    id: str
    record_id: str
    event_type: str
    event_date: datetime
    description: str
    icd_code: Optional[str] = None
    severity: Optional[str] = None
    professional_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ExamCreate(BaseModel):
    patient_id: str
    exam_type: str = Field(..., min_length=2)
    exam_date: date
    result: Optional[str] = None
    result_value: Optional[float] = None
    result_unit: Optional[str] = None
    reference_range: Optional[str] = None
    lab_name: Optional[str] = None
    storage_url: Optional[str] = None


class ExamResponse(BaseModel):
    id: str
    patient_id: str
    exam_type: str
    exam_date: date
    result: Optional[str] = None
    result_value: Optional[float] = None
    result_unit: Optional[str] = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PrescriptionCreate(BaseModel):
    patient_id: str
    medication: str = Field(..., min_length=2)
    active_ingredient: Optional[str] = None
    dosage: str
    frequency: str
    route: str
    duration_days: Optional[int] = Field(None, gt=0)
    instructions: Optional[str] = None


class PrescriptionResponse(BaseModel):
    id: str
    patient_id: str
    medication: str
    dosage: str
    frequency: str
    route: str
    is_active: bool
    prescribed_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class AllergyCreate(BaseModel):
    patient_id: str
    allergen: str = Field(..., min_length=2)
    allergen_type: str
    severity: Severity
    reaction: Optional[str] = None


class AllergyResponse(BaseModel):
    id: str
    patient_id: str
    allergen: str
    allergen_type: str
    severity: str
    reaction: Optional[str] = None
    confirmed: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentCreate(BaseModel):
    record_id: str
    doc_type: str
    title: str = Field(..., min_length=3)
    description: Optional[str] = None
    storage_url: str
    mime_type: str
    file_size_bytes: Optional[int] = None


class DocumentResponse(BaseModel):
    id: str
    record_id: str
    doc_type: str
    title: str
    storage_url: str
    mime_type: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AISummaryResponse(BaseModel):
    id: str
    patient_id: str
    summary: str
    risk_level: str
    confidence_score: float
    confidence_label: str
    model_name: str
    processing_time_ms: int
    generated_at: datetime
    clinical_alerts: Optional[str] = None
    is_validated: bool

    model_config = {"from_attributes": True}
