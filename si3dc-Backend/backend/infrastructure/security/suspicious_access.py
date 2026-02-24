"""SI3DC — Suspicious Access Detector.

Detects anomalous access patterns to patient records.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.models.clinical import AccessLogORM

logger = structlog.get_logger(__name__)


# Thresholds
MAX_PATIENTS_PER_HOUR = 50
MAX_ACCESS_SAME_PATIENT_PER_HOUR = 20
UNUSUAL_HOUR_START = 0  # midnight
UNUSUAL_HOUR_END = 5    # 5 AM


async def check_suspicious_access(
    db: AsyncSession,
    professional_id: str,
    patient_id: str,
) -> Optional[str]:
    """
    Check if the current access pattern is suspicious.
    Returns a warning message if suspicious, None otherwise.
    """
    now = datetime.now(timezone.utc)
    one_hour_ago = now - timedelta(hours=1)

    # Check 1: Too many distinct patients accessed in the last hour
    result = await db.execute(
        select(func.count(func.distinct(AccessLogORM.patient_id)))
        .where(AccessLogORM.professional_id == professional_id)
        .where(AccessLogORM.accessed_at >= one_hour_ago)
    )
    distinct_patients = result.scalar() or 0

    if distinct_patients > MAX_PATIENTS_PER_HOUR:
        warning = (
            f"Acesso suspeito: {distinct_patients} pacientes acessados na última hora "
            f"(limite: {MAX_PATIENTS_PER_HOUR})"
        )
        logger.warning(
            "suspicious_access_volume",
            professional_id=professional_id,
            distinct_patients=distinct_patients,
        )
        return warning

    # Check 2: Too many accesses to the same patient
    result = await db.execute(
        select(func.count(AccessLogORM.id))
        .where(AccessLogORM.professional_id == professional_id)
        .where(AccessLogORM.patient_id == patient_id)
        .where(AccessLogORM.accessed_at >= one_hour_ago)
    )
    same_patient_count = result.scalar() or 0

    if same_patient_count > MAX_ACCESS_SAME_PATIENT_PER_HOUR:
        warning = (
            f"Acesso repetitivo ao paciente {patient_id}: "
            f"{same_patient_count} vezes na última hora"
        )
        logger.warning(
            "suspicious_access_repetitive",
            professional_id=professional_id,
            patient_id=patient_id,
            count=same_patient_count,
        )
        return warning

    # Check 3: Access during unusual hours
    if UNUSUAL_HOUR_START <= now.hour < UNUSUAL_HOUR_END:
        logger.info(
            "unusual_hour_access",
            professional_id=professional_id,
            hour=now.hour,
        )
        return f"Acesso em horário incomum: {now.hour}h UTC"

    return None
