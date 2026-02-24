"""SI3DC — Script de Inicialização do Banco de Dados.

Executa as migrations do Alembic e opcionalmente cria dados iniciais (seed).

Uso:
    python scripts/init_db.py              # Aplica todas as migrations
    python scripts/init_db.py --seed       # Aplica migrations + seed inicial

REQUISITOS:
    - DATABASE_URL definida como variável de ambiente
    - PostgreSQL acessível
    - Alembic configurado em alembic.ini
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

# Carregar .env antes de qualquer coisa
# Isso garante que DATABASE_URL está disponível para o Alembic subprocess
_env_path = Path(__file__).resolve().parent.parent / ".env"
if _env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(_env_path, override=True)
    print(f"[OK] .env carregado de: {_env_path}")


def run_migrations() -> None:
    """Executa alembic upgrade head para aplicar todas as migrations."""
    print("[MIGRATE] Aplicando migrations do Alembic...")
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"[ERROR] Erro ao aplicar migrations:\n{result.stderr}")
        sys.exit(1)
    print(f"[OK] Migrations aplicadas com sucesso.\n{result.stdout}")


def run_seed() -> None:
    """Cria dados iniciais no banco (instituição padrão, admin, etc.).

    NOTA: Em produção, ajustar os dados de seed conforme necessário.
    Não criar usuários com senhas padrão em produção.
    """
    import asyncio

    async def _seed() -> None:
        # Importações locais para evitar problemas com o Alembic
        from backend.config import get_settings
        from backend.infrastructure.database.session import init_db, close_db, get_db
        from backend.domain.models.institution import InstitutionORM
        from backend.domain.models.professional import HealthProfessionalORM
        from passlib.context import CryptContext
        from sqlalchemy import select
        import uuid

        settings = get_settings()
        await init_db()

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        async for db in get_db():
            # Verificar se já existe seed
            result = await db.execute(
                select(InstitutionORM).where(InstitutionORM.cnes == "0000001")
            )
            if result.scalar_one_or_none():
                print("[SKIP] Seed ja existe, pulando...")
                await close_db()
                return

            # Criar instituição padrão
            inst_id = str(uuid.uuid4())
            institution = InstitutionORM(
                id=inst_id,
                cnes="0000001",
                name="Hospital SI3DC (Desenvolvimento)",
                type="hospital",
                city="São Paulo",
                state="SP",
                is_active=True,
            )
            db.add(institution)

            # Criar admin padrão (APENAS para desenvolvimento)
            if settings.ENVIRONMENT.value == "development":
                admin = HealthProfessionalORM(
                    id=str(uuid.uuid4()),
                    registration_type="ADMIN",
                    registration_number="ADMIN001",
                    registration_state="SP",
                    full_name="Administrador SI3DC",
                    email="admin@si3dc.dev",
                    password_hash=pwd_context.hash("admin12345"),
                    role="ADMIN",
                    institution_id=inst_id,
                    is_active=True,
                )
                db.add(admin)
                print("[USER] Admin criado: ADMIN / ADMIN001 / admin12345")

            # Commit é feito pelo context manager do get_db()
            break

        await close_db()
        print("[SEED] Seed concluido.")

    asyncio.run(_seed())


def main() -> None:
    parser = argparse.ArgumentParser(description="SI3DC — Inicialização do banco de dados")
    parser.add_argument("--seed", action="store_true", help="Criar dados iniciais (seed)")
    args = parser.parse_args()

    run_migrations()

    if args.seed:
        run_seed()

    print("\n[DONE] Banco de dados inicializado com sucesso!")


if __name__ == "__main__":
    main()
