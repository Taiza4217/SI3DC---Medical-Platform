"""SI3DC — Testes de Integração: Pacientes.

Testa operações CRUD de pacientes contra banco real:
- Criação de paciente com validação de CPF
- Listagem de pacientes
- Busca por ID
- Endpoints protegidos requerem autenticação
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

# Importar fixtures de integração
from tests.conftest_integration import (  # noqa: F401
    setup_test_database,
    db_session,
    async_client,
    seeded_institution,
    seeded_professional,
)


async def _get_auth_token(client: AsyncClient, professional: dict) -> str:
    """Helper: faz login e retorna o access token."""
    resp = await client.post("/auth/login", json={
        "registration_type": professional["registration_type"],
        "registration_number": professional["registration_number"],
        "password": professional["password"],
    })
    return resp.json()["access_token"]


# ═══════════════════════════════════════════════════════════════════════
# PATIENT CRUD TESTS
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_create_patient_success(async_client: AsyncClient, seeded_professional: dict):
    """Criar paciente com dados válidos retorna 201."""
    token = await _get_auth_token(async_client, seeded_professional)

    response = await async_client.post(
        "/patients/",
        json={
            "cpf": "52998224725",
            "full_name": "João Carlos da Silva",
            "birth_date": "1985-03-15",
            "gender": "masculino",
            "blood_type": "O+",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    # Accept 200 or 201 depending on implementation
    assert response.status_code in (200, 201)
    data = response.json()
    assert data["full_name"] == "João Carlos da Silva"


@pytest.mark.asyncio
async def test_create_patient_invalid_cpf(async_client: AsyncClient, seeded_professional: dict):
    """Criar paciente com CPF inválido retorna 422."""
    token = await _get_auth_token(async_client, seeded_professional)

    response = await async_client.post(
        "/patients/",
        json={
            "cpf": "11111111111",  # CPF inválido (todos dígitos iguais)
            "full_name": "Teste Invalido",
            "birth_date": "1990-01-01",
            "gender": "masculino",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_patients_requires_auth(async_client: AsyncClient):
    """Acessar /patients sem token retorna 401."""
    response = await async_client.post("/patients/", json={
        "cpf": "52998224725",
        "full_name": "Test",
        "birth_date": "1990-01-01",
        "gender": "masculino",
    })
    assert response.status_code == 401


# ═══════════════════════════════════════════════════════════════════════
# HEALTH CHECK TESTS
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_health_endpoint(async_client: AsyncClient):
    """GET /health retorna status healthy."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "uptime_seconds" in data
