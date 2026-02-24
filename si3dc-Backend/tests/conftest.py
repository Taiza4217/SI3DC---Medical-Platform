"""SI3DC — Test: Shared Fixtures and Configuration."""

from __future__ import annotations

import pytest


@pytest.fixture
def sample_patient_data():
    """Sample patient data for testing."""
    return {
        "cpf": "52998224725",  # CPF válido (dígitos verificadores corretos)
        "full_name": "João Carlos da Silva",
        "birth_date": "1985-03-15",
        "gender": "masculino",
        "blood_type": "O+",
        "cns": "898000000012345",
        "phone": "(11) 99999-0000",
        "email": "joao@example.com",
        "city": "São Paulo",
        "state": "SP",
    }


@pytest.fixture
def sample_professional_data():
    """Sample health professional data for testing."""
    return {
        "registration_type": "CRM",
        "registration_number": "123456",
        "registration_state": "SP",
        "full_name": "Dra. Maria Souza",
        "specialty": "Cardiologia",
        "email": "maria@hospital.com",
        "password": "secure_password_123",
        "role": "MEDIUM",
        "institution_id": "inst-001",
    }


@pytest.fixture
def sample_patient_history():
    """Sample longitudinal patient history for AI pipeline testing."""
    return {
        "patient_id": "patient-001",
        "records_count": 3,
        "events": [
            {
                "type": "consulta",
                "date": "2024-01-15",
                "description": "Consulta cardiológica de rotina",
                "icd_code": "I10",
                "severity": "leve",
            },
            {
                "type": "internacao",
                "date": "2023-06-20",
                "description": "Internação por pneumonia",
                "icd_code": "J18.9",
                "severity": "moderado",
            },
            {
                "type": "cirurgia",
                "date": "2022-11-10",
                "description": "Apendicectomia laparoscópica",
                "icd_code": "K35",
                "severity": "grave",
            },
        ],
        "exams": [
            {
                "type": "Hemograma completo",
                "date": "2024-01-15",
                "result": "Normal",
                "status": "completed",
            },
            {
                "type": "Glicemia",
                "date": "2024-01-15",
                "result": "110 mg/dL",
                "status": "completed",
            },
        ],
        "prescriptions": [
            {
                "medication": "Losartana",
                "dosage": "50mg",
                "frequency": "1x ao dia",
                "is_active": True,
                "prescribed_at": "2024-01-15",
            },
            {
                "medication": "AAS",
                "dosage": "100mg",
                "frequency": "1x ao dia",
                "is_active": True,
                "prescribed_at": "2024-01-15",
            },
        ],
        "allergies": [
            {
                "allergen": "Dipirona",
                "type": "drug",
                "severity": "grave",
                "confirmed": True,
            },
            {
                "allergen": "Penicilina",
                "type": "drug",
                "severity": "critico",
                "confirmed": True,
            },
        ],
        "medication_history": [
            {
                "medication": "Amoxicilina",
                "dosage": "500mg",
                "start_date": "2023-06-20",
                "end_date": "2023-07-05",
            },
        ],
    }
