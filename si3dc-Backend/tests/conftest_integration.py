"""SI3DC — Fixtures de Integração para Testes com Banco Real.

Configura um banco de dados de teste isolado usando SQLite assíncrono
para testes de integração rápidos e determinísticos.

DECISÕES:
- Usamos SQLite com shared cache (file::memory:?cache=shared) para
  permitir que múltiplas conexões vejam as mesmas tabelas.
- Cada teste roda com setup/teardown de tabelas (isolamento total).
- O app de teste sobrescreve get_db() para usar a sessão de teste.
"""

from __future__ import annotations

import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from passlib.context import CryptContext
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.domain.models.base import Base

# Importar todos os modelos para garantir que o metadata está completo
from backend.domain.models.institution import InstitutionORM  # noqa: F401
from backend.domain.models.professional import HealthProfessionalORM  # noqa: F401
from backend.domain.models.patient import PatientORM  # noqa: F401
from backend.domain.models.clinical import (  # noqa: F401
    MedicalRecordORM, ClinicalEventORM, MedicalDocumentORM,
    ExamORM, PrescriptionORM, AllergyORM, MedicationHistoryORM,
    AccessLogORM, AIClinicalSummaryORM, ConsentRecordORM,
)
from backend.domain.models.refresh_token import RefreshTokenORM  # noqa: F401

# ── Engine e Session de Teste ────────────────────────────────────────

# SQLite com shared cache para que múltiplas sessões vejam as mesmas tabelas
_TEST_DB_URL = "sqlite+aiosqlite:///file::memory:?cache=shared&uri=true"

_test_engine = create_async_engine(
    _TEST_DB_URL,
    echo=False,
    # Necessário para SQLite com async: impedir que o pool feche conexões
    # (que apagaria o banco in-memory)
    pool_size=1,
    max_overflow=0,
    pool_pre_ping=False,
)

# SQLite precisa que foreign keys sejam habilitados a cada conexão
@event.listens_for(_test_engine.sync_engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


_test_session_factory = async_sessionmaker(
    bind=_test_engine, class_=AsyncSession, expire_on_commit=False
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@pytest_asyncio.fixture(autouse=True)
async def setup_test_database():
    """Cria todas as tabelas antes de cada teste e limpa depois."""
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Sessão de banco de teste com rollback automático."""
    async with _test_session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Cliente HTTP assíncrono para testes de integração."""
    from backend.infrastructure.database.session import get_db
    from backend.main import app

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def seeded_institution(db_session: AsyncSession) -> str:
    """Cria uma instituição de teste e retorna seu ID."""
    inst_id = str(uuid.uuid4())
    institution = InstitutionORM(
        id=inst_id,
        cnes="TEST001",
        name="Hospital de Teste",
        type="hospital",
        city="Sao Paulo",
        state="SP",
        is_active=True,
    )
    db_session.add(institution)
    await db_session.flush()
    return inst_id


@pytest_asyncio.fixture
async def seeded_professional(db_session: AsyncSession, seeded_institution: str) -> dict:
    """Cria um profissional de teste e retorna seus dados."""
    prof_id = str(uuid.uuid4())
    password = "TestPassword123"

    professional = HealthProfessionalORM(
        id=prof_id,
        registration_type="CRM",
        registration_number="TEST123",
        registration_state="SP",
        full_name="Dr. Teste Silva",
        specialty="Cardiologia",
        email="teste@hospital.test",
        password_hash=pwd_context.hash(password),
        role="MEDIUM",
        institution_id=seeded_institution,
        is_active=True,
    )
    db_session.add(professional)
    await db_session.flush()

    return {
        "id": prof_id,
        "registration_type": "CRM",
        "registration_number": "TEST123",
        "password": password,
        "institution_id": seeded_institution,
    }
