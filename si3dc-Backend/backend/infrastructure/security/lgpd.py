"""SI3DC — Módulo de Conformidade LGPD.

Gerenciamento de consentimento, anonimização de dados, e exportação
para atender aos direitos do titular previstos na LGPD.

DECISÕES DE ARQUITETURA:
- Usa .is_(True) e .is_(None) para comparações SQLAlchemy corretas.
- Anonimização é irreversível — remove dados pessoais permanentemente.
- Exportação retorna todos os dados pessoais para portabilidade.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.models.clinical import ConsentRecordORM
from backend.domain.models.patient import PatientORM
from backend.infrastructure.security.encryption import anonymize_name, mask_cpf

logger = structlog.get_logger(__name__)


async def record_consent(
    db: AsyncSession,
    patient_id: str,
    consent_type: str,
    granted: bool,
    purpose: str,
    ip_address: str | None = None,
) -> ConsentRecordORM:
    """Registra uma decisão de consentimento do paciente (concessão ou revogação).

    O registro inclui timestamp, IP, e propósito para rastreabilidade LGPD.
    """
    consent = ConsentRecordORM(
        patient_id=patient_id,
        consent_type=consent_type,
        granted=granted,
        granted_at=datetime.now(timezone.utc),
        purpose=purpose,
        ip_address=ip_address,
    )
    db.add(consent)
    logger.info("consent_recorded", patient_id=patient_id, type=consent_type, granted=granted)
    return consent


async def revoke_consent(
    db: AsyncSession,
    patient_id: str,
    consent_type: str,
) -> bool:
    """Revoga um consentimento previamente concedido.

    Busca o consentimento ativo (granted=True, revoked_at=None)
    e marca como revogado com timestamp.

    SEC-5 fix: usa .is_(True) e .is_(None) em vez de == True e == None.
    """
    result = await db.execute(
        select(ConsentRecordORM)
        .where(ConsentRecordORM.patient_id == patient_id)
        .where(ConsentRecordORM.consent_type == consent_type)
        .where(ConsentRecordORM.granted.is_(True))
        .where(ConsentRecordORM.revoked_at.is_(None))
    )
    consent = result.scalar_one_or_none()
    if consent:
        consent.revoked_at = datetime.now(timezone.utc)
        consent.granted = False
        logger.info("consent_revoked", patient_id=patient_id, type=consent_type)
        return True
    return False


async def verify_consent(
    db: AsyncSession,
    patient_id: str,
    consent_type: str,
) -> bool:
    """Verifica se o paciente possui consentimento ativo para o tipo dado.

    Retorna True se houver um consentimento concedido e não revogado.
    """
    result = await db.execute(
        select(ConsentRecordORM)
        .where(ConsentRecordORM.patient_id == patient_id)
        .where(ConsentRecordORM.consent_type == consent_type)
        .where(ConsentRecordORM.granted.is_(True))
        .where(ConsentRecordORM.revoked_at.is_(None))
    )
    return result.scalar_one_or_none() is not None


async def anonymize_patient_data(
    db: AsyncSession,
    patient_id: str,
) -> dict[str, Any]:
    """Anonimiza dados pessoais do paciente — direito ao esquecimento (LGPD Art. 18).

    ATENÇÃO: Esta operação é IRREVERSÍVEL.
    Remove: nome completo, CPF, email, telefone, endereço, contato de emergência.
    """
    result = await db.execute(
        select(PatientORM).where(PatientORM.id == patient_id)
    )
    patient = result.scalar_one_or_none()
    if not patient:
        return {"status": "patient_not_found"}

    # Anonimizar dados pessoais identificáveis
    patient.full_name = anonymize_name(patient.full_name)
    patient.cpf = mask_cpf(patient.cpf)
    patient.email = None
    patient.phone = None
    patient.address = None
    patient.emergency_contact_name = None
    patient.emergency_contact_phone = None
    patient.is_active = False

    logger.info("patient_data_anonymized", patient_id=patient_id)
    return {"status": "anonymized", "patient_id": patient_id}


async def export_patient_data(
    db: AsyncSession,
    patient_id: str,
) -> dict[str, Any]:
    """Exporta todos os dados pessoais do paciente — portabilidade (LGPD Art. 18).

    Retorna dados em formato estruturado para transferência a outro controlador.
    """
    result = await db.execute(
        select(PatientORM).where(PatientORM.id == patient_id)
    )
    patient = result.scalar_one_or_none()
    if not patient:
        return {"status": "patient_not_found"}

    return {
        "status": "exported",
        "patient": {
            "full_name": patient.full_name,
            "cpf": patient.cpf,
            "birth_date": str(patient.birth_date),
            "gender": patient.gender,
            "blood_type": patient.blood_type,
            "cns": patient.cns,
            "phone": patient.phone,
            "email": patient.email,
            "address": patient.address,
            "city": patient.city,
            "state": patient.state,
        },
    }
