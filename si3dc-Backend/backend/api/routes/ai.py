"""SI3DC — AI Routes.

API endpoints for AI-powered clinical analysis, multi-model management,
and medical image analysis.
"""

from __future__ import annotations

from typing import Any, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.ai.models.model_adapter import ModelOrchestrator, ModelType
from backend.ai.pipelines.clinical_pipeline import ClinicalPipeline
from backend.ai.governance.ai_governance import AIGovernance
from backend.domain.models.professional import HealthProfessionalORM
from backend.infrastructure.auth.oauth2 import get_current_user
from backend.infrastructure.database.session import get_db
from backend.services.patient_service import PatientService

logger = structlog.get_logger(__name__)
router = APIRouter()

# ── Singletons ───────────────────────────────────────────────────────
_orchestrator: Optional[ModelOrchestrator] = None


def get_orchestrator() -> ModelOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = ModelOrchestrator()
    return _orchestrator


# ── Schemas ──────────────────────────────────────────────────────────

class AnalysisRequest(BaseModel):
    patient_id: str
    model_type: Optional[str] = None  # e.g., "medgemma-27b", "hai-def-clinical"
    use_ensemble: bool = False


class ImageAnalysisRequest(BaseModel):
    patient_id: str
    clinical_context: str = ""
    body_region: str = ""
    modality: str = ""  # e.g., "X-Ray", "CT", "MRI"
    model_type: Optional[str] = None


# ── Endpoints ────────────────────────────────────────────────────────

@router.get("/models", summary="Listar modelos de IA disponíveis")
async def list_models(
    current_user: HealthProfessionalORM = Depends(get_current_user),
) -> dict[str, Any]:
    """Lista todos os modelos de IA registrados e suas capacidades."""
    orchestrator = get_orchestrator()
    return {
        "models": orchestrator.list_available_models(),
        "count": len(orchestrator.adapters),
    }


@router.get("/models/health", summary="Verificar saúde dos modelos de IA")
async def models_health(
    current_user: HealthProfessionalORM = Depends(get_current_user),
) -> dict[str, Any]:
    """Verifica a disponibilidade de todos os modelos de IA."""
    orchestrator = get_orchestrator()
    return await orchestrator.check_health()


@router.post("/analyze", summary="Análise clínica com IA")
async def analyze_patient(
    request: AnalysisRequest,
    current_user: HealthProfessionalORM = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Executa análise clínica completa do paciente usando o pipeline de IA.

    - **model_type**: Modelo a ser usado (padrão: MedGemma-27B)
    - **use_ensemble**: Se True, roda análise em múltiplos modelos para cross-validação
    """
    service = PatientService(db)
    history = await service.get_longitudinal_history(request.patient_id)

    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Histórico do paciente não encontrado",
        )

    pipeline = ClinicalPipeline()
    orchestrator = get_orchestrator()
    governance = AIGovernance()

    # Normalize data for prompt building
    ingested = pipeline.ingest_clinical_data(history)
    normalized = pipeline.normalize_medical_data(ingested)

    if request.use_ensemble:
        # Ensemble analysis across all available models
        prompt = list(orchestrator.adapters.values())[0].build_clinical_prompt(normalized)
        ensemble_result = await orchestrator.ensemble_analysis(prompt)

        return {
            "patient_id": request.patient_id,
            "analysis_type": "ensemble",
            "ensemble": ensemble_result,
            "risk_level": pipeline.detect_risk_level(normalized),
            "conflicts": governance.verify_clinical_conflicts(
                normalized.get("active_medications", []),
                normalized.get("allergies", []),
            ),
        }

    # Single model analysis
    model_type = None
    if request.model_type:
        try:
            model_type = ModelType(request.model_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Modelo '{request.model_type}' não suportado. Use GET /ai/models para ver os disponíveis.",
            )

    adapter = orchestrator.get_adapter(model_type or ModelType.MEDGEMMA_27B)
    prompt = adapter.build_clinical_prompt(normalized)
    response = await orchestrator.generate(prompt, model_type=model_type)

    # Validate and govern the AI output
    validation = pipeline.validate_ai_output(
        {"raw_response": response.text}, normalized
    )
    risk = pipeline.detect_risk_level(normalized)
    conflicts = governance.verify_clinical_conflicts(
        normalized.get("active_medications", []),
        normalized.get("allergies", []),
    )

    return {
        "patient_id": request.patient_id,
        "summary": response.text,
        "model": response.model_name,
        "model_type": response.model_type.value,
        "risk_level": risk,
        "confidence": validation.get("confidence", {}),
        "validation": validation,
        "conflicts": conflicts,
        "processing_time_ms": response.processing_time_ms,
        "explanation": governance.explain_ai_decision({
            "model": response.model_name,
            "processing_time_ms": response.processing_time_ms,
            "confidence": validation.get("confidence", {}),
            "validation": validation,
            "risk_level": risk,
        }),
    }


@router.post("/analyze-image", summary="Análise de imagem médica com IA")
async def analyze_medical_image(
    file: UploadFile = File(...),
    patient_id: str = Form(...),
    clinical_context: str = Form(""),
    body_region: str = Form(""),
    modality: str = Form(""),
    model_type: Optional[str] = Form(None),
    current_user: HealthProfessionalORM = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Analisa uma imagem médica (raio-x, CT, MRI, dermatologia, patologia)
    usando modelos de IA multimodais (MedGemma ou HAI-DEF especializado).
    """
    orchestrator = get_orchestrator()
    image_data = await file.read()

    prompt = (
        f"Analise esta imagem médica.\n"
        f"Contexto clínico: {clinical_context or 'Não informado'}\n"
        f"Região corporal: {body_region or 'Não especificada'}\n"
        f"Modalidade: {modality or 'Não especificada'}\n"
        f"Gere um laudo estruturado com achados, impressão diagnóstica e recomendações."
    )

    mt = None
    if model_type:
        try:
            mt = ModelType(model_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Modelo '{model_type}' não suportado.",
            )

    response = await orchestrator.analyze_image(
        image_data, prompt,
        model_type=mt,
        mime_type=file.content_type or "image/png",
    )

    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Nenhum modelo multimodal disponível: {response.error}",
        )

    return {
        "patient_id": patient_id,
        "analysis": response.text,
        "model": response.model_name,
        "model_type": response.model_type.value,
        "processing_time_ms": response.processing_time_ms,
        "metadata": response.metadata,
        "disclaimer": (
            "Este laudo foi gerado por IA e deve ser validado por um "
            "profissional de saúde qualificado."
        ),
    }


@router.post("/clinical-summary", summary="Gerar resumo clínico com IA")
async def generate_clinical_summary(
    request: AnalysisRequest,
    current_user: HealthProfessionalORM = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Gera resumo clínico estruturado do paciente usando o pipeline completo.
    Inclui fail-safe (resumo determinístico) se a IA estiver indisponível.
    """
    service = PatientService(db)
    history = await service.get_longitudinal_history(request.patient_id)

    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Histórico do paciente não encontrado",
        )

    pipeline = ClinicalPipeline()
    result = await pipeline.generate_clinical_summary(history)

    governance = AIGovernance()
    ingested = pipeline.ingest_clinical_data(history)
    normalized = pipeline.normalize_medical_data(ingested)
    conflicts = governance.verify_clinical_conflicts(
        normalized.get("active_medications", []),
        normalized.get("allergies", []),
    )

    result["conflicts"] = conflicts
    return result
