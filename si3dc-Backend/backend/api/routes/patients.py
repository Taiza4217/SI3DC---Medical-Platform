"""SI3DC — Patient Routes.

Patient CRUD, search, and longitudinal history endpoints.
"""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.models.patient import PatientCreate, PatientResponse, PatientSummary
from backend.domain.models.professional import HealthProfessionalORM
from backend.infrastructure.auth.audit import log_patient_access
from backend.infrastructure.auth.oauth2 import get_current_user
from backend.infrastructure.auth.rbac import require_permission
from backend.infrastructure.database.session import get_db
from backend.infrastructure.security.suspicious_access import check_suspicious_access
from backend.services.patient_service import PatientService

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.post(
    "/",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar novo paciente",
)
async def create_patient(
    body: PatientCreate,
    request: Request,
    current_user: HealthProfessionalORM = Depends(require_permission("patient:write")),
    db: AsyncSession = Depends(get_db),
):
    """Registrar um novo paciente no sistema."""
    service = PatientService(db)

    # Check if CPF already exists
    existing = await service.get_patient_by_cpf(body.cpf)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Paciente com este CPF já cadastrado",
        )

    patient = await service.create_patient(body, created_by=current_user.id)

    await log_patient_access(
        db, current_user.id, patient.id, "create", "patient",
        ip_address=request.client.host if request.client else None,
    )

    return PatientResponse.model_validate(patient)


@router.get(
    "/search",
    response_model=list[PatientSummary],
    summary="Buscar pacientes",
)
async def search_patients(
    q: str = Query(..., min_length=2, description="Termo de busca (nome ou CPF)"),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: HealthProfessionalORM = Depends(require_permission("patient:read")),
    db: AsyncSession = Depends(get_db),
):
    """Buscar pacientes por nome ou CPF."""
    service = PatientService(db)
    patients = await service.search_patients(q, offset, limit)
    return [PatientSummary.model_validate(p) for p in patients]


@router.get(
    "/{patient_id}",
    response_model=PatientResponse,
    summary="Buscar paciente por ID",
)
async def get_patient(
    patient_id: str,
    request: Request,
    current_user: HealthProfessionalORM = Depends(require_permission("patient:read")),
    db: AsyncSession = Depends(get_db),
):
    """
    Buscar detalhes de um paciente.

    Aciona verificação de acesso suspeito e registra log de auditoria.
    """
    service = PatientService(db)
    patient = await service.get_patient(patient_id)

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paciente não encontrado",
        )

    # Check for suspicious access
    warning = await check_suspicious_access(db, current_user.id, patient_id)
    if warning:
        logger.warning("suspicious_access_detected", warning=warning, user_id=current_user.id)

    # Audit log
    await log_patient_access(
        db, current_user.id, patient_id, "read", "patient",
        ip_address=request.client.host if request.client else None,
    )

    return PatientResponse.model_validate(patient)


@router.get(
    "/{patient_id}/history",
    summary="Histórico clínico longitudinal",
)
async def get_patient_history(
    patient_id: str,
    request: Request,
    current_user: HealthProfessionalORM = Depends(require_permission("clinical:read")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Retorna o histórico clínico longitudinal completo do paciente.

    Inclui: eventos clínicos, exames, prescrições, alergias e histórico medicamentoso.
    """
    service = PatientService(db)

    # Verify patient exists
    patient = await service.get_patient(patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paciente não encontrado",
        )

    # Audit log
    await log_patient_access(
        db, current_user.id, patient_id, "read", "clinical_history",
        ip_address=request.client.host if request.client else None,
    )

    history = await service.get_longitudinal_history(patient_id)
    return history
