"""OpenTelemetry setup.

Default: console exporter (spans printed as JSON to stdout — free, local,
visible in uvicorn logs). Set OTEL_EXPORTER_OTLP_ENDPOINT to send to a real
backend (Jaeger, Tempo, Honeycomb...) without code changes.
"""

import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from app.core.config import get_settings

_tracer: trace.Tracer | None = None


def setup_tracing() -> None:
    """Install a TracerProvider once. Called at app startup."""
    global _tracer
    if _tracer is not None:
        return

    settings = get_settings()

    # Tests do not export spans to stdout or an external telemetry backend.
    if settings.app_env == "test":
        trace.set_tracer_provider(trace.NoOpTracerProvider())
        _tracer = trace.get_tracer(settings.app_name)
        return

    resource = Resource.create(
        {"service.name": settings.app_name, "deployment.environment": settings.app_env}
    )
    provider = TracerProvider(resource=resource)

    if os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    else:
        # Local dev: human-readable-ish JSON spans in the uvicorn log.
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(provider)
    _tracer = trace.get_tracer(settings.app_name)


def get_tracer() -> trace.Tracer:
    if _tracer is None:
        setup_tracing()
    assert _tracer is not None
    return _tracer
