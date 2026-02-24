"""SI3DC — Serviço de Pacientes.

Lógica de negócio para gerenciamento de pacientes e orquestração de resumos IA.

DECISÕES DE ARQUITETURA:
- Usa cache Redis com TTL de 5 minutos para histórico longitudinal.
- O cache é invalidado quando novos dados clínicos são criados.
- A busca de pacientes sanitiza a entrada para prevenir SQL injection via LIKE.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any, Optional

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.domain.models.clinical import (
    AccessLogORM,
    AIClinicalSummaryORM,
    AllergyORM,
    ClinicalEventORM,
    ExamORM,
    MedicalRecordORM,
    MedicationHistoryORM,
    PrescriptionORM,
)
from backend.domain.models.patient import PatientCreate, PatientORM, PatientResponse
from backend.infrastructure.auth.audit import log_patient_access
from backend.infrastructure.database.redis_client import cache_delete, cache_get, cache_set

logger = structlog.get_logger(__name__)


class PatientService:
    """Camada de serviço para operações de pacientes.

    Gerencia CRUD de pacientes, busca, e construção de histórico longitudinal.
    Utiliza cache Redis para otimizar consultas frequentes ao histórico.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_patient(self, data: PatientCreate, created_by: str) -> PatientORM:
        """Registra um novo paciente no sistema.

        O CPF já foi validado (com dígito verificador) pelo schema Pydantic.
        """
        patient = PatientORM(
            cpf=data.cpf,
            full_name=data.full_name,
            social_name=data.social_name,
            birth_date=data.birth_date,
            gender=data.gender.value,
            blood_type=data.blood_type.value if data.blood_type else None,
            cns=data.cns,
            phone=data.phone,
            email=data.email,
            address=data.address,
            city=data.city,
            state=data.state,
            zip_code=data.zip_code,
            emergency_contact_name=data.emergency_contact_name,
            emergency_contact_phone=data.emergency_contact_phone,
        )
        self.db.add(patient)
        await self.db.flush()

        logger.info("patient_created", patient_id=patient.id, created_by=created_by)
        return patient

    async def get_patient(self, patient_id: str) -> Optional[PatientORM]:
        """Busca um paciente pelo seu ID (UUID)."""
        result = await self.db.execute(
            select(PatientORM).where(PatientORM.id == patient_id)
        )
        return result.scalar_one_or_none()

    async def get_patient_by_cpf(self, cpf: str) -> Optional[PatientORM]:
        """Busca um paciente pelo CPF (campo único)."""
        result = await self.db.execute(
            select(PatientORM).where(PatientORM.cpf == cpf)
        )
        return result.scalar_one_or_none()

    async def search_patients(
        self, query: str, offset: int = 0, limit: int = 20
    ) -> list[PatientORM]:
        """Busca pacientes por nome ou CPF com proteção contra SQL injection.

        SEGURANÇA: Os caracteres wildcard do SQL LIKE (%, _, \\) são removidos
        da entrada para prevenir injeção de wildcards que poderiam causar
        buscas excessivamente amplas ou exposição de dados.
        """
        # Sanitizar entrada — remover caracteres especiais do LIKE (BUG-4 fix)
        safe_query = re.sub(r"[%_\\]", "", query)

        if not safe_query:
            return []

        result = await self.db.execute(
            select(PatientORM)
            .where(
                PatientORM.full_name.ilike(f"%{safe_query}%")
                | PatientORM.cpf.like(f"%{safe_query}%")
            )
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_longitudinal_history(
        self, patient_id: str
    ) -> dict[str, Any]:
        """Constrói o histórico clínico longitudinal completo do paciente.

        Dados incluídos:
        - Prontuários e eventos clínicos
        - Exames com resultados
        - Prescrições (ativas e históricas)
        - Alergias com severidade
        - Histórico medicamentoso

        PERFORMANCE: Resultado é cacheado no Redis por 5 minutos.
        O cache é invalidado por invalidate_patient_cache() quando
        novos dados clínicos são criados.
        """
        # Tentar cache primeiro
        cache_key = f"history:{patient_id}"
        cached = await cache_get(cache_key)
        if cached:
            return json.loads(cached)

        # Prontuários do paciente
        records_result = await self.db.execute(
            select(MedicalRecordORM)
            .where(MedicalRecordORM.patient_id == patient_id)
            .order_by(MedicalRecordORM.created_at.desc())
        )
        records = records_result.scalars().all()

        # Eventos clínicos (vinculados aos prontuários)
        record_ids = [r.id for r in records]
        events_result = await self.db.execute(
            select(ClinicalEventORM)
            .where(ClinicalEventORM.record_id.in_(record_ids))
            .order_by(ClinicalEventORM.event_date.desc())
        ) if record_ids else None
        events = events_result.scalars().all() if events_result else []

        # Exames
        exams_result = await self.db.execute(
            select(ExamORM)
            .where(ExamORM.patient_id == patient_id)
            .order_by(ExamORM.exam_date.desc())
        )
        exams = exams_result.scalars().all()

        # Prescrições
        rx_result = await self.db.execute(
            select(PrescriptionORM)
            .where(PrescriptionORM.patient_id == patient_id)
            .order_by(PrescriptionORM.prescribed_at.desc())
        )
        prescriptions = rx_result.scalars().all()

        # Alergias
        allergies_result = await self.db.execute(
            select(AllergyORM)
            .where(AllergyORM.patient_id == patient_id)
        )
        allergies = allergies_result.scalars().all()

        # Histórico medicamentoso
        medhist_result = await self.db.execute(
            select(MedicationHistoryORM)
            .where(MedicationHistoryORM.patient_id == patient_id)
            .order_by(MedicationHistoryORM.start_date.desc())
        )
        med_history = medhist_result.scalars().all()

        # Montar o dicionário de histórico completo
        history = {
            "patient_id": patient_id,
            "records_count": len(records),
            "events": [
                {
                    "type": e.event_type,
                    "date": str(e.event_date),
                    "description": e.description,
                    "icd_code": e.icd_code,
                    "severity": e.severity,
                }
                for e in events
            ],
            "exams": [
                {
                    "type": ex.exam_type,
                    "date": str(ex.exam_date),
                    "result": ex.result,
                    "status": ex.status,
                }
                for ex in exams
            ],
            "prescriptions": [
                {
                    "medication": rx.medication,
                    "dosage": rx.dosage,
                    "frequency": rx.frequency,
                    "is_active": rx.is_active,
                    "prescribed_at": str(rx.prescribed_at),
                }
                for rx in prescriptions
            ],
            "allergies": [
                {
                    "allergen": a.allergen,
                    "type": a.allergen_type,
                    "severity": a.severity,
                    "confirmed": a.confirmed,
                }
                for a in allergies
            ],
            "medication_history": [
                {
                    "medication": m.medication,
                    "dosage": m.dosage,
                    "start_date": str(m.start_date),
                    "end_date": str(m.end_date) if m.end_date else None,
                }
                for m in med_history
            ],
        }

        # Cachear por 5 minutos
        await cache_set(cache_key, json.dumps(history), ttl=300)
        return history

    @staticmethod
    async def invalidate_patient_cache(patient_id: str) -> None:
        """Invalida o cache do histórico longitudinal de um paciente.

        Deve ser chamado sempre que novos dados clínicos são criados
        (evento, exame, prescrição, alergia, etc.) para garantir
        que o próximo acesso ao histórico retorne dados atualizados.
        """
        await cache_delete(f"history:{patient_id}")
        logger.info("patient_cache_invalidated", patient_id=patient_id)
