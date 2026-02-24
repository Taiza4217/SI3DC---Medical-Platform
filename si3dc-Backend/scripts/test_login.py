"""Quick test to capture login error traceback."""
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)

async def test_login():
    from backend.infrastructure.database.session import init_db, close_db, get_db, _safe_db_url
    from backend.domain.models.professional import HealthProfessionalORM
    from sqlalchemy import select

    print("[1] Initializing DB...")
    await init_db()

    print("[2] Querying for ADMIN001...")
    async for db in get_db():
        try:
            result = await db.execute(
                select(HealthProfessionalORM).where(
                    HealthProfessionalORM.registration_type == "ADMIN",
                    HealthProfessionalORM.registration_number == "ADMIN001",
                )
            )
            user = result.scalar_one_or_none()
            if user:
                print(f"[OK] Found user: {user.full_name} (id={user.id})")
                print(f"     Role: {user.role}, Institution: {user.institution_id}")
            else:
                print("[WARN] User ADMIN001 not found!")
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[ERROR] {e}")
        break

    await close_db()

if __name__ == "__main__":
    asyncio.run(test_login())
