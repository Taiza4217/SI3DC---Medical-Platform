"""SI3DC — Testes: Modelo de Domínio do Paciente e Validação.

Testa criação, validação de CPF (incluindo dígitos verificadores),
campos opcionais e tipos sanguíneos.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.domain.models.patient import PatientCreate


# CPF válido para testes (dígitos verificadores corretos pelo módulo 11)
VALID_CPF = "52998224725"


class TestPatientCreate:
    def test_valid_patient(self, sample_patient_data):
        """Testa criação de paciente com CPF válido e todos os campos."""
        patient = PatientCreate(**sample_patient_data)
        assert patient.full_name == "João Carlos da Silva"
        assert patient.cpf == VALID_CPF

    def test_invalid_cpf_too_short(self):
        """CPF com menos de 11 dígitos deve ser rejeitado."""
        with pytest.raises(ValidationError):
            PatientCreate(
                cpf="123",
                full_name="Test",
                birth_date="1990-01-01",
                gender="masculino",
            )

    def test_invalid_cpf_all_same_digits(self):
        """CPF com todos os dígitos iguais (111...) deve ser rejeitado."""
        with pytest.raises(ValidationError):
            PatientCreate(
                cpf="11111111111",
                full_name="Test Patient",
                birth_date="1990-01-01",
                gender="masculino",
            )

    def test_invalid_cpf_wrong_check_digit(self):
        """CPF com dígito verificador errado deve ser rejeitado (BUG-2 fix)."""
        with pytest.raises(ValidationError):
            PatientCreate(
                cpf="12345678901",  # Dígito verificador inválido
                full_name="Test Patient",
                birth_date="1990-01-01",
                gender="masculino",
            )

    def test_name_too_short(self):
        """Nome com menos de 3 caracteres deve ser rejeitado."""
        with pytest.raises(ValidationError):
            PatientCreate(
                cpf=VALID_CPF,
                full_name="AB",
                birth_date="1990-01-01",
                gender="masculino",
            )

    def test_optional_fields_default_none(self):
        """Campos opcionais devem ser None por padrão."""
        patient = PatientCreate(
            cpf=VALID_CPF,
            full_name="Test Patient",
            birth_date="1990-01-01",
            gender="masculino",
        )
        assert patient.blood_type is None
        assert patient.phone is None
        assert patient.email is None

    def test_valid_blood_type(self, sample_patient_data):
        """Tipo sanguíneo válido (O+) deve ser aceito."""
        patient = PatientCreate(**sample_patient_data)
        assert patient.blood_type.value == "O+"

    def test_state_max_length(self):
        """Estado com mais de 2 caracteres deve ser rejeitado."""
        with pytest.raises(ValidationError):
            PatientCreate(
                cpf=VALID_CPF,
                full_name="Test Patient",
                birth_date="1990-01-01",
                gender="masculino",
                state="SPQ",  # max 2 chars
            )
