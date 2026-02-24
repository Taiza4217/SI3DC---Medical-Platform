"""SI3DC — OpenTelemetry Tracing.

Distributed tracing for request tracking across services.
"""

from __future__ import annotations

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource

from backend.config import get_settings


def setup_tracing() -> None:
    """Initialize OpenTelemetry tracing."""
    settings = get_settings()

    resource = Resource.create({
        "service.name": settings.APP_NAME,
        "service.version": settings.APP_VERSION,
        "deployment.environment": settings.ENVIRONMENT.value,
    })

    provider = TracerProvider(resource=resource)

    # Console exporter for development; replace with OTLP exporter in production
    if settings.ENVIRONMENT.value == "development":
        processor = BatchSpanProcessor(ConsoleSpanExporter())
        provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)


def get_tracer(name: str = "si3dc") -> trace.Tracer:
    """Get a named tracer instance."""
    return trace.get_tracer(name)
