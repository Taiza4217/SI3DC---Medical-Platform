"""SI3DC — Serviço Clínico.

Lógica de negócio para prontuário clínico: documentos, exames, prescrições, alergias.

DECISÕES DE ARQUITETURA:
- Cada operação de escrita invalida o cache do histórico do paciente.
- Usa .is_(True) para comparações SQLAlchemy corretas.
- Flush após cada insert para obter o ID antes do commit.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.models.clinical import (
    AllergyCreate,
    AllergyORM,
    ClinicalEventCreate,
    ClinicalEventORM,
    DocumentCreate,
    ExamCreate,
    ExamORM,
    MedicalDocumentORM,
    PrescriptionCreate,
    PrescriptionORM,
)
from backend.services.patient_service import PatientService

logger = structlog.get_logger(__name__)


class ClinicalService:
    """Camada de serviço para operações do prontuário clínico.

    Gerencia: eventos clínicos, documentos, exames, prescrições e alergias.
    Toda operação de escrita invalida o cache do histórico do paciente.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Eventos Clínicos ─────────────────────────────────────────────

    async def create_clinical_event(
        self, data: ClinicalEventCreate, professional_id: str
    ) -> ClinicalEventORM:
        """Registra um novo evento clínico (consulta, internação, procedimento, etc.)."""
        event = ClinicalEventORM(
            record_id=data.record_id,
            event_type=data.event_type.value,
            event_date=data.event_date,
            description=data.description,
            icd_code=data.icd_code,
            severity=data.severity.value if data.severity else None,
            professional_id=professional_id,
        )
        self.db.add(event)
        await self.db.flush()
        logger.info("clinical_event_created", event_id=event.id, type=event.event_type)
        return event

    async def get_patient_events(
        self, patient_id: str, offset: int = 0, limit: int = 50
    ) -> list[ClinicalEventORM]:
        """Lista eventos clínicos de um paciente em ordem cronológica reversa."""
        from backend.domain.models.clinical import MedicalRecordORM

        # Buscar IDs dos prontuários do paciente
        record_ids_result = await self.db.execute(
            select(MedicalRecordORM.id).where(MedicalRecordORM.patient_id == patient_id)
        )
        record_ids = [r for r in record_ids_result.scalars().all()]

        if not record_ids:
            return []

        result = await self.db.execute(
            select(ClinicalEventORM)
            .where(ClinicalEventORM.record_id.in_(record_ids))
            .order_by(ClinicalEventORM.event_date.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    # ── Documentos Médicos ───────────────────────────────────────────

    async def add_document(
        self, data: DocumentCreate, uploaded_by: str
    ) -> MedicalDocumentORM:
        """Adiciona um documento médico ao prontuário (laudo, imagem, etc.)."""
        doc = MedicalDocumentORM(
            record_id=data.record_id,
            doc_type=data.doc_type,
            title=data.title,
            description=data.description,
            storage_url=data.storage_url,
            mime_type=data.mime_type,
            file_size_bytes=data.file_size_bytes,
            uploaded_by=uploaded_by,
        )
        self.db.add(doc)
        await self.db.flush()
        logger.info("document_added", doc_id=doc.id, type=doc.doc_type)
        return doc

    # ── Exames ───────────────────────────────────────────────────────

    async def add_exam(
        self, data: ExamCreate, requesting_professional_id: str
    ) -> ExamORM:
        """Registra um resultado de exame para o paciente.

        Status é automaticamente definido como 'completed' se houver resultado.
        """
        exam = ExamORM(
            patient_id=data.patient_id,
            exam_type=data.exam_type,
            exam_date=data.exam_date,
            result=data.result,
            result_value=data.result_value,
            result_unit=data.result_unit,
            reference_range=data.reference_range,
            lab_name=data.lab_name,
            storage_url=data.storage_url,
            requesting_professional_id=requesting_professional_id,
            status="completed" if data.result else "pending",
        )
        self.db.add(exam)
        await self.db.flush()

        # Invalidar cache do histórico do paciente
        await PatientService.invalidate_patient_cache(data.patient_id)

        logger.info("exam_added", exam_id=exam.id, type=exam.exam_type)
        return exam

    async def get_patient_exams(
        self, patient_id: str, offset: int = 0, limit: int = 50
    ) -> list[ExamORM]:
        """Lista todos os exames de um paciente ordenados por data."""
        result = await self.db.execute(
            select(ExamORM)
            .where(ExamORM.patient_id == patient_id)
            .order_by(ExamORM.exam_date.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    # ── Prescrições ──────────────────────────────────────────────────

    async def add_prescription(
        self, data: PrescriptionCreate, professional_id: str
    ) -> PrescriptionORM:
        """Registra uma prescrição médica para o paciente."""
        rx = PrescriptionORM(
            patient_id=data.patient_id,
            professional_id=professional_id,
            medication=data.medication,
            active_ingredient=data.active_ingredient,
            dosage=data.dosage,
            frequency=data.frequency,
            route=data.route,
            duration_days=data.duration_days,
            instructions=data.instructions,
            prescribed_at=datetime.now(timezone.utc),
        )
        self.db.add(rx)
        await self.db.flush()

        # Invalidar cache do histórico do paciente
        await PatientService.invalidate_patient_cache(data.patient_id)

        logger.info("prescription_added", rx_id=rx.id, medication=rx.medication)
        return rx

    async def get_active_prescriptions(self, patient_id: str) -> list[PrescriptionORM]:
        """Lista prescrições ativas de um paciente.

        SEC-5 fix: usa .is_(True) em vez de == True.
        """
        result = await self.db.execute(
            select(PrescriptionORM)
            .where(PrescriptionORM.patient_id == patient_id)
            .where(PrescriptionORM.is_active.is_(True))
            .order_by(PrescriptionORM.prescribed_at.desc())
        )
        return list(result.scalars().all())

    # ── Alergias ─────────────────────────────────────────────────────

    async def add_allergy(
        self, data: AllergyCreate, added_by: str
    ) -> AllergyORM:
        """Registra uma alergia para o paciente.

        Alergias com severidade 'grave' ou 'crítico' disparam alertas
        no resumo emergencial e na análise de IA.
        """
        allergy = AllergyORM(
            patient_id=data.patient_id,
            allergen=data.allergen,
            allergen_type=data.allergen_type,
            severity=data.severity.value,
            reaction=data.reaction,
        )
        self.db.add(allergy)
        await self.db.flush()

        # Invalidar cache do histórico do paciente
        await PatientService.invalidate_patient_cache(data.patient_id)

        logger.info("allergy_added", allergy_id=allergy.id, allergen=allergy.allergen)
        return allergy

    async def get_patient_allergies(self, patient_id: str) -> list[AllergyORM]:
        """Lista todas as alergias de um paciente."""
        result = await self.db.execute(
            select(AllergyORM)
            .where(AllergyORM.patient_id == patient_id)
        )
        return list(result.scalars().all())

    async def get_critical_allergies(self, patient_id: str) -> list[AllergyORM]:
        """Busca apenas alergias graves/críticas — usado no modo emergência."""
        result = await self.db.execute(
            select(AllergyORM)
            .where(AllergyORM.patient_id == patient_id)
            .where(AllergyORM.severity.in_(["grave", "critico"]))
        )
        return list(result.scalars().all())
