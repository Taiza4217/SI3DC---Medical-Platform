"""SI3DC — SUS Integration Service.

Integration with SUS (Sistema Único de Saúde) APIs.
"""

from __future__ import annotations

from typing import Any, Optional

import httpx
import structlog

from backend.config import get_settings

logger = structlog.get_logger(__name__)


class SUSService:
    """Client for SUS (Sistema Único de Saúde) APIs."""

    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.SUS_API_BASE_URL

    async def _get(self, path: str, params: Optional[dict] = None) -> dict[str, Any]:
        """Make a GET request to SUS API."""
        url = f"{self.base_url}/{path}"
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error("sus_api_error", url=url, error=str(e))
            return {"error": str(e), "status": "unavailable"}

    async def search_institution_by_cnes(self, cnes: str) -> dict[str, Any]:
        """Search for a health institution by CNES code."""
        return await self._get("cnes/estabelecimentos", params={"codigo_cnes": cnes})

    async def get_procedures(self, procedure_code: str) -> dict[str, Any]:
        """Get SUS procedure details by code."""
        return await self._get(
            "procedimentos/procedimentos",
            params={"codigo_procedimento": procedure_code},
        )

    async def get_medications(self, medication_name: str) -> dict[str, Any]:
        """Search SUS medication database (RENAME)."""
        return await self._get(
            "assistencia-farmaceutica/medicamentos",
            params={"nome": medication_name},
        )

    async def sync_patient_data(
        self, cns: str
    ) -> dict[str, Any]:
        """
        Synchronize patient data from SUS databases using CNS.
        Returns available clinical data from public health records.
        """
        logger.info("sus_sync_started", cns=cns)

        # In production, this would aggregate data from multiple SUS endpoints
        result = {
            "cns": cns,
            "vaccination_records": await self._get(
                "imunizacao/vacinacao", params={"cns": cns}
            ),
            "hospitalizations": await self._get(
                "sih/internacoes", params={"cns_paciente": cns}
            ),
            "sync_status": "completed",
        }

        logger.info("sus_sync_completed", cns=cns)
        return result
