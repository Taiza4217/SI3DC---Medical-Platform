"""SI3DC — Testes de Integração: Autenticação.

Testa os fluxos completos de autenticação com banco real:
- Login com credenciais válidas/inválidas
- Criação de usuários
- Refresh token flow (rotação, revogação)
- Logout (individual e global)
- Token blacklist (prevenção de reutilização)
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

# Importar fixtures de integração
from tests.conftest_integration import (  # noqa: F401
    setup_test_database,
    db_session,
    async_client,
    seeded_institution,
    seeded_professional,
)


# ═══════════════════════════════════════════════════════════════════════
# LOGIN TESTS
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient, seeded_professional: dict):
    """Login com credenciais válidas retorna tokens JWT."""
    response = await async_client.post("/auth/login", json={
        "registration_type": seeded_professional["registration_type"],
        "registration_number": seeded_professional["registration_number"],
        "password": seeded_professional["password"],
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["registration_number"] == seeded_professional["registration_number"]


@pytest.mark.asyncio
async def test_login_wrong_password(async_client: AsyncClient, seeded_professional: dict):
    """Login com senha incorreta retorna 401."""
    response = await async_client.post("/auth/login", json={
        "registration_type": seeded_professional["registration_type"],
        "registration_number": seeded_professional["registration_number"],
        "password": "WrongPassword123",
    })
    assert response.status_code == 401
    assert "inválidos" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_nonexistent_user(async_client: AsyncClient):
    """Login com usuário inexistente retorna 401 (timing-safe)."""
    response = await async_client.post("/auth/login", json={
        "registration_type": "CRM",
        "registration_number": "NONEXISTENT999",
        "password": "AnyPassword123",
    })
    assert response.status_code == 401


# ═══════════════════════════════════════════════════════════════════════
# REFRESH TOKEN TESTS
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_refresh_token_flow(async_client: AsyncClient, seeded_professional: dict):
    """Refresh token válido gera novo par de tokens."""
    # Login para obter tokens
    login_resp = await async_client.post("/auth/login", json={
        "registration_type": seeded_professional["registration_type"],
        "registration_number": seeded_professional["registration_number"],
        "password": seeded_professional["password"],
    })
    tokens = login_resp.json()

    # Usar refresh token para obter novos tokens
    refresh_resp = await async_client.post("/auth/refresh", json={
        "refresh_token": tokens["refresh_token"],
    })
    assert refresh_resp.status_code == 200
    new_tokens = refresh_resp.json()
    # Refresh tokens DEVEM ser diferentes (rotação)
    assert new_tokens["refresh_token"] != tokens["refresh_token"]


@pytest.mark.asyncio
async def test_refresh_token_reuse_blocked(async_client: AsyncClient, seeded_professional: dict):
    """Reutilização de refresh token (já rotacionado) é bloqueada.

    SEGURANÇA: Após um refresh, o token antigo é revogado.
    Tentar reutilizá-lo revoga TODOS os tokens do usuário (family rotation).
    """
    # Login
    login_resp = await async_client.post("/auth/login", json={
        "registration_type": seeded_professional["registration_type"],
        "registration_number": seeded_professional["registration_number"],
        "password": seeded_professional["password"],
    })
    old_refresh = login_resp.json()["refresh_token"]

    # Primeiro refresh (consome o token)
    await async_client.post("/auth/refresh", json={"refresh_token": old_refresh})

    # Segundo uso do MESMO token (deve falhar — family rotation)
    reuse_resp = await async_client.post("/auth/refresh", json={"refresh_token": old_refresh})
    assert reuse_resp.status_code == 401
    assert "reutilizado" in reuse_resp.json()["detail"].lower() or "revogado" in reuse_resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_refresh_with_invalid_token(async_client: AsyncClient):
    """Refresh com token inválido retorna 401."""
    response = await async_client.post("/auth/refresh", json={
        "refresh_token": "invalid.jwt.token",
    })
    assert response.status_code == 401


# ═══════════════════════════════════════════════════════════════════════
# LOGOUT TESTS
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_logout_success(async_client: AsyncClient, seeded_professional: dict):
    """Logout com token válido revoga o refresh token."""
    # Login
    login_resp = await async_client.post("/auth/login", json={
        "registration_type": seeded_professional["registration_type"],
        "registration_number": seeded_professional["registration_number"],
        "password": seeded_professional["password"],
    })
    tokens = login_resp.json()

    # Logout
    logout_resp = await async_client.post(
        "/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert logout_resp.status_code == 200
    assert logout_resp.json()["revoked"] is True

    # Tentar usar o refresh token revogado
    refresh_resp = await async_client.post("/auth/refresh", json={
        "refresh_token": tokens["refresh_token"],
    })
    assert refresh_resp.status_code == 401


@pytest.mark.asyncio
async def test_logout_all_devices(async_client: AsyncClient, seeded_professional: dict):
    """Logout-all revoga todos os refresh tokens do usuário."""
    # Login duas vezes (simular dois dispositivos)
    login_resp1 = await async_client.post("/auth/login", json={
        "registration_type": seeded_professional["registration_type"],
        "registration_number": seeded_professional["registration_number"],
        "password": seeded_professional["password"],
    })
    tokens1 = login_resp1.json()

    login_resp2 = await async_client.post("/auth/login", json={
        "registration_type": seeded_professional["registration_type"],
        "registration_number": seeded_professional["registration_number"],
        "password": seeded_professional["password"],
    })
    tokens2 = login_resp2.json()

    # Logout all
    logout_all_resp = await async_client.post(
        "/auth/logout-all",
        headers={"Authorization": f"Bearer {tokens1['access_token']}"},
    )
    assert logout_all_resp.status_code == 200

    # Ambos refresh tokens estão revogados
    assert (await async_client.post("/auth/refresh", json={"refresh_token": tokens1["refresh_token"]})).status_code == 401
    assert (await async_client.post("/auth/refresh", json={"refresh_token": tokens2["refresh_token"]})).status_code == 401


# ═══════════════════════════════════════════════════════════════════════
# AUTH PROFILE TESTS
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_get_me_authenticated(async_client: AsyncClient, seeded_professional: dict):
    """GET /auth/me com token válido retorna perfil do profissional."""
    login_resp = await async_client.post("/auth/login", json={
        "registration_type": seeded_professional["registration_type"],
        "registration_number": seeded_professional["registration_number"],
        "password": seeded_professional["password"],
    })
    token = login_resp.json()["access_token"]

    me_resp = await async_client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200
    data = me_resp.json()
    assert data["id"] == seeded_professional["id"]
    assert data["registration_number"] == seeded_professional["registration_number"]


@pytest.mark.asyncio
async def test_get_me_unauthenticated(async_client: AsyncClient):
    """GET /auth/me sem token retorna 401."""
    response = await async_client.get("/auth/me")
    assert response.status_code == 401
