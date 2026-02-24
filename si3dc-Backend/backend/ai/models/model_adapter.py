"""SI3DC — Multi-Model AI Adapter.

Supports MedGemma, HAI-DEF fine-tuned models, and other clinical AI models.
Designed for the Kaggle competition with flexible model switching.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

import httpx
import structlog

from backend.config import get_settings

logger = structlog.get_logger(__name__)


class ModelType(str, Enum):
    """Supported AI model types."""
    MEDGEMMA_4B = "medgemma-4b"
    MEDGEMMA_27B = "medgemma-27b"
    HAI_DEF_CLINICAL = "hai-def-clinical"
    HAI_DEF_RADIOLOGY = "hai-def-radiology"
    HAI_DEF_PATHOLOGY = "hai-def-pathology"
    HAI_DEF_DERMATOLOGY = "hai-def-dermatology"
    HAI_DEF_OPHTHO = "hai-def-ophthalmology"
    CUSTOM_FINETUNED = "custom-finetuned"


@dataclass
class ModelConfig:
    """Configuration for a specific AI model."""
    model_type: ModelType
    endpoint_url: str
    model_name: str
    max_tokens: int = 2048
    temperature: float = 0.1
    timeout_seconds: int = 30
    api_key: Optional[str] = None
    headers: dict[str, str] = field(default_factory=dict)
    supports_multimodal: bool = False
    supports_medical_images: bool = False
    fine_tuned_task: Optional[str] = None  # e.g., "clinical_summary", "radiology_report"


@dataclass
class ModelResponse:
    """Standardized response from any AI model."""
    text: str
    model_type: ModelType
    model_name: str
    tokens_used: int
    processing_time_ms: int
    raw_response: dict[str, Any]
    success: bool
    error: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseModelAdapter(ABC):
    """Abstract base adapter for AI model integration."""

    def __init__(self, config: ModelConfig):
        self.config = config

    @abstractmethod
    async def generate(self, prompt: str, **kwargs: Any) -> ModelResponse:
        """Generate a response from the model."""
        ...

    @abstractmethod
    async def analyze_image(
        self, image_data: bytes, prompt: str, **kwargs: Any
    ) -> ModelResponse:
        """Analyze a medical image (if supported)."""
        ...

    @abstractmethod
    def build_clinical_prompt(self, data: dict[str, Any]) -> str:
        """Build a model-specific clinical prompt."""
        ...

    async def health_check(self) -> bool:
        """Check if the model endpoint is healthy."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.config.endpoint_url}/health")
                return resp.status_code == 200
        except Exception:
            return False


