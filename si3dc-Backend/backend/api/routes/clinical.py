"""SI3DC — Clinical Routes.

Endpoints for clinical records: documents, exams, prescriptions, allergies, events.
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.models.clinical import (
    AllergyCreate,
    AllergyResponse,
    ClinicalEventCreate,
    ClinicalEventResponse,
    DocumentCreate,
    DocumentResponse,
    ExamCreate,
    ExamResponse,
    PrescriptionCreate,
    PrescriptionResponse,
)
from backend.domain.models.professional import HealthProfessionalORM
from backend.infrastructure.auth.audit import log_patient_access
from backend.infrastructure.auth.oauth2 import get_current_user
from backend.infrastructure.auth.rbac import require_permission
from backend.infrastructure.database.session import get_db
from backend.services.clinical_service import ClinicalService

logger = structlog.get_logger(__name__)
router = APIRouter()


# ── Documents ────────────────────────────────────────────────────────


@router.post(
    "/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Adicionar documento médico",
)
async def add_document(
    body: DocumentCreate,
    request: Request,
    current_user: HealthProfessionalORM = Depends(require_permission("clinical:write")),
    db: AsyncSession = Depends(get_db),
):
    """Adicionar um documento médico ao prontuário."""
    service = ClinicalService(db)
    doc = await service.add_document(body, uploaded_by=current_user.id)
    return DocumentResponse.model_validate(doc)


# ── Exams ────────────────────────────────────────────────────────────


@router.post(
    "/exams",
    response_model=ExamResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar resultado de exame",
)
async def add_exam(
    body: ExamCreate,
    request: Request,
    current_user: HealthProfessionalORM = Depends(require_permission("exam:write")),
    db: AsyncSession = Depends(get_db),
):
    """Registrar um resultado de exame para um paciente."""
    service = ClinicalService(db)
    exam = await service.add_exam(body, requesting_professional_id=current_user.id)

    await log_patient_access(
        db, current_user.id, body.patient_id, "write", "exam",
        ip_address=request.client.host if request.client else None,
    )

    return ExamResponse.model_validate(exam)


@router.get(
    "/exams/{patient_id}",
    response_model=list[ExamResponse],
    summary="Listar exames do paciente",
)
async def list_exams(
    patient_id: str,
    current_user: HealthProfessionalORM = Depends(require_permission("exam:read")),
    db: AsyncSession = Depends(get_db),
):
    """Listar todos os exames de um paciente."""
    service = ClinicalService(db)
    exams = await service.get_patient_exams(patient_id)
    return [ExamResponse.model_validate(e) for e in exams]


# ── Prescriptions ────────────────────────────────────────────────────


@router.post(
    "/prescriptions",
    response_model=PrescriptionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar prescrição médica",
)
async def add_prescription(
    body: PrescriptionCreate,
    request: Request,
    current_user: HealthProfessionalORM = Depends(require_permission("prescription:write")),
    db: AsyncSession = Depends(get_db),
):
    """Registrar uma prescrição médica para um paciente."""
    service = ClinicalService(db)
    rx = await service.add_prescription(body, professional_id=current_user.id)

    await log_patient_access(
        db, current_user.id, body.patient_id, "write", "prescription",
        ip_address=request.client.host if request.client else None,
    )

    return PrescriptionResponse.model_validate(rx)


@router.get(
    "/prescriptions/{patient_id}",
    response_model=list[PrescriptionResponse],
    summary="Listar prescrições ativas do paciente",
)
async def list_prescriptions(
    patient_id: str,
    current_user: HealthProfessionalORM = Depends(require_permission("prescription:read")),
    db: AsyncSession = Depends(get_db),
):
    """Listar prescrições ativas de um paciente."""
    service = ClinicalService(db)
    prescriptions = await service.get_active_prescriptions(patient_id)
    return [PrescriptionResponse.model_validate(rx) for rx in prescriptions]


# ── Allergies ────────────────────────────────────────────────────────


@router.post(
    "/allergies",
    response_model=AllergyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar alergia do paciente",
)
async def add_allergy(
    body: AllergyCreate,
    request: Request,
    current_user: HealthProfessionalORM = Depends(require_permission("allergy:write")),
    db: AsyncSession = Depends(get_db),
):
    """Registrar uma alergia para um paciente."""
    service = ClinicalService(db)
    allergy = await service.add_allergy(body, added_by=current_user.id)

    await log_patient_access(
        db, current_user.id, body.patient_id, "write", "allergy",
        ip_address=request.client.host if request.client else None,
    )

    return AllergyResponse.model_validate(allergy)


@router.get(
    "/allergies/{patient_id}",
    response_model=list[AllergyResponse],
    summary="Listar alergias do paciente",
)
async def list_allergies(
    patient_id: str,
    current_user: HealthProfessionalORM = Depends(require_permission("allergy:read")),
    db: AsyncSession = Depends(get_db),
):
    """Listar todas as alergias de um paciente."""
    service = ClinicalService(db)
    allergies = await service.get_patient_allergies(patient_id)
    return [AllergyResponse.model_validate(a) for a in allergies]


# ── Clinical Events ─────────────────────────────────────────────────


@router.post(
    "/events",
    response_model=ClinicalEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar evento clínico",
)
async def create_event(
    body: ClinicalEventCreate,
    request: Request,
    current_user: HealthProfessionalORM = Depends(require_permission("clinical:write")),
    db: AsyncSession = Depends(get_db),
):
    """Registrar um evento clínico (consulta, internação, procedimento, etc.)."""
    service = ClinicalService(db)
    event = await service.create_clinical_event(body, professional_id=current_user.id)
    return ClinicalEventResponse.model_validate(event)


@router.get(
    "/events/{patient_id}",
    response_model=list[ClinicalEventResponse],
    summary="Listar eventos clínicos do paciente",
)
async def list_events(
    patient_id: str,
    current_user: HealthProfessionalORM = Depends(require_permission("clinical:read")),
    db: AsyncSession = Depends(get_db),
):
    """Listar eventos clínicos de um paciente em ordem cronológica reversa."""
    service = ClinicalService(db)
    events = await service.get_patient_events(patient_id)
    return [ClinicalEventResponse.model_validate(e) for e in events]
