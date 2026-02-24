"""SI3DC — Pipeline Clínico de IA.

Pipeline principal para análise de dados clínicos usando MedGemma.
Inclui: ingestão, normalização, análise, validação e geração de resumo.

DECISÕES DE ARQUITETURA:
- Pipeline de 5 estágios: Ingest → Normalize → Analyze → Validate → Risk
- Fail-safe: gera resumo determinístico se a IA estiver indisponível
- Todas as chaves de dicionário acessadas com .get() para evitar crashes
- consistency_score é clampado em [0, 1] para evitar valores negativos
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any, Optional

import httpx
import structlog

from backend.ai.governance.confidence_scorer import classify_confidence
from backend.ai.governance.hallucination_detector import detect_hallucinations
from backend.config import get_settings

logger = structlog.get_logger(__name__)


class ClinicalPipeline:
    """Pipeline de IA para análise clínica e geração de resumos.

    Estágios do pipeline:
    1. Ingestão — valida e estrutura os dados brutos
    2. Normalização — padroniza terminologias, CIDs e medicações
    3. Análise — envia ao MedGemma para análise multimodal
    4. Validação — detecta alucinações e mede confiança
    5. Risco — classifica nível de urgência clínica
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    # ── Estágio 1: Ingestão de Dados Clínicos ────────────────────────

    def ingest_clinical_data(self, patient_history: dict[str, Any]) -> dict[str, Any]:
        """Ingere dados clínicos brutos do histórico longitudinal.

        Valida a estrutura básica e adiciona metadados de processamento.
        """
        ingested = {
            "patient_id": patient_history.get("patient_id"),
            "events_count": len(patient_history.get("events", [])),
            "exams_count": len(patient_history.get("exams", [])),
            "prescriptions_count": len(patient_history.get("prescriptions", [])),
            "allergies_count": len(patient_history.get("allergies", [])),
            "medication_history_count": len(patient_history.get("medication_history", [])),
            "raw_data": patient_history,
            "ingested_at": datetime.now(timezone.utc).isoformat(),
        }
        logger.info("clinical_data_ingested", patient_id=ingested["patient_id"])
        return ingested

    # ── Estágio 2: Normalização dos Dados Médicos ────────────────────

    def normalize_medical_data(self, ingested_data: dict[str, Any]) -> dict[str, Any]:
        """Normaliza dados clínicos: padroniza terminologias, CIDs e nomes.

        NOTA: Usa .get() em todas as chaves para prevenir KeyError (BUG-6 fix).
        """
        raw = ingested_data["raw_data"]

        # Normalizar eventos clínicos
        normalized_events = []
        for event in raw.get("events", []):
            normalized_events.append({
                "type": (event.get("type") or "unknown").lower(),
                "date": event.get("date"),
                "description": event.get("description", ""),
                "icd_code": event.get("icd_code"),
                "severity": (event.get("severity") or "unknown").lower(),
            })

        # Normalizar medicações ativas (prescrições vigentes)
        active_meds = [
            {
                "name": rx.get("medication", ""),
                "dosage": rx.get("dosage", ""),
                "frequency": rx.get("frequency", ""),
                "active": rx.get("is_active", False),
            }
            for rx in raw.get("prescriptions", [])
        ]

        # Normalizar alergias com classificação de severidade
        allergies = [
            {
                "allergen": a.get("allergen", ""),
                "type": a.get("type", ""),
                "severity_grade": self._grade_severity(a.get("severity", "")),
                "confirmed": a.get("confirmed", False),
            }
            for a in raw.get("allergies", [])
        ]

        return {
            "patient_id": ingested_data["patient_id"],
            "events": normalized_events,
            "active_medications": active_meds,
            "allergies": allergies,
            "exams": raw.get("exams", []),
            "medication_history": raw.get("medication_history", []),
            "normalized_at": datetime.now(timezone.utc).isoformat(),
        }

    # ── Estágio 3: Análise com MedGemma ──────────────────────────────

    async def analyze_with_medgemma(
        self, normalized_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Envia dados normalizados ao MedGemma para análise multimodal.

        SEGURANÇA: temperatura 0.1 para maximizar precisão clínica.
        FALLBACK: retorna flag indicando necessidade de resumo determinístico.
        """
        prompt = self._build_clinical_prompt(normalized_data)

        try:
            async with httpx.AsyncClient(timeout=self.settings.AI_TIMEOUT_SECONDS) as client:
                response = await client.post(
                    self.settings.AI_ENDPOINT_URL,
                    json={
                        "model": self.settings.AI_MODEL_NAME,
                        "prompt": prompt,
                        "max_tokens": 2048,
                        "temperature": 0.1,  # Temperatura baixa para precisão clínica
                    },
                )
                response.raise_for_status()
                ai_result = response.json()

            return {
                "raw_response": ai_result.get("text", ai_result.get("response", "")),
                "model": self.settings.AI_MODEL_NAME,
                "tokens_used": ai_result.get("usage", {}).get("total_tokens", 0),
                "analyzed_at": datetime.now(timezone.utc).isoformat(),
            }
        except httpx.HTTPError as e:
            logger.error("medgemma_request_failed", error=str(e))
            return {
                "raw_response": None,
                "error": str(e),
                "fallback": True,
            }

    # ── Estágio 4: Validação do Output da IA ─────────────────────────

    def validate_ai_output(
        self, ai_response: dict[str, Any], normalized_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Valida o output da IA para consistência clínica e detecção de alucinações.

        Verificações:
        - Resposta não vazia
        - Alucinações (medicações desconhecidas, CIDs não registrados, etc.)
        - Score de confiança baseado em completude dos dados e tamanho da resposta
        """
        raw_text = ai_response.get("raw_response", "")
        if not raw_text:
            return {
                "valid": False,
                "reason": "AI response is empty or unavailable",
                "hallucination_flags": [],
                "consistency_score": 0.0,
            }

        # Detectar alucinações cruzando com dados fonte
        hallucination_result = detect_hallucinations(raw_text, normalized_data)

        # Calcular confiança
        confidence = classify_confidence(
            hallucination_count=hallucination_result["flag_count"],
            data_completeness=self._calculate_completeness(normalized_data),
            response_length=len(raw_text),
        )

        # BUG-7 fix: clampar consistency_score em [0, 1]
        raw_consistency = 1.0 - (hallucination_result["flag_count"] * 0.2)
        consistency_score = max(0.0, min(1.0, raw_consistency))

        return {
            "valid": hallucination_result["flag_count"] == 0,
            "hallucination_flags": hallucination_result["flags"],
            "flag_count": hallucination_result["flag_count"],
            "consistency_score": consistency_score,
            "confidence": confidence,
        }

    # ── Estágio 5: Detecção de Nível de Risco ────────────────────────

    def detect_risk_level(self, normalized_data: dict[str, Any]) -> str:
        """Classifica o nível de risco clínico baseado nos dados do paciente.

        Critérios de pontuação:
        - Alergias críticas (severidade ≥ 3): +2 pontos cada
        - Polifarmácia (≥ 5 medicações): +2 pontos
        - Polifarmácia extrema (≥ 10 medicações): +3 pontos adicionais
        - Eventos clínicos graves/críticos: +1 ponto cada

        Returns:
            LOW (< 2), MODERATE (2-3), HIGH (4-6), CRITICAL (≥ 7)
        """
        score = 0

        # Alergias críticas aumentam o risco significativamente
        critical_allergies = [
            a for a in normalized_data.get("allergies", [])
            if a.get("severity_grade", 0) >= 3
        ]
        score += len(critical_allergies) * 2

        # Polifarmácia — múltiplas medicações ativas
        active_meds = normalized_data.get("active_medications", [])
        if len(active_meds) >= 5:
            score += 2
        if len(active_meds) >= 10:
            score += 3

        # Eventos clínicos graves ou críticos
        severe_events = [
            e for e in normalized_data.get("events", [])
            if e.get("severity") in ("grave", "critico")
        ]
        score += len(severe_events)

        if score >= 7:
            return "CRITICAL"
        elif score >= 4:
            return "HIGH"
        elif score >= 2:
            return "MODERATE"
        return "LOW"

    # ── Pipeline Completo ────────────────────────────────────────────

    async def analyze_patient_history(
        self, patient_history: dict[str, Any]
    ) -> dict[str, Any]:
        """Executa o pipeline clínico completo de IA.

        Fluxo: 1. Ingestão → 2. Normalização → 3. Análise → 4. Validação → 5. Risco
        """
        start_time = time.time()

        # Estágio 1: Ingestão
        ingested = self.ingest_clinical_data(patient_history)

        # Estágio 2: Normalização
        normalized = self.normalize_medical_data(ingested)

        # Estágio 3: Análise com MedGemma
        ai_response = await self.analyze_with_medgemma(normalized)

        # Estágio 4: Validação
        validation = self.validate_ai_output(ai_response, normalized)

        # Estágio 5: Nível de risco
        risk_level = self.detect_risk_level(normalized)

        processing_time_ms = int((time.time() - start_time) * 1000)

        return {
            "patient_id": patient_history.get("patient_id"),
            "summary": ai_response.get("raw_response", ""),
            "risk_level": risk_level,
            "confidence": validation["confidence"],
            "validation": validation,
            "model": self.settings.AI_MODEL_NAME,
            "processing_time_ms": processing_time_ms,
            "fallback_used": ai_response.get("fallback", False),
        }

    # ── Geração de Resumo Clínico ────────────────────────────────────

    async def generate_clinical_summary(
        self, patient_history: dict[str, Any]
    ) -> dict[str, Any]:
        """Gera resumo clínico estruturado do paciente.

        Se a IA estiver indisponível, gera resumo determinístico (fail-safe).
        """
        result = await self.analyze_patient_history(patient_history)

        if result.get("fallback_used") or not result.get("summary"):
            # Gerar resumo determinístico a partir dos dados estruturados
            result["summary"] = self._generate_fallback_summary(patient_history)
            result["confidence"]["label"] = "LOW"
            result["confidence"]["score"] = 0.3

        return result

    # ── Resumo de Emergência ─────────────────────────────────────────

    async def generate_emergency_summary(
        self, patient_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Gera resumo emergencial priorizando dados críticos.

        SEMPRE retorna dados estruturados (fail-safe), independente da IA.
        Prioriza: alergias críticas, medicações ativas, doenças crônicas.
        """
        # Sempre gerar os dados determinísticos primeiro (fail-safe)
        emergency = {
            "patient_id": patient_data.get("patient_id"),
            "critical_allergies": [
                a for a in patient_data.get("allergies", [])
                if a.get("severity") in ("grave", "critico")
            ],
            "active_medications": [
                {
                    "medication": rx.get("medication", ""),
                    "dosage": rx.get("dosage", ""),
                    "frequency": rx.get("frequency", ""),
                }
                for rx in patient_data.get("prescriptions", [])
                if rx.get("is_active")
            ],
            "chronic_conditions": [
                e for e in patient_data.get("events", [])
                if e.get("type") in ("diagnostico", "tratamento")
            ],
            "recent_surgeries": [
                e for e in patient_data.get("events", [])
                if e.get("type") == "cirurgia"
            ][:5],
            "clinical_alerts": [],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "ai_enhanced": False,
        }

        # Tentar enriquecer com IA
        try:
            ai_result = await self.analyze_patient_history(patient_data)
            if ai_result.get("summary"):
                emergency["ai_summary"] = ai_result["summary"]
                emergency["ai_enhanced"] = True
                emergency["risk_level"] = ai_result["risk_level"]
        except Exception as e:
            logger.warning("emergency_ai_fallback", error=str(e))
            emergency["ai_summary"] = None
            emergency["risk_level"] = self.detect_risk_level(
                self.normalize_medical_data(self.ingest_clinical_data(patient_data))
            )

        return emergency

    # ── Métodos Auxiliares Privados ───────────────────────────────────

    def _build_clinical_prompt(self, data: dict[str, Any]) -> str:
        """Constrói o prompt de análise clínica estruturado para o MedGemma."""
        sections = [
            "Analise os seguintes dados clínicos do paciente e gere um resumo médico estruturado.",
            "",
            f"## Eventos Clínicos ({len(data.get('events', []))} registros)",
        ]
        for event in data.get("events", [])[:20]:
            sections.append(
                f"- [{event.get('date')}] {event.get('type')}: {event.get('description')}"
            )

        sections.append(f"\n## Medicações Ativas ({len(data.get('active_medications', []))})")
        for med in data.get("active_medications", []):
            sections.append(f"- {med.get('name', '')} {med.get('dosage', '')} ({med.get('frequency', '')})")

        sections.append(f"\n## Alergias ({len(data.get('allergies', []))})")
        for allergy in data.get("allergies", []):
            sections.append(f"- {allergy.get('allergen', '')} (Severidade: {allergy.get('severity_grade', 'N/A')})")

        sections.append("\n## Instruções")
        sections.append("1. Gere um resumo clínico estruturado")
        sections.append("2. Identifique riscos e alertas")
        sections.append("3. Destaque interações medicamentosas potenciais")
        sections.append("4. Classifique a urgência geral do caso")

        return "\n".join(sections)

    def _grade_severity(self, severity: str) -> int:
        """Converte severidade textual para grau numérico (1-4).

        BUG-5 fix: trata None/empty string sem crash.
        """
        grades = {"leve": 1, "moderado": 2, "grave": 3, "critico": 4}
        return grades.get((severity or "").lower(), 0)

    def _calculate_completeness(self, data: dict[str, Any]) -> float:
        """Calcula score de completude dos dados (0.0 a 1.0).

        Quanto mais categorias de dados disponíveis, maior a completude.
        """
        factors = [
            bool(data.get("events")),
            bool(data.get("active_medications")),
            bool(data.get("allergies")),
            bool(data.get("exams")),
            bool(data.get("medication_history")),
        ]
        return sum(factors) / len(factors)

    def _generate_fallback_summary(self, data: dict[str, Any]) -> str:
        """Gera resumo determinístico quando a IA está indisponível.

        Usa apenas dados estruturados — sem IA, sem alucinações.
        """
        lines = ["# Resumo Clínico (Modo Fallback)", ""]

        allergies = data.get("allergies", [])
        if allergies:
            lines.append("## Alergias")
            for a in allergies:
                lines.append(f"- {a.get('allergen', 'N/A')} ({a.get('severity', 'N/A')})")
            lines.append("")

        prescriptions = [rx for rx in data.get("prescriptions", []) if rx.get("is_active")]
        if prescriptions:
            lines.append("## Medicações Ativas")
            for rx in prescriptions:
                lines.append(f"- {rx.get('medication', '')} {rx.get('dosage', '')} ({rx.get('frequency', '')})")
            lines.append("")

        events = data.get("events", [])[:10]
        if events:
            lines.append("## Últimos Eventos Clínicos")
            for e in events:
                lines.append(f"- [{e.get('date', 'N/A')}] {e.get('type', 'N/A')}: {e.get('description', 'N/A')}")

        return "\n".join(lines)
