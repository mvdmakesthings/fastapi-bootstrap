"""
Test configuration and fixtures for pytest.
"""

from unittest.mock import MagicMock, patch

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider


@pytest.fixture(scope="session", autouse=True)
def disable_telemetry():
    """
    Fixture to disable OpenTelemetry tracing during test execution.
    This prevents test interactions from being logged to the telemetry system.
    """
    # Create a no-op tracer provider
    no_op_provider = TracerProvider()

    # Replace the global tracer provider
    trace.set_tracer_provider(no_op_provider)

    # Patch BatchSpanProcessor to prevent any span processing
    with patch(
        "opentelemetry.sdk.trace.export.BatchSpanProcessor", return_value=MagicMock()
    ):
        # Patch OTLPSpanExporter to prevent connection attempts
        with patch(
            "opentelemetry.exporter.otlp.proto.grpc.trace_exporter.OTLPSpanExporter",
            return_value=MagicMock(),
        ):
            # Patch the instrumentation classes
            with patch(
                "opentelemetry.instrumentation.fastapi.FastAPIInstrumentor.instrument_app",
                return_value=None,
            ):
                with patch(
                    "opentelemetry.instrumentation.requests.RequestsInstrumentor.instrument",
                    return_value=None,
                ):
                    with patch(
                        "opentelemetry.instrumentation.botocore.BotocoreInstrumentor.instrument",
                        return_value=None,
                    ):
                        yield
