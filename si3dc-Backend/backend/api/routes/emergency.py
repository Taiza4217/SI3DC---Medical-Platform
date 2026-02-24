"""SI3DC — Emergency Routes.

Fast emergency patient summary endpoint with fail-safe mode.
"""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.ai.pipelines.clinical_pipeline import ClinicalPipeline
from backend.domain.models.professional import HealthProfessionalORM
from backend.infrastructure.auth.audit import log_patient_access
from backend.infrastructure.auth.oauth2 import get_current_user
from backend.infrastructure.database.session import get_db
from backend.services.patient_service import PatientService

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.get(
    "/patient-summary/{patient_id}",
    summary="Resumo emergencial do paciente",
    response_model=None,
)
async def emergency_patient_summary(
    patient_id: str,
    request: Request,
    current_user: HealthProfessionalORM = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Gera um resumo emergencial do paciente em poucos segundos.

    **Prioriza:**
    - Alergias críticas
    - Medicações atuais
    - Doenças crônicas
    - Cirurgias importantes
    - Alertas clínicos

    **Fail-safe:** Retorna dados estruturados mesmo se a IA falhar.
    """
    service = PatientService(db)
    patient = await service.get_patient(patient_id)

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paciente não encontrado",
        )

    # Audit log
    await log_patient_access(
        db, current_user.id, patient_id, "emergency_read", "emergency_summary",
        ip_address=request.client.host if request.client else None,
        details="Acesso emergencial ao resumo do paciente",
    )

    # Get longitudinal history
    history = await service.get_longitudinal_history(patient_id)

    # Generate emergency summary via AI pipeline (with fail-safe)
    pipeline = ClinicalPipeline()

    try:
        summary = await pipeline.generate_emergency_summary(history)
    except Exception as e:
        logger.error("emergency_pipeline_failure", error=str(e), patient_id=patient_id)
        # Fail-safe: return raw structured data
        summary = {
            "patient_id": patient_id,
            "fail_safe_mode": True,
            "critical_allergies": [
                a for a in history.get("allergies", [])
                if a.get("severity") in ("grave", "critico")
            ],
            "active_medications": [
                rx for rx in history.get("prescriptions", [])
                if rx.get("is_active")
            ],
            "recent_events": history.get("events", [])[:10],
            "message": "Resumo gerado em modo de segurança (IA indisponível)",
        }

    # Add patient demographic info
    summary["patient_info"] = {
        "name": patient.full_name,
        "birth_date": str(patient.birth_date),
        "gender": patient.gender,
        "blood_type": patient.blood_type,
        "cns": patient.cns,
    }

    logger.info(
        "emergency_summary_generated",
        patient_id=patient_id,
        ai_enhanced=summary.get("ai_enhanced", False),
        requested_by=current_user.id,
    )

    return summary
