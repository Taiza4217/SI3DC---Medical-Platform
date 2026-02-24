"""SI3DC — Hallucination Detector.

Cross-references AI output with source clinical data to detect fabricated information.
"""

from __future__ import annotations

import re
from typing import Any


def detect_hallucinations(
    ai_text: str,
    source_data: dict[str, Any],
) -> dict[str, Any]:
    """
    Detect potential hallucinations in AI-generated clinical text
    by cross-referencing with source patient data.

    Returns:
        Dictionary with flags list and flag_count.
    """
    flags: list[dict[str, str]] = []

    if not ai_text:
        return {"flags": [], "flag_count": 0}

    ai_lower = ai_text.lower()

    # ── Check 1: Medication mentions not in source data ──────────────
    known_meds = set()
    for rx in source_data.get("active_medications", []):
        name = rx.get("name", rx.get("medication", ""))
        if name:
            known_meds.add(name.lower())
    for mh in source_data.get("medication_history", []):
        name = mh.get("medication", "")
        if name:
            known_meds.add(name.lower())

    # Common medication patterns in text
    med_patterns = re.findall(
        r"(?:medicação|medicamento|prescrito|uso de|tomando)\s+(\w+)", ai_lower
    )
    for med_mention in med_patterns:
        if med_mention and len(med_mention) > 3 and med_mention not in known_meds:
            # Check partial match
            if not any(med_mention in known or known in med_mention for known in known_meds):
                flags.append({
                    "type": "unknown_medication",
                    "detail": f"Medicação '{med_mention}' mencionada mas não encontrada nos dados",
                })

    # ── Check 2: ICD codes mentioned but not in events ───────────────
    known_icds = {
        e.get("icd_code", "").lower()
        for e in source_data.get("events", [])
        if e.get("icd_code")
    }
    icd_mentions = re.findall(r"[A-Z]\d{2}(?:\.\d{1,2})?", ai_text)
    for icd in icd_mentions:
        if icd.lower() not in known_icds and known_icds:
            flags.append({
                "type": "unknown_icd_code",
                "detail": f"CID '{icd}' mencionado mas não registrado nos eventos clínicos",
            })

    # ── Check 3: Contradiction detection ─────────────────────────────
    allergy_names = {
        a.get("allergen", "").lower()
        for a in source_data.get("allergies", [])
    }

    # Check if AI recommends an allergen
    for allergen in allergy_names:
        if allergen and f"prescrever {allergen}" in ai_lower:
            flags.append({
                "type": "allergy_contradiction",
                "detail": f"IA sugere prescrição de '{allergen}' que é um alérgeno do paciente",
            })

    # ── Check 4: Date consistency ────────────────────────────────────
    date_patterns = re.findall(r"\d{4}-\d{2}-\d{2}", ai_text)
    known_dates = set()
    for e in source_data.get("events", []):
        d = e.get("date", "")
        if d:
            known_dates.add(d[:10])

    for mentioned_date in date_patterns:
        if known_dates and mentioned_date not in known_dates:
            flags.append({
                "type": "unverified_date",
                "detail": f"Data '{mentioned_date}' mencionada sem correspondência nos registros",
            })

    return {
        "flags": flags,
        "flag_count": len(flags),
    }
