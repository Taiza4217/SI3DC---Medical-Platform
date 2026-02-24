"""SI3DC — Test: Security Module."""

from __future__ import annotations

import pytest

from backend.infrastructure.security.encryption import (
    decrypt_field,
    encrypt_field,
    mask_cpf,
    anonymize_name,
)


class TestEncryption:
    def test_encrypt_decrypt_roundtrip(self):
        plaintext = "123.456.789-01"
        encrypted = encrypt_field(plaintext)
        assert encrypted != plaintext
        decrypted = decrypt_field(encrypted)
        assert decrypted == plaintext

    def test_encrypted_is_different_from_plaintext(self):
        plaintext = "Dados sensíveis do paciente"
        encrypted = encrypt_field(plaintext)
        assert encrypted != plaintext

    def test_different_plaintexts_different_ciphertexts(self):
        enc1 = encrypt_field("data1")
        enc2 = encrypt_field("data2")
        assert enc1 != enc2


class TestCPFMasking:
    def test_mask_cpf(self):
        masked = mask_cpf("123.456.789-01")
        assert "123" not in masked
        assert "***" in masked

    def test_mask_cpf_digits_only(self):
        masked = mask_cpf("12345678901")
        assert "***" in masked

    def test_mask_short_cpf(self):
        masked = mask_cpf("123")
        assert masked == "***.***.***-**"


class TestNameAnonymization:
    def test_anonymize_full_name(self):
        anon = anonymize_name("João Carlos da Silva")
        assert "João" not in anon
        assert "Silva" not in anon
        assert "***" in anon

    def test_anonymize_single_name(self):
        anon = anonymize_name("João")
        assert anon == "***"

    def test_anonymize_two_names(self):
        anon = anonymize_name("Maria Santos")
        assert "Maria" not in anon
        assert "Santos" not in anon
