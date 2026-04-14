from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

_INITIALIZED = False


def configure_telemetry() -> None:
    """Configure OpenTelemetry. L'export OTLP n'est activé que si CLAIRE_OTLP_ENDPOINT est défini."""
    global _INITIALIZED
    if _INITIALIZED:
        return
    provider = TracerProvider()

    from app.core.config import settings
    if settings.otlp_endpoint:
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        exporter = OTLPSpanExporter(endpoint=settings.otlp_endpoint, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(exporter))

    trace.set_tracer_provider(provider)
    _INITIALIZED = True
