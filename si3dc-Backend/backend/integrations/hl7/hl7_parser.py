"""SI3DC — HL7 v2 Message Parser.

Parses HL7 v2.x messages for clinical data exchange with legacy hospital systems.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

import structlog

logger = structlog.get_logger(__name__)


class HL7Parser:
    """Parser for HL7 v2.x messages."""

    SEGMENT_SEPARATOR = "\r"
    FIELD_SEPARATOR = "|"
    COMPONENT_SEPARATOR = "^"

    def parse_message(self, raw_message: str) -> dict[str, Any]:
        """Parse a raw HL7 v2 message into a structured dictionary."""
        segments = raw_message.strip().split(self.SEGMENT_SEPARATOR)
        if not segments:
            segments = raw_message.strip().split("\n")

        parsed: dict[str, Any] = {"segments": {}, "raw": raw_message}

        for segment_str in segments:
            if not segment_str.strip():
                continue
            fields = segment_str.split(self.FIELD_SEPARATOR)
            segment_type = fields[0].strip()

            if segment_type == "MSH":
                parsed["segments"]["MSH"] = self._parse_msh(fields)
            elif segment_type == "PID":
                parsed["segments"]["PID"] = self._parse_pid(fields)
            elif segment_type == "OBX":
                if "OBX" not in parsed["segments"]:
                    parsed["segments"]["OBX"] = []
                parsed["segments"]["OBX"].append(self._parse_obx(fields))
            elif segment_type == "AL1":
                if "AL1" not in parsed["segments"]:
                    parsed["segments"]["AL1"] = []
                parsed["segments"]["AL1"].append(self._parse_al1(fields))
            elif segment_type == "DG1":
                if "DG1" not in parsed["segments"]:
                    parsed["segments"]["DG1"] = []
                parsed["segments"]["DG1"].append(self._parse_dg1(fields))
            else:
                parsed["segments"][segment_type] = fields

        return parsed

    def _parse_msh(self, fields: list[str]) -> dict[str, str]:
        """Parse MSH (Message Header) segment."""
        return {
            "encoding_chars": self._safe_get(fields, 1, ""),
            "sending_app": self._safe_get(fields, 2, ""),
            "sending_facility": self._safe_get(fields, 3, ""),
            "receiving_app": self._safe_get(fields, 4, ""),
            "receiving_facility": self._safe_get(fields, 5, ""),
            "datetime": self._safe_get(fields, 6, ""),
            "message_type": self._safe_get(fields, 8, ""),
            "message_control_id": self._safe_get(fields, 9, ""),
            "version": self._safe_get(fields, 11, ""),
        }

    def _parse_pid(self, fields: list[str]) -> dict[str, str]:
        """Parse PID (Patient Identification) segment."""
        patient_name = self._safe_get(fields, 5, "")
        name_parts = patient_name.split(self.COMPONENT_SEPARATOR)

        return {
            "patient_id": self._safe_get(fields, 3, ""),
            "last_name": name_parts[0] if name_parts else "",
            "first_name": name_parts[1] if len(name_parts) > 1 else "",
            "birth_date": self._safe_get(fields, 7, ""),
            "gender": self._safe_get(fields, 8, ""),
            "address": self._safe_get(fields, 11, ""),
            "phone": self._safe_get(fields, 13, ""),
            "cpf": self._safe_get(fields, 19, ""),
        }

    def _parse_obx(self, fields: list[str]) -> dict[str, str]:
        """Parse OBX (Observation/Result) segment."""
        return {
            "set_id": self._safe_get(fields, 1, ""),
            "value_type": self._safe_get(fields, 2, ""),
            "observation_id": self._safe_get(fields, 3, ""),
            "value": self._safe_get(fields, 5, ""),
            "units": self._safe_get(fields, 6, ""),
            "reference_range": self._safe_get(fields, 7, ""),
            "status": self._safe_get(fields, 11, ""),
        }

    def _parse_al1(self, fields: list[str]) -> dict[str, str]:
        """Parse AL1 (Patient Allergy) segment."""
        return {
            "set_id": self._safe_get(fields, 1, ""),
            "allergy_type": self._safe_get(fields, 2, ""),
            "allergen": self._safe_get(fields, 3, ""),
            "severity": self._safe_get(fields, 4, ""),
            "reaction": self._safe_get(fields, 5, ""),
        }

    def _parse_dg1(self, fields: list[str]) -> dict[str, str]:
        """Parse DG1 (Diagnosis) segment."""
        return {
            "set_id": self._safe_get(fields, 1, ""),
            "diagnosis_code": self._safe_get(fields, 3, ""),
            "description": self._safe_get(fields, 4, ""),
            "diagnosis_type": self._safe_get(fields, 6, ""),
        }

    def _safe_get(self, lst: list[str], index: int, default: str) -> str:
        """Safely get an element from a list."""
        try:
            return lst[index].strip() if index < len(lst) else default
        except (IndexError, AttributeError):
            return default

    def to_internal_patient(self, parsed: dict[str, Any]) -> dict[str, Any]:
        """Convert parsed HL7 data to internal patient format."""
        pid = parsed.get("segments", {}).get("PID", {})
        return {
            "cpf": pid.get("cpf", ""),
            "full_name": f"{pid.get('first_name', '')} {pid.get('last_name', '')}".strip(),
            "birth_date": self._parse_hl7_date(pid.get("birth_date", "")),
            "gender": self._map_gender(pid.get("gender", "")),
        }

    def _parse_hl7_date(self, date_str: str) -> Optional[str]:
        """Parse HL7 date format (YYYYMMDD) to ISO format."""
        if len(date_str) >= 8:
            try:
                return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            except Exception:
                return None
        return None

    def _map_gender(self, hl7_gender: str) -> str:
        mapping = {"M": "masculino", "F": "feminino", "O": "outro", "U": "nao_informado"}
        return mapping.get(hl7_gender.upper(), "nao_informado")
