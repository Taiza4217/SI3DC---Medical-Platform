"""SI3DC — Módulo de Configuração do Backend.

Configuração baseada em variáveis de ambiente usando Pydantic BaseSettings.
Todos os segredos e endpoints de infraestrutura são carregados do ambiente.

SEGURANÇA:
- Em produção, chaves padrão (JWT, ENCRYPTION) causam erro no boot.
- Usa .env para desenvolvimento, variáveis de ambiente para produção.
"""

from __future__ import annotations

from enum import Enum
from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings


class Environment(str, Enum):
    """Ambientes de execução suportados."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Configurações da aplicação carregadas de variáveis de ambiente.

    Em produção, as chaves JWT_SECRET_KEY e ENCRYPTION_KEY não podem
    permanecer com valores padrão — o boot falhará.
    """

    # ── Geral ────────────────────────────────────────────────────────
    APP_NAME: str = "SI3DC"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # ── Banco de Dados (PostgreSQL Assíncrono) ───────────────────────
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://si3dc:si3dc_secret@localhost:5432/si3dc",
        description="String de conexão PostgreSQL assíncrona",
    )
    DB_POOL_SIZE: int = 20  # Tamanho do pool de conexões
    DB_MAX_OVERFLOW: int = 10  # Conexões extras além do pool
    DB_ECHO: bool = False  # Log de SQL (desabilitar em produção)

    # ── Redis (Cache e Rate Limiting) ────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 300  # TTL padrão em segundos (5 minutos)

    # ── JWT / Autenticação ───────────────────────────────────────────
    JWT_SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_USE_OPENSSL_RAND_HEX_64"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # 30 minutos
    JWT_REFRESH_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 horas

    # ── Criptografia de Campos Sensíveis ─────────────────────────────
    ENCRYPTION_KEY: str = "CHANGE_ME_BASE64_32_BYTES_KEY"

    # ── IA / MedGemma ────────────────────────────────────────────────
    AI_ENDPOINT_URL: str = "http://localhost:8080/v1/generate"
    AI_MODEL_NAME: str = "medgemma-27b"
    AI_TIMEOUT_SECONDS: int = 30
    AI_MAX_RETRIES: int = 2
    AI_CONFIDENCE_THRESHOLD: float = 0.7  # Limiar mínimo de confiança

    # ── HAI-DEF — Modelos Fine-Tuned (Kaggle) ────────────────────────
    HAIDEF_ENDPOINT_URL: str = ""
    HAIDEF_MODEL_NAME: str = "hai-def-clinical"
    HAIDEF_API_KEY: str = ""
    HAIDEF_RADIOLOGY_URL: str = ""
    HAIDEF_RADIOLOGY_MODEL: str = "hai-def-radiology"
    HAIDEF_PATHOLOGY_URL: str = ""
    HAIDEF_PATHOLOGY_MODEL: str = "hai-def-pathology"

    # ── Integrações Externas ─────────────────────────────────────────
    SUS_API_BASE_URL: str = "https://apidadosabertos.saude.gov.br"
    FHIR_SERVER_URL: str = "http://localhost:8081/fhir"

    # ── Rate Limiting ────────────────────────────────────────────────
    RATE_LIMIT_REQUESTS: int = 100  # Requisições por janela
    RATE_LIMIT_WINDOW_SECONDS: int = 60  # Janela em segundos

    # ── Proxy (Rate Limiter compatível com proxy reverso) ────────────
    TRUSTED_PROXY_CIDRS: list[str] = []  # CIDRs de proxies confiáveis
    # Exemplo: ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]

    # ── Sentry (Monitoramento de Erros em Produção) ──────────────────
    SENTRY_DSN: str = ""  # Deixar vazio para desativar
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1  # 10% das transações

    # ── CORS ─────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "case_sensitive": True}

    # ── SEC-2: Validação de segurança em produção ────────────────────

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        """Impede o boot em produção com chaves padrão inseguras.

        SEGURANÇA CRÍTICA: Em produção e staging, as chaves criptográficas
        DEVEM ser substituídas por valores seguros gerados com:
            openssl rand -hex 64  (para JWT_SECRET_KEY)
            openssl rand -base64 32  (para ENCRYPTION_KEY)
        """
        if self.ENVIRONMENT in (Environment.PRODUCTION, Environment.STAGING):
            if "CHANGE_ME" in self.JWT_SECRET_KEY:
                raise ValueError(
                    "ERRO FATAL: JWT_SECRET_KEY não pode usar valor padrão em produção. "
                    "Gere uma chave segura com: openssl rand -hex 64"
                )
            if "CHANGE_ME" in self.ENCRYPTION_KEY:
                raise ValueError(
                    "ERRO FATAL: ENCRYPTION_KEY não pode usar valor padrão em produção. "
                    "Gere uma chave segura com: openssl rand -base64 32"
                )
        return self


@lru_cache
def get_settings() -> Settings:
    """Singleton cacheado das configurações da aplicação.

    Usa @lru_cache para evitar reler o .env a cada chamada.
    Em testes, usar get_settings.cache_clear() para resetar.
    """
    return Settings()
