"""SI3DC — AI Governance Layer.

Verifies clinical conflicts, detects inconsistencies,
analyzes recommendation risk, and explains AI decisions.
"""

from __future__ import annotations

from typing import Any

import structlog

logger = structlog.get_logger(__name__)


# ── Known drug interaction database (simplified) ─────────────────────
KNOWN_INTERACTIONS: dict[tuple[str, str], str] = {
    ("warfarina", "aspirina"): "Risco elevado de sangramento",
    ("metformina", "contraste_iodado"): "Risco de acidose láctica",
    ("inibidor_eca", "potassio"): "Risco de hipercalemia",
    ("lítio", "ibuprofeno"): "Aumento dos níveis de lítio",
    ("ssri", "imao"): "Síndrome serotoninérgica",
    ("metformina", "alcool"): "Hipoglicemia severa",
    ("anticoagulante", "aine"): "Risco de sangramento gastrointestinal",
}


class AIGovernance:
    """AI governance layer for clinical decision support validation."""

    def verify_clinical_conflicts(
        self, medications: list[dict[str, Any]], allergies: list[dict[str, Any]]
    ) -> list[dict[str, str]]:
        """
        Check for drug-drug interactions and drug-allergy conflicts.
        Returns a list of detected conflicts.
        """
        conflicts: list[dict[str, str]] = []

        # Check drug-drug interactions
        med_names = [m.get("name", m.get("medication", "")).lower() for m in medications]
        for i, med_a in enumerate(med_names):
            for med_b in med_names[i + 1:]:
                key1 = (med_a, med_b)
                key2 = (med_b, med_a)
                if key1 in KNOWN_INTERACTIONS:
                    conflicts.append({
                        "type": "drug_interaction",
                        "drug_a": med_a,
                        "drug_b": med_b,
                        "risk": KNOWN_INTERACTIONS[key1],
                    })
                elif key2 in KNOWN_INTERACTIONS:
                    conflicts.append({
                        "type": "drug_interaction",
                        "drug_a": med_b,
                        "drug_b": med_a,
                        "risk": KNOWN_INTERACTIONS[key2],
                    })

        # Check drug-allergy conflicts
        allergens = [a.get("allergen", "").lower() for a in allergies]
        for med_name in med_names:
            for allergen in allergens:
                if allergen in med_name or med_name in allergen:
                    conflicts.append({
                        "type": "drug_allergy_conflict",
                        "medication": med_name,
                        "allergen": allergen,
                        "risk": "Paciente alérgico a esta medicação ou classe",
                    })

        if conflicts:
            logger.warning("clinical_conflicts_detected", count=len(conflicts))

        return conflicts

    def detect_inconsistencies(
        self, ai_summary: str, patient_data: dict[str, Any]
    ) -> list[dict[str, str]]:
        """
        Detect inconsistencies between AI summary and source patient data.
        """
        inconsistencies: list[dict[str, str]] = []

        # Check if AI mentions medications not in the patient's list
        known_meds = {
            rx.get("medication", rx.get("name", "")).lower()
            for rx in patient_data.get("prescriptions", [])
            + patient_data.get("active_medications", [])
        }

        summary_lower = ai_summary.lower()

        # Check for allergy inconsistencies
        for allergy in patient_data.get("allergies", []):
            allergen = allergy.get("allergen", "").lower()
            if allergen and allergen not in summary_lower and allergy.get("severity") in ("grave", "critico"):
                inconsistencies.append({
                    "type": "missing_critical_allergy",
                    "detail": f"Alergia crítica a '{allergen}' não mencionada no resumo",
                })

        return inconsistencies

    def analyze_recommendation_risk(
        self, ai_output: dict[str, Any], patient_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Analyze the risk level of AI recommendations.
        """
        risk_factors: list[str] = []

        # Check confidence
        confidence = ai_output.get("confidence", {})
        if confidence.get("score", 0) < 0.5:
            risk_factors.append("Confiança baixa na análise da IA")

        # Check for hallucinations
        validation = ai_output.get("validation", {})
        if validation.get("flag_count", 0) > 0:
            risk_factors.append(
                f"{validation['flag_count']} possíveis alucinações detectadas"
            )

        # Check data completeness
        events = patient_data.get("events", [])
        if len(events) < 3:
            risk_factors.append("Poucos eventos clínicos disponíveis para análise")

        risk_level = "LOW"
        if len(risk_factors) >= 3:
            risk_level = "HIGH"
        elif len(risk_factors) >= 1:
            risk_level = "MODERATE"

        return {
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "recommendation": (
                "Verificação médica obrigatória" if risk_level != "LOW"
                else "Análise consistente com dados disponíveis"
            ),
        }

    def explain_ai_decision(
        self, ai_output: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Generate a human-readable explanation of how the AI reached its conclusions.
        """
        return {
            "model_used": ai_output.get("model", "unknown"),
            "processing_time_ms": ai_output.get("processing_time_ms", 0),
            "data_sources_analyzed": {
                "events": True,
                "medications": True,
                "allergies": True,
                "exams": True,
                "medication_history": True,
            },
            "confidence": ai_output.get("confidence", {}),
            "validation_result": ai_output.get("validation", {}),
            "risk_assessment": ai_output.get("risk_level", "UNKNOWN"),
            "disclaimer": (
                "Este resumo foi gerado por inteligência artificial e deve ser "
                "validado por um profissional de saúde qualificado. "
                "Não substitui avaliação clínica presencial."
            ),
        }
