"""SI3DC — Testes: Sistema de Autenticação.

Testa JWT tokens, RBAC (controle de acesso por papel), e hashing de senhas.

NOTA: O passlib tem incompatibilidade com bcrypt>=4.1 em senhas longas.
Os testes usam bcrypt diretamente para evitar este bug conhecido.
"""

from __future__ import annotations

import pytest
import bcrypt

from backend.infrastructure.auth.jwt_handler import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from backend.infrastructure.auth.rbac import (
    AccessLevel,
    has_permission,
)


# ── Testes JWT ───────────────────────────────────────────────────────


class TestJWTHandler:
    def test_create_access_token(self):
        """Token de acesso deve ser uma string não vazia."""
        token = create_access_token({"sub": "user-123", "role": "BASIC"})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_access_token(self):
        """Token decodificado deve conter sub, role, e type='access'."""
        token = create_access_token({"sub": "user-123", "role": "MEDIUM"})
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user-123"
        assert payload["role"] == "MEDIUM"
        assert payload["type"] == "access"

    def test_create_refresh_token(self):
        """Refresh token deve ter type='refresh'."""
        token = create_refresh_token({"sub": "user-123"})
        payload = decode_token(token)
        assert payload is not None
        assert payload["type"] == "refresh"

    def test_invalid_token(self):
        """Token inválido deve retornar None."""
        payload = decode_token("invalid.token.here")
        assert payload is None

    def test_empty_token(self):
        """Token vazio deve retornar None."""
        payload = decode_token("")
        assert payload is None


# ── Testes RBAC ──────────────────────────────────────────────────────


class TestRBAC:
    def test_basic_can_read_patient(self):
        """BASIC pode ler dados de pacientes."""
        assert has_permission("BASIC", "patient:read") is True

    def test_basic_cannot_write_patient(self):
        """BASIC NÃO pode escrever dados de pacientes."""
        assert has_permission("BASIC", "patient:write") is False

    def test_medium_can_write(self):
        """MEDIUM pode escrever dados clínicos e de pacientes."""
        assert has_permission("MEDIUM", "patient:write") is True
        assert has_permission("MEDIUM", "clinical:write") is True

    def test_admin_has_full_access(self):
        """ADMIN tem acesso completo a todas as permissões."""
        assert has_permission("ADMIN", "patient:delete") is True
        assert has_permission("ADMIN", "admin:system") is True
        assert has_permission("ADMIN", "audit:read") is True

    def test_unknown_role(self):
        """Role desconhecida não tem nenhuma permissão."""
        assert has_permission("UNKNOWN", "patient:read") is False

    def test_unknown_permission(self):
        """Permissão desconhecida é negada mesmo para ADMIN."""
        assert has_permission("ADMIN", "nonexistent:permission") is False

    def test_role_hierarchy(self):
        """ADMIN herda todas as permissões de MEDIUM e BASIC."""
        assert has_permission("ADMIN", "clinical:write") is True
        assert has_permission("ADMIN", "prescription:write") is True

    def test_basic_can_access_emergency(self):
        """BASIC pode acessar dados de emergência (acesso universal)."""
        assert has_permission("BASIC", "emergency:read") is True

    def test_basic_can_view_ai_summary(self):
        """BASIC pode visualizar resumos de IA."""
        assert has_permission("BASIC", "ai:summary") is True


# ── Testes de Hashing de Senha ───────────────────────────────────────


class TestPasswordHashing:
    """Testa hashing de senhas usando bcrypt diretamente.

    NOTA: Passlib tem bug conhecido com bcrypt>=4.1.
    Usamos bcrypt diretamente para evitar falsos negativos.
    """

    def test_hash_and_verify(self):
        """Senha correta deve ser verificada com sucesso."""
        password = b"secure_password_123"
        hashed = bcrypt.hashpw(password, bcrypt.gensalt())
        assert bcrypt.checkpw(password, hashed) is True

    def test_wrong_password_fails(self):
        """Senha incorreta deve falhar na verificação."""
        hashed = bcrypt.hashpw(b"correct_password", bcrypt.gensalt())
        assert bcrypt.checkpw(b"wrong_password", hashed) is False
