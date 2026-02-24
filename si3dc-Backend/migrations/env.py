"""SI3DC — Alembic Environment Configuration.

Configura o Alembic para auto-generate de migrations a partir dos modelos ORM.
Suporta execução síncrona (psycopg2) para operações de migração.

IMPORTANTE:
- A DATABASE_URL do ambiente usa asyncpg, mas o Alembic precisa de psycopg2.
- Este módulo converte automaticamente o driver da URL.
- Todos os modelos devem ser importados aqui para que o autogenerate funcione.
"""

from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# ── Importar TODOS os modelos para que o autogenerate detecte as tabelas ──
# Ordem: base primeiro, depois os modelos que dependem dele.
from backend.domain.models.base import Base  # noqa: F401
from backend.domain.models.institution import InstitutionORM  # noqa: F401
from backend.domain.models.professional import HealthProfessionalORM  # noqa: F401
from backend.domain.models.patient import PatientORM  # noqa: F401
from backend.domain.models.clinical import (  # noqa: F401
    MedicalRecordORM,
    ClinicalEventORM,
    MedicalDocumentORM,
    ExamORM,
    PrescriptionORM,
    AllergyORM,
    MedicationHistoryORM,
    AccessLogORM,
    AIClinicalSummaryORM,
    ConsentRecordORM,
)

# Refresh token blacklist (Task 3)
from backend.domain.models.refresh_token import RefreshTokenORM  # noqa: F401

config = context.config

# Interpretar o arquivo de logging .ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata alvo para autogenerate
target_metadata = Base.metadata


def _get_sync_url() -> str:
    """Obtém a DATABASE_URL e converte asyncpg → psycopg2 para Alembic sync.

    O Alembic roda em modo síncrono, então precisamos converter o driver
    de 'postgresql+asyncpg' para 'postgresql+psycopg2'.
    """
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise ValueError(
            "DATABASE_URL não definida. Defina a variável de ambiente antes de rodar migrations."
        )
    # Converter driver assíncrono para síncrono
    url = url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
    # Se for apenas 'postgresql://', manter (psycopg2 é o padrão)
    return url


def run_migrations_offline() -> None:
    """Executa migrations em modo 'offline' (gera SQL sem conexão).

    Útil para gerar scripts SQL para revisão antes de aplicar.
    """
    url = _get_sync_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Executa migrations em modo 'online' (conecta ao banco).

    Modo padrão de execução — conecta ao PostgreSQL e aplica as alterações.
    """
    # Sobrescrever a URL do alembic.ini com a variável de ambiente
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = _get_sync_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
