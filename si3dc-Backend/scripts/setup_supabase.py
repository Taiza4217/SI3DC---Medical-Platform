"""Connect to Supabase via Pooler (IPv4) and create all tables + seed admin."""
import asyncio
import os
from pathlib import Path
from urllib.parse import urlparse, quote_plus

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)


def _build_safe_url(raw_url: str) -> str:
    """Rebuild DATABASE_URL with URL-encoded user/password for asyncpg."""
    parsed = urlparse(raw_url)
    user = quote_plus(parsed.username or "")
    password = quote_plus(parsed.password or "")
    host = parsed.hostname or ""
    port = parsed.port or 5432
    dbname = parsed.path.lstrip("/")
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{dbname}"


async def create_tables():
    from backend.domain.models.base import Base
    from backend.domain.models.institution import InstitutionORM  # noqa
    from backend.domain.models.professional import HealthProfessionalORM  # noqa
    from backend.domain.models.patient import PatientORM  # noqa
    from backend.domain.models.clinical import (  # noqa
        MedicalRecordORM, ClinicalEventORM, MedicalDocumentORM,
        ExamORM, PrescriptionORM, AllergyORM, MedicationHistoryORM,
        AccessLogORM, AIClinicalSummaryORM, ConsentRecordORM,
    )
    from backend.domain.models.refresh_token import RefreshTokenORM  # noqa
    from sqlalchemy.ext.asyncio import create_async_engine

    raw_url = os.getenv("DATABASE_URL", "")
    safe_url = _build_safe_url(raw_url)
    parsed = urlparse(raw_url)
    print(f"[INFO] Host: {parsed.hostname}:{parsed.port}")
    print(f"[INFO] User: {parsed.username}")

    engine = create_async_engine(safe_url, echo=False)
    try:
        async with engine.begin() as conn:
            print("[INFO] Connected! Creating tables...")
            await conn.run_sync(Base.metadata.create_all)
            print("[OK] All 14 tables created successfully!")
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        await engine.dispose()


async def seed_data():
    import uuid
    from passlib.context import CryptContext
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from backend.domain.models.institution import InstitutionORM
    from backend.domain.models.professional import HealthProfessionalORM

    raw_url = os.getenv("DATABASE_URL", "")
    safe_url = _build_safe_url(raw_url)
    engine = create_async_engine(safe_url)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    try:
        async with session_factory() as db:
            result = await db.execute(
                select(InstitutionORM).where(InstitutionORM.cnes == "0000001")
            )
            if result.scalar_one_or_none():
                print("[SKIP] Seed already exists.")
                return

            inst_id = str(uuid.uuid4())
            db.add(InstitutionORM(
                id=inst_id, cnes="0000001", name="Hospital SI3DC (Dev)",
                type="hospital", city="Sao Paulo", state="SP", is_active=True,
            ))
            db.add(HealthProfessionalORM(
                id=str(uuid.uuid4()), registration_type="ADMIN",
                registration_number="ADMIN001", registration_state="SP",
                full_name="Administrador SI3DC", email="admin@si3dc.dev",
                password_hash=pwd_context.hash("admin12345"),
                role="ADMIN", institution_id=inst_id, is_active=True,
            ))
            await db.commit()
            print("[OK] Admin criado: ADMIN / ADMIN001 / senha: admin12345")
    except Exception as e:
        print(f"[ERROR] Seed: {e}")
    finally:
        await engine.dispose()


async def main():
    await create_tables()
    await seed_data()
    print("\n[DONE] Banco inicializado com sucesso!")

if __name__ == "__main__":
    asyncio.run(main())
