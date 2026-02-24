"""SI3DC — FHIR R4 Client.

Integration with FHIR R4 compliant servers for clinical data exchange.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Optional

import httpx
import structlog

from backend.config import get_settings

logger = structlog.get_logger(__name__)


class FHIRClient:
    """Client for FHIR R4 resource operations."""

    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.FHIR_SERVER_URL

    async def _request(
        self, method: str, path: str, data: Optional[dict] = None
    ) -> dict[str, Any]:
        """Make a request to the FHIR server."""
        url = f"{self.base_url}/{path}"
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.request(
                method, url,
                json=data,
                headers={"Content-Type": "application/fhir+json", "Accept": "application/fhir+json"},
            )
            response.raise_for_status()
            return response.json()

    # ── Patient Resource ─────────────────────────────────────────────

    async def get_patient(self, fhir_id: str) -> dict[str, Any]:
        """Fetch a Patient resource by FHIR ID."""
        return await self._request("GET", f"Patient/{fhir_id}")

    async def search_patient(self, identifier: str) -> dict[str, Any]:
        """Search for patients by identifier (e.g., CPF)."""
        return await self._request("GET", f"Patient?identifier={identifier}")

    def to_fhir_patient(self, patient_data: dict[str, Any]) -> dict[str, Any]:
        """Convert internal patient data to FHIR R4 Patient resource."""
        return {
            "resourceType": "Patient",
            "identifier": [
                {
                    "system": "urn:oid:2.16.840.1.113883.13.236",  # CPF OID
                    "value": patient_data.get("cpf", ""),
                }
            ],
            "name": [
                {
                    "use": "official",
                    "text": patient_data.get("full_name", ""),
                }
            ],
            "gender": self._map_gender(patient_data.get("gender", "")),
            "birthDate": str(patient_data.get("birth_date", "")),
            "telecom": [
                {"system": "phone", "value": patient_data.get("phone", "")},
                {"system": "email", "value": patient_data.get("email", "")},
            ],
            "address": [
                {
                    "text": patient_data.get("address", ""),
                    "city": patient_data.get("city", ""),
                    "state": patient_data.get("state", ""),
                    "postalCode": patient_data.get("zip_code", ""),
                    "country": "BR",
                }
            ],
        }

    def from_fhir_patient(self, fhir_resource: dict[str, Any]) -> dict[str, Any]:
        """Convert FHIR R4 Patient resource to internal format."""
        identifiers = fhir_resource.get("identifier", [])
        cpf = ""
        for ident in identifiers:
            if "cpf" in ident.get("system", "").lower() or "236" in ident.get("system", ""):
                cpf = ident.get("value", "")
                break

        names = fhir_resource.get("name", [{}])
        full_name = names[0].get("text", "") if names else ""

        return {
            "cpf": cpf,
            "full_name": full_name,
            "gender": self._reverse_map_gender(fhir_resource.get("gender", "")),
            "birth_date": fhir_resource.get("birthDate", ""),
        }

    # ── Observation (Exam) Resource ──────────────────────────────────

    def to_fhir_observation(self, exam_data: dict[str, Any]) -> dict[str, Any]:
        """Convert exam data to FHIR R4 Observation resource."""
        return {
            "resourceType": "Observation",
            "status": "final" if exam_data.get("status") == "completed" else "preliminary",
            "code": {
                "coding": [{"display": exam_data.get("exam_type", "")}],
            },
            "subject": {"reference": f"Patient/{exam_data.get('patient_id', '')}"},
            "effectiveDateTime": str(exam_data.get("exam_date", "")),
            "valueString": exam_data.get("result", ""),
        }

    # ── AllergyIntolerance Resource ──────────────────────────────────

    def to_fhir_allergy(self, allergy_data: dict[str, Any]) -> dict[str, Any]:
        """Convert allergy data to FHIR R4 AllergyIntolerance resource."""
        severity_map = {
            "leve": "mild",
            "moderado": "moderate",
            "grave": "severe",
            "critico": "severe",
        }
        return {
            "resourceType": "AllergyIntolerance",
            "clinicalStatus": {
                "coding": [{"code": "active", "display": "Active"}]
            },
            "type": "allergy",
            "criticality": "high" if allergy_data.get("severity") in ("grave", "critico") else "low",
            "code": {"coding": [{"display": allergy_data.get("allergen", "")}]},
            "patient": {"reference": f"Patient/{allergy_data.get('patient_id', '')}"},
            "reaction": [
                {
                    "severity": severity_map.get(allergy_data.get("severity", ""), "mild"),
                    "description": allergy_data.get("reaction", ""),
                }
            ],
        }

    # ── Helpers ──────────────────────────────────────────────────────

    def _map_gender(self, gender: str) -> str:
        mapping = {"masculino": "male", "feminino": "female", "outro": "other"}
        return mapping.get(gender.lower(), "unknown")

    def _reverse_map_gender(self, fhir_gender: str) -> str:
        mapping = {"male": "masculino", "female": "feminino", "other": "outro"}
        return mapping.get(fhir_gender.lower(), "nao_informado")