class MedGemmaAdapter(BaseModelAdapter):
    """Adapter for Google MedGemma models (4B and 27B)."""

    async def generate(self, prompt: str, **kwargs: Any) -> ModelResponse:
        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                payload = {
                    "model": self.config.model_name,
                    "prompt": prompt,
                    "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                    "temperature": kwargs.get("temperature", self.config.temperature),
                }

                # Support Vertex AI / Gemini API format
                if self.config.api_key:
                    headers = {
                        "Authorization": f"Bearer {self.config.api_key}",
                        "Content-Type": "application/json",
                        **self.config.headers,
                    }
                else:
                    headers = {"Content-Type": "application/json", **self.config.headers}

                response = await client.post(
                    self.config.endpoint_url,
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                result = response.json()

            elapsed_ms = int((time.time() - start) * 1000)

            # Handle different response formats (Vertex AI, local, HuggingFace)
            text = (
                result.get("text")
                or result.get("response")
                or result.get("generated_text")
                or result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            )

            return ModelResponse(
                text=text,
                model_type=self.config.model_type,
                model_name=self.config.model_name,
                tokens_used=result.get("usage", {}).get("total_tokens", 0),
                processing_time_ms=elapsed_ms,
                raw_response=result,
                success=True,
            )
        except Exception as e:
            elapsed_ms = int((time.time() - start) * 1000)
            logger.error("medgemma_error", error=str(e), model=self.config.model_name)
            return ModelResponse(
                text="",
                model_type=self.config.model_type,
                model_name=self.config.model_name,
                tokens_used=0,
                processing_time_ms=elapsed_ms,
                raw_response={},
                success=False,
                error=str(e),
            )

    async def analyze_image(
        self, image_data: bytes, prompt: str, **kwargs: Any
    ) -> ModelResponse:
        """MedGemma multimodal analysis for medical images."""
        import base64

        start = time.time()
        try:
            encoded_image = base64.b64encode(image_data).decode("utf-8")
            mime_type = kwargs.get("mime_type", "image/png")

            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                payload = {
                    "model": self.config.model_name,
                    "contents": [
                        {
                            "parts": [
                                {"text": prompt},
                                {
                                    "inline_data": {
                                        "mime_type": mime_type,
                                        "data": encoded_image,
                                    }
                                },
                            ]
                        }
                    ],
                    "generation_config": {
                        "max_output_tokens": self.config.max_tokens,
                        "temperature": self.config.temperature,
                    },
                }

                headers = {"Content-Type": "application/json", **self.config.headers}
                if self.config.api_key:
                    headers["Authorization"] = f"Bearer {self.config.api_key}"

                response = await client.post(
                    self.config.endpoint_url,
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                result = response.json()

            elapsed_ms = int((time.time() - start) * 1000)
            text = (
                result.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )

            return ModelResponse(
                text=text,
                model_type=self.config.model_type,
                model_name=self.config.model_name,
                tokens_used=result.get("usageMetadata", {}).get("totalTokenCount", 0),
                processing_time_ms=elapsed_ms,
                raw_response=result,
                success=True,
                metadata={"multimodal": True, "image_analyzed": True},
            )
        except Exception as e:
            elapsed_ms = int((time.time() - start) * 1000)
            logger.error("medgemma_image_error", error=str(e))
            return ModelResponse(
                text="",
                model_type=self.config.model_type,
                model_name=self.config.model_name,
                tokens_used=0,
                processing_time_ms=elapsed_ms,
                raw_response={},
                success=False,
                error=str(e),
            )

    def build_clinical_prompt(self, data: dict[str, Any]) -> str:
        """Build a MedGemma-optimized clinical prompt."""
        sections = [
            "<clinical_context>",
            "You are a medical AI assistant. Analyze the following patient data",
            "and generate a structured clinical summary in Portuguese (PT-BR).",
            "",
        ]

        events = data.get("events", [])
        if events:
            sections.append(f"## Eventos Clínicos ({len(events)})")
            for e in events[:20]:
                sections.append(f"- [{e.get('date', 'N/A')}] {e.get('type', 'N/A')}: {e.get('description', '')}")

        meds = data.get("active_medications", [])
        if meds:
            sections.append(f"\n## Medicações Ativas ({len(meds)})")
            for m in meds:
                sections.append(f"- {m.get('name', '')} {m.get('dosage', '')} ({m.get('frequency', '')})")

        allergies = data.get("allergies", [])
        if allergies:
            sections.append(f"\n## Alergias ({len(allergies)})")
            for a in allergies:
                sections.append(f"- {a.get('allergen', '')} (Severidade: {a.get('severity_grade', 'N/A')})")

        sections.append("\n</clinical_context>")
        sections.append("\n<instructions>")
        sections.append("1. Gere um resumo clínico estruturado")
        sections.append("2. Identifique riscos e alertas clínicos")
        sections.append("3. Destaque interações medicamentosas potenciais")
        sections.append("4. Classifique a urgência geral: BAIXA, MODERADA, ALTA, CRÍTICA")
        sections.append("5. Inclua recomendações de acompanhamento")
        sections.append("</instructions>")

        return "\n".join(sections)


class HAIDEFAdapter(BaseModelAdapter):
    """
    Adapter for HAI-DEF (Healthcare AI Definition Framework) fine-tuned models.

    Supports multiple HAI-DEF specialized models:
    - Clinical summary generation
    - Radiology report analysis
    - Pathology slide analysis
    - Dermatology image classification
    - Ophthalmology retinal analysis
    """

    async def generate(self, prompt: str, **kwargs: Any) -> ModelResponse:
        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                # HAI-DEF models use HuggingFace Inference API compatible format
                payload = {
                    "inputs": prompt,
                    "parameters": {
                        "max_new_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                        "temperature": kwargs.get("temperature", self.config.temperature),
                        "do_sample": True,
                        "return_full_text": False,
                    },
                }

                headers = {"Content-Type": "application/json", **self.config.headers}
                if self.config.api_key:
                    headers["Authorization"] = f"Bearer {self.config.api_key}"

                response = await client.post(
                    self.config.endpoint_url,
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                result = response.json()

            elapsed_ms = int((time.time() - start) * 1000)

            # Handle HuggingFace / custom endpoint response formats
            if isinstance(result, list) and len(result) > 0:
                text = result[0].get("generated_text", "")
            elif isinstance(result, dict):
                text = result.get("generated_text", result.get("text", result.get("response", "")))
            else:
                text = str(result)

            return ModelResponse(
                text=text,
                model_type=self.config.model_type,
                model_name=self.config.model_name,
                tokens_used=0,  # HF API doesn't always return token count
                processing_time_ms=elapsed_ms,
                raw_response=result if isinstance(result, dict) else {"result": result},
                success=True,
                metadata={"fine_tuned_task": self.config.fine_tuned_task},
            )
        except Exception as e:
            elapsed_ms = int((time.time() - start) * 1000)
            logger.error("haidef_error", error=str(e), model=self.config.model_name)
            return ModelResponse(
                text="",
                model_type=self.config.model_type,
                model_name=self.config.model_name,
                tokens_used=0,
                processing_time_ms=elapsed_ms,
                raw_response={},
                success=False,
                error=str(e),
            )

    async def analyze_image(
        self, image_data: bytes, prompt: str, **kwargs: Any
    ) -> ModelResponse:
        """HAI-DEF image analysis (radiology, pathology, dermatology, etc.)."""
        import base64

        start = time.time()
        try:
            encoded_image = base64.b64encode(image_data).decode("utf-8")
            mime_type = kwargs.get("mime_type", "image/png")

            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                payload = {
                    "inputs": {
                        "image": encoded_image,
                        "text": prompt,
                        "mime_type": mime_type,
                    },
                    "parameters": {
                        "max_new_tokens": self.config.max_tokens,
                        "temperature": self.config.temperature,
                    },
                }

                headers = {"Content-Type": "application/json", **self.config.headers}
                if self.config.api_key:
                    headers["Authorization"] = f"Bearer {self.config.api_key}"

                response = await client.post(
                    self.config.endpoint_url,
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                result = response.json()

            elapsed_ms = int((time.time() - start) * 1000)

            if isinstance(result, list) and len(result) > 0:
                text = result[0].get("generated_text", "")
            elif isinstance(result, dict):
                text = result.get("generated_text", result.get("text", ""))
            else:
                text = str(result)

            return ModelResponse(
                text=text,
                model_type=self.config.model_type,
                model_name=self.config.model_name,
                tokens_used=0,
                processing_time_ms=elapsed_ms,
                raw_response=result if isinstance(result, dict) else {"result": result},
                success=True,
                metadata={
                    "multimodal": True,
                    "fine_tuned_task": self.config.fine_tuned_task,
                    "image_analyzed": True,
                },
            )
        except Exception as e:
            elapsed_ms = int((time.time() - start) * 1000)
            logger.error("haidef_image_error", error=str(e))
            return ModelResponse(
                text="",
                model_type=self.config.model_type,
                model_name=self.config.model_name,
                tokens_used=0,
                processing_time_ms=elapsed_ms,
                raw_response={},
                success=False,
                error=str(e),
            )

    def build_clinical_prompt(self, data: dict[str, Any]) -> str:
        """Build a HAI-DEF-optimized prompt based on the fine-tuned task."""
        task = self.config.fine_tuned_task or "clinical_summary"

        if task == "radiology_report":
            return self._build_radiology_prompt(data)
        elif task == "pathology_analysis":
            return self._build_pathology_prompt(data)
        else:
            return self._build_clinical_summary_prompt(data)

    def _build_clinical_summary_prompt(self, data: dict[str, Any]) -> str:
        """Structured clinical summary prompt for fine-tuned HAI-DEF model."""
        lines = [
            "[INST] Gere um resumo clínico estruturado para o paciente.",
            "",
            "Dados clínicos:",
        ]

        for e in data.get("events", [])[:15]:
            lines.append(f"  Evento: {e.get('type', '')} | Data: {e.get('date', '')} | {e.get('description', '')}")

        for m in data.get("active_medications", []):
            lines.append(f"  Medicação: {m.get('name', '')} {m.get('dosage', '')} ({m.get('frequency', '')})")

        for a in data.get("allergies", []):
            lines.append(f"  Alergia: {a.get('allergen', '')} (Severidade: {a.get('severity_grade', '')})")

        lines.append("")
        lines.append("Gere: resumo, riscos, interações medicamentosas, e urgência. [/INST]")
        return "\n".join(lines)

    def _build_radiology_prompt(self, data: dict[str, Any]) -> str:
        """Prompt optimized for radiology report generation."""
        return (
            "[INST] Analise a imagem radiológica fornecida e gere um laudo estruturado.\n"
            f"Contexto clínico: {data.get('clinical_context', 'Não informado')}\n"
            f"Região: {data.get('body_region', 'Não especificada')}\n"
            f"Modalidade: {data.get('modality', 'Não especificada')}\n"
            "Inclua: achados, impressão diagnóstica, e recomendações. [/INST]"
        )

    def _build_pathology_prompt(self, data: dict[str, Any]) -> str:
        """Prompt optimized for pathology analysis."""
        return (
            "[INST] Analise a lâmina de patologia fornecida.\n"
            f"Tipo de tecido: {data.get('tissue_type', 'Não informado')}\n"
            f"Contexto: {data.get('clinical_context', 'Não informado')}\n"
            "Descreva: características morfológicas, diagnóstico provável, "
            "e classificação histológica quando aplicável. [/INST]"
        )


class ModelOrchestrator:
    """
    Orchestrates multiple AI models, managing routing, failover,
    and ensemble analysis for the SI3DC platform.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self.adapters: dict[ModelType, BaseModelAdapter] = {}
        self._register_default_models()

    def _register_default_models(self) -> None:
        """Register all configured AI models."""
        # MedGemma primary model
        self.register_model(
            ModelConfig(
                model_type=ModelType.MEDGEMMA_27B,
                endpoint_url=self.settings.AI_ENDPOINT_URL,
                model_name=self.settings.AI_MODEL_NAME,
                max_tokens=2048,
                temperature=0.1,
                timeout_seconds=self.settings.AI_TIMEOUT_SECONDS,
                supports_multimodal=True,
                supports_medical_images=True,
            )
        )

        # HAI-DEF clinical model (if configured)
        haidef_url = getattr(self.settings, "HAIDEF_ENDPOINT_URL", None)
        if haidef_url:
            self.register_model(
                ModelConfig(
                    model_type=ModelType.HAI_DEF_CLINICAL,
                    endpoint_url=haidef_url,
                    model_name=getattr(self.settings, "HAIDEF_MODEL_NAME", "hai-def-clinical"),
                    max_tokens=2048,
                    temperature=0.1,
                    timeout_seconds=30,
                    api_key=getattr(self.settings, "HAIDEF_API_KEY", None),
                    fine_tuned_task="clinical_summary",
                )
            )

        # HAI-DEF radiology model (if configured)
        haidef_rad_url = getattr(self.settings, "HAIDEF_RADIOLOGY_URL", None)
        if haidef_rad_url:
            self.register_model(
                ModelConfig(
                    model_type=ModelType.HAI_DEF_RADIOLOGY,
                    endpoint_url=haidef_rad_url,
                    model_name=getattr(self.settings, "HAIDEF_RADIOLOGY_MODEL", "hai-def-radiology"),
                    supports_multimodal=True,
                    supports_medical_images=True,
                    fine_tuned_task="radiology_report",
                )
            )

    def register_model(self, config: ModelConfig) -> None:
        """Register a new AI model adapter."""
        if config.model_type in (ModelType.MEDGEMMA_4B, ModelType.MEDGEMMA_27B):
            adapter = MedGemmaAdapter(config)
        elif config.model_type.value.startswith("hai-def"):
            adapter = HAIDEFAdapter(config)
        else:
            # Default to HAI-DEF adapter for custom fine-tuned models
            adapter = HAIDEFAdapter(config)

        self.adapters[config.model_type] = adapter
        logger.info("model_registered", model_type=config.model_type.value, name=config.model_name)

    def get_adapter(self, model_type: ModelType) -> BaseModelAdapter:
        """Get a specific model adapter."""
        if model_type not in self.adapters:
            raise ValueError(f"Model {model_type.value} not registered")
        return self.adapters[model_type]

    def list_available_models(self) -> list[dict[str, Any]]:
        """List all registered models and their capabilities."""
        return [
            {
                "model_type": model_type.value,
                "model_name": adapter.config.model_name,
                "supports_multimodal": adapter.config.supports_multimodal,
                "supports_medical_images": adapter.config.supports_medical_images,
                "fine_tuned_task": adapter.config.fine_tuned_task,
                "endpoint": adapter.config.endpoint_url,
            }
            for model_type, adapter in self.adapters.items()
        ]

    async def generate(
        self,
        prompt: str,
        model_type: Optional[ModelType] = None,
        fallback: bool = True,
        **kwargs: Any,
    ) -> ModelResponse:
        """
        Generate a response using the specified model (or primary).
        Falls back to other available models if the primary fails.
        """
        preferred = model_type or ModelType.MEDGEMMA_27B
        model_priority = [preferred] + [
            mt for mt in self.adapters if mt != preferred
        ]

        for mt in model_priority:
            if mt not in self.adapters:
                continue

            adapter = self.adapters[mt]
            response = await adapter.generate(prompt, **kwargs)

            if response.success:
                logger.info(
                    "model_response_success",
                    model=mt.value,
                    time_ms=response.processing_time_ms,
                )
                return response

            logger.warning("model_response_failed", model=mt.value, error=response.error)

            if not fallback:
                return response

        # All models failed
        return ModelResponse(
            text="",
            model_type=preferred,
            model_name="none",
            tokens_used=0,
            processing_time_ms=0,
            raw_response={},
            success=False,
            error="All configured models failed to respond",
        )

    async def analyze_image(
        self,
        image_data: bytes,
        prompt: str,
        model_type: Optional[ModelType] = None,
        **kwargs: Any,
    ) -> ModelResponse:
        """
        Analyze a medical image using a multimodal model.
        Prioritizes models that support medical image analysis.
        """
        # Filter to models that support image analysis
        image_models = [
            mt for mt, adapter in self.adapters.items()
            if adapter.config.supports_medical_images
        ]

        if model_type and model_type in image_models:
            preferred_order = [model_type] + [m for m in image_models if m != model_type]
        else:
            preferred_order = image_models

        for mt in preferred_order:
            adapter = self.adapters[mt]
            response = await adapter.analyze_image(image_data, prompt, **kwargs)
            if response.success:
                return response
            logger.warning("image_model_failed", model=mt.value, error=response.error)

        return ModelResponse(
            text="",
            model_type=model_type or ModelType.MEDGEMMA_27B,
            model_name="none",
            tokens_used=0,
            processing_time_ms=0,
            raw_response={},
            success=False,
            error="No multimodal model available for image analysis",
        )

    async def ensemble_analysis(
        self,
        prompt: str,
        model_types: Optional[list[ModelType]] = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Run the same prompt through multiple models and aggregate results.
        Useful for cross-validation and confidence boosting.
        """
        targets = model_types or list(self.adapters.keys())
        results: list[ModelResponse] = []

        for mt in targets:
            if mt in self.adapters:
                response = await self.adapters[mt].generate(prompt, **kwargs)
                results.append(response)

        successful = [r for r in results if r.success]

        return {
            "responses": [
                {
                    "model": r.model_type.value,
                    "text": r.text,
                    "success": r.success,
                    "time_ms": r.processing_time_ms,
                }
                for r in results
            ],
            "successful_count": len(successful),
            "total_count": len(results),
            "consensus": len(successful) > len(results) / 2,
            "primary_response": successful[0].text if successful else "",
        }

    async def check_health(self) -> dict[str, Any]:
        """Check health of all registered models."""
        health: dict[str, Any] = {}
        for mt, adapter in self.adapters.items():
            healthy = await adapter.health_check()
            health[mt.value] = {
                "healthy": healthy,
                "model_name": adapter.config.model_name,
                "endpoint": adapter.config.endpoint_url,
            }
        return health
