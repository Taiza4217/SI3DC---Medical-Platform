"""SI3DC — Segurança: Criptografia AES-256 com Salt por Registro.

Criptografa campos sensíveis (CPF, notas clínicas) em repouso usando Fernet.
Implementa salt ÚNICO por registro para máxima segurança.

SEGURANÇA:
- Cada registro tem seu próprio salt aleatório de 16 bytes.
- O salt é armazenado junto com o dado criptografado (base64).
- PBKDF2-HMAC-SHA256 com 100.000 iterações para resistência a brute-force.
- Mesmo que dois registros tenham o mesmo texto, os ciphertexts serão diferentes.

FORMATO DE ARMAZENAMENTO (per-record salt):
    salt_b64:ciphertext_b64
    Onde salt_b64 é o salt em base64, separado por ':' do ciphertext.
"""

from __future__ import annotations

import base64
import hashlib
import os
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from backend.config import get_settings


# ══════════════════════════════════════════════════════════════════════
# CRIPTOGRAFIA COM SALT POR REGISTRO (RECOMENDADO PARA PRODUÇÃO)
# ══════════════════════════════════════════════════════════════════════


def _derive_key_with_salt(secret: str, salt: bytes) -> bytes:
    """Deriva uma chave Fernet usando PBKDF2 com salt fornecido.

    Args:
        secret: Chave mestra da configuração (ENCRYPTION_KEY).
        salt: Salt aleatório de 16 bytes, único por registro.

    Returns:
        Chave de 32 bytes codificada em base64 para Fernet.
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100_000,
    )
    return base64.urlsafe_b64encode(kdf.derive(secret.encode()))


def encrypt_field(plaintext: str) -> str:
    """Criptografa um campo sensível com salt único por registro.

    Gera um salt aleatório de 16 bytes para cada chamada, garantindo
    que o mesmo texto gere ciphertexts diferentes em registros distintos.

    Formato de saída: 'salt_b64:ciphertext_b64'

    Args:
        plaintext: Texto a ser criptografado (CPF, notas, etc.).

    Returns:
        String no formato 'salt_b64:ciphertext' para armazenamento.
    """
    settings = get_settings()

    # Gerar salt aleatório único para este registro
    salt = os.urandom(16)
    key = _derive_key_with_salt(settings.ENCRYPTION_KEY, salt)
    cipher = Fernet(key)

    ciphertext = cipher.encrypt(plaintext.encode()).decode()
    salt_b64 = base64.urlsafe_b64encode(salt).decode()

    # Formato: salt_b64:ciphertext
    return f"{salt_b64}:{ciphertext}"


def decrypt_field(stored_value: str) -> str:
    """Descriptografa um campo sensível de volta ao texto original.

    Detecta automaticamente o formato:
    - Novo formato (salt por registro): 'salt_b64:ciphertext'
    - Formato legado (salt global): apenas o ciphertext

    Args:
        stored_value: Valor armazenado no banco.

    Returns:
        Texto original descriptografado.

    Raises:
        ValueError: Se o valor não puder ser descriptografado.
    """
    settings = get_settings()

    if ":" in stored_value:
        # Novo formato com salt por registro
        salt_b64, ciphertext = stored_value.split(":", 1)
        salt = base64.urlsafe_b64decode(salt_b64.encode())
        key = _derive_key_with_salt(settings.ENCRYPTION_KEY, salt)
        cipher = Fernet(key)
        try:
            return cipher.decrypt(ciphertext.encode()).decode()
        except InvalidToken:
            raise ValueError("Falha ao descriptografar: chave ou dados corrompidos")
    else:
        # Formato legado (salt derivado da chave — backward compatibility)
        cipher = _get_legacy_cipher()
        try:
            return cipher.decrypt(stored_value.encode()).decode()
        except InvalidToken:
            raise ValueError("Falha ao descriptografar: chave ou dados corrompidos (formato legado)")


# ══════════════════════════════════════════════════════════════════════
# FUNÇÕES LEGADO (backward compatibility — remover após migração)
# ══════════════════════════════════════════════════════════════════════


def _derive_legacy_key(secret: str) -> bytes:
    """Deriva chave Fernet com salt fixo (formato legado).

    DEPRECIADO: Mantido apenas para descriptografar dados existentes.
    """
    salt = hashlib.sha256(f"si3dc:{secret}:salt".encode()).digest()[:16]
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100_000,
    )
    return base64.urlsafe_b64encode(kdf.derive(secret.encode()))


@lru_cache(maxsize=1)
def _get_legacy_cipher() -> Fernet:
    """Retorna cipher Fernet do formato legado (singleton cacheado)."""
    settings = get_settings()
    key = _derive_legacy_key(settings.ENCRYPTION_KEY)
    return Fernet(key)


# ══════════════════════════════════════════════════════════════════════
# FUNÇÕES DE MASCARAMENTO (LGPD)
# ══════════════════════════════════════════════════════════════════════


def mask_cpf(cpf: str) -> str:
    """Mascara um CPF para exibição segura: ***.***.***-XX.

    Exibe apenas os 2 últimos dígitos (verificadores).
    Exemplo: 123.456.789-09 → ***.***.***-09
    """
    digits = "".join(c for c in cpf if c.isdigit())
    if len(digits) < 11:
        return "***.***.***-**"
    return f"***.***.***-{digits[9]}{digits[10]}"


def anonymize_name(name: str) -> str:
    """Anonimiza o nome de um paciente para conformidade com LGPD.

    Mantém apenas a inicial do primeiro e último nome.
    Exemplo: "João da Silva Santos" → "J*** S***"
    """
    parts = name.split()
    if len(parts) <= 1:
        return "***"
    return f"{parts[0][0]}*** {parts[-1][0]}***"
