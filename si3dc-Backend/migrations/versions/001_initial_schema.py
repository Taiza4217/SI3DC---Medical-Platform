"""SI3DC — Initial schema: todas as tabelas do domínio.

Revision ID: 001_initial
Revises:
Create Date: 2026-02-21
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Institutions ─────────────────────────────────────────────────
    op.create_table(
        "institutions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("cnes", sa.String(20), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("cnpj", sa.String(18), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("state", sa.String(2), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.create_index("ix_institution_cnes", "institutions", ["cnes"], unique=True)

    # ── Health Professionals ─────────────────────────────────────────
    op.create_table(
        "health_professionals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("registration_type", sa.String(10), nullable=False),
        sa.Column("registration_number", sa.String(20), unique=True, nullable=False),
        sa.Column("registration_state", sa.String(2), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("specialty", sa.String(100), nullable=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="BASIC"),
        sa.Column("institution_id", sa.String(36), sa.ForeignKey("institutions.id"), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.create_index("ix_hp_registration", "health_professionals", ["registration_number"], unique=True)
    op.create_index("ix_hp_institution", "health_professionals", ["institution_id"])

    # ── Patients ─────────────────────────────────────────────────────
    op.create_table(
        "patients",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("cpf", sa.String(14), unique=True, nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("social_name", sa.String(255), nullable=True),
        sa.Column("birth_date", sa.Date(), nullable=False),
        sa.Column("gender", sa.String(20), nullable=False),
        sa.Column("blood_type", sa.String(5), nullable=True),
        sa.Column("rh_factor", sa.String(3), nullable=True),
        sa.Column("cns", sa.String(20), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("state", sa.String(2), nullable=True),
        sa.Column("zip_code", sa.String(10), nullable=True),
        sa.Column("emergency_contact_name", sa.String(255), nullable=True),
        sa.Column("emergency_contact_phone", sa.String(20), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("deceased_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_patients_cpf", "patients", ["cpf"], unique=True)
    op.create_index("ix_patients_name", "patients", ["full_name"])
    op.create_index("ix_patients_birth", "patients", ["birth_date"])

    # ── Medical Records ──────────────────────────────────────────────
    op.create_table(
        "medical_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("patient_id", sa.String(36), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("institution_id", sa.String(36), sa.ForeignKey("institutions.id"), nullable=False),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("health_professionals.id"), nullable=False),
        sa.Column("record_number", sa.String(50), unique=True, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_mr_patient", "medical_records", ["patient_id"])
    op.create_index("ix_mr_institution", "medical_records", ["institution_id"])

    # ── Clinical Events ──────────────────────────────────────────────
    op.create_table(
        "clinical_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("record_id", sa.String(36), sa.ForeignKey("medical_records.id"), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("event_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("icd_code", sa.String(10), nullable=True),
        sa.Column("severity", sa.String(20), nullable=True),
        sa.Column("professional_id", sa.String(36), sa.ForeignKey("health_professionals.id"), nullable=False),
    )
    op.create_index("ix_ce_record", "clinical_events", ["record_id"])
    op.create_index("ix_ce_date", "clinical_events", ["event_date"])
    op.create_index("ix_ce_type", "clinical_events", ["event_type"])

    # ── Medical Documents ────────────────────────────────────────────
    op.create_table(
        "medical_documents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("record_id", sa.String(36), sa.ForeignKey("medical_records.id"), nullable=False),
        sa.Column("doc_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("storage_url", sa.String(500), nullable=False),
        sa.Column("mime_type", sa.String(50), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("uploaded_by", sa.String(36), sa.ForeignKey("health_professionals.id"), nullable=False),
    )
    op.create_index("ix_md_record", "medical_documents", ["record_id"])

    # ── Exams ────────────────────────────────────────────────────────
    op.create_table(
        "exams",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("patient_id", sa.String(36), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("exam_type", sa.String(100), nullable=False),
        sa.Column("exam_date", sa.Date(), nullable=False),
        sa.Column("result", sa.Text(), nullable=True),
        sa.Column("result_value", sa.Float(), nullable=True),
        sa.Column("result_unit", sa.String(50), nullable=True),
        sa.Column("reference_range", sa.String(100), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("lab_name", sa.String(255), nullable=True),
        sa.Column("requesting_professional_id", sa.String(36), sa.ForeignKey("health_professionals.id"), nullable=False),
        sa.Column("storage_url", sa.String(500), nullable=True),
    )
    op.create_index("ix_exam_patient", "exams", ["patient_id"])
    op.create_index("ix_exam_date", "exams", ["exam_date"])

    # ── Prescriptions ────────────────────────────────────────────────
    op.create_table(
        "prescriptions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("patient_id", sa.String(36), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("professional_id", sa.String(36), sa.ForeignKey("health_professionals.id"), nullable=False),
        sa.Column("medication", sa.String(255), nullable=False),
        sa.Column("active_ingredient", sa.String(255), nullable=True),
        sa.Column("dosage", sa.String(100), nullable=False),
        sa.Column("frequency", sa.String(100), nullable=False),
        sa.Column("route", sa.String(50), nullable=False),
        sa.Column("duration_days", sa.Integer(), nullable=True),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("prescribed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.create_index("ix_rx_patient", "prescriptions", ["patient_id"])
    op.create_index("ix_rx_date", "prescriptions", ["prescribed_at"])

    # ── Allergies ────────────────────────────────────────────────────
    op.create_table(
        "allergies",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("patient_id", sa.String(36), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("allergen", sa.String(255), nullable=False),
        sa.Column("allergen_type", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("reaction", sa.Text(), nullable=True),
        sa.Column("confirmed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("confirmed_by", sa.String(36), sa.ForeignKey("health_professionals.id"), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_allergy_patient", "allergies", ["patient_id"])

    # ── Medication History ───────────────────────────────────────────
    op.create_table(
        "medication_history",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("patient_id", sa.String(36), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("medication", sa.String(255), nullable=False),
        sa.Column("dosage", sa.String(100), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("discontinued_reason", sa.Text(), nullable=True),
        sa.Column("adverse_effects", sa.Text(), nullable=True),
    )
    op.create_index("ix_medhist_patient", "medication_history", ["patient_id"])

    # ── Access Logs ──────────────────────────────────────────────────
    op.create_table(
        "access_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("professional_id", sa.String(36), sa.ForeignKey("health_professionals.id"), nullable=False),
        sa.Column("patient_id", sa.String(36), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("resource", sa.String(100), nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("accessed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
    )
    op.create_index("ix_access_professional", "access_logs", ["professional_id"])
    op.create_index("ix_access_patient", "access_logs", ["patient_id"])
    op.create_index("ix_access_timestamp", "access_logs", ["accessed_at"])

    # ── AI Clinical Summaries ────────────────────────────────────────
    op.create_table(
        "ai_clinical_summaries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("patient_id", sa.String(36), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("risk_level", sa.String(20), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("confidence_label", sa.String(20), nullable=False),
        sa.Column("model_name", sa.String(50), nullable=False),
        sa.Column("model_version", sa.String(20), nullable=False),
        sa.Column("processing_time_ms", sa.Integer(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("clinical_alerts", sa.Text(), nullable=True),
        sa.Column("hallucination_flags", sa.Text(), nullable=True),
        sa.Column("requested_by", sa.String(36), sa.ForeignKey("health_professionals.id"), nullable=False),
        sa.Column("is_validated", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.create_index("ix_ais_patient", "ai_clinical_summaries", ["patient_id"])
    op.create_index("ix_ais_generated", "ai_clinical_summaries", ["generated_at"])

    # ── Consent Records ──────────────────────────────────────────────
    op.create_table(
        "consent_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("patient_id", sa.String(36), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("consent_type", sa.String(50), nullable=False),
        sa.Column("granted", sa.Boolean(), nullable=False),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("purpose", sa.Text(), nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=True),
    )
    op.create_index("ix_consent_patient", "consent_records", ["patient_id"])

    # ── Refresh Tokens (Blacklist) ───────────────────────────────────
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("jti", sa.String(36), unique=True, nullable=False, comment="JWT ID"),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("health_professionals.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False, comment="SHA-256 hash"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_rt_jti", "refresh_tokens", ["jti"], unique=True)
    op.create_index("ix_rt_user", "refresh_tokens", ["user_id"])
    op.create_index("ix_rt_token_hash", "refresh_tokens", ["token_hash"])
    op.create_index("ix_rt_expires", "refresh_tokens", ["expires_at"])


def downgrade() -> None:
    """Drop all tables in reverse dependency order."""
    op.drop_table("refresh_tokens")
    op.drop_table("consent_records")
    op.drop_table("ai_clinical_summaries")
    op.drop_table("access_logs")
    op.drop_table("medication_history")
    op.drop_table("allergies")
    op.drop_table("prescriptions")
    op.drop_table("exams")
    op.drop_table("medical_documents")
    op.drop_table("clinical_events")
    op.drop_table("medical_records")
    op.drop_table("patients")
    op.drop_table("health_professionals")
    op.drop_table("institutions")
