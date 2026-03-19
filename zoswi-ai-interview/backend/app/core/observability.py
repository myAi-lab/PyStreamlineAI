from __future__ import annotations

import logging

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


def configure_observability(app: FastAPI, engine: AsyncEngine | None = None) -> None:
    if not settings.telemetry_enabled:
        return

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except Exception as exc:
        logger.warning("OpenTelemetry modules unavailable: %s", exc)
        return

    resource = Resource.create({"service.name": settings.telemetry_service_name})
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=settings.telemetry_otlp_endpoint or None)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app)
    if engine is not None:
        SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)
