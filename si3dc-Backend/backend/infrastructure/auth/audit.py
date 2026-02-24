"""SI3DC — Audit Logger.

Records every access to patient data for compliance and security.
"""

from __future__ import annotations

from datetime import datetime, timezone

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.models.clinical import AccessLogORM

logger = structlog.get_logger(__name__)


async def log_patient_access(
    db: AsyncSession,
    professional_id: str,
    patient_id: str,
    action: str,
    resource: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
    details: str | None = None,
) -> None:
    """Record an access to a patient's data in the audit trail."""
    log_entry = AccessLogORM(
        professional_id=professional_id,
        patient_id=patient_id,
        action=action,
        resource=resource,
        ip_address=ip_address,
        user_agent=user_agent,
        accessed_at=datetime.now(timezone.utc),
        details=details,
    )
    db.add(log_entry)

    logger.info(
        "patient_data_access",
        professional_id=professional_id,
        patient_id=patient_id,
        action=action,
        resource=resource,
        ip_address=ip_address,
    )
