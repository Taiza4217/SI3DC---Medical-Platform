"""SI3DC — Test: Clinical Models and Validation."""

from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from backend.domain.models.clinical import (
    AllergyCreate,
    ClinicalEventCreate,
    ExamCreate,
    PrescriptionCreate,
)


class TestClinicalEventCreate:
    def test_valid_event(self):
        event = ClinicalEventCreate(
            record_id="rec-001",
            event_type="consulta",
            event_date=datetime(2024, 1, 15, 10, 0),
            description="Consulta de rotina com cardiologista",
        )
        assert event.event_type.value == "consulta"

    def test_description_too_short(self):
        with pytest.raises(ValidationError):
            ClinicalEventCreate(
                record_id="rec-001",
                event_type="consulta",
                event_date=datetime(2024, 1, 15),
                description="abc",  # min 5 chars
            )


class TestExamCreate:
    def test_valid_exam(self):
        exam = ExamCreate(
            patient_id="patient-001",
            exam_type="Hemograma",
            exam_date="2024-01-15",
            result="Normal",
            result_value=12.5,
            result_unit="g/dL",
        )
        assert exam.exam_type == "Hemograma"
        assert exam.result_value == 12.5


class TestPrescriptionCreate:
    def test_valid_prescription(self):
        rx = PrescriptionCreate(
            patient_id="patient-001",
            medication="Losartana",
            dosage="50mg",
            frequency="1x ao dia",
            route="oral",
            duration_days=30,
        )
        assert rx.medication == "Losartana"
        assert rx.duration_days == 30

    def test_invalid_duration(self):
        with pytest.raises(ValidationError):
            PrescriptionCreate(
                patient_id="patient-001",
                medication="Losartana",
                dosage="50mg",
                frequency="1x ao dia",
                route="oral",
                duration_days=0,  # must be > 0
            )


class TestAllergyCreate:
    def test_valid_allergy(self):
        allergy = AllergyCreate(
            patient_id="patient-001",
            allergen="Dipirona",
            allergen_type="drug",
            severity="grave",
        )
        assert allergy.severity.value == "grave"

    def test_allergen_too_short(self):
        with pytest.raises(ValidationError):
            AllergyCreate(
                patient_id="patient-001",
                allergen="X",  # min 2 chars
                allergen_type="drug",
                severity="leve",
            )
