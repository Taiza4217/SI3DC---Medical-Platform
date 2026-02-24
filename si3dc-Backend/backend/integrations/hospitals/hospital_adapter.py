"""SI3DC — Hospital Adapter.

Generic adapter for integrating with hospital information systems (HIS).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

import httpx
import structlog

logger = structlog.get_logger(__name__)


class HospitalAdapter(ABC):
    """Abstract adapter for hospital system integration."""

    @abstractmethod
    async def fetch_patient(self, patient_id: str) -> dict[str, Any]:
        """Fetch patient data from the hospital system."""
        ...

    @abstractmethod
    async def fetch_exams(self, patient_id: str) -> list[dict[str, Any]]:
        """Fetch exam results from the hospital system."""
        ...

    @abstractmethod
    async def fetch_prescriptions(self, patient_id: str) -> list[dict[str, Any]]:
        """Fetch active prescriptions from the hospital system."""
        ...

    @abstractmethod
    async def send_clinical_summary(
        self, patient_id: str, summary: dict[str, Any]
    ) -> bool:
        """Send a clinical summary back to the hospital system."""
        ...


class GenericHospitalAdapter(HospitalAdapter):
    """Generic HTTP-based hospital adapter for REST APIs."""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key

    async def _request(
        self, method: str, path: str, data: Optional[dict] = None
    ) -> dict[str, Any]:
        """Make an authenticated request to the hospital API."""
        url = f"{self.base_url}/{path}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.request(method, url, json=data, headers=headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error("hospital_api_error", url=url, error=str(e))
            return {"error": str(e)}

    async def fetch_patient(self, patient_id: str) -> dict[str, Any]:
        return await self._request("GET", f"patients/{patient_id}")

    async def fetch_exams(self, patient_id: str) -> list[dict[str, Any]]:
        result = await self._request("GET", f"patients/{patient_id}/exams")
        return result.get("data", []) if isinstance(result, dict) else []

    async def fetch_prescriptions(self, patient_id: str) -> list[dict[str, Any]]:
        result = await self._request("GET", f"patients/{patient_id}/prescriptions")
        return result.get("data", []) if isinstance(result, dict) else []

    async def send_clinical_summary(
        self, patient_id: str, summary: dict[str, Any]
    ) -> bool:
        result = await self._request(
            "POST", f"patients/{patient_id}/summaries", data=summary
        )
        return "error" not in result
