"""SI3DC — Test: AI Pipeline and Governance."""

from __future__ import annotations

import pytest

from backend.ai.governance.confidence_scorer import classify_confidence
from backend.ai.governance.hallucination_detector import detect_hallucinations
from backend.ai.governance.ai_governance import AIGovernance
from backend.ai.pipelines.clinical_pipeline import ClinicalPipeline


# ── Confidence Scorer Tests ──────────────────────────────────────────


class TestConfidenceScorer:
    def test_high_confidence(self):
        result = classify_confidence(
            hallucination_count=0,
            data_completeness=1.0,
            response_length=500,
        )
        assert result["label"] == "HIGH"
        assert result["score"] >= 0.8

    def test_low_confidence_with_hallucinations(self):
        result = classify_confidence(
            hallucination_count=3,
            data_completeness=0.5,
            response_length=100,
        )
        assert result["label"] in ("LOW", "UNRELIABLE")
        assert result["score"] < 0.5

    def test_medium_confidence(self):
        result = classify_confidence(
            hallucination_count=1,
            data_completeness=0.8,
            response_length=400,
        )
        assert result["label"] in ("MEDIUM", "HIGH")

    def test_unreliable_with_no_data(self):
        result = classify_confidence(
            hallucination_count=4,
            data_completeness=0.0,
            response_length=50,
        )
        assert result["label"] == "UNRELIABLE"
        assert result["score"] == 0.0

    def test_score_always_between_0_and_1(self):
        result = classify_confidence(0, 1.0, 1000)
        assert 0.0 <= result["score"] <= 1.0

        result = classify_confidence(10, 0.0, 10)
        assert 0.0 <= result["score"] <= 1.0


# ── Hallucination Detector Tests ─────────────────────────────────────


class TestHallucinationDetector:
    def test_no_hallucinations_with_matching_data(self):
        ai_text = "Paciente em uso de Losartana 50mg diariamente."
        source_data = {
            "active_medications": [{"name": "losartana"}],
            "allergies": [],
            "events": [],
            "medication_history": [],
        }
        result = detect_hallucinations(ai_text, source_data)
        assert result["flag_count"] == 0

    def test_allergy_contradiction(self):
        ai_text = "Recomendo prescrever dipirona para controle da dor."
        source_data = {
            "active_medications": [],
            "allergies": [{"allergen": "dipirona"}],
            "events": [],
            "medication_history": [],
        }
        result = detect_hallucinations(ai_text, source_data)
        has_allergy_flag = any(
            f["type"] == "allergy_contradiction" for f in result["flags"]
        )
        assert has_allergy_flag

    def test_empty_text(self):
        result = detect_hallucinations("", {})
        assert result["flag_count"] == 0

    def test_icd_code_detection(self):
        ai_text = "Diagnóstico: CID Z99.9 - sem registro prévio."
        source_data = {
            "active_medications": [],
            "allergies": [],
            "events": [{"icd_code": "I10"}],
            "medication_history": [],
        }
        result = detect_hallucinations(ai_text, source_data)
        has_icd_flag = any(
            f["type"] == "unknown_icd_code" for f in result["flags"]
        )
        assert has_icd_flag


# ── AI Governance Tests ──────────────────────────────────────────────


class TestAIGovernance:
    def setup_method(self):
        self.governance = AIGovernance()

    def test_no_drug_conflicts(self):
        medications = [
            {"name": "Losartana"},
            {"name": "Metformina"},
        ]
        conflicts = self.governance.verify_clinical_conflicts(medications, [])
        # No direct interaction between these two
        drug_interactions = [c for c in conflicts if c["type"] == "drug_interaction"]
        assert len(drug_interactions) == 0

    def test_drug_allergy_conflict(self):
        medications = [{"name": "dipirona"}]
        allergies = [{"allergen": "dipirona"}]
        conflicts = self.governance.verify_clinical_conflicts(medications, allergies)
        assert len(conflicts) > 0
        assert conflicts[0]["type"] == "drug_allergy_conflict"

    def test_inconsistency_detection(self):
        ai_summary = "Paciente sem alergias conhecidas."
        patient_data = {
            "allergies": [
                {"allergen": "penicilina", "severity": "critico"},
            ],
            "prescriptions": [],
        }
        inconsistencies = self.governance.detect_inconsistencies(
            ai_summary, patient_data
        )
        assert len(inconsistencies) > 0

    def test_risk_analysis(self):
        ai_output = {
            "confidence": {"score": 0.9},
            "validation": {"flag_count": 0},
        }
        patient_data = {"events": [{"type": "consulta"}] * 5}
        result = self.governance.analyze_recommendation_risk(ai_output, patient_data)
        assert result["risk_level"] == "LOW"

    def test_explain_decision(self):
        ai_output = {
            "model": "medgemma-27b",
            "processing_time_ms": 1500,
            "confidence": {"score": 0.85, "label": "HIGH"},
            "validation": {"valid": True},
            "risk_level": "LOW",
        }
        explanation = self.governance.explain_ai_decision(ai_output)
        assert "disclaimer" in explanation
        assert explanation["model_used"] == "medgemma-27b"


# ── Clinical Pipeline Tests ─────────────────────────────────────────


class TestClinicalPipeline:
    def setup_method(self):
        self.pipeline = ClinicalPipeline()

    def test_ingest_data(self, sample_patient_history):
        result = self.pipeline.ingest_clinical_data(sample_patient_history)
        assert result["patient_id"] == "patient-001"
        assert result["events_count"] == 3
        assert result["allergies_count"] == 2

    def test_normalize_data(self, sample_patient_history):
        ingested = self.pipeline.ingest_clinical_data(sample_patient_history)
        normalized = self.pipeline.normalize_medical_data(ingested)
        assert "active_medications" in normalized
        assert "allergies" in normalized
        assert len(normalized["allergies"]) == 2
        assert normalized["allergies"][0]["severity_grade"] >= 3  # grave = 3

    def test_detect_risk_level_high(self, sample_patient_history):
        ingested = self.pipeline.ingest_clinical_data(sample_patient_history)
        normalized = self.pipeline.normalize_medical_data(ingested)
        risk = self.pipeline.detect_risk_level(normalized)
        # 2 critical allergies (2*2=4) + 1 severe event (1) = score 5 -> HIGH
        assert risk in ("HIGH", "CRITICAL")

    def test_detect_risk_level_low(self):
        data = {
            "allergies": [],
            "active_medications": [{"name": "vitamina D"}],
            "events": [{"severity": "leve"}],
        }
        risk = self.pipeline.detect_risk_level(data)
        assert risk == "LOW"

    def test_fallback_summary(self, sample_patient_history):
        summary = self.pipeline._generate_fallback_summary(sample_patient_history)
        assert "Resumo Clínico" in summary
        assert "Dipirona" in summary
        assert "Losartana" in summary

    def test_validate_empty_response(self, sample_patient_history):
        ingested = self.pipeline.ingest_clinical_data(sample_patient_history)
        normalized = self.pipeline.normalize_medical_data(ingested)
        result = self.pipeline.validate_ai_output(
            {"raw_response": ""}, normalized
        )
        assert result["valid"] is False
