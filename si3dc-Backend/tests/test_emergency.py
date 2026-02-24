"""SI3DC — Test: Emergency Mode."""

from __future__ import annotations

import pytest

from backend.ai.pipelines.clinical_pipeline import ClinicalPipeline


class TestEmergencyMode:
    def setup_method(self):
        self.pipeline = ClinicalPipeline()

    @pytest.mark.asyncio
    async def test_emergency_summary_contains_critical_allergies(
        self, sample_patient_history
    ):
        result = await self.pipeline.generate_emergency_summary(sample_patient_history)
        assert "critical_allergies" in result
        assert len(result["critical_allergies"]) > 0

    @pytest.mark.asyncio
    async def test_emergency_summary_contains_active_medications(
        self, sample_patient_history
    ):
        result = await self.pipeline.generate_emergency_summary(sample_patient_history)
        assert "active_medications" in result
        assert len(result["active_medications"]) > 0

    @pytest.mark.asyncio
    async def test_emergency_summary_contains_chronic_conditions(
        self, sample_patient_history
    ):
        result = await self.pipeline.generate_emergency_summary(sample_patient_history)
        assert "chronic_conditions" in result

    @pytest.mark.asyncio
    async def test_emergency_summary_includes_timestamp(
        self, sample_patient_history
    ):
        result = await self.pipeline.generate_emergency_summary(sample_patient_history)
        assert "generated_at" in result

    @pytest.mark.asyncio
    async def test_emergency_failsafe_mode(self, sample_patient_history):
        """Test that fail-safe mode works when AI endpoint is unavailable."""
        result = await self.pipeline.generate_emergency_summary(sample_patient_history)
        # Since AI endpoint is not running, fail-safe should kick in
        assert result is not None
        assert "critical_allergies" in result
        # Even in fail-safe, structured data should be present

    @pytest.mark.asyncio
    async def test_emergency_with_empty_history(self):
        empty_history = {
            "patient_id": "patient-empty",
            "events": [],
            "prescriptions": [],
            "allergies": [],
            "medication_history": [],
            "exams": [],
        }
        result = await self.pipeline.generate_emergency_summary(empty_history)
        assert result["patient_id"] == "patient-empty"
        assert result["critical_allergies"] == []
