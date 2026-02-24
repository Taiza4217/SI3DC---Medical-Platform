"""SI3DC — LGPD Consent Management.

Patient consent management for data sharing and processing.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.infrastructure.security.lgpd import (
    anonymize_patient_data,
    export_patient_data,
    record_consent,
    revoke_consent,
    verify_consent,
)


class ConsentManager:
    """High-level consent management for LGPD compliance."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def grant_consent(
        self,
        patient_id: str,
        consent_type: str,
        purpose: str,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        """Record a patient granting consent."""
        consent = await record_consent(
            self.db, patient_id, consent_type, granted=True,
            purpose=purpose, ip_address=ip_address,
        )
        return {
            "status": "granted",
            "consent_id": consent.id,
            "consent_type": consent_type,
            "patient_id": patient_id,
        }

    async def revoke(self, patient_id: str, consent_type: str) -> dict[str, Any]:
        """Revoke a previously granted consent."""
        success = await revoke_consent(self.db, patient_id, consent_type)
        return {
            "status": "revoked" if success else "not_found",
            "consent_type": consent_type,
            "patient_id": patient_id,
        }

    async def check(self, patient_id: str, consent_type: str) -> bool:
        """Check if a patient has active consent."""
        return await verify_consent(self.db, patient_id, consent_type)

    async def request_data_export(self, patient_id: str) -> dict[str, Any]:
        """LGPD right to data portability."""
        return await export_patient_data(self.db, patient_id)

    async def request_data_erasure(self, patient_id: str) -> dict[str, Any]:
        """LGPD right to erasure (anonymization)."""
        return await anonymize_patient_data(self.db, patient_id)
